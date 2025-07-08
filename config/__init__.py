"""
Configuration module for BBSchedule
"""

import os
from .production import ProductionConfig

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'production')
    
    if env == 'production':
        return ProductionConfig
    else:
        return ProductionConfig  # Default to production config

__all__ = ['get_config', 'ProductionConfig']