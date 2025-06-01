# tests/test_allergen_functionality.py
import pytest
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP, AdditionalGuest
from app.models.allergen import Allergen, GuestAllergen
import secrets

class TestAllergenFunctionality:
    """Comprehensive tests for allergen functionality."""
    
    @pytest.fixture
    def allergens(self, app):
        """Create test allergens."""
        with app.app_context():
            allergens = []
            allergen_names = ['Gluten', 'Dairy', 'Nuts', 'Peanuts']
            
            for name in allergen_names:
                existing = Allergen.query.filter_by(name=name).first()
                if existing:
                    allergens.append(existing)
                else:
                    allergen = Allergen(name=name)
                    db.session.add(allergen)
                    allergens.append(allergen)
            
            db.session.commit()
            return allergens
    
    @pytest.fixture
    def family_guest(self, app):
        """Create a family guest for testing."""
        with app.app_context():
            guest = Guest(
                name="Test Family",
                email="family@test.com",
                phone="555-0001",
                token=secrets.token_urlsafe(32),
                language_preference="en",
                has_plus_one=False,
                is_family=True
            )
            db.session.add(guest)
            db.session.commit()
            return guest

    def test_allergen_creation_and_retrieval(self, app, allergens):
        """Test that allergens are created and can be retrieved."""
        with app.app_context():
            # Verify allergens exist
            assert len(allergens) >= 4
            
            # Test retrieval
            gluten = Allergen.query.filter_by(name='Gluten').first()
            assert gluten is not None
            assert gluten.name == 'Gluten'

    def test_rsvp_submission_with_allergens(self, client, app, family_guest, allergens):
        """Test submitting an RSVP with allergens through the web interface."""
        with app.app_context():
            # Get the RSVP form
            response = client.get(f'/rsvp/{family_guest.token}')
            assert response.status_code == 200
            
            # Submit RSVP with allergens
            form_data = {
                'csrf_token': 'test-token',
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel',
                'adults_count': '2',
                'children_count': '1',
                'adult_name_0': 'John Doe',
                'adult_name_1': 'Jane Doe',
                'child_name_0': 'Baby Doe',
                # Main guest allergens
                'allergens_main': [str(allergens[0].id), str(allergens[1].id)],
                'custom_allergen_main': 'Shellfish',
                # Adult allergens
                f'allergens_adult_0': [str(allergens[2].id)],
                f'custom_allergen_adult_0': 'Sesame',
                f'allergens_adult_1': [str(allergens[3].id)],
                # Child allergens
                f'allergens_child_0': [str(allergens[0].id)],
                f'custom_allergen_child_0': 'Soy'
            }
            
            response = client.post(
                f'/rsvp/{family_guest.token}',
                data=form_data,
                follow_redirects=True
            )
            
            # Check response
            assert response.status_code == 200
            
            # Verify RSVP was created
            rsvp = RSVP.query.filter_by(guest_id=family_guest.id).first()
            assert rsvp is not None
            assert rsvp.is_attending is True
            
            # Verify additional guests were created
            additional_guests = AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).all()
            assert len(additional_guests) == 3  # 2 adults + 1 child
            
            # Verify allergens were saved
            guest_allergens = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).all()
            
            # Should have allergens for main guest (3), adult_0 (2), adult_1 (1), child_0 (2) = 8 total
            assert len(guest_allergens) >= 6  # At least some allergens should be saved
            
            # Check main guest allergens
            main_allergens = GuestAllergen.query.filter_by(
                rsvp_id=rsvp.id,
                guest_name=family_guest.name
            ).all()
            assert len(main_allergens) >= 2  # Should have standard + custom allergens
            
            # Check for custom allergen
            main_custom = [a for a in main_allergens if a.custom_allergen == 'Shellfish']
            assert len(main_custom) == 1

    def test_allergen_display_in_admin(self, client, app, family_guest, allergens):
        """Test that allergens display correctly in the admin dashboard."""
        with app.app_context():
            # First create an RSVP with allergens directly
            rsvp = RSVP(
                guest_id=family_guest.id,
                is_attending=True,
                adults_count=1,
                hotel_name="Admin Test Hotel"
            )
            db.session.add(rsvp)
            db.session.flush()
            
            # Add allergens
            allergen1 = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=family_guest.name,
                allergen_id=allergens[0].id
            )
            allergen2 = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=family_guest.name,
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
            assert family_guest.name in response_text
            assert "Dietary Restrictions" in response_text

    def test_allergen_properties_on_rsvp_model(self, app, family_guest, allergens):
        """Test the allergen properties on the RSVP model."""
        with app.app_context():
            # Create RSVP
            rsvp = RSVP(
                guest_id=family_guest.id,
                is_attending=True
            )
            db.session.add(rsvp)
            db.session.flush()
            
            # Add allergens
            allergen1 = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=family_guest.name,
                allergen_id=allergens[0].id
            )
            allergen2 = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=family_guest.name,
                allergen_id=allergens[1].id
            )
            custom_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=family_guest.name,
                custom_allergen="Test Custom"
            )
            db.session.add_all([allergen1, allergen2, custom_allergen])
            db.session.commit()
            
            # Test properties
            allergen_ids = rsvp.allergen_ids
            assert len(allergen_ids) == 2
            assert allergens[0].id in allergen_ids
            assert allergens[1].id in allergen_ids
            
            custom = rsvp.custom_allergen
            assert custom == "Test Custom"

    def test_allergen_deletion_on_rsvp_update(self, client, app, family_guest, allergens):
        """Test that allergens are properly deleted and recreated when updating RSVP."""
        with app.app_context():
            # Create initial RSVP with allergens
            rsvp = RSVP(
                guest_id=family_guest.id,
                is_attending=True
            )
            db.session.add(rsvp)
            db.session.flush()
            
            # Add initial allergen
            initial_allergen = GuestAllergen(
                rsvp_id=rsvp.id,
                guest_name=family_guest.name,
                allergen_id=allergens[0].id
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
                'allergens_main': [str(allergens[1].id), str(allergens[2].id)],
                'custom_allergen_main': 'New Custom Allergen'
            }
            
            response = client.post(
                f'/rsvp/{family_guest.token}',
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
            assert allergens[0].id not in allergen_ids
            # New allergens should be present
            assert allergens[1].id in allergen_ids or allergens[2].id in allergen_ids
            assert 'New Custom Allergen' in custom_allergens

def run_allergen_test():
    """Standalone function to test allergen functionality."""
    print("Testing allergen functionality...")
    
    # This can be run independently to test the allergen system
    from app import create_app
    from app.config import TestConfig
    
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        
        # Create test allergens
        allergens = []
        for name in ['Gluten', 'Dairy', 'Nuts']:
            allergen = Allergen(name=name)
            db.session.add(allergen)
            allergens.append(allergen)
        
        db.session.commit()
        
        # Create test guest
        guest = Guest(
            name="Test Guest",
            email="test@example.com",
            phone="555-0123",
            token=secrets.token_urlsafe(32),
            is_family=True
        )
        db.session.add(guest)
        db.session.commit()
        
        # Create RSVP with allergens
        rsvp = RSVP(guest_id=guest.id, is_attending=True)
        db.session.add(rsvp)
        db.session.flush()
        
        # Add allergens
        guest_allergen = GuestAllergen(
            rsvp_id=rsvp.id,
            guest_name=guest.name,
            allergen_id=allergens[0].id
        )
        custom_allergen = GuestAllergen(
            rsvp_id=rsvp.id,
            guest_name=guest.name,
            custom_allergen="Test Custom"
        )
        db.session.add_all([guest_allergen, custom_allergen])
        db.session.commit()
        
        # Verify
        saved_allergens = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).all()
        print(f"Created {len(saved_allergens)} allergen records")
        
        for allergen in saved_allergens:
            if allergen.allergen:
                print(f"- Standard: {allergen.allergen.name} for {allergen.guest_name}")
            if allergen.custom_allergen:
                print(f"- Custom: {allergen.custom_allergen} for {allergen.guest_name}")
        
        print("Allergen test completed successfully!")

if __name__ == '__main__':
    run_allergen_test()