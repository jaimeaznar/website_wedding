import pytest
from datetime import datetime
from app import create_app, db
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.models.allergen import Allergen
from app.config import TestConfig

@pytest.fixture(scope='function')
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

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
            token="test-token",
            language_preference="en",
            has_plus_one=True,
            is_family=False
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
            created_at=datetime.utcnow()
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
    
    # Use the actual cookie that the application checks for
    client.set_cookie('/', 'admin_authenticated', 'true')
    return client
