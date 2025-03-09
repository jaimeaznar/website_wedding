# run.py
from app import create_app, db
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        logger.debug("Creating database tables...")
        db.create_all()
        logger.debug("Database tables created")
        
    logger.debug("Starting Flask application...")
    app.run(debug=True)