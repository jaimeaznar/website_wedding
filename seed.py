# seed_allergens.py
from app import create_app, db
from app.models.allergen import Allergen

def seed_allergens():
    common_allergens = [
        'Gluten',
        'Dairy',
        'Nuts',
        'Peanuts',
        'Soy',
        'Eggs',
        'Fish',
        'Shellfish',
        'Celery',
        'Mustard',
        'Sesame',
        'Sulphites',
        'Lupins',
        'Molluscs'
    ]
    
    for allergen_name in common_allergens:
        existing = Allergen.query.filter_by(name=allergen_name).first()
        if not existing:
            allergen = Allergen(name=allergen_name)
            db.session.add(allergen)
    
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_allergens()