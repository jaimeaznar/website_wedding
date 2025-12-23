# tests/test_reminder_timing.py
"""
Comprehensive tests for reminder timing functionality.

Tests cover:
- Reminder type to days mapping
- Date-based reminder scheduling logic
- Guest filtering for reminders
- Opt-out and max reminder limits
- Batch reminder execution
- Scheduled reminder runs
"""

import pytest
import secrets
from datetime import datetime, timedelta, date
from unittest.mock import patch, MagicMock
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.models.reminder import (
    ReminderType, ReminderStatus, ReminderHistory,
    ReminderBatch, GuestReminderPreference
)
from app.services.reminder_service import ReminderService
from app.constants import DateFormat, DEFAULT_CONFIG


class TestReminderTypeMapping:
    """Test ReminderType class and days mapping."""
    
    def test_initial_reminder_is_30_days_before(self):
        """Initial reminder should be 30 days before deadline."""
        days = ReminderType.get_days_before(ReminderType.INITIAL)
        assert days == 30
    
    def test_first_followup_is_14_days_before(self):
        """First follow-up should be 14 days before deadline."""
        days = ReminderType.get_days_before(ReminderType.FIRST_FOLLOWUP)
        assert days == 14
    
    def test_second_followup_is_7_days_before(self):
        """Second follow-up should be 7 days before deadline."""
        days = ReminderType.get_days_before(ReminderType.SECOND_FOLLOWUP)
        assert days == 7
    
    def test_final_reminder_is_3_days_before(self):
        """Final reminder should be 3 days before deadline."""
        days = ReminderType.get_days_before(ReminderType.FINAL)
        assert days == 3
    
    def test_invalid_reminder_type_returns_none(self):
        """Invalid reminder type should return None."""
        days = ReminderType.get_days_before('invalid_type')
        assert days is None
    
    def test_all_types_list_contains_all_reminders(self):
        """ALL_TYPES should contain all four reminder types."""
        assert len(ReminderType.ALL_TYPES) == 4
        assert ReminderType.INITIAL in ReminderType.ALL_TYPES
        assert ReminderType.FIRST_FOLLOWUP in ReminderType.ALL_TYPES
        assert ReminderType.SECOND_FOLLOWUP in ReminderType.ALL_TYPES
        assert ReminderType.FINAL in ReminderType.ALL_TYPES


