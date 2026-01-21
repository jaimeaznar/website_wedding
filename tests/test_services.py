# tests/test_services.py - Fixed TestAdminService class
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

                language_preference='en'
            )
            
            assert guest.id is not None
            assert guest.name == "Service Test Guest"
            assert guest.phone == "555-SERVICE"

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
    
    def test_find_guest_by_phone(self, app):
        """Test finding a guest by phone."""
        with app.app_context():
            # Create a guest
            guest = GuestService.create_guest(
                name="Find Test Guest",
                phone="555-FIND",
            )

            
            # Find by phone
            found_by_phone = GuestService.find_guest_by_phone(phone="555-FIND")
            assert found_by_phone is not None
            assert found_by_phone.id == guest.id
            
            # Find by both (should return the same guest)
            found_by_both = GuestService.find_guest_by_phone(
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
                'allergens_main': [str(allergen.id)],
                'custom_allergen_main': 'Shellfish'
            }
            
            # Create RSVP
            success, message, rsvp = RSVPService.create_or_update_rsvp(guest, form_data)
            
            assert success is True
            assert rsvp is not None
            assert rsvp.is_attending is True
            assert rsvp.hotel_name == 'Test Hotel'
                        
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

    def test_create_rsvp_with_children_needs_menu(self, app):
        """Test creating an RSVP with children who need menu."""
        with app.app_context():
            from app.models.rsvp import AdditionalGuest
            from datetime import datetime, timedelta

            # Ensure RSVP deadline is in the future
            future_deadline = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            app.config['RSVP_DEADLINE'] = future_deadline
            
            # Create guest
            guest = GuestService.create_guest("Children Menu Test Guest", "555-CHILDMENU")
            
            # Prepare form data with 2 children - one with menu, one without
            form_data = {
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel',
                'adults_count': '0',
                'children_count': '2',
                'child_name_0': 'Child With Menu',
                'child_needs_menu_0': 'on',  # Checkbox checked
                'child_name_1': 'Child No Menu',
                # child_needs_menu_1 NOT present = unchecked
            }
            
            # Create RSVP
            success, message, rsvp = RSVPService.create_or_update_rsvp(guest, form_data)

            # Debug: print error message if failed
            if not success:
                print(f"RSVP creation failed: {message}")
            
            assert success is True, f"RSVP creation failed: {message}"
            
            assert success is True
            assert rsvp is not None
            assert rsvp.children_count == 2
            
            # Verify children were saved with correct needs_menu values
            children = AdditionalGuest.query.filter_by(
                rsvp_id=rsvp.id,
                is_child=True
            ).order_by(AdditionalGuest.name).all()
            
            assert len(children) == 2
            
            # Child No Menu (alphabetically first)
            child_no_menu = next(c for c in children if c.name == 'Child No Menu')
            assert child_no_menu.needs_menu is False
            
            # Child With Menu
            child_with_menu = next(c for c in children if c.name == 'Child With Menu')
            assert child_with_menu.needs_menu is True
            
            # Clean up
            AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).delete()
            db.session.delete(rsvp)
            db.session.delete(guest)
            db.session.commit()

    def test_create_rsvp_children_default_no_menu(self, app):
        """Test that children default to needs_menu=False when checkbox not checked."""
        with app.app_context():
            from app.models.rsvp import AdditionalGuest
            from datetime import datetime, timedelta

            # Ensure RSVP deadline is in the future
            future_deadline = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            app.config['RSVP_DEADLINE'] = future_deadline
            
            # Create guest
            guest = GuestService.create_guest("Default Menu Test Guest", "555-DEFAULTMENU")
            
            # Prepare form data with child - NO checkbox checked
            form_data = {
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel',
                'adults_count': '0',
                'children_count': '1',
                'child_name_0': 'Default Child',
                # No child_needs_menu_0 = defaults to False
            }
            
            # Create RSVP
            success, message, rsvp = RSVPService.create_or_update_rsvp(guest, form_data)
            
            assert success is True, f"RSVP creation failed: {message}"
            
            # Verify child has needs_menu=False
            child = AdditionalGuest.query.filter_by(
                rsvp_id=rsvp.id,
                is_child=True
            ).first()
            
            assert child is not None
            assert child.name == 'Default Child'
            assert child.needs_menu is False
            
            # Clean up
            AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).delete()
            db.session.delete(rsvp)
            db.session.delete(guest)
            db.session.commit()

    def test_update_rsvp_children_menu_preference(self, app):
        """Test updating an RSVP changes children menu preferences correctly."""
        with app.app_context():
            from app.models.rsvp import AdditionalGuest
            from datetime import datetime, timedelta

            # Ensure RSVP deadline is in the future
            future_deadline = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            app.config['RSVP_DEADLINE'] = future_deadline
            
            # Create guest
            guest = GuestService.create_guest("Update Menu Test Guest", "555-UPDATEMENU")
            
            # First submission: child WITHOUT menu
            form_data_1 = {
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel',
                'adults_count': '0',
                'children_count': '1',
                'child_name_0': 'Toggle Child',
                # No checkbox = no menu
            }
            
            success, message, rsvp = RSVPService.create_or_update_rsvp(guest, form_data_1)
            assert success is True, f"First RSVP creation failed: {message}"
            
            # Verify child has no menu
            child = AdditionalGuest.query.filter_by(rsvp_id=rsvp.id, is_child=True).first()
            assert child.needs_menu is False
            
            # Second submission: same child WITH menu
            form_data_2 = {
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel',
                'adults_count': '0',
                'children_count': '1',
                'child_name_0': 'Toggle Child',
                'child_needs_menu_0': 'on',  # Now checked
            }
            
            success, message, rsvp = RSVPService.create_or_update_rsvp(guest, form_data_2)
            assert success is True, f"Second RSVP update failed: {message}"
            
            # Verify child now has menu
            child = AdditionalGuest.query.filter_by(rsvp_id=rsvp.id, is_child=True).first()
            assert child is not None
            assert child.name == 'Toggle Child'
            assert child.needs_menu is True
            
            # Clean up
            AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).delete()
            db.session.delete(rsvp)
            db.session.delete(guest)
            db.session.commit()

    def test_adults_do_not_have_needs_menu_in_form(self, app):
        """Test that adults are created without needs_menu being set from form."""
        with app.app_context():
            from app.models.rsvp import AdditionalGuest
            from datetime import datetime, timedelta

            # Ensure RSVP deadline is in the future
            future_deadline = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            app.config['RSVP_DEADLINE'] = future_deadline
            
            # Create guest
            guest = GuestService.create_guest("Adult Menu Test Guest", "555-ADULTMENU")
            
            # Prepare form data with adult
            form_data = {
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel',
                'adults_count': '1',
                'children_count': '0',
                'adult_name_0': 'Test Adult',
            }
            
            # Create RSVP
            success, message, rsvp = RSVPService.create_or_update_rsvp(guest, form_data)
            
            assert success is True, f"RSVP creation failed: {message}"
            
            # Verify adult was created with default needs_menu=False
            adult = AdditionalGuest.query.filter_by(
                rsvp_id=rsvp.id,
                is_child=False
            ).first()
            
            assert adult is not None
            assert adult.name == 'Test Adult'
            assert adult.is_child is False
            assert adult.needs_menu is False  # Default value, not set from form
            
            # Clean up
            AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).delete()
            db.session.delete(rsvp)
            db.session.delete(guest)
            db.session.commit()

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
            from app.admin_auth import reset_password_cache
            from werkzeug.security import generate_password_hash
            
            # IMPORTANT: Reset the password cache before the test
            reset_password_cache()
            
            # Generate a fresh hash for testing
            test_password = 'test-password-123'
            test_hash = generate_password_hash(test_password, method='pbkdf2:sha256')
            
            # Set it in the config
            app.config['ADMIN_PASSWORD_HASH'] = test_hash
            # Remove ADMIN_PASSWORD to ensure we use the hash
            app.config.pop('ADMIN_PASSWORD', None)
            
            # Test with correct password
            result = AdminService.verify_admin_password(test_password)
            assert result is True, "Password verification failed with correct password"
            
            # Test with incorrect password
            result = AdminService.verify_admin_password('wrong-password')
            assert result is False, "Password verification succeeded with wrong password"
            
            # Clean up: reset cache after test
            reset_password_cache()
    
    def test_get_dashboard_data(self, app):
        """Test getting dashboard data."""
        with app.app_context():
            from app.services.admin_service import AdminService
            
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
            from app.services.guest_service import GuestService
            from app.services.admin_service import AdminService
            from app.models.rsvp import RSVP
            from app import db
            
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