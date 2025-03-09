from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_babel import Babel
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
mail = Mail()
babel = Babel()
migrate = Migrate()

def get_locale():
    return request.accept_languages.best_match(['en', 'es'])

def create_app(config_class=Config):
    print("Creating Flask app...")  # Debug print
    app = Flask(__name__)
    CORS(app, 
         resources={
    r"/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],  # Specify your frontend URL(s)
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
    app.config.from_object(config_class)

    db.init_app(app)
    mail.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    migrate.init_app(app, db)

    print("Registering blueprints...")  # Debug print
    from app.routes import main_bp, auth_bp, rsvp_bp, admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(rsvp_bp)
    app.register_blueprint(admin_bp)
    print("Blueprints registered!")  # Debug print

    print("Available routes:")  # Debug print
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

    return app