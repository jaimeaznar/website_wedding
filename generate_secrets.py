#!/usr/bin/env python3
"""
Generate secure secret keys and passwords for production use.
Run this script to generate secure values for your .env file.
"""

import secrets
import string
import sys
from pathlib import Path
from werkzeug.security import generate_password_hash

def generate_secret_key(length=32):
    """
    Generate a secure secret key for Flask.
    
    Args:
        length: Number of bytes (will produce hex string of 2x length)
        
    Returns:
        Cryptographically secure hex string
    """
    return secrets.token_hex(length)

def generate_password(length=16, include_symbols=True):
    """
    Generate a secure random password.
    
    Args:
        length: Password length
        include_symbols: Whether to include special characters
        
    Returns:
        Secure random password
    """
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    
    # Build alphabet based on requirements
    alphabet = lowercase + uppercase + digits
    
    if include_symbols:
        # Use a subset of symbols that won't cause issues in configs
        safe_symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        alphabet += safe_symbols
    
    # Ensure password has at least one of each type
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits)
    ]
    
    if include_symbols:
        password.append(secrets.choice(safe_symbols))
    
    # Fill the rest of the password
    for _ in range(length - len(password)):
        password.append(secrets.choice(alphabet))
    
    # Shuffle the password to avoid predictable patterns
    password_list = list(password)
    for i in range(len(password_list) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_list[i], password_list[j] = password_list[j], password_list[i]
    
    return ''.join(password_list)

def generate_admin_password_hash(password):
    """Generate a password hash for the admin password."""
    return generate_password_hash(password, method='pbkdf2:sha256')

def check_env_file_exists():
    """Check if .env file already exists."""
    env_path = Path('.env')
    if env_path.exists():
        return True
    return False

def write_to_env_file(content, append=False):
    """
    Write or append content to .env file.
    
    Args:
        content: Content to write
        append: Whether to append or create new
    """
    mode = 'a' if append else 'w'
    with open('.env', mode) as f:
        if append:
            f.write('\n\n# Generated secure values\n')
        f.write(content)

def main():
    print("=" * 60)
    print("SECURE KEY GENERATOR FOR WEDDING WEBSITE")
    print("=" * 60)
    
    # Check if .env exists
    env_exists = check_env_file_exists()
    if env_exists:
        print("\n⚠️  .env file already exists!")
        print("Options:")
        print("1. Display new values to copy manually")
        print("2. Append to existing .env file")
        print("3. Create new .env.production file")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '4':
            print("Exiting...")
            sys.exit(0)
    else:
        choice = '1'  # Default to display if no .env exists
    
    # Generate values
    print("\n🔐 Generating secure values...")
    
    # Generate Flask secret key (64 bytes = 128 char hex string)
    secret_key = generate_secret_key(64)
    
    # Generate admin password (20 chars with symbols)
    admin_password = generate_password(20, include_symbols=True)
    admin_hash = generate_admin_password_hash(admin_password)
    
    # Generate email app password (16 chars, no symbols for compatibility)
    email_app_password = generate_password(16, include_symbols=False)
    
    # Generate API keys
    sendgrid_key = f"SG.{generate_secret_key(32)}"
    sentry_dsn = f"https://{generate_secret_key(16)}@sentry.io/project"
    
    # Build content
    env_content = f"""# ================================================
# SECURITY CONFIGURATION - KEEP THESE SECRET!
# Generated on: {__import__('datetime').datetime.now()}
# ================================================

# Flask Security (128 character hex string)
SECRET_KEY={secret_key}

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost/wedding_db

# Admin Authentication
ADMIN_PASSWORD={admin_password}
# Alternative: Use the hash directly (more secure)
# ADMIN_PASSWORD_HASH={admin_hash}

# Admin Contact Information
ADMIN_EMAIL=your-email@example.com
ADMIN_PHONE=123-456-7890

# Email Configuration (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD={email_app_password}

# Wedding Details
WEDDING_DATE=2026-06-06
RSVP_DEADLINE=2026-05-06

# Optional Services (uncomment if using)
# SENDGRID_API_KEY={sendgrid_key}
# SENTRY_DSN={sentry_dsn}

# Environment
FLASK_ENV=development  # Change to 'production' for production deployment
"""

    # Handle output based on choice
    if choice == '1' or not env_exists:
        print("\n" + "=" * 60)
        print("📋 Copy these values to your .env file:")
        print("=" * 60)
        print(env_content)
        
        print("\n" + "=" * 60)
        print("🔒 CRITICAL SECURITY INFORMATION:")
        print("=" * 60)
        print(f"Admin Password: {admin_password}")
        print("⚠️  Save this password in a secure password manager!")
        print("This is the only time it will be displayed.")
        
    elif choice == '2':
        # Append to existing
        write_to_env_file(env_content, append=True)
        print("\n✅ Values appended to .env file")
        print(f"\n🔒 Admin Password: {admin_password}")
        print("⚠️  Save this password securely!")
        
    elif choice == '3':
        # Create .env.production
        with open('.env.production', 'w') as f:
            f.write(env_content)
        print("\n✅ Created .env.production file")
        print(f"\n🔒 Admin Password: {admin_password}")
        print("⚠️  Save this password securely!")
    
    # Security reminders
    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT SECURITY NOTES:")
    print("=" * 60)
    print("1. NEVER commit .env files to version control")
    print("2. Add .env to .gitignore if not already there")
    print("3. Use different values for production and development")
    print("4. Store the admin password in a password manager")
    print("5. For Gmail, use an app-specific password, not your account password")
    print("6. Rotate keys periodically (every 3-6 months)")
    print("7. Use environment variables on your hosting platform")
    print("8. Enable 2FA on all service accounts (Gmail, Heroku, etc.)")
    print("=" * 60)
    
    # Check current environment
    print("\n📍 Current Configuration Tips:")
    print("-" * 60)
    
    flask_env = __import__('os').getenv('FLASK_ENV', 'not set')
    if flask_env == 'production':
        print("⚠️  You're in PRODUCTION mode - use strong values!")
    elif flask_env == 'development':
        print("ℹ️  You're in DEVELOPMENT mode")
    else:
        print("ℹ️  FLASK_ENV is not set - defaults to development")
    
    print("\n✅ Generation complete!")

if __name__ == "__main__":
    main()