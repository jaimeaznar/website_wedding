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