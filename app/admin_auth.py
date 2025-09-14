# app/admin_auth.py
"""
Admin authentication module.
Handles password verification for admin panel access.
"""

import os
from werkzeug.security import check_password_hash, generate_password_hash
from flask import current_app

# Cache for the hashed password to avoid re-hashing on every check
_password_hash_cache = None

def get_admin_password_hash():
    """
    Get or generate admin password hash from configuration.
    Uses caching to avoid re-hashing the same password multiple times.
    
    Returns:
        str: The hashed password for comparison
    """
    global _password_hash_cache
    
    if _password_hash_cache:
        return _password_hash_cache
    
    # Check if we have a pre-hashed password in config (for backward compatibility)
    if current_app.config.get('ADMIN_PASSWORD_HASH'):
        _password_hash_cache = current_app.config.get('ADMIN_PASSWORD_HASH')
        return _password_hash_cache
    
    # Get the plain password from config
    admin_password = current_app.config.get('ADMIN_PASSWORD')
    if not admin_password:
        current_app.logger.error("No admin password configured!")
        raise ValueError("Admin password not configured. Check your .env file.")
    
    # Generate hash from plain password
    # Using pbkdf2:sha256 for compatibility
    _password_hash_cache = generate_password_hash(
        admin_password, 
        method='pbkdf2:sha256'
    )
    
    return _password_hash_cache

def verify_admin_password(password):
    """
    Verify a password against the admin password.
    
    Args:
        password (str): The password to verify
        
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        password_hash = get_admin_password_hash()
        return check_password_hash(password_hash, password)
    except Exception as e:
        current_app.logger.error(f"Error verifying admin password: {str(e)}")
        return False

def reset_password_cache():
    """
    Reset the password hash cache.
    Useful for testing or when changing passwords at runtime.
    """
    global _password_hash_cache
    _password_hash_cache = None