import asyncio
import logging
import time
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
from api.routes import router
from config.settings import (
    DEFAULT_SYMBOLS, TIMEFRAMES, DEFAULT_ROLLING_WINDOW,
    API_HOST, API_PORT, ANALYTICS_INTERVAL
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Quant Analytics API")
app.include_router(router, prefix="/api/v1")

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
        await asyncio.sleep(10)
        
        while self.running:
            try:
                await asyncio.sleep(5)
                
                for symbol in self.symbols:
                    ticks = self.rolling_buffer.get_ticks(symbol, limit=5000)
                    
                    if len(ticks) < 10:
                        continue
                    
                    db = SessionLocal()
                    
                    for timeframe in TIMEFRAMES:
                        try:
                            bars = Resampler.resample_ticks(ticks, timeframe)
                            
                            if bars and len(bars) > 0:
                                ResampledRepository.bulk_insert_bars(db, bars)
                                logger.debug(f"Resampled {len(bars)} bars for {symbol} {timeframe}")
                        except Exception as e:
                            logger.debug(f"Resampling error for {symbol} {timeframe}: {e}")
                    
                    db.close()
            
            except Exception as e:
                logger.error(f"Error in resampling loop: {e}")
    
    async def analytics_loop(self):
        await asyncio.sleep(15)
        
        while self.running:
            try:
                await asyncio.sleep(ANALYTICS_INTERVAL)
                
                if len(self.symbols) < 2:
                    continue
                
                symbol_x = self.symbols[0]
                symbol_y = self.symbols[1]
                
                prices_x = self.rolling_buffer.get_prices(symbol_x, limit=1000)
                prices_y = self.rolling_buffer.get_prices(symbol_y, limit=1000)
                
                if len(prices_x) < DEFAULT_ROLLING_WINDOW or len(prices_y) < DEFAULT_ROLLING_WINDOW:
                    continue
                
                prices_x = prices_x[~prices_x.index.duplicated(keep='last')]
                prices_y = prices_y[~prices_y.index.duplicated(keep='last')]
                
                prices_x = prices_x.iloc[-500:]
                prices_y = prices_y.iloc[-500:]
                
                analytics = SpreadAnalytics.calculate_pair_analytics(
                    prices_x, prices_y, DEFAULT_ROLLING_WINDOW
                )
                
                if analytics:
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
                    logger.debug(f"Analytics computed: z_score={analytics.get('z_score_last')}")
            
            except Exception as e:
                logger.error(f"Error in analytics loop: {e}")
    
    async def stop(self):
        self.running = False
        
        if self.ws_client:
            await self.ws_client.stop()
        
        await self.tick_handler.stop()
        
        logger.info("Application stopped")

analytics_app = QuantAnalyticsApp()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(analytics_app.start())

@app.on_event("shutdown")
async def shutdown_event():
    await analytics_app.stop()

@app.get("/")
def root():
    return {
        "status": "running",
        "symbols": analytics_app.symbols,
        "websocket_stats": analytics_app.ws_client.get_stats() if analytics_app.ws_client else {},
        "buffer_status": {symbol: len(analytics_app.rolling_buffer.get_ticks(symbol)) 
                         for symbol in analytics_app.symbols}
    }

def main():
    logger.info("=" * 60)
    logger.info("Starting Quant Analytics Application")
    logger.info("=" * 60)
    logger.info(f"Symbols: {DEFAULT_SYMBOLS}")
    logger.info(f"API Server: http://{API_HOST}:{API_PORT}")
    logger.info(f"API Docs: http://{API_HOST}:{API_PORT}/docs")
    logger.info("")
    logger.info("To start the dashboard, run in another terminal:")
    logger.info("  streamlit run frontend/dashboard.py")
    logger.info("=" * 60)
    
    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="info")

if __name__ == "__main__":
    main()