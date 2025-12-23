# tests/test_cron_reminders.py
"""
Tests for the cron reminder system.

Tests cover:
- Reminder date calculations
- Endpoint authentication
- Dry run mode
- Reminder sending logic
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
import json


class TestReminderDateCalculations:
    """Test reminder date calculation logic."""
    
    def test_get_reminder_for_today_reminder_1(self):
        """30 days before deadline should return reminder 1."""
        from app.routes.cron import get_reminder_for_today
        
        deadline = date(2026, 5, 6)
        today = date(2026, 4, 6)  # 30 days before
        
        result = get_reminder_for_today(deadline, today)
        assert result == 1
    
    def test_get_reminder_for_today_reminder_2(self):
        """14 days before deadline should return reminder 2."""
        from app.routes.cron import get_reminder_for_today
        
        deadline = date(2026, 5, 6)
        today = date(2026, 4, 22)  # 14 days before
        
        result = get_reminder_for_today(deadline, today)
        assert result == 2
    
    def test_get_reminder_for_today_reminder_3(self):
        """7 days before deadline should return reminder 3."""
        from app.routes.cron import get_reminder_for_today
        
        deadline = date(2026, 5, 6)
        today = date(2026, 4, 29)  # 7 days before
        
        result = get_reminder_for_today(deadline, today)
        assert result == 3
    
    def test_get_reminder_for_today_reminder_4(self):
        """3 days before deadline should return reminder 4 (final)."""
        from app.routes.cron import get_reminder_for_today
        
        deadline = date(2026, 5, 6)
        today = date(2026, 5, 3)  # 3 days before
        
        result = get_reminder_for_today(deadline, today)
        assert result == 4
    
    def test_get_reminder_for_today_no_reminder(self):
        """Non-reminder days should return None."""
        from app.routes.cron import get_reminder_for_today
        
        deadline = date(2026, 5, 6)
        
        # Test various non-reminder days
        non_reminder_days = [
            date(2026, 4, 5),   # 31 days before
            date(2026, 4, 7),   # 29 days before
            date(2026, 4, 20),  # 16 days before
            date(2026, 5, 1),   # 5 days before
            date(2026, 5, 6),   # deadline day
        ]
        
        for today in non_reminder_days:
            result = get_reminder_for_today(deadline, today)
            assert result is None, f"Expected None for {today}, got {result}"
    
    def test_get_reminder_for_today_past_deadline(self):
        """Days after deadline should return None."""
        from app.routes.cron import get_reminder_for_today
        
        deadline = date(2026, 5, 6)
        today = date(2026, 5, 10)  # 4 days after
        
        result = get_reminder_for_today(deadline, today)
        assert result is None
    
    def test_calculate_reminder_dates(self):
        """Test calculation of all reminder dates."""
        from app.routes.cron import calculate_reminder_dates
        
        deadline = date(2026, 5, 6)
        
        result = calculate_reminder_dates(deadline)
        
        assert result[1] == date(2026, 4, 6)   # 30 days before
        assert result[2] == date(2026, 4, 22)  # 14 days before
        assert result[3] == date(2026, 4, 29)  # 7 days before
        assert result[4] == date(2026, 5, 3)   # 3 days before


class TestCronEndpointAuth:
    """Test cron endpoint authentication."""
    
    @pytest.fixture
    def app(self):
        """Create test app."""
        from app import create_app
        
        app = create_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_missing_key_returns_401(self, client):
        """Request without key should return 401."""
        with patch.dict('os.environ', {'CRON_SECRET_KEY': 'test-secret'}):
            response = client.get('/api/cron/send-reminders')
            assert response.status_code == 401
    
    def test_wrong_key_returns_401(self, client):
        """Request with wrong key should return 401."""
        with patch.dict('os.environ', {'CRON_SECRET_KEY': 'test-secret'}):
            response = client.get('/api/cron/send-reminders?key=wrong-key')
            assert response.status_code == 401
    
    def test_correct_key_allowed(self, client):
        """Request with correct key should be allowed."""
        with patch.dict('os.environ', {'CRON_SECRET_KEY': 'test-secret'}):
            # Mock the services to avoid actual API calls
            with patch('app.services.airtable_service.get_airtable_service') as mock_airtable:
                mock_service = Mock()
                mock_service.is_configured = True
                mock_service.get_guests_needing_reminder.return_value = []
                mock_airtable.return_value = mock_service
                
                with patch('app.services.whatsapp_service.get_whatsapp_service') as mock_whatsapp:
                    mock_wa = Mock()
                    mock_wa.is_configured = True
                    mock_whatsapp.return_value = mock_wa
                    
                    response = client.get('/api/cron/send-reminders?key=test-secret&force_reminder=1')
                    assert response.status_code == 200
    
    def test_missing_env_secret_returns_500(self, client):
        """Missing CRON_SECRET_KEY env var should return 500."""
        with patch.dict('os.environ', {}, clear=True):
            # Remove CRON_SECRET_KEY if it exists
            import os
            if 'CRON_SECRET_KEY' in os.environ:
                del os.environ['CRON_SECRET_KEY']
            
            response = client.get('/api/cron/send-reminders?key=any-key')
            # Should return 500 because server is misconfigured
            assert response.status_code == 500


class TestCronSendReminders:
    """Test the send-reminders endpoint logic."""
    
    @pytest.fixture
    def app(self):
        """Create test app."""
        from app import create_app
        
        app = create_app()
        app.config['TESTING'] = True
        app.config['RSVP_DEADLINE'] = '2026-05-06'
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_no_reminder_day_returns_no_action(self, client):
        """Non-reminder day should return no_action status."""
        with patch.dict('os.environ', {'CRON_SECRET_KEY': 'test-secret'}):
            # Patch date.today() to return a non-reminder day
            with patch('app.routes.cron.date') as mock_date:
                mock_date.today.return_value = date(2026, 4, 10)  # Not a reminder day
                mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
                
                response = client.get('/api/cron/send-reminders?key=test-secret')
                data = json.loads(response.data)
                
                assert response.status_code == 200
                assert data['status'] == 'no_action'
    
    def test_force_reminder_works(self, client):
        """force_reminder parameter should override date logic."""
        with patch.dict('os.environ', {'CRON_SECRET_KEY': 'test-secret'}):
            with patch('app.services.airtable_service.get_airtable_service') as mock_airtable:
                mock_service = Mock()
                mock_service.is_configured = True
                mock_service.get_guests_needing_reminder.return_value = []
                mock_airtable.return_value = mock_service
                
                with patch('app.services.whatsapp_service.get_whatsapp_service') as mock_whatsapp:
                    mock_wa = Mock()
                    mock_wa.is_configured = True
                    mock_whatsapp.return_value = mock_wa
                    
                    response = client.get('/api/cron/send-reminders?key=test-secret&force_reminder=2')
                    data = json.loads(response.data)
                    
                    assert response.status_code == 200
                    assert data['reminder_number'] == 2
    
    def test_dry_run_does_not_send(self, client):
        """dry_run=true should not actually send messages."""
        with patch.dict('os.environ', {'CRON_SECRET_KEY': 'test-secret'}):
            with patch('app.services.airtable_service.get_airtable_service') as mock_airtable:
                # Create mock guest
                mock_guest = Mock()
                mock_guest.name = 'Test Guest'
                mock_guest.phone = '+34612345678'
                mock_guest.token = 'test-token'
                mock_guest.language = 'es'
                mock_guest.record_id = 'rec123'
                
                mock_service = Mock()
                mock_service.is_configured = True
                mock_service.get_guests_needing_reminder.return_value = [mock_guest]
                mock_airtable.return_value = mock_service
                
                with patch('app.services.whatsapp_service.get_whatsapp_service') as mock_whatsapp:
                    mock_wa = Mock()
                    mock_wa.is_configured = True
                    mock_whatsapp.return_value = mock_wa
                    
                    response = client.get(
                        '/api/cron/send-reminders?key=test-secret&force_reminder=1&dry_run=true'
                    )
                    data = json.loads(response.data)
                    
                    assert response.status_code == 200
                    assert data['dry_run'] == True
                    assert data['sent'] == 1
                    assert data['details'][0]['status'] == 'dry_run'
                    
                    # Verify WhatsApp was NOT called
                    mock_wa.send_reminder_and_update_airtable.assert_not_called()
    
    def test_successful_send(self, client):
        """Successful reminder send should update counts."""
        with patch.dict('os.environ', {'CRON_SECRET_KEY': 'test-secret'}):
            with patch('app.services.airtable_service.get_airtable_service') as mock_airtable:
                # Create mock guest
                mock_guest = Mock()
                mock_guest.name = 'Test Guest'
                mock_guest.phone = '+34612345678'
                mock_guest.token = 'test-token'
                mock_guest.language = 'es'
                mock_guest.record_id = 'rec123'
                
                mock_service = Mock()
                mock_service.is_configured = True
                mock_service.get_guests_needing_reminder.return_value = [mock_guest]
                mock_airtable.return_value = mock_service
                
                with patch('app.services.whatsapp_service.get_whatsapp_service') as mock_whatsapp:
                    # Mock successful send
                    mock_result = Mock()
                    mock_result.success = True
                    mock_result.message_sid = 'SM123456'
                    
                    mock_wa = Mock()
                    mock_wa.is_configured = True
                    mock_wa.send_reminder_and_update_airtable.return_value = mock_result
                    mock_whatsapp.return_value = mock_wa
                    
                    response = client.get(
                        '/api/cron/send-reminders?key=test-secret&force_reminder=1'
                    )
                    data = json.loads(response.data)
                    
                    assert response.status_code == 200
                    assert data['sent'] == 1
                    assert data['failed'] == 0
                    assert data['details'][0]['status'] == 'sent'
                    assert data['details'][0]['message_sid'] == 'SM123456'
    
    def test_failed_send_counted(self, client):
        """Failed reminder send should be counted in failed."""
        with patch.dict('os.environ', {'CRON_SECRET_KEY': 'test-secret'}):
            with patch('app.services.airtable_service.get_airtable_service') as mock_airtable:
                mock_guest = Mock()
                mock_guest.name = 'Test Guest'
                mock_guest.phone = '+34612345678'
                mock_guest.token = 'test-token'
                mock_guest.language = 'es'
                mock_guest.record_id = 'rec123'
                
                mock_service = Mock()
                mock_service.is_configured = True
                mock_service.get_guests_needing_reminder.return_value = [mock_guest]
                mock_airtable.return_value = mock_service
                
                with patch('app.services.whatsapp_service.get_whatsapp_service') as mock_whatsapp:
                    # Mock failed send
                    mock_result = Mock()
                    mock_result.success = False
                    mock_result.error = 'Invalid phone number'
                    
                    mock_wa = Mock()
                    mock_wa.is_configured = True
                    mock_wa.send_reminder_and_update_airtable.return_value = mock_result
                    mock_whatsapp.return_value = mock_wa
                    
                    response = client.get(
                        '/api/cron/send-reminders?key=test-secret&force_reminder=1'
                    )
                    data = json.loads(response.data)
                    
                    assert response.status_code == 200
                    assert data['sent'] == 0
                    assert data['failed'] == 1
                    assert data['details'][0]['status'] == 'failed'
    
    def test_guest_without_token_skipped(self, client):
        """Guest without token should be skipped."""
        with patch.dict('os.environ', {'CRON_SECRET_KEY': 'test-secret'}):
            with patch('app.services.airtable_service.get_airtable_service') as mock_airtable:
                mock_guest = Mock()
                mock_guest.name = 'No Token Guest'
                mock_guest.phone = '+34612345678'
                mock_guest.token = None  # No token!
                mock_guest.language = 'es'
                mock_guest.record_id = 'rec123'
                
                mock_service = Mock()
                mock_service.is_configured = True
                mock_service.get_guests_needing_reminder.return_value = [mock_guest]
                mock_airtable.return_value = mock_service
                
                with patch('app.services.whatsapp_service.get_whatsapp_service') as mock_whatsapp:
                    mock_wa = Mock()
                    mock_wa.is_configured = True
                    mock_whatsapp.return_value = mock_wa
                    
                    response = client.get(
                        '/api/cron/send-reminders?key=test-secret&force_reminder=1'
                    )
                    data = json.loads(response.data)
                    
                    assert response.status_code == 200
                    assert data['sent'] == 0
                    assert data['failed'] == 1
                    assert data['details'][0]['reason'] == 'No token'


class TestCronStatus:
    """Test the status endpoint."""
    
    @pytest.fixture
    def app(self):
        """Create test app."""
        from app import create_app
        
        app = create_app()
        app.config['TESTING'] = True
        app.config['RSVP_DEADLINE'] = '2026-05-06'
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_status_returns_schedule(self, client):
        """Status endpoint should return reminder schedule."""
        with patch.dict('os.environ', {'CRON_SECRET_KEY': 'test-secret'}):
            with patch('app.services.airtable_service.get_airtable_service') as mock_airtable:
                mock_service = Mock()
                mock_service.is_configured = True
                mock_service.get_guests_pending_rsvp.return_value = []
                mock_airtable.return_value = mock_service
                
                response = client.get('/api/cron/status?key=test-secret')
                data = json.loads(response.data)
                
                assert response.status_code == 200
                assert data['status'] == 'ok'
                assert 'reminder_schedule' in data
                assert 'reminder_1' in data['reminder_schedule']
                assert 'reminder_2' in data['reminder_schedule']
                assert 'reminder_3' in data['reminder_schedule']
                assert 'reminder_4' in data['reminder_schedule']