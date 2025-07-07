"""
Configuration module for the Construction Project Scheduler application.
"""
import os
import logging
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Security configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    
    # File upload configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {
        'documents': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'dwg', 'jpg', 'jpeg', 'png'],
        'schedules': ['xer', 'xml', 'mpp']
    }
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Application settings
    ITEMS_PER_PAGE = 20
    DEFAULT_TIMEZONE = 'UTC'
    
    # Logging configuration
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'app.log'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = logging.DEBUG

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = logging.WARNING

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}