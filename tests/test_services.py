# tests/test_services.py
import pytest
import secrets
from datetime import datetime, timedelta
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.models.allergen import Allergen, GuestAllergen
from app.services.guest_service import GuestService
from app.services.rsvp_service import RSVPService
from app.services.allergen_service import AllergenService
from app.services.admin_service import AdminService


class TestGuestService:
    """Test cases for GuestService."""
    
    def test_create_guest(self, app):
        """Test creating a guest through the service."""
        with app.app_context():
            # Create a guest
            guest = GuestService.create_guest(
                name="Service Test Guest",
                phone="555-SERVICE",
                email="service@test.com",
                has_plus_one=True,
                is_family=False,
                language_preference='en'
            )
            
            assert guest.id is not None
            assert guest.name == "Service Test Guest"
            assert guest.phone == "555-SERVICE"
            assert guest.email == "service@test.com"
            assert guest.has_plus_one is True
            assert guest.is_family is False
            assert len(guest.token) > 0
            
            # Clean up
            db.session.delete(guest)
            db.session.commit()
    
    def test_create_guest_missing_required_fields(self, app):
        """Test creating a guest with missing required fields."""
        with app.app_context():
            with pytest.raises(ValueError) as excinfo:
                GuestService.create_guest(
                    name="",
                    phone="555-1234"
                )
            assert "Please fill in all required fields" in str(excinfo.value)
    
    def test_get_guest_by_token(self, app):
        """Test retrieving a guest by token."""
        with app.app_context():
            # Create a guest first
            guest = GuestService.create_guest(
                name="Token Test Guest",
                phone="555-TOKEN"
            )
            token = guest.token
            
            # Retrieve by token
            found_guest = GuestService.get_guest_by_token(token)
            assert found_guest is not None
            assert found_guest.id == guest.id
            assert found_guest.name == "Token Test Guest"
            
            # Test with invalid token
            not_found = GuestService.get_guest_by_token("invalid-token")
            assert not_found is None
            
            # Clean up
            db.session.delete(guest)
            db.session.commit()
    
    def test_find_guest_by_email_or_phone(self, app):
        """Test finding a guest by email or phone."""
        with app.app_context():
            # Create a guest
            guest = GuestService.create_guest(
                name="Find Test Guest",
                phone="555-FIND",
                email="find@test.com"
            )
            
            # Find by email
            found_by_email = GuestService.find_guest_by_email_or_phone(email="find@test.com")
            assert found_by_email is not None
            assert found_by_email.id == guest.id
            
            # Find by phone
            found_by_phone = GuestService.find_guest_by_email_or_phone(phone="555-FIND")
            assert found_by_phone is not None
            assert found_by_phone.id == guest.id
            
            # Find by both (should return the same guest)
            found_by_both = GuestService.find_guest_by_email_or_phone(
                email="find@test.com",
                phone="555-FIND"
            )
            assert found_by_both is not None
            assert found_by_both.id == guest.id
            
            # Clean up
            db.session.delete(guest)
            db.session.commit()
    
    def test_get_guest_statistics(self, app):
        """Test getting guest statistics."""
        with app.app_context():
            # Create test data
            guest1 = GuestService.create_guest("Stats Guest 1", "555-0001")
            guest2 = GuestService.create_guest("Stats Guest 2", "555-0002")
            
            # Create RSVPs
            rsvp1 = RSVP(guest_id=guest1.id, is_attending=True)
            rsvp2 = RSVP(guest_id=guest2.id, is_attending=False)
            db.session.add_all([rsvp1, rsvp2])
            db.session.commit()
            
            # Get statistics
            stats = GuestService.get_guest_statistics()
            
            assert stats['total_guests'] >= 2
            assert stats['attending_count'] >= 1
            assert stats['declined_count'] >= 1
            
            # Clean up
            db.session.delete(rsvp1)
            db.session.delete(rsvp2)
            db.session.delete(guest1)
            db.session.delete(guest2)
            db.session.commit()


