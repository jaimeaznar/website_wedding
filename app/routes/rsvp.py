# app/routes/rsvp.py - FIXED VERSION
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP, AdditionalGuest
from app.models.allergen import Allergen, GuestAllergen
from app.utils.email import send_cancellation_notification
from app.forms import RSVPForm, RSVPCancellationForm
from app.security import rate_limit
from datetime import datetime, date
import logging

# Set up logger
logger = logging.getLogger(__name__)

bp = Blueprint('rsvp', __name__, url_prefix='/rsvp')

def display_warning(message, admin_phone):
    flash(f'{message} Please contact {admin_phone} for assistance.', 'warning')
    return True

def process_guest_allergens(rsvp_id, guest_name, form, prefix):
    """Process allergens for a specific guest - FIXED VERSION."""
    # Check if rsvp_id is None
    if rsvp_id is None:
        logger.warning(f"Cannot process allergens: rsvp_id is None for {guest_name}")
        return
        
    logger.debug(f"Processing allergens for guest: {guest_name}, prefix: {prefix}, rsvp_id: {rsvp_id}")
    
    # First, delete any existing allergens for this guest
    existing_count = GuestAllergen.query.filter_by(rsvp_id=rsvp_id, guest_name=guest_name).count()
    logger.debug(f"Deleting {existing_count} existing allergens for {guest_name}")
    GuestAllergen.query.filter_by(rsvp_id=rsvp_id, guest_name=guest_name).delete()
    
    # Process standard allergens
    allergen_field_name = f'allergens_{prefix}'
    allergen_ids = form.getlist(allergen_field_name)
    logger.debug(f"Found allergen IDs for {allergen_field_name}: {allergen_ids}")
    
    allergens_added = 0
    for allergen_id in allergen_ids:
        try:
            allergen_id = int(allergen_id)
            # Verify the allergen exists
            allergen = Allergen.query.get(allergen_id)
            if allergen:
                guest_allergen = GuestAllergen(
                    rsvp_id=rsvp_id,
                    guest_name=guest_name,
                    allergen_id=allergen_id
                )
                db.session.add(guest_allergen)
                allergens_added += 1
                logger.debug(f"Added allergen {allergen.name} for {guest_name}")
            else:
                logger.warning(f"Allergen with ID {allergen_id} not found")
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid allergen ID for {guest_name}: {allergen_id}, {e}")
    
    # Process custom allergen
    custom_field_name = f'custom_allergen_{prefix}'
    custom_allergen = form.get(custom_field_name, '').strip()
    logger.debug(f"Custom allergen for {custom_field_name}: '{custom_allergen}'")
    
    if custom_allergen:
        guest_allergen = GuestAllergen(
            rsvp_id=rsvp_id,
            guest_name=guest_name,
            custom_allergen=custom_allergen
        )
        db.session.add(guest_allergen)
        allergens_added += 1
        logger.debug(f"Added custom allergen '{custom_allergen}' for {guest_name}")
    
    logger.info(f"Total allergens added for {guest_name}: {allergens_added}")

def is_rsvp_deadline_passed():
    """Check if the RSVP deadline has passed"""
    rsvp_deadline_str = current_app.config.get('RSVP_DEADLINE')
    if not rsvp_deadline_str:
        return False  # If no deadline is set, assume it hasn't passed
    
    try:
        rsvp_deadline = datetime.strptime(rsvp_deadline_str, '%Y-%m-%d').date()
        today = date.today()
        return today > rsvp_deadline
    except (ValueError, TypeError):
        logger.error(f"Invalid RSVP_DEADLINE format: {rsvp_deadline_str}")
        return False  # If there's an error, default to allowing RSVPs

