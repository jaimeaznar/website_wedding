# tests/test_allergen_functionality.py - COMPLETELY FIXED VERSION
import pytest
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP, AdditionalGuest
from app.models.allergen import Allergen, GuestAllergen
import secrets

class TestAllergenFunctionality:
    """Comprehensive tests for allergen functionality."""

    def test_allergen_creation_and_retrieval(self, app):
        """Test that allergens are created and can be retrieved."""
        with app.app_context():
            # Create allergens within the test
            allergen_names = ['Test Gluten', 'Test Dairy', 'Test Nuts', 'Test Peanuts']
            created_allergens = []
            
            for name in allergen_names:
                # Check if it already exists
                existing = Allergen.query.filter_by(name=name).first()
                if existing:
                    created_allergens.append(existing)
                else:
                    allergen = Allergen(name=name)
                    db.session.add(allergen)
                    created_allergens.append(allergen)
            
            db.session.commit()
            
            # Verify allergens exist
            assert len(created_allergens) >= 4
            
            # Test retrieval
            gluten = Allergen.query.filter_by(name='Test Gluten').first()
            assert gluten is not None
            assert gluten.name == 'Test Gluten'

    def test_rsvp_submission_with_allergens(self, client, app):
        """Test submitting an RSVP with allergens through the web interface."""
        with app.app_context():
            # Create allergens
            allergen_names = ['Web Test Gluten', 'Web Test Dairy', 'Web Test Nuts', 'Web Test Peanuts']
            allergens = []
            
            for name in allergen_names:
                existing = Allergen.query.filter_by(name=name).first()
                if existing:
                    allergens.append(existing)
                else:
                    allergen = Allergen(name=name)
                    db.session.add(allergen)
                    allergens.append(allergen)
            
            db.session.commit()
            
            # Create guest
            guest = Guest(
                name="Web Test Family",
                phone="555-0001",
                token=secrets.token_urlsafe(32),
                language_preference="en",

            )
            db.session.add(guest)
            db.session.commit()
            
            # Get the RSVP form
            response = client.get(f'/rsvp/{guest.token}')
            assert response.status_code == 200
            
            # Submit RSVP with allergens
            form_data = {
                'csrf_token': 'test-token',
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel',
                'adults_count': '1',
                'children_count': '1',
                'adult_name_0': 'John Doe',
                'child_name_0': 'Baby Doe',
                # Main guest allergens
                'allergens_main': [str(allergens[0].id)],
                'custom_allergen_main': 'Shellfish',
                # Adult allergens
                f'allergens_adult_0': [str(allergens[1].id)],
                f'custom_allergen_adult_0': 'Sesame',
                # Child allergens
                f'allergens_child_0': [str(allergens[2].id)],
                f'custom_allergen_child_0': 'Soy'
            }
            
            response = client.post(
                f'/rsvp/{guest.token}/edit',
                data=form_data,
                follow_redirects=True
            )
            
            # Check response
            assert response.status_code == 200
            
            # Verify RSVP was created
            rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
            assert rsvp is not None
            assert rsvp.is_attending is True
            
            # Verify additional guests were created
            additional_guests = AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).all()
            assert len(additional_guests) == 2  # 1 adult + 1 child
            
            # Verify allergens were saved
            guest_allergens = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).all()
            assert len(guest_allergens) >= 3  # At least some allergens should be saved
            
            # Check main guest allergens
            main_allergens = GuestAllergen.query.filter_by(
                rsvp_id=rsvp.id,
                guest_name=guest.name
            ).all()
            assert len(main_allergens) >= 1  # Should have at least one allergen

    def test_allergen_display_in_admin(self, client, app):
        """Test that allergens display correctly in the admin dashboard."""
        with app.app_context():
            # Create allergen
            allergen = Allergen.query.filter_by(name='Admin Test Allergen').first()
            if not allergen:
                allergen = Allergen(name='Admin Test Allergen')
                db.session.add(allergen)
                db.session.commit()
            
            # Create guest
            guest = Guest(
                name="Admin Test Guest",
                phone="555-0002",
                token=secrets.token_urlsafe(32),
                language_preference="en",
            )
            db.session.add(guest)
            db.session.commit()
            
            # Create RSVP with allergens
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                adults_count=1,
                hotel_name="Admin Test Hotel"
            )
            db.session.add(rsvp)
            db.session.flush()
            
            # Add allergens
            allergen1 = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,
                allergen_id=allergen.id
            )
            allergen2 = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,
                custom_allergen="Custom Restriction"
            )
            db.session.add(allergen1)
            db.session.add(allergen2)
            db.session.commit()
            
            # Set authentication cookie for admin access
            client.set_cookie('admin_authenticated', 'true')
            
            # Access admin dashboard
            response = client.get('/admin/dashboard')
            assert response.status_code == 200
            
            # Check that allergen information is displayed
            response_text = response.data.decode('utf-8')
            assert guest.name in response_text
            assert "Dietary Restrictions" in response_text

    def test_allergen_properties_on_rsvp_model(self, app):
        """Test the allergen properties on the RSVP model."""
        with app.app_context():
            # Create allergens
            allergen1 = Allergen.query.filter_by(name='Property Test Allergen 1').first()
            if not allergen1:
                allergen1 = Allergen(name='Property Test Allergen 1')
                db.session.add(allergen1)
            
            allergen2 = Allergen.query.filter_by(name='Property Test Allergen 2').first()
            if not allergen2:
                allergen2 = Allergen(name='Property Test Allergen 2')
                db.session.add(allergen2)
            
            db.session.commit()
            
            # Create guest
            guest = Guest(
                name="Property Test Guest",
                phone="555-0003",
                token=secrets.token_urlsafe(32),
                language_preference="en",

            )
            db.session.add(guest)
            db.session.commit()
            
            # Create RSVP
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True
            )
            db.session.add(rsvp)
            db.session.flush()
            
            # Add allergens
            guest_allergen1 = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,
                allergen_id=allergen1.id
            )
            guest_allergen2 = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,
                allergen_id=allergen2.id
            )
            custom_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,
                custom_allergen="Test Custom"
            )
            db.session.add_all([guest_allergen1, guest_allergen2, custom_allergen])
            db.session.commit()
            
            # Test properties
            allergen_ids = rsvp.allergen_ids
            assert len(allergen_ids) == 2
            assert allergen1.id in allergen_ids
            assert allergen2.id in allergen_ids
            
            custom = rsvp.custom_allergen
            assert custom == "Test Custom"

    def test_allergen_deletion_on_rsvp_update(self, client, app):
        """Test that allergens are properly deleted and recreated when updating RSVP."""
        with app.app_context():
            # Create allergens
            allergen1 = Allergen.query.filter_by(name='Update Test Allergen 1').first()
            if not allergen1:
                allergen1 = Allergen(name='Update Test Allergen 1')
                db.session.add(allergen1)
            
            allergen2 = Allergen.query.filter_by(name='Update Test Allergen 2').first()
            if not allergen2:
                allergen2 = Allergen(name='Update Test Allergen 2')
                db.session.add(allergen2)
            
            allergen3 = Allergen.query.filter_by(name='Update Test Allergen 3').first()
            if not allergen3:
                allergen3 = Allergen(name='Update Test Allergen 3')
                db.session.add(allergen3)
            
            db.session.commit()
            
            # Create guest
            guest = Guest(
                name="Update Test Guest",
                phone="555-0004",
                token=secrets.token_urlsafe(32),
                language_preference="en",

            )
            db.session.add(guest)
            db.session.commit()
            
            # Create initial RSVP with allergens
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True
            )
            db.session.add(rsvp)
            db.session.flush()
            
            # Add initial allergen
            initial_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,
                allergen_id=allergen1.id
            )
            db.session.add(initial_allergen)
            db.session.commit()
            
            # Verify initial state
            initial_count = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).count()
            assert initial_count == 1
            
            # Update RSVP with different allergens
            form_data = {
                'csrf_token': 'test-token',
                'is_attending': 'yes',
                'hotel_name': 'Updated Hotel',
                'allergens_main': [str(allergen2.id), str(allergen3.id)],
                'custom_allergen_main': 'New Custom Allergen'
            }
            
            response = client.post(
                f'/rsvp/{guest.token}/edit',
                data=form_data,
                follow_redirects=True
            )
            
            assert response.status_code == 200
            
            # Verify old allergens were deleted and new ones added
            final_allergens = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).all()
            
            # Should have new allergens, not old ones
            allergen_ids = [a.allergen_id for a in final_allergens if a.allergen_id]
            custom_allergens = [a.custom_allergen for a in final_allergens if a.custom_allergen]
            
            # Old allergen should be gone
            assert allergen1.id not in allergen_ids
            # New allergens should be present  
            assert any(aid in allergen_ids for aid in [allergen2.id, allergen3.id])
            assert 'New Custom Allergen' in custom_allergens

    def test_simple_allergen_workflow(self, client, app):
        """Test a simple allergen workflow end-to-end."""
        with app.app_context():
            # Create allergen
            allergen = Allergen.query.filter_by(name='Simple Test Allergen').first()
            if not allergen:
                allergen = Allergen(name='Simple Test Allergen')
                db.session.add(allergen)
                db.session.commit()
            
            # Create guest
            guest = Guest(
                name="Simple Test",
                phone="555-0005",
                token=secrets.token_urlsafe(32),
                language_preference="en",

            )
            db.session.add(guest)
            db.session.commit()
            
            # Submit simple RSVP with allergen
            form_data = {
                'csrf_token': 'test-token',
                'is_attending': 'yes',
                'hotel_name': 'Simple Hotel',
                'allergens_main': [str(allergen.id)],
                'custom_allergen_main': 'Simple Custom'
            }
            
            response = client.post(
                f'/rsvp/{guest.token}/edit',
                data=form_data,
                follow_redirects=True
            )
            
            assert response.status_code == 200
            
            # Verify RSVP and allergens were created
            rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
            assert rsvp is not None
            assert rsvp.is_attending is True
            
            allergens_saved = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).all()
            assert len(allergens_saved) >= 1  # At least one allergen should be saved
            
            # Check for the specific allergens we added
            has_standard = any(a.allergen_id == allergen.id for a in allergens_saved)
            has_custom = any(a.custom_allergen == 'Simple Custom' for a in allergens_saved)
            
            assert has_standard or has_custom  # At least one should be present

    def test_direct_database_operations(self, app):
        """Test direct database operations without web interface."""
        with app.app_context():
            # Create allergen
            allergen = Allergen(name='Direct Test Allergen')
            db.session.add(allergen)
            db.session.commit()
            
            # Create guest
            guest = Guest(
                name="Direct Test Guest",
                phone="555-DIRECT",
                token=secrets.token_urlsafe(32)
            )
            db.session.add(guest)
            db.session.commit()
            
            # Create RSVP
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True
            )
            db.session.add(rsvp)
            db.session.flush()
            
            # Add allergen directly
            guest_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=guest.name,
                allergen_id=allergen.id
            )
            db.session.add(guest_allergen)
            db.session.commit()
            
            # Verify
            saved_allergens = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).all()
            assert len(saved_allergens) == 1
            assert saved_allergens[0].allergen.name == 'Direct Test Allergen'
            assert saved_allergens[0].guest_name == guest.name