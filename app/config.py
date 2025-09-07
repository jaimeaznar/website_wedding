import os
import sys
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
from app.constants import (
    Language, DEFAULT_CONFIG, TimeLimit, DateFormat
)

basedir = Path(__file__).parent.parent.absolute()
load_dotenv(basedir / '.env')

# Validation function for required environment variables
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
    # EMAIL CONFIGURATION
    # ============================================
    
    MAIL_SERVER = get_env_variable('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(get_env_variable('MAIL_PORT', '587'))
    MAIL_USE_TLS = get_env_variable('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = get_env_variable('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = get_env_variable('MAIL_USERNAME')
    MAIL_PASSWORD = get_env_variable('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = get_env_variable('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
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
        if self.is_production:
            # Additional production checks
            if 'your-secret-key' in self.SECRET_KEY.lower():
                print("❌ ERROR: Using default SECRET_KEY in production!")
                sys.exit(1)
            if 'your-secure-password' in self.ADMIN_PASSWORD.lower():
                print("❌ ERROR: Using default ADMIN_PASSWORD in production!")
                sys.exit(1)
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
        super().__init__()
        # Development-specific overrides
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
        
        # Ensure email is configured for production
        if not self.MAIL_USERNAME or not self.MAIL_PASSWORD:
            print("⚠️  WARNING: Email not configured properly for production!")


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    DEBUG = True
    
    def __init__(self):
        # For testing, we don't require environment variables
        pass
    
    # Override with test values
    SECRET_KEY = 'test-secret-key'
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