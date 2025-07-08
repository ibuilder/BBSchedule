"""
Enterprise monitoring and observability for BBSchedule
"""

import os
import time
try:
    import psutil
except ImportError:
    psutil = None
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
from flask import request, g
import json
from collections import defaultdict, deque
import threading

# Metrics collection
metrics_logger = logging.getLogger('metrics')

@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: float
    value: float
    labels: Dict[str, str]

class MetricsCollector:
    """Enterprise metrics collection system"""
    
    def __init__(self):
        self.metrics = defaultdict(deque)
        self.alerts = defaultdict(list)
        self.lock = threading.Lock()
        
        # Metric thresholds for alerting
        self.thresholds = {
            'response_time': {'warning': 2.0, 'critical': 5.0},
            'memory_usage': {'warning': 80.0, 'critical': 95.0},
            'cpu_usage': {'warning': 70.0, 'critical': 90.0},
            'disk_usage': {'warning': 80.0, 'critical': 95.0},
            'error_rate': {'warning': 5.0, 'critical': 10.0},
            'concurrent_users': {'warning': 100, 'critical': 150},
            'database_connections': {'warning': 80, 'critical': 95}
        }
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict] = None):
        """Record a metric value"""
        with self.lock:
            labels = labels or {}
            point = MetricPoint(
                timestamp=time.time(),
                value=value,
                labels=labels
            )
            
            # Keep only last 1000 points per metric
            self.metrics[name].append(point)
            if len(self.metrics[name]) > 1000:
                self.metrics[name].popleft()
            
            # Check for alerts
            self._check_threshold(name, value, labels)
    
    def _check_threshold(self, name: str, value: float, labels: Dict):
        """Check if metric exceeds thresholds"""
        if name in self.thresholds:
            threshold = self.thresholds[name]
            
            if value >= threshold['critical']:
                self._trigger_alert(name, 'critical', value, labels)
            elif value >= threshold['warning']:
                self._trigger_alert(name, 'warning', value, labels)
    
    def _trigger_alert(self, metric: str, level: str, value: float, labels: Dict):
        """Trigger alert for metric threshold breach"""
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'metric': metric,
            'level': level,
            'value': value,
            'labels': labels,
            'threshold': self.thresholds[metric][level]
        }
        
        self.alerts[level].append(alert)
        
        # Log alert
        metrics_logger.warning(f"ALERT {level.upper()}: {metric} = {value} (threshold: {self.thresholds[metric][level]})")
        
        # In production, this would send notifications
        # to Slack, PagerDuty, email, etc.
    
    def get_metrics_summary(self) -> Dict:
        """Get current metrics summary"""
        with self.lock:
            summary = {}
            
            for name, points in self.metrics.items():
                if points:
                    recent_points = list(points)[-10:]  # Last 10 points
                    values = [p.value for p in recent_points]
                    
                    summary[name] = {
                        'current': values[-1] if values else 0,
                        'average': sum(values) / len(values) if values else 0,
                        'min': min(values) if values else 0,
                        'max': max(values) if values else 0,
                        'count': len(points)
                    }
            
            return summary

