# app/error_handlers.py
from flask import render_template, request
import logging
from werkzeug.exceptions import HTTPException
import traceback

# Configure logger for application errors
logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Register error handlers for the app."""
    
    @app.errorhandler(404)
    def page_not_found(e):
        logger.info(f"404 error: {request.path}")
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        logger.warning(f"403 error for {request.path} from IP {request.remote_addr}")
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_server_error(e):
        error_traceback = traceback.format_exc()
        logger.error(f"500 error: {str(e)}\n{error_traceback}")
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Pass through HTTP errors
        if isinstance(e, HTTPException):
            return e
        
        # Log unhandled exceptions
        error_traceback = traceback.format_exc()
        logger.critical(f"Unhandled exception: {str(e)}\n{error_traceback}")
        
        # Return generic 500 error page
        return render_template('errors/500.html'), 500