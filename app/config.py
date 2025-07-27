import os
from datetime import timedelta
from dotenv import load_dotenv
from app.constants import (
    Language, DEFAULT_CONFIG, TimeLimit, DateFormat
)

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
    LANGUAGES = Language.SUPPORTED
    BABEL_DEFAULT_LOCALE = Language.DEFAULT
    
    # Custom config with defaults from constants
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', DEFAULT_CONFIG['ADMIN_EMAIL'])
    ADMIN_PHONE = os.getenv('ADMIN_PHONE', DEFAULT_CONFIG['ADMIN_PHONE'])
    RSVP_DEADLINE = os.getenv('RSVP_DEADLINE', DEFAULT_CONFIG['RSVP_DEADLINE'])
    WEDDING_DATE = os.getenv('WEDDING_DATE', DEFAULT_CONFIG['WEDDING_DATE'])
    REMINDER_DAYS_BEFORE = int(os.getenv('REMINDER_DAYS_BEFORE', DEFAULT_CONFIG['REMINDER_DAYS_BEFORE']))
    WARNING_MESSAGE_TIMEOUT = int(os.getenv('WARNING_MESSAGE_TIMEOUT', DEFAULT_CONFIG['WARNING_MESSAGE_TIMEOUT']))
    WARNING_CUTOFF_DAYS = int(os.getenv('WARNING_CUTOFF_DAYS', DEFAULT_CONFIG['WARNING_CUTOFF_DAYS']))
    
    # For tests - set a default admin password hash
    ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', 'pbkdf2:sha256:600000$MlXi8Xcgp3y5$d17a4d3dce0a3d5be306beb47fddee0fc7d8c6ba51f7a9c7ea3e4fea4f33ad01')

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # Make sure CSRF is explicitly disabled
    WTF_CSRF_CHECK_DEFAULT = False  # Double-check with another setting
    SECRET_KEY = 'test-secret-key'
    WEDDING_DATE = DEFAULT_CONFIG['WEDDING_DATE']
    RSVP_DEADLINE = DEFAULT_CONFIG['RSVP_DEADLINE']
    # Set accessible admin password for tests
    ADMIN_PASSWORD_HASH = 'pbkdf2:sha256:600000$MlXi8Xcgp3y5$d17a4d3dce0a3d5be306beb47fddee0fc7d8c6ba51f7a9c7ea3e4fea4f33ad01'  # 'your-secure-password'