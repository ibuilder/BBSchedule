"""
Production configuration for BBSchedule Enterprise
"""

import os
from datetime import timedelta

class ProductionConfig:
    """Production configuration settings"""
    
    # Application
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 20,
        'max_overflow': 30,
        'pool_timeout': 30,
        'echo': False
    }
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Enterprise Security
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    DATA_ENCRYPTION_KEY = os.environ.get('DATA_ENCRYPTION_KEY')
    
    # File Upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = 'uploads'
    UPLOAD_EXTENSIONS = {
        'documents': ['pdf', 'doc', 'docx', 'xls', 'xlsx'],
        'schedules': ['xer', 'xml', 'mpp', 'p6xml'],
        'images': ['jpg', 'jpeg', 'png', 'gif'],
        'cad': ['dwg', 'dxf', 'dgn']
    }
    
    # Caching
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/production.log'
    
    # Monitoring
    METRICS_RETENTION_HOURS = 24 * 30  # 30 days
    HEALTH_CHECK_INTERVAL = 30
    
    # Compliance
    AUDIT_RETENTION_DAYS = 2555  # 7 years for SOX
    DATA_RETENTION_DAYS = 2190   # 6 years
    
    # External Integrations
    EXTERNAL_API_TIMEOUT = 30
    EXTERNAL_API_RETRY_COUNT = 3
    
    # Performance
    SEND_FILE_MAX_AGE_DEFAULT = 86400  # 24 hours