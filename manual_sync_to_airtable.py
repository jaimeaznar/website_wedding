#!/usr/bin/env python3
"""
Manually sync a specific guest from production Postgres to Airtable.

Usage:
    DATABASE_URL="your_supabase_url" python manual_sync_to_airtable.py +34625070835
    
Or set DATABASE_URL in your .env and run:
    python manual_sync_to_airtable.py +34625070835
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env if present
from dotenv import load_dotenv
load_dotenv()

def main():
    if len(sys.argv) < 2:
        print("Usage: python manual_sync_to_airtable.py <phone_or_token>")
        print("Example: python manual_sync_to_airtable.py +34625070835")
        sys.exit(1)
    
    search_term = sys.argv[1]
    
    # Check we have production DATABASE_URL
    db_url = os.environ.get('DATABASE_URL', '')
    if 'supabase' not in db_url and 'railway' not in db_url:
        print("⚠️  WARNING: DATABASE_URL doesn't look like production!")
        print(f"   Current: {db_url[:50]}...")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    from app import create_app
    from app.models.guest import Guest
    from app.models.rsvp import RSVP
    
    app = create_app()
    with app.app_context():
        # Find guest
        guest = Guest.query.filter(
            (Guest.phone == search_term) | 
            (Guest.token == search_term) |
            (Guest.name.ilike(f'%{search_term}%'))
        ).first()
        
        if not guest:
            print(f"❌ Guest not found: {search_term}")
            sys.exit(1)
        
        print(f"\n{'='*50}")
        print(f"GUEST FOUND: {guest.name}")
        print(f"{'='*50}")
        print(f"Phone: {guest.phone}")
        print(f"Token: {guest.token[:20]}...")
        
        # Check RSVP
        rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
        
        if not rsvp:
            print(f"\n❌ NO RSVP RECORD in Postgres!")
            print("   This is the problem - the RSVP was never saved to Postgres.")
            print("   The guest needs to re-submit their RSVP.")
            sys.exit(1)
        
        print(f"\n{'='*50}")
        print(f"RSVP DATA IN POSTGRES")
        print(f"{'='*50}")
        print(f"Is Attending: {rsvp.is_attending}")
        print(f"Is Cancelled: {rsvp.is_cancelled}")
        print(f"Adults: {rsvp.adults_count}")
        print(f"Children: {rsvp.children_count}")
        print(f"Hotel: {rsvp.hotel_name}")
        print(f"Transport to Reception: {rsvp.transport_to_reception}")
        print(f"Transport to Hotel: {rsvp.transport_to_hotel}")
        print(f"Created: {rsvp.created_at}")
        print(f"Last Updated: {rsvp.last_updated}")
        
        # Show additional guests
        if rsvp.additional_guests:
            print(f"\nAdditional Guests ({len(rsvp.additional_guests)}):")
            for ag in rsvp.additional_guests:
                print(f"  - {ag.name} (child={ag.is_child})")
        
        # Confirm sync
        print(f"\n{'='*50}")
        response = input("Sync this data to Airtable? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
        
        # Do the sync
        print("\nSyncing to Airtable...")
        from app.services.airtable_service import get_airtable_service
        
        airtable = get_airtable_service()
        
        if not airtable.is_configured:
            print("❌ Airtable not configured!")
            sys.exit(1)
        
        try:
            airtable.sync_rsvp_to_airtable(guest.token)
            print(f"\n✅ Successfully synced {guest.name} to Airtable!")
        except Exception as e:
            print(f"\n❌ Sync failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()