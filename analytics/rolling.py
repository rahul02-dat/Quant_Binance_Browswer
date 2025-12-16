import pandas as pd
import numpy as np
from typing import Dict, List
from collections import deque

class RollingBuffer:
    def __init__(self, maxlen: int = 10000):
        self.maxlen = maxlen
        self.buffers = {}
    
    def add_tick(self, symbol: str, tick: dict):
        if symbol not in self.buffers:
            self.buffers[symbol] = deque(maxlen=self.maxlen)
        
        self.buffers[symbol].append(tick)
    
    def get_ticks(self, symbol: str, limit: int = None) -> List[dict]:
        if symbol not in self.buffers:
            return []
        
        if limit is None:
            return list(self.buffers[symbol])
        
        return list(self.buffers[symbol])[-limit:]
    
    def get_dataframe(self, symbol: str, limit: int = None) -> pd.DataFrame:
        ticks = self.get_ticks(symbol, limit)
        
        if not ticks:
            return pd.DataFrame()
        
        df = pd.DataFrame(ticks)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('timestamp')
        df = df[~df.index.duplicated(keep='last')]
        df = df.sort_index()
        
        return df
    
    def get_prices(self, symbol: str, limit: int = None) -> pd.Series:
        df = self.get_dataframe(symbol, limit)
        
        if df.empty:
            return pd.Series()
        
        return df['price']
    
    def clear(self, symbol: str = None):
        if symbol:
            if symbol in self.buffers:
                self.buffers[symbol].clear()
        else:
            self.buffers.clear()