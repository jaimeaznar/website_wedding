# tests/test_routes.py

from flask import url_for
import pytest
from urllib.parse import urlparse

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

    def test_rsvp_form_with_valid_token(self, client, sample_guest, sample_rsvp):
        """Test the RSVP form with a valid token."""
        response = client.get(f'/rsvp/{sample_guest.token}')
        assert response.status_code == 200
        assert sample_guest.name.encode() in response.data
        assert b'Will you attend?' in response.data
        
        # Since sample_rsvp is associated with sample_guest, we should see some of its data
        assert b'Test Hotel' in response.data  # This is the hotel name from sample_rsvp

    def test_rsvp_form_with_invalid_token(self, client):
        """Test the RSVP form with an invalid token."""
        response = client.get('/rsvp/invalid-token')
        assert response.status_code == 404

    def test_rsvp_submission(self, client, sample_guest):
        """Test submitting an RSVP."""
        # Submit an RSVP for not attending
        response = client.post(
            f'/rsvp/{sample_guest.token}',
            data={
                'is_attending': 'no'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Thank You!' in response.data
        
        # Submit an RSVP for attending
        response = client.post(
            f'/rsvp/{sample_guest.token}',
            data={
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel',
                'transport_to_church': 'on',
                'adults_count': '0',
                'children_count': '0'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Thank You!' in response.data

    def test_rsvp_cancel(self, client, sample_guest, sample_rsvp, monkeypatch):
        """Test cancelling an RSVP."""
        # Mock current_app.config
        monkeypatch.setattr('app.routes.rsvp.current_app.config', {
            'ADMIN_PHONE': '123456789',
            'ADMIN_EMAIL': 'admin@example.com',
            'MAIL_DEFAULT_SENDER': 'test@example.com',
            'WARNING_CUTOFF_DAYS': 7
        })
        
        # Mock send_cancellation_notification to avoid sending emails during tests
        monkeypatch.setattr('app.routes.rsvp.send_cancellation_notification', lambda g, r: True)
        
        response = client.post(
            f'/rsvp/{sample_guest.token}/cancel',
            follow_redirects=True
        )
        assert response.status_code == 200
        # Should see the RSVP form again after cancellation
        assert sample_guest.name.encode() in response.data

class TestAdminRoutes:
    def test_admin_login_page(self, client):
        """Test the admin login page."""
        response = client.get('/admin/login')
        assert response.status_code == 200
        assert b'Admin Login' in response.data

    def test_admin_login_success(self, client, monkeypatch):
        """Test successful admin login."""
        # Mock check_password_hash to always return True
        monkeypatch.setattr('app.routes.admin.check_password_hash', lambda h, p: True)
        
        response = client.post(
            '/admin/login',
            data={'password': 'correct-password'},
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Guest Management' in response.data

    def test_admin_login_failure(self, client, monkeypatch):
        """Test failed admin login."""
        # Mock check_password_hash to always return False
        monkeypatch.setattr('app.routes.admin.check_password_hash', lambda h, p: False)
        
        response = client.post(
            '/admin/login',
            data={'password': 'wrong-password'},
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Invalid password' in response.data

    def test_admin_dashboard(self, admin_authenticated_client, sample_guest, sample_rsvp):
        """Test the admin dashboard."""
        response = admin_authenticated_client.get('/admin/dashboard')
        assert response.status_code == 200
        assert b'Guest Management' in response.data
        assert b'RSVP Responses' in response.data
        assert sample_guest.name.encode() in response.data
        
        # Check for RSVP-specific information in the dashboard
        assert b'Test Hotel' in response.data  # Hotel name from sample_rsvp
        assert b'Attending' in response.data  # Should show attendance status

    def test_admin_add_guest(self, admin_authenticated_client):
        """Test adding a guest via the admin interface."""
        response = admin_authenticated_client.get('/admin/guest/add')
        assert response.status_code == 200
        assert b'Add Guest' in response.data
        
        # Test form submission
        response = admin_authenticated_client.post(
            '/admin/guest/add',
            data={
                'name': 'New Guest',
                'phone': '987654321',
                'email': 'new@example.com',
                'has_plus_one': 'on',
                'language': 'en'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'New Guest' in response.data

    def test_admin_download_template(self, admin_authenticated_client):
        """Test downloading the guest import template."""
        response = admin_authenticated_client.get('/admin/download-template')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        assert b'name,phone,email,has_plus_one,is_family,language' in response.data

    def test_admin_logout(self, admin_authenticated_client):
        """Test admin logout."""
        response = admin_authenticated_client.get('/admin/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Admin Login' in response.data
        
        # Cookie should be deleted
        cookies = admin_authenticated_client.cookie_jar._cookies['localhost.local']['/']
        assert 'admin_authenticated' not in cookies