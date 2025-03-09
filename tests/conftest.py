# tests/conftest.py

import os
import pytest
import tempfile
from app import create_app, db
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.models.allergen import Allergen
import secrets

class TestConfig:
    """Test configuration"""
    SECRET_KEY = 'test-secret-key'
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = 'test@example.com'
    ADMIN_EMAIL = 'admin@example.com'
    ADMIN_PHONE = '123456789'
    RSVP_DEADLINE = '2026-05-01'
    WEDDING_DATE = '2026-06-06'
    LANGUAGES = ['en', 'es']

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app(TestConfig)
    
    # Create the database and tables
    with app.app_context():
        db.create_all()
        yield app
        # Clean up after test
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def _db(app):
    """Special fixture for pytest-flask-sqlalchemy."""
    return db

@pytest.fixture
def sample_guest(app):
    """Create a sample guest for testing."""
    with app.app_context():
        guest = Guest(
            name='Test Guest',
            email='test@example.com',
            phone='123456789',
            token=secrets.token_urlsafe(32),
            language_preference='en',
            has_plus_one=True,
            is_family=False
        )
        db.session.add(guest)
        db.session.commit()
        return guest

@pytest.fixture
def sample_rsvp(app, sample_guest):
    """Create a sample RSVP for testing."""
    with app.app_context():
        rsvp = RSVP(
            guest_id=sample_guest.id,
            is_attending=True,
            adults_count=1,
            children_count=0,
            hotel_name='Test Hotel',
            transport_to_church=True,
            transport_to_reception=False,
            transport_to_hotel=True
        )
        db.session.add(rsvp)
        db.session.commit()
        return rsvp

@pytest.fixture
def sample_allergens(app):
    """Create sample allergens for testing."""
    with app.app_context():
        allergens = [
            Allergen(name='Gluten'),
            Allergen(name='Dairy'),
            Allergen(name='Nuts')
        ]
        db.session.add_all(allergens)
        db.session.commit()
        return allergens

@pytest.fixture
def admin_authenticated_client(client):
    """A test client that has been authenticated as admin."""
    client.set_cookie('localhost', 'admin_authenticated', 'true')
    return client