class PerformanceMonitor:
    """Application performance monitoring"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.request_times = defaultdict(list)
    
    def start_request_timer(self):
        """Start timing a request"""
        g.request_start_time = time.time()
    
    def end_request_timer(self, endpoint: str, status_code: int):
        """End timing a request and record metrics"""
        if hasattr(g, 'request_start_time'):
            duration = time.time() - g.request_start_time
            
            self.metrics.record_metric(
                'response_time',
                duration,
                {
                    'endpoint': endpoint,
                    'status_code': str(status_code),
                    'method': request.method
                }
            )
            
            # Track error rates
            if status_code >= 400:
                self.metrics.record_metric(
                    'error_count',
                    1,
                    {'endpoint': endpoint, 'status_code': str(status_code)}
                )
    
    def record_database_query(self, query_type: str, duration: float):
        """Record database query performance"""
        self.metrics.record_metric(
            'database_query_time',
            duration,
            {'query_type': query_type}
        )
    
    def record_custom_metric(self, name: str, value: float, labels: Dict = None):
        """Record custom business metrics"""
        self.metrics.record_metric(name, value, labels or {})

class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval: int = 30):
        """Start system monitoring in background thread"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_system_resources,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_system_resources(self, interval: int):
        """Monitor system resources continuously"""
        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics.record_metric('cpu_usage', cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.metrics.record_metric('memory_usage', memory.percent)
                self.metrics.record_metric('memory_available', memory.available)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                self.metrics.record_metric('disk_usage', disk_percent)
                
                # Network I/O
                network = psutil.net_io_counters()
                self.metrics.record_metric('network_bytes_sent', network.bytes_sent)
                self.metrics.record_metric('network_bytes_recv', network.bytes_recv)
                
                # Process count
                process_count = len(psutil.pids())
                self.metrics.record_metric('process_count', process_count)
                
                time.sleep(interval)
                
            except Exception as e:
                metrics_logger.error(f"Error monitoring system resources: {e}")
                time.sleep(interval)

class BusinessMetricsMonitor:
    """Business-specific metrics monitoring"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
    
    def record_user_activity(self, action: str, user_id: str):
        """Record user activity metrics"""
        self.metrics.record_metric(
            'user_activity',
            1,
            {'action': action, 'user_id': user_id}
        )
    
    def record_project_metrics(self, project_count: int, active_projects: int):
        """Record project-related metrics"""
        self.metrics.record_metric('total_projects', project_count)
        self.metrics.record_metric('active_projects', active_projects)
    
    def record_performance_metrics(self, spi: float, cpi: float, project_id: str):
        """Record project performance metrics"""
        self.metrics.record_metric(
            'schedule_performance_index',
            spi,
            {'project_id': project_id}
        )
        self.metrics.record_metric(
            'cost_performance_index',
            cpi,
            {'project_id': project_id}
        )

class LogAnalyzer:
    """Log analysis and alerting"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.error_patterns = [
            'ERROR',
            'CRITICAL',
            'FATAL',
            'Exception',
            'Traceback',
            'Database connection failed',
            'Memory error',
            'Timeout'
        ]
    
    def analyze_log_entry(self, log_entry: str):
        """Analyze log entry for issues"""
        for pattern in self.error_patterns:
            if pattern in log_entry:
                self.metrics.record_metric(
                    'log_errors',
                    1,
                    {'pattern': pattern}
                )
                break

class EnterpriseHealthCheck:
    """Comprehensive health checking system"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
    
    def check_database_health(self) -> Dict:
        """Check database connectivity and performance"""
        try:
            from extensions import db
            start_time = time.time()
            
            # Simple query to test connectivity
            result = db.session.execute('SELECT 1').fetchone()
            
            response_time = time.time() - start_time
            self.metrics.record_metric('database_response_time', response_time)
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.metrics.record_metric('database_errors', 1)
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_redis_health(self) -> Dict:
        """Check Redis connectivity if available"""
        try:
            # This would check Redis if configured
            return {
                'status': 'not_configured',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_external_services(self) -> Dict:
        """Check external service dependencies"""
        services = {}
        
        # Check each external service
        # This would include weather APIs, BIM services, etc.
        
        return services
    
    def get_overall_health(self) -> Dict:
        """Get overall system health status"""
        db_health = self.check_database_health()
        redis_health = self.check_redis_health()
        external_health = self.check_external_services()
        
        # Determine overall status
        statuses = [db_health['status']]
        if redis_health['status'] != 'not_configured':
            statuses.append(redis_health['status'])
        
        overall_status = 'healthy' if all(s == 'healthy' for s in statuses) else 'degraded'
        
        return {
            'overall_status': overall_status,
            'database': db_health,
            'redis': redis_health,
            'external_services': external_health,
            'timestamp': datetime.utcnow().isoformat()
        }

# Global monitoring instances
metrics_collector = MetricsCollector()
performance_monitor = PerformanceMonitor(metrics_collector)
system_monitor = SystemMonitor(metrics_collector)
business_monitor = BusinessMetricsMonitor(metrics_collector)
log_analyzer = LogAnalyzer(metrics_collector)
health_checker = EnterpriseHealthCheck(metrics_collector)

def init_enterprise_monitoring(app):
    """Initialize enterprise monitoring for Flask app"""
    
    @app.before_request
    def before_request():
        performance_monitor.start_request_timer()
    
    @app.after_request
    def after_request(response):
        performance_monitor.end_request_timer(
            request.endpoint or 'unknown',
            response.status_code
        )
        return response
    
    # Start system monitoring
    system_monitor.start_monitoring(interval=30)
    
    return {
        'metrics_collector': metrics_collector,
        'performance_monitor': performance_monitor,
        'system_monitor': system_monitor,
        'business_monitor': business_monitor,
        'health_checker': health_checker
    }