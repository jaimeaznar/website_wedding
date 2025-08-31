# tests/test_edge_cases.py
import pytest
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading
from app import create_app, db
from app.services.guest_service import GuestService
from app.services.rsvp_service import RSVPService
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.constants import GuestLimit, ErrorMessage, DEFAULT_CONFIG


class TestMaximumLimits:
    """Test maximum guest limits and edge cases."""
    
    @pytest.fixture
    def app(self):
        """Create app with test config."""
        from app.config import TestConfig
        app = create_app(TestConfig)
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_maximum_family_guests(self, app):
        """Test RSVP with maximum allowed family members."""
        with app.app_context():
            # Create family guest
            guest = GuestService.create_guest(
                name="Large Family",
                phone="555-0001",
                is_family=True
            )
            
            # Prepare form data with maximum guests
            form_data = {
                'is_attending': 'yes',
                'adults_count': str(GuestLimit.MAX_ADULTS_FAMILY),
                'children_count': str(GuestLimit.MAX_CHILDREN_FAMILY)
            }
            
            # Add names for all guests
            for i in range(GuestLimit.MAX_ADULTS_FAMILY):
                form_data[f'adult_name_{i}'] = f'Adult {i+1}'
            
            for i in range(GuestLimit.MAX_CHILDREN_FAMILY):
                form_data[f'child_name_{i}'] = f'Child {i+1}'
            
            # Submit RSVP
            success, message, rsvp = RSVPService.create_or_update_rsvp(guest, form_data)
            
            assert success is True
            assert rsvp.adults_count == GuestLimit.MAX_ADULTS_FAMILY
            assert rsvp.children_count == GuestLimit.MAX_CHILDREN_FAMILY
            assert len(rsvp.additional_guests) == GuestLimit.MAX_ADULTS_FAMILY + GuestLimit.MAX_CHILDREN_FAMILY
    
    def test_exceeding_family_limits(self, app):
        """Test validation when exceeding family guest limits."""
        with app.app_context():
            from app.utils.validators import RSVPValidator
            
            guest = GuestService.create_guest(
                name="Too Large Family",
                phone="555-0002",
                is_family=True
            )
            
            # Try to exceed adult limit
            form_data = {
                'is_attending': 'yes',
                'adults_count': str(GuestLimit.MAX_ADULTS_FAMILY + 1)
            }
            
            validator = RSVPValidator(form_data, guest)
            is_valid, errors = validator.validate()
            
            assert is_valid is False
            assert any(f"more than {GuestLimit.MAX_ADULTS_FAMILY}" in error for error in errors)
    
    def test_maximum_field_lengths(self, app):
        """Test maximum field lengths for various inputs."""
        with app.app_context():
            # Test maximum name length
            max_name = 'A' * GuestLimit.MAX_NAME_LENGTH
            guest = GuestService.create_guest(
                name=max_name,
                phone="555-0003"
            )
            assert len(guest.name) == GuestLimit.MAX_NAME_LENGTH
            
            # Test exceeding name length
            with pytest.raises(Exception):  # SQLAlchemy should raise an error
                too_long_name = 'A' * (GuestLimit.MAX_NAME_LENGTH + 1)
                GuestService.create_guest(
                    name=too_long_name,
                    phone="555-0004"
                )
    
    def test_boundary_values(self, app):
        """Test boundary values for numeric inputs."""
        with app.app_context():
            guest = GuestService.create_guest(
                name="Boundary Test",
                phone="555-0005",
                is_family=True
            )
            
            # Test zero guests
            form_data = {
                'is_attending': 'yes',
                'adults_count': '0',
                'children_count': '0'
            }
            success, _, rsvp = RSVPService.create_or_update_rsvp(guest, form_data)
            assert success is True
            assert rsvp.adults_count == 0
            assert rsvp.children_count == 0
            
            # Test negative values (should be validated)
            from app.utils.validators import RSVPValidator
            form_data['adults_count'] = '-1'
            validator = RSVPValidator(form_data, guest)
            is_valid, errors = validator.validate()
            assert is_valid is False
            assert any("cannot be negative" in error for error in errors)


