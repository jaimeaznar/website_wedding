"""Configuration module for the Flask application.

This module contains the configuration classes for different environments
and handles loading environment variables.
"""
import os
from datetime import timedelta
from typing import List
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration class for the Flask application.
    
    This class contains all the configuration variables used throughout
    the application. It loads most values from environment variables
    with sensible defaults.
    """
    
    # Basic Flask config
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        'DATABASE_URL',
        'postgresql://jaimeaznar@localhost/wedding_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # CSRF settings
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_SECRET_KEY: str = os.getenv('WTF_CSRF_SECRET_KEY', SECRET_KEY)
    
    # Email configuration
    MAIL_SERVER: str = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT: int = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS: bool = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME: str = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD: str = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER: str = os.getenv('MAIL_DEFAULT_SENDER', '')
    
    # Languages
    LANGUAGES: List[str] = ['en', 'es']
    BABEL_DEFAULT_LOCALE: str = 'en'
    
    # Custom configuration
    ADMIN_EMAIL: str = os.getenv('ADMIN_EMAIL', 'your@email.com')
    ADMIN_PHONE: str = os.getenv('ADMIN_PHONE', '123456789')
    RSVP_DEADLINE: str = os.getenv('RSVP_DEADLINE', '2026-05-06')  # Default 1 month before wedding
    WEDDING_DATE: str = os.getenv('WEDDING_DATE', '2026-06-06')
    REMINDER_DAYS_BEFORE: int = 30  # Send reminder 30 days before deadline
    WARNING_MESSAGE_TIMEOUT: int = 0  # 0 means no auto-dismiss
    WARNING_CUTOFF_DAYS: int = 7  # days before wedding for warnings
    
    # Admin password hash for tests
    ADMIN_PASSWORD_HASH: str = os.getenv(
        'ADMIN_PASSWORD_HASH',
        'pbkdf2:sha256:600000$MlXi8Xcgp3y5$d17a4d3dce0a3d5be306beb47fddee0fc7d8c6ba51f7a9c7ea3e4fea4f33ad01'
    )

class TestConfig(Config):
    """Test configuration class.
    
    This class inherits from the base Config class and overrides
    settings specific to the testing environment.
    """
    
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED: bool = False
    WTF_CSRF_CHECK_DEFAULT: bool = False
    SECRET_KEY: str = 'test-secret-key'
    WEDDING_DATE: str = '2026-06-06'
    RSVP_DEADLINE: str = '2026-05-06'  # 1 month before wedding
    
    # Set accessible admin password for tests
    ADMIN_PASSWORD_HASH: str = (
        'pbkdf2:sha256:600000$MlXi8Xcgp3y5$d17a4d3dce0a3d5be306beb47fddee0fc7d8c6ba51f7a9c7ea3e4fea4f33ad01'
    )