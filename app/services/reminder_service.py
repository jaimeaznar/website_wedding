# app/services/reminder_service.py
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
from flask import current_app, render_template
from flask_mail import Message
from app import db, mail
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.models.reminder import (
    ReminderHistory, ReminderBatch, GuestReminderPreference,
    ReminderType, ReminderStatus
)
from app.constants import Language, DEFAULT_CONFIG, DateFormat

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for managing RSVP reminders."""
    
    @staticmethod
    def get_guests_needing_reminder(reminder_type: str = ReminderType.INITIAL) -> List[Guest]:
        """
        Get list of guests who need a reminder.
        
        Args:
            reminder_type: Type of reminder to check for
            
        Returns:
            List of guests who haven't responded and haven't received this reminder type
        """
        # Get all guests without RSVPs
        guests_without_rsvp = db.session.query(Guest).outerjoin(RSVP).filter(
            RSVP.id == None
        ).all()
        
        # Get guests with cancelled RSVPs (they might want to reconsider)
        guests_with_cancelled = db.session.query(Guest).join(RSVP).filter(
            RSVP.is_cancelled == True
        ).all()
        
        # Combine lists
        all_pending = guests_without_rsvp + guests_with_cancelled
        
        # Filter out those who already received this reminder type
        guests_needing_reminder = []
        for guest in all_pending:
            # Check if guest has opted out
            pref = GuestReminderPreference.query.filter_by(guest_id=guest.id).first()
            if pref and pref.opt_out:
                continue
            
            # Check if already sent this reminder type
            existing_reminder = ReminderHistory.query.filter_by(
                guest_id=guest.id,
                reminder_type=reminder_type,
                status=ReminderStatus.SENT
            ).first()
            
            if not existing_reminder:
                guests_needing_reminder.append(guest)
        
        return guests_needing_reminder
    
    @staticmethod
    def should_send_reminder_today(reminder_type: str) -> bool:
        """
        Check if a specific reminder type should be sent today.
        
        Args:
            reminder_type: Type of reminder to check
            
        Returns:
            True if reminder should be sent today
        """
        if reminder_type == ReminderType.MANUAL:
            return False  # Manual reminders are sent on demand
        
        # Get RSVP deadline
        deadline_str = current_app.config.get('RSVP_DEADLINE', DEFAULT_CONFIG['RSVP_DEADLINE'])
        if not deadline_str:
            return False
        
        try:
            deadline = datetime.strptime(deadline_str, DateFormat.DATABASE).date()
            days_before = ReminderType.get_days_before(reminder_type)
            
            if days_before is None:
                return False
            
            # Calculate when this reminder should be sent
            reminder_date = deadline - timedelta(days=days_before)
            
            return datetime.now().date() == reminder_date
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error checking reminder date: {str(e)}")
            return False
    
    @staticmethod
    def send_reminder(
        guest: Guest,
        reminder_type: str = ReminderType.INITIAL,
        custom_message: Optional[str] = None,
        sent_by: str = 'system'
    ) -> Tuple[bool, str]:
        """
        Send a reminder to a single guest.
        
        Args:
            guest: Guest to send reminder to
            reminder_type: Type of reminder
            custom_message: Optional custom message for manual reminders
            sent_by: Who is sending (system or admin email)
            
        Returns:
            Tuple of (success, message)
        """
        # Check if guest has email
        if not guest.email:
            return False, f"Guest {guest.name} has no email address"
        
        # Check guest preferences
        pref = GuestReminderPreference.query.filter_by(guest_id=guest.id).first()
        if not pref:
            pref = GuestReminderPreference(guest_id=guest.id)
            db.session.add(pref)
            db.session.flush()
        
        if not pref.can_send_reminder:
            return False, f"Guest {guest.name} has opted out or reached reminder limit"
        
        # Create reminder history record
        reminder = ReminderHistory(
            guest_id=guest.id,
            reminder_type=reminder_type,
            email_sent_to=guest.email,
            scheduled_for=datetime.now(),
            sent_by=sent_by,
            status=ReminderStatus.PENDING
        )
        
        if custom_message:
            reminder.notes = custom_message
        
        db.session.add(reminder)
        db.session.flush()
        
        try:
            # Determine subject and template based on reminder type
            subject, template = ReminderService._get_reminder_template(
                reminder_type,
                guest.language_preference
            )
            
            reminder.email_subject = subject
            
            # Prepare email
            msg = Message(
                subject=subject,
                recipients=[guest.email],
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            
            # Get RSVP deadline for template
            deadline_str = current_app.config.get('RSVP_DEADLINE', DEFAULT_CONFIG['RSVP_DEADLINE'])
            deadline_formatted = datetime.strptime(deadline_str, DateFormat.DATABASE).strftime(DateFormat.DISPLAY)
            
            # Render email body
            html_body = render_template(
                template,
                guest=guest,
                rsvp_deadline=deadline_formatted,
                custom_message=custom_message,
                reminder_type=reminder_type
            )
            
            msg.html = html_body
            
            # Send email
            mail.send(msg)
            
            # Update reminder status
            reminder.status = ReminderStatus.SENT
            reminder.sent_at = datetime.now()
            
            # Update guest preference
            pref.increment_sent_count()
            
            db.session.commit()
            
            logger.info(f"Sent {reminder_type} reminder to {guest.name} ({guest.email})")
            return True, f"Reminder sent to {guest.name}"
            
        except Exception as e:
            # Update reminder status
            reminder.status = ReminderStatus.FAILED
            reminder.error_message = str(e)
            db.session.commit()
            
            logger.error(f"Failed to send reminder to {guest.name}: {str(e)}")
            return False, f"Failed to send reminder: {str(e)}"
    
    @staticmethod
    def send_batch_reminders(
        reminder_type: str = ReminderType.INITIAL,
        executed_by: str = 'scheduler'
    ) -> Dict[str, Any]:
        """
        Send reminders to all guests who need them.
        
        Args:
            reminder_type: Type of reminder to send
            executed_by: Who is executing (scheduler or admin)
            
        Returns:
            Dictionary with batch results
        """
        # Create batch record
        batch = ReminderBatch(
            batch_type='scheduled' if executed_by == 'scheduler' else 'manual',
            reminder_type=reminder_type,
            executed_by=executed_by,
            days_before_deadline=ReminderType.get_days_before(reminder_type)
        )
        db.session.add(batch)
        db.session.flush()
        
        # Get guests needing reminder
        guests = ReminderService.get_guests_needing_reminder(reminder_type)
        
        results = {
            'total': len(guests),
            'sent': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        for guest in guests:
            # Check if guest has already responded (might have happened during batch)
            rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
            if rsvp and not rsvp.is_cancelled:
                results['skipped'] += 1
                results['details'].append({
                    'guest': guest.name,
                    'status': 'skipped',
                    'reason': 'Already responded'
                })
                continue
            
            # Send reminder
            success, message = ReminderService.send_reminder(
                guest,
                reminder_type,
                sent_by=executed_by
            )
            
            if success:
                results['sent'] += 1
                results['details'].append({
                    'guest': guest.name,
                    'status': 'sent',
                    'message': message
                })
            else:
                results['failed'] += 1
                results['details'].append({
                    'guest': guest.name,
                    'status': 'failed',
                    'message': message
                })
        
        # Update batch statistics
        batch.total_guests = results['total']
        batch.sent_count = results['sent']
        batch.failed_count = results['failed']
        batch.skipped_count = results['skipped']
        batch.completed_at = datetime.now()
        db.session.commit()
        
        logger.info(f"Batch reminder {reminder_type} completed: {results['sent']}/{results['total']} sent")
        
        return results
    
    @staticmethod
    def send_manual_reminder(
        guest_ids: List[int],
        message: Optional[str] = None,
        sent_by: str = 'admin'
    ) -> Dict[str, Any]:
        """
        Send manual reminders to specific guests.
        
        Args:
            guest_ids: List of guest IDs to send reminders to
            message: Optional custom message
            sent_by: Admin email or identifier
            
        Returns:
            Dictionary with results
        """
        results = {
            'total': len(guest_ids),
            'sent': 0,
            'failed': 0,
            'details': []
        }
        
        for guest_id in guest_ids:
            guest = Guest.query.get(guest_id)
            if not guest:
                results['failed'] += 1
                results['details'].append({
                    'guest_id': guest_id,
                    'status': 'failed',
                    'message': 'Guest not found'
                })
                continue
            
            success, message_result = ReminderService.send_reminder(
                guest,
                ReminderType.MANUAL,
                custom_message=message,
                sent_by=sent_by
            )
            
            if success:
                results['sent'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'guest': guest.name,
                'status': 'sent' if success else 'failed',
                'message': message_result
            })
        
        return results
    
    @staticmethod
    def get_reminder_history(guest_id: Optional[int] = None) -> List[ReminderHistory]:
        """
        Get reminder history, optionally filtered by guest.
        
        Args:
            guest_id: Optional guest ID to filter by
            
        Returns:
            List of reminder history records
        """
        query = ReminderHistory.query
        
        if guest_id:
            query = query.filter_by(guest_id=guest_id)
        
        return query.order_by(ReminderHistory.created_at.desc()).all()
    
    @staticmethod
    def get_reminder_statistics() -> Dict[str, Any]:
        """
        Get statistics about reminders.
        
        Returns:
            Dictionary with reminder statistics
        """
        total_sent = ReminderHistory.query.filter_by(status=ReminderStatus.SENT).count()
        total_failed = ReminderHistory.query.filter_by(status=ReminderStatus.FAILED).count()
        total_pending = ReminderHistory.query.filter_by(status=ReminderStatus.PENDING).count()
        
        # Get breakdown by type
        by_type = {}
        for reminder_type in ReminderType.ALL_TYPES:
            by_type[reminder_type] = ReminderHistory.query.filter_by(
                reminder_type=reminder_type,
                status=ReminderStatus.SENT
            ).count()
        
        # Get recent batches
        recent_batches = ReminderBatch.query.order_by(
            ReminderBatch.started_at.desc()
        ).limit(10).all()
        
        # Get guests with opt-out
        opted_out = GuestReminderPreference.query.filter_by(opt_out=True).count()
        
        return {
            'total_sent': total_sent,
            'total_failed': total_failed,
            'total_pending': total_pending,
            'by_type': by_type,
            'recent_batches': recent_batches,
            'opted_out_guests': opted_out
        }
    
    @staticmethod
    def _get_reminder_template(reminder_type: str, language: str = Language.DEFAULT) -> Tuple[str, str]:
        """
        Get email subject and template for reminder type.
        
        Args:
            reminder_type: Type of reminder
            language: Guest's preferred language
            
        Returns:
            Tuple of (subject, template_path)
        """
        # Map reminder types to templates
        templates = {
            ReminderType.INITIAL: {
                'en': ('RSVP Reminder - 30 Days Left', 'emails/reminder_initial_en.html'),
                'es': ('Recordatorio RSVP - 30 Días Restantes', 'emails/reminder_initial_es.html')
            },
            ReminderType.FIRST_FOLLOWUP: {
                'en': ('RSVP Reminder - 2 Weeks Left', 'emails/reminder_first_en.html'),
                'es': ('Recordatorio RSVP - 2 Semanas Restantes', 'emails/reminder_first_es.html')
            },
            ReminderType.SECOND_FOLLOWUP: {
                'en': ('RSVP Reminder - 1 Week Left', 'emails/reminder_second_en.html'),
                'es': ('Recordatorio RSVP - 1 Semana Restante', 'emails/reminder_second_es.html')
            },
            ReminderType.FINAL: {
                'en': ('Final RSVP Reminder - 3 Days Left!', 'emails/reminder_final_en.html'),
                'es': ('Recordatorio Final RSVP - ¡3 Días Restantes!', 'emails/reminder_final_es.html')
            },
            ReminderType.MANUAL: {
                'en': ('RSVP Reminder for Our Wedding', 'emails/reminder_manual_en.html'),
                'es': ('Recordatorio RSVP para Nuestra Boda', 'emails/reminder_manual_es.html')
            }
        }
        
        # Get template for type and language
        template_info = templates.get(reminder_type, templates[ReminderType.INITIAL])
        return template_info.get(language, template_info['en'])
    
    @staticmethod
    def opt_out_guest(guest_id: int) -> bool:
        """
        Opt a guest out of reminders.
        
        Args:
            guest_id: ID of guest to opt out
            
        Returns:
            True if successful
        """
        pref = GuestReminderPreference.query.filter_by(guest_id=guest_id).first()
        if not pref:
            pref = GuestReminderPreference(guest_id=guest_id)
            db.session.add(pref)
        
        pref.opt_out = True
        db.session.commit()
        
        logger.info(f"Guest {guest_id} opted out of reminders")
        return True
    
    @staticmethod
    def run_scheduled_reminders():
        """
        Run scheduled reminders. This should be called by a scheduler/cron job.
        """
        results = {}
        
        # Check each reminder type
        for reminder_type in [
            ReminderType.INITIAL,
            ReminderType.FIRST_FOLLOWUP,
            ReminderType.SECOND_FOLLOWUP,
            ReminderType.FINAL
        ]:
            if ReminderService.should_send_reminder_today(reminder_type):
                logger.info(f"Running scheduled reminder: {reminder_type}")
                result = ReminderService.send_batch_reminders(
                    reminder_type=reminder_type,
                    executed_by='scheduler'
                )
                results[reminder_type] = result
        
        return results