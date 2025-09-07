# run.py
"""
Main application entry point.
Handles database initialization and starts the Flask development server.
"""

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST thing
basedir = Path(__file__).parent.absolute()
load_dotenv(basedir / '.env')

import os
import sys
from app import create_app, db
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if environment is properly configured."""
    logger.info("Checking environment configuration...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        logger.warning("⚠️  .env file not found!")
        logger.warning("   Run: cp .env.example .env")
        logger.warning("   Then update it with your configuration")
        return False
    
    # Check critical environment variables
    required_vars = ['SECRET_KEY', 'DATABASE_URL', 'ADMIN_PASSWORD', 'ADMIN_EMAIL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("   Please check your .env file")
        return False
    
    logger.info("✅ Environment configuration OK")
    return True

def initialize_database(app):
    """Initialize database tables if they don't exist."""
    with app.app_context():
        try:
            logger.info("Checking database connection...")
            # Test the connection
            db.engine.connect()
            logger.info("✅ Database connection successful")
            
            logger.info("Creating database tables if needed...")
            db.create_all()
            logger.info("✅ Database tables ready")
            
            # Seed initial allergens if needed
            from app.models.allergen import Allergen
            if Allergen.query.count() == 0:
                logger.info("Seeding initial allergens...")
                seed_allergens()
                logger.info("✅ Allergens seeded")
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {str(e)}")
            logger.error("   Check your DATABASE_URL in .env")
            logger.error("   Make sure PostgreSQL is running")
            sys.exit(1)

def seed_allergens():
    """Seed the database with common allergens."""
    from app.models.allergen import Allergen
    
    common_allergens = [
        'Gluten', 'Dairy', 'Nuts (Tree nuts)', 'Peanuts',
        'Soy', 'Eggs', 'Fish', 'Shellfish',
        'Celery', 'Mustard', 'Sesame', 'Sulphites',
        'Lupins', 'Molluscs', 'Vegetarian', 'Vegan',
        'Kosher', 'Halal'
    ]
    
    for allergen_name in common_allergens:
        existing = Allergen.query.filter_by(name=allergen_name).first()
        if not existing:
            allergen = Allergen(name=allergen_name)
            db.session.add(allergen)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning(f"Could not seed allergens: {str(e)}")

if __name__ == '__main__':
    # Check environment first
    if not check_environment():
        logger.error("Please configure your environment properly before running the application.")
        sys.exit(1)
    
    # Create the application
    try:
        app = create_app()
    except SystemExit:
        logger.error("Application failed to start due to configuration errors.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to create application: {str(e)}")
        sys.exit(1)
    
    # Initialize database
    initialize_database(app)
    
    # Run the application
    port = int(os.getenv('PORT', 5001))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info("=" * 60)
    logger.info("🎊 Wedding Website Ready!")
    logger.info("=" * 60)
    logger.info(f"🌐 Access the website at: http://localhost:{port}")
    logger.info(f"👤 Admin panel at: http://localhost:{port}/admin")
    logger.info(f"📝 RSVP landing at: http://localhost:{port}/rsvp")
    logger.info("=" * 60)
    logger.info("Press CTRL+C to stop the server")
    logger.info("=" * 60)
    
    app.run(
        host=host,
        port=port,
        debug=app.config.get('DEBUG', False)
    )