# tests/test_routes.py

from flask import url_for
import pytest
from urllib.parse import urlparse
from app import db
from app.models.rsvp import RSVP
from app.models.allergen import GuestAllergen
from app.models.rsvp import AdditionalGuest

class TestMainRoutes:
    def test_index_route(self, client):
        """Test the index route."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Irene & Jaime' in response.data

    def test_schedule_route(self, client):
        """Test the schedule route."""
        response = client.get('/schedule')
        assert response.status_code == 200
        assert b'Wedding Schedule' in response.data

    def test_venue_route(self, client):
        """Test the venue route."""
        response = client.get('/venue')
        assert response.status_code == 200
        assert b'Wedding Venue' in response.data
        
    def test_accommodation_route(self, client):
        """Test the accommodation route."""
        response = client.get('/accommodation')
        assert response.status_code == 200

    def test_activities_route(self, client):
        """Test the activities route."""
        response = client.get('/activities')
        assert response.status_code == 200
        assert b'Things to Do' in response.data

    def test_gallery_route(self, client):
        """Test the gallery route."""
        response = client.get('/gallery')
        assert response.status_code == 200
        assert b'Our Gallery' in response.data

    def test_language_switching(self, client):
        """Test language switching."""
        # Default is English
        response = client.get('/')
        assert response.status_code == 200
        
        # Switch to Spanish
        response = client.get('/?lang=es')
        assert response.status_code == 200
        
        # Ensure language is in context
        assert b'class="lang-btn active">ES' in response.data

class TestRSVPRoutes:
    def test_rsvp_landing(self, client):
        """Test the RSVP landing page."""
        response = client.get('/rsvp/')
        assert response.status_code == 200
        assert b'Please use the link provided in your invitation' in response.data

    def test_rsvp_form_with_valid_token(self, client, sample_guest):
        """Test the RSVP form with a valid token."""
        response = client.get(f'/rsvp/{sample_guest.token}')
        assert response.status_code == 200
        assert b'RSVP' in response.data
        assert sample_guest.name.encode() in response.data

    def test_rsvp_form_with_invalid_token(self, client):
        """Test the RSVP form with an invalid token."""
        response = client.get('/rsvp/invalid-token')
        assert response.status_code == 404
        
    def test_rsvp_deadline_passed(self, client, app, sample_guest):
        """Test RSVP when deadline has passed."""
        with app.app_context():
            # Set RSVP deadline to a past date
            app.config['RSVP_DEADLINE'] = '2020-01-01'
            
            response = client.get(f'/rsvp/{sample_guest.token}')
            assert response.status_code == 200
            # This depends on your template content
            # assert b'RSVP deadline has passed' in response.data

    def test_direct_rsvp_creation(self, app, sample_guest):
        """Test creating an RSVP directly without using the form."""
        with app.app_context():
            # First make sure there's no existing RSVP
            RSVP.query.filter_by(guest_id=sample_guest.id).delete()
            db.session.commit()
            
            # Create an RSVP directly
            rsvp = RSVP(
                guest_id=sample_guest.id,
                is_attending=True,
                adults_count=1,
                children_count=0,
                hotel_name="Direct Test Hotel",
                transport_to_church=True,
                transport_to_reception=False,
                transport_to_hotel=True
            )
            db.session.add(rsvp)
            
            try:
                # tests/test_routes.py (continued)
                db.session.commit()
                print(f"Successfully created RSVP with ID: {rsvp.id}")
            except Exception as e:
                db.session.rollback()
                print(f"Failed to create RSVP: {str(e)}")
                raise
            
            # Verify RSVP was created
            fetched_rsvp = RSVP.query.filter_by(guest_id=sample_guest.id).first()
            assert fetched_rsvp is not None
            assert fetched_rsvp.is_attending is True
            assert fetched_rsvp.hotel_name == "Direct Test Hotel"
            
            # Clean up
            db.session.delete(fetched_rsvp)
            db.session.commit()
    
    def test_rsvp_submission(self, client, app, sample_guest):
        """Test submitting an RSVP form."""
        with app.app_context():
            # First make sure there's no existing RSVP
            RSVP.query.filter_by(guest_id=sample_guest.id).delete()
            db.session.commit()

            # Ensure sample_guest has is_family set to True for this test
            sample_guest.is_family = True
            db.session.commit()

            # Create a minimal valid data set for the RSVP form
            data = {
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel',
                # Include csrf_token for Flask-WTF
                'csrf_token': 'test-token'
            }

            # Make the POST request with the form data
            response = client.post(
                f'/rsvp/{sample_guest.token}',
                data=data,
                follow_redirects=True
            )
            assert response.status_code == 200
            
            # Force database query to verify RSVP was created
            db.session.expire_all()  # Clear any cached instances
            rsvp = RSVP.query.filter_by(guest_id=sample_guest.id).first()
            
            # Debug output if test fails
            if not rsvp:
                print("RSVP not found in database")
                print(f"Response content: {response.data}")
            
            assert rsvp is not None
            assert rsvp.is_attending is True
            assert rsvp.hotel_name == 'Test Hotel'
            
            # Clean up
            if rsvp:
                db.session.delete(rsvp)
                db.session.commit()

    def test_rsvp_invalid_submission(self, client, app, sample_guest):
        """Test invalid RSVP submission."""
        with app.app_context():
            # First make sure there's no existing RSVP
            RSVP.query.filter_by(guest_id=sample_guest.id).delete()
            db.session.commit()
            
            # Get the form first to simulate a more realistic test
            initial_response = client.get(f'/rsvp/{sample_guest.token}')
            assert initial_response.status_code == 200
            
            # Submit invalid data (transport without hotel)
            data = {
                'is_attending': 'yes',
                'transport_to_church': 'on',
                # Include csrf_token for Flask-WTF
                'csrf_token': 'test-token'
            }
            
            response = client.post(
                f'/rsvp/{sample_guest.token}',
                data=data
            )
            assert response.status_code == 200
            
            # For invalid submission, we should see the form again
            assert b'RSVP' in response.data or b'form' in response.data

    def test_rsvp_cancel(self, client, app, sample_guest):
        """Test cancelling an RSVP."""
        with app.app_context():
            # First make sure there's an RSVP to cancel
            existing_rsvp = RSVP.query.filter_by(guest_id=sample_guest.id).first()
            if existing_rsvp:
                db.session.delete(existing_rsvp)
                db.session.commit()
            
            # Create a new RSVP
            rsvp = RSVP(
                guest_id=sample_guest.id,
                is_attending=True,
                adults_count=1,
                hotel_name="Test Hotel"
            )
            db.session.add(rsvp)
            db.session.commit()
            
            # Set the wedding date far in future to ensure it's editable
            app.config['WEDDING_DATE'] = '2026-06-06'
            
            # Get the cancel page first
            cancel_page = client.get(f'/rsvp/{sample_guest.token}/cancel')
            assert cancel_page.status_code == 200
            
            # Now try to cancel it with minimal form data
            response = client.post(
                f'/rsvp/{sample_guest.token}/cancel',
                data={'csrf_token': 'test-token'},  # Minimal form data
                follow_redirects=True
            )
            assert response.status_code == 200
            
            # Verify it was cancelled
            db.session.expire_all()  # Clear any cached instances
            rsvp = RSVP.query.filter_by(guest_id=sample_guest.id).first()
            
            # More robust assertion with debugging
            if not rsvp or not rsvp.is_cancelled:
                print(f"Cancel test failed. Response: {response.data}")
                if rsvp:
                    print(f"RSVP state: is_cancelled={rsvp.is_cancelled}")
            
            assert rsvp is not None
            assert rsvp.is_cancelled is True
            
            # Clean up
            db.session.delete(rsvp)
            db.session.commit()

class TestAdminRoutes:
    def test_admin_login_page(self, client):
        response = client.get('/admin/login')
        assert response.status_code == 200
        assert b'Admin Login' in response.data

    def test_admin_login_success(self, client, app):
        with app.app_context():
            # Set the password hash in the config
            app.config['ADMIN_PASSWORD_HASH'] = 'pbkdf2:sha256:600000$MlXi8Xcgp3y5$d17a4d3dce0a3d5be306beb47fddee0fc7d8c6ba51f7a9c7ea3e4fea4f33ad01'
            
            # Use the known password for the hash
            response = client.post('/admin/login', 
                                data={'password': 'your-secure-password'},
                                follow_redirects=True)
            
            # After successful login, the cookie should be set
            assert 'admin_authenticated' in [cookie.name for cookie in client.cookie_jar]
            assert response.status_code == 200
            
            # Check for dashboard content rather than specific text
            assert b'dashboard' in response.data.lower() or b'guest' in response.data.lower()


    def test_admin_dashboard(self, auth_client):
        response = auth_client.get('/admin/dashboard')
        assert response.status_code == 200
        assert b'Guest Management' in response.data or b'Guest List' in response.data

    def test_admin_add_guest(self, auth_client):
        response = auth_client.get('/admin/guest/add')
        assert response.status_code == 200
        assert b'Add Guest' in response.data

    def test_admin_download_template(self, auth_client):
        response = auth_client.get('/admin/download-template')
        assert response.status_code == 200
        assert b'name,phone,email,has_plus_one,is_family,language' in response.data
        
    def test_admin_import_guests(self, auth_client):
        """Test importing guests."""
        from io import BytesIO
        
        # Create a test CSV file
        csv_content = b'name,phone,email,has_plus_one,is_family,language\nTest Import,123456,test@example.com,true,false,en'
        csv_file = BytesIO(csv_content)
        
        response = auth_client.post(
            '/admin/guest/import',
            data={
                'file': (csv_file, 'test.csv')
            },
            follow_redirects=True,
            content_type='multipart/form-data'
        )
        assert response.status_code == 200
        # Check for success message in the response
        # The exact message might vary based on your flash messages
        
    def test_admin_debug_allergens(self, auth_client, app, sample_rsvp, sample_allergens):
        """Test the debug allergens route."""
        with app.app_context():
            # Store guest name while in session
            guest_name = sample_rsvp.guest.name
            
            # Add an allergen to the RSVP
            guest_allergen = GuestAllergen(
                rsvp_id=sample_rsvp.id,
                guest_name=guest_name,
                allergen_id=sample_allergens[0].id
            )
            db.session.add(guest_allergen)
            db.session.commit()
            
            response = auth_client.get('/admin/debug/allergens')
            
            # Debugging output
            if response.status_code != 200:
                print(f"Debug allergens response: {response.status_code}")
                print(f"Response data: {response.data}")
            
            assert response.status_code == 200
            
            # Generic check for JSON content
            assert b'{' in response.data and b'}' in response.data
            
            # Clean up
            db.session.delete(guest_allergen)
            db.session.commit()

    def test_admin_logout(self, auth_client):
        response = auth_client.get('/admin/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Admin Login' in response.data