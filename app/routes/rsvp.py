# app/routes/rsvp.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP, AdditionalGuest
from app.models.allergen import Allergen, GuestAllergen
from app.utils.email import send_cancellation_notification
from app.forms import RSVPForm, RSVPCancellationForm
from app.security import rate_limit
from datetime import datetime
import logging

# Set up logger
logger = logging.getLogger(__name__)

bp = Blueprint('rsvp', __name__, url_prefix='/rsvp')

def display_warning(message, admin_phone):
    flash(f'{message} Please contact {admin_phone} for assistance.', 'warning')
    return True

@bp.route('/')
def landing():
    return render_template('rsvp_landing.html')

@bp.route('/<token>', methods=['GET', 'POST'])
@rate_limit(max_requests=30, window=300)  # Rate limit RSVP submissions
def rsvp_form(token):
    logger.info(f"RSVP form accessed with token: {token}")
    guest = Guest.query.filter_by(token=token).first_or_404()
    logger.info(f"Guest found: {guest.name} (ID: {guest.id})")
    
    allergens = Allergen.query.all()
    rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
    
    if rsvp:
        logger.info(f"Existing RSVP found (attending: {rsvp.is_attending}, cancelled: {rsvp.is_cancelled})")
    else:
        logger.info("No existing RSVP found")
    
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    show_warning = False
    
    # Check editability
    if rsvp and not rsvp.is_editable:
        logger.info("RSVP not editable")
        show_warning = display_warning('Changes are not possible at this time.', admin_phone)
        return render_template('rsvp.html', 
                             guest=guest, 
                             rsvp=rsvp, 
                             allergens=allergens,
                             admin_phone=admin_phone,
                             readonly=True,
                             show_warning=show_warning)
    
    # Initialize form with guest
    form = RSVPForm(obj=rsvp, guest=guest)
    
    if request.method == 'POST':
        logger.info(f"Processing POST request for RSVP form, guest: {guest.name}")
        
        # Log form data for debugging
        logger.debug(f"Form data keys: {list(request.form.keys())}")
        
        try:
            # Create or get existing RSVP
            if not rsvp:
                logger.info("Creating new RSVP")
                rsvp = RSVP(guest_id=guest.id)
                db.session.add(rsvp)
            else:
                logger.info("Updating existing RSVP")
            
            # Basic info - handle both 'yes' and 'no' responses
            is_attending = request.form.get('is_attending') == 'yes'
            logger.info(f"Setting is_attending to: {is_attending}")
            rsvp.is_attending = is_attending
            
            # Process other fields if attending
            if is_attending:
                logger.info("Processing attendance details")
                rsvp.hotel_name = request.form.get('hotel_name', '')
                rsvp.transport_to_church = 'transport_to_church' in request.form
                rsvp.transport_to_reception = 'transport_to_reception' in request.form
                rsvp.transport_to_hotel = 'transport_to_hotel' in request.form
                
                logger.debug(f"Hotel: {rsvp.hotel_name}")
                logger.debug(f"Transport - Church: {rsvp.transport_to_church}, Reception: {rsvp.transport_to_reception}, Hotel: {rsvp.transport_to_hotel}")
                
                # Process plus one if guest has plus one but is not family
                if guest.has_plus_one and not guest.is_family:
                    logger.info("Processing plus one")
                    plus_one_name = request.form.get('plus_one_name', '').strip()
                    if plus_one_name:
                        logger.debug(f"Plus one name: {plus_one_name}")
                        rsvp.plus_one_name = plus_one_name
                        guest.plus_one_used = True
                        
                        # Create an additional guest entry for the plus one
                        existing_plus_one = AdditionalGuest.query.filter_by(
                            rsvp_id=rsvp.id,
                            name=plus_one_name
                        ).first()
                        
                        if not existing_plus_one:
                            plus_one = AdditionalGuest(
                                rsvp_id=rsvp.id,
                                name=plus_one_name,
                                is_child=False
                            )
                            db.session.add(plus_one)
                            logger.debug(f"Added plus one as additional guest: {plus_one_name}")
                
                # Process adults count and children count for family guests
                if guest.is_family:
                    try:
                        rsvp.adults_count = int(request.form.get('adults_count', 0))
                        logger.debug(f"Adults count: {rsvp.adults_count}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing adults_count: {e}")
                        rsvp.adults_count = 0
                        
                    try:
                        rsvp.children_count = int(request.form.get('children_count', 0))
                        logger.debug(f"Children count: {rsvp.children_count}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing children_count: {e}")
                        rsvp.children_count = 0
                    
                    # Handle family additional guests
                    logger.info("Processing family additional guests")
                    # Clear existing additional guests
                    existing_guests = AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).all()
                    for g in existing_guests:
                        logger.debug(f"Removing existing additional guest: {g.name}")
                        db.session.delete(g)
                    
                    # Process adults
                    for i in range(rsvp.adults_count):
                        name_key = f'adult_name_{i}'
                        name = request.form.get(name_key, '').strip()
                        if name:
                            logger.debug(f"Adding adult: {name}")
                            guest_obj = AdditionalGuest(
                                rsvp_id=rsvp.id,
                                name=name,
                                is_child=False
                            )
                            db.session.add(guest_obj)
                        else:
                            logger.warning(f"Missing name for adult #{i}")
                    
                    # Process children
                    for i in range(rsvp.children_count):
                        name_key = f'child_name_{i}'
                        name = request.form.get(name_key, '').strip()
                        if name:
                            logger.debug(f"Adding child: {name}")
                            guest_obj = AdditionalGuest(
                                rsvp_id=rsvp.id,
                                name=name,
                                is_child=True
                            )
                            db.session.add(guest_obj)
                        else:
                            logger.warning(f"Missing name for child #{i}")
            else:
                logger.info("Not attending, setting default values")
                # Reset values for non-attending guests
                rsvp.hotel_name = None
                rsvp.transport_to_church = False
                rsvp.transport_to_reception = False
                rsvp.transport_to_hotel = False
                rsvp.adults_count = 0
                rsvp.children_count = 0
                
                # Clear any existing additional guests
                AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).delete()
            
            # Update last_updated timestamp
            rsvp.last_updated = datetime.now()
            
            # Flush to detect errors early
            logger.debug("Flushing session to detect errors")
            db.session.flush()
            
            # Then commit
            logger.info("Committing changes to database")
            db.session.commit()
            
            status = "attendance" if rsvp.is_attending else "decline"
            logger.info(f"RSVP {status} submitted successfully for: {guest.name}")
            flash('Your RSVP has been submitted successfully!', 'success')
            return redirect(url_for('rsvp.confirmation'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing RSVP: {str(e)}", exc_info=True)
            flash(f'Error submitting RSVP: {str(e)}', 'danger')
    
    # GET request - display the form or reload with validation errors
    return render_template('rsvp.html',
                         guest=guest,
                         rsvp=rsvp,
                         form=form,
                         allergens=allergens,
                         admin_phone=admin_phone,
                         show_warning=show_warning)

@bp.route('/<token>/cancel', methods=['GET', 'POST'])
def cancel_rsvp(token):
    guest = Guest.query.filter_by(token=token).first_or_404()
    rsvp = RSVP.query.filter_by(guest_id=guest.id).first_or_404()
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    
    # Check if cancellation is allowed
    if not rsvp.is_editable:
        show_warning = display_warning('Cancellations are not possible at this time.', admin_phone)
        return redirect(url_for('rsvp.rsvp_form', token=token))
    
    # Cancellation form
    form = RSVPCancellationForm()
    
    if form.validate_on_submit():
        if rsvp.cancel():
            try:
                db.session.commit()
                # Send immediate notification to admin
                send_cancellation_notification(guest, rsvp)
                logger.info(f"RSVP cancelled for: {guest.name}")
                flash('Your RSVP has been cancelled successfully.', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error cancelling RSVP: {str(e)}")
                flash('There was an error cancelling your RSVP. Please try again.', 'error')
        
        return redirect(url_for('rsvp.rsvp_form', token=token))
    
    # GET request - show confirmation form
    return render_template('rsvp_cancel.html', 
                        guest=guest,
                        rsvp=rsvp,
                        form=form,
                        admin_phone=admin_phone)

@bp.route('/confirmation')
def confirmation():
    return render_template('rsvp_confirmation.html')