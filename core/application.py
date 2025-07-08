"""
Enterprise initialization and configuration for BBSchedule
"""

import os
import logging
from flask import Flask
from datetime import timedelta

# Import core modules
from .security import (
    enterprise_auth, rbac, audit_logger, data_encryption, 
    security_middleware, EnterpriseCompliance
)
from .monitoring import init_enterprise_monitoring
from .scalability import init_enterprise_scalability
from .integrations import init_enterprise_integrations
from .compliance import init_enterprise_compliance

# Enterprise logging setup
def setup_enterprise_logging():
    """Setup enterprise-grade logging configuration"""
    
    # Create enterprise log formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - '
        '%(funcName)s() - %(message)s'
    )
    
    security_formatter = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
    )
    
    audit_formatter = logging.Formatter(
        '%(asctime)s - AUDIT - %(message)s'
    )
    
    # Setup file handlers with rotation
    from logging.handlers import RotatingFileHandler
    
    # Application logs
    app_handler = RotatingFileHandler(
        'logs/application.log', 
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    app_handler.setFormatter(detailed_formatter)
    app_handler.setLevel(logging.INFO)
    
    # Security logs
    security_handler = RotatingFileHandler(
        'logs/security.log', 
        maxBytes=10485760,
        backupCount=20  # Keep more security logs
    )
    security_handler.setFormatter(security_formatter)
    security_handler.setLevel(logging.WARNING)
    
    # Audit logs
    audit_handler = RotatingFileHandler(
        'logs/audit.log', 
        maxBytes=10485760,
        backupCount=50  # Keep many audit logs for compliance
    )
    audit_handler.setFormatter(audit_formatter)
    audit_handler.setLevel(logging.INFO)
    
    # Compliance logs
    compliance_handler = RotatingFileHandler(
        'logs/compliance.log', 
        maxBytes=10485760,
        backupCount=100  # Long retention for compliance
    )
    compliance_handler.setFormatter(detailed_formatter)
    compliance_handler.setLevel(logging.INFO)
    
    # Configure loggers
    loggers = {
        'app': logging.getLogger('app'),
        'security': logging.getLogger('security'),
        'audit': logging.getLogger('audit'),
        'compliance': logging.getLogger('compliance'),
        'performance': logging.getLogger('performance'),
        'integration': logging.getLogger('integration'),
        'metrics': logging.getLogger('metrics')
    }
    
    # Set log levels based on environment
    log_level = logging.DEBUG if os.environ.get('DEBUG') == 'True' else logging.INFO
    
    for logger_name, logger in loggers.items():
        logger.setLevel(log_level)
        
        # Add appropriate handlers
        if logger_name == 'security':
            logger.addHandler(security_handler)
        elif logger_name == 'audit':
            logger.addHandler(audit_handler)
        elif logger_name == 'compliance':
            logger.addHandler(compliance_handler)
        else:
            logger.addHandler(app_handler)
        
        # Prevent duplicate logs
        logger.propagate = False
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logging.getLogger('enterprise').info("Enterprise logging configured")

class EnterpriseConfig:
    """Enterprise configuration settings"""
    
    # Security Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', os.urandom(32).hex())
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    DATA_ENCRYPTION_KEY = os.environ.get('DATA_ENCRYPTION_KEY')
    
    # Session Configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # Database Configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 20,
        'max_overflow': 30,
        'pool_timeout': 30,
        'echo': False  # Disable in production
    }
    
    # File Upload Security
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB for enterprise files
    UPLOAD_EXTENSIONS = {
        'documents': ['pdf', 'doc', 'docx', 'xls', 'xlsx'],
        'schedules': ['xer', 'xml', 'mpp', 'p6xml'],
        'images': ['jpg', 'jpeg', 'png', 'gif'],
        'cad': ['dwg', 'dxf', 'dgn']
    }
    
    # Compliance Configuration
    AUDIT_RETENTION_DAYS = 2555  # 7 years for SOX
    DATA_RETENTION_DAYS = 2190   # 6 years default
    BACKUP_RETENTION_DAYS = 365  # 1 year for backups
    
    # Integration Configuration
    EXTERNAL_API_TIMEOUT = 30
    EXTERNAL_API_RETRY_COUNT = 3
    WEBHOOK_SECRET_LENGTH = 32
    
    # Monitoring Configuration
    METRICS_RETENTION_HOURS = 24 * 30  # 30 days
    HEALTH_CHECK_INTERVAL = 30  # seconds
    ALERT_THRESHOLDS = {
        'response_time_critical': 5.0,
        'memory_usage_critical': 95.0,
        'cpu_usage_critical': 90.0,
        'error_rate_critical': 10.0
    }

