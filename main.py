"""
BBSchedule Application Entry Point
Production-ready construction project scheduling platform
"""

import os
import logging
from app import app

# Configure production logging
if not app.debug:
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = logging.FileHandler('logs/bbschedule.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('BBSchedule startup')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
