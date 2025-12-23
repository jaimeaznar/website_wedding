# app/routes/cron.py
"""
Cron endpoints for scheduled tasks.

These endpoints are called by external schedulers (e.g., cron-job.org)
to trigger automated tasks like sending WhatsApp reminders.

Security: All endpoints require a secret key passed as a query parameter.
"""

import os
import logging
from datetime import datetime, date, timedelta
from typing import Optional
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

bp = Blueprint('cron', __name__, url_prefix='/api/cron')


def verify_cron_secret(f):
    """Decorator to verify cron secret key."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        secret = request.args.get('key')
        expected_secret = os.environ.get('CRON_SECRET_KEY')
        
        if not expected_secret:
            logger.error("CRON_SECRET_KEY not configured")
            return jsonify({'error': 'Server misconfigured'}), 500
        
        if not secret or secret != expected_secret:
            logger.warning(f"Invalid cron key attempt from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_reminder_for_today(rsvp_deadline: date, today: date = None) -> Optional[int]:
    """
    Determine which reminder (if any) should be sent today.
    
    Args:
        rsvp_deadline: The RSVP deadline date
        today: Today's date (defaults to actual today, can be overridden for testing)
        
    Returns:
        Reminder number (1, 2, 3, or 4) or None if no reminder today
    """
    if today is None:
        today = date.today()
    
    # Reminder schedule: days before deadline -> reminder number
    reminder_schedule = {
        30: 1,  # 30 days before = Reminder 1
        14: 2,  # 14 days before = Reminder 2
        7: 3,   # 7 days before = Reminder 3
        3: 4,   # 3 days before = Reminder 4 (final)
    }
    
    days_until_deadline = (rsvp_deadline - today).days
    
    return reminder_schedule.get(days_until_deadline)


def calculate_reminder_dates(rsvp_deadline: date) -> dict:
    """
    Calculate all reminder dates for a given deadline.
    
    Args:
        rsvp_deadline: The RSVP deadline date
        
    Returns:
        Dict mapping reminder number to date
    """
    return {
        1: rsvp_deadline - timedelta(days=30),
        2: rsvp_deadline - timedelta(days=14),
        3: rsvp_deadline - timedelta(days=7),
        4: rsvp_deadline - timedelta(days=3),
    }


@bp.route('/send-reminders', methods=['GET', 'POST'])
@verify_cron_secret
def send_reminders():
    """
    Send scheduled WhatsApp reminders.
    
    This endpoint is called by cron-job.org on reminder days.
    It determines which reminder to send based on today's date.
    
    Query parameters:
        key: Secret key for authentication (required)
        force_reminder: Force a specific reminder number (optional, for testing)
        dry_run: If 'true', don't actually send messages (optional)
    
    Returns:
        JSON with results summary
    """
    try:
        # Get RSVP deadline from config
        from app.constants import DEFAULT_CONFIG, DateFormat
        
        rsvp_deadline_str = current_app.config.get('RSVP_DEADLINE', DEFAULT_CONFIG['RSVP_DEADLINE'])
        rsvp_deadline = datetime.strptime(rsvp_deadline_str, DateFormat.DATABASE).date()
        
        today = date.today()
        
        # Check for force_reminder parameter (for testing)
        force_reminder = request.args.get('force_reminder', type=int)
        dry_run = request.args.get('dry_run', '').lower() == 'true'
        
        # Determine which reminder to send
        if force_reminder:
            reminder_number = force_reminder
            logger.info(f"Forced reminder {reminder_number}")
        else:
            reminder_number = get_reminder_for_today(rsvp_deadline, today)
        
        if reminder_number is None:
            # Not a reminder day
            days_left = (rsvp_deadline - today).days
            reminder_dates = calculate_reminder_dates(rsvp_deadline)
            
            return jsonify({
                'status': 'no_action',
                'message': f'No reminder scheduled for today. {days_left} days until deadline.',
                'today': today.isoformat(),
                'rsvp_deadline': rsvp_deadline.isoformat(),
                'upcoming_reminders': {
                    f'reminder_{k}': v.isoformat() 
                    for k, v in reminder_dates.items() 
                    if v >= today
                }
            }), 200
        
        # Get services
        from app.services.airtable_service import get_airtable_service
        from app.services.whatsapp_service import get_whatsapp_service
        
        airtable = get_airtable_service()
        whatsapp = get_whatsapp_service()
        
        # Check if services are configured
        if not airtable.is_configured:
            return jsonify({'error': 'Airtable not configured'}), 500
        
        if not whatsapp.is_configured:
            return jsonify({'error': 'WhatsApp/Twilio not configured'}), 500
        
        # Get guests needing this reminder
        guests = airtable.get_guests_needing_reminder(reminder_number)
        
        if not guests:
            return jsonify({
                'status': 'no_guests',
                'message': f'No guests need reminder {reminder_number}',
                'reminder_number': reminder_number,
                'today': today.isoformat()
            }), 200
        
        # Send reminders
        results = {
            'status': 'completed',
            'reminder_number': reminder_number,
            'today': today.isoformat(),
            'dry_run': dry_run,
            'total': len(guests),
            'sent': 0,
            'failed': 0,
            'details': []
        }
        
        for guest in guests:
            if not guest.token:
                results['failed'] += 1
                results['details'].append({
                    'name': guest.name,
                    'status': 'skipped',
                    'reason': 'No token'
                })
                continue
            
            if dry_run:
                # Don't actually send
                results['sent'] += 1
                results['details'].append({
                    'name': guest.name,
                    'phone': guest.phone,
                    'status': 'dry_run',
                    'would_send': f'Reminder {reminder_number}'
                })
            else:
                # Send the reminder
                result = whatsapp.send_reminder_and_update_airtable(
                    airtable_guest=guest,
                    airtable_service=airtable,
                    reminder_number=reminder_number
                )
                
                if result.success:
                    results['sent'] += 1
                    results['details'].append({
                        'name': guest.name,
                        'phone': guest.phone,
                        'status': 'sent',
                        'message_sid': result.message_sid
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'name': guest.name,
                        'phone': guest.phone,
                        'status': 'failed',
                        'error': result.error
                    })
        
        logger.info(
            f"Reminder {reminder_number} complete: "
            f"{results['sent']}/{results['total']} sent, "
            f"{results['failed']} failed"
        )
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Error in send_reminders: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@bp.route('/status', methods=['GET'])
@verify_cron_secret
def cron_status():
    """
    Get status of reminder schedule.
    
    Returns upcoming reminder dates and current configuration.
    """
    try:
        from app.constants import DEFAULT_CONFIG, DateFormat
        from app.services.airtable_service import get_airtable_service
        
        rsvp_deadline_str = current_app.config.get('RSVP_DEADLINE', DEFAULT_CONFIG['RSVP_DEADLINE'])
        rsvp_deadline = datetime.strptime(rsvp_deadline_str, DateFormat.DATABASE).date()
        
        today = date.today()
        days_left = (rsvp_deadline - today).days
        
        reminder_dates = calculate_reminder_dates(rsvp_deadline)
        
        # Get pending count from Airtable
        airtable = get_airtable_service()
        pending_count = 0
        if airtable.is_configured:
            try:
                pending_guests = airtable.get_guests_pending_rsvp()
                pending_count = len(pending_guests)
            except Exception:
                pending_count = -1  # Indicate error
        
        return jsonify({
            'status': 'ok',
            'today': today.isoformat(),
            'rsvp_deadline': rsvp_deadline.isoformat(),
            'days_until_deadline': days_left,
            'pending_guests': pending_count,
            'reminder_schedule': {
                f'reminder_{k}': {
                    'date': v.isoformat(),
                    'days_before_deadline': (rsvp_deadline - v).days,
                    'status': 'past' if v < today else ('today' if v == today else 'upcoming')
                }
                for k, v in reminder_dates.items()
            },
            'today_reminder': get_reminder_for_today(rsvp_deadline, today)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in cron_status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500