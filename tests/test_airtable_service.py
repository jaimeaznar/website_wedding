# tests/test_airtable_service.py
"""
Tests for the Airtable integration service.

Tests cover:
- AirtableGuest dataclass parsing
- Sync operations (create, update, delete)
- Statistics calculation
- Token generation
- RSVP status updates
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.services.airtable_service import (
    AirtableService,
    AirtableGuest,
    AirtableStatus,
    get_airtable_service,
)


class TestAirtableGuestDataclass:
    """Test AirtableGuest dataclass and parsing."""
    
    def test_from_airtable_record_full_data(self):
        """Test parsing a complete Airtable record."""
        record = {
            'id': 'rec123ABC',
            'fields': {
                'Name': 'John Doe',
                'Phone': '+34612345678',
                'Language': 'es',
                'Token': 'test-token-123',
                'Status': 'Attending',
                'RSVP Date': '2025-12-15',
                'Adults Count': 2,
                'Children Count': 1,
                'Hotel': 'Hotel Test',
                'Dietary Notes': 'Vegetarian',
                'Transport Church': True,
                'Transport Reception': True,
                'Transport Hotel': False,
                'Link Sent': '2025-12-01T10:00:00Z',
                'Reminder 1': '2025-12-05T10:00:00Z',
                'Personal Message': 'Welcome!',
                'Pre-boda Invited': True,
            }
        }
        
        guest = AirtableGuest.from_airtable_record(record)
        
        assert guest.record_id == 'rec123ABC'
        assert guest.name == 'John Doe'
        assert guest.phone == '+34612345678'
        assert guest.language == 'es'
        assert guest.token == 'test-token-123'
        assert guest.status == 'Attending'
        assert guest.adults_count == 2
        assert guest.children_count == 1
        assert guest.hotel == 'Hotel Test'
        assert guest.dietary_notes == 'Vegetarian'
        assert guest.transport_church is True
        assert guest.transport_reception is True
        assert guest.transport_hotel is False
        assert guest.link_sent is not None
        assert guest.reminder_1 is not None
        assert guest.personal_message == 'Welcome!'
        assert guest.preboda_invited is True
    
    def test_from_airtable_record_minimal_data(self):
        """Test parsing a minimal Airtable record with defaults."""
        record = {
            'id': 'rec456DEF',
            'fields': {
                'Name': 'Jane Smith',
            }
        }
        
        guest = AirtableGuest.from_airtable_record(record)
        
        assert guest.record_id == 'rec456DEF'
        assert guest.name == 'Jane Smith'
        assert guest.phone == ''
        assert guest.language == 'es'  # Default
        assert guest.token is None
        assert guest.status == AirtableStatus.PENDING  # Default
        assert guest.adults_count is None
        assert guest.children_count is None
        assert guest.hotel is None
        assert guest.transport_church is False  # Default
        assert guest.preboda_invited is False  # Default
    
    def test_from_airtable_record_invalid_date(self):
        """Test parsing with invalid date format."""
        record = {
            'id': 'rec789GHI',
            'fields': {
                'Name': 'Invalid Date Guest',
                'RSVP Date': 'not-a-date',
                'Link Sent': 'invalid',
            }
        }
        
        guest = AirtableGuest.from_airtable_record(record)
        
        assert guest.record_id == 'rec789GHI'
        assert guest.rsvp_date is None  # Should be None for invalid date
        assert guest.link_sent is None


class TestAirtableServiceConfiguration:
    """Test AirtableService configuration and initialization."""
    
    def test_is_configured_with_credentials(self):
        """Service should be configured when env vars are set."""
        with patch.dict('os.environ', {
            'AIRTABLE_API_KEY': 'test-api-key',
            'AIRTABLE_BASE_ID': 'appTestBase123',
        }):
            service = AirtableService()
            assert service.is_configured is True
    
    def test_is_not_configured_without_api_key(self):
        """Service should not be configured without API key."""
        with patch.dict('os.environ', {
            'AIRTABLE_BASE_ID': 'appTestBase123',
        }, clear=True):
            service = AirtableService()
            assert service.is_configured is False
    
    def test_is_not_configured_without_base_id(self):
        """Service should not be configured without base ID."""
        with patch.dict('os.environ', {
            'AIRTABLE_API_KEY': 'test-api-key',
        }, clear=True):
            service = AirtableService()
            assert service.is_configured is False


class TestSyncGuestToLocalDb:
    """Test syncing individual guests to local database."""
    
    def test_sync_creates_new_guest(self, app):
        """Sync should create a new guest when none exists."""
        with app.app_context():
            airtable_guest = AirtableGuest(
                record_id='recNew123',
                name='New Sync Guest',
                phone='+34611111111',
                language='es',
                token='new-sync-token-123',
                status=AirtableStatus.PENDING,
                rsvp_date=None,
                adults_count=None,
                children_count=None,
                hotel=None,
                dietary_notes=None,
                transport_church=False,
                transport_reception=False,
                transport_hotel=False,
                link_sent=None,
                reminder_1=None,
                reminder_2=None,
                reminder_3=None,
                reminder_4=None,
                personal_message=None,
                preboda_invited=False,
            )
            
            service = AirtableService()
            local_guest = service.sync_guest_to_local_db(airtable_guest)
            
            assert local_guest.id is not None
            assert local_guest.name == 'New Sync Guest'
            assert local_guest.phone == '+34611111111'
            assert local_guest.token == 'new-sync-token-123'
            
            # Verify no RSVP created for pending status
            rsvp = RSVP.query.filter_by(guest_id=local_guest.id).first()
            assert rsvp is None
            
            # Clean up
            db.session.delete(local_guest)
            db.session.commit()
    
    def test_sync_updates_existing_guest_by_token(self, app):
        """Sync should update existing guest matched by token."""
        with app.app_context():
            # Create existing guest
            existing_guest = Guest(
                name='Old Name',
                phone='+34600000000',
                token='existing-token-456',
                language_preference='en',
            )
            db.session.add(existing_guest)
            db.session.commit()
            existing_id = existing_guest.id
            
            # Sync with updated data
            airtable_guest = AirtableGuest(
                record_id='recExisting456',
                name='Updated Name',
                phone='+34699999999',
                language='es',
                token='existing-token-456',  # Same token
                status=AirtableStatus.PENDING,
                rsvp_date=None,
                adults_count=None,
                children_count=None,
                hotel=None,
                dietary_notes=None,
                transport_church=False,
                transport_reception=False,
                transport_hotel=False,
                link_sent=None,
                reminder_1=None,
                reminder_2=None,
                reminder_3=None,
                reminder_4=None,
                personal_message='Updated message',
                preboda_invited=True,
            )
            
            service = AirtableService()
            local_guest = service.sync_guest_to_local_db(airtable_guest)
            
            assert local_guest.id == existing_id  # Same guest
            assert local_guest.name == 'Updated Name'
            assert local_guest.phone == '+34699999999'
            assert local_guest.language_preference == 'es'
            assert local_guest.personal_message == 'Updated message'
            assert local_guest.preboda_invited is True
            
            # Clean up
            db.session.delete(local_guest)
            db.session.commit()
    
    def test_sync_creates_rsvp_for_attending_guest(self, app):
        """Sync should create RSVP when guest is attending."""
        with app.app_context():
            airtable_guest = AirtableGuest(
                record_id='recAttending789',
                name='Attending Guest',
                phone='+34622222222',
                language='en',
                token='attending-token-789',
                status=AirtableStatus.ATTENDING,
                rsvp_date=datetime(2025, 12, 15),
                adults_count=2,
                children_count=1,
                hotel='Grand Hotel',
                dietary_notes='Vegetarian',
                transport_church=False,
                transport_reception=True,
                transport_hotel=True,
                link_sent=None,
                reminder_1=None,
                reminder_2=None,
                reminder_3=None,
                reminder_4=None,
                personal_message=None,
                preboda_invited=False,
            )
            
            service = AirtableService()
            local_guest = service.sync_guest_to_local_db(airtable_guest)
            
            # Verify RSVP was created
            rsvp = RSVP.query.filter_by(guest_id=local_guest.id).first()
            assert rsvp is not None
            assert rsvp.is_attending is True
            assert rsvp.is_cancelled is False
            assert rsvp.hotel_name == 'Grand Hotel'
            assert rsvp.adults_count == 2
            assert rsvp.children_count == 1
            assert rsvp.transport_to_reception is True
            assert rsvp.transport_to_hotel is True
            
            # Clean up
            db.session.delete(rsvp)
            db.session.delete(local_guest)
            db.session.commit()
    
    def test_sync_creates_rsvp_for_declined_guest(self, app):
        """Sync should create RSVP with is_attending=False for declined guest."""
        with app.app_context():
            airtable_guest = AirtableGuest(
                record_id='recDeclined101',
                name='Declined Guest',
                phone='+34633333333',
                language='es',
                token='declined-token-101',
                status=AirtableStatus.DECLINED,
                rsvp_date=datetime(2025, 12, 10),
                adults_count=None,
                children_count=None,
                hotel=None,
                dietary_notes=None,
                transport_church=False,
                transport_reception=False,
                transport_hotel=False,
                link_sent=None,
                reminder_1=None,
                reminder_2=None,
                reminder_3=None,
                reminder_4=None,
                personal_message=None,
                preboda_invited=False,
            )
            
            service = AirtableService()
            local_guest = service.sync_guest_to_local_db(airtable_guest)
            
            # Verify RSVP was created with declined status
            rsvp = RSVP.query.filter_by(guest_id=local_guest.id).first()
            assert rsvp is not None
            assert rsvp.is_attending is False
            assert rsvp.is_cancelled is False
            
            # Clean up
            db.session.delete(rsvp)
            db.session.delete(local_guest)
            db.session.commit()


class TestSyncAllToLocalDb:
    """Test bulk sync operations including delete functionality."""
    
    def test_sync_creates_new_guests(self, app):
        """Sync should create guests that exist in Airtable but not locally."""
        with app.app_context():
            # Mock Airtable guests
            mock_airtable_guests = [
                AirtableGuest(
                    record_id='recBulk1',
                    name='Bulk Guest 1',
                    phone='+34644444441',
                    language='es',
                    token='bulk-token-1',
                    status=AirtableStatus.PENDING,
                    rsvp_date=None,
                    adults_count=None,
                    children_count=None,
                    hotel=None,
                    dietary_notes=None,
                    transport_church=False,
                    transport_reception=False,
                    transport_hotel=False,
                    link_sent=None,
                    reminder_1=None,
                    reminder_2=None,
                    reminder_3=None,
                    reminder_4=None,
                    personal_message=None,
                    preboda_invited=False,
                ),
                AirtableGuest(
                    record_id='recBulk2',
                    name='Bulk Guest 2',
                    phone='+34644444442',
                    language='en',
                    token='bulk-token-2',
                    status=AirtableStatus.PENDING,
                    rsvp_date=None,
                    adults_count=None,
                    children_count=None,
                    hotel=None,
                    dietary_notes=None,
                    transport_church=False,
                    transport_reception=False,
                    transport_hotel=False,
                    link_sent=None,
                    reminder_1=None,
                    reminder_2=None,
                    reminder_3=None,
                    reminder_4=None,
                    personal_message=None,
                    preboda_invited=False,
                ),
            ]
            
            service = AirtableService()
            
            with patch.object(service, 'get_all_guests', return_value=mock_airtable_guests):
                created, updated, deleted = service.sync_all_to_local_db()
            
            assert created == 2
            assert updated == 0
            assert deleted == 0
            
            # Verify guests were created
            guest1 = Guest.query.filter_by(token='bulk-token-1').first()
            guest2 = Guest.query.filter_by(token='bulk-token-2').first()
            assert guest1 is not None
            assert guest2 is not None
            assert guest1.name == 'Bulk Guest 1'
            assert guest2.name == 'Bulk Guest 2'
            
            # Clean up
            db.session.delete(guest1)
            db.session.delete(guest2)
            db.session.commit()
    
    def test_sync_updates_existing_guests(self, app):
        """Sync should update guests that exist in both places."""
        with app.app_context():
            # Create existing local guest
            existing_guest = Guest(
                name='Existing Guest Old Name',
                phone='+34655555555',
                token='existing-bulk-token',
                language_preference='en',
            )
            db.session.add(existing_guest)
            db.session.commit()
            
            # Mock Airtable with updated data
            mock_airtable_guests = [
                AirtableGuest(
                    record_id='recExistingBulk',
                    name='Existing Guest New Name',
                    phone='+34655555555',
                    language='es',
                    token='existing-bulk-token',
                    status=AirtableStatus.PENDING,
                    rsvp_date=None,
                    adults_count=None,
                    children_count=None,
                    hotel=None,
                    dietary_notes=None,
                    transport_church=False,
                    transport_reception=False,
                    transport_hotel=False,
                    link_sent=None,
                    reminder_1=None,
                    reminder_2=None,
                    reminder_3=None,
                    reminder_4=None,
                    personal_message=None,
                    preboda_invited=False,
                ),
            ]
            
            service = AirtableService()
            
            with patch.object(service, 'get_all_guests', return_value=mock_airtable_guests):
                created, updated, deleted = service.sync_all_to_local_db()
            
            assert created == 0
            assert updated == 1
            assert deleted == 0
            
            # Verify guest was updated
            updated_guest = Guest.query.filter_by(token='existing-bulk-token').first()
            assert updated_guest.name == 'Existing Guest New Name'
            assert updated_guest.language_preference == 'es'
            
            # Clean up
            db.session.delete(updated_guest)
            db.session.commit()
    
    def test_sync_deletes_removed_guests(self, app):
        """Sync should delete local guests that no longer exist in Airtable."""
        with app.app_context():
            # Create local guest that won't be in Airtable
            orphan_guest = Guest(
                name='Orphan Guest To Delete',
                phone='+34666666666',
                token='orphan-token-delete',
                language_preference='es',
            )
            db.session.add(orphan_guest)
            db.session.commit()
            orphan_id = orphan_guest.id
            
            # Mock empty Airtable (no guests)
            mock_airtable_guests = []
            
            service = AirtableService()
            
            with patch.object(service, 'get_all_guests', return_value=mock_airtable_guests):
                created, updated, deleted = service.sync_all_to_local_db()
            
            assert created == 0
            assert updated == 0
            assert deleted == 1
            
            # Verify guest was deleted
            deleted_guest = Guest.query.get(orphan_id)
            assert deleted_guest is None
    
    def test_sync_mixed_operations(self, app):
        """Sync should handle create, update, and delete in single operation."""
        with app.app_context():
            # Create existing guest to update
            update_guest = Guest(
                name='Guest To Update',
                phone='+34677777771',
                token='update-mixed-token',
                language_preference='en',
            )
            # Create guest to delete (not in Airtable)
            delete_guest = Guest(
                name='Guest To Delete',
                phone='+34677777772',
                token='delete-mixed-token',
                language_preference='es',
            )
            db.session.add_all([update_guest, delete_guest])
            db.session.commit()
            delete_id = delete_guest.id
            
            # Mock Airtable: one to update, one new (delete_guest not included)
            mock_airtable_guests = [
                AirtableGuest(
                    record_id='recUpdateMixed',
                    name='Guest To Update - Updated',
                    phone='+34677777771',
                    language='es',
                    token='update-mixed-token',
                    status=AirtableStatus.PENDING,
                    rsvp_date=None,
                    adults_count=None,
                    children_count=None,
                    hotel=None,
                    dietary_notes=None,
                    transport_church=False,
                    transport_reception=False,
                    transport_hotel=False,
                    link_sent=None,
                    reminder_1=None,
                    reminder_2=None,
                    reminder_3=None,
                    reminder_4=None,
                    personal_message=None,
                    preboda_invited=False,
                ),
                AirtableGuest(
                    record_id='recNewMixed',
                    name='New Guest Mixed',
                    phone='+34677777773',
                    language='en',
                    token='new-mixed-token',
                    status=AirtableStatus.PENDING,
                    rsvp_date=None,
                    adults_count=None,
                    children_count=None,
                    hotel=None,
                    dietary_notes=None,
                    transport_church=False,
                    transport_reception=False,
                    transport_hotel=False,
                    link_sent=None,
                    reminder_1=None,
                    reminder_2=None,
                    reminder_3=None,
                    reminder_4=None,
                    personal_message=None,
                    preboda_invited=False,
                ),
            ]
            
            service = AirtableService()
            
            with patch.object(service, 'get_all_guests', return_value=mock_airtable_guests):
                created, updated, deleted = service.sync_all_to_local_db()
            
            assert created == 1
            assert updated == 1
            assert deleted == 1
            
            # Verify operations
            updated_guest = Guest.query.filter_by(token='update-mixed-token').first()
            assert updated_guest.name == 'Guest To Update - Updated'
            
            new_guest = Guest.query.filter_by(token='new-mixed-token').first()
            assert new_guest is not None
            
            deleted_guest = Guest.query.get(delete_id)
            assert deleted_guest is None
            
            # Clean up
            db.session.delete(updated_guest)
            db.session.delete(new_guest)
            db.session.commit()
    
    def test_sync_matches_by_phone_when_no_token(self, app):
        """Sync should match existing guests by phone if token doesn't match."""
        with app.app_context():
            # Create guest with specific phone but different token
            existing_guest = Guest(
                name='Phone Match Guest',
                phone='+34688888888',
                token='local-only-token',
                language_preference='en',
            )
            db.session.add(existing_guest)
            db.session.commit()
            existing_id = existing_guest.id
            
            # Mock Airtable guest with same phone but new token
            mock_airtable_guests = [
                AirtableGuest(
                    record_id='recPhoneMatch',
                    name='Phone Match Guest Updated',
                    phone='+34688888888',  # Same phone
                    language='es',
                    token='airtable-new-token',  # Different token
                    status=AirtableStatus.PENDING,
                    rsvp_date=None,
                    adults_count=None,
                    children_count=None,
                    hotel=None,
                    dietary_notes=None,
                    transport_church=False,
                    transport_reception=False,
                    transport_hotel=False,
                    link_sent=None,
                    reminder_1=None,
                    reminder_2=None,
                    reminder_3=None,
                    reminder_4=None,
                    personal_message=None,
                    preboda_invited=False,
                ),
            ]
            
            service = AirtableService()
            
            with patch.object(service, 'get_all_guests', return_value=mock_airtable_guests):
                created, updated, deleted = service.sync_all_to_local_db()
            
            # Should update existing, not create new
            assert created == 0
            assert updated == 1
            assert deleted == 0
            
            # Verify same guest was updated
            updated_guest = Guest.query.get(existing_id)
            assert updated_guest is not None
            assert updated_guest.name == 'Phone Match Guest Updated'
            assert updated_guest.token == 'airtable-new-token'  # Token updated
            
            # Clean up
            db.session.delete(updated_guest)
            db.session.commit()


