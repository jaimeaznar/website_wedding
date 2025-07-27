# app/security.py - UPDATED WITH CONSTANTS
from flask import request, abort, current_app
from functools import wraps
import time
from werkzeug.security import generate_password_hash, check_password_hash
import os
from app.constants import HttpStatus, TimeLimit, LogMessage

# Simple rate limiting implementation
request_history = {}

def configure_security(app):
    """Configure security features for the application."""
    pass
    # Security headers can be configured here if needed

# Rate limiting decorator
def rate_limit(max_requests=TimeLimit.RATE_LIMIT_MAX_REQUESTS, window=TimeLimit.RATE_LIMIT_WINDOW):
    """
    Limit requests to max_requests per window seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip rate limiting for testing
            if current_app.config.get('TESTING'):
                return f(*args, **kwargs)
                
            ip = request.remote_addr
            now = time.time()
            
            # Initialize or reset if needed
            if ip not in request_history:
                request_history[ip] = {'count': 0, 'reset_time': now + TimeLimit.CACHE_TIMEOUT}
            elif now > request_history[ip]['reset_time']:
                request_history[ip] = {'count': 0, 'reset_time': now + TimeLimit.CACHE_TIMEOUT}
            
            # Track request
            request_window = request_history.setdefault(ip, {}).setdefault(window, {'count': 0, 'start_time': now})
            
            # Reset window if needed
            if now - request_window['start_time'] > window:
                request_window['count'] = 0
                request_window['start_time'] = now
            
            # Check if rate limit exceeded
            if request_window['count'] >= max_requests:
                current_app.logger.warning(LogMessage.ERROR_GENERIC.format(
                    operation="Rate limit check",
                    error=f"Rate limit exceeded for IP: {ip}"
                ))
                abort(HttpStatus.TOO_MANY_REQUESTS)
            
            # Increment counter and proceed
            request_window['count'] += 1
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Get admin password hash (moved from admin_auth.py)
def get_admin_password_hash():
    """Get the admin password hash from environment or config."""
    admin_password = os.environ.get('ADMIN_PASSWORD', current_app.config.get('ADMIN_PASSWORD', 'changeme'))
    return generate_password_hash(admin_password)

def verify_admin_password(password):
    """Verify the admin password against the hash."""
    admin_password_hash = os.environ.get('ADMIN_PASSWORD_HASH', 
                                        current_app.config.get('ADMIN_PASSWORD_HASH'))
    
    # If no hash is stored, use the function to generate one from the raw password
    if not admin_password_hash:
        admin_password_hash = get_admin_password_hash()
    
    return check_password_hash(admin_password_hash, password)