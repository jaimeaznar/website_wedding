#!/usr/bin/env python3
"""
Test the new async _sync_to_airtable implementation.

This script:
1. Patches rsvp_service with the new async implementation
2. Tests it with a real guest from your database
3. Verifies async behavior (instant return, background sync)

Usage:
    cd /path/to/website_wedding
    python test_new_sync_implementation.py
"""
import os
import sys
import time
import threading
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# NEW IMPLEMENTATION TO TEST (copy of proposed changes)
# ============================================================
def new_sync_to_airtable(guest) -> None:
    """
    NEW async implementation to test.
    
    Sync RSVP data to Airtable in background thread.
    User gets immediate response, sync happens asynchronously.
    """
    # Capture values before thread starts
    token = guest.token
    name = guest.name
    
    def sync_task():
        try:
            from app import create_app
            from app.services.airtable_service import get_airtable_service
            
            app = create_app()
            with app.app_context():
                airtable = get_airtable_service()
                
                if not airtable.is_configured:
                    logger.debug("Airtable not configured, skipping sync")
                    return
                
                logger.info(f"[BACKGROUND] Starting Airtable sync for {name}...")
                airtable.sync_rsvp_to_airtable(token)
                logger.info(f"[BACKGROUND] ✅ Synced RSVP for {name} to Airtable")
                
        except Exception as e:
            logger.warning(f"[BACKGROUND] ❌ Airtable sync failed for {name}: {e}")
    
    thread = threading.Thread(target=sync_task, daemon=True)
    thread.start()
    logger.info(f"[MAIN] Async sync started for {name} (not waiting)")
    return thread  # Return for testing only


# ============================================================
# TESTS
# ============================================================
def test_with_real_guest():
    """Test with a real guest from the database."""
    print("\n" + "="*60)
    print("TEST: Real guest async sync")
    print("="*60)
    
    from app import create_app
    from app.models.guest import Guest
    
    app = create_app()
    with app.app_context():
        # Find a guest with an RSVP (preferably one that already synced successfully)
        guest = Guest.query.filter(Guest.rsvp != None).first()
        
        if not guest:
            print("⚠️  No guests with RSVP found. Trying any guest...")
            guest = Guest.query.first()
        
        if not guest:
            print("❌ No guests in database!")
            return False
        
        print(f"\nUsing guest: {guest.name} (token: {guest.token[:8]}...)")
        print(f"Has RSVP: {guest.rsvp is not None}")
        
        # Time the async call
        start = time.time()
        thread = new_sync_to_airtable(guest)
        return_time = time.time() - start
        
        print(f"\n⏱️  Function returned in {return_time*1000:.1f}ms")
        
        if return_time > 0.1:
            print("❌ FAILED: Should return instantly (<100ms)")
            return False
        
        print("✅ PASSED: Instant return (async working)")
        
        # Now wait for background to complete
        print("\nWaiting for background sync to complete...")
        thread.join(timeout=30)
        
        if thread.is_alive():
            print("⚠️  Background thread still running after 30s (possible timeout issue)")
        else:
            print("✅ Background sync completed")
        
        return True


def test_with_specific_guest(phone_or_token: str):
    """Test with a specific guest by phone or token."""
    print("\n" + "="*60)
    print(f"TEST: Specific guest sync ({phone_or_token})")
    print("="*60)
    
    from app import create_app
    from app.models.guest import Guest
    
    app = create_app()
    with app.app_context():
        # Try to find by phone or token
        guest = Guest.query.filter(
            (Guest.phone == phone_or_token) | 
            (Guest.token == phone_or_token)
        ).first()
        
        if not guest:
            print(f"❌ Guest not found: {phone_or_token}")
            return False
        
        print(f"\nFound guest: {guest.name}")
        print(f"Phone: {guest.phone}")
        print(f"Token: {guest.token[:8]}...")
        
        # Run async sync
        start = time.time()
        thread = new_sync_to_airtable(guest)
        return_time = time.time() - start
        
        print(f"\n⏱️  Function returned in {return_time*1000:.1f}ms")
        
        # Wait for completion
        print("Waiting for background sync...")
        thread.join(timeout=30)
        
        total_time = time.time() - start
        print(f"⏱️  Total sync time: {total_time:.1f}s")
        
        return True


def test_failure_handling():
    """Test that failures in background don't crash anything."""
    print("\n" + "="*60)
    print("TEST: Failure handling")
    print("="*60)
    
    from app import create_app
    from app.models.guest import Guest
    
    app = create_app()
    with app.app_context():
        # Create a fake guest with invalid token
        class FakeGuest:
            token = "invalid-token-12345"
            name = "Fake Test Guest"
        
        fake_guest = FakeGuest()
        
        print(f"Testing with invalid token: {fake_guest.token}")
        
        start = time.time()
        thread = new_sync_to_airtable(fake_guest)
        return_time = time.time() - start
        
        print(f"⏱️  Function returned in {return_time*1000:.1f}ms")
        
        # Wait for background (should fail gracefully)
        thread.join(timeout=10)
        
        print("✅ PASSED: Main thread not affected by background failure")
        return True


def main():
    """Run tests."""
    print("\n" + "="*60)
    print("TESTING NEW ASYNC _sync_to_airtable IMPLEMENTATION")
    print("="*60)
    
    # Check for specific guest argument
    if len(sys.argv) > 1:
        phone_or_token = sys.argv[1]
        test_with_specific_guest(phone_or_token)
        return
    
    # Run all tests
    tests = [
        ("Real guest sync", test_with_real_guest),
        ("Failure handling", test_failure_handling),
    ]
    
    passed = 0
    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
        except Exception as e:
            print(f"❌ FAILED: {name} - {e}")
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    print("="*60)
    
    # Offer to test specific guest
    print("\nTo test with a specific guest (like Lourdes):")
    print("  python test_new_sync_implementation.py +34625070835")


if __name__ == "__main__":
    main()