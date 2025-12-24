import os
import sys
import secrets
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
from app.constants import (
    Language, DEFAULT_CONFIG)

basedir = Path(__file__).parent.parent.absolute()
load_dotenv(basedir / '.env')

# List of known weak/default secret keys to reject
WEAK_SECRET_KEYS = [
    'your-secret-key-here',
    'change-this-secret-key',
    'dev-secret-key',
    'test-secret-key',
    'secret',
    'changeme',
    'your-secret-key-here-generate-a-new-one',
    'test-secret-key-for-testing-only'
]

# List of weak passwords to reject
WEAK_PASSWORDS = [
    'your-secure-password',
    'changeme',
    'password',
    'admin',
    'test-password',
    'your-admin-password'
]

def validate_secret_key(secret_key: str, is_production: bool = False) -> bool:
    """
    Validate that a secret key is secure enough.
    
    Args:
        secret_key: The secret key to validate
        is_production: Whether running in production (stricter validation)
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not secret_key:
        return False
    
    # Check against known weak keys
    if secret_key.lower() in [k.lower() for k in WEAK_SECRET_KEYS]:
        return False
    
    # Check minimum length (32 chars for production, 16 for dev)
    min_length = 32 if is_production else 16
    if len(secret_key) < min_length:
        return False
    
    # In production, ensure it looks like a proper random key
    if is_production:
        # Check if it has enough entropy (mix of chars)
        unique_chars = len(set(secret_key))
        if unique_chars < 10:  # Too few unique characters
            return False
    
    return True

def validate_admin_password(password: str, is_production: bool = False) -> bool:
    """
    Validate that an admin password is secure enough.
    
    Args:
        password: The password to validate
        is_production: Whether running in production (stricter validation)
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not password:
        return False
    
    # Check against known weak passwords
    if password.lower() in [p.lower() for p in WEAK_PASSWORDS]:
        return False
    
    # Check minimum length
    min_length = 12 if is_production else 8
    if len(password) < min_length:
        return False
    
    return True

def get_env_variable(var_name, default=None, required=False):
    """Get environment variable with validation."""
    value = os.getenv(var_name, default)
    if required and not value:
        print(f"❌ ERROR: Required environment variable '{var_name}' is not set!")
        print(f"   Please check your .env file or environment configuration.")
        print(f"   See ENVIRONMENT_SETUP.md for configuration instructions.")
        sys.exit(1)
    return value

