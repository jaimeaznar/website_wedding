# app/admin_auth.py
import os
from werkzeug.security import generate_password_hash
from flask import current_app

# Use environment variable for admin password if available, or use the default for testing
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'your-secure-password')
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

# Function to get admin password hash from config or generate it
def get_admin_password_hash():
    if current_app and current_app.config.get('ADMIN_PASSWORD_HASH'):
        return current_app.config.get('ADMIN_PASSWORD_HASH')
    return ADMIN_PASSWORD_HASH

# Note: In production, you should set the ADMIN_PASSWORD environment variable
# and not rely on the hardcoded fallback