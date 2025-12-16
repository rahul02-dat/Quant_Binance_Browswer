from pydantic import BaseModel
from typing import Optional, List

class TickResponse(BaseModel):
    timestamp: int
    symbol: str
    price: float
    quantity: float
    
    class Config:
        from_attributes = True

class ResampledBarResponse(BaseModel):
    symbol: str
    timeframe: str
    start_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    symbol_x: str
    symbol_y: str
    timeframe: str
    hedge_ratio: Optional[float]
    spread: Optional[float]
    z_score: Optional[float]
    rolling_corr: Optional[float]
    adf_stat: Optional[float]
    p_value: Optional[float]
    computed_at: int
    
    class Config:
        from_attributes = True

class AlertCreate(BaseModel):
    metric: str
    condition: str
    threshold: float

class AlertResponse(BaseModel):
    id: int
    metric: str
    condition: str
    threshold: float
    is_active: bool
    
    class Config:
        from_attributes = True

class AnalyticsRequest(BaseModel):
    symbol_x: str
    symbol_y: str
    timeframe: str
    window: int = 20