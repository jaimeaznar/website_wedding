# app/admin_auth.py
import os
from werkzeug.security import generate_password_hash
from flask import current_app

def get_admin_password_hash():
    """
    Get the admin password hash from environment variables or config.
    """
    # First priority: Get from environment variable
    env_hash = os.environ.get('ADMIN_PASSWORD_HASH')
    if env_hash:
        return env_hash
        
    # Second priority: Get the raw password from environment and hash it
    env_password = os.environ.get('ADMIN_PASSWORD')
    if env_password:
        return generate_password_hash(env_password)
        
    # Third priority: Get from app config
    if current_app and current_app.config.get('ADMIN_PASSWORD_HASH'):
        return current_app.config.get('ADMIN_PASSWORD_HASH')
        
    # If nothing found and we're not in production, use a dev password
    if current_app and (current_app.debug or current_app.testing):
        return generate_password_hash('development-password-do-not-use-in-production')
        
    # If we're in production and no password is configured, raise error
    raise ValueError("Admin password hash not configured")

# Note: In production, you should set the ADMIN_PASSWORD_HASH environment variable