import pandas as pd
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class Resampler:
    TIMEFRAMES = {
        '1s': '1s',
        '1m': '1min',
        '5m': '5min'
    }
    
    @staticmethod
    def resample_ticks(ticks: List[dict], timeframe: str) -> List[dict]:
        if not ticks:
            return []
        
        if timeframe not in Resampler.TIMEFRAMES:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        df = pd.DataFrame(ticks)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('timestamp')
        df = df.sort_index()
        
        resampled = df['price'].resample(Resampler.TIMEFRAMES[timeframe]).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        })
        
        volume = df['quantity'].resample(Resampler.TIMEFRAMES[timeframe]).sum()
        
        resampled['volume'] = volume
        resampled = resampled.dropna()
        
        bars = []
        for idx, row in resampled.iterrows():
            bars.append({
                'symbol': ticks[0]['symbol'],
                'timeframe': timeframe,
                'start_time': int(idx.timestamp() * 1000),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            })
        
        return bars
    
    @staticmethod
    def resample_from_dataframe(df: pd.DataFrame, timeframe: str, symbol: str) -> List[dict]:
        if df.empty:
            return []
        
        if timeframe not in Resampler.TIMEFRAMES:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        if 'timestamp' not in df.columns:
            return []
        
        df_copy = df.copy()
        df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'], unit='ms')
        df_copy = df_copy.set_index('timestamp')
        df_copy = df_copy.sort_index()
        
        resampled = df_copy['price'].resample(Resampler.TIMEFRAMES[timeframe]).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        })
        
        volume = df_copy['quantity'].resample(Resampler.TIMEFRAMES[timeframe]).sum()
        resampled['volume'] = volume
        resampled = resampled.dropna()
        
        bars = []
        for idx, row in resampled.iterrows():
            bars.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'start_time': int(idx.timestamp() * 1000),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            })
        
        return bars