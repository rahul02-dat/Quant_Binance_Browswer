import asyncio
import logging
import time
import subprocess
import os
from fastapi import FastAPI
import uvicorn
from storage.database import init_db, SessionLocal
from storage.repository import TickRepository, ResampledRepository, AnalyticsRepository, AlertRepository
from ingestion.binance_ws import BinanceWebSocket
from ingestion.tick_handler import TickHandler
from analytics.resampler import Resampler
from analytics.rolling import RollingBuffer
from analytics.spread import SpreadAnalytics
from alerts.engine import AlertEngine
from api.routes import router, set_analytics_app
from config.settings import (
    DEFAULT_SYMBOLS, TIMEFRAMES, DEFAULT_ROLLING_WINDOW,
    API_HOST, API_PORT, ANALYTICS_INTERVAL, DASHBOARD_PORT
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Quant Analytics API")
app.include_router(router, prefix="/api/v1")

dashboard_process = None

class QuantAnalyticsApp:
    def __init__(self, symbols=None):
        self.symbols = symbols or DEFAULT_SYMBOLS
        self.tick_handler = TickHandler()
        self.rolling_buffer = RollingBuffer()
        self.alert_engine = AlertEngine()
        self.ws_client = None
        self.running = False
        
        init_db()
        logger.info("Database initialized")
        
        db = SessionLocal()
        alerts = AlertRepository.get_active_alerts(db)
        self.alert_engine.load_alerts(alerts)
        db.close()
    
    async def start(self):
        self.running = True
        
        self.ws_client = BinanceWebSocket(
            symbols=self.symbols,
            callback=self.on_tick
        )
        
        await self.tick_handler.start()
        
        asyncio.create_task(self.ws_client.connect())
        asyncio.create_task(self.resampling_loop())
        asyncio.create_task(self.analytics_loop())
        
        logger.info(f"Application started for symbols: {self.symbols}")
    
    async def on_tick(self, tick: dict):
        await self.tick_handler.handle_tick(tick)
        self.rolling_buffer.add_tick(tick['symbol'], tick)
    
    async def resampling_loop(self):
        logger.info("Resampling loop starting in 10 seconds...")
        await asyncio.sleep(10)
        
        while self.running:
            try:
                await asyncio.sleep(5)
                
                for symbol in self.symbols:
                    ticks = self.rolling_buffer.get_ticks(symbol, limit=5000)
                    
                    if len(ticks) < 10:
                        logger.debug(f"Not enough ticks for {symbol}: {len(ticks)}")
                        continue
                    
                    db = SessionLocal()
                    
                    for timeframe in TIMEFRAMES:
                        try:
                            bars = Resampler.resample_ticks(ticks, timeframe)
                            
                            if bars and len(bars) > 0:
                                ResampledRepository.bulk_insert_bars(db, bars)
                                logger.info(f"✓ Resampled {len(bars)} bars for {symbol} {timeframe}")
                        except Exception as e:
                            logger.error(f"Resampling error for {symbol} {timeframe}: {e}")
                    
                    db.close()
            
            except Exception as e:
                logger.error(f"Error in resampling loop: {e}")
    
    async def analytics_loop(self):
        logger.info("Analytics loop starting in 5 seconds...")
        await asyncio.sleep(5)
        
        while self.running:
            try:
                await asyncio.sleep(1.0)  # Run every 1 second instead of 500ms
                
                if len(self.symbols) < 2:
                    continue
                
                symbol_x = self.symbols[0]
                symbol_y = self.symbols[1]
                
                prices_x = self.rolling_buffer.get_prices(symbol_x, limit=1000)
                prices_y = self.rolling_buffer.get_prices(symbol_y, limit=1000)
                
                if len(prices_x) < 10 or len(prices_y) < 10:
                    continue
                
                # Remove duplicates
                prices_x = prices_x[~prices_x.index.duplicated(keep='last')]
                prices_y = prices_y[~prices_y.index.duplicated(keep='last')]
                
                # Use recent data for calculation
                prices_x = prices_x.iloc[-200:]
                prices_y = prices_y.iloc[-200:]
                
                # Calculate with adaptive window size
                window = min(DEFAULT_ROLLING_WINDOW, len(prices_x) // 2)
                if window < 5:
                    continue
                
                analytics = SpreadAnalytics.calculate_pair_analytics(
                    prices_x, prices_y, window
                )
                
                if analytics and (analytics.get('z_score_last') is not None or analytics.get('correlation') is not None):
                    try:
                        db = SessionLocal()
                        
                        AnalyticsRepository.insert_analytics(
                            db=db,
                            symbol_x=symbol_x,
                            symbol_y=symbol_y,
                            timeframe='tick',
                            hedge_ratio=analytics.get('hedge_ratio'),
                            spread=analytics.get('spread_last'),
                            z_score=analytics.get('z_score_last'),
                            rolling_corr=analytics.get('correlation'),
                            adf_stat=analytics.get('adf_statistic'),
                            p_value=analytics.get('adf_p_value'),
                            computed_at=int(time.time() * 1000)
                        )
                        
                        db.close()
                        self.alert_engine.check_alerts(analytics)
                        logger.debug(f"✓ Analytics saved: Z={analytics.get('z_score_last'):.2f}, Corr={analytics.get('correlation'):.2f}")
                    except Exception as db_error:
                        logger.error(f"Database error saving analytics: {db_error}")
                        try:
                            db.close()
                        except:
                            pass
            
            except Exception as e:
                logger.error(f"Error in analytics loop: {e}")
    
    async def stop(self):
        self.running = False
        
        if self.ws_client:
            await self.ws_client.stop()
        
        await self.tick_handler.stop()
        
        logger.info("Application stopped")

analytics_app = QuantAnalyticsApp()

# Pass the analytics app to the router so it can access app state
set_analytics_app(analytics_app)

@app.on_event("startup")
async def startup_event():
    global dashboard_process
    asyncio.create_task(analytics_app.start())
    
    # Start the Streamlit dashboard in a subprocess
    dashboard_path = os.path.join(os.path.dirname(__file__), "frontend", "dashboard.py")
    try:
        dashboard_process = subprocess.Popen(
            ["streamlit", "run", dashboard_path, f"--server.port={DASHBOARD_PORT}", "--logger.level=warning"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"Dashboard started on http://localhost:{DASHBOARD_PORT}")
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    global dashboard_process
    await analytics_app.stop()
    
    # Stop the Streamlit dashboard
    if dashboard_process:
        dashboard_process.terminate()
        try:
            dashboard_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            dashboard_process.kill()

def main():
    logger.info("=" * 60)
    logger.info("Starting Quant Analytics Application")
    logger.info("=" * 60)
    logger.info(f"Symbols: {DEFAULT_SYMBOLS}")
    logger.info(f"API Server: http://{API_HOST}:{API_PORT}")
    logger.info(f"API Docs: http://{API_HOST}:{API_PORT}/docs")
    logger.info(f"Dashboard: http://localhost:{DASHBOARD_PORT}")
    logger.info("=" * 60)
    
    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="info")

if __name__ == "__main__":
    main()