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