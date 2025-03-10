# tests/test_models.py

import pytest
import secrets
from datetime import datetime, timedelta
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.models.allergen import Allergen
from app import db

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

    def test_is_editable_property(self, app, sample_rsvp):
        with app.app_context():
            # Should be editable if created within the last 24 hours
            assert sample_rsvp.is_editable is True

            # Set created_at to more than 24 hours ago
            sample_rsvp.created_at = datetime.utcnow() - timedelta(hours=25)
            db.session.commit()
            assert sample_rsvp.is_editable is False

    def test_cancel_method(self, app, sample_rsvp):
        with app.app_context():
            sample_rsvp.cancel()
            db.session.commit()
            assert sample_rsvp.is_cancelled is True
            assert sample_rsvp.cancelled_at is not None

class TestAllergenModel:
    def test_create_allergen(self, app):
        """Test creating an allergen."""
        with app.app_context():
            allergen = Allergen(name='Peanuts')
            db.session.add(allergen)
            db.session.commit()

            assert allergen.id is not None
            assert allergen.name == 'Peanuts'

    def test_create_guest_allergen(self, app, sample_guest):
        """Test creating a guest allergen relationship."""
        with app.app_context():
            allergen = Allergen(name='Shellfish')
            db.session.add(allergen)
            db.session.commit()

            sample_guest.allergens.append(allergen)
            db.session.commit()

            assert allergen in sample_guest.allergens

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
