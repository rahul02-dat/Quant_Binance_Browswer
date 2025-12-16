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
        if len(prices_x) < 5 or len(prices_y) < 5:
            return {}
        
        hedge_ratio = Regression.calculate_hedge_ratio(prices_y, prices_x)
        
        if hedge_ratio is None:
            return {}
        
        spread = Regression.calculate_spread(prices_y, prices_x, hedge_ratio)
        
        if spread.empty or len(spread) < 5:
            return {}
        
        # Calculate Z-Score directly from recent data
        spread_recent = spread.iloc[-max(window, 5):]
        spread_mean = float(spread_recent.mean())
        spread_std = float(spread_recent.std())
        
        z_score_last = 0.0
        try:
            if spread_std > 0:
                z_score_last = float((spread.iloc[-1] - spread_mean) / spread_std)
                if not pd.notna(z_score_last):
                    z_score_last = 0.0
            else:
                z_score_last = 0.0
        except Exception as e:
            z_score_last = 0.0
        
        # Calculate correlation directly from recent prices
        prices_x_recent = prices_x.iloc[-max(window, 5):]
        prices_y_recent = prices_y.iloc[-max(window, 5):]
        
        corr_last = 1.0
        try:
            if len(prices_x_recent) > 1 and len(prices_y_recent) > 1:
                corr_val = prices_x_recent.corr(prices_y_recent)
                corr_last = float(corr_val) if pd.notna(corr_val) else 1.0
        except Exception as e:
            corr_last = 1.0
        
        adf_result = Stationarity.adf_test(spread)
        
        analytics = {
            'hedge_ratio': float(hedge_ratio),
            'spread_mean': float(spread_mean),
            'spread_std': float(spread_std),
            'spread_last': float(spread.iloc[-1]) if len(spread) > 0 else None,
            'z_score_last': z_score_last,
            'z_score_mean': float(spread_recent.mean()),
            'z_score_std': float(spread_std),
            'correlation': corr_last,
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