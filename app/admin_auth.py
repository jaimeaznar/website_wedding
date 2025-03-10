# app/admin_auth.py
import os
from werkzeug.security import generate_password_hash

# Use environment variable for admin password if available
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'your-secure-password')
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

# Note: In production, you should set the ADMIN_PASSWORD environment variable
# and not rely on the hardcoded fallback