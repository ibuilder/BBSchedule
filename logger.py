"""
Logging configuration and utilities.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(app):
    """Set up application logging."""
    
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Set up file handler with rotation
        file_handler = RotatingFileHandler(
            'logs/construction_scheduler.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Set up console handler for production
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        app.logger.addHandler(console_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Construction Project Scheduler startup')

def log_error(error, context=None):
    """Log error with optional context."""
    error_msg = f"Error: {str(error)}"
    if context:
        error_msg += f" | Context: {context}"
    
    logging.error(error_msg, exc_info=True)

def log_activity(user_id, action, details=None):
    """Log user activity."""
    activity_msg = f"User {user_id}: {action}"
    if details:
        activity_msg += f" | Details: {details}"
    
    logging.info(activity_msg)

def log_performance(function_name, execution_time, additional_info=None):
    """Log performance metrics."""
    perf_msg = f"Performance - {function_name}: {execution_time:.3f}s"
    if additional_info:
        perf_msg += f" | {additional_info}"
    
    logging.info(perf_msg)