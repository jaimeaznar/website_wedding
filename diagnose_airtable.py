#!/usr/bin/env python3
"""
Diagnostic script to troubleshoot Airtable sync issues.
Run from the project root: python diagnose_airtable_sync.py --phone "+34625070835"

This script will:
1. Find the guest in your local database by phone or token
2. Find the guest in Airtable
3. Compare the data
4. Attempt to sync and show detailed errors
"""

import os
import sys

# Add the app to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.models.allergen import GuestAllergen

app = create_app()


def diagnose_by_phone(phone: str):
    """Diagnose sync issues for a guest by phone number."""
    
    print("=" * 60)
    print(f"DIAGNOSING AIRTABLE SYNC FOR PHONE: {phone}")
    print("=" * 60)
    
    with app.app_context():
        # Step 1: Find in local database
        print("\n[1] SEARCHING LOCAL DATABASE BY PHONE...")
        local_guest = Guest.query.filter_by(phone=phone).first()
        
        if not local_guest:
            print(f"   ❌ No guest found with phone '{phone}' in local DB")
            # Try partial match
            local_guest = Guest.query.filter(Guest.phone.ilike(f"%{phone[-9:]}%")).first()
            if local_guest:
                print(f"   ⚠️  Found partial match: {local_guest.phone}")
            else:
                return
        
        _diagnose_guest(local_guest)


def diagnose_by_token(token: str):
    """Diagnose sync issues for a guest by token."""
    
    print("=" * 60)
    print(f"DIAGNOSING AIRTABLE SYNC FOR TOKEN: {token[:20]}...")
    print("=" * 60)
    
    with app.app_context():
        # Step 1: Find in local database
        print("\n[1] SEARCHING LOCAL DATABASE BY TOKEN...")
        local_guest = Guest.query.filter_by(token=token).first()
        
        if not local_guest:
            print(f"   ❌ No guest found with this token in local DB")
            return
        
        _diagnose_guest(local_guest)


