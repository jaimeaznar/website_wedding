# tests/test_utils.py

import pytest
from io import BytesIO
from app.utils.import_guests import process_guest_csv
from app.utils.rsvp_helpers import process_allergens
from app.utils.rsvp_processor import RSVPFormProcessor
from app.utils.validators import RSVPValidator
from app.models.allergen import GuestAllergen
from unittest.mock import MagicMock, patch

class TestImportGuests:
    def test_process_guest_csv_valid(self):
        """Test processing a valid CSV file."""
        csv_content = b'name,phone,email,has_plus_one,is_family,language\nJohn Doe,123456789,john@example.com,true,false,en\nJane Smith,987654321,jane@example.com,false,true,es'
        
        guests = process_guest_csv(csv_content)
        assert len(guests) == 2
        
        # Check first guest
        assert guests[0].name == 'John Doe'
        assert guests[0].phone == '123456789'
        assert guests[0].email == 'john@example.com'
        assert guests[0].has_plus_one is True
        assert guests[0].is_family is False
        assert guests[0].language_preference == 'en'
        
        # Check second guest
        assert guests[1].name == 'Jane Smith'
        assert guests[1].phone == '987654321'
        assert guests[1].email == 'jane@example.com'
        assert guests[1].has_plus_one is False
        assert guests[1].is_family is True
        assert guests[1].language_preference == 'es'

    def test_process_guest_csv_missing_headers(self):
        """Test processing a CSV with missing required headers."""
        csv_content = b'name,phone,email\nJohn Doe,123456789,john@example.com'
        
        with pytest.raises(ValueError) as excinfo:
            process_guest_csv(csv_content)
        
        assert "Missing required headers" in str(excinfo.value)

    def test_process_guest_csv_missing_required_fields(self):
        """Test processing a CSV with missing required fields."""
        csv_content = b'name,phone,email,has_plus_one,is_family,language\n,123456789,john@example.com,true,false,en'
        
        with pytest.raises(ValueError) as excinfo:
            process_guest_csv(csv_content)
        
        assert "Name and phone are required" in str(excinfo.value)

class TestRSVPHelpers:
    def test_process_allergens(self, app, sample_rsvp, sample_allergens):
        """Test processing allergens from form data."""
        with app.app_context():
            # Create mock form data
            form = {}
            form.setlist = MagicMock(return_value=[str(sample_allergens[0].id), str(sample_allergens[1].id)])
            form.get = MagicMock(return_value='Strawberries')
            
            # Call the function
            process_allergens(form, sample_rsvp.id, 'Test Guest', 'main')
            
            # Check if allergens were added
            allergens = GuestAllergen.query.filter_by(
                rsvp_id=sample_rsvp.id,
                guest_name='Test Guest'
            ).all()
            
            # Should have one for the custom allergen
            assert len(allergens) == 1
            assert allergens[0].custom_allergen == 'Strawberries'

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
            'transport_to_church': 'on',
            'transport_to_hotel': 'on'
        }
        guest = MagicMock()
        validator = RSVPValidator(form, guest)
        
        validator._validate_transport()
        assert len(validator.errors) == 0
        
        # Missing hotel name with transport
        form = {
            'hotel_name': '',
            'transport_to_church': 'on'
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
            # Mock the validator to pass validation
            mock_validator.return_value.validate.return_value = (True, [])
            
            # Create form data
            form_data = {
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel',
                'transport_to_church': 'on'
            }
            
            # Create processor
            processor = RSVPFormProcessor(form_data, sample_guest)
            
            # Override _get_or_create_rsvp to avoid database calls
            processor._get_or_create_rsvp = MagicMock()
            processor.rsvp = MagicMock()
            
            # Call process
            success, message = processor.process()
            
            # Check result
            assert success is True
            assert "successfully" in message
            
            # Verify methods were called
            processor._get_or_create_rsvp.assert_called_once()
            assert processor._process_attendance.called
            assert processor._process_hotel_info.called
            assert processor._process_transport.called
            assert processor._process_main_guest_allergens.called

    @patch('app.utils.rsvp_processor.RSVPValidator')
    def test_process_validation_failure(self, mock_validator, app, sample_guest):
        """Test RSVP processing with validation failure."""
        with app.app_context():
            # Mock the validator to fail validation
            mock_validator.return_value.validate.return_value = (False, ["Error 1", "Error 2"])
            
            # Create form data
            form_data = {
                'is_attending': 'yes',
                'hotel_name': '',  # Missing required hotel
                'transport_to_church': 'on'
            }
            
            # Create processor
            processor = RSVPFormProcessor(form_data, sample_guest)
            
            # Call process
            success, message = processor.process()
            
            # Check result
            assert success is False
            assert "Error 1\nError 2" == message
            
            # Verify no database operations were attempted
            assert not hasattr(processor, 'rsvp')