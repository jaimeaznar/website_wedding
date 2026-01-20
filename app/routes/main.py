# app/routes/main.py
from flask import Blueprint, render_template, request, session
from app import db
from app.services.guest_service import GuestService
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Render the homepage."""
    logger.debug("Index route accessed")
    
    guest = None
    
    # Check for token in URL query param
    token = request.args.get('token')
    if token:
        guest = GuestService.get_guest_by_token(token)
        if guest:
            session['guest_token'] = token
            logger.info(f"Guest token stored in session: {guest.name}")
    
    # Fallback to session token if no URL param
    if not guest:
        token = session.get('guest_token')
        if token:
            guest = GuestService.get_guest_by_token(token)
            if guest:
                logger.debug(f"Guest retrieved from session: {guest.name}")
            else:
                # Invalid token in session, clear it
                session.pop('guest_token', None)
    
    try:
        logger.debug("Attempting to render home.html")
        return render_template('home.html', guest=guest)
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        raise

@bp.route('/health')
def health():
    """Health check endpoint for Railway/load balancers."""
    try:
        # Quick database connectivity check
        db.session.execute(db.text('SELECT 1'))
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {'status': 'unhealthy', 'error': str(e)}, 503


@bp.route('/seed-allergens')
def seed_allergens():
    """One-time endpoint to seed allergens."""
    from app.models.allergen import Allergen
    
    if Allergen.query.count() > 0:
        return {'status': 'already seeded', 'count': Allergen.query.count()}
    
    common_allergens = [
        'Gluten', 'Dairy', 'Nuts (Tree nuts)', 'Peanuts',
        'Soy', 'Eggs', 'Fish', 'Shellfish',
        'Celery', 'Mustard', 'Sesame', 'Sulphites',
        'Lupins', 'Molluscs', 'Vegetarian', 'Vegan',
        'Kosher', 'Halal'
    ]
    
    for name in common_allergens:
        db.session.add(Allergen(name=name))
    
    db.session.commit()
    return {'status': 'seeded', 'count': len(common_allergens)}


@bp.route('/clear-and-sync')
def clear_and_sync():
    """Clear local DB and resync from Airtable."""
    from app.models.guest import Guest
    from app.models.rsvp import RSVP
    from app.models.allergen import GuestAllergen
    from app.services.airtable_service import get_airtable_service
    
    # Delete all RSVPs and guests
    GuestAllergen.query.delete()
    RSVP.query.delete()
    Guest.query.delete()
    db.session.commit()
    
    # Sync from Airtable
    airtable = get_airtable_service()
    created, updated = airtable.sync_all_to_local_db()
    
    return {'status': 'cleared and synced', 'created': created, 'updated': updated}