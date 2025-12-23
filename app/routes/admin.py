# app/routes/admin.py - REFACTORED VERSION
from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, current_app
from app.services.admin_service import AdminService
from app.services.guest_service import GuestService
from app.services.rsvp_service import RSVPService
from app.forms import LoginForm, GuestForm, ImportForm
from app.security import rate_limit
from app.constants import (
    LogMessage, ErrorMessage, FlashCategory, TimeLimit, Template, Security
)
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.cookies.get(Security.ADMIN_COOKIE_NAME):
            logger.warning(LogMessage.ADMIN_UNAUTHORIZED.format(ip=request.remote_addr))
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=TimeLimit.ADMIN_RATE_LIMIT_MAX_REQUESTS, window=TimeLimit.RATE_LIMIT_WINDOW)
def login():
    """Handle admin login."""
    form = LoginForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        password = form.password.data
        
        # Use service to verify password
        if AdminService.verify_admin_password(password):
            response = redirect(url_for('admin.dashboard'))
            response.set_cookie(
                Security.ADMIN_COOKIE_NAME,
                'true',
                httponly=Security.COOKIE_HTTPONLY,
                secure=Security.COOKIE_SECURE if not current_app.debug else False,
                max_age=TimeLimit.ADMIN_SESSION_TIMEOUT
            )
            logger.info(LogMessage.ADMIN_LOGIN_SUCCESS.format(ip=request.remote_addr))
            return response
        else:
            logger.warning(LogMessage.ADMIN_LOGIN_FAILED.format(ip=request.remote_addr))
            flash(ErrorMessage.INVALID_PASSWORD, FlashCategory.ERROR)
    
    return render_template(Template.ADMIN_LOGIN, form=form)


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

# ============= PDF EXPORT ROUTES =============

# ADD THESE ROUTES TO: app/routes/admin.py
# Insert after the existing routes, before the end of the file

# ============= PDF EXPORT ROUTES =============

@bp.route('/reports/dietary/pdf')
@admin_required
def download_dietary_pdf():
    """Download dietary restrictions report as PDF."""
    try:
        from app.services.pdf_service import PDFService
        from flask import send_file
        import io
        
        logger.info("Admin requested dietary PDF download")
        
        # Generate PDF
        pdf_data = PDFService.generate_dietary_pdf()
        
        # Create a file-like object
        pdf_buffer = io.BytesIO(pdf_data)
        pdf_buffer.seek(0)
        
        # Generate filename with date
        filename = f"dietary_restrictions_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Send file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating dietary PDF: {str(e)}", exc_info=True)
        flash(f"Error generating PDF: {str(e)}", 'error')
        return redirect(url_for('admin.dietary_report'))


@bp.route('/reports/transport/pdf')
@admin_required
def download_transport_pdf():
    """Download transport requirements report as PDF."""
    try:
        from app.services.pdf_service import PDFService
        from flask import send_file
        import io
        
        logger.info("Admin requested transport PDF download")
        
        # Generate PDF
        pdf_data = PDFService.generate_transport_pdf()
        
        # Create a file-like object
        pdf_buffer = io.BytesIO(pdf_data)
        pdf_buffer.seek(0)
        
        # Generate filename with date
        filename = f"transport_plan_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Send file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating transport PDF: {str(e)}", exc_info=True)
        flash(f"Error generating PDF: {str(e)}", 'error')
        return redirect(url_for('admin.transport_report'))


@bp.route('/reports/export-all')
@admin_required
def export_all_reports():
    """Generate and download all reports as a ZIP file."""
    try:
        from app.services.pdf_service import PDFService
        from flask import send_file
        import io
        import zipfile
        
        logger.info("Admin requested full report export")
        
        # Create ZIP buffer
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add dietary PDF
            dietary_pdf = PDFService.generate_dietary_pdf()
            zip_file.writestr(
                f"dietary_restrictions_{datetime.now().strftime('%Y%m%d')}.pdf",
                dietary_pdf
            )
            
            # Add transport PDF
            transport_pdf = PDFService.generate_transport_pdf()
            zip_file.writestr(
                f"transport_plan_{datetime.now().strftime('%Y%m%d')}.pdf",
                transport_pdf
            )
            
            # Add CSV export of all guests
            csv_data = _generate_guest_csv()
            zip_file.writestr(
                f"guest_list_{datetime.now().strftime('%Y%m%d')}.csv",
                csv_data
            )
        
        # Prepare for download
        zip_buffer.seek(0)
        
        filename = f"wedding_reports_{datetime.now().strftime('%Y%m%d')}.zip"
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating report export: {str(e)}", exc_info=True)
        flash(f"Error generating reports: {str(e)}", 'error')
        return redirect(url_for('admin.dashboard'))


def _generate_guest_csv():
    """
    Helper function to generate CSV export of all guests and RSVPs.
    
    Returns:
        CSV data as string
    """
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Guest Name',
        'Phone',
        'Language',
        'Has Plus One',
        'Is Family',
        'RSVP Status',
        'Attending',
        'Additional Guests',
        'Total People',
        'Hotel',
        'Transport to Church',
        'Transport to Reception',
        'Transport to Hotel',
        'Dietary Restrictions',
        'Last Updated'
    ])
    
    # Get all RSVPs with detailed info
    from app.services.admin_service import AdminService
    report = AdminService.get_detailed_rsvp_report()
    
    for rsvp_data in report:
        # Format allergens
        allergens_str = ''
        if rsvp_data['allergens']:
            allergen_list = []
            for guest_name, restrictions in rsvp_data['allergens'].items():
                # Convert restriction items to strings
                restriction_strs = []
                for r in restrictions:
                    if isinstance(r, dict):
                        # Handle dict format (allergen object)
                        restriction_strs.append(r.get('name', str(r)))
                    else:
                        restriction_strs.append(str(r))
                allergen_list.append(f"{guest_name}: {', '.join(restriction_strs)}")
            allergens_str = '; '.join(allergen_list)
        
        # Format additional guests
        additional_str = ''
        if rsvp_data['additional_guests']:
            additional_list = [
                f"{ag['name']} ({'Child' if ag['is_child'] else 'Adult'})"
                for ag in rsvp_data['additional_guests']
            ]
            additional_str = ', '.join(additional_list)
        
        writer.writerow([
            rsvp_data['guest_name'],
            rsvp_data['guest_phone'],
            rsvp_data['language'],
            'Yes' if rsvp_data['has_plus_one'] else 'No',
            'Yes' if rsvp_data['is_family'] else 'No',
            rsvp_data['status'],
            'Yes' if rsvp_data['status'] == 'Attending' else 'No',
            additional_str,
            rsvp_data['total_guests'],
            rsvp_data['hotel'] or '',
            'Yes' if rsvp_data['transport_church'] else 'No',
            'Yes' if rsvp_data['transport_reception'] else 'No',
            'Yes' if rsvp_data['transport_hotel'] else 'No',
            allergens_str,
            rsvp_data['last_updated']
        ])
    
    return output.getvalue()