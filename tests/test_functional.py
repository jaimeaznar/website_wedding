import pytest
from flask import url_for
import os

class TestMainNavigation:
    """Test main website navigation."""
    
    def test_home_page(self, client):
        """Test that the home page loads and has expected content."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Irene & Jaime' in response.data
        
        # Test that language switcher exists (but not testing JavaScript behavior)
        response = client.get('/')
        assert response.status_code == 200
        # Check that the language switcher HTML structure exists
        assert b'language-switcher' in response.data
        assert b'lang-btn' in response.data
        assert b'>EN</a>' in response.data
        assert b'>ES</a>' in response.data
        

class TestRSVPProcess:
    """Test the RSVP process flow."""
    
    @pytest.fixture
    def rsvp_guest(self, app):
        """Create a test guest for RSVP testing."""
        from app import db
        from app.models.guest import Guest
        from app.models.rsvp import RSVP, AdditionalGuest
        from app.models.allergen import GuestAllergen
        import secrets

        with app.app_context():
            guest = Guest(
                name='Functional Test Guest',
                phone='555-123-4567',
                token=secrets.token_urlsafe(32),
                language_preference='en',
            )
            db.session.add(guest)
            db.session.commit()
            yield guest
            
            # Clean up - first delete any associated RSVPs
            rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
            if rsvp:
                # Delete any additional guests
                AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).delete()
                # Delete any allergens
                GuestAllergen.query.filter_by(rsvp_id=rsvp.id).delete()
                # Then delete RSVP
                db.session.delete(rsvp)
                db.session.commit()
            
            # Now safe to delete the guest
            db.session.delete(guest)
            db.session.commit()
        
    def test_rsvp_attending_flow(self, client, rsvp_guest):
        """Test the RSVP flow for an attending guest."""
        # Set token in session by visiting homepage with token
        client.get(f'/?token={rsvp_guest.token}')
        
        # Get the RSVP form
        response = client.get('/rsvp')
        assert response.status_code == 200
        assert rsvp_guest.name.encode() in response.data
        
        # Submit the RSVP form with attendance data
        data = {
            'is_attending': 'yes',
            'hotel_name': 'Test Hotel',
            'adults_count': '1',
            'adult_name_0': 'Additional Adult'
        }
        response = client.post(
            '/rsvp/edit', 
            data=data,
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Thank You' in response.data or b'Thank' in response.data
    
    def test_rsvp_not_attending_flow(self, client, rsvp_guest):
        """Test the RSVP flow for a non-attending guest."""
        # Set token in session by visiting homepage with token
        client.get(f'/?token={rsvp_guest.token}')
        
        # Submit the RSVP form with non-attendance data
        data = {
            'is_attending': 'no'
        }
        response = client.post(
            '/rsvp/edit', 
            data=data,
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Thank' in response.data or b'Miss You' in response.data

    def test_rsvp_with_children_menu_flow(self, client, rsvp_guest):
        """Test the RSVP flow with children who need menu."""
        from app.models.rsvp import RSVP, AdditionalGuest
        from app import db
        
        # Set token in session by visiting homepage with token
        client.get(f'/?token={rsvp_guest.token}')
        
        # Submit the RSVP form with children - one with menu, one without
        data = {
            'is_attending': 'yes',
            'hotel_name': 'Family Hotel',
            'adults_count': '0',
            'children_count': '2',
            'child_name_0': 'Child With Menu',
            'child_needs_menu_0': 'on',  # Checkbox checked
            'child_name_1': 'Child Without Menu',
            # child_needs_menu_1 NOT present = unchecked
        }
        response = client.post(
            '/rsvp/edit',
            data=data,
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Verify children were saved correctly in database
        rsvp = RSVP.query.filter_by(guest_id=rsvp_guest.id).first()
        assert rsvp is not None
        assert rsvp.children_count == 2
        
        children = AdditionalGuest.query.filter_by(
            rsvp_id=rsvp.id,
            is_child=True
        ).all()
        
        assert len(children) == 2
        
        child_with_menu = next((c for c in children if c.name == 'Child With Menu'), None)
        child_without_menu = next((c for c in children if c.name == 'Child Without Menu'), None)
        
        assert child_with_menu is not None
        assert child_with_menu.needs_menu is True
        
        assert child_without_menu is not None
        assert child_without_menu.needs_menu is False

    def test_rsvp_edit_children_menu_update(self, client, rsvp_guest):
        """Test editing an RSVP updates children menu preferences correctly."""
        from app.models.rsvp import RSVP, AdditionalGuest
        from app import db
        
        # Set token in session
        client.get(f'/?token={rsvp_guest.token}')
        
        # First submission: child WITHOUT menu
        data_1 = {
            'is_attending': 'yes',
            'hotel_name': 'Update Test Hotel',
            'adults_count': '0',
            'children_count': '1',
            'child_name_0': 'Toggle Menu Child',
            # No checkbox = no menu
        }
        response = client.post('/rsvp/edit', data=data_1, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify initial state
        rsvp = RSVP.query.filter_by(guest_id=rsvp_guest.id).first()
        child = AdditionalGuest.query.filter_by(rsvp_id=rsvp.id, is_child=True).first()
        assert child.needs_menu is False
        
        # Second submission: same child WITH menu (editing RSVP)
        data_2 = {
            'is_attending': 'yes',
            'hotel_name': 'Update Test Hotel',
            'adults_count': '0',
            'children_count': '1',
            'child_name_0': 'Toggle Menu Child',
            'child_needs_menu_0': 'on',  # Now checked
        }
        response = client.post('/rsvp/edit', data=data_2, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify updated state
        child = AdditionalGuest.query.filter_by(rsvp_id=rsvp.id, is_child=True).first()
        assert child is not None
        assert child.needs_menu is True

    def test_rsvp_summary_shows_children_menu_status(self, client, rsvp_guest):
        """Test that RSVP summary page displays children menu status."""
        from app.models.rsvp import RSVP, AdditionalGuest
        from app import db
        
        # Set token in session
        client.get(f'/?token={rsvp_guest.token}')
        
        # Submit RSVP with children
        data = {
            'is_attending': 'yes',
            'hotel_name': 'Summary Test Hotel',
            'adults_count': '0',
            'children_count': '2',
            'child_name_0': 'Menu Kid',
            'child_needs_menu_0': 'on',
            'child_name_1': 'No Menu Kid',
        }
        client.post('/rsvp/edit', data=data, follow_redirects=True)
        
        # Visit RSVP summary page
        response = client.get('/rsvp')
        assert response.status_code == 200
        
        # Check that children names appear
        assert b'Menu Kid' in response.data
        assert b'No Menu Kid' in response.data
        
        # Check that menu status badges/text appear
        # These are the translation keys we added
        assert b'with menu' in response.data or b'con men' in response.data
        assert b'no menu' in response.data or b'sin men' in response.data

    def test_rsvp_json_data_includes_needs_menu(self, client, rsvp_guest):
        """Test that the hidden JSON data for JavaScript includes needs_menu field."""
        from app.models.rsvp import RSVP, AdditionalGuest
        from app import db
        
        # Set token in session
        client.get(f'/?token={rsvp_guest.token}')
        
        # Submit RSVP with a child who needs menu
        data = {
            'is_attending': 'yes',
            'hotel_name': 'JSON Test Hotel',
            'adults_count': '0',
            'children_count': '1',
            'child_name_0': 'JSON Test Child',
            'child_needs_menu_0': 'on',
        }
        client.post('/rsvp/edit', data=data, follow_redirects=True)
        
        # Visit the edit page to check the JSON data
        response = client.get('/rsvp/edit')
        assert response.status_code == 200
        
        # Check that the JSON data includes needs_menu field
        # The template outputs: {"name": "...", "is_child": true, "needs_menu": true}
        assert b'"needs_menu": true' in response.data or b'"needs_menu":true' in response.data

class TestAdminInterface:
    """Test the admin interface."""
    
    def test_admin_login_and_dashboard(self, client, app):
        """Test logging into admin and viewing the dashboard."""
        # Test the login page
        response = client.get('/admin/login')
        assert response.status_code == 200
        assert b'Admin Login' in response.data

        # Set cookie correctly for Flask 3.0+
        client.set_cookie('admin_authenticated', 'true')
        
        # Test accessing the dashboard
        response = client.get('/admin/dashboard')
        assert response.status_code == 200

    def test_admin_add_guest(self, client, app):
        """Test adding a guest through the admin interface."""
        # Set authentication cookie
        client.set_cookie('admin_authenticated', 'true')
        
        # Test accessing the add guest page
        response = client.get('/admin/guest/add')
        assert response.status_code == 200