class TestAirtableServiceStatistics:
    """Test statistics calculation."""
    
    def test_get_statistics_empty(self):
        """Statistics should handle empty guest list."""
        service = AirtableService()
        
        with patch.object(service, 'get_all_guests', return_value=[]):
            stats = service.get_statistics()
        
        assert stats['total_guests'] == 0
        assert stats['pending'] == 0
        assert stats['attending'] == 0
        assert stats['declined'] == 0
        assert stats['cancelled'] == 0
        assert stats['total_people'] == 0
        assert stats['links_sent'] == 0
        assert stats['links_not_sent'] == 0
    
    def test_get_statistics_mixed_statuses(self):
        """Statistics should correctly count different statuses."""
        mock_guests = [
            AirtableGuest(
                record_id='rec1', name='Pending 1', phone='1', language='es',
                token='t1', status=AirtableStatus.PENDING, rsvp_date=None,
                adults_count=None, children_count=None, hotel=None,
                dietary_notes=None, transport_church=False, transport_reception=False,
                transport_hotel=False, link_sent=None, reminder_1=None,
                reminder_2=None, reminder_3=None, reminder_4=None,
                personal_message=None, preboda_invited=False,
            ),
            AirtableGuest(
                record_id='rec2', name='Attending 1', phone='2', language='es',
                token='t2', status=AirtableStatus.ATTENDING, rsvp_date=None,
                adults_count=2, children_count=1, hotel=None,
                dietary_notes=None, transport_church=False, transport_reception=False,
                transport_hotel=False, link_sent=datetime.now(), reminder_1=None,
                reminder_2=None, reminder_3=None, reminder_4=None,
                personal_message=None, preboda_invited=False,
            ),
            AirtableGuest(
                record_id='rec3', name='Attending 2', phone='3', language='es',
                token='t3', status=AirtableStatus.ATTENDING, rsvp_date=None,
                adults_count=1, children_count=0, hotel=None,
                dietary_notes=None, transport_church=False, transport_reception=False,
                transport_hotel=False, link_sent=datetime.now(), reminder_1=None,
                reminder_2=None, reminder_3=None, reminder_4=None,
                personal_message=None, preboda_invited=False,
            ),
            AirtableGuest(
                record_id='rec4', name='Declined 1', phone='4', language='es',
                token='t4', status=AirtableStatus.DECLINED, rsvp_date=None,
                adults_count=None, children_count=None, hotel=None,
                dietary_notes=None, transport_church=False, transport_reception=False,
                transport_hotel=False, link_sent=None, reminder_1=None,
                reminder_2=None, reminder_3=None, reminder_4=None,
                personal_message=None, preboda_invited=False,
            ),
            AirtableGuest(
                record_id='rec5', name='Cancelled 1', phone='5', language='es',
                token='t5', status=AirtableStatus.CANCELLED, rsvp_date=None,
                adults_count=None, children_count=None, hotel=None,
                dietary_notes=None, transport_church=False, transport_reception=False,
                transport_hotel=False, link_sent=None, reminder_1=None,
                reminder_2=None, reminder_3=None, reminder_4=None,
                personal_message=None, preboda_invited=False,
            ),
        ]
        
        service = AirtableService()
        
        with patch.object(service, 'get_all_guests', return_value=mock_guests):
            stats = service.get_statistics()
        
        assert stats['total_guests'] == 5
        assert stats['pending'] == 1
        assert stats['attending'] == 2
        assert stats['declined'] == 1
        assert stats['cancelled'] == 1
        assert stats['total_people'] == 4  # (2+1) + (1+0)
        assert stats['links_sent'] == 2
        assert stats['links_not_sent'] == 3  # Have token but no link_sent


class TestAirtableServiceSingleton:
    """Test singleton pattern for service access."""
    
    def test_get_airtable_service_returns_same_instance(self):
        """get_airtable_service should return the same instance."""
        # Reset singleton for testing
        import app.services.airtable_service as module
        module._airtable_service = None
        
        service1 = get_airtable_service()
        service2 = get_airtable_service()
        
        assert service1 is service2
        
        # Clean up
        module._airtable_service = None