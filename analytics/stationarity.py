import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from typing import Dict, Optional

class Stationarity:
    @staticmethod
    def adf_test(series: pd.Series, maxlag: Optional[int] = None) -> Dict:
        if len(series) < 10:
            return {}
        
        series_clean = series.replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(series_clean) < 10:
            return {}
        
        try:
            result = adfuller(series_clean, maxlag=maxlag, autolag='AIC')
            
            return {
                'adf_statistic': float(result[0]),
                'p_value': float(result[1]),
                'used_lag': int(result[2]),
                'n_obs': int(result[3]),
                'critical_values': {
                    '1%': float(result[4]['1%']),
                    '5%': float(result[4]['5%']),
                    '10%': float(result[4]['10%'])
                },
                'is_stationary': result[1] < 0.05
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def is_stationary(series: pd.Series, significance_level: float = 0.05) -> bool:
        result = Stationarity.adf_test(series)
        if 'p_value' in result:
            return result['p_value'] < significance_level
        return False