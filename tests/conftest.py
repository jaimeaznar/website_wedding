import os
import pytest
import secrets
from datetime import datetime
from app import create_app, db
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.models.allergen import Allergen
from app.config import TestConfig
from dotenv import load_dotenv

# Load environment variables from .env file at the start of testing
load_dotenv()

class CustomTestConfig(TestConfig):
    """Custom test configuration to explicitly disable CSRF."""
    WTF_CSRF_ENABLED = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    ADMIN_PASSWORD_HASH = 'pbkdf2:sha256:600000$MlXi8Xcgp3y5$d17a4d3dce0a3d5be306beb47fddee0fc7d8c6ba51f7a9c7ea3e4fea4f33ad01'  # 'your-secure-password'

@pytest.fixture(scope='session')
def app():
    """Create and configure a Flask app for testing."""
    # Create the app with the test config
    app = create_app(CustomTestConfig)
    
    # Establish an application context
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Add some basic test data (allergens) that will be shared
        basic_allergens = ['Gluten', 'Dairy', 'Nuts']
        for name in basic_allergens:
            allergen = Allergen.query.filter_by(name=name).first()
            if not allergen:
                db.session.add(Allergen(name=name))
        db.session.commit()
        
        yield app
        
        # Clean up
        db.session.remove()

@pytest.fixture(autouse=True)
def clean_db(app):
    """Clean database between tests by removing test data but keeping basic allergens."""
    with app.app_context():
        # Delete test-specific data but keep basic allergens
        
        # Delete guests (which will cascade to RSVPs and their allergens)
        test_guests = Guest.query.filter(
            Guest.email.like('%test%') | 
            Guest.name.like('%Test%')
        ).all()
        
        for guest in test_guests:
            # The cascade should handle related records
            db.session.delete(guest)
        
        # Delete any test allergens (but keep basic ones)
        test_allergens = Allergen.query.filter(
            Allergen.name.like('%Test%') | 
            Allergen.name.like('%test%')
        ).all()
        
        for allergen in test_allergens:
            db.session.delete(allergen)
        
        db.session.commit()
    yield

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def auth_client(client, app):
    """Create an authenticated client."""
    with client.session_transaction() as session:
        session['admin_logged_in'] = True
    
    # Set the authentication cookie
    client.set_cookie('admin_authenticated', 'true')
    return client

@pytest.fixture
def sample_guest(app):
    """Create a sample guest for testing."""
    with app.app_context():
        guest = Guest(
            name='Test Guest',
            email='test@example.com',
            phone='555-0123',
            token=secrets.token_urlsafe(32),
            language_preference='en',
            has_plus_one=True,
            is_family=False
        )
        db.session.add(guest)
        db.session.commit()
        
        yield guest
        
        # Clean up
        if Guest.query.get(guest.id):
            db.session.delete(guest)
            db.session.commit()

@pytest.fixture
def sample_rsvp(app, sample_guest):
    """Create a sample RSVP for testing."""
    with app.app_context():
        rsvp = RSVP(
            guest_id=sample_guest.id,
            is_attending=True,
            hotel_name='Test Hotel',
            transport_to_church=True,
            transport_to_reception=False,
            transport_to_hotel=False
        )
        db.session.add(rsvp)
        db.session.commit()
        
        yield rsvp
        
        # Clean up
        if RSVP.query.get(rsvp.id):
            db.session.delete(rsvp)
            db.session.commit()