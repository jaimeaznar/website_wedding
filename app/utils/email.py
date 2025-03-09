from flask import render_template, current_app, flash
from flask_mail import Message
from app import mail
import logging

logger = logging.getLogger(__name__)

def send_invitation_email(guest):
    subject = "Wedding Invitation"
    
    if guest.language_preference == 'es':
        template = 'emails/invitation_es.html'
    else:
        template = 'emails/invitation_en.html'
    
    msg = Message(
        subject,
        recipients=[guest.email],
        html=render_template(template, 
                           name=guest.name,
                           token=guest.token)
    )
    mail.send(msg)

def send_cancellation_notification(guest, rsvp):
    """Send immediate notification to admin when a guest cancels their RSVP"""
    subject = "RSVP Cancellation Notice"
    
    body = f"""
    A guest has cancelled their RSVP:

    Guest Name: {guest.name}
    Email: {guest.email}
    Phone: {guest.phone}
    
    Previous RSVP Details:
    - Number of Adults: {rsvp.adults_count}
    - Number of Children: {rsvp.children_count}
    - Hotel: {rsvp.hotel_name or 'Not specified'}
    - Transport Needed: {any([rsvp.transport_to_church, rsvp.transport_to_reception, rsvp.transport_to_hotel])}
    
    Cancellation Time: {rsvp.cancellation_date.strftime('%Y-%m-%d %H:%M')}
    """
    
    try:
        msg = Message(
            subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[current_app.config['ADMIN_EMAIL']],
            body=body
        )
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"Error sending cancellation email: {str(e)}")
        flash('Unable to send notification email. Please try again later.', 'warning')
        return False
