# seed.py - ENHANCED VERSION
from app import create_app, db
from app.models.allergen import Allergen
from app.models.guest import Guest
from app.models.rsvp import RSVP
import secrets

def seed_allergens():
    """Seed the database with common allergens."""
    print("Seeding allergens...")
    
    common_allergens = [
        'Gluten',
        'Dairy',
        'Nuts (Tree nuts)',
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
        'Molluscs',
        'Vegetarian',
        'Vegan',
        'Kosher',
        'Halal'
    ]
    
    allergens_added = 0
    for allergen_name in common_allergens:
        existing = Allergen.query.filter_by(name=allergen_name).first()
        if not existing:
            allergen = Allergen(name=allergen_name)
            db.session.add(allergen)
            allergens_added += 1
            print(f"  Added: {allergen_name}")
        else:
            print(f"  Exists: {allergen_name}")
    
    db.session.commit()
    print(f"Allergen seeding complete. Added {allergens_added} new allergens.")
    
    # Verify allergens were added
    total_allergens = Allergen.query.count()
    print(f"Total allergens in database: {total_allergens}")

def seed_test_guest():
    """Create a test guest for testing purposes."""
    print("\nCreating test guest...")
    
    # Check if test guest already exists
    existing_guest = Guest.query.filter_by(email='test@example.com').first()
    if existing_guest:
        print(f"Test guest already exists: {existing_guest.name} (token: {existing_guest.token})")
        return existing_guest
    
    # Create test guest
    test_guest = Guest(
        name='Test Family Guest',
        email='test@example.com',
        phone='555-0123',
        token=secrets.token_urlsafe(32),
        language_preference='en',
        has_plus_one=False,
        is_family=True  # Make it a family guest for testing
    )
    
    db.session.add(test_guest)
    db.session.commit()
    
    print(f"Created test guest: {test_guest.name}")
    print(f"RSVP URL: http://localhost:5000/rsvp/{test_guest.token}")
    
    return test_guest

def verify_database():
    """Verify the database setup."""
    print("\nVerifying database setup...")
    
    # Check allergens
    allergen_count = Allergen.query.count()
    print(f"Allergens in database: {allergen_count}")
    
    if allergen_count > 0:
        print("Sample allergens:")
        for allergen in Allergen.query.limit(5).all():
            print(f"  ID {allergen.id}: {allergen.name}")
    
    # Check guests
    guest_count = Guest.query.count()
    print(f"Guests in database: {guest_count}")
    
    # Check RSVPs
    rsvp_count = RSVP.query.count()
    print(f"RSVPs in database: {rsvp_count}")

def main():
    """Main seeding function."""
    app = create_app()
    
    with app.app_context():
        print("Starting database seeding...")
        
        # Create tables if they don't exist
        db.create_all()
        
        # Seed allergens
        seed_allergens()
        
        # Create test guest
        test_guest = seed_test_guest()
        
        # Verify setup
        verify_database()
        
        print("\nDatabase seeding complete!")
        print("\nNext steps:")
        print("1. Run the application: python run.py")
        print("2. Visit the admin panel: http://localhost:5000/admin/login")
        print("3. Test RSVP form: http://localhost:5000/rsvp/{test_guest.token}")
        print("4. Admin password: 'your-secure-password' (change this in production!)")

if __name__ == '__main__':
    main()