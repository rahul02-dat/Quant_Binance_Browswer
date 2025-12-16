import pandas as pd
import numpy as np
from typing import Dict, Optional

class Statistics:
    @staticmethod
    def calculate_returns(prices: pd.Series) -> pd.Series:
        return prices.pct_change().dropna()
    
    @staticmethod
    def calculate_log_returns(prices: pd.Series) -> pd.Series:
        return np.log(prices / prices.shift(1)).dropna()
    
    @staticmethod
    def calculate_statistics(prices: pd.Series) -> Dict:
        if len(prices) == 0:
            return {}
        
        returns = Statistics.calculate_returns(prices)
        
        stats = {
            'mean': float(prices.mean()),
            'std': float(prices.std()),
            'min': float(prices.min()),
            'max': float(prices.max()),
            'last': float(prices.iloc[-1]) if len(prices) > 0 else None,
            'returns_mean': float(returns.mean()) if len(returns) > 0 else None,
            'returns_std': float(returns.std()) if len(returns) > 0 else None,
            'count': len(prices)
        }
        
        return stats
    
    @staticmethod
    def calculate_rolling_correlation(series_x: pd.Series, series_y: pd.Series, 
                                     window: int = 20) -> pd.Series:
        if len(series_x) < window or len(series_y) < window:
            return pd.Series()
        
        df = pd.DataFrame({'x': series_x, 'y': series_y})
        df = df.dropna()
        
        if len(df) < window:
            return pd.Series()
        
        return df['x'].rolling(window=window).corr(df['y'])
    
    @staticmethod
    def calculate_rolling_mean_std(series: pd.Series, window: int = 20) -> tuple:
        if len(series) < window:
            return pd.Series(), pd.Series()
        
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()
        
        return rolling_mean, rolling_std
    
    @staticmethod
    def calculate_z_score(series: pd.Series, window: int = 20) -> pd.Series:
        if len(series) < window:
            return pd.Series()
        
        rolling_mean, rolling_std = Statistics.calculate_rolling_mean_std(series, window)
        
        z_score = (series - rolling_mean) / rolling_std
        return z_score.replace([np.inf, -np.inf], np.nan).dropna()