"""Flask application factory module.

This module contains the application factory and extension initialization.
"""
from typing import Optional

from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_babel import Babel
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from .config import Config

# Initialize extensions
db = SQLAlchemy()
mail = Mail()
babel = Babel()
migrate = Migrate()
csrf = CSRFProtect()


def get_locale() -> str:
    """Get the best matching locale based on the request's accept languages.
    
    Returns:
        str: The best matching locale code ('en' or 'es').
    """
    return request.accept_languages.best_match(['en', 'es'])


def create_app(config_class: Optional[Config] = None) -> Flask:
    """Create and configure the Flask application.
    
    Args:
        config_class: The configuration class to use. Defaults to Config.
        
    Returns:
        Flask: The configured Flask application.
    """
    if config_class is None:
        config_class = Config
        
    app = Flask(__name__)
    
    # Configure CORS
    CORS(
        app,
        resources={
            r"/*": {
                "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        }
    )
    
    # Load configuration
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Configure logging
    from app.logging_config import configure_logging
    configure_logging(app)
    
    # Configure security
    from app.security import configure_security
    configure_security(app)
    
    # Register error handlers
    from app.error_handlers import register_error_handlers
    register_error_handlers(app)

    # Register blueprints
    from app.routes import main_bp, auth_bp, rsvp_bp, admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(rsvp_bp)
    app.register_blueprint(admin_bp)

    return app