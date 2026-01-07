# app/routes/rsvp.py - REFACTORED VERSION
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
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


@bp.route('/<token>', methods=['GET'])
@rate_limit(max_requests=TimeLimit.RATE_LIMIT_MAX_REQUESTS, window=TimeLimit.RATE_LIMIT_WINDOW)
def rsvp_form(token):
    """Handle RSVP - show summary if submitted, form if not."""
    logger.info(LogMessage.RSVP_ACCESS.format(token=token))
    
    # Get guest by token
    guest = GuestService.get_guest_by_token(token)
    if not guest:
        logger.warning(f"Invalid token attempted: {token}")
        abort(HttpStatus.NOT_FOUND)
    
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

@bp.route('/<token>/edit', methods=['GET', 'POST'])
@rate_limit(max_requests=TimeLimit.RATE_LIMIT_MAX_REQUESTS, window=TimeLimit.RATE_LIMIT_WINDOW)
def edit_rsvp(token):
    """Handle RSVP form editing."""
    logger.info(f"Edit RSVP access: {token}")
    
    # Get guest by token
    guest = GuestService.get_guest_by_token(token)
    if not guest:
        logger.warning(f"Invalid token attempted: {token}")
        abort(HttpStatus.NOT_FOUND)
    
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

@bp.route('/<token>/cancel', methods=['GET', 'POST'])
def cancel_rsvp(token):
    """Handle RSVP cancellation."""
    try:
        # Get guest
        guest = GuestService.get_guest_by_token(token)
        if not guest:
            abort(404)
        
        # Check if guest has RSVP
        rsvp = RSVPService.get_rsvp_by_guest_id(guest.id)
        if not rsvp:
            flash('No RSVP found to cancel.', 'warning')
            return redirect(url_for('rsvp.rsvp_form', token=token))
        
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
                return redirect(url_for('rsvp.rsvp_form', token=token))
        
        # GET request - show cancellation confirmation page
        return render_template('rsvp_cancel.html', 
                             guest=guest,
                             rsvp=rsvp,
                             admin_phone=admin_phone)
    
    except Exception as e:
        logger.error(f"Unexpected error in cancel_rsvp: {str(e)}", exc_info=True)
        flash(f'An unexpected error occurred: {str(e)}', 'danger')
        return redirect(url_for('main.index'))


@bp.route('/confirmation/accepted')
def confirmation_accepted():
    """Legacy route - redirect to home with success."""
    return redirect(url_for('main.index', rsvp_success=1))


@bp.route('/confirmation/declined')
def confirmation_declined():
    """Legacy route - redirect to home with success."""
    return redirect(url_for('main.index', rsvp_success=1))


@bp.route('/confirmation/cancelled')
def confirmation_cancelled():
    """Legacy route - redirect to home."""
    return redirect(url_for('main.index', rsvp_cancelled=1))


@bp.route('/confirmation')
def confirmation():
    """Legacy confirmation route - redirect to home."""
    return redirect(url_for('main.index', rsvp_success=1))