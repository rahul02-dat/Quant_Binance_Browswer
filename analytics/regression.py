import pandas as pd
import numpy as np
from statsmodels.api import OLS, add_constant
from typing import Dict, Tuple, Optional

class Regression:
    @staticmethod
    def ols_regression(y: pd.Series, x: pd.Series) -> Dict:
        if len(y) != len(x) or len(y) < 2:
            return {}
        
        df = pd.DataFrame({'y': y, 'x': x}).dropna()
        
        if len(df) < 2:
            return {}
        
        X = add_constant(df['x'])
        model = OLS(df['y'], X).fit()
        
        return {
            'intercept': float(model.params['const']),
            'slope': float(model.params['x']),
            'r_squared': float(model.rsquared),
            'p_value': float(model.pvalues['x']),
            'std_err': float(model.bse['x'])
        }
    
    @staticmethod
    def calculate_hedge_ratio(prices_y: pd.Series, prices_x: pd.Series) -> Optional[float]:
        result = Regression.ols_regression(prices_y, prices_x)
        if result:
            return result.get('slope')
        return None
    
    @staticmethod
    def calculate_spread(prices_y: pd.Series, prices_x: pd.Series, 
                        hedge_ratio: Optional[float] = None) -> pd.Series:
        if hedge_ratio is None:
            hedge_ratio = Regression.calculate_hedge_ratio(prices_y, prices_x)
        
        if hedge_ratio is None:
            return pd.Series()
        
        df = pd.DataFrame({'x': prices_x, 'y': prices_y})
        df = df.dropna()
        
        if df.empty:
            return pd.Series()
        
        spread = df['y'] - hedge_ratio * df['x']
        return spread
    
    @staticmethod
    def rolling_ols(y: pd.Series, x: pd.Series, window: int = 20) -> pd.DataFrame:
        if len(y) < window or len(x) < window:
            return pd.DataFrame()
        
        results = []
        
        for i in range(window, len(y) + 1):
            y_window = y.iloc[i-window:i]
            x_window = x.iloc[i-window:i]
            
            result = Regression.ols_regression(y_window, x_window)
            
            if result:
                results.append({
                    'timestamp': y.index[i-1],
                    'hedge_ratio': result['slope'],
                    'intercept': result['intercept'],
                    'r_squared': result['r_squared']
                })
        
        return pd.DataFrame(results).set_index('timestamp')