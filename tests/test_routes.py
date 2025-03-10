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

    def test_rsvp_form_with_valid_token(self, client, sample_guest):
        response = client.get(f'/rsvp/{sample_guest.token}')
        assert response.status_code == 200
        assert b'RSVP Form' in response.data

    def test_rsvp_form_with_invalid_token(self, client):
        """Test the RSVP form with an invalid token."""
        response = client.get('/rsvp/invalid-token')
        assert response.status_code == 404

    def test_rsvp_submission(self, client, sample_guest):
        data = {
            'is_attending': 'yes',
            'adults_count': '2',
            'children_count': '0',
            'hotel_name': 'Test Hotel',
            'transport_to_church': 'on'
        }
        response = client.post(
            f'/rsvp/{sample_guest.token}',
            data=data,
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Thank you for your RSVP' in response.data

    def test_rsvp_cancel(self, client, sample_guest, sample_rsvp):
        response = client.post(
            f'/rsvp/{sample_guest.token}/cancel',
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Your RSVP has been cancelled' in response.data

class TestAdminRoutes:
    def test_admin_login_page(self, client):
        response = client.get('/admin/login')
        assert response.status_code == 200
        assert b'Admin Login' in response.data

    def test_admin_login_success(self, client, app):
        with app.app_context():
            response = client.post('/admin/login', 
                                 data={'password': app.config['ADMIN_PASSWORD_HASH']},
                                 follow_redirects=True)
            assert response.status_code == 200

    def test_admin_dashboard(self, auth_client):
        response = auth_client.get('/admin/dashboard')
        assert response.status_code == 200

    def test_admin_add_guest(self, auth_client):
        response = auth_client.get('/admin/guest/add')
        assert response.status_code == 200

    def test_admin_download_template(self, auth_client):
        response = auth_client.get('/admin/download-template')
        assert response.status_code == 200

    def test_admin_logout(self, auth_client):
        response = auth_client.get('/admin/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Admin Login' in response.data
