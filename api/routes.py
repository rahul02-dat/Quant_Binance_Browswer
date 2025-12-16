from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from storage.database import get_db
from storage.repository import TickRepository, ResampledRepository, AnalyticsRepository, AlertRepository
from api.schemas import (
    TickResponse, ResampledBarResponse, AnalyticsResponse, 
    AlertCreate, AlertResponse, AnalyticsRequest
)
from typing import List
import time

router = APIRouter()

# Global reference to the analytics app (will be set from app.py)
_analytics_app = None

def set_analytics_app(app):
    global _analytics_app
    _analytics_app = app

@router.get("/", response_model=dict)
def root_status():
    """Root status endpoint for dashboard connection check"""
    if not _analytics_app:
        return {"status": "initializing", "websocket_stats": {}, "buffer_status": {}}
    
    return {
        "status": "running",
        "symbols": _analytics_app.symbols,
        "websocket_stats": _analytics_app.ws_client.get_stats() if _analytics_app.ws_client else {},
        "buffer_status": {symbol: len(_analytics_app.rolling_buffer.get_ticks(symbol)) 
                         for symbol in _analytics_app.symbols}
    }

@router.get("/ticks/{symbol}", response_model=List[TickResponse])
def get_ticks(symbol: str, limit: int = 1000, db: Session = Depends(get_db)):
    ticks = TickRepository.get_recent_ticks(db, symbol, limit)
    return ticks

@router.get("/bars/{symbol}/{timeframe}", response_model=List[ResampledBarResponse])
def get_bars(symbol: str, timeframe: str, limit: int = 500, db: Session = Depends(get_db)):
    bars = ResampledRepository.get_recent_bars(db, symbol, timeframe, limit)
    return bars

@router.get("/analytics/{symbol_x}/{symbol_y}/{timeframe}", response_model=List[AnalyticsResponse])
def get_analytics(symbol_x: str, symbol_y: str, timeframe: str, 
                 limit: int = 100, db: Session = Depends(get_db)):
    analytics = AnalyticsRepository.get_recent_analytics(db, symbol_x, symbol_y, timeframe, limit)
    return analytics

@router.get("/analytics-debug/{symbol_x}/{symbol_y}")
def get_analytics_debug(symbol_x: str, symbol_y: str, db: Session = Depends(get_db)):
    """Debug endpoint to check what analytics are stored"""
    try:
        analytics_tick = AnalyticsRepository.get_recent_analytics(db, symbol_x, symbol_y, 'tick', limit=5)
        return {
            "status": "success",
            "symbol_x": symbol_x,
            "symbol_y": symbol_y,
            "count": len(analytics_tick),
            "records": [dict(a) if hasattr(a, '__dict__') else a for a in analytics_tick[:2]]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.post("/alerts", response_model=AlertResponse)
def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    new_alert = AlertRepository.create_alert(db, alert.metric, alert.condition, alert.threshold)
    return new_alert

@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    alerts = AlertRepository.get_active_alerts(db)
    return alerts

@router.delete("/alerts/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    AlertRepository.delete_alert(db, alert_id)
    return {"status": "deleted"}

@router.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": int(time.time() * 1000)}

@router.get("/status")
def system_status():
    return {
        "status": "operational",
        "timestamp": int(time.time() * 1000),
        "database": "connected"
    }