def create_enterprise_app(config_name='production'):
    """Create Flask app with enterprise features"""
    
    # Setup enterprise logging first
    setup_enterprise_logging()
    
    app = Flask(__name__)
    
    # Load enterprise configuration
    app.config.from_object(EnterpriseConfig)
    
    # Initialize core components
    from extensions import db
    db.init_app(app)
    
    # Initialize enterprise security
    enterprise_auth.init_app(app)
    security_middleware.init_app(app)
    
    # Initialize enterprise monitoring
    monitoring_components = init_enterprise_monitoring(app)
    app.monitoring = monitoring_components
    
    # Initialize enterprise scalability
    scalability_components = init_enterprise_scalability(app, monitoring_components['metrics_collector'])
    app.scalability = scalability_components
    
    # Initialize enterprise integrations
    integration_components = init_enterprise_integrations(app)
    app.integrations = integration_components
    
    # Initialize enterprise compliance
    compliance_components = init_enterprise_compliance(app)
    app.compliance = compliance_components
    
    # Register enterprise blueprints
    register_enterprise_blueprints(app)
    
    # Setup enterprise error handlers
    setup_enterprise_error_handlers(app)
    
    logging.getLogger('enterprise').info("Enterprise application initialized successfully")
    
    return app

def register_enterprise_blueprints(app):
    """Register enterprise-specific blueprints"""
    
    from flask import Blueprint, jsonify, request
    from enterprise_security import require_api_key
    from enterprise_monitoring import metrics_collector, health_checker
    
    # Enterprise API Blueprint
    enterprise_api = Blueprint('enterprise_api', __name__, url_prefix='/api/enterprise')
    
    @enterprise_api.route('/health/detailed')
    @require_api_key(['system.health'])
    def detailed_health():
        """Detailed health check for enterprise monitoring"""
        health_status = health_checker.get_overall_health()
        return jsonify(health_status)
    
    @enterprise_api.route('/metrics/summary')
    @require_api_key(['system.metrics'])
    def metrics_summary():
        """Get enterprise metrics summary"""
        summary = metrics_collector.get_metrics_summary()
        return jsonify(summary)
    
    @enterprise_api.route('/compliance/audit')
    @require_api_key(['compliance.audit'])
    def compliance_audit():
        """Get compliance audit information"""
        from datetime import datetime, timedelta
        
        # Get audit data for last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        audit_report = app.compliance['audit_trail'].get_audit_report(start_date, end_date)
        
        return jsonify({
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'total_events': len(audit_report),
            'events': audit_report[:100]  # Limit to first 100 events
        })
    
    @enterprise_api.route('/integrations/status')
    @require_api_key(['integrations.read'])
    def integration_status():
        """Get status of external integrations"""
        status = {}
        
        if hasattr(app, 'integrations') and app.integrations:
            for name, integration in app.integrations['integrations'].items():
                try:
                    # Test integration connectivity
                    if hasattr(integration, '_ensure_authenticated'):
                        auth_status = integration._ensure_authenticated()
                        status[name] = 'connected' if auth_status else 'disconnected'
                    else:
                        status[name] = 'unknown'
                except Exception as e:
                    status[name] = f'error: {str(e)}'
        
        return jsonify(status)
    
    # Security API Blueprint
    security_api = Blueprint('security_api', __name__, url_prefix='/api/security')
    
    @security_api.route('/generate-api-key', methods=['POST'])
    @require_api_key(['security.api_keys'])
    def generate_api_key():
        """Generate new API key for external systems"""
        data = request.get_json()
        
        client_name = data.get('client_name')
        permissions = data.get('permissions', [])
        
        if not client_name:
            return jsonify({'error': 'client_name required'}), 400
        
        api_key = app.integrations['api_gateway'].generate_api_key(client_name, permissions)
        
        return jsonify({
            'api_key': api_key,
            'client_name': client_name,
            'permissions': permissions,
            'expires_in': '365 days'
        })
    
    # Register blueprints
    app.register_blueprint(enterprise_api)
    app.register_blueprint(security_api)

