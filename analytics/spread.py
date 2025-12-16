import pandas as pd
import numpy as np
from analytics.regression import Regression
from analytics.statistics import Statistics
from analytics.stationarity import Stationarity
from typing import Dict, Optional

class SpreadAnalytics:
    @staticmethod
    def calculate_pair_analytics(prices_x: pd.Series, prices_y: pd.Series, 
                                 window: int = 20) -> Dict:
        if len(prices_x) < window or len(prices_y) < window:
            return {}
        
        hedge_ratio = Regression.calculate_hedge_ratio(prices_y, prices_x)
        
        if hedge_ratio is None:
            return {}
        
        spread = Regression.calculate_spread(prices_y, prices_x, hedge_ratio)
        
        if spread.empty:
            return {}
        
        z_score = Statistics.calculate_z_score(spread, window)
        rolling_corr = Statistics.calculate_rolling_correlation(prices_x, prices_y, window)
        
        adf_result = Stationarity.adf_test(spread)
        
        analytics = {
            'hedge_ratio': float(hedge_ratio),
            'spread_mean': float(spread.mean()),
            'spread_std': float(spread.std()),
            'spread_last': float(spread.iloc[-1]) if len(spread) > 0 else None,
            'z_score_last': float(z_score.iloc[-1]) if len(z_score) > 0 else None,
            'z_score_mean': float(z_score.mean()) if len(z_score) > 0 else None,
            'z_score_std': float(z_score.std()) if len(z_score) > 0 else None,
            'correlation': float(rolling_corr.iloc[-1]) if len(rolling_corr) > 0 else None,
            'adf_statistic': adf_result.get('adf_statistic'),
            'adf_p_value': adf_result.get('p_value'),
            'is_stationary': adf_result.get('is_stationary', False)
        }
        
        return analytics
    
    @staticmethod
    def calculate_rolling_analytics(prices_x: pd.Series, prices_y: pd.Series, 
                                    window: int = 20) -> pd.DataFrame:
        if len(prices_x) < window or len(prices_y) < window:
            return pd.DataFrame()
        
        results = []
        
        for i in range(window, len(prices_x) + 1):
            x_window = prices_x.iloc[i-window:i]
            y_window = prices_y.iloc[i-window:i]
            
            analytics = SpreadAnalytics.calculate_pair_analytics(x_window, y_window, window)
            
            if analytics:
                analytics['timestamp'] = prices_x.index[i-1]
                results.append(analytics)
        
        if results:
            return pd.DataFrame(results).set_index('timestamp')
        return pd.DataFrame()