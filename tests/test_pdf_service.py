# tests/test_pdf_service.py
import pytest
import io
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP, AdditionalGuest
from app.models.allergen import Allergen, GuestAllergen
from app.services.pdf_service import PDFService
from PyPDF2 import PdfReader


class TestPDFService:
    """Test cases for PDF generation service."""
    
    @pytest.fixture
    def sample_data(self, app):
        """Create sample data for PDF testing."""
        with app.app_context():
            # Create allergens (check if they exist first)
            allergens = []
            for name in ['Gluten', 'Dairy', 'Nuts', 'Shellfish']:
                allergen = Allergen.query.filter_by(name=name).first()
                if not allergen:
                    allergen = Allergen(name=name)
                    db.session.add(allergen)
                allergens.append(allergen)
            db.session.flush()
            
            # Create guests with RSVPs and allergens
            guests_data = [
                {
                    'name': 'John Doe',
                    'phone': '555-0001',
                    'hotel': 'Hotel Parador Trujillo',
                    'transport_church': True,
                    'transport_reception': True,
                    'transport_hotel': True,
                    'allergens': [allergens[0], allergens[1]]  # Gluten, Dairy
                },
                {
                    'name': 'Jane Smith',
                    'phone': '555-0002',
                    'hotel': 'Hotel Cáceres',
                    'transport_church': True,
                    'transport_reception': False,
                    'transport_hotel': True,
                    'allergens': [allergens[2]]  # Nuts
                },
                {
                    'name': 'Bob Johnson',
                    'phone': '555-0003',
                    'hotel': 'Hotel Parador Trujillo',
                    'transport_church': False,
                    'transport_reception': True,
                    'transport_hotel': False,
                    'allergens': []
                }
            ]
            
            created_guests = []
            for data in guests_data:
                guest = Guest(
                    name=data['name'],
                    phone=data['phone'],
                    token=f"token-{data['phone']}"
                )
                db.session.add(guest)
                db.session.flush()
                
                rsvp = RSVP(
                    guest_id=guest.id,
                    is_attending=True,
                    hotel_name=data['hotel'],
                    transport_to_church=data['transport_church'],
                    transport_to_reception=data['transport_reception'],
                    transport_to_hotel=data['transport_hotel']
                )
                db.session.add(rsvp)
                db.session.flush()
                
                # Add allergens
                for allergen in data['allergens']:
                    guest_allergen = GuestAllergen(
                        rsvp_id=rsvp.id,
                        guest_name=guest.name,
                        allergen_id=allergen.id
                    )
                    db.session.add(guest_allergen)
                
                # Add custom allergen for first guest
                if guest.name == 'John Doe':
                    custom_allergen = GuestAllergen(
                        rsvp_id=rsvp.id,
                        guest_name=guest.name,
                        custom_allergen='Vegetarian'
                    )
                    db.session.add(custom_allergen)
                
                created_guests.append(guest)
            
            db.session.commit()
            
            yield created_guests
            
            # Cleanup
            for guest in created_guests:
                if Guest.query.get(guest.id):
                    db.session.delete(guest)
            db.session.commit()
    
    def test_generate_dietary_pdf_returns_bytes(self, app, sample_data):
        """Test that dietary PDF generation returns bytes."""
        with app.app_context():
            pdf_data = PDFService.generate_dietary_pdf()
            
            assert isinstance(pdf_data, bytes)
            assert len(pdf_data) > 0
    
    def test_dietary_pdf_is_valid_pdf(self, app, sample_data):
        """Test that generated dietary PDF is a valid PDF file."""
        with app.app_context():
            pdf_data = PDFService.generate_dietary_pdf()
            
            # Try to read PDF
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            assert len(reader.pages) > 0
    
    def test_dietary_pdf_contains_guest_names(self, app, sample_data):
        """Test that dietary PDF contains guest names."""
        with app.app_context():
            pdf_data = PDFService.generate_dietary_pdf()
            
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            # Extract text from all pages
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            
            # Check for guest names
            assert 'John Doe' in text
            assert 'Jane Smith' in text
    
    def test_dietary_pdf_contains_allergens(self, app, sample_data):
        """Test that dietary PDF contains allergen information."""
        with app.app_context():
            pdf_data = PDFService.generate_dietary_pdf()
            
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            
            # Check for allergens
            assert 'Gluten' in text
            assert 'Dairy' in text
            assert 'Nuts' in text
    
    def test_dietary_pdf_contains_custom_allergen(self, app, sample_data):
        """Test that dietary PDF includes custom allergens."""
        with app.app_context():
            pdf_data = PDFService.generate_dietary_pdf()
            
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            
            assert 'Vegetarian' in text
    
    def test_dietary_pdf_has_header(self, app, sample_data):
        """Test that dietary PDF contains wedding header."""
        with app.app_context():
            pdf_data = PDFService.generate_dietary_pdf()
            
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            text = reader.pages[0].extract_text()
            
            assert "Irene & Jaime" in text or "Wedding" in text
    
    def test_generate_transport_pdf_returns_bytes(self, app, sample_data):
        """Test that transport PDF generation returns bytes."""
        with app.app_context():
            pdf_data = PDFService.generate_transport_pdf()
            
            assert isinstance(pdf_data, bytes)
            assert len(pdf_data) > 0
    
    def test_transport_pdf_is_valid_pdf(self, app, sample_data):
        """Test that generated transport PDF is a valid PDF file."""
        with app.app_context():
            pdf_data = PDFService.generate_transport_pdf()
            
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            assert len(reader.pages) > 0
    
    def test_transport_pdf_contains_guest_names(self, app, sample_data):
        """Test that transport PDF contains guest names."""
        with app.app_context():
            pdf_data = PDFService.generate_transport_pdf()
            
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            
            assert 'John Doe' in text
            assert 'Jane Smith' in text
    
    def test_transport_pdf_contains_hotel_names(self, app, sample_data):
        """Test that transport PDF contains hotel information."""
        with app.app_context():
            pdf_data = PDFService.generate_transport_pdf()
            
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            
            assert 'Hotel Parador Trujillo' in text or 'Parador Trujillo' in text
            assert 'Cáceres' in text
    
    def test_transport_pdf_contains_route_information(self, app, sample_data):
        """Test that transport PDF contains route descriptions."""
        with app.app_context():
            pdf_data = PDFService.generate_transport_pdf()
            
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            
            # Check for route descriptions
            assert 'Church' in text
            assert 'Reception' in text
            assert 'Hotel' in text
    
    def test_transport_pdf_contains_contact_info(self, app, sample_data):
        """Test that transport PDF includes phone numbers."""
        with app.app_context():
            pdf_data = PDFService.generate_transport_pdf()
            
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            
            # Check for phone numbers
            assert '555-0001' in text or '5550001' in text
    
    def test_transport_pdf_groups_by_hotel(self, app, sample_data):
        """Test that transport PDF groups guests by hotel."""
        with app.app_context():
            pdf_data = PDFService.generate_transport_pdf()
            
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            
            # Both hotels should appear
            assert 'Parador' in text or 'Trujillo' in text
            assert 'Cáceres' in text
    
    def test_pdf_generation_with_no_data(self, app):
        """Test PDF generation when no RSVP data exists."""
        with app.app_context():
            # Should not crash, should generate empty/minimal PDF
            pdf_data = PDFService.generate_dietary_pdf()
            assert isinstance(pdf_data, bytes)
            assert len(pdf_data) > 0
            
            pdf_data = PDFService.generate_transport_pdf()
            assert isinstance(pdf_data, bytes)
            assert len(pdf_data) > 0
    
    def test_dietary_pdf_with_many_allergens(self, app):
        """Test dietary PDF generation with multiple allergens per guest."""
        with app.app_context():
            # Create guest with many allergens
            allergens = []
            for name in ['Gluten', 'Dairy', 'Nuts', 'Shellfish', 'Eggs', 'Soy']:
                allergen = Allergen.query.filter_by(name=name).first()
                if not allergen:
                    allergen = Allergen(name=name)
                    db.session.add(allergen)
                allergens.append(allergen)
            db.session.flush()
            
            guest = Guest(
                name='Allergy Test Guest',
                phone='555-9999',
                token='token-allergy'
            )
            db.session.add(guest)
            db.session.flush()
            
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.flush()
            
            # Add multiple allergens
            for allergen in allergens:
                guest_allergen = GuestAllergen(
                    rsvp_id=rsvp.id,
                    guest_name=guest.name,
                    allergen_id=allergen.id
                )
                db.session.add(guest_allergen)
            
            db.session.commit()
            
            # Generate PDF
            pdf_data = PDFService.generate_dietary_pdf()
            
            assert isinstance(pdf_data, bytes)
            assert len(pdf_data) > 0
            
            # Verify PDF is valid
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            assert len(reader.pages) > 0
            
            # Cleanup
            db.session.delete(guest)
            db.session.commit()
    
    def test_transport_pdf_with_additional_guests(self, app):
        """Test transport PDF includes additional guests in count."""
        with app.app_context():
            guest = Guest(
                name='Family Test',
                phone='555-8888',

                token='token-family',

            )
            db.session.add(guest)
            db.session.flush()
            
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                hotel_name='Family Hotel',
                transport_to_church=True
            )
            db.session.add(rsvp)
            db.session.flush()
            
            # Add additional guests
            additional1 = AdditionalGuest(
                rsvp_id=rsvp.id,
                name='Spouse',
                is_child=False
            )
            additional2 = AdditionalGuest(
                rsvp_id=rsvp.id,
                name='Child',
                is_child=True
            )
            db.session.add(additional1)
            db.session.add(additional2)
            db.session.commit()
            
            # Generate PDF
            pdf_data = PDFService.generate_transport_pdf()
            
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            
            # Should show count of 3 (main + 2 additional)
            assert 'Family Test' in text
            assert '3' in text  # Total passenger count
            
            # Cleanup
            db.session.delete(guest)
            db.session.commit()
    
    def test_pdf_service_page_count(self, app, sample_data):
        """Test that PDFs have multiple pages when needed."""
        with app.app_context():
            dietary_pdf = PDFService.generate_dietary_pdf()
            transport_pdf = PDFService.generate_transport_pdf()
            
            dietary_reader = PdfReader(io.BytesIO(dietary_pdf))
            transport_reader = PdfReader(io.BytesIO(transport_pdf))
            
            # Should have at least 1 page each
            assert len(dietary_reader.pages) >= 1
            assert len(transport_reader.pages) >= 1
    
    def test_pdf_headers_and_footers(self, app, sample_data):
        """Test that PDFs include headers and footers."""
        with app.app_context():
            pdf_data = PDFService.generate_dietary_pdf()
            
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)
            
            # Check first page
            text = reader.pages[0].extract_text()
            
            # Should have wedding names in header
            assert 'Irene' in text or 'Jaime' in text or 'Wedding' in text
            
            # Should have generation date
            assert 'Generated' in text or '202' in text  # Year format