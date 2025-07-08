"""
WSGI entry point for BBSchedule Enterprise
For production deployment with Gunicorn
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app import app
    
    # Configure for production
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        file_handler = RotatingFileHandler(
            'logs/bbschedule.log', 
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s %(threadName)s: %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('BBSchedule Enterprise started')

except Exception as e:
    print(f"Error starting application: {e}")
    # Create a minimal error app
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def error():
        return f"Application startup error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)