def get_rsvp_deadline_formatted():
    """Get formatted RSVP deadline for display"""
    rsvp_deadline_str = current_app.config.get('RSVP_DEADLINE')
    if not rsvp_deadline_str:
        return "Not specified"
    
    try:
        rsvp_deadline = datetime.strptime(rsvp_deadline_str, '%Y-%m-%d').date()
        return rsvp_deadline.strftime('%B %d, %Y')  # e.g. "April 15, 2026"
    except (ValueError, TypeError):
        return rsvp_deadline_str  # Return as-is if there's a parsing error

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
    logger.debug(f"Available allergens: {[a.name for a in allergens]}")
    
    rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
    
    if rsvp:
        logger.info(f"Existing RSVP found (attending: {rsvp.is_attending}, cancelled: {rsvp.is_cancelled})")
    else:
        logger.info("No existing RSVP found")
    
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    rsvp_deadline = get_rsvp_deadline_formatted()
    
    # Check if RSVP deadline has passed
    if is_rsvp_deadline_passed():
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
        logger.debug(f"Form data: {dict(request.form)}")
        
        try:
            # Create or get existing RSVP
            if not rsvp:
                logger.info("Creating new RSVP")
                rsvp = RSVP(guest_id=guest.id)
                db.session.add(rsvp)
                # Flush to generate an ID for the new RSVP
                db.session.flush()
                logger.debug(f"New RSVP created with ID: {rsvp.id}")
            else:
                logger.info(f"Updating existing RSVP with ID: {rsvp.id}")
            
            # Basic info - handle both 'yes' and 'no' responses
            is_attending = request.form.get('is_attending') == 'yes'
            logger.info(f"Setting is_attending to: {is_attending}")
            rsvp.is_attending = is_attending
            
            # Make sure rsvp has an ID before processing allergens
            if rsvp.id is None:
                db.session.flush()
                logger.debug(f"RSVP ID after flush: {rsvp.id}")
            
            # Clear existing allergens and additional guests first
            if rsvp.id:
                logger.debug("Clearing existing allergens and additional guests")
                GuestAllergen.query.filter_by(rsvp_id=rsvp.id).delete()
                AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).delete()
            
            # Process allergens and additional info only if attending
            if is_attending:
                logger.info("Processing attendance details")
                
                # Basic attendance details
                rsvp.hotel_name = request.form.get('hotel_name', '').strip() or None
                rsvp.transport_to_church = 'transport_to_church' in request.form
                rsvp.transport_to_reception = 'transport_to_reception' in request.form
                rsvp.transport_to_hotel = 'transport_to_hotel' in request.form
                
                logger.debug(f"Hotel: {rsvp.hotel_name}")
                logger.debug(f"Transport - Church: {rsvp.transport_to_church}, Reception: {rsvp.transport_to_reception}, Hotel: {rsvp.transport_to_hotel}")
                
                # Process main guest allergens
                logger.debug("Processing main guest allergens")
                process_guest_allergens(rsvp.id, guest.name, request.form, 'main')
                
                # Process plus one if guest has plus one but is not family
                if guest.has_plus_one and not guest.is_family:
                    logger.info("Processing plus one")
                    plus_one_name = request.form.get('plus_one_name', '').strip()
                    if plus_one_name:
                        logger.debug(f"Plus one name: {plus_one_name}")
                        rsvp.plus_one_name = plus_one_name
                        guest.plus_one_used = True
                        
                        # Create an additional guest entry for the plus one
                        plus_one = AdditionalGuest(
                            rsvp_id=rsvp.id,
                            name=plus_one_name,
                            is_child=False
                        )
                        db.session.add(plus_one)
                        logger.debug(f"Added plus one as additional guest: {plus_one_name}")
                        
                        # Process plus one allergens
                        process_guest_allergens(rsvp.id, plus_one_name, request.form, 'plus_one')
                
                # Process family guests
                if guest.is_family:
                    logger.info("Processing family additional guests")
                    
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
                            
                            # Process allergens for this adult
                            process_guest_allergens(rsvp.id, name, request.form, f'adult_{i}')
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
                            
                            # Process allergens for this child
                            process_guest_allergens(rsvp.id, name, request.form, f'child_{i}')
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
            
            # Update last_updated timestamp
            rsvp.last_updated = datetime.now()
            
            # Flush to detect errors early
            logger.debug("Flushing session to detect errors")
            db.session.flush()
            
            # Verify allergens were added correctly
            if is_attending:
                allergen_count = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).count()
                logger.info(f"Total allergens saved for RSVP {rsvp.id}: {allergen_count}")
                
                # Log detailed allergen info for debugging
                saved_allergens = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).all()
                for sa in saved_allergens:
                    allergen_name = sa.allergen.name if sa.allergen else "Custom"
                    logger.debug(f"Saved allergen for {sa.guest_name}: {allergen_name} / {sa.custom_allergen}")
            
            # Then commit
            logger.info("Committing changes to database")
            db.session.commit()
            
            # Redirect to appropriate confirmation page
            if rsvp.is_attending:
                logger.info(f"RSVP acceptance submitted successfully for: {guest.name}")
                flash('Your RSVP has been submitted successfully!', 'success')
                return redirect(url_for('rsvp.confirmation_accepted'))
            else:
                logger.info(f"RSVP decline submitted successfully for: {guest.name}")
                flash('Your response has been recorded.', 'info')
                return redirect(url_for('rsvp.confirmation_declined'))
            
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
                         show_warning=False)

