"""
Health check endpoints for production monitoring
"""
import os
import time
from datetime import datetime
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text
try:
    from extensions import db
except ImportError:
    db = None
try:
    from models import Project, Activity
except ImportError:
    Project = Activity = None

health_bp = Blueprint('health', __name__, url_prefix='/health')

@health_bp.route('/ping')
def ping():
    """Simple ping endpoint for load balancer health checks."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'BBSchedule Construction Scheduler'
    })

@health_bp.route('/ready')
def ready():
    """Readiness check - application is ready to serve traffic."""
    try:
        # Check database connectivity
        start_time = time.time()
        db.session.execute(text('SELECT 1'))
        db_response_time = time.time() - start_time
        
        # Check basic data integrity (avoid enum issues)
        project_count = db.session.execute(text('SELECT COUNT(*) FROM projects')).scalar()
        activity_count = db.session.execute(text('SELECT COUNT(*) FROM activities')).scalar()
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'database': {
                    'status': 'healthy',
                    'response_time_ms': round(db_response_time * 1000, 2)
                },
                'data_integrity': {
                    'status': 'healthy',
                    'project_count': project_count,
                    'activity_count': activity_count
                }
            }
        })
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@health_bp.route('/live')
def live():
    """Liveness check - application is running."""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime': time.time() - current_app.start_time if hasattr(current_app, 'start_time') else 0
    })

@health_bp.route('/metrics')
def metrics():
    """Basic application metrics for monitoring."""
    try:
        # Database metrics (avoid enum issues)
        db_start = time.time()
        project_count = db.session.execute(text('SELECT COUNT(*) FROM projects')).scalar()
        activity_count = db.session.execute(text('SELECT COUNT(*) FROM activities')).scalar()
        active_projects = db.session.execute(text("SELECT COUNT(*) FROM projects WHERE status = 'planning'")).scalar()
        completed_projects = db.session.execute(text("SELECT COUNT(*) FROM projects WHERE status = 'completed'")).scalar()
        db_response_time = time.time() - db_start
        
        # Application metrics
        app_start_time = getattr(current_app, 'start_time', time.time())
        uptime = time.time() - app_start_time
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'application': {
                'uptime_seconds': round(uptime, 2),
                'environment': os.environ.get('FLASK_ENV', 'production'),
                'version': '1.0.0'
            },
            'database': {
                'response_time_ms': round(db_response_time * 1000, 2),
                'connection_pool_size': db.engine.pool.size(),
                'connection_pool_checked_out': db.engine.pool.checkedout()
            },
            'data': {
                'total_projects': project_count,
                'total_activities': activity_count,
                'active_projects': active_projects,
                'completed_projects': completed_projects
            }
        })
    except Exception as e:
        current_app.logger.error(f"Metrics collection failed: {str(e)}")
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@health_bp.route('/status')
def status():
    """Comprehensive status check for detailed monitoring."""
    try:
        checks = {}
        overall_status = 'healthy'
        
        # Database check
        try:
            start_time = time.time()
            db.session.execute(text('SELECT version()'))
            db_response_time = time.time() - start_time
            checks['database'] = {
                'status': 'healthy',
                'response_time_ms': round(db_response_time * 1000, 2),
                'message': 'Database connection successful'
            }
        except Exception as e:
            checks['database'] = {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Database connection failed'
            }
            overall_status = 'unhealthy'
        
        # File system check
        try:
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            if os.path.exists(upload_folder) and os.access(upload_folder, os.W_OK):
                checks['filesystem'] = {
                    'status': 'healthy',
                    'upload_folder': upload_folder,
                    'writable': True
                }
            else:
                checks['filesystem'] = {
                    'status': 'warning',
                    'upload_folder': upload_folder,
                    'writable': False,
                    'message': 'Upload folder not writable'
                }
        except Exception as e:
            checks['filesystem'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_status = 'unhealthy'
        
        # Memory check (basic)
        try:
            import psutil
            memory_usage = psutil.virtual_memory().percent
            checks['memory'] = {
                'status': 'healthy' if memory_usage < 80 else 'warning',
                'usage_percent': memory_usage,
                'message': f'Memory usage: {memory_usage}%'
            }
            if memory_usage > 90:
                overall_status = 'warning'
        except ImportError:
            checks['memory'] = {
                'status': 'unknown',
                'message': 'psutil not available for memory monitoring'
            }
        
        return jsonify({
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        })
        
    except Exception as e:
        current_app.logger.error(f"Status check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500