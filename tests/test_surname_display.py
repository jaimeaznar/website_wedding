# tests/test_surname_display.py
"""
Tests for surname display functionality in dietary restrictions.
Verifies that guest names include surnames in:
- Allergen service (get_guests_with_allergen)
- PDF generation (children menu section)
- Dashboard display
"""

import pytest
import io
import secrets
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP, AdditionalGuest
from app.models.allergen import Allergen, GuestAllergen
from app.services.allergen_service import AllergenService
from app.services.pdf_service import PDFService
from PyPDF2 import PdfReader


class TestSurnameInAllergenService:
    """Test surname display in AllergenService.get_guests_with_allergen()"""

    def test_main_guest_with_surname(self, app):
        """Test that main guest shows 'Name Surname' format."""
        with app.app_context():
            # Create allergen
            allergen = Allergen.query.filter_by(name='Surname Test Allergen').first()
            if not allergen:
                allergen = Allergen(name='Surname Test Allergen')
                db.session.add(allergen)
                db.session.commit()

            # Create guest WITH surname
            guest = Guest(
                name='María',
                surname='García',
                phone='555-SURNAME1',
                token=secrets.token_urlsafe(32),
                language_preference='es'
            )
            db.session.add(guest)
            db.session.commit()

            # Create RSVP
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.flush()

            # Add allergen for main guest
            guest_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,  # Stored as 'María'
                allergen_id=allergen.id
            )
            db.session.add(guest_allergen)
            db.session.commit()

            # Get guests with allergen
            guests_list = AllergenService.get_guests_with_allergen('Surname Test Allergen')

            # Verify surname is included
            assert 'María García' in guests_list, f"Expected 'María García' in {guests_list}"

            # Cleanup
            db.session.delete(guest)
            db.session.commit()

    def test_main_guest_without_surname(self, app):
        """Test that main guest without surname shows just name."""
        with app.app_context():
            # Create allergen
            allergen = Allergen.query.filter_by(name='No Surname Test Allergen').first()
            if not allergen:
                allergen = Allergen(name='No Surname Test Allergen')
                db.session.add(allergen)
                db.session.commit()

            # Create guest WITHOUT surname
            guest = Guest(
                name='Pedro',
                surname=None,  # No surname
                phone='555-NOSURNAME',
                token=secrets.token_urlsafe(32),
                language_preference='es'
            )
            db.session.add(guest)
            db.session.commit()

            # Create RSVP
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.flush()

            # Add allergen
            guest_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,
                allergen_id=allergen.id
            )
            db.session.add(guest_allergen)
            db.session.commit()

            # Get guests with allergen
            guests_list = AllergenService.get_guests_with_allergen('No Surname Test Allergen')

            # Verify just name is shown (no extra spaces or formatting)
            assert 'Pedro' in guests_list, f"Expected 'Pedro' in {guests_list}"
            assert 'Pedro ' not in guests_list, "Should not have trailing space"

            # Cleanup
            db.session.delete(guest)
            db.session.commit()

    def test_additional_guest_with_family_surname(self, app):
        """Test that additional guest shows 'Name (Surname)' format."""
        with app.app_context():
            # Create allergen
            allergen = Allergen.query.filter_by(name='Additional Guest Allergen').first()
            if not allergen:
                allergen = Allergen(name='Additional Guest Allergen')
                db.session.add(allergen)
                db.session.commit()

            # Create main guest with surname
            guest = Guest(
                name='Juan',
                surname='López',
                phone='555-ADDITIONAL',
                token=secrets.token_urlsafe(32),
                language_preference='es'
            )
            db.session.add(guest)
            db.session.commit()

            # Create RSVP
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                adults_count=2,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.flush()

            # Add additional adult guest
            additional = AdditionalGuest(
                rsvp_id=rsvp.id,
                name='Ana',
                is_child=False
            )
            db.session.add(additional)

            # Add allergen for the ADDITIONAL guest (not main)
            guest_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name='Ana',  # Additional guest's name
                allergen_id=allergen.id
            )
            db.session.add(guest_allergen)
            db.session.commit()

            # Get guests with allergen
            guests_list = AllergenService.get_guests_with_allergen('Additional Guest Allergen')

            # Verify additional guest shows family surname in parentheses
            assert 'Ana (López)' in guests_list, f"Expected 'Ana (López)' in {guests_list}"

            # Cleanup
            db.session.delete(guest)
            db.session.commit()

    def test_additional_guest_without_family_surname(self, app):
        """Test that additional guest without family surname shows just name."""
        with app.app_context():
            # Create allergen
            allergen = Allergen.query.filter_by(name='No Family Surname Allergen').first()
            if not allergen:
                allergen = Allergen(name='No Family Surname Allergen')
                db.session.add(allergen)
                db.session.commit()

            # Create main guest WITHOUT surname
            guest = Guest(
                name='Carlos',
                surname=None,
                phone='555-NOFAMILY',
                token=secrets.token_urlsafe(32),
                language_preference='es'
            )
            db.session.add(guest)
            db.session.commit()

            # Create RSVP
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                adults_count=2,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.flush()

            # Add additional guest
            additional = AdditionalGuest(
                rsvp_id=rsvp.id,
                name='Elena',
                is_child=False
            )
            db.session.add(additional)

            # Add allergen for additional guest
            guest_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name='Elena',
                allergen_id=allergen.id
            )
            db.session.add(guest_allergen)
            db.session.commit()

            # Get guests with allergen
            guests_list = AllergenService.get_guests_with_allergen('No Family Surname Allergen')

            # Verify just name shown (no parentheses)
            assert 'Elena' in guests_list, f"Expected 'Elena' in {guests_list}"
            assert 'Elena (' not in guests_list, "Should not have parentheses without surname"

            # Cleanup
            db.session.delete(guest)
            db.session.commit()

    def test_custom_allergen_with_surname(self, app):
        """Test that custom allergens also show surnames."""
        with app.app_context():
            # Create guest with surname
            guest = Guest(
                name='Rosa',
                surname='Martínez',
                phone='555-CUSTOM',
                token=secrets.token_urlsafe(32),
                language_preference='es'
            )
            db.session.add(guest)
            db.session.commit()

            # Create RSVP
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.flush()

            # Add CUSTOM allergen (no allergen_id)
            guest_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,
                allergen_id=None,
                custom_allergen='Vegetariano'
            )
            db.session.add(guest_allergen)
            db.session.commit()

            # Get guests with custom allergen
            guests_list = AllergenService.get_guests_with_allergen('Vegetariano')

            # Verify surname is included for custom allergens too
            assert 'Rosa Martínez' in guests_list, f"Expected 'Rosa Martínez' in {guests_list}"

            # Cleanup
            db.session.delete(guest)
            db.session.commit()


