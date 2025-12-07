# app/security.py
"""Security utilities for the wedding website."""
from flask import request, abort, current_app
from functools import wraps
import time
from app.constants import HttpStatus, TimeLimit

# Simple rate limiting implementation (in-memory)
# Note: This resets on app restart and doesn't share across workers.
# For a wedding website with single-worker deployment, this is acceptable.
_rate_limit_storage = {}


def configure_security(app):
    """Configure security features for the application."""
    # Security headers can be configured here if needed
    pass


def rate_limit(max_requests=TimeLimit.RATE_LIMIT_MAX_REQUESTS, window=TimeLimit.RATE_LIMIT_WINDOW):
    """
    Simple rate limiting decorator.
    
    Limits requests to max_requests per window seconds per IP address.
    
    Args:
        max_requests: Maximum number of requests allowed in the window
        window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip rate limiting for testing
            if current_app.config.get('TESTING'):
                return f(*args, **kwargs)
            
            ip = request.remote_addr
            now = time.time()
            key = f"{ip}:{f.__name__}"
            
            # Get or create rate limit record for this IP + endpoint
            if key not in _rate_limit_storage:
                _rate_limit_storage[key] = {'count': 0, 'window_start': now}
            
            record = _rate_limit_storage[key]
            
            # Reset window if expired
            if now - record['window_start'] > window:
                record['count'] = 0
                record['window_start'] = now
            
            # Check if rate limit exceeded
            if record['count'] >= max_requests:
                current_app.logger.warning(
                    f"Rate limit exceeded for IP {ip} on {f.__name__}"
                )
                abort(HttpStatus.TOO_MANY_REQUESTS)
            
            # Increment counter and proceed
            record['count'] += 1
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def cleanup_rate_limit_storage():
    """
    Remove expired entries from rate limit storage.
    Call this periodically to prevent memory growth.
    """
    now = time.time()
    expired_keys = [
        key for key, record in _rate_limit_storage.items()
        if now - record['window_start'] > TimeLimit.RATE_LIMIT_WINDOW * 2
    ]
    for key in expired_keys:
        del _rate_limit_storage[key]