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
    guest = Guest.query.filter_by(token=token).first_or_404()
    allergens = Allergen.query.all()
    rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    show_warning = False
    
    # Check editability
    if rsvp and not rsvp.is_editable:
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
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Create or get existing RSVP
            if not rsvp:
                rsvp = RSVP(guest_id=guest.id)
                db.session.add(rsvp)
            
            # Basic info
            rsvp.is_attending = (form.is_attending.data == 'yes')
            
            if rsvp.is_attending:
                # Process attendance details
                rsvp.hotel_name = form.hotel_name.data
                rsvp.transport_to_church = form.transport_to_church.data
                rsvp.transport_to_reception = form.transport_to_reception.data
                rsvp.transport_to_hotel = form.transport_to_hotel.data
                
                # Process allergens for main guest
                GuestAllergen.query.filter_by(rsvp_id=rsvp.id, guest_name=guest.name).delete()
                
                # Main guest allergens - custom handling since we're not using nested forms
                for allergen_id in request.form.getlist('allergens_main'):
                    try:
                        allergen_id = int(allergen_id)
                        guest_allergen = GuestAllergen(
                            rsvp_id=rsvp.id,
                            guest_name=guest.name,
                            allergen_id=allergen_id
                        )
                        db.session.add(guest_allergen)
                    except ValueError:
                        pass
                
                custom_allergen = request.form.get('custom_allergen_main', '').strip()
                if custom_allergen:
                    guest_allergen = GuestAllergen(
                        rsvp_id=rsvp.id,
                        guest_name=guest.name,
                        custom_allergen=custom_allergen
                    )
                    db.session.add(guest_allergen)
                
                # Process additional guests if guest is family
                if guest.is_family:
                    # Update counts
                    rsvp.adults_count = form.adults_count.data
                    rsvp.children_count = form.children_count.data
                    
                    # Clear existing additional guests
                    AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).delete()
                    
                    # Process adults
                    for i in range(rsvp.adults_count):
                        name = request.form.get(f'adult_name_{i}', '').strip()
                        if name:
                            guest = AdditionalGuest(
                                rsvp_id=rsvp.id,
                                name=name,
                                is_child=False
                            )
                            db.session.add(guest)
                            
                            # Process allergens for this guest
                            for allergen_id in request.form.getlist(f'allergens_adult_{i}'):
                                try:
                                    allergen_id = int(allergen_id)
                                    guest_allergen = GuestAllergen(
                                        rsvp_id=rsvp.id,
                                        guest_name=name,
                                        allergen_id=allergen_id
                                    )
                                    db.session.add(guest_allergen)
                                except ValueError:
                                    pass
                            
                            custom_allergen = request.form.get(f'custom_allergen_adult_{i}', '').strip()
                            if custom_allergen:
                                guest_allergen = GuestAllergen(
                                    rsvp_id=rsvp.id,
                                    guest_name=name,
                                    custom_allergen=custom_allergen
                                )
                                db.session.add(guest_allergen)
                    
                    # Process children
                    for i in range(rsvp.children_count):
                        name = request.form.get(f'child_name_{i}', '').strip()
                        if name:
                            guest = AdditionalGuest(
                                rsvp_id=rsvp.id,
                                name=name,
                                is_child=True
                            )
                            db.session.add(guest)
                            
                            # Process allergens for this child
                            for allergen_id in request.form.getlist(f'allergens_child_{i}'):
                                try:
                                    allergen_id = int(allergen_id)
                                    guest_allergen = GuestAllergen(
                                        rsvp_id=rsvp.id,
                                        guest_name=name,
                                        allergen_id=allergen_id
                                    )
                                    db.session.add(guest_allergen)
                                except ValueError:
                                    pass
                            
                            custom_allergen = request.form.get(f'custom_allergen_child_{i}', '').strip()
                            if custom_allergen:
                                guest_allergen = GuestAllergen(
                                    rsvp_id=rsvp.id,
                                    guest_name=name,
                                    custom_allergen=custom_allergen
                                )
                                db.session.add(guest_allergen)
            
            db.session.commit()
            logger.info(f"RSVP submitted for: {guest.name} - Attending: {rsvp.is_attending}")
            flash('Your RSVP has been submitted successfully!', 'success')
            return redirect(url_for('rsvp.confirmation'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing RSVP: {str(e)}")
            flash(f'Error submitting RSVP: {str(e)}', 'danger')
    
    elif form.errors:
        # Form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'danger')
    
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