@bp.route('/<token>/cancel', methods=['GET', 'POST'])
def cancel_rsvp(token):
    try:
        guest = Guest.query.filter_by(token=token).first_or_404()
        rsvp = RSVP.query.filter_by(guest_id=guest.id).first_or_404()
        admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
        
        # For debugging purposes
        logger.info(f"Cancel RSVP for guest: {guest.name}, RSVP ID: {rsvp.id}")
        logger.info(f"Current RSVP state - attending: {rsvp.is_attending}, cancelled: {rsvp.is_cancelled}")
        
        # Check if RSVP deadline has passed
        if is_rsvp_deadline_passed():
            logger.info("RSVP deadline has passed - cannot cancel")
            flash('The RSVP deadline has passed. Please contact the wedding administrators for assistance.', 'warning')
            return redirect(url_for('rsvp.rsvp_form', token=token))
        
        # Check if cancellation is allowed
        if not rsvp.is_editable:
            logger.warning(f"RSVP not editable for {guest.name}")
            flash('Cancellations are not possible at this time. Please contact the wedding administrators for assistance.', 'warning')
            return redirect(url_for('rsvp.rsvp_form', token=token))
        
        # Initialize a simpler form without validation to avoid potential issues
        if request.method == 'POST':
            logger.info("Processing cancellation POST request")
            
            # Simple direct cancellation without using the form validation
            rsvp.is_cancelled = True
            rsvp.is_attending = False
            rsvp.cancellation_date = datetime.now()
            
            # Not all models have cancelled_at, so check first
            if hasattr(rsvp, 'cancelled_at'):
                rsvp.cancelled_at = rsvp.cancellation_date
            
            logger.info(f"Updated RSVP state before commit: is_cancelled={rsvp.is_cancelled}, is_attending={rsvp.is_attending}")
            
            try:
                db.session.commit()
                logger.info("Successfully committed cancellation")
                flash('Your RSVP has been cancelled.', 'info')
                return redirect(url_for('rsvp.confirmation_cancelled'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error committing cancellation: {str(e)}", exc_info=True)
                flash(f'Error cancelling RSVP: {str(e)}', 'danger')
                return redirect(url_for('rsvp.rsvp_form', token=token))
        
        # GET request - show a simpler cancellation page
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
    return render_template('rsvp_accepted.html')

@bp.route('/confirmation/declined')
def confirmation_declined():
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    return render_template('rsvp_declined.html', admin_phone=admin_phone)

@bp.route('/confirmation/cancelled')
def confirmation_cancelled():
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    return render_template('rsvp_cancelled.html', admin_phone=admin_phone)

@bp.route('/confirmation')
def confirmation():
    # Kept for backward compatibility, now redirects to accepted confirmation
    return redirect(url_for('rsvp.confirmation_accepted'))