# app/routes/rsvp.py - SESSION-BASED TOKEN VERSION
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort, session
from app.services.guest_service import GuestService
from app.services.rsvp_service import RSVPService
from app.services.allergen_service import AllergenService
from app.forms import RSVPForm
from app.security import rate_limit
from app.constants import (
    LogMessage, HttpStatus, TimeLimit, Template, DEFAULT_CONFIG
)
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('rsvp', __name__, url_prefix='/rsvp')


def get_guest_from_session():
    """Get guest from session token. Returns (guest, error_response) tuple."""
    token = session.get('guest_token')
    if not token:
        logger.warning("No token in session, redirecting to home")
        return None, redirect(url_for('main.index'))
    
    guest = GuestService.get_guest_by_token(token)
    if not guest:
        logger.warning(f"Invalid token in session: {token}")
        session.pop('guest_token', None)
        return None, redirect(url_for('main.index'))
    
    return guest, None


@bp.route('', methods=['GET'])
@rate_limit(max_requests=TimeLimit.RATE_LIMIT_MAX_REQUESTS, window=TimeLimit.RATE_LIMIT_WINDOW)
def rsvp():
    """Handle RSVP - show summary if submitted, form if not."""
    guest, error_response = get_guest_from_session()
    if error_response:
        return error_response
    
    logger.info(LogMessage.RSVP_ACCESS.format(token=guest.token))
    logger.info(LogMessage.RSVP_GUEST_FOUND.format(name=guest.name, id=guest.id))
    
    # Get configuration
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    
    # Check if RSVP deadline has passed
    if RSVPService.is_rsvp_deadline_passed():
        logger.info("RSVP deadline has passed")
        return redirect(url_for('main.index', deadline_passed=1))
    
    # Get existing RSVP if any
    rsvp = RSVPService.get_rsvp_by_guest_id(guest.id)
    
    # If RSVP exists and is not cancelled, show summary page
    if rsvp and not rsvp.is_cancelled:
        logger.info(f"Showing RSVP summary for {guest.name}")
        return render_template('rsvp_summary.html',
                             guest=guest,
                             rsvp=rsvp,
                             admin_phone=admin_phone)
    
    # No RSVP yet (or cancelled) - show form
    allergens = AllergenService.get_all_allergens()
    form = RSVPForm(obj=rsvp, guest=guest)
    
    return render_template('rsvp.html',
                         guest=guest,
                         rsvp=rsvp,
                         form=form,
                         allergens=allergens,
                         admin_phone=admin_phone,
                         personal_message=guest.personal_message,
                         readonly=False,
                         show_warning=False)


@bp.route('/<token>', methods=['GET'])
@rate_limit(max_requests=TimeLimit.RATE_LIMIT_MAX_REQUESTS, window=TimeLimit.RATE_LIMIT_WINDOW)
def rsvp_with_token(token):
    """Handle RSVP access via direct token link (e.g., /rsvp/abc123)."""
    # Validate token and store in session
    guest = GuestService.get_guest_by_token(token)
    if not guest:
        logger.warning(f"Invalid token in URL: {token}")
        abort(404)
    
    # Store token in session
    session['guest_token'] = token
    logger.info(f"Token stored in session from URL: {guest.name}")
    
    # Redirect to main RSVP route (which now has the session)
    return redirect(url_for('rsvp.rsvp'))

@bp.route('/edit', methods=['GET', 'POST'])
@rate_limit(max_requests=TimeLimit.RATE_LIMIT_MAX_REQUESTS, window=TimeLimit.RATE_LIMIT_WINDOW)
def edit():
    """Handle RSVP form editing."""
    guest, error_response = get_guest_from_session()
    if error_response:
        return error_response
    
    logger.info(f"Edit RSVP access: {guest.name}")
    
    # Get configuration
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    
    # Check if RSVP deadline has passed
    if RSVPService.is_rsvp_deadline_passed():
        logger.info("RSVP deadline has passed")
        return redirect(url_for('main.index', deadline_passed=1))
    
    # Get existing RSVP
    rsvp = RSVPService.get_rsvp_by_guest_id(guest.id)
    
    # Check editability
    readonly = False
    show_warning = False
    if rsvp and not rsvp.is_editable:
        logger.info("RSVP not editable")
        readonly = True
        show_warning = True
        flash('Changes are not possible at this time. Please contact ' + admin_phone + ' for assistance.', 'warning')
    
    # Get allergens for form
    allergens = AllergenService.get_all_allergens()
    
    # Initialize form
    form = RSVPForm(obj=rsvp, guest=guest)
    
    if request.method == 'POST' and not readonly:
        logger.info(f"Processing POST request for RSVP form, guest: {guest.name}")
        
        # Use service to process RSVP
        success, message, updated_rsvp = RSVPService.create_or_update_rsvp(guest, request.form)
        
        if success:
            # Redirect to home with success param
            return redirect(url_for('main.index', rsvp_success=1))
        else:
            flash(message, 'danger')
    
    # Render form
    return render_template('rsvp.html',
                         guest=guest,
                         rsvp=rsvp,
                         form=form,
                         allergens=allergens,
                         admin_phone=admin_phone,
                         personal_message=None,  # Don't show modal on edit
                         readonly=readonly,
                         show_warning=show_warning,
                         is_editing=True)


@bp.route('/cancel', methods=['GET', 'POST'])
def cancel():
    """Handle RSVP cancellation."""
    guest, error_response = get_guest_from_session()
    if error_response:
        return error_response
    
    try:
        # Check if guest has RSVP
        rsvp = RSVPService.get_rsvp_by_guest_id(guest.id)
        if not rsvp:
            flash('No RSVP found to cancel.', 'warning')
            return redirect(url_for('rsvp.rsvp'))
        
        admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
        
        logger.info(f"Cancel RSVP for guest: {guest.name}, RSVP ID: {rsvp.id}")
        
        if request.method == 'POST':
            logger.info("Processing cancellation POST request")
            
            # Use service to cancel RSVP
            success, message = RSVPService.cancel_rsvp(guest)
            
            if success:
                return redirect(url_for('main.index', rsvp_cancelled=1))
            else:
                flash(message, 'warning')
                return redirect(url_for('rsvp.rsvp'))
        
        # GET request - show cancellation confirmation page
        return render_template('rsvp_cancel.html', 
                             guest=guest,
                             rsvp=rsvp,
                             admin_phone=admin_phone)
    
    except Exception as e:
        logger.error(f"Unexpected error in cancel: {str(e)}", exc_info=True)
        flash(f'An unexpected error occurred: {str(e)}', 'danger')
        return redirect(url_for('main.index'))


