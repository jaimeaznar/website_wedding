# app/routes/rsvp.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.models.allergen import Allergen
from app.utils.email import send_cancellation_notification
from app.utils.rsvp_processor import RSVPFormProcessor
from datetime import datetime

bp = Blueprint('rsvp', __name__, url_prefix='/rsvp')

def display_warning(message, admin_phone):
    flash(f'{message} Please contact {admin_phone} for assistance.', 'warning')
    return True

@bp.route('/')
def landing():
    return render_template('rsvp_landing.html')

@bp.route('/<token>', methods=['GET', 'POST'])
def rsvp_form(token):
    guest = Guest.query.filter_by(token=token).first_or_404()
    allergens = Allergen.query.all()
    rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    show_warning = False
    
    if request.method == 'POST':
        if not request.form:
            flash('No form data received.', 'danger')
            return render_template('rsvp.html',
                                guest=guest,
                                rsvp=rsvp,
                                allergens=allergens,
                                admin_phone=admin_phone,
                                show_warning=show_warning)
        
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

        # Process the form with validation
        processor = RSVPFormProcessor(request.form, guest)
        success, message = processor.process()
        
        if success:
            flash(message, 'success')
            return redirect(url_for('rsvp.confirmation'))
        else:
            # Split validation errors to display them better
            errors = message.split('\n')
            for error in errors:
                flash(error, 'danger')
            
            # Return to form with current data
            return render_template('rsvp.html', 
                                guest=guest, 
                                rsvp=rsvp, 
                                allergens=allergens,
                                admin_phone=admin_phone,
                                form_data=request.form,
                                show_warning=show_warning)
    
    # GET request - display the form
    return render_template('rsvp.html',
                         guest=guest,
                         rsvp=rsvp,
                         allergens=allergens,
                         admin_phone=admin_phone,
                         show_warning=show_warning)

@bp.route('/<token>/cancel', methods=['POST'])
def cancel_rsvp(token):
    guest = Guest.query.filter_by(token=token).first_or_404()
    rsvp = RSVP.query.filter_by(guest_id=guest.id).first_or_404()
    admin_phone = current_app.config.get('ADMIN_PHONE', '123456789')
    
    if not rsvp.is_editable:
        show_warning = display_warning('Cancellations are not possible at this time.', admin_phone)
        return redirect(url_for('rsvp.rsvp_form', token=token))
    
    if rsvp.cancel():
        try:
            db.session.commit()
            # Send immediate notification to admin
            send_cancellation_notification(guest, rsvp)
            flash('Your RSVP has been cancelled successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('There was an error cancelling your RSVP. Please try again.', 'error')
    
    return redirect(url_for('rsvp.rsvp_form', token=token))

@bp.route('/confirmation')
def confirmation():
    return render_template('rsvp_confirmation.html')
