# app/routes/rsvp.py - REFACTORED VERSION
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from app.services.guest_service import GuestService
from app.services.rsvp_service import RSVPService
from app.services.allergen_service import AllergenService
from app.forms import RSVPForm, RSVPCancellationForm
from app.security import rate_limit
from app.constants import (
    LogMessage, ErrorMessage, SuccessMessage, FlashCategory,
    HttpStatus, TimeLimit, Template, DEFAULT_CONFIG
)
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('rsvp', __name__, url_prefix='/rsvp')


@bp.route('/')
def landing():
    """Landing page for RSVP without token."""
    return render_template(Template.RSVP_LANDING)


@bp.route('/<token>', methods=['GET', 'POST'])
@rate_limit(max_requests=TimeLimit.RATE_LIMIT_MAX_REQUESTS, window=TimeLimit.RATE_LIMIT_WINDOW)
def rsvp_form(token):
    """Handle RSVP form display and submission."""
    logger.info(LogMessage.RSVP_ACCESS.format(token=token))
    
    # Get guest by token
    guest = GuestService.get_guest_by_token(token)
    if not guest:
        logger.warning(f"Invalid token attempted: {token}")
        abort(HttpStatus.NOT_FOUND)
    
    logger.info(LogMessage.RSVP_GUEST_FOUND.format(name=guest.name, id=guest.id))
    
    # Get allergens for form
    allergens = AllergenService.get_all_allergens()
    logger.debug(f"Available allergens: {[a.name for a in allergens]}")
    
    # Get existing RSVP if any
    rsvp = RSVPService.get_rsvp_by_guest_id(guest.id)
    
    # Get configuration
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    rsvp_deadline = RSVPService.get_rsvp_deadline_formatted()
    
    # Check if RSVP deadline has passed
    if RSVPService.is_rsvp_deadline_passed():
        logger.info("RSVP deadline has passed")
        return render_template('rsvp_deadline_passed.html', 
                             guest=guest,
                             rsvp=rsvp,
                             admin_phone=admin_phone,
                             rsvp_deadline=rsvp_deadline)
    
    # Handle previously declined or cancelled RSVPs
    if rsvp:
        if rsvp.is_cancelled:
            logger.info("Previously cancelled RSVP")
            return render_template('rsvp_previously_cancelled.html', 
                                 guest=guest,
                                 admin_phone=admin_phone,
                                 rsvp_deadline=rsvp_deadline)
        elif not rsvp.is_attending and not rsvp.is_cancelled:
            logger.info("Previously declined RSVP")
            return render_template('rsvp_previously_declined.html', 
                                 guest=guest,
                                 admin_phone=admin_phone,
                                 rsvp_deadline=rsvp_deadline)
    
    # Check editability
    readonly = False
    show_warning = False
    if rsvp and not rsvp.is_editable:
        logger.info("RSVP not editable")
        readonly = True
        show_warning = True
        flash('Changes are not possible at this time. Please contact ' + admin_phone + ' for assistance.', 'warning')
    
    # Initialize form
    form = RSVPForm(obj=rsvp, guest=guest)
    
    if request.method == 'POST' and not readonly:
        logger.info(f"Processing POST request for RSVP form, guest: {guest.name}")
        
        # Use service to process RSVP
        success, message, updated_rsvp = RSVPService.create_or_update_rsvp(guest, request.form)
        
        if success:
            flash(message, 'success' if updated_rsvp.is_attending else 'info')
            
            # Redirect to appropriate confirmation page
            if updated_rsvp.is_attending:
                return redirect(url_for('rsvp.confirmation_accepted'))
            else:
                return redirect(url_for('rsvp.confirmation_declined'))
        else:
            flash(message, 'danger')
            # Re-render form with errors
    
    # Render form
    return render_template('rsvp.html',
                         guest=guest,
                         rsvp=rsvp,
                         form=form,
                         allergens=allergens,
                         admin_phone=admin_phone,
                         readonly=readonly,
                         show_warning=show_warning)


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
                flash(message, 'info')
                return redirect(url_for('rsvp.confirmation_cancelled'))
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
    """Show confirmation page for accepted RSVP."""
    return render_template('rsvp_accepted.html')


@bp.route('/confirmation/declined')
def confirmation_declined():
    """Show confirmation page for declined RSVP."""
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    return render_template('rsvp_declined.html', admin_phone=admin_phone)


@bp.route('/confirmation/cancelled')
def confirmation_cancelled():
    """Show confirmation page for cancelled RSVP."""
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    return render_template('rsvp_cancelled.html', admin_phone=admin_phone)


@bp.route('/confirmation')
def confirmation():
    """Legacy confirmation route - redirect to accepted."""
    return redirect(url_for('rsvp.confirmation_accepted'))