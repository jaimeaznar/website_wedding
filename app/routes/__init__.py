# app/routes/__init__.py
from app.routes.main import bp as main_bp
from app.routes.rsvp import bp as rsvp_bp
from app.routes.admin import bp as admin_bp

# These will be imported by the app factory