class TestSurnameInPDFChildrenMenu:
    """Test surname display in PDF children menu section."""

    def test_children_menu_includes_parent_surname(self, app):
        """Test that PDF children menu shows parent with surname."""
        with app.app_context():
            # Create guest with surname
            guest = Guest(
                name='Luis',
                surname='Fernández',
                phone='555-PDFPARENT',
                token=secrets.token_urlsafe(32),
                language_preference='es'
            )
            db.session.add(guest)
            db.session.commit()

            # Create RSVP
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                children_count=1,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.flush()

            # Add child who needs menu
            child = AdditionalGuest(
                rsvp_id=rsvp.id,
                name='Sofía',
                is_child=True,
                needs_menu=True
            )
            db.session.add(child)
            db.session.commit()

            # Get children menu data
            children_data = PDFService._get_children_menu_data()

            # Find our child in the with_menu list
            our_child = None
            for c in children_data['with_menu']:
                if c['name'] == 'Sofía (Fernández)':
                    our_child = c
                    break

            assert our_child is not None, f"Expected child 'Sofía (Fernández)' in {children_data['with_menu']}"
            assert our_child['parent'] == 'Luis Fernández', f"Expected parent 'Luis Fernández', got '{our_child['parent']}'"

            # Cleanup
            db.session.delete(guest)
            db.session.commit()

    def test_children_menu_without_parent_surname(self, app):
        """Test that PDF children menu works when parent has no surname."""
        with app.app_context():
            # Create guest without surname
            guest = Guest(
                name='Miguel',
                surname=None,
                phone='555-PDFNOSURNAME',
                token=secrets.token_urlsafe(32),
                language_preference='es'
            )
            db.session.add(guest)
            db.session.commit()

            # Create RSVP
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                children_count=1,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.flush()

            # Add child
            child = AdditionalGuest(
                rsvp_id=rsvp.id,
                name='Pablo',
                is_child=True,
                needs_menu=True
            )
            db.session.add(child)
            db.session.commit()

            # Get children menu data
            children_data = PDFService._get_children_menu_data()

            # Find our child - should just be 'Pablo' without parentheses
            our_child = None
            for c in children_data['with_menu']:
                if c['name'] == 'Pablo':
                    our_child = c
                    break

            assert our_child is not None, f"Expected child 'Pablo' in {children_data['with_menu']}"
            assert our_child['parent'] == 'Miguel', f"Expected parent 'Miguel', got '{our_child['parent']}'"

            # Cleanup
            db.session.delete(guest)
            db.session.commit()

    def test_dietary_pdf_contains_surnames(self, app):
        """Test that generated dietary PDF contains guest surnames."""
        with app.app_context():
            # Create allergen
            allergen = Allergen.query.filter_by(name='PDF Surname Test').first()
            if not allergen:
                allergen = Allergen(name='PDF Surname Test')
                db.session.add(allergen)
                db.session.commit()

            # Create guest with surname
            guest = Guest(
                name='Carmen',
                surname='Ruiz',
                phone='555-PDFTEST',
                token=secrets.token_urlsafe(32),
                language_preference='es'
            )
            db.session.add(guest)
            db.session.commit()

            # Create RSVP
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.flush()

            # Add allergen
            guest_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,
                allergen_id=allergen.id
            )
            db.session.add(guest_allergen)
            db.session.commit()

            # Generate PDF
            pdf_data = PDFService.generate_dietary_pdf()

            # Extract text from PDF
            pdf_buffer = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_buffer)

            text = ''
            for page in reader.pages:
                text += page.extract_text()

            # Verify surname appears in PDF
            assert 'Carmen Ruiz' in text, f"Expected 'Carmen Ruiz' in PDF text"

            # Cleanup
            db.session.delete(guest)
            db.session.commit()


