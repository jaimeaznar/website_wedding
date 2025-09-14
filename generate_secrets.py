#!/usr/bin/env python3
"""
Generate secure secret keys and passwords for production use.
Run this script to generate secure values for your .env file.
"""

import secrets
import string
from werkzeug.security import generate_password_hash

def generate_secret_key(length=32):
    """Generate a secure secret key for Flask."""
    return secrets.token_hex(length)

def generate_password(length=16):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Avoid problematic characters in passwords
    alphabet = alphabet.replace('"', '').replace("'", '').replace('\\', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_admin_password_hash(password):
    """Generate a password hash for the admin password."""
    return generate_password_hash(password, method='pbkdf2:sha256')

def main():
    print("=" * 60)
    print("SECURE KEY GENERATOR FOR WEDDING WEBSITE")
    print("=" * 60)
    print("\n📋 Copy these values to your .env file:\n")
    
    # Generate Flask secret key
    secret_key = generate_secret_key()
    print(f"SECRET_KEY={secret_key}")
    
    # Generate admin password
    admin_password = generate_password()
    admin_hash = generate_admin_password_hash(admin_password)
    
    print(f"\n# Admin password (save this securely!)")
    print(f"ADMIN_PASSWORD={admin_password}")
    print(f"# Or use the hash directly (more secure):")
    print(f"ADMIN_PASSWORD_HASH={admin_hash}")
    
    # Generate email app password placeholder
    email_app_password = generate_password()
    print(f"\n# Example email app password (replace with your actual Gmail app password)")
    print(f"MAIL_PASSWORD={email_app_password}")
    
    # Generate API keys for future services
    print(f"\n# Optional: API keys for external services")
    print(f"SENDGRID_API_KEY=SG.{generate_secret_key(32)}")
    print(f"SENTRY_DSN=https://{generate_secret_key(16)}@sentry.io/project")
    
    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT SECURITY NOTES:")
    print("=" * 60)
    print("1. NEVER commit your .env file to version control")
    print("2. Save the admin password in a password manager")
    print("3. Use different values for production and development")
    print("4. For Gmail, use an app-specific password, not your regular password")
    print("5. Rotate these keys periodically for better security")
    print("=" * 60)

if __name__ == "__main__":
    main()