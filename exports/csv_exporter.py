import pandas as pd
import os
from typing import List
from storage.models import Tick, ResampledData, Analytics

class CSVExporter:
    @staticmethod
    def export_ticks(ticks: List[Tick], filename: str) -> str:
        os.makedirs('exports', exist_ok=True)
        
        data = [{
            'timestamp': tick.timestamp,
            'symbol': tick.symbol,
            'price': tick.price,
            'quantity': tick.quantity
        } for tick in ticks]
        
        df = pd.DataFrame(data)
        filepath = os.path.join('exports', filename)
        df.to_csv(filepath, index=False)
        
        return filepath
    
    @staticmethod
    def export_resampled(bars: List[ResampledData], filename: str) -> str:
        os.makedirs('exports', exist_ok=True)
        
        data = [{
            'timestamp': bar.start_time,
            'symbol': bar.symbol,
            'timeframe': bar.timeframe,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        } for bar in bars]
        
        df = pd.DataFrame(data)
        filepath = os.path.join('exports', filename)
        df.to_csv(filepath, index=False)
        
        return filepath
    
    @staticmethod
    def export_analytics(analytics: List[Analytics], filename: str) -> str:
        os.makedirs('exports', exist_ok=True)
        
        data = [{
            'timestamp': a.computed_at,
            'symbol_x': a.symbol_x,
            'symbol_y': a.symbol_y,
            'timeframe': a.timeframe,
            'hedge_ratio': a.hedge_ratio,
            'spread': a.spread,
            'z_score': a.z_score,
            'rolling_corr': a.rolling_corr,
            'adf_stat': a.adf_stat,
            'p_value': a.p_value
        } for a in analytics]
        
        df = pd.DataFrame(data)
        filepath = os.path.join('exports', filename)
        df.to_csv(filepath, index=False)
        
        return filepath
    
    @staticmethod
    def export_dataframe(df: pd.DataFrame, filename: str) -> str:
        os.makedirs('exports', exist_ok=True)
        
        filepath = os.path.join('exports', filename)
        df.to_csv(filepath, index=True)
        
        return filepath