# tests/test_functional.py

import pytest
from flask import url_for
import os

# Remove the skipif marker so tests always run
# pytestmark = pytest.mark.skipif(
#     not os.environ.get('RUN_FUNCTIONAL_TESTS'),
#     reason="Functional tests are disabled. Set RUN_FUNCTIONAL_TESTS=1 to enable."
# )

class TestMainNavigation:
    """Test main website navigation."""
    
    def test_home_page(self, client):
        """Test that the home page loads and has expected content."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Irene & Jaime' in response.data
        
        # Test language switching
        response = client.get('/?lang=en')
        assert response.status_code == 200
        assert b'lang-btn active">EN' in response.data
        
        # Test navigation to schedule page
        response = client.get('/schedule')
        assert response.status_code == 200
        assert b'Wedding Schedule' in response.data

class TestRSVPProcess:
    """Test the RSVP process flow."""
    
    @pytest.fixture
    def rsvp_guest(self, app):
        """Create a test guest for RSVP testing."""
        from app import db
        from app.models.guest import Guest
        import secrets
        
        with app.app_context():
            guest = Guest(
                name='Functional Test Guest',
                email='functional_test@example.com',
                phone='555-123-4567',
                token=secrets.token_urlsafe(32),
                language_preference='en',
                has_plus_one=True,
                is_family=True
            )
            db.session.add(guest)
            db.session.commit()
            yield guest
            # Clean up
            db.session.delete(guest)
            db.session.commit()
    
    def test_rsvp_attending_flow(self, client, rsvp_guest):
        """Test the RSVP flow for an attending guest."""
        # Get the RSVP form
        response = client.get(f'/rsvp/{rsvp_guest.token}')
        assert response.status_code == 200
        assert rsvp_guest.name.encode() in response.data
        
        # Submit the RSVP form with attendance data
        data = {
            'is_attending': 'yes',
            'hotel_name': 'Test Hotel',
            'transport_to_church': 'on',
            'adults_count': '1',
            'adult_name_0': 'Additional Adult'
        }
        response = client.post(
            f'/rsvp/{rsvp_guest.token}', 
            data=data,
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Thank You' in response.data
    
    def test_rsvp_not_attending_flow(self, client, rsvp_guest):
        """Test the RSVP flow for a non-attending guest."""
        # Submit the RSVP form with non-attendance data
        data = {
            'is_attending': 'no'
        }
        response = client.post(
            f'/rsvp/{rsvp_guest.token}', 
            data=data,
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Thank You' in response.data

class TestAdminInterface:
    """Test the admin interface."""
    
    def test_admin_login_and_dashboard(self, client, app):
        """Test logging into admin and viewing the dashboard."""
        # Test the login page
        response = client.get('/admin/login')
        assert response.status_code == 200
        assert b'Admin Login' in response.data
        
        # Mock login
        with app.test_request_context():
            client.set_cookie('localhost', 'admin_authenticated', 'true')
            
            # Test dashboard access
            response = client.get('/admin/dashboard')
            assert response.status_code == 200
            assert b'Guest Management' in response.data
    
    def test_admin_add_guest(self, client, app):
        """Test adding a guest through the admin interface."""
        # Set authentication cookie
        with app.test_request_context():
            client.set_cookie('localhost', 'admin_authenticated', 'true')
            
            # Test the add guest page
            response = client.get('/admin/guest/add')
            assert response.status_code == 200
            assert b'Add Guest' in response.data
            
            # Test adding a guest
            data = {
                'name': 'Test Guest Added',
                'phone': '123-456-7890',
                'email': 'test@example.com',
                'language_preference': 'en'
            }
            response = client.post(
                '/admin/guest/add',
                data=data,
                follow_redirects=True
            )
            assert response.status_code == 200
            assert b'Guest added successfully' in response.data or b'Test Guest Added' in response.data