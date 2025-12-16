from sqlalchemy import Column, Integer, Float, String, BigInteger, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Tick(Base):
    __tablename__ = 'ticks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(BigInteger, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)

class ResampledData(Base):
    __tablename__ = 'resampled_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    start_time = Column(BigInteger, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

class Analytics(Base):
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol_x = Column(String(20), nullable=False, index=True)
    symbol_y = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    hedge_ratio = Column(Float, nullable=True)
    spread = Column(Float, nullable=True)
    z_score = Column(Float, nullable=True)
    rolling_corr = Column(Float, nullable=True)
    adf_stat = Column(Float, nullable=True)
    p_value = Column(Float, nullable=True)
    computed_at = Column(BigInteger, nullable=False, index=True)

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric = Column(String(50), nullable=False)
    condition = Column(String(10), nullable=False)
    threshold = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)