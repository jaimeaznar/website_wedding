import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Basic Flask config
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Database - directly specify the URL
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://jaimeaznar@localhost/wedding_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Languages
    LANGUAGES = ['en', 'es']
    BABEL_DEFAULT_LOCALE = 'en'
    
    # Custom config
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'your@email.com')
    ADMIN_PHONE = os.getenv('ADMIN_PHONE', '123456789')
    RSVP_DEADLINE = os.getenv('RSVP_DEADLINE', '2026-05-06')  # Default 1 month before wedding
    WEDDING_DATE = os.getenv('WEDDING_DATE', '2026-06-06')
    REMINDER_DAYS_BEFORE = 30  # Send reminder 30 days before deadline
    WARNING_MESSAGE_TIMEOUT = 0  # 0 means no auto-dismiss
    WARNING_CUTOFF_DAYS = 7     # days before wedding for warnings
    
    # For tests - set a default admin password hash
    ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', 'pbkdf2:sha256:600000$MlXi8Xcgp3y5$d17a4d3dce0a3d5be306beb47fddee0fc7d8c6ba51f7a9c7ea3e4fea4f33ad01')

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # Make sure CSRF is explicitly disabled
    WTF_CSRF_CHECK_DEFAULT = False  # Double-check with another setting
    SECRET_KEY = 'test-secret-key'
    WEDDING_DATE = '2026-06-06'
    RSVP_DEADLINE = '2026-05-06'  # 1 month before wedding
    # Set accessible admin password for tests
    ADMIN_PASSWORD_HASH = 'pbkdf2:sha256:600000$MlXi8Xcgp3y5$d17a4d3dce0a3d5be306beb47fddee0fc7d8c6ba51f7a9c7ea3e4fea4f33ad01'  # 'your-secure-password'