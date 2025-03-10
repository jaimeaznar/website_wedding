import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Basic Flask config
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Database - directly specify the URL
    SQLALCHEMY_DATABASE_URI = 'postgresql://jaimeaznar@localhost/wedding_db'
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
    ADMIN_EMAIL = 'your@email.com'
    ADMIN_PHONE = '123456789'
    RSVP_DEADLINE = os.getenv('RSVP_DEADLINE')
    WEDDING_DATE = os.getenv('WEDDING_DATE')
    REMINDER_DAYS_BEFORE = 30  # Send reminder 30 days before deadline
    WARNING_MESSAGE_TIMEOUT = 0  # 0 means no auto-dismiss
    WARNING_CUTOFF_DAYS = 7     # days before wedding for warnings

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    ADMIN_PASSWORD_HASH = 'test-hash'