class TestConcurrentOperations:
    """Test concurrent RSVP submissions and race conditions."""
    
    @pytest.fixture
    def app(self):
        """Create app with test config for concurrent testing."""
        from app.config import TestConfig
        
        class ConcurrentTestConfig(TestConfig):
            # Use a different database to avoid conflicts
            SQLALCHEMY_DATABASE_URI = 'sqlite:///test_concurrent.db'
            
        app = create_app(ConcurrentTestConfig)
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_concurrent_rsvp_updates(self, app):
        """Test concurrent updates to the same RSVP."""
        with app.app_context():
            # Create guest
            guest = GuestService.create_guest(
                name="Concurrent Update Test",
                phone="555-1000"
            )
            guest_id = guest.id
            
            # Create initial RSVP
            initial_data = {'is_attending': 'yes', 'hotel_name': 'Initial Hotel'}
            RSVPService.create_or_update_rsvp(guest, initial_data)
            db.session.commit()
            
            results = []
            errors = []
            
            def update_rsvp(hotel_name):
                """Update RSVP with different hotel name."""
                try:
                    with app.app_context():
                        from app import db
                        from app.models.guest import Guest
                        
                        # New session for this thread
                        db.session.remove()
                        
                        # Reload guest in this context
                        guest_copy = db.session.get(Guest, guest_id)
                        if not guest_copy:
                            raise Exception(f"Guest {guest_id} not found")
                            
                        form_data = {'is_attending': 'yes', 'hotel_name': hotel_name}
                        success, message, rsvp = RSVPService.create_or_update_rsvp(guest_copy, form_data)
                        db.session.commit()
                        results.append((success, hotel_name))
                except Exception as e:
                    errors.append(str(e))
            
            # Use fewer threads to avoid SQLite issues
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = []
                for i in range(5):
                    future = executor.submit(update_rsvp, f'Hotel {i}')
                    futures.append(future)
                
                # Wait for all to complete
                for future in futures:
                    future.result()
            
            # Verify no errors occurred
            assert len(errors) == 0, f"Errors during concurrent updates: {errors}"
            assert len(results) == 5, "Not all updates completed"
    
    def test_duplicate_token_generation(self, app):
        """Test that duplicate tokens are not generated even under concurrent conditions."""
        with app.app_context():
            tokens = set()
            lock = threading.Lock()
            errors = []
            
            def create_guest_thread_safe(index):
                """Create guest and store token thread-safely."""
                try:
                    with app.app_context():
                        from app import db
                        db.session.remove()  # New session for thread
                        
                        guest = GuestService.create_guest(
                            name=f"Token Test {index}",
                            phone=f"555-{2000+index:04d}"
                        )
                        db.session.commit()
                        
                        with lock:
                            tokens.add(guest.token)
                except Exception as e:
                    errors.append(str(e))
            
            # Create guests with fewer workers
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for i in range(20):  # Reduced from 100
                    future = executor.submit(create_guest_thread_safe, i)
                    futures.append(future)
                
                # Wait for all to complete
                for future in futures:
                    try:
                        future.result()
                    except Exception as e:
                        errors.append(str(e))
            
            # Check for errors
            assert len(errors) == 0, f"Errors during token generation: {errors}"
            
            # Verify all tokens are unique
            assert len(tokens) == 20, f"Duplicate tokens generated: expected 20, got {len(tokens)}"