class Config:
    """Base configuration class with security-first approach."""
    
    # ============================================
    # REQUIRED SECURITY CONFIGURATIONS
    # ============================================
    
    # Secret key for Flask sessions - MUST be set in production
    SECRET_KEY = get_env_variable('SECRET_KEY', required=True)
    
    # Database URL - MUST be set for the app to work
    database_url = get_env_variable('DATABASE_URL', required=True)
    # Handle Heroku's postgres:// to postgresql:// change
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Admin authentication - MUST be set
    ADMIN_PASSWORD = get_env_variable('ADMIN_PASSWORD', required=True)
    # Note: The app will hash this password automatically when comparing
    
    # ============================================
    # WEDDING CONFIGURATION
    # ============================================
    
    ADMIN_EMAIL = get_env_variable('ADMIN_EMAIL', required=True)
    ADMIN_PHONE = get_env_variable('ADMIN_PHONE', required=True)
    WEDDING_DATE = get_env_variable('WEDDING_DATE', DEFAULT_CONFIG['WEDDING_DATE'])
    RSVP_DEADLINE = get_env_variable('RSVP_DEADLINE', DEFAULT_CONFIG['RSVP_DEADLINE'])
    
    # Reminder and warning settings
    REMINDER_DAYS_BEFORE = int(get_env_variable(
        'REMINDER_DAYS_BEFORE', 
        str(DEFAULT_CONFIG['REMINDER_DAYS_BEFORE'])
    ))
    WARNING_MESSAGE_TIMEOUT = int(get_env_variable(
        'WARNING_MESSAGE_TIMEOUT', 
        str(DEFAULT_CONFIG['WARNING_MESSAGE_TIMEOUT'])
    ))
    WARNING_CUTOFF_DAYS = int(get_env_variable(
        'WARNING_CUTOFF_DAYS', 
        str(DEFAULT_CONFIG['WARNING_CUTOFF_DAYS'])
    ))
    
    # ============================================
    # APPLICATION SETTINGS
    # ============================================
    
    # Language settings
    LANGUAGES = Language.SUPPORTED
    BABEL_DEFAULT_LOCALE = Language.DEFAULT
    
    # Session configuration
    SESSION_COOKIE_SECURE = get_env_variable('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    
    # ============================================
    # OPTIONAL EXTERNAL SERVICES
    # ============================================
    
    # Error tracking with Sentry (optional)
    SENTRY_DSN = get_env_variable('SENTRY_DSN')
    
    # SendGrid API (optional, for production email)
    SENDGRID_API_KEY = get_env_variable('SENDGRID_API_KEY')
    
    # Cloudflare API (optional, for CDN)
    CLOUDFLARE_API_KEY = get_env_variable('CLOUDFLARE_API_KEY')
    
    # ============================================
    # ENVIRONMENT-SPECIFIC SETTINGS
    # ============================================
    
    @property
    def is_production(self):
        """Check if running in production."""
        flask_env = get_env_variable('FLASK_ENV', 'development')
        return flask_env.lower() == 'production'
    
    def __init__(self):
        """Validate configuration on initialization."""
        # Validate SECRET_KEY
        if not validate_secret_key(self.SECRET_KEY, self.is_production):
            if self.is_production:
                print("❌ ERROR: SECRET_KEY is not secure enough for production!")
                print("   - Must be at least 32 characters long")
                print("   - Must not be a known default value")
                print("   - Must have sufficient entropy")
                print("\n   Generate a secure key with: python generate_secrets.py")
                sys.exit(1)
            else:
                print("⚠️  WARNING: Using weak SECRET_KEY in development.")
                print("   For production, generate a secure key with: python generate_secrets.py")
        
        # Validate ADMIN_PASSWORD
        if not validate_admin_password(self.ADMIN_PASSWORD, self.is_production):
            if self.is_production:
                print("❌ ERROR: ADMIN_PASSWORD is not secure enough for production!")
                print("   - Must be at least 12 characters long")
                print("   - Must not be a known default value")
                print("\n   Generate a secure password with: python generate_secrets.py")
                sys.exit(1)
            else:
                print("⚠️  WARNING: Using weak ADMIN_PASSWORD in development.")
        
        # Additional production validations
        if self.is_production:
            # Ensure HTTPS in production
            self.SESSION_COOKIE_SECURE = True
            print("✅ Production configuration validated")
        else:
            print("✅ Development configuration loaded")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    
    def __init__(self):
        # Skip production-level validation for development
        # But still validate basic requirements
        super().__init__()
        self.SESSION_COOKIE_SECURE = False  # Allow HTTP in development


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    def __init__(self):
        super().__init__()
        # Production-specific settings
        self.SESSION_COOKIE_SECURE = True
        self.WTF_CSRF_ENABLED = True
        
        # Additional production validations
        if not self.MAIL_USERNAME or not self.MAIL_PASSWORD:
            print("⚠️  WARNING: Email not configured properly for production!")
            print("   Invitations and confirmations will not be sent.")
        
        # Ensure we're not using any development values
        if 'localhost' in self.SQLALCHEMY_DATABASE_URI or '127.0.0.1' in self.SQLALCHEMY_DATABASE_URI:
            print("⚠️  WARNING: Using local database in production!")


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    DEBUG = True
    
    def __init__(self):
        # For testing, we don't require environment variables
        pass
    
    # Override with test values
    SECRET_KEY = 'test-secret-key-for-automated-testing-only'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    ADMIN_PASSWORD = 'test-password'
    ADMIN_EMAIL = 'test@test.com'
    ADMIN_PHONE = '555-TEST'
    
    # Use defaults for other values
    WEDDING_DATE = DEFAULT_CONFIG['WEDDING_DATE']
    RSVP_DEADLINE = DEFAULT_CONFIG['RSVP_DEADLINE']


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment."""
    env = get_env_variable('FLASK_ENV', 'development')
    return config.get(env, config['default'])