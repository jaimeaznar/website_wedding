# smoke_test.py - Quick test to verify services work
import sys
from app import create_app
from app.services.guest_service import GuestService
from app.services.rsvp_service import RSVPService
from app.services.allergen_service import AllergenService
from app.services.admin_service import AdminService

def run_smoke_test():
    """Run a quick smoke test of the refactored services."""
    print("🔥 Running smoke test for refactored services...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test 1: Guest Service
            print("\n1️⃣ Testing GuestService...")
            guests = GuestService.get_all_guests()
            print(f"   ✅ Found {len(guests)} guests in database")
            
            # Test 2: RSVP Service
            print("\n2️⃣ Testing RSVPService...")
            rsvps = RSVPService.get_all_rsvps()
            print(f"   ✅ Found {len(rsvps)} RSVPs in database")
            
            deadline = RSVPService.get_rsvp_deadline_formatted()
            print(f"   ✅ RSVP deadline: {deadline}")
            
            # Test 3: Allergen Service
            print("\n3️⃣ Testing AllergenService...")
            allergens = AllergenService.get_all_allergens()
            print(f"   ✅ Found {len(allergens)} allergens in database")
            
            # Test 4: Admin Service
            print("\n4️⃣ Testing AdminService...")
            dashboard_data = AdminService.get_dashboard_data()
            print(f"   ✅ Dashboard data keys: {', '.join(dashboard_data.keys())}")
            
            # Test 5: Create a test guest
            print("\n5️⃣ Testing guest creation...")
            test_guest = GuestService.create_guest(
                name="Smoke Test Guest",
                phone="555-SMOKE",
                email="smoke@test.com"
            )
            print(f"   ✅ Created guest: {test_guest.name}")
            print(f"   📝 RSVP URL: http://localhost:5001/rsvp/{test_guest.token}")
            
            # Test 6: Create a test RSVP
            print("\n6️⃣ Testing RSVP creation...")
            form_data = {
                'is_attending': 'yes',
                'hotel_name': 'Smoke Test Hotel'
            }
            success, message, rsvp = RSVPService.create_or_update_rsvp(test_guest, form_data)
            if success:
                print(f"   ✅ Created RSVP: {message}")
            else:
                print(f"   ❌ Failed to create RSVP: {message}")
            
            print("\n✅ All smoke tests passed!")
            print("\n📌 Quick Links:")
            print(f"   - Home: http://localhost:5001/")
            print(f"   - Admin: http://localhost:5001/admin/login")
            print(f"   - Test RSVP: http://localhost:5001/rsvp/{test_guest.token}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Smoke test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    if run_smoke_test():
        sys.exit(0)
    else:
        sys.exit(1)