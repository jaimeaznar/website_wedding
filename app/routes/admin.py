# app/routes/admin.py - REFACTORED VERSION
from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, current_app
from app.services.admin_service import AdminService
from app.services.guest_service import GuestService
from app.services.rsvp_service import RSVPService
from app.forms import LoginForm, GuestForm, ImportForm
from app.security import rate_limit
from functools import wraps
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.cookies.get('admin_authenticated'):
            logger.warning(f"Unauthorized admin access attempt: {request.remote_addr}")
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window=300)  # 5 attempts per 5 minutes
def login():
    """Handle admin login."""
    form = LoginForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        password = form.password.data
        
        # Use service to verify password
        if AdminService.verify_admin_password(password):
            response = redirect(url_for('admin.dashboard'))
            response.set_cookie(
                'admin_authenticated', 
                'true', 
                httponly=True, 
                secure=not current_app.debug,
                max_age=1800  # 30 minutes
            )
            logger.info(f"Admin login successful: {request.remote_addr}")
            return response
        else:
            logger.warning(f"Failed admin login attempt: {request.remote_addr}")
            flash('Invalid password', 'error')
    
    return render_template('admin/login.html', form=form)


@bp.route('/dashboard')
@admin_required
def dashboard():
    """Display admin dashboard with statistics."""
    # Use service to get all dashboard data
    dashboard_data = AdminService.get_dashboard_data()
    
    return render_template('admin/dashboard.html', **dashboard_data)


@bp.route('/guest/add', methods=['GET', 'POST'])
@admin_required
def add_guest():
    """Add a new guest."""
    form = GuestForm()
    
    if form.validate_on_submit():
        try:
            # Use service to create guest
            guest = GuestService.create_guest(
                name=form.name.data,
                phone=form.phone.data,
                email=form.email.data,
                has_plus_one=form.has_plus_one.data,
                is_family=form.is_family.data,
                language_preference=form.language_preference.data
            )
            
            flash('Guest added successfully', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            logger.error(f"Error adding guest: {str(e)}")
            flash(f'Error adding guest: {str(e)}', 'error')
    
    return render_template('admin/guest_form.html', form=form)


@bp.route('/guest/import', methods=['POST'])
@admin_required
def import_guests():
    """Import guests from CSV file."""
    form = ImportForm()
    
    if form.validate_on_submit():
        try:
            # Use service to import guests
            file_content = form.file.data.read()
            guests = GuestService.import_guests_from_csv(file_content)
            
            flash(f'Successfully imported {len(guests)} guests', 'success')
            
        except Exception as e:
            logger.error(f"Error importing guests: {str(e)}")
            flash(f'Error importing guests: {str(e)}', 'error')
    else:
        # Flash form errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'error')
    
    return redirect(url_for('admin.dashboard'))


@bp.route('/download-template')
@admin_required
def download_template():
    """Download CSV template for guest import."""
    template_content = AdminService.generate_csv_template()
    
    return Response(
        template_content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=guest_template.csv'}
    )


@bp.route('/logout')
def logout():
    """Log out admin user."""
    logger.info(f"Admin logout: {request.remote_addr}")
    response = redirect(url_for('admin.login'))
    response.delete_cookie('admin_authenticated')
    return response


# Additional admin routes for reports (future implementation)

@bp.route('/reports/dietary')
@admin_required
def dietary_report():
    """Generate dietary restrictions report."""
    report_data = AdminService.get_dietary_report()
    return render_template('admin/dietary_report.html', **report_data)


@bp.route('/reports/transport')
@admin_required
def transport_report():
    """Generate transport requirements report."""
    report_data = AdminService.get_transport_report()
    return render_template('admin/transport_report.html', **report_data)


@bp.route('/reports/export')
@admin_required
def export_report():
    """Export comprehensive RSVP report."""
    # This will be implemented in the export phase
    flash('Export functionality coming soon!', 'info')
    return redirect(url_for('admin.dashboard'))


# Debug route - can be removed in production
@bp.route('/debug/allergens')
@admin_required
def debug_allergens():
    """Debug route to check allergens in the database."""
    from flask import jsonify
    from app.services.allergen_service import AllergenService
    
    rsvps = RSVPService.get_all_rsvps()
    result = []
    
    for rsvp in rsvps:
        allergens = AllergenService.get_allergens_for_rsvp(rsvp.id)
        
        rsvp_info = {
            'rsvp_id': rsvp.id,
            'guest_name': rsvp.guest.name if rsvp.guest else 'Unknown',
            'is_attending': rsvp.is_attending,
            'is_cancelled': rsvp.is_cancelled,
            'allergens': allergens
        }
        
        result.append(rsvp_info)
    
    return jsonify(result)