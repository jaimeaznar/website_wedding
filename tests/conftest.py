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

@pytest.fixture(scope='session')
def app():
    """Create and configure a Flask app for testing."""
    # Create the app with the test config
    app = create_app(CustomTestConfig)
    
    # Establish an application context
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Add some test data (allergens)
        allergens = ['Gluten', 'Dairy', 'Nuts']
        for name in allergens:
            allergen = Allergen.query.filter_by(name=name).first()
            if not allergen:
                db.session.add(Allergen(name=name))
        db.session.commit()
        
        yield app
        
        # Clean up (don't delete tables, as it can cause issues with SQLite in-memory DB)
        db.session.remove()

@pytest.fixture(autouse=True)
def clean_db(app):
    """Clean database between tests by removing all data but keeping tables."""
    with app.app_context():
        # Clear all tables without dropping them
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
    yield

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def sample_guest(app):
    """Create a sample guest."""
    with app.app_context():
        guest = Guest(
            name="Test Guest",
            email="test@example.com",
            phone="1234567890",
            token=secrets.token_urlsafe(16),
            language_preference="en",
            has_plus_one=True,
            is_family=True  # Set is_family to True for all tests
        )
        db.session.add(guest)
        db.session.commit()
        
        # Refresh the instance to ensure it's attached to the session
        db.session.refresh(guest)
        return guest

@pytest.fixture(scope='function')
def sample_rsvp(app, sample_guest):
    """Create a sample RSVP."""
    with app.app_context():
        rsvp = RSVP(
            guest_id=sample_guest.id,
            is_attending=True,
            adults_count=2,
            children_count=0,
            hotel_name="Test Hotel",
            transport_to_church=True,
            created_at=datetime.now()
        )
        db.session.add(rsvp)
        db.session.commit()
        
        # Refresh the instance to ensure it's attached to the session
        db.session.refresh(rsvp)
        return rsvp

@pytest.fixture(scope='function')
def sample_allergens(app):
    """Create sample allergens."""
    with app.app_context():
        allergens = []
        for name in ["Peanuts", "Gluten", "Dairy"]:
            # Check if allergen already exists
            existing = Allergen.query.filter_by(name=name).first()
            if existing:
                allergens.append(existing)
                continue
                
            allergen = Allergen(name=name)
            db.session.add(allergen)
            allergens.append(allergen)
        db.session.commit()
        return allergens

@pytest.fixture(scope='function')
def auth_client(client, app):
    """Create an authenticated client."""
    with client.session_transaction() as session:
        session['admin_logged_in'] = True
    
    # Fix: Use the correct signature for set_cookie
    client.set_cookie('admin_authenticated', 'true')
    return client