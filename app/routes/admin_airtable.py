# app/routes/admin_airtable.py
"""
Admin routes for Airtable sync and WhatsApp messaging.

These routes handle:
- Syncing guests from Airtable to local database
- Generating tokens for guests
- Sending RSVP links via WhatsApp
- Sending reminders via WhatsApp
- Viewing Airtable sync status
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from functools import wraps
from datetime import datetime
import logging

from app.constants import Security

logger = logging.getLogger(__name__)

bp = Blueprint('admin_airtable', __name__, url_prefix='/admin/airtable')


def admin_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.cookies.get(Security.ADMIN_COOKIE_NAME):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_services():
    """Get Airtable and WhatsApp service instances."""
    from app.services.airtable_service import get_airtable_service
    from app.services.whatsapp_service import get_whatsapp_service
    
    return get_airtable_service(), get_whatsapp_service()


# =============================================================================
# DASHBOARD / STATUS
# =============================================================================

@bp.route('/')
@admin_required
def airtable_dashboard():
    """Display Airtable integration dashboard."""
    airtable, whatsapp = get_services()
    
    # Check configuration status
    config_status = {
        'airtable_configured': airtable.is_configured,
        'whatsapp_configured': whatsapp.is_configured,
    }
    
    # Get statistics if configured
    stats = None
    guests = []
    error = None
    
    if airtable.is_configured:
        try:
            stats = airtable.get_statistics()
            guests = airtable.get_all_guests()
        except Exception as e:
            error = str(e)
            logger.error(f"Error fetching Airtable data: {e}")
    
    return render_template(
        'admin/airtable_dashboard.html',
        config_status=config_status,
        stats=stats,
        guests=guests,
        error=error
    )


@bp.route('/status')
@admin_required
def status():
    """API endpoint to check service status."""
    airtable, whatsapp = get_services()
    
    status = {
        'airtable': {
            'configured': airtable.is_configured,
            'base_id': airtable.base_id[:10] + '...' if airtable.base_id else None,
        },
        'whatsapp': {
            'configured': whatsapp.is_configured,
            'number': whatsapp.whatsapp_number,
        },
        'base_url': whatsapp.base_url,
    }
    
    # Test Airtable connection
    if airtable.is_configured:
        try:
            guests = airtable.get_all_guests()
            status['airtable']['connected'] = True
            status['airtable']['guest_count'] = len(guests)
        except Exception as e:
            status['airtable']['connected'] = False
            status['airtable']['error'] = str(e)
    
    return jsonify(status)


# =============================================================================
# SYNC OPERATIONS
# =============================================================================

@bp.route('/sync-to-local', methods=['POST'])
@admin_required
def sync_to_local():
    """Sync all guests from Airtable to local database."""
    airtable, _ = get_services()
    
    if not airtable.is_configured:
        flash('Airtable is not configured', 'error')
        return redirect(url_for('admin_airtable.airtable_dashboard'))
    
    try:
        created, updated = airtable.sync_all_to_local_db()
        flash(f'Sync complete: {created} created, {updated} updated', 'success')
        logger.info(f"Airtable sync: {created} created, {updated} updated")
    except Exception as e:
        flash(f'Sync failed: {str(e)}', 'error')
        logger.error(f"Airtable sync failed: {e}")
    
    return redirect(url_for('admin_airtable.airtable_dashboard'))


@bp.route('/generate-tokens', methods=['POST'])
@admin_required
def generate_tokens():
    """Generate tokens for all guests who don't have one."""
    airtable, _ = get_services()
    
    if not airtable.is_configured:
        flash('Airtable is not configured', 'error')
        return redirect(url_for('admin_airtable.airtable_dashboard'))
    
    try:
        results = airtable.generate_tokens_for_all()
        flash(f'Generated tokens for {len(results)} guests', 'success')
        logger.info(f"Generated tokens for {len(results)} guests")
    except Exception as e:
        flash(f'Token generation failed: {str(e)}', 'error')
        logger.error(f"Token generation failed: {e}")
    
    return redirect(url_for('admin_airtable.airtable_dashboard'))


@bp.route('/generate-token/<record_id>', methods=['POST'])
@admin_required
def generate_single_token(record_id):
    """Generate token for a single guest."""
    airtable, _ = get_services()
    
    if not airtable.is_configured:
        flash('Airtable is not configured', 'error')
        return redirect(url_for('admin_airtable.airtable_dashboard'))
    
    try:
        token = airtable.generate_token_for_guest(record_id)
        flash(f'Token generated successfully', 'success')
    except Exception as e:
        flash(f'Token generation failed: {str(e)}', 'error')
        logger.error(f"Token generation failed for {record_id}: {e}")
    
    return redirect(url_for('admin_airtable.airtable_dashboard'))