def _diagnose_guest(local_guest: Guest):
    """Core diagnosis logic for a guest."""
    
    print(f"   ✅ Found: {local_guest.name} {local_guest.surname}")
    print(f"   - ID: {local_guest.id}")
    print(f"   - Token: {local_guest.token}")
    print(f"   - Phone: {local_guest.phone}")
    
    # Step 2: Get RSVP
    print("\n[2] CHECKING LOCAL RSVP...")
    rsvp = RSVP.query.filter_by(guest_id=local_guest.id).first()
    
    if not rsvp:
        print("   ❌ No RSVP found for this guest")
        return
    
    print(f"   ✅ RSVP found:")
    print(f"   - ID: {rsvp.id}")
    print(f"   - Attending: {rsvp.is_attending}")
    print(f"   - Cancelled: {rsvp.is_cancelled}")
    print(f"   - Adults: {rsvp.adults_count}")
    print(f"   - Children: {rsvp.children_count}")
    print(f"   - Hotel: {rsvp.hotel_name}")
    print(f"   - Transport Reception: {rsvp.transport_to_reception}")
    print(f"   - Transport Hotel: {rsvp.transport_to_hotel}")
    print(f"   - Created: {rsvp.created_at}")
    
    # Additional guests
    if rsvp.additional_guests:
        print(f"   - Additional guests ({len(rsvp.additional_guests)}):")
        for ag in rsvp.additional_guests:
            child_str = " [CHILD]" if ag.is_child else ""
            print(f"     • {ag.name}{child_str}")
    
    # Allergens
    allergens = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).all()
    if allergens:
        print(f"   - Dietary restrictions ({len(allergens)}):")
        for ga in allergens:
            allergen_name = ga.allergen.name if ga.allergen else ga.custom_allergen
            print(f"     • {ga.guest_name}: {allergen_name}")
    
    # Step 3: Check Airtable configuration
    print("\n[3] CHECKING AIRTABLE CONFIGURATION...")
    from app.services.airtable_service import get_airtable_service
    
    airtable = get_airtable_service()
    
    if not airtable.is_configured:
        print("   ❌ Airtable is NOT configured!")
        print(f"   - AIRTABLE_API_KEY: {'SET' if os.environ.get('AIRTABLE_API_KEY') else 'MISSING'}")
        print(f"   - AIRTABLE_BASE_ID: {'SET' if os.environ.get('AIRTABLE_BASE_ID') else 'MISSING'}")
        return
    
    print("   ✅ Airtable is configured")
    print(f"   - Base ID: {airtable.base_id}")
    print(f"   - Table: {airtable.table_name}")
    
    # Step 4: Find in Airtable by token
    print("\n[4] SEARCHING AIRTABLE BY TOKEN...")
    airtable_guest = None
    try:
        airtable_guest = airtable.get_guest_by_token(local_guest.token)
        
        if airtable_guest:
            print(f"   ✅ Found by token:")
            print(f"   - Record ID: {airtable_guest.record_id}")
            print(f"   - Name: {airtable_guest.name} {airtable_guest.surname}")
            print(f"   - Status: {airtable_guest.status}")
            print(f"   - Phone: {airtable_guest.phone}")
        else:
            print(f"   ❌ NOT found by token: {local_guest.token}")
            
    except Exception as e:
        print(f"   ❌ Error searching by token: {e}")
    
    # Step 5: Try finding by phone as backup
    if not airtable_guest and local_guest.phone:
        print("\n[5] SEARCHING AIRTABLE BY PHONE...")
        try:
            airtable_guest = airtable.get_guest_by_phone(local_guest.phone)
            
            if airtable_guest:
                print(f"   ✅ Found by phone:")
                print(f"   - Record ID: {airtable_guest.record_id}")
                print(f"   - Name: {airtable_guest.name} {airtable_guest.surname}")
                print(f"   - Token in Airtable: {airtable_guest.token}")
                print(f"   - Token in Local DB: {local_guest.token}")
                
                if airtable_guest.token != local_guest.token:
                    print("\n   ⚠️  TOKEN MISMATCH DETECTED!")
                    print("   This is why the sync failed - tokens don't match.")
            else:
                print(f"   ❌ NOT found by phone: {local_guest.phone}")
                
        except Exception as e:
            print(f"   ❌ Error searching by phone: {e}")
    
    # Step 6: Attempt manual sync with detailed logging
    if airtable_guest:
        print("\n[6] ATTEMPTING MANUAL SYNC...")
        try:
            from app.services.airtable_service import AirtableStatus
            
            # Determine status
            if rsvp.is_cancelled:
                status = AirtableStatus.CANCELLED
            elif rsvp.is_attending:
                status = AirtableStatus.ATTENDING
            else:
                status = AirtableStatus.DECLINED
            
            # Gather dietary notes
            dietary_notes = ""
            if allergens:
                allergen_list = []
                for ga in allergens:
                    if ga.allergen:
                        allergen_list.append(f"{ga.guest_name}: {ga.allergen.name}")
                    elif ga.custom_allergen:
                        allergen_list.append(f"{ga.guest_name}: {ga.custom_allergen}")
                dietary_notes = "; ".join(allergen_list)
            
            # Count guests
            adults = 1 + len([g for g in rsvp.additional_guests if not g.is_child])
            children = len([g for g in rsvp.additional_guests if g.is_child])
            
            print(f"   Preparing to update Airtable:")
            print(f"   - Record ID: {airtable_guest.record_id}")
            print(f"   - Status: {status.value}")
            print(f"   - Adults: {adults}")
            print(f"   - Children: {children}")
            print(f"   - Hotel: {rsvp.hotel_name}")
            print(f"   - Dietary Notes: {dietary_notes[:100]}..." if len(dietary_notes) > 100 else f"   - Dietary Notes: {dietary_notes}")
            
            # Confirm before updating
            confirm = input("\n   Do you want to sync this to Airtable? (y/n): ")
            
            if confirm.lower() == 'y':
                airtable.update_rsvp_status(
                    record_id=airtable_guest.record_id,
                    status=status,
                    rsvp_date=rsvp.created_at,
                    adults_count=adults,
                    children_count=children,
                    hotel=rsvp.hotel_name,
                    dietary_notes=dietary_notes,
                    transport_reception=rsvp.transport_to_reception,
                    transport_hotel=rsvp.transport_to_hotel,
                )
                print("\n   ✅ SYNC SUCCESSFUL!")
            else:
                print("\n   Sync cancelled by user.")
                
        except Exception as e:
            print(f"\n   ❌ SYNC FAILED with error:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            print("\n   Full traceback:")
            traceback.print_exc()
    else:
        print("\n[6] CANNOT SYNC - Guest not found in Airtable")
        print("   Possible issues:")
        print("   - Guest was deleted from Airtable")
        print("   - Token was changed in Airtable")
        print("   - Phone number format differs")


def list_all_guests():
    """List all guests in local DB for reference."""
    print("\n" + "=" * 60)
    print("ALL GUESTS IN LOCAL DATABASE")
    print("=" * 60)
    
    with app.app_context():
        guests = Guest.query.all()
        for g in guests:
            rsvp = RSVP.query.filter_by(guest_id=g.id).first()
            status = "No RSVP"
            if rsvp:
                if rsvp.is_cancelled:
                    status = "Cancelled"
                elif rsvp.is_attending:
                    status = "Attending"
                else:
                    status = "Declined"
            
            print(f"  {g.id}: {g.name} {g.surname or ''} | {g.phone} | {status}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Diagnose Airtable sync issues")
    parser.add_argument("--phone", help="Guest phone number to search for")
    parser.add_argument("--token", help="Guest token to search for")
    parser.add_argument("--list", action="store_true", help="List all guests")
    
    args = parser.parse_args()
    
    if args.list:
        list_all_guests()
    elif args.phone:
        diagnose_by_phone(args.phone)
    elif args.token:
        diagnose_by_token(args.token)
    else:
        print("Usage:")
        print("  python diagnose_airtable_sync.py --phone '+34625070835'")
        print("  python diagnose_airtable_sync.py --token 'abc123...'")
        print("  python diagnose_airtable_sync.py --list")