# tests/test_functional.py

import pytest
from flask import url_for
import os

# Set environment variable to control functional test execution
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
        
    def test_all_navigation_pages(self, client):
        """Test all navigation pages."""
        # Test venue page
        response = client.get('/venue')
        assert response.status_code == 200
        assert b'Wedding Venue' in response.data
        
        # Test accommodation page
        response = client.get('/accommodation')
        assert response.status_code == 200
        
        # Test activities page
        response = client.get('/activities')
        assert response.status_code == 200
        
        # Test gallery page
        response = client.get('/gallery')
        assert response.status_code == 200
        assert b'Our Gallery' in response.data

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
        assert b'We\'re Sorry You Can\'t Make It' in response.data
        
    def test_rsvp_cancel_flow(self, client, rsvp_guest, app):
        """Test cancelling an RSVP."""
        with app.app_context():
            # First create an RSVP
            from app.models.rsvp import RSVP
            
            # Delete any existing RSVP
            RSVP.query.filter_by(guest_id=rsvp_guest.id).delete()
            db.session.commit()
            
            # Create a new RSVP
            rsvp = RSVP(
                guest_id=rsvp_guest.id,
                is_attending=True,
                hotel_name="Test Hotel"
            )
            db.session.add(rsvp)
            db.session.commit()
            
            # Set the wedding date far in the future
            app.config['WEDDING_DATE'] = '2026-06-06'
                
            # Now cancel it
            response = client.get(f'/rsvp/{rsvp_guest.token}/cancel')
            assert response.status_code == 200
            assert b'Cancel RSVP' in response.data
            
            # Confirm cancellation
            response = client.post(
                f'/rsvp/{rsvp_guest.token}/cancel',
                data={'csrf_token': 'test-token'},
                follow_redirects=True
            )
            
            # Check if we were redirected to the cancellation confirmation page
            assert b'cancelled' in response.data.lower() or b'sorry' in response.data.lower()
            
            # Verify the RSVP was actually cancelled in the database
            db.session.expire_all()
            rsvp = RSVP.query.filter_by(guest_id=rsvp_guest.id).first()
            assert rsvp.is_cancelled is True

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
        assert b'Guest Management' in response.data

    def test_admin_add_guest(self, client, app):
        """Test adding a guest through the admin interface."""
        # Set authentication cookie
        client.set_cookie('admin_authenticated', 'true')
        
        # Test accessing the add guest page
        response = client.get('/admin/guest/add')
        assert response.status_code == 200
        assert b'Add Guest' in response.data
        
        # Test submitting the form
        data = {
            'name': 'New Test Guest',
            'phone': '555-555-5555',
            'email': 'new_test@example.com',
            'has_plus_one': 'y',
            'is_family': 'y',
            'language_preference': 'en'
        }
        response = client.post(
            '/admin/guest/add',
            data=data,
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Guest added successfully' in response.data or b'New Test Guest' in response.data
        
    def test_admin_download_template(self, client, app):
        """Test downloading the guest template."""
        # Set authentication cookie
        client.set_cookie('admin_authenticated', 'true')
        
        response = client.get('/admin/download-template')
        assert response.status_code == 200
        assert b'name,phone,email,has_plus_one,is_family,language' in response.data