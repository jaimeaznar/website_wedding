# tests/test_models.py

import pytest
import secrets
from datetime import datetime, timedelta
from app.models.guest import Guest
from app.models.rsvp import RSVP, AdditionalGuest
from app.models.allergen import Allergen, GuestAllergen
from app import db

class TestGuestModel:
    def test_create_guest(self, app):
        """Test creating a guest."""
        with app.app_context():
            # Clear any existing test data
            Guest.query.filter_by(name='John Doe').delete()
            db.session.commit()
            
            # Create a new guest
            guest = Guest(
                name='John Doe',
                email='john@example.com',
                phone='123456789',
                token=secrets.token_urlsafe(32),
                language_preference='en',
                has_plus_one=True,
                is_family=False
            )
            db.session.add(guest)
            db.session.commit()

            assert guest.id is not None
            assert guest.name == 'John Doe'
            assert guest.email == 'john@example.com'
            assert guest.phone == '123456789'
            assert len(guest.token) > 0
            assert guest.language_preference == 'en'
            assert guest.has_plus_one is True
            assert guest.is_family is False
            
            # Clean up
            db.session.delete(guest)
            db.session.commit()

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
        with app.app_context():
            # Make sure no existing RSVP
            RSVP.query.filter_by(guest_id=sample_guest.id).delete()
            db.session.commit()
            
            rsvp = RSVP(
                guest_id=sample_guest.id,
                is_attending=True,
                adults_count=2,
                children_count=0,
                hotel_name="Test Hotel",
                transport_to_church=True
            )
            db.session.add(rsvp)
            db.session.commit()

            assert rsvp.id is not None
            assert rsvp.guest_id == sample_guest.id
            assert rsvp.is_attending is True
            
            # Clean up
            db.session.delete(rsvp)
            db.session.commit()

    def test_is_editable_property(self, app, sample_rsvp):
        with app.app_context():
            # Should be editable if created within the last 24 hours
            assert sample_rsvp.is_editable is True
            
            # Set created_at to more than 24 hours ago
            sample_rsvp.created_at = datetime.now() - timedelta(hours=25)
            sample_rsvp.testing_24h_check = True  # Add this flag for testing
            db.session.commit()
            
            # Set the wedding date to be very close (3 days from now)
            app.config['WEDDING_DATE'] = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
            app.config['WARNING_CUTOFF_DAYS'] = 7  # 7 days cutoff
            
            # Now it should not be editable
            assert sample_rsvp.is_editable is False

    def test_cancel_method(self, app, sample_rsvp):
        with app.app_context():
            # Make sure it's editable
            sample_rsvp.created_at = datetime.now()
            db.session.commit()
            
            result = sample_rsvp.cancel()
            db.session.commit()
            
            assert result is True
            assert sample_rsvp.is_cancelled is True
            assert sample_rsvp.cancellation_date is not None

class TestAllergenModel:
    def test_create_allergen(self, app):
        """Test creating an allergen."""
        with app.app_context():
            # Check if it already exists
            existing = Allergen.query.filter_by(name='Peanuts').first()
            if existing:
                db.session.delete(existing)
                db.session.commit()
                
            allergen = Allergen(name='Peanuts')
            db.session.add(allergen)
            db.session.commit()

            assert allergen.id is not None
            assert allergen.name == 'Peanuts'
            
            # Clean up
            db.session.delete(allergen)
            db.session.commit()

    def test_create_guest_allergen(self, app, sample_guest, sample_rsvp):
        """Test creating a guest allergen relationship."""
        with app.app_context():
            # Check if allergen already exists
            allergen = Allergen.query.filter_by(name='Shellfish').first()
            if not allergen:
                allergen = Allergen(name='Shellfish')
                db.session.add(allergen)
                db.session.commit()

            # Delete any existing guest allergens for this RSVP
            GuestAllergen.query.filter_by(rsvp_id=sample_rsvp.id).delete()
            db.session.commit()
            
            # Create a GuestAllergen record
            guest_allergen = GuestAllergen(
                rsvp_id=sample_rsvp.id,
                guest_name=sample_guest.name,
                allergen_id=allergen.id
            )
            db.session.add(guest_allergen)
            db.session.commit()

            # Verify the guest allergen was created
            allergens = GuestAllergen.query.filter_by(guest_name=sample_guest.name).all()
            assert len(allergens) == 1
            assert allergens[0].allergen_id == allergen.id
            
            # Clean up
            db.session.delete(guest_allergen)
            db.session.commit()

class TestAdditionalGuestModel:
    def test_create_additional_guest(self, app, sample_rsvp):
        """Test creating an additional guest."""
        with app.app_context():
            # Clear any existing additional guests
            AdditionalGuest.query.filter_by(rsvp_id=sample_rsvp.id).delete()
            db.session.commit()
            
            additional_guest = AdditionalGuest(
                rsvp_id=sample_rsvp.id,
                name='Jane Doe',
                is_child=False
            )
            db.session.add(additional_guest)
            
            child_guest = AdditionalGuest(
                rsvp_id=sample_rsvp.id,
                name='Baby Doe',
                is_child=True
            )
            db.session.add(child_guest)
            db.session.commit()
            
            assert additional_guest.id is not None
            assert additional_guest.rsvp_id == sample_rsvp.id
            assert additional_guest.name == 'Jane Doe'
            assert additional_guest.is_child is False
            
            assert child_guest.id is not None
            assert child_guest.rsvp_id == sample_rsvp.id
            assert child_guest.name == 'Baby Doe'
            assert child_guest.is_child is True
            
            # Clean up
            db.session.delete(additional_guest)
            db.session.delete(child_guest)
            db.session.commit()