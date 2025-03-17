# tests/utils.py
from werkzeug.security import generate_password_hash

# Test password constants
TEST_PASSWORD = 'your-secure-password'
TEST_PASSWORD_HASH = generate_password_hash(TEST_PASSWORD)

def get_test_config():
    """Get test configuration overrides"""
    return {
        'ADMIN_PASSWORD_HASH': TEST_PASSWORD_HASH,
        'WTF_CSRF_ENABLED': False,
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
    }