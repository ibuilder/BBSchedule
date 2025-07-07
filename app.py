"""
Main application factory and configuration.
"""
import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from config import config
from extensions import db
from logger import setup_logging

def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Set up proxy fix for production
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    
    # Set up logging
    setup_logging(app)
    
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