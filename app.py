"""
BBSchedule Application Factory
Enterprise-grade construction project scheduling platform
"""
import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from config import get_config
from extensions import db
from logger import setup_logging
from core.middleware import SecurityMiddleware
from core.health import health_bp
from core.errors import register_error_handlers
from core.monitoring_legacy import start_monitoring

def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Set up proxy fix for production
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    
    # Set up logging
    setup_logging(app)
    
    # Initialize security middleware
    security = SecurityMiddleware(app)
    
    # Register health check blueprint
    app.register_blueprint(health_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Track application start time for metrics
    import time
    app.start_time = time.time()
    
    # Initialize monitoring service after app context is available
    with app.app_context():
        start_monitoring()
        app.logger.info("Monitoring service started")
    
    # Create database tables
    with app.app_context():
        import models  # noqa: F401
        db.create_all()
        app.logger.info("Database tables created successfully")
    
    return app

# Create application instance
app = create_app()

# Import routes after app is created
import routes  # noqa: F401
import routes_sop  # noqa: F401