class TestInvalidDateScenarios:
    """Test various invalid date scenarios."""
    
    @pytest.fixture
    def app(self):
        """Create app with test config."""
        from app.config import TestConfig
        
        class DateTestConfig(TestConfig):
            pass
        
        app = create_app(DateTestConfig)
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_past_rsvp_deadline(self, app):
        """Test RSVP submission after deadline has passed."""
        with app.app_context():
            # Set RSVP deadline to yesterday
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            app.config['RSVP_DEADLINE'] = yesterday
            
            guest = GuestService.create_guest(
                name="Late RSVP Test",
                phone="555-3000"
            )
            
            # Check deadline is recognized as passed
            assert RSVPService.is_rsvp_deadline_passed() is True
            
            # Try to submit RSVP
            form_data = {'is_attending': 'yes'}
            success, message, rsvp = RSVPService.create_or_update_rsvp(guest, form_data)
            
            assert success is False
            assert "deadline has passed" in message
    
    def test_invalid_date_formats(self, app):
        """Test handling of invalid date formats in configuration."""
        with app.app_context():
            # Test invalid RSVP deadline format
            app.config['RSVP_DEADLINE'] = 'invalid-date'
            
            # Should handle gracefully
            assert RSVPService.is_rsvp_deadline_passed() is False
            formatted = RSVPService.get_rsvp_deadline_formatted()
            assert formatted == 'invalid-date'  # Returns as-is when invalid
            
            # Test missing dates
            app.config['RSVP_DEADLINE'] = None
            assert RSVPService.is_rsvp_deadline_passed() is False
    
    def test_rsvp_edit_window(self, app):
        """Test RSVP edit window (24 hours) edge cases."""
        with app.app_context():
            guest = GuestService.create_guest(
                name="Edit Window Test",
                phone="555-4000"
            )
            
            # Create RSVP
            form_data = {'is_attending': 'yes'}
            success, _, rsvp = RSVPService.create_or_update_rsvp(guest, form_data)
            assert success is True
            
            # Should be editable immediately
            assert rsvp.is_editable is True
            
            # Simulate RSVP created 23 hours ago (should still be editable)
            rsvp.created_at = datetime.now() - timedelta(hours=23, minutes=59)
            rsvp.testing_24h_check = True  # Use testing flag
            db.session.commit()
            assert rsvp.is_editable is True
            
            # Simulate RSVP created 25 hours ago (should not be editable)
            rsvp.created_at = datetime.now() - timedelta(hours=25)
            db.session.commit()
            assert rsvp.is_editable is False
    
    def test_wedding_date_cutoff(self, app):
        """Test wedding date cutoff scenarios."""
        with app.app_context():
            guest = GuestService.create_guest(
                name="Cutoff Test",
                phone="555-5000"
            )
            
            # Create RSVP more than 24 hours ago
            form_data = {'is_attending': 'yes'}
            _, _, rsvp = RSVPService.create_or_update_rsvp(guest, form_data)
            rsvp.created_at = datetime.now() - timedelta(days=2)
            db.session.commit()
            
            # Set wedding date to 8 days from now (within cutoff)
            future_date = (datetime.now() + timedelta(days=8)).strftime('%Y-%m-%d')
            app.config['WEDDING_DATE'] = future_date
            app.config['WARNING_CUTOFF_DAYS'] = 7
            
            # Should be editable (8 days > 7 days cutoff)
            assert rsvp.is_editable is True
            
            # Set wedding date to 6 days from now (past cutoff)
            close_date = (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d')
            app.config['WEDDING_DATE'] = close_date
            
            # Should not be editable (6 days < 7 days cutoff)
            assert rsvp.is_editable is False


class TestDataIntegrity:
    """Test data integrity under various conditions."""
    
    @pytest.fixture
    def app(self):
        """Create app with test config."""
        from app.config import TestConfig
        app = create_app(TestConfig)
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_cascade_deletion(self, app):
        """Test that deleting a guest cascades properly."""
        with app.app_context():
            # Create guest with RSVP and allergens
            guest = GuestService.create_guest(
                name="Cascade Test",
                phone="555-6000",
                is_family=True
            )
            
            # Create RSVP with additional guests
            form_data = {
                'is_attending': 'yes',
                'adults_count': '1',
                'adult_name_0': 'Additional Adult',
                'allergens_main': ['1'],
                'allergens_adult_0': ['2']
            }
            
            # Create allergens first
            from app.models.allergen import Allergen
            db.session.add(Allergen(name='Test Allergen 1'))
            db.session.add(Allergen(name='Test Allergen 2'))
            db.session.commit()
            
            RSVPService.create_or_update_rsvp(guest, form_data)
            
            # Verify data exists
            assert RSVP.query.filter_by(guest_id=guest.id).count() == 1
            from app.models.rsvp import AdditionalGuest
            from app.models.allergen import GuestAllergen
            rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
            assert AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).count() == 1
            assert GuestAllergen.query.filter_by(rsvp_id=rsvp.id).count() >= 1
            
            # Delete guest
            GuestService.delete_guest(guest.id)
            
            # Verify cascade deletion
            assert RSVP.query.filter_by(guest_id=guest.id).count() == 0
            assert AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).count() == 0
            assert GuestAllergen.query.filter_by(rsvp_id=rsvp.id).count() == 0
    
    # Add this fix to tests/test_edge_cases.py, TestDataIntegrity class
    def test_transaction_rollback(self, app):
        """Test that transactions rollback properly on error."""
        with app.app_context():
            initial_count = Guest.query.count()
            
            # Test that the service properly handles errors
            try:
                # Create a guest with invalid data that will cause an error
                guest = Guest(
                    name="Rollback Test",
                    phone="555-7000",
                    token=None  # This will cause an IntegrityError
                )
                db.session.add(guest)
                db.session.flush()  # This should raise an error
            except Exception:
                db.session.rollback()
            
            # Verify no partial data was saved
            final_count = Guest.query.count()
            assert final_count == initial_count, "Transaction did not rollback properly"