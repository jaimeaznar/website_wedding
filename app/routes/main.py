# app/routes/main.py
from flask import Blueprint, render_template
from app import db
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    logger.debug("Index route accessed")
    try:
        logger.debug("Attempting to render home.html")
        return render_template('home.html')
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