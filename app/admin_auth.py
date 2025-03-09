# app/admin_auth.py
from werkzeug.security import generate_password_hash

# Generate a hash for your admin password
ADMIN_PASSWORD = "your-secure-password"  # Change this
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)