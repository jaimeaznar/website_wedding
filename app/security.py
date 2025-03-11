# app/security.py
from flask import request, abort, current_app
from functools import wraps
import time
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Simple rate limiting implementation
request_history = {}
RATE_LIMIT_RESET_TIME = 3600  # 1 hour in seconds

def configure_security(app):
    """Configure security features for the application."""
    
    # Set security headers
    @app.after_request
    def add_security_headers(response):
        # Skip security headers for testing
        if app.config.get('TESTING'):
            return response
            
        # Content Security Policy
        response.headers['Content-Security-Policy'] = "default-src 'self'; \
            script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; \
            style-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com 'unsafe-inline'; \
            font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; \
            img-src 'self' data:; \
            frame-ancestors 'none'"
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Protect against clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS - only in production
        if not app.debug and not app.testing:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response

# Rate limiting decorator
def rate_limit(max_requests=20, window=60):
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
                request_history[ip] = {'count': 0, 'reset_time': now + RATE_LIMIT_RESET_TIME}
            elif now > request_history[ip]['reset_time']:
                request_history[ip] = {'count': 0, 'reset_time': now + RATE_LIMIT_RESET_TIME}
            
            # Track request
            request_window = request_history.setdefault(ip, {}).setdefault(window, {'count': 0, 'start_time': now})
            
            # Reset window if needed
            if now - request_window['start_time'] > window:
                request_window['count'] = 0
                request_window['start_time'] = now
            
            # Check if rate limit exceeded
            if request_window['count'] >= max_requests:
                current_app.logger.warning(f"Rate limit exceeded for IP: {ip}")
                abort(429)  # Too Many Requests
            
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