class TestShouldSendReminderToday:
    """Test the should_send_reminder_today logic."""
    
    def test_initial_reminder_on_correct_date(self, app):
        """Initial reminder should send exactly 30 days before deadline."""
        with app.app_context():
            # Set deadline to 30 days from "today"
            deadline = date(2026, 5, 6)  # RSVP deadline
            reminder_date = deadline - timedelta(days=30)  # April 6, 2026
            
            app.config['RSVP_DEADLINE'] = deadline.strftime(DateFormat.DATABASE)
            
            with patch('app.services.reminder_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.combine(reminder_date, datetime.min.time())
                mock_datetime.strptime = datetime.strptime
                
                result = ReminderService.should_send_reminder_today(ReminderType.INITIAL)
                assert result is True
    
    def test_initial_reminder_on_wrong_date(self, app):
        """Initial reminder should NOT send on other dates."""
        with app.app_context():
            deadline = date(2026, 5, 6)
            wrong_date = deadline - timedelta(days=29)  # One day off
            
            app.config['RSVP_DEADLINE'] = deadline.strftime(DateFormat.DATABASE)
            
            with patch('app.services.reminder_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.combine(wrong_date, datetime.min.time())
                mock_datetime.strptime = datetime.strptime
                
                result = ReminderService.should_send_reminder_today(ReminderType.INITIAL)
                assert result is False
    
    def test_first_followup_on_correct_date(self, app):
        """First follow-up should send exactly 14 days before deadline."""
        with app.app_context():
            deadline = date(2026, 5, 6)
            reminder_date = deadline - timedelta(days=14)  # April 22, 2026
            
            app.config['RSVP_DEADLINE'] = deadline.strftime(DateFormat.DATABASE)
            
            with patch('app.services.reminder_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.combine(reminder_date, datetime.min.time())
                mock_datetime.strptime = datetime.strptime
                
                result = ReminderService.should_send_reminder_today(ReminderType.FIRST_FOLLOWUP)
                assert result is True
    
    def test_second_followup_on_correct_date(self, app):
        """Second follow-up should send exactly 7 days before deadline."""
        with app.app_context():
            deadline = date(2026, 5, 6)
            reminder_date = deadline - timedelta(days=7)  # April 29, 2026
            
            app.config['RSVP_DEADLINE'] = deadline.strftime(DateFormat.DATABASE)
            
            with patch('app.services.reminder_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.combine(reminder_date, datetime.min.time())
                mock_datetime.strptime = datetime.strptime
                
                result = ReminderService.should_send_reminder_today(ReminderType.SECOND_FOLLOWUP)
                assert result is True
    
    def test_final_reminder_on_correct_date(self, app):
        """Final reminder should send exactly 3 days before deadline."""
        with app.app_context():
            deadline = date(2026, 5, 6)
            reminder_date = deadline - timedelta(days=3)  # May 3, 2026
            
            app.config['RSVP_DEADLINE'] = deadline.strftime(DateFormat.DATABASE)
            
            with patch('app.services.reminder_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.combine(reminder_date, datetime.min.time())
                mock_datetime.strptime = datetime.strptime
                
                result = ReminderService.should_send_reminder_today(ReminderType.FINAL)
                assert result is True
    
    def test_no_deadline_configured_returns_false(self, app):
        """Should return False if no RSVP deadline is configured."""
        with app.app_context():
            app.config['RSVP_DEADLINE'] = None
            
            result = ReminderService.should_send_reminder_today(ReminderType.INITIAL)
            assert result is False
    
    def test_invalid_deadline_format_returns_false(self, app):
        """Should return False if deadline has invalid format."""
        with app.app_context():
            app.config['RSVP_DEADLINE'] = 'invalid-date'
            
            result = ReminderService.should_send_reminder_today(ReminderType.INITIAL)
            assert result is False
    
    def test_invalid_reminder_type_returns_false(self, app):
        """Should return False for invalid reminder type."""
        with app.app_context():
            deadline = date(2026, 5, 6)
            app.config['RSVP_DEADLINE'] = deadline.strftime(DateFormat.DATABASE)
            
            result = ReminderService.should_send_reminder_today('invalid_type')
            assert result is False


class TestGuestsNeedingReminder:
    """Test get_guests_needing_reminder filtering logic."""
    
    @pytest.fixture
    def guests_without_rsvp(self, app):
        """Create guests without RSVPs for testing."""
        with app.app_context():
            guests = []
            for i in range(3):
                guest = Guest(
                    name=f'Test No RSVP Guest {i}',
                    email=f'norsvp{i}@test.com',
                    phone=f'555-{i:04d}',
                    token=secrets.token_urlsafe(32)
                )
                db.session.add(guest)
                guests.append(guest)
            db.session.commit()
            
            yield guests
            
            # Cleanup
            for guest in guests:
                if Guest.query.get(guest.id):
                    db.session.delete(guest)
            db.session.commit()
    
    @pytest.fixture
    def guest_with_rsvp(self, app):
        """Create a guest with an active RSVP."""
        with app.app_context():
            guest = Guest(
                name='Test RSVP Guest',
                email='rsvp@test.com',
                phone='555-9999',
                token=secrets.token_urlsafe(32)
            )
            db.session.add(guest)
            db.session.flush()
            
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.commit()
            
            yield guest
            
            # Cleanup
            if Guest.query.get(guest.id):
                db.session.delete(guest)
                db.session.commit()
    
    @pytest.fixture
    def guest_with_cancelled_rsvp(self, app):
        """Create a guest with a cancelled RSVP."""
        with app.app_context():
            guest = Guest(
                name='Test Cancelled Guest',
                email='cancelled@test.com',
                phone='555-8888',
                token=secrets.token_urlsafe(32)
            )
            db.session.add(guest)
            db.session.flush()
            
            rsvp = RSVP(
                guest_id=guest.id,
                is_attending=True,
                is_cancelled=True,
                hotel_name='Test Hotel'
            )
            db.session.add(rsvp)
            db.session.commit()
            
            yield guest
            
            # Cleanup
            if Guest.query.get(guest.id):
                db.session.delete(guest)
                db.session.commit()
    
    def test_guests_without_rsvp_need_reminder(self, app, guests_without_rsvp):
        """Guests without RSVPs should be included in reminder list."""
        with app.app_context():
            guests = ReminderService.get_guests_needing_reminder(ReminderType.INITIAL)
            
            guest_ids = [g.id for g in guests]
            for test_guest in guests_without_rsvp:
                assert test_guest.id in guest_ids
    
    def test_guests_with_active_rsvp_excluded(self, app, guest_with_rsvp, guests_without_rsvp):
        """Guests with active RSVPs should NOT be included."""
        with app.app_context():
            guests = ReminderService.get_guests_needing_reminder(ReminderType.INITIAL)
            
            guest_ids = [g.id for g in guests]
            assert guest_with_rsvp.id not in guest_ids
    
    def test_guests_with_cancelled_rsvp_included(self, app, guest_with_cancelled_rsvp):
        """Guests with cancelled RSVPs should be included."""
        with app.app_context():
            guests = ReminderService.get_guests_needing_reminder(ReminderType.INITIAL)
            
            guest_ids = [g.id for g in guests]
            assert guest_with_cancelled_rsvp.id in guest_ids
    
    def test_guests_already_sent_reminder_excluded(self, app, guests_without_rsvp):
        """Guests who already received this reminder type should be excluded."""
        with app.app_context():
            # Mark first guest as already sent initial reminder
            target_guest = guests_without_rsvp[0]
            reminder = ReminderHistory(
                guest_id=target_guest.id,
                reminder_type=ReminderType.INITIAL,
                status=ReminderStatus.SENT,
                email_sent_to=target_guest.email
            )
            db.session.add(reminder)
            db.session.commit()
            
            # Get guests needing reminder
            guests = ReminderService.get_guests_needing_reminder(ReminderType.INITIAL)
            
            guest_ids = [g.id for g in guests]
            assert target_guest.id not in guest_ids
            
            # Other guests should still be included
            assert guests_without_rsvp[1].id in guest_ids
            assert guests_without_rsvp[2].id in guest_ids
            
            # Cleanup
            db.session.delete(reminder)
            db.session.commit()
    
    def test_opted_out_guests_excluded(self, app, guests_without_rsvp):
        """Guests who opted out should be excluded."""
        with app.app_context():
            # Opt out first guest
            target_guest = guests_without_rsvp[0]
            pref = GuestReminderPreference(
                guest_id=target_guest.id,
                opt_out=True
            )
            db.session.add(pref)
            db.session.commit()
            
            # Get guests needing reminder
            guests = ReminderService.get_guests_needing_reminder(ReminderType.INITIAL)
            
            guest_ids = [g.id for g in guests]
            assert target_guest.id not in guest_ids
            
            # Cleanup
            db.session.delete(pref)
            db.session.commit()


class TestGuestReminderPreference:
    """Test GuestReminderPreference model and limits."""
    
    def test_can_send_reminder_default_true(self, app, sample_guest):
        """By default, can_send_reminder should be True."""
        with app.app_context():
            pref = GuestReminderPreference(guest_id=sample_guest.id)
            db.session.add(pref)
            db.session.commit()
            
            assert pref.can_send_reminder is True
            
            # Cleanup
            db.session.delete(pref)
            db.session.commit()
    
    def test_can_send_reminder_false_when_opted_out(self, app, sample_guest):
        """can_send_reminder should be False when opted out."""
        with app.app_context():
            pref = GuestReminderPreference(
                guest_id=sample_guest.id,
                opt_out=True
            )
            db.session.add(pref)
            db.session.commit()
            
            assert pref.can_send_reminder is False
            
            # Cleanup
            db.session.delete(pref)
            db.session.commit()
    
    def test_can_send_reminder_false_when_max_reached(self, app, sample_guest):
        """can_send_reminder should be False when max reminders reached."""
        with app.app_context():
            pref = GuestReminderPreference(
                guest_id=sample_guest.id,
                max_reminders=4,
                total_sent=4  # Reached max
            )
            db.session.add(pref)
            db.session.commit()
            
            assert pref.can_send_reminder is False
            
            # Cleanup
            db.session.delete(pref)
            db.session.commit()
    
    def test_can_send_reminder_true_when_below_max(self, app, sample_guest):
        """can_send_reminder should be True when below max."""
        with app.app_context():
            pref = GuestReminderPreference(
                guest_id=sample_guest.id,
                max_reminders=4,
                total_sent=3  # One below max
            )
            db.session.add(pref)
            db.session.commit()
            
            assert pref.can_send_reminder is True
            
            # Cleanup
            db.session.delete(pref)
            db.session.commit()
    
    def test_increment_sent_count(self, app, sample_guest):
        """increment_sent_count should increase total_sent."""
        with app.app_context():
            pref = GuestReminderPreference(
                guest_id=sample_guest.id,
                total_sent=0
            )
            db.session.add(pref)
            db.session.commit()
            
            assert pref.total_sent == 0
            
            pref.increment_sent_count()
            
            assert pref.total_sent == 1
            assert pref.last_reminder_sent is not None
            
            # Cleanup
            db.session.delete(pref)
            db.session.commit()


class TestOptOutGuest:
    """Test opt_out_guest functionality."""
    
    def test_opt_out_creates_preference_if_not_exists(self, app, sample_guest):
        """opt_out_guest should create preference record if needed."""
        with app.app_context():
            # Ensure no preference exists
            existing = GuestReminderPreference.query.filter_by(
                guest_id=sample_guest.id
            ).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()
            
            # Opt out
            result = ReminderService.opt_out_guest(sample_guest.id)
            
            assert result is True
            
            # Check preference was created
            pref = GuestReminderPreference.query.filter_by(
                guest_id=sample_guest.id
            ).first()
            assert pref is not None
            assert pref.opt_out is True
            
            # Cleanup
            db.session.delete(pref)
            db.session.commit()
    
    def test_opt_out_updates_existing_preference(self, app, sample_guest):
        """opt_out_guest should update existing preference."""
        with app.app_context():
            # Create preference with opt_out=False
            pref = GuestReminderPreference(
                guest_id=sample_guest.id,
                opt_out=False
            )
            db.session.add(pref)
            db.session.commit()
            
            # Opt out
            result = ReminderService.opt_out_guest(sample_guest.id)
            
            assert result is True
            
            # Refresh and check
            db.session.refresh(pref)
            assert pref.opt_out is True
            
            # Cleanup
            db.session.delete(pref)
            db.session.commit()


class TestReminderScheduleCalculation:
    """Test calculation of reminder schedule dates."""
    
    def test_all_reminder_dates_before_deadline(self, app):
        """All reminder dates should be before the deadline."""
        with app.app_context():
            deadline = date(2026, 5, 6)
            
            for reminder_type in ReminderType.ALL_TYPES:
                days_before = ReminderType.get_days_before(reminder_type)
                reminder_date = deadline - timedelta(days=days_before)
                
                assert reminder_date < deadline, \
                    f"{reminder_type} date {reminder_date} should be before deadline {deadline}"
    
    def test_reminder_dates_in_correct_order(self, app):
        """Reminder dates should be in chronological order."""
        with app.app_context():
            deadline = date(2026, 5, 6)
            
            dates = []
            for reminder_type in [
                ReminderType.INITIAL,
                ReminderType.FIRST_FOLLOWUP,
                ReminderType.SECOND_FOLLOWUP,
                ReminderType.FINAL
            ]:
                days_before = ReminderType.get_days_before(reminder_type)
                reminder_date = deadline - timedelta(days=days_before)
                dates.append(reminder_date)
            
            # Dates should be in ascending order
            for i in range(len(dates) - 1):
                assert dates[i] < dates[i + 1], \
                    f"Date {dates[i]} should be before {dates[i + 1]}"
    
    def test_reminder_dates_for_specific_deadline(self, app):
        """Test specific reminder dates for May 6, 2026 deadline."""
        with app.app_context():
            deadline = date(2026, 5, 6)
            
            expected_dates = {
                ReminderType.INITIAL: date(2026, 4, 6),       # 30 days before
                ReminderType.FIRST_FOLLOWUP: date(2026, 4, 22),  # 14 days before
                ReminderType.SECOND_FOLLOWUP: date(2026, 4, 29),  # 7 days before
                ReminderType.FINAL: date(2026, 5, 3),         # 3 days before
            }
            
            for reminder_type, expected_date in expected_dates.items():
                days_before = ReminderType.get_days_before(reminder_type)
                actual_date = deadline - timedelta(days=days_before)
                
                assert actual_date == expected_date, \
                    f"{reminder_type}: expected {expected_date}, got {actual_date}"


class TestRunScheduledReminders:
    """Test the run_scheduled_reminders main scheduler function."""
    
    def test_runs_correct_reminder_type_for_date(self, app):
        """Should only run reminders scheduled for today."""
        with app.app_context():
            deadline = date(2026, 5, 6)
            initial_date = deadline - timedelta(days=30)
            
            app.config['RSVP_DEADLINE'] = deadline.strftime(DateFormat.DATABASE)
            
            with patch('app.services.reminder_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.combine(initial_date, datetime.min.time())
                mock_datetime.strptime = datetime.strptime
                
                # Mock send_batch_reminders to avoid actual sending
                with patch.object(ReminderService, 'send_batch_reminders') as mock_send:
                    mock_send.return_value = {'total': 0, 'sent': 0, 'failed': 0, 'skipped': 0, 'details': []}
                    
                    results = ReminderService.run_scheduled_reminders()
                    
                    # Should have called send_batch_reminders for INITIAL
                    mock_send.assert_called_once()
                    call_args = mock_send.call_args
                    assert call_args[1]['reminder_type'] == ReminderType.INITIAL
    
    def test_no_reminders_on_non_scheduled_date(self, app):
        """Should not run any reminders on non-scheduled dates."""
        with app.app_context():
            deadline = date(2026, 5, 6)
            random_date = deadline - timedelta(days=25)  # Not a scheduled date
            
            app.config['RSVP_DEADLINE'] = deadline.strftime(DateFormat.DATABASE)
            
            with patch('app.services.reminder_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.combine(random_date, datetime.min.time())
                mock_datetime.strptime = datetime.strptime
                
                results = ReminderService.run_scheduled_reminders()
                
                # Should return empty dict (no reminders scheduled)
                assert results == {}
    
    def test_multiple_reminder_types_same_day_impossible(self, app):
        """No two reminder types should be scheduled for the same day."""
        with app.app_context():
            deadline = date(2026, 5, 6)
            
            # Get all reminder dates
            reminder_dates = {}
            for reminder_type in ReminderType.ALL_TYPES:
                days_before = ReminderType.get_days_before(reminder_type)
                reminder_date = deadline - timedelta(days=days_before)
                
                # Check no duplicate dates
                assert reminder_date not in reminder_dates.values(), \
                    f"Multiple reminders scheduled for {reminder_date}"
                
                reminder_dates[reminder_type] = reminder_date


class TestReminderHistory:
    """Test ReminderHistory model."""
    
    def test_create_reminder_history(self, app, sample_guest):
        """Should be able to create reminder history record."""
        with app.app_context():
            reminder = ReminderHistory(
                guest_id=sample_guest.id,
                reminder_type=ReminderType.INITIAL,
                status=ReminderStatus.PENDING,
                email_sent_to=sample_guest.email
            )
            db.session.add(reminder)
            db.session.commit()
            
            assert reminder.id is not None
            assert reminder.guest_id == sample_guest.id
            assert reminder.is_sent is False
            assert reminder.can_retry is True
            
            # Cleanup
            db.session.delete(reminder)
            db.session.commit()
    
    def test_is_sent_property(self, app, sample_guest):
        """is_sent should return True only when status is SENT."""
        with app.app_context():
            reminder = ReminderHistory(
                guest_id=sample_guest.id,
                reminder_type=ReminderType.INITIAL,
                status=ReminderStatus.SENT,
                email_sent_to=sample_guest.email,
                sent_at=datetime.now()
            )
            db.session.add(reminder)
            db.session.commit()
            
            assert reminder.is_sent is True
            
            # Cleanup
            db.session.delete(reminder)
            db.session.commit()
    
    def test_can_retry_property(self, app, sample_guest):
        """can_retry should return True for FAILED or PENDING status."""
        with app.app_context():
            # FAILED should be retryable
            failed_reminder = ReminderHistory(
                guest_id=sample_guest.id,
                reminder_type=ReminderType.INITIAL,
                status=ReminderStatus.FAILED,
                email_sent_to=sample_guest.email,
                error_message='Test error'
            )
            db.session.add(failed_reminder)
            db.session.commit()
            
            assert failed_reminder.can_retry is True
            
            # SENT should NOT be retryable
            failed_reminder.status = ReminderStatus.SENT
            db.session.commit()
            
            assert failed_reminder.can_retry is False
            
            # Cleanup
            db.session.delete(failed_reminder)
            db.session.commit()


class TestReminderBatch:
    """Test ReminderBatch model."""
    
    def test_create_reminder_batch(self, app):
        """Should be able to create batch record."""
        with app.app_context():
            batch = ReminderBatch(
                batch_type='scheduled',
                reminder_type=ReminderType.INITIAL,
                executed_by='scheduler',
                days_before_deadline=30
            )
            db.session.add(batch)
            db.session.commit()
            
            assert batch.id is not None
            assert batch.is_complete is False
            assert batch.success_rate == 0
            
            # Cleanup
            db.session.delete(batch)
            db.session.commit()
    
    def test_batch_completion(self, app):
        """Batch should be marked complete when completed_at is set."""
        with app.app_context():
            batch = ReminderBatch(
                batch_type='scheduled',
                reminder_type=ReminderType.INITIAL,
                executed_by='scheduler',
                total_guests=10,
                sent_count=8,
                failed_count=2
            )
            db.session.add(batch)
            db.session.commit()
            
            assert batch.is_complete is False
            
            batch.completed_at = datetime.now()
            db.session.commit()
            
            assert batch.is_complete is True
            
            # Cleanup
            db.session.delete(batch)
            db.session.commit()
    
    def test_success_rate_calculation(self, app):
        """Success rate should be calculated correctly."""
        with app.app_context():
            batch = ReminderBatch(
                batch_type='scheduled',
                reminder_type=ReminderType.INITIAL,
                executed_by='scheduler',
                total_guests=10,
                sent_count=8,
                failed_count=2
            )
            db.session.add(batch)
            db.session.commit()
            
            assert batch.success_rate == 80.0
            
            # Cleanup
            db.session.delete(batch)
            db.session.commit()
    
    def test_success_rate_with_zero_guests(self, app):
        """Success rate should be 0 when no guests."""
        with app.app_context():
            batch = ReminderBatch(
                batch_type='scheduled',
                reminder_type=ReminderType.INITIAL,
                executed_by='scheduler',
                total_guests=0
            )
            db.session.add(batch)
            db.session.commit()
            
            assert batch.success_rate == 0
            
            # Cleanup
            db.session.delete(batch)
            db.session.commit()


class TestReminderStatistics:
    """Test get_reminder_statistics functionality."""
    
    def test_statistics_empty_database(self, app):
        """Should return zero counts with empty database."""
        with app.app_context():
            stats = ReminderService.get_reminder_statistics()
            
            assert 'total_sent' in stats
            assert 'total_failed' in stats
            assert 'total_pending' in stats
            assert 'by_type' in stats
            assert 'recent_batches' in stats
            assert 'opted_out_guests' in stats
    
    def test_statistics_counts_by_status(self, app, sample_guest):
        """Should correctly count reminders by status."""
        with app.app_context():
            # Create reminders with different statuses
            sent = ReminderHistory(
                guest_id=sample_guest.id,
                reminder_type=ReminderType.INITIAL,
                status=ReminderStatus.SENT,
                email_sent_to=sample_guest.email
            )
            failed = ReminderHistory(
                guest_id=sample_guest.id,
                reminder_type=ReminderType.FIRST_FOLLOWUP,
                status=ReminderStatus.FAILED,
                email_sent_to=sample_guest.email
            )
            db.session.add_all([sent, failed])
            db.session.commit()
            
            stats = ReminderService.get_reminder_statistics()
            
            assert stats['total_sent'] >= 1
            assert stats['total_failed'] >= 1
            
            # Cleanup
            db.session.delete(sent)
            db.session.delete(failed)
            db.session.commit()


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_reminder_with_guest_no_email(self, app):
        """Should handle guests without email addresses."""
        with app.app_context():
            guest = Guest(
                name='No Email Guest',
                phone='555-0000',
                email=None,  # No email
                token=secrets.token_urlsafe(32)
            )
            db.session.add(guest)
            db.session.commit()
            
            # Should fail gracefully when trying to send
            success, message = ReminderService.send_reminder(
                guest=guest,
                reminder_type=ReminderType.INITIAL
            )
            
            assert success is False
            assert 'no email' in message.lower()
            
            # Cleanup
            db.session.delete(guest)
            db.session.commit()
    
    def test_leap_year_deadline_handling(self, app):
        """Should handle leap year dates correctly."""
        with app.app_context():
            # Use a leap year date
            deadline = date(2028, 2, 29)  # 2028 is a leap year
            
            app.config['RSVP_DEADLINE'] = deadline.strftime(DateFormat.DATABASE)
            
            # Initial reminder would be Jan 30, 2028 (30 days before)
            expected_initial = date(2028, 1, 30)
            
            with patch('app.services.reminder_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.combine(expected_initial, datetime.min.time())
                mock_datetime.strptime = datetime.strptime
                
                result = ReminderService.should_send_reminder_today(ReminderType.INITIAL)
                assert result is True
    
    def test_year_boundary_deadline(self, app):
        """Should handle deadline crossing year boundary."""
        with app.app_context():
            # Deadline in early January
            deadline = date(2026, 1, 15)
            
            app.config['RSVP_DEADLINE'] = deadline.strftime(DateFormat.DATABASE)
            
            # Initial reminder would be Dec 16, 2025 (30 days before)
            expected_initial = date(2025, 12, 16)
            
            with patch('app.services.reminder_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.combine(expected_initial, datetime.min.time())
                mock_datetime.strptime = datetime.strptime
                
                result = ReminderService.should_send_reminder_today(ReminderType.INITIAL)
                assert result is True