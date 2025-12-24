# wsgi.py
"""
WSGI entry point for production deployment (Railway, Gunicorn, etc.)
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).parent.absolute()
env_file = basedir / '.env'
if env_file.exists():
    load_dotenv(env_file)

from app import create_app, db
from app.models.allergen import Allergen

# Create the application
app = create_app()

def seed_allergens():
    """Seed the database with common allergens."""
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
        print(f"Seeded {len(common_allergens)} allergens")
    except Exception as e:
        db.session.rollback()
        print(f"Could not seed allergens: {str(e)}")

# Initialize database on startup
with app.app_context():
    db.create_all()
    
    # Seed allergens if needed
    if Allergen.query.count() == 0:
        seed_allergens()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)