# =============================================================================
# WHATSAPP - SEND RSVP LINKS
# =============================================================================

@bp.route('/send-link/<record_id>', methods=['POST'])
@admin_required
def send_single_link(record_id):
    """Send RSVP link to a single guest via WhatsApp."""
    airtable, whatsapp = get_services()
    
    if not airtable.is_configured or not whatsapp.is_configured:
        flash('Airtable or WhatsApp is not configured', 'error')
        return redirect(url_for('admin_airtable.airtable_dashboard'))
    
    try:
        # Get guest from Airtable
        guests = airtable.get_all_guests()
        guest = next((g for g in guests if g.record_id == record_id), None)
        
        if not guest:
            flash('Guest not found', 'error')
            return redirect(url_for('admin_airtable.airtable_dashboard'))
        
        # Send WhatsApp and update Airtable
        result = whatsapp.send_rsvp_link_and_update_airtable(guest, airtable)
        
        if result.success:
            flash(f'RSVP link sent to {guest.name}', 'success')
        else:
            flash(f'Failed to send: {result.error}', 'error')
            
    except Exception as e:
        flash(f'Error sending link: {str(e)}', 'error')
        logger.error(f"Error sending link to {record_id}: {e}")
    
    return redirect(url_for('admin_airtable.airtable_dashboard'))


@bp.route('/send-all-links', methods=['POST'])
@admin_required
def send_all_links():
    """Send RSVP links to all guests who haven't received one."""
    airtable, whatsapp = get_services()
    
    if not airtable.is_configured or not whatsapp.is_configured:
        flash('Airtable or WhatsApp is not configured', 'error')
        return redirect(url_for('admin_airtable.airtable_dashboard'))
    
    try:
        # Get guests needing links
        guests = airtable.get_guests_needing_link()
        
        if not guests:
            flash('No guests need RSVP links', 'info')
            return redirect(url_for('admin_airtable.airtable_dashboard'))
        
        sent = 0
        failed = 0
        
        for guest in guests:
            result = whatsapp.send_rsvp_link_and_update_airtable(guest, airtable)
            if result.success:
                sent += 1
            else:
                failed += 1
                logger.error(f"Failed to send to {guest.name}: {result.error}")
        
        flash(f'Sent {sent} links, {failed} failed', 'success' if failed == 0 else 'warning')
        logger.info(f"Bulk send links: {sent} sent, {failed} failed")
        
    except Exception as e:
        flash(f'Error sending links: {str(e)}', 'error')
        logger.error(f"Bulk send links failed: {e}")
    
    return redirect(url_for('admin_airtable.airtable_dashboard'))


# =============================================================================
# WHATSAPP - SEND REMINDERS
# =============================================================================

@bp.route('/send-reminder/<record_id>/<int:reminder_number>', methods=['POST'])
@admin_required
def send_single_reminder(record_id, reminder_number):
    """Send a specific reminder to a single guest."""
    airtable, whatsapp = get_services()
    
    if not airtable.is_configured or not whatsapp.is_configured:
        flash('Airtable or WhatsApp is not configured', 'error')
        return redirect(url_for('admin_airtable.airtable_dashboard'))
    
    try:
        # Get guest from Airtable
        guests = airtable.get_all_guests()
        guest = next((g for g in guests if g.record_id == record_id), None)
        
        if not guest:
            flash('Guest not found', 'error')
            return redirect(url_for('admin_airtable.airtable_dashboard'))
        
        if not guest.token:
            flash('Guest has no token. Generate one first.', 'error')
            return redirect(url_for('admin_airtable.airtable_dashboard'))
        
        # Send reminder
        result = whatsapp.send_reminder_and_update_airtable(guest, airtable, reminder_number)
        
        if result.success:
            flash(f'Reminder {reminder_number} sent to {guest.name}', 'success')
        else:
            flash(f'Failed to send: {result.error}', 'error')
            
    except Exception as e:
        flash(f'Error sending reminder: {str(e)}', 'error')
        logger.error(f"Error sending reminder to {record_id}: {e}")
    
    return redirect(url_for('admin_airtable.airtable_dashboard'))


