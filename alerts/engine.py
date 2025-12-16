import logging
from typing import Dict, List, Callable, Optional
from storage.models import Alert
from datetime import datetime

logger = logging.getLogger(__name__)

class AlertEngine:
    def __init__(self):
        self.alerts = []
        self.callbacks = []
        self.alert_history = []
        
    def load_alerts(self, alerts: List[Alert]):
        self.alerts = [a for a in alerts if a.is_active]
        logger.info(f"Loaded {len(self.alerts)} active alerts")
    
    def add_callback(self, callback: Callable):
        self.callbacks.append(callback)
    
    def check_alerts(self, analytics: Dict):
        triggered_alerts = []
        
        for alert in self.alerts:
            if self._evaluate_alert(alert, analytics):
                triggered_alerts.append(alert)
                self._trigger_alert(alert, analytics)
        
        return triggered_alerts
    
    def _evaluate_alert(self, alert: Alert, analytics: Dict) -> bool:
        metric_value = analytics.get(alert.metric)
        
        if metric_value is None:
            return False
        
        try:
            metric_value = float(metric_value)
        except (ValueError, TypeError):
            return False
        
        if alert.condition == '>':
            return metric_value > alert.threshold
        elif alert.condition == '<':
            return metric_value < alert.threshold
        elif alert.condition == '>=':
            return metric_value >= alert.threshold
        elif alert.condition == '<=':
            return metric_value <= alert.threshold
        elif alert.condition == '==':
            return abs(metric_value - alert.threshold) < 1e-6
        elif alert.condition == '!=':
            return abs(metric_value - alert.threshold) >= 1e-6
        
        return False
    
    def _trigger_alert(self, alert: Alert, analytics: Dict):
        alert_data = {
            'alert_id': alert.id,
            'metric': alert.metric,
            'condition': alert.condition,
            'threshold': alert.threshold,
            'current_value': analytics.get(alert.metric),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.alert_history.append(alert_data)
        
        logger.warning(f"ALERT TRIGGERED: {alert.metric} {alert.condition} {alert.threshold}, "
                      f"current value: {alert_data['current_value']}")
        
        for callback in self.callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        return self.alert_history[-limit:]