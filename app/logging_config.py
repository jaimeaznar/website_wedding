# app/logging_config.py
import os
import logging
from logging.handlers import RotatingFileHandler
import time

def configure_logging(app):
    """Configure logging for the application."""
    
    # Set up logging based on environment
    if app.debug:
        # In development, log to console with more details
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        # In production, log to file with rotation
        log_dir = os.path.join(app.root_path, '../logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = time.strftime('%Y%m%d')
        log_file = os.path.join(log_dir, f'wedding_app_{timestamp}.log')
        
        # Configure file handler with rotation (10MB max size, keep 10 backups)
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10485760, 
            backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        
        # Add handler to root logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        
    app.logger.info('Wedding application startup')