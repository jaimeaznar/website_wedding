# app/routes/admin_qr.py
"""
Admin routes for QR code generation.

Generates QR codes for each guest's personalized RSVP link.
"""

from flask import Blueprint, render_template, request, send_file, redirect, url_for, current_app
from functools import wraps
import qrcode
import qrcode.image.svg
from io import BytesIO
import zipfile
import logging

from app.constants import Security

logger = logging.getLogger(__name__)

bp = Blueprint('admin_qr', __name__, url_prefix='/admin/qr')


def admin_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.cookies.get(Security.ADMIN_COOKIE_NAME):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


def generate_qr_code(url: str, format: str = 'png', size: int = 10) -> BytesIO:
    """
    Generate a QR code image for a URL.
    
    Args:
        url: The URL to encode
        format: 'png' or 'svg'
        size: Box size (pixels per box for PNG)
        
    Returns:
        BytesIO buffer with the image
    """
    if format == 'svg':
        factory = qrcode.image.svg.SvgPathImage
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=2,
            image_factory=factory
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer)
        buffer.seek(0)
        return buffer
    else:
        # PNG format
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer


@bp.route('/')
@admin_required
def qr_dashboard():
    """Display QR code dashboard with all guests."""
    from app.models.guest import Guest
    
    guests = Guest.query.order_by(Guest.name).all()
    
    # Generate RSVP URLs for each guest
    guest_data = []
    for guest in guests:
        rsvp_url = url_for('main.index', token=guest.token, _external=True)
        guest_data.append({
            'id': guest.id,
            'name': guest.name,
            'surname': guest.surname,
            'phone': guest.phone,
            'token': guest.token,
            'rsvp_url': rsvp_url,
        })
    
    return render_template('admin/qr_dashboard.html', guests=guest_data)


@bp.route('/download/<int:guest_id>')
@bp.route('/download/<int:guest_id>/<format>')
@admin_required
def download_qr(guest_id, format='png'):
    """Download QR code for a single guest."""
    from app.models.guest import Guest
    
    guest = Guest.query.get_or_404(guest_id)
    rsvp_url = url_for('main.index', token=guest.token, _external=True)
    
    # Generate QR code
    buffer = generate_qr_code(rsvp_url, format=format)
    
    # Clean filename - include surname
    full_name = f"{guest.name} {guest.surname}" if guest.surname else guest.name
    safe_name = "".join(c for c in full_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')
    
    if format == 'svg':
        return send_file(
            buffer,
            mimetype='image/svg+xml',
            as_attachment=True,
            download_name=f'qr_{safe_name}.svg'
        )
    else:
        return send_file(
            buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'qr_{safe_name}.png'
        )


@bp.route('/preview/<int:guest_id>')
@admin_required
def preview_qr(guest_id):
    """Return QR code image for preview (inline, not download)."""
    from app.models.guest import Guest
    
    guest = Guest.query.get_or_404(guest_id)
    rsvp_url = url_for('main.index', token=guest.token, _external=True)
    
    buffer = generate_qr_code(rsvp_url, format='png', size=8)
    
    return send_file(
        buffer,
        mimetype='image/png',
        as_attachment=False
    )


@bp.route('/download-all')
@bp.route('/download-all/<format>')
@admin_required
def download_all_qr(format='png'):
    """Download all QR codes as a ZIP file."""
    from app.models.guest import Guest
    
    guests = Guest.query.order_by(Guest.name).all()
    
    # Create ZIP file in memory
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for guest in guests:
            rsvp_url = url_for('main.index', token=guest.token, _external=True)
            qr_buffer = generate_qr_code(rsvp_url, format=format)
            
            # Clean filename - include surname
            full_name = f"{guest.name} {guest.surname}" if guest.surname else guest.name
            safe_name = "".join(c for c in full_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            
            
            ext = 'svg' if format == 'svg' else 'png'
            zip_file.writestr(f'{safe_name}.{ext}', qr_buffer.getvalue())
    
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'wedding_qr_codes_{format}.zip'
    )


@bp.route('/printable')
@admin_required
def printable_sheet():
    """Generate a printable page with all QR codes and names."""
    from app.models.guest import Guest
    
    guests = Guest.query.order_by(Guest.name).all()
    
    guest_data = []
    for guest in guests:
        rsvp_url = url_for('main.index', token=guest.token, _external=True)
        guest_data.append({
            'id': guest.id,
            'name': guest.name,
            'rsvp_url': rsvp_url,
        })
    
    return render_template('admin/qr_printable.html', guests=guest_data)