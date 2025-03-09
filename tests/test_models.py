# tests/test_models.py

from datetime import datetime, timedelta
from app.models.guest import Guest
from app.models.rsvp import RSVP, AdditionalGuest
from app.models.allergen import Allergen, GuestAllergen
import secrets

class TestGuestModel:
    def test_create_guest(self, app):
        """Test creating a guest."""
        with app.app_context():
            guest = Guest(
                name='John Doe',
                email='john@example.com',
                phone='123456789',
                token=secrets.token_urlsafe(32),
                language_preference='en',
                has_plus_one=True,
                is_family=False
            )
            assert guest.name == 'John Doe'
            assert guest.email == 'john@example.com'
            assert guest.phone == '123456789'
            assert len(guest.token) > 0
            assert guest.language_preference == 'en'
            assert guest.has_plus_one is True
            assert guest.is_family is False

    def test_guest_rsvp_relationship(self, app, sample_guest, sample_rsvp):
        """Test guest to RSVP relationship."""
        with app.app_context():
            # Get fresh instance from database
            guest = Guest.query.get(sample_guest.id)
            assert guest.rsvp is not None
            assert guest.rsvp.is_attending is True
            assert guest.rsvp.hotel_name == 'Test Hotel'
            
            # Verify the relationship works both ways
            assert guest.rsvp.guest_id == sample_guest.id
            assert guest.rsvp.guest.name == sample_guest.name

class TestRSVPModel:
    def test_create_rsvp(self, app, sample_guest):
        """Test creating an RSVP."""
        with app.app_context():
            rsvp = RSVP(
                guest_id=sample_guest.id,
                is_attending=True,
                adults_count=2,
                children_count=1,
                hotel_name='Grand Hotel',
                transport_to_church=True,
                transport_to_reception=True,
                transport_to_hotel=False
            )
            assert rsvp.guest_id == sample_guest.id
            assert rsvp.is_attending is True
            assert rsvp.adults_count == 2
            assert rsvp.children_count == 1
            assert rsvp.hotel_name == 'Grand Hotel'
            assert rsvp.transport_to_church is True
            assert rsvp.transport_to_reception is True
            assert rsvp.transport_to_hotel is False
            assert rsvp.is_cancelled is False

    def test_is_editable_property(self, app, monkeypatch):
        """Test RSVP.is_editable property."""
        with app.app_context():
            # Mock current_app.config
            monkeypatch.setattr('app.models.rsvp.current_app.config', {
                'WEDDING_DATE': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            })
            
            rsvp = RSVP(guest_id=1)
            # Should be editable when wedding is more than 7 days away
            assert rsvp.is_editable is True
            
            # Mock wedding date to be 5 days from now
            monkeypatch.setattr('app.models.rsvp.current_app.config', {
                'WEDDING_DATE': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
            })
            # Should not be editable when wedding is less than 7 days away
            assert rsvp.is_editable is False

    def test_cancel_method(self, app, sample_rsvp, monkeypatch):
        """Test RSVP.cancel method."""
        with app.app_context():
            # Mock current_app.config
            monkeypatch.setattr('app.models.rsvp.current_app.config', {
                'WEDDING_DATE': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            })
            
            # Get fresh instance
            rsvp = RSVP.query.get(sample_rsvp.id)
            
            # Test cancellation
            result = rsvp.cancel()
            assert result is True
            assert rsvp.is_cancelled is True
            assert rsvp.is_attending is False
            assert rsvp.cancellation_date is not None
            
            # Mock wedding date to be 5 days from now
            monkeypatch.setattr('app.models.rsvp.current_app.config', {
                'WEDDING_DATE': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
            })
            
            # Reset RSVP
            rsvp.is_cancelled = False
            rsvp.is_attending = True
            rsvp.cancellation_date = None
            
            # Test cancellation not allowed when too close to wedding
            result = rsvp.cancel()
            assert result is False
            assert rsvp.is_cancelled is False
            assert rsvp.is_attending is True

class TestAllergenModel:
    def test_create_allergen(self, app):
        """Test creating an allergen."""
        with app.app_context():
            allergen = Allergen(name='Seafood')
            assert allergen.name == 'Seafood'

    def test_create_guest_allergen(self, app, sample_rsvp, sample_allergens):
        """Test creating a guest allergen."""
        with app.app_context():
            guest_allergen = GuestAllergen(
                rsvp_id=sample_rsvp.id,
                guest_name='Test Guest',
                allergen_id=sample_allergens[0].id
            )
            assert guest_allergen.rsvp_id == sample_rsvp.id
            assert guest_allergen.guest_name == 'Test Guest'
            assert guest_allergen.allergen_id == sample_allergens[0].id
            
            custom_allergen = GuestAllergen(
                rsvp_id=sample_rsvp.id,
                guest_name='Test Guest',
                custom_allergen='Strawberries'
            )
            assert custom_allergen.rsvp_id == sample_rsvp.id
            assert custom_allergen.guest_name == 'Test Guest'
            assert custom_allergen.custom_allergen == 'Strawberries'

class TestAdditionalGuestModel:
    def test_create_additional_guest(self, app, sample_rsvp):
        """Test creating an additional guest."""
        with app.app_context():
            additional_guest = AdditionalGuest(
                rsvp_id=sample_rsvp.id,
                name='Jane Doe',
                is_child=False
            )
            assert additional_guest.rsvp_id == sample_rsvp.id
            assert additional_guest.name == 'Jane Doe'
            assert additional_guest.is_child is False
            
            child_guest = AdditionalGuest(
                rsvp_id=sample_rsvp.id,
                name='Baby Doe',
                is_child=True
            )
            assert child_guest.rsvp_id == sample_rsvp.id
            assert child_guest.name == 'Baby Doe'
            assert child_guest.is_child is True