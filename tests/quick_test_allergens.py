# quick_test_allergens.py - Quick manual test for allergen functionality
import sys
import os

# Add the parent directory to the Python path so we can import app
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app import create_app, db
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.models.allergen import Allergen, GuestAllergen
import secrets

def test_allergen_functionality():
    """Quick test to verify allergen functionality works."""
    print("🧪 Testing allergen functionality...")
    
    app = create_app()
    
    with app.app_context():
        print("📊 Setting up test data...")
        
        # Clean up any existing test data
        test_guests = Guest.query.filter(Guest.email.like('%testquick%')).all()
        for guest in test_guests:
            if guest.rsvp:
                # Delete allergens first
                GuestAllergen.query.filter_by(rsvp_id=guest.rsvp.id).delete()
                # Delete RSVP
                db.session.delete(guest.rsvp)
            db.session.delete(guest)
        db.session.commit()
        
        # Ensure we have allergens
        allergens = Allergen.query.all()
        if len(allergens) < 3:
            print("📝 Creating test allergens...")
            for name in ['Test Gluten', 'Test Dairy', 'Test Nuts']:
                if not Allergen.query.filter_by(name=name).first():
                    allergen = Allergen(name=name)
                    db.session.add(allergen)
            db.session.commit()
            allergens = Allergen.query.all()
        
        print(f"✅ Found {len(allergens)} allergens in database")
        
        # Create test guest
        guest = Guest(
            name="Quick Test Guest",
            email="testquick@example.com",
            phone="555-QUICK",
            token=secrets.token_urlsafe(32),
            is_family=True
        )
        db.session.add(guest)
        db.session.commit()
        print(f"✅ Created test guest: {guest.name} (ID: {guest.id})")
        
        # Create RSVP
        rsvp = RSVP(
            guest_id=guest.id,
            is_attending=True,
            hotel_name="Quick Test Hotel"
        )
        db.session.add(rsvp)
        db.session.flush()  # Get the ID
        print(f"✅ Created RSVP (ID: {rsvp.id})")
        
        # Add allergens
        print("📝 Adding allergens...")
        
        # Standard allergen
        guest_allergen = GuestAllergen(
            rsvp_id=rsvp.id,
            guest_name=guest.name,
            allergen_id=allergens[0].id
        )
        db.session.add(guest_allergen)
        print(f"   - Standard: {allergens[0].name}")
        
        # Custom allergen
        custom_allergen = GuestAllergen(
            rsvp_id=rsvp.id,
            guest_name=guest.name,
            custom_allergen="Custom Shellfish Allergy"
        )
        db.session.add(custom_allergen)
        print(f"   - Custom: Custom Shellfish Allergy")
        
        db.session.commit()
        
        # Verify allergens were saved
        print("\n🔍 Verifying saved allergens...")
        saved_allergens = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).all()
        print(f"Found {len(saved_allergens)} saved allergen records:")
        
        for allergen in saved_allergens:
            if allergen.allergen:
                print(f"   ✅ Standard: {allergen.allergen.name} for {allergen.guest_name}")
            if allergen.custom_allergen:
                print(f"   ✅ Custom: {allergen.custom_allergen} for {allergen.guest_name}")
        
        # Test RSVP properties
        print("\n🔧 Testing RSVP allergen properties...")
        allergen_ids = rsvp.allergen_ids
        print(f"   Allergen IDs: {allergen_ids}")
        
        custom_allergen_text = rsvp.custom_allergen
        print(f"   Custom allergen: {custom_allergen_text}")
        
        # Test admin view simulation
        print("\n👨‍💼 Simulating admin view...")
        all_rsvps = RSVP.query.all()
        for test_rsvp in all_rsvps:
            if test_rsvp.is_attending:
                allergen_records = test_rsvp.allergens
                if allergen_records:
                    print(f"   RSVP {test_rsvp.id} has {len(allergen_records)} allergen records")
                    for record in allergen_records:
                        if record.allergen:
                            print(f"     - {record.guest_name}: {record.allergen.name}")
                        if record.custom_allergen:
                            print(f"     - {record.guest_name}: {record.custom_allergen} (custom)")
                else:
                    print(f"   RSVP {test_rsvp.id} has no allergen records")
        
        print(f"\n🎉 Test completed successfully!")
        print(f"📍 Test RSVP URL: http://localhost:5001/rsvp/{guest.token}")
        print(f"🔗 Admin dashboard: http://localhost:5001/admin/dashboard")
        
        return True

if __name__ == '__main__':
    try:
        test_allergen_functionality()
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()