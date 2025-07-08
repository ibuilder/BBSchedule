"""
Application monitoring and alerting system
"""
import os
import time
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
from flask import current_app
from extensions import db
from models import Project, Activity, ProjectStatus

@dataclass
class Alert:
    """Alert data structure."""
    id: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    metadata: Dict = None

class MonitoringService:
    """Application monitoring and alerting service."""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.metrics_history: List[Dict] = []
        self.thresholds = {
            'response_time_ms': 1000,
            'error_rate_percent': 5.0,
            'database_response_ms': 500,
            'memory_usage_percent': 80,
            'disk_usage_percent': 85,
            'active_connections': 80
        }
    
    def collect_metrics(self) -> Dict:
        """Collect application metrics."""
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'application': self._get_app_metrics(),
            'database': self._get_database_metrics(),
            'system': self._get_system_metrics(),
            'business': self._get_business_metrics()
        }
        
        # Store in history
        self.metrics_history.append(metrics)
        
        # Keep only last 1000 entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return metrics
    
    def _get_app_metrics(self) -> Dict:
        """Get application-level metrics."""
        try:
            return {
                'uptime_seconds': time.time() - getattr(current_app, 'start_time', time.time()),
                'environment': os.environ.get('FLASK_ENV', 'production'),
                'version': '1.0.0',
                'debug_mode': current_app.debug,
                'config_loaded': bool(current_app.config)
            }
        except Exception as e:
            current_app.logger.error(f"Error collecting app metrics: {e}")
            return {}
    
    def _get_database_metrics(self) -> Dict:
        """Get database performance metrics."""
        try:
            start_time = time.time()
            
            # Test database connectivity
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db_response_time = (time.time() - start_time) * 1000
            
            # Get connection pool stats
            pool_stats = {
                'pool_size': db.engine.pool.size(),
                'checked_out': db.engine.pool.checkedout(),
                'overflow': db.engine.pool.overflow(),
                'checked_in': db.engine.pool.checkedin()
            }
            
            # Get table row counts
            project_count = Project.query.count()
            activity_count = Activity.query.count()
            
            return {
                'response_time_ms': round(db_response_time, 2),
                'connection_pool': pool_stats,
                'table_counts': {
                    'projects': project_count,
                    'activities': activity_count
                },
                'status': 'healthy' if db_response_time < self.thresholds['database_response_ms'] else 'slow'
            }
        except Exception as e:
            current_app.logger.error(f"Error collecting database metrics: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_system_metrics(self) -> Dict:
        """Get system-level metrics."""
        try:
            # Try to get system metrics if psutil is available
            try:
                import psutil
                
                # Memory metrics
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                return {
                    'memory_usage_percent': round(memory.percent, 2),
                    'memory_available_mb': round(memory.available / 1024 / 1024, 2),
                    'disk_usage_percent': round(disk.percent, 2),
                    'disk_free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                    'cpu_count': psutil.cpu_count(),
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
                }
            except ImportError:
                # Fallback metrics without psutil
                return {
                    'memory_usage_percent': 0,
                    'disk_usage_percent': 0,
                    'note': 'psutil not available - limited system metrics'
                }
        except Exception as e:
            current_app.logger.error(f"Error collecting system metrics: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_business_metrics(self) -> Dict:
        """Get business-level metrics."""
        try:
            # Project metrics
            active_projects = Project.query.filter(Project.status == ProjectStatus.ACTIVE).count()
            completed_projects = Project.query.filter(Project.status == ProjectStatus.COMPLETED).count()
            total_projects = Project.query.count()
            
            # Activity metrics
            overdue_activities = Activity.query.filter(
                Activity.end_date < datetime.utcnow(),
                Activity.progress < 100
            ).count()
            
            # Calculate completion rates
            completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
            
            return {
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'total_projects': total_projects,
                'completion_rate_percent': round(completion_rate, 2),
                'overdue_activities': overdue_activities,
                'projects_created_today': Project.query.filter(
                    Project.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
                ).count()
            }
        except Exception as e:
            current_app.logger.error(f"Error collecting business metrics: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_alerts(self, metrics: Dict) -> List[Alert]:
        """Check metrics against thresholds and generate alerts."""
        new_alerts = []
        
        # Database response time alert
        db_response = metrics.get('database', {}).get('response_time_ms', 0)
        if db_response > self.thresholds['database_response_ms']:
            new_alerts.append(Alert(
                id=f"db_slow_{int(time.time())}",
                severity='high',
                title='Slow Database Response',
                message=f'Database response time: {db_response}ms (threshold: {self.thresholds["database_response_ms"]}ms)',
                timestamp=datetime.utcnow(),
                metadata={'response_time_ms': db_response}
            ))
        
        # Memory usage alert
        memory_usage = metrics.get('system', {}).get('memory_usage_percent', 0)
        if memory_usage > self.thresholds['memory_usage_percent']:
            severity = 'critical' if memory_usage > 90 else 'high'
            new_alerts.append(Alert(
                id=f"memory_high_{int(time.time())}",
                severity=severity,
                title='High Memory Usage',
                message=f'Memory usage: {memory_usage}% (threshold: {self.thresholds["memory_usage_percent"]}%)',
                timestamp=datetime.utcnow(),
                metadata={'memory_usage_percent': memory_usage}
            ))
        
        # Disk usage alert
        disk_usage = metrics.get('system', {}).get('disk_usage_percent', 0)
        if disk_usage > self.thresholds['disk_usage_percent']:
            severity = 'critical' if disk_usage > 95 else 'high'
            new_alerts.append(Alert(
                id=f"disk_high_{int(time.time())}",
                severity=severity,
                title='High Disk Usage',
                message=f'Disk usage: {disk_usage}% (threshold: {self.thresholds["disk_usage_percent"]}%)',
                timestamp=datetime.utcnow(),
                metadata={'disk_usage_percent': disk_usage}
            ))
        
        # Connection pool alert
        pool_stats = metrics.get('database', {}).get('connection_pool', {})
        checked_out = pool_stats.get('checked_out', 0)
        pool_size = pool_stats.get('pool_size', 1)
        pool_usage = (checked_out / pool_size * 100) if pool_size > 0 else 0
        
        if pool_usage > self.thresholds['active_connections']:
            new_alerts.append(Alert(
                id=f"pool_high_{int(time.time())}",
                severity='high',
                title='High Database Connection Usage',
                message=f'Connection pool usage: {pool_usage:.1f}% ({checked_out}/{pool_size})',
                timestamp=datetime.utcnow(),
                metadata={'pool_usage_percent': pool_usage}
            ))
        
        # Business metric alerts
        overdue_activities = metrics.get('business', {}).get('overdue_activities', 0)
        if overdue_activities > 10:
            severity = 'critical' if overdue_activities > 50 else 'medium'
            new_alerts.append(Alert(
                id=f"overdue_activities_{int(time.time())}",
                severity=severity,
                title='High Number of Overdue Activities',
                message=f'{overdue_activities} activities are overdue',
                timestamp=datetime.utcnow(),
                metadata={'overdue_count': overdue_activities}
            ))
        
        # Add new alerts to the list
        self.alerts.extend(new_alerts)
        
        # Clean up old resolved alerts (keep last 100)
        self.alerts = self.alerts[-100:]
        
        return new_alerts
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                return True
        return False
    
    def get_metrics_summary(self, hours: int = 24) -> Dict:
        """Get metrics summary for the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # Calculate averages
        avg_db_response = sum(
            m.get('database', {}).get('response_time_ms', 0)
            for m in recent_metrics
        ) / len(recent_metrics)
        
        avg_memory_usage = sum(
            m.get('system', {}).get('memory_usage_percent', 0)
            for m in recent_metrics
        ) / len(recent_metrics)
        
        return {
            'time_period_hours': hours,
            'data_points': len(recent_metrics),
            'averages': {
                'database_response_ms': round(avg_db_response, 2),
                'memory_usage_percent': round(avg_memory_usage, 2)
            },
            'alerts_generated': len([a for a in self.alerts if a.timestamp > cutoff_time])
        }
    
    def export_metrics(self, filename: str = None) -> str:
        """Export metrics to JSON file."""
        if not filename:
            filename = f"metrics_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'metrics_history': self.metrics_history,
            'alerts': [
                {
                    'id': alert.id,
                    'severity': alert.severity,
                    'title': alert.title,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'resolved': alert.resolved,
                    'metadata': alert.metadata
                }
                for alert in self.alerts
            ]
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            return filename
        except Exception as e:
            current_app.logger.error(f"Error exporting metrics: {e}")
            return None

# Global monitoring instance
monitoring_service = MonitoringService()

def start_monitoring():
    """Start the monitoring service."""
    try:
        # Initial metrics collection without current_app dependency
        monitoring_service.collect_metrics()
        return monitoring_service
    except Exception as e:
        print(f"Warning: Monitoring service failed to start: {e}")
        return monitoring_service