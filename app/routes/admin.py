# app/routes/admin.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, current_app, session
from werkzeug.security import check_password_hash
from app import db
from app.models.guest import Guest
from app.models.allergen import GuestAllergen, Allergen
from app.models.rsvp import RSVP, AdditionalGuest
from app.forms import LoginForm, GuestForm, ImportForm
from app.security import verify_admin_password, rate_limit
from app.admin_auth import ADMIN_PASSWORD_HASH, get_admin_password_hash
from functools import wraps
import secrets
import logging

# Set up logger
logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.cookies.get('admin_authenticated'):
            logger.warning(f"Unauthorized admin access attempt: {request.remote_addr}")
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        password = form.password.data
        
        # Get admin password hash from config or generate it
        admin_password_hash = get_admin_password_hash()
        
        if check_password_hash(admin_password_hash, password):
            response = redirect(url_for('admin.dashboard'))
            response.set_cookie('admin_authenticated', 'true', httponly=True, secure=not current_app.debug)
            logger.info(f"Admin login successful: {request.remote_addr}")
            return response
        flash('Invalid password', 'error')
    return render_template('admin/login.html', form=form)

@bp.route('/dashboard')
@admin_required
def dashboard():
    guests = Guest.query.all()
    rsvps = RSVP.query.all()
    
    # Make allergen model available to the template
    from app.models.allergen import GuestAllergen, Allergen
    
    # Calculate statistics
    total_guests = len(guests)
    total_people_attending = 0
    transport_stats = {
        'to_church': 0,
        'to_reception': 0,
        'to_hotel': 0,
        'hotels': set()
    }
    responses_received = 0  # This counts both attending and declined RSVPs
    attending_count = 0
    declined_count = 0
    cancelled_count = 0
    
    for rsvp in rsvps:
        if rsvp.is_cancelled:
            cancelled_count += 1
        else:
            # Count as a response received whether attending or not
            responses_received += 1
            
            if rsvp.is_attending:
                attending_count += 1
                # Count main guest
                total_people_attending += 1
                # Count additional guests
                total_people_attending += len(rsvp.additional_guests)
                
                # Count transport needs
                if rsvp.transport_to_church:
                    transport_stats['to_church'] += 1
                if rsvp.transport_to_reception:
                    transport_stats['to_reception'] += 1
                if rsvp.transport_to_hotel:
                    transport_stats['to_hotel'] += 1
                
                # Add hotel to set if specified
                if rsvp.hotel_name:
                    transport_stats['hotels'].add(rsvp.hotel_name)
            else:
                # This is a declined RSVP
                declined_count += 1
    
    pending_count = total_guests - responses_received - cancelled_count
    
    return render_template('admin/dashboard.html',
                         guests=guests,
                         rsvps=rsvps,
                         GuestAllergen=GuestAllergen,  # Make available to template
                         Allergen=Allergen,  # Make available to template
                         total_guests=total_guests,
                         total_attending=total_people_attending,
                         responses_received=responses_received,
                         attending_count=attending_count,
                         declined_count=declined_count,
                         pending_count=pending_count,
                         cancelled_count=cancelled_count,
                         transport_stats=transport_stats)

@bp.route('/guest/add', methods=['GET', 'POST'])
@admin_required
def add_guest():
    form = GuestForm()
    if form.validate_on_submit():
        guest = Guest(
            name=form.name.data,
            phone=form.phone.data,
            email=form.email.data if form.email.data else None,
            token=secrets.token_urlsafe(32),
            has_plus_one=form.has_plus_one.data,
            is_family=form.is_family.data,
            language_preference=form.language_preference.data
        )
        db.session.add(guest)
        
        try:
            db.session.commit()
            logger.info(f"Guest added: {guest.name}")
            flash('Guest added successfully', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding guest: {str(e)}")
            flash(f'Error adding guest: {str(e)}', 'error')
    
    return render_template('admin/guest_form.html', form=form)

@bp.route('/guest/import', methods=['POST'])
@admin_required
def import_guests():
    form = ImportForm()
    if form.validate_on_submit():
        try:
            # Process the CSV file using the import utility function
            from app.utils.import_guests import process_guest_csv
            guests = process_guest_csv(form.file.data.read())
            
            for guest in guests:
                db.session.add(guest)
            
            db.session.commit()
            logger.info(f"Successfully imported {len(guests)} guests")
            flash(f'Successfully imported {len(guests)} guests', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error importing guests: {str(e)}")
            flash(f'Error importing guests: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'error')
    
    return redirect(url_for('admin.dashboard'))

@bp.route('/download-template')
@admin_required
def download_template():
    template_content = 'name,phone,email,has_plus_one,is_family,language\n'
    return Response(
        template_content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=guest_template.csv'}
    )

@bp.route('/logout')
def logout():
    logger.info(f"Admin logout: {request.remote_addr}")
    response = redirect(url_for('admin.login'))
    response.delete_cookie('admin_authenticated')
    return response


# Add this route to app/routes/admin.py for debugging purposes
# You can remove it after fixing the issue

@bp.route('/debug/allergens')
@admin_required
def debug_allergens():
    """Debug route to check allergens in the database"""
    from flask import jsonify
    
    # Get all RSVPs
    rsvps = RSVP.query.all()
    
    result = []
    for rsvp in rsvps:
        guest = Guest.query.get(rsvp.guest_id)
        
        # Get allergens directly from the database
        allergens = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).all()
        
        allergen_data = []
        for allergen in allergens:
            allergen_info = {
                'guest_name': allergen.guest_name,
                'allergen_id': allergen.allergen_id,
                'custom_allergen': allergen.custom_allergen
            }
            
            if allergen.allergen_id:
                allergen_obj = Allergen.query.get(allergen.allergen_id)
                if allergen_obj:
                    allergen_info['allergen_name'] = allergen_obj.name
            
            allergen_data.append(allergen_info)
        
        rsvp_info = {
            'rsvp_id': rsvp.id,
            'guest_name': guest.name if guest else 'Unknown',
            'is_attending': rsvp.is_attending,
            'is_cancelled': rsvp.is_cancelled,
            'allergen_count': len(allergens),
            'allergens': allergen_data
        }
        
        result.append(rsvp_info)
    
    return jsonify(result)