class TestSurnameInDashboard:
    """Test surname display in admin dashboard (integration test)."""

    def test_dashboard_dietary_shows_surname(self, client, app):
        """Test that dashboard RSVP table shows surnames in dietary restrictions."""
        with app.app_context():
            # Create allergen
            allergen = Allergen.query.filter_by(name='Dashboard Surname Test').first()
            if not allergen:
                allergen = Allergen(name='Dashboard Surname Test')
                db.session.add(allergen)
                db.session.commit()

            # Create guest with surname
            guest = Guest(
                name='Antonio',
                surname='Sánchez',
                phone='555-DASHBOARD',
                token=secrets.token_urlsafe(32),
                language_preference='es'
            )
            db.session.add(guest)
            db.session.commit()

            # Create RSVP
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.flush()

            # Add allergen
            guest_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,
                allergen_id=allergen.id
            )
            db.session.add(guest_allergen)
            db.session.commit()

            # Set admin cookie and access dashboard
            client.set_cookie('admin_authenticated', 'true')
            response = client.get('/admin/dashboard')

            assert response.status_code == 200

            # Check response contains the surname
            response_text = response.data.decode('utf-8')

            # The template should show "Antonio Sánchez" for the main guest
            assert 'Antonio' in response_text
            assert 'Sánchez' in response_text

            # Cleanup
            db.session.delete(guest)
            db.session.commit()

    def test_dietary_report_page_shows_surname(self, client, app):
        """Test that dietary report page shows surnames."""
        with app.app_context():
            # Create allergen
            allergen = Allergen.query.filter_by(name='Report Page Test').first()
            if not allergen:
                allergen = Allergen(name='Report Page Test')
                db.session.add(allergen)
                db.session.commit()

            # Create guest with surname
            guest = Guest(
                name='Marta',
                surname='Díaz',
                phone='555-REPORT',
                token=secrets.token_urlsafe(32),
                language_preference='es'
            )
            db.session.add(guest)
            db.session.commit()

            # Create RSVP
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.flush()

            # Add allergen
            guest_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,
                allergen_id=allergen.id
            )
            db.session.add(guest_allergen)
            db.session.commit()

            # Set admin cookie and access dietary report
            client.set_cookie('admin_authenticated', 'true')
            response = client.get('/admin/reports/dietary')

            assert response.status_code == 200

            # Check response contains full name with surname
            response_text = response.data.decode('utf-8')
            assert 'Marta Díaz' in response_text, f"Expected 'Marta Díaz' in response"

            # Cleanup
            db.session.delete(guest)
            db.session.commit()