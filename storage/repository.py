from sqlalchemy.orm import Session
from storage.models import Tick, ResampledData, Analytics, Alert
from typing import List, Optional
import pandas as pd

class TickRepository:
    @staticmethod
    def insert_tick(db: Session, timestamp: int, symbol: str, price: float, quantity: float):
        tick = Tick(timestamp=timestamp, symbol=symbol, price=price, quantity=quantity)
        db.add(tick)
        db.commit()
        return tick
    
    @staticmethod
    def bulk_insert_ticks(db: Session, ticks: List[dict]):
        tick_objs = [Tick(**tick) for tick in ticks]
        db.bulk_save_objects(tick_objs)
        db.commit()
    
    @staticmethod
    def get_ticks(db: Session, symbol: str, start_time: int, end_time: int) -> List[Tick]:
        return db.query(Tick).filter(
            Tick.symbol == symbol,
            Tick.timestamp >= start_time,
            Tick.timestamp <= end_time
        ).order_by(Tick.timestamp).all()
    
    @staticmethod
    def get_recent_ticks(db: Session, symbol: str, limit: int = 1000) -> List[Tick]:
        return db.query(Tick).filter(
            Tick.symbol == symbol
        ).order_by(Tick.timestamp.desc()).limit(limit).all()

class ResampledRepository:
    @staticmethod
    def insert_bar(db: Session, symbol: str, timeframe: str, start_time: int, 
                   open_price: float, high: float, low: float, close: float, volume: float):
        bar = ResampledData(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=volume
        )
        db.add(bar)
        db.commit()
        return bar
    
    @staticmethod
    def bulk_insert_bars(db: Session, bars: List[dict]):
        bar_objs = [ResampledData(**bar) for bar in bars]
        db.bulk_save_objects(bar_objs)
        db.commit()
    
    @staticmethod
    def get_bars(db: Session, symbol: str, timeframe: str, start_time: int, end_time: int) -> List[ResampledData]:
        return db.query(ResampledData).filter(
            ResampledData.symbol == symbol,
            ResampledData.timeframe == timeframe,
            ResampledData.start_time >= start_time,
            ResampledData.start_time <= end_time
        ).order_by(ResampledData.start_time).all()
    
    @staticmethod
    def get_recent_bars(db: Session, symbol: str, timeframe: str, limit: int = 500) -> List[ResampledData]:
        return db.query(ResampledData).filter(
            ResampledData.symbol == symbol,
            ResampledData.timeframe == timeframe
        ).order_by(ResampledData.start_time.desc()).limit(limit).all()

class AnalyticsRepository:
    @staticmethod
    def insert_analytics(db: Session, symbol_x: str, symbol_y: str, timeframe: str,
                        hedge_ratio: Optional[float], spread: Optional[float], 
                        z_score: Optional[float], rolling_corr: Optional[float],
                        adf_stat: Optional[float], p_value: Optional[float], 
                        computed_at: int):
        analytics = Analytics(
            symbol_x=symbol_x,
            symbol_y=symbol_y,
            timeframe=timeframe,
            hedge_ratio=hedge_ratio,
            spread=spread,
            z_score=z_score,
            rolling_corr=rolling_corr,
            adf_stat=adf_stat,
            p_value=p_value,
            computed_at=computed_at
        )
        db.add(analytics)
        db.commit()
        return analytics
    
    @staticmethod
    def get_analytics(db: Session, symbol_x: str, symbol_y: str, timeframe: str, 
                     start_time: int, end_time: int) -> List[Analytics]:
        return db.query(Analytics).filter(
            Analytics.symbol_x == symbol_x,
            Analytics.symbol_y == symbol_y,
            Analytics.timeframe == timeframe,
            Analytics.computed_at >= start_time,
            Analytics.computed_at <= end_time
        ).order_by(Analytics.computed_at).all()
    
    @staticmethod
    def get_recent_analytics(db: Session, symbol_x: str, symbol_y: str, 
                           timeframe: str, limit: int = 100) -> List[Analytics]:
        return db.query(Analytics).filter(
            Analytics.symbol_x == symbol_x,
            Analytics.symbol_y == symbol_y,
            Analytics.timeframe == timeframe
        ).order_by(Analytics.computed_at.desc()).limit(limit).all()

class AlertRepository:
    @staticmethod
    def create_alert(db: Session, metric: str, condition: str, threshold: float) -> Alert:
        alert = Alert(metric=metric, condition=condition, threshold=threshold, is_active=True)
        db.add(alert)
        db.commit()
        return alert
    
    @staticmethod
    def get_active_alerts(db: Session) -> List[Alert]:
        return db.query(Alert).filter(Alert.is_active == True).all()
    
    @staticmethod
    def deactivate_alert(db: Session, alert_id: int):
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.is_active = False
            db.commit()
    
    @staticmethod
    def delete_alert(db: Session, alert_id: int):
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            db.delete(alert)
            db.commit()