class TestRSVPService:
    """Test cases for RSVPService."""
    
    def test_create_rsvp_attending(self, app):
        """Test creating an attending RSVP."""
        with app.app_context():
            # Create guest and allergen
            guest = GuestService.create_guest("RSVP Test Guest", "555-RSVP")
            allergen = Allergen.query.filter_by(name="Gluten").first()
            if not allergen:
                allergen = Allergen(name="Gluten")
                db.session.add(allergen)
                db.session.commit()
            
            # Prepare form data
            form_data = {
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel',
                'transport_to_church': 'on',
                'allergens_main': [str(allergen.id)],
                'custom_allergen_main': 'Shellfish'
            }
            
            # Create RSVP
            success, message, rsvp = RSVPService.create_or_update_rsvp(guest, form_data)
            
            assert success is True
            assert rsvp is not None
            assert rsvp.is_attending is True
            assert rsvp.hotel_name == 'Test Hotel'
            assert rsvp.transport_to_church is True
            
            # Verify allergens were saved
            allergens = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).all()
            assert len(allergens) == 2  # One standard, one custom
            
            # Clean up
            GuestAllergen.query.filter_by(rsvp_id=rsvp.id).delete()
            db.session.delete(rsvp)
            db.session.delete(guest)
            db.session.commit()
    
    def test_create_rsvp_declining(self, app):
        """Test creating a declining RSVP."""
        with app.app_context():
            # Create guest
            guest = GuestService.create_guest("Decline Test Guest", "555-DECLINE")
            
            # Prepare form data
            form_data = {
                'is_attending': 'no'
            }
            
            # Create RSVP
            success, message, rsvp = RSVPService.create_or_update_rsvp(guest, form_data)
            
            assert success is True
            assert rsvp is not None
            assert rsvp.is_attending is False
            assert rsvp.hotel_name is None
            
            # Clean up
            db.session.delete(rsvp)
            db.session.delete(guest)
            db.session.commit()
    
    def test_cancel_rsvp(self, app):
        """Test cancelling an RSVP."""
        with app.app_context():
            # Create guest and RSVP
            guest = GuestService.create_guest("Cancel Test Guest", "555-CANCEL")
            rsvp = RSVP(guest_id=guest.id, is_attending=True)
            db.session.add(rsvp)
            db.session.commit()
            
            # Cancel the RSVP
            success, message = RSVPService.cancel_rsvp(guest)
            
            assert success is True
            assert rsvp.is_cancelled is True
            assert rsvp.is_attending is False
            assert rsvp.cancellation_date is not None
            
            # Clean up
            db.session.delete(rsvp)
            db.session.delete(guest)
            db.session.commit()
    
    def test_is_rsvp_deadline_passed(self, app):
        """Test checking if RSVP deadline has passed."""
        with app.app_context():
            # Test with future deadline
            future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            app.config['RSVP_DEADLINE'] = future_date
            assert RSVPService.is_rsvp_deadline_passed() is False
            
            # Test with past deadline
            past_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            app.config['RSVP_DEADLINE'] = past_date
            assert RSVPService.is_rsvp_deadline_passed() is True


class TestAllergenService:
    """Test cases for AllergenService."""
    
    def test_create_allergen(self, app):
        """Test creating an allergen."""
        with app.app_context():
            # Create unique allergen name
            allergen_name = f"Test Allergen {datetime.now().timestamp()}"
            
            allergen = AllergenService.create_allergen(allergen_name)
            assert allergen.id is not None
            assert allergen.name == allergen_name
            
            # Test duplicate creation
            with pytest.raises(ValueError) as excinfo:
                AllergenService.create_allergen(allergen_name)
            assert "already exists" in str(excinfo.value)
            
            # Clean up
            db.session.delete(allergen)
            db.session.commit()
    
    def test_get_allergen_summary(self, app):
        """Test getting allergen summary."""
        with app.app_context():
            # Create test data
            guest = GuestService.create_guest("Allergen Summary Guest", "555-ALLERGEN")
            rsvp = RSVP(guest_id=guest.id, is_attending=True)
            db.session.add(rsvp)
            db.session.flush()
            
            # Add some allergens
            allergen = Allergen.query.first()
            if allergen:
                guest_allergen = GuestAllergen(
                    rsvp_id=rsvp.id,
                    guest_name=guest.name,
                    allergen_id=allergen.id
                )
                db.session.add(guest_allergen)
                db.session.commit()
                
                # Get summary
                summary = AllergenService.get_allergen_summary()
                assert allergen.name in summary
                assert summary[allergen.name] >= 1
                
                # Clean up
                db.session.delete(guest_allergen)
            
            # Clean up
            db.session.delete(rsvp)
            db.session.delete(guest)
            db.session.commit()


class TestAdminService:
    """Test cases for AdminService."""
    
    def test_verify_admin_password(self, app):
        """Test admin password verification."""
        with app.app_context():
            # Test with correct password (from test config)
            assert AdminService.verify_admin_password('your-secure-password') is True
            
            # Test with incorrect password
            assert AdminService.verify_admin_password('wrong-password') is False
    
    def test_get_dashboard_data(self, app):
        """Test getting dashboard data."""
        with app.app_context():
            # Get dashboard data
            data = AdminService.get_dashboard_data()
            
            # Check required keys
            assert 'guests' in data
            assert 'rsvps' in data
            assert 'total_guests' in data
            assert 'total_attending' in data
            assert 'transport_stats' in data
            
            # Check data types
            assert isinstance(data['guests'], list)
            assert isinstance(data['rsvps'], list)
            assert isinstance(data['total_guests'], int)
    
    def test_get_pending_rsvps(self, app):
        """Test getting pending RSVPs."""
        with app.app_context():
            # Create guest without RSVP
            guest_no_rsvp = GuestService.create_guest("No RSVP Guest", "555-NORSVP")
            
            # Create guest with RSVP
            guest_with_rsvp = GuestService.create_guest("Has RSVP Guest", "555-HASRSVP")
            rsvp = RSVP(guest_id=guest_with_rsvp.id, is_attending=True)
            db.session.add(rsvp)
            db.session.commit()
            
            # Get pending
            pending = AdminService.get_pending_rsvps()
            pending_ids = [g.id for g in pending]
            
            # Check results
            assert guest_no_rsvp.id in pending_ids
            assert guest_with_rsvp.id not in pending_ids
            
            # Clean up
            db.session.delete(rsvp)
            db.session.delete(guest_with_rsvp)
            db.session.delete(guest_no_rsvp)
            db.session.commit()