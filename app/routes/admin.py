# app/routes/admin.py - REFACTORED VERSION
from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, current_app
from app.services.admin_service import AdminService
from app.services.guest_service import GuestService
from app.services.rsvp_service import RSVPService
from app.services.reminder_service import ReminderService
from app.forms import LoginForm, GuestForm, ImportForm
from app.security import rate_limit
from app.constants import (
    LogMessage, ErrorMessage, FlashCategory, TimeLimit, Template, Security
)
from app.models.reminder import ReminderType
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

# ============= REMINDER MANAGEMENT ROUTES =============

@bp.route('/reminders')
@admin_required
def reminders():
    """Display reminder management interface."""
    # Get statistics
    statistics = ReminderService.get_reminder_statistics()
    
    # Get pending guests
    pending_guests = AdminService.get_pending_rsvps()
    
    # Calculate reminder schedule
    reminder_schedule = []
    deadline_str = current_app.config.get('RSVP_DEADLINE')
    
    if deadline_str:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        
        for reminder_type in [
            ReminderType.INITIAL,
            ReminderType.FIRST_FOLLOWUP,
            ReminderType.SECOND_FOLLOWUP,
            ReminderType.FINAL
        ]:
            days_before = ReminderType.get_days_before(reminder_type)
            scheduled_date = deadline - timedelta(days=days_before)
            guests = ReminderService.get_guests_needing_reminder(reminder_type)
            
            # Check if already sent today
            from app.models.reminder import ReminderBatch
            sent = ReminderBatch.query.filter_by(
                reminder_type=reminder_type
            ).filter(
                ReminderBatch.started_at >= datetime.combine(scheduled_date, datetime.min.time())
            ).first()
            
            reminder_schedule.append({
                'type': reminder_type,
                'days_before': days_before,
                'scheduled_date': scheduled_date.strftime('%Y-%m-%d'),
                'guests_count': len(guests),
                'sent': sent is not None,
                'sent_date': sent.started_at.strftime('%Y-%m-%d') if sent else None
            })
    
    today = datetime.now().date().strftime('%Y-%m-%d')
    
    return render_template('admin/reminders.html',
                         statistics=statistics,
                         pending_guests=pending_guests,
                         reminder_schedule=reminder_schedule,
                         today=today)


@bp.route('/reminders/send-batch', methods=['POST'])
@admin_required
def send_batch_reminder():
    """Send batch reminders."""
    reminder_type = request.form.get('reminder_type')
    target = request.form.get('target', 'all')
    
    # Get admin email for tracking
    admin_email = current_app.config.get('ADMIN_EMAIL', 'admin')
    
    try:
        # Send reminders
        results = ReminderService.send_batch_reminders(
            reminder_type=reminder_type,
            executed_by=admin_email
        )
        
        flash(f"Sent {results['sent']} reminders, {results['failed']} failed", 
              'success' if results['sent'] > 0 else 'warning')
        
    except Exception as e:
        logger.error(f"Error sending batch reminders: {str(e)}")
        flash(f"Error sending reminders: {str(e)}", 'error')
    
    return redirect(url_for('admin.reminders'))


@bp.route('/reminders/send-individual/<int:guest_id>')
@admin_required
def send_individual_reminder(guest_id):
    """Send reminder to individual guest."""
    from app.models.guest import Guest
    
    guest = Guest.query.get_or_404(guest_id)
    admin_email = current_app.config.get('ADMIN_EMAIL', 'admin')
    
    try:
        success, message = ReminderService.send_reminder(
            guest=guest,
            reminder_type=ReminderType.INITIAL,  # Default to initial
            sent_by=admin_email
        )
        
        if success:
            flash(f"Reminder sent to {guest.name}", 'success')
        else:
            flash(message, 'warning')
            
    except Exception as e:
        logger.error(f"Error sending individual reminder: {str(e)}")
        flash(f"Error sending reminder: {str(e)}", 'error')
    
    return redirect(url_for('admin.reminders'))


@bp.route('/reminders/send-scheduled/<string:reminder_type>')
@admin_required
def send_scheduled_reminder(reminder_type):
    """Send a scheduled reminder type now."""
    admin_email = current_app.config.get('ADMIN_EMAIL', 'admin')
    
    try:
        results = ReminderService.send_batch_reminders(
            reminder_type=reminder_type,
            executed_by=admin_email
        )
        
        flash(f"Sent {results['sent']} {reminder_type} reminders", 'success')
        
    except Exception as e:
        logger.error(f"Error sending scheduled reminders: {str(e)}")
        flash(f"Error sending reminders: {str(e)}", 'error')
    
    return redirect(url_for('admin.reminders'))


@bp.route('/reminders/opt-out/<int:guest_id>')
@admin_required
def opt_out_guest(guest_id):
    """Opt out a guest from reminders."""
    from app.models.guest import Guest
    
    guest = Guest.query.get_or_404(guest_id)
    
    try:
        ReminderService.opt_out_guest(guest_id)
        flash(f"{guest.name} has been opted out of reminders", 'success')
        
    except Exception as e:
        logger.error(f"Error opting out guest: {str(e)}")
        flash(f"Error opting out guest: {str(e)}", 'error')
    
    return redirect(url_for('admin.reminders'))


@bp.route('/reminders/history')
@admin_required
def reminder_history():
    """View detailed reminder history."""
    from app.models.reminder import ReminderHistory
    
    # Get filter parameters
    guest_id = request.args.get('guest_id', type=int)
    reminder_type = request.args.get('type')
    status = request.args.get('status')
    
    # Build query
    query = ReminderHistory.query
    
    if guest_id:
        query = query.filter_by(guest_id=guest_id)
    if reminder_type:
        query = query.filter_by(reminder_type=reminder_type)
    if status:
        query = query.filter_by(status=status)
    
    # Order by most recent first
    history = query.order_by(ReminderHistory.created_at.desc()).limit(100).all()
    
    return render_template('admin/reminder_history.html', history=history)


@bp.route('/reminders/test')
@admin_required
def test_reminder():
    """Test reminder email by sending to admin."""
    admin_email = current_app.config.get('ADMIN_EMAIL')
    
    if not admin_email:
        flash('Admin email not configured', 'error')
        return redirect(url_for('admin.reminders'))
    
    # Create a test guest object
    from app.models.guest import Guest
    test_guest = Guest(
        name='Admin (Test)',
        email=admin_email,
        token='test-token',
        language_preference='en'
    )
    
    try:
        from flask_mail import Message
        from app import mail
        from datetime import datetime
        
        msg = Message(
            subject='Test Reminder Email',
            recipients=[admin_email],
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        # Use the initial reminder template as a test
        deadline_str = current_app.config.get('RSVP_DEADLINE', '2026-05-06')
        deadline_formatted = datetime.strptime(deadline_str, '%Y-%m-%d').strftime('%B %d, %Y')
        
        html_body = render_template(
            'emails/reminder_initial_en.html',
            guest=test_guest,
            rsvp_deadline=deadline_formatted,
            config=current_app.config
        )
        
        msg.html = html_body
        mail.send(msg)
        
        flash('Test email sent successfully to admin email', 'success')
        
    except Exception as e:
        logger.error(f"Error sending test reminder: {str(e)}")
        flash(f"Error sending test email: {str(e)}", 'error')
    
    return redirect(url_for('admin.reminders'))


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
        'Email',
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
            rsvp_data['guest_email'],
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