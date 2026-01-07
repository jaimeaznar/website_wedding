# tests/test_utils.py

import pytest
from io import BytesIO
from app import db
from app.utils.import_guests import process_guest_csv
from app.utils.rsvp_helpers import process_allergens
from app.utils.rsvp_processor import RSVPFormProcessor
from app.utils.validators import RSVPValidator
from app.models.allergen import Allergen, GuestAllergen
from unittest.mock import MagicMock, patch


class TestImportGuests:
    def test_process_guest_csv_valid(self):
        """Test processing a valid CSV file."""
        csv_content = b'name,phone,language\nJohn Doe,123456789,en\nJane Smith,987654321,es'
        
        guests = process_guest_csv(csv_content)
        assert len(guests) == 2
        
        # Check first guest
        assert guests[0].name == 'John Doe'
        assert guests[0].phone == '123456789'
        assert guests[0].language_preference == 'en'
        
        # Check second guest
        assert guests[1].name == 'Jane Smith'
        assert guests[1].phone == '987654321'
        assert guests[1].language_preference == 'es'

    def test_process_guest_csv_missing_headers(self):
        """Test processing a CSV with missing required headers."""
        csv_content = b'name,phone,John Doe,123456789'
        
        with pytest.raises(ValueError) as excinfo:
            process_guest_csv(csv_content)
        
        assert "Missing required headers" in str(excinfo.value)

    def test_process_guest_csv_missing_required_fields(self):
        """Test processing a CSV with missing required fields."""
        csv_content = b'name,phone,language\n,123456789,true,false,en'
        
        with pytest.raises(ValueError) as excinfo:
            process_guest_csv(csv_content)
        
        assert "Name and phone are required" in str(excinfo.value)

class TestRSVPHelpers:
    def test_process_allergens(self, app, sample_rsvp):
        """Test processing allergens from form data."""
        with app.app_context():
            # Clean up any existing allergens for this RSVP
            GuestAllergen.query.filter_by(rsvp_id=sample_rsvp.id).delete()
            db.session.commit()
            
            # Create sample allergens within this session
            allergen1 = Allergen.query.filter_by(name="Peanuts").first()
            if not allergen1:
                allergen1 = Allergen(name="Peanuts")
                db.session.add(allergen1)
                
            allergen2 = Allergen.query.filter_by(name="Gluten").first()
            if not allergen2:
                allergen2 = Allergen(name="Gluten")
                db.session.add(allergen2)
                
            db.session.commit()
            
            # Create mock form data
            form = MagicMock()
            form.getlist.return_value = [str(allergen1.id), str(allergen2.id)]
            form.get.return_value = 'Strawberries'
            
            # Call the function
            process_allergens(form, sample_rsvp.id, 'Test Guest', 'main')
            
            # Check if allergens were added
            allergens = GuestAllergen.query.filter_by(
                rsvp_id=sample_rsvp.id,
                guest_name='Test Guest'
            ).all()
            
            # Should have 3 allergens (2 standard + 1 custom)
            assert len(allergens) == 3
            
            # Verify the custom allergen
            custom_allergens = [a for a in allergens if a.custom_allergen == 'Strawberries']
            assert len(custom_allergens) == 1
            
            # Clean up
            for allergen in allergens:
                db.session.delete(allergen)
            db.session.commit()

class TestRSVPValidator:
    def test_validate_attendance(self):
        """Test validating attendance."""
        form = {'is_attending': 'yes'}
        guest = MagicMock()
        validator = RSVPValidator(form, guest)
        
        validator._validate_attendance()
        assert len(validator.errors) == 0
        
        # Invalid attendance
        form = {'is_attending': 'maybe'}
        validator = RSVPValidator(form, guest)
        validator._validate_attendance()
        assert len(validator.errors) == 1
        
        # Missing attendance
        form = {}
        validator = RSVPValidator(form, guest)
        validator._validate_attendance()
        assert len(validator.errors) == 1

    def test_validate_transport(self):
        """Test validating transport selections."""
        form = {
            'hotel_name': 'Test Hotel',
            'transport_to_hotel': 'on'
        }
        guest = MagicMock()
        validator = RSVPValidator(form, guest)
        
        validator._validate_transport()
        assert len(validator.errors) == 0
        
        # Missing hotel name with transport
        form = {
            'hotel_name': ''
        }
        validator = RSVPValidator(form, guest)
        validator._validate_transport()
        assert len(validator.errors) == 1

    def test_validate_family_members(self):
        """Test validating family members information."""
        form = {
            'adults_count': '2',
            'children_count': '1',
            'adult_name_0': 'Adult 1',
            'adult_name_1': 'Adult 2',
            'child_name_0': 'Child 1'
        }
        guest = MagicMock()
        validator = RSVPValidator(form, guest)
        
        validator._validate_family_members()
        assert len(validator.errors) == 0
        
        # Missing adult name
        form = {
            'adults_count': '2',
            'children_count': '0',
            'adult_name_0': 'Adult 1',
            'adult_name_1': ''
        }
        validator = RSVPValidator(form, guest)
        validator._validate_family_members()
        assert len(validator.errors) == 1
        
        # Too many adults
        form = {
            'adults_count': '15'
        }
        validator = RSVPValidator(form, guest)
        validator._validate_family_members()
        assert len(validator.errors) == 1

class TestRSVPProcessor:
    @patch('app.utils.rsvp_processor.RSVPValidator')
    def test_process_success(self, mock_validator, app, sample_guest):
        """Test successful RSVP processing."""
        with app.app_context():
            # First make sure there's no existing RSVP
            from app.models.rsvp import RSVP
            RSVP.query.filter_by(guest_id=sample_guest.id).delete()
            db.session.commit()
            
            # Mock the validator to pass validation
            mock_validator.return_value.validate.return_value = (True, [])
            
            # Create form data
            form_data = {
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel'            }
            
            # Create processor with actual guest instance
            processor = RSVPFormProcessor(form_data, sample_guest)
            
            # Only mock specific internal methods that interact with DB
            processor._process_main_guest_allergens = MagicMock()
            if hasattr(processor, '_process_additional_guests'):
                processor._process_additional_guests = MagicMock()
            
            # Call process
            with patch.object(db.session, 'commit') as mock_commit:
                success, message = processor.process()
                
            # Check result
            assert success is True
            
            # Clean up any created RSVP
            RSVP.query.filter_by(guest_id=sample_guest.id).delete()
            db.session.commit()

    @patch('app.utils.rsvp_processor.RSVPValidator')
    def test_process_validation_failure(self, mock_validator, app, sample_guest):
        """Test RSVP processing with validation failure."""
        with app.app_context():
            # Mock the validator to fail validation
            mock_validator.return_value.validate.return_value = (False, ["Error 1", "Error 2"])
    
            # Create form data
            form_data = {
                'is_attending': 'yes',
                'hotel_name': ''  # Missing required hotel
            }
    
            # Create processor
            processor = RSVPFormProcessor(form_data, sample_guest)
    
            # Call process
            success, message = processor.process()
    
            # Check result
            assert success is False
            assert "Error 1\nError 2" == message