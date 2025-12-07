from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_babel import Babel
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
import sys

db = SQLAlchemy()
mail = Mail()
babel = Babel()
migrate = Migrate()
csrf = CSRFProtect()

def get_locale():
    return request.accept_languages.best_match(['es', 'en'], default='es')

def create_app(config_class=None):
    """Create and configure the Flask application."""
    print("Creating Flask app...")
    
    # Create Flask instance
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        # Get configuration based on environment
        from app.config import get_config
        config_class = get_config()
    
    # Apply configuration
    try:
        if isinstance(config_class, type):
            # It's a class, instantiate it
            app.config.from_object(config_class())
        else:
            # It's already an instance
            app.config.from_object(config_class)
    except SystemExit:
        # Configuration validation failed
        print("❌ Configuration validation failed. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading configuration: {str(e)}")
        sys.exit(1)
    
    # Configure CORS
    CORS(app, 
         resources={
            r"/*": {
                "origins": [
                    "http://localhost:5000",
                    "http://localhost:5001", 
                    "http://127.0.0.1:5000",
                    "http://127.0.0.1:5001"
                ],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })
    
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
    print("Registering blueprints...")
    from app.routes import main_bp, rsvp_bp, admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(rsvp_bp)
    app.register_blueprint(admin_bp)
    print("Blueprints registered!")
    
    # Log configuration status (without exposing sensitive data)
    with app.app_context():
        app.logger.info("=" * 50)
        app.logger.info("Application Configuration Status:")
        app.logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
        app.logger.info(f"Database: {'✅ Configured' if app.config.get('SQLALCHEMY_DATABASE_URI') else '❌ Not configured'}")
        app.logger.info(f"Admin: {'✅ Configured' if app.config.get('ADMIN_PASSWORD') else '❌ Not configured'}")
        app.logger.info(f"Email: {'✅ Configured' if app.config.get('MAIL_USERNAME') else '⚠️  Not configured'}")
        app.logger.info(f"Wedding Date: {app.config.get('WEDDING_DATE')}")
        app.logger.info(f"RSVP Deadline: {app.config.get('RSVP_DEADLINE')}")
        app.logger.info("=" * 50)
    
    print("✅ Flask app created successfully!")
    
    # Show available routes in debug mode
    if app.debug:
        print("\nAvailable routes:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.endpoint}: {rule.rule}")
    
    return app