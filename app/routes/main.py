# app/routes/main.py
from flask import Blueprint, render_template, request, g
from app import db
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('main', __name__)

@bp.before_request
def before_request():
    g.lang_code = request.args.get('lang', 'en')

@bp.route('/')
def index():
    logger.debug("Index route accessed")
    try:
        logger.debug("Attempting to render home.html")
        return render_template('home.html')
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        raise

@bp.route('/schedule')
def schedule():
    return render_template('schedule.html')

@bp.route('/venue')
def venue():
    return render_template('venue.html')

@bp.route('/accommodation')
def accommodation():
    return render_template('accommodation.html')

@bp.route('/activities')
def activities():
    return render_template('activities.html')

@bp.route('/gallery')
def gallery():
    return render_template('gallery.html')