@bp.route('/send-reminders/<int:reminder_number>', methods=['POST'])
@admin_required
def send_batch_reminders(reminder_number):
    """Send a specific reminder to all guests who need it."""
    airtable, whatsapp = get_services()
    
    if not airtable.is_configured or not whatsapp.is_configured:
        flash('Airtable or WhatsApp is not configured', 'error')
        return redirect(url_for('admin_airtable.airtable_dashboard'))
    
    try:
        # Get guests needing this reminder
        guests = airtable.get_guests_needing_reminder(reminder_number)
        
        if not guests:
            flash(f'No guests need reminder {reminder_number}', 'info')
            return redirect(url_for('admin_airtable.airtable_dashboard'))
        
        sent = 0
        failed = 0
        
        for guest in guests:
            if not guest.token:
                logger.warning(f"Skipping {guest.name} - no token")
                failed += 1
                continue
            
            result = whatsapp.send_reminder_and_update_airtable(guest, airtable, reminder_number)
            if result.success:
                sent += 1
            else:
                failed += 1
                logger.error(f"Failed to send reminder to {guest.name}: {result.error}")
        
        flash(f'Reminder {reminder_number}: {sent} sent, {failed} failed', 
              'success' if failed == 0 else 'warning')
        logger.info(f"Bulk reminder {reminder_number}: {sent} sent, {failed} failed")
        
    except Exception as e:
        flash(f'Error sending reminders: {str(e)}', 'error')
        logger.error(f"Bulk reminder {reminder_number} failed: {e}")
    
    return redirect(url_for('admin_airtable.airtable_dashboard'))


# =============================================================================
# TEST ENDPOINTS
# =============================================================================

@bp.route('/test-whatsapp', methods=['POST'])
@admin_required
def test_whatsapp():
    """Send a test WhatsApp message to the admin."""
    _, whatsapp = get_services()
    
    if not whatsapp.is_configured:
        flash('WhatsApp is not configured', 'error')
        return redirect(url_for('admin_airtable.airtable_dashboard'))
    
    admin_phone = current_app.config.get('ADMIN_PHONE')
    
    if not admin_phone:
        flash('ADMIN_PHONE not configured in environment', 'error')
        return redirect(url_for('admin_airtable.airtable_dashboard'))
    
    try:
        result = whatsapp.send_message(
            to_phone=admin_phone,
            message=(
                "🧪 *Test Message*\n\n"
                "This is a test from your wedding website WhatsApp integration.\n\n"
                f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "If you received this, WhatsApp is working! ✅"
            )
        )
        
        if result.success:
            flash(f'Test message sent to {admin_phone}', 'success')
        else:
            flash(f'Test failed: {result.error}', 'error')
            
    except Exception as e:
        flash(f'Test failed: {str(e)}', 'error')
        logger.error(f"WhatsApp test failed: {e}")
    
    return redirect(url_for('admin_airtable.airtable_dashboard'))


@bp.route('/test-phone-normalize', methods=['POST'])
@admin_required
def test_phone_normalize():
    """Test phone number normalization."""
    from app.services.whatsapp_service import WhatsAppService
    
    phone = request.form.get('phone', '')
    
    try:
        normalized = WhatsAppService.normalize_phone(phone)
        flash(f'"{phone}" → "{normalized}" ✓', 'success')
    except Exception as e:
        flash(f'"{phone}" → Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_airtable.airtable_dashboard'))


# =============================================================================
# API ENDPOINTS (for AJAX calls)
# =============================================================================

@bp.route('/api/guests')
@admin_required
def api_guests():
    """API endpoint to get all guests from Airtable."""
    airtable, _ = get_services()
    
    if not airtable.is_configured:
        return jsonify({'error': 'Airtable not configured'}), 400
    
    try:
        guests = airtable.get_all_guests()
        return jsonify({
            'guests': [
                {
                    'record_id': g.record_id,
                    'name': g.name,
                    'phone': g.phone,
                    'language': g.language,
                    'status': g.status,
                    'token': g.token,
                    'link_sent': g.link_sent.isoformat() if g.link_sent else None,
                    'rsvp_date': g.rsvp_date.isoformat() if g.rsvp_date else None,
                }
                for g in guests
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/stats')
@admin_required
def api_stats():
    """API endpoint to get Airtable statistics."""
    airtable, _ = get_services()
    
    if not airtable.is_configured:
        return jsonify({'error': 'Airtable not configured'}), 400
    
    try:
        stats = airtable.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500