def setup_enterprise_error_handlers(app):
    """Setup enterprise error handling"""
    
    @app.errorhandler(429)
    def rate_limit_error(error):
        """Handle rate limit errors"""
        logging.getLogger('security').warning(f"Rate limit exceeded: {request.remote_addr}")
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'retry_after': getattr(error, 'retry_after', 60)
        }), 429
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle forbidden access"""
        logging.getLogger('security').warning(f"Forbidden access attempt: {request.remote_addr}")
        return jsonify({
            'error': 'Access forbidden',
            'message': 'Insufficient permissions for this resource'
        }), 403
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        """Handle unauthorized access"""
        logging.getLogger('security').warning(f"Unauthorized access attempt: {request.remote_addr}")
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Valid authentication required'
        }), 401

def configure_enterprise_database(app):
    """Configure database for enterprise use"""
    
    with app.app_context():
        from extensions import db
        from enterprise_scalability import QueryOptimizer
        
        # Create enterprise indexes
        optimizer = QueryOptimizer()
        optimizations = optimizer.optimize_project_queries()
        
        try:
            for sql in optimizations:
                db.session.execute(sql)
            db.session.commit()
            logging.getLogger('enterprise').info("Enterprise database optimizations applied")
        except Exception as e:
            logging.getLogger('enterprise').warning(f"Database optimization failed: {e}")
            db.session.rollback()

def setup_enterprise_monitoring_endpoints(app):
    """Setup additional monitoring endpoints"""
    
    @app.route('/metrics/prometheus')
    def prometheus_metrics():
        """Prometheus-compatible metrics endpoint"""
        metrics = app.monitoring['metrics_collector'].get_metrics_summary()
        
        # Convert to Prometheus format
        prometheus_output = []
        for metric_name, data in metrics.items():
            prometheus_output.append(f"# TYPE {metric_name} gauge")
            prometheus_output.append(f"{metric_name} {data['current']}")
        
        return '\n'.join(prometheus_output), 200, {'Content-Type': 'text/plain'}
    
    @app.route('/health/ready')
    def readiness_probe():
        """Kubernetes readiness probe"""
        health = app.monitoring['health_checker'].get_overall_health()
        
        if health['overall_status'] == 'healthy':
            return jsonify({'status': 'ready'}), 200
        else:
            return jsonify({'status': 'not_ready', 'details': health}), 503
    
    @app.route('/health/live')
    def liveness_probe():
        """Kubernetes liveness probe"""
        return jsonify({'status': 'alive', 'timestamp': datetime.utcnow().isoformat()}), 200

# Enterprise feature flags
ENTERPRISE_FEATURES = {
    'ADVANCED_SECURITY': True,
    'COMPLIANCE_MONITORING': True,
    'EXTERNAL_INTEGRATIONS': True,
    'ADVANCED_ANALYTICS': True,
    'AUTO_SCALING': True,
    'AUDIT_LOGGING': True,
    'DATA_ENCRYPTION': True,
    'ROLE_BASED_ACCESS': True,
    'API_RATE_LIMITING': True,
    'ENTERPRISE_SSO': False,  # Requires additional configuration
    'DISASTER_RECOVERY': False,  # Requires additional infrastructure
    'MULTI_TENANT': False  # Requires schema changes
}

def is_feature_enabled(feature_name: str) -> bool:
    """Check if enterprise feature is enabled"""
    return ENTERPRISE_FEATURES.get(feature_name, False)

# Export main initialization function
__all__ = ['create_enterprise_app', 'EnterpriseConfig', 'is_feature_enabled']