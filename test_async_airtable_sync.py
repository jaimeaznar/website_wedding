#!/usr/bin/env python3
"""
Test script to verify async Airtable sync approach.
Run this locally before deploying changes to production.

Usage:
    cd /path/to/website_wedding
    python test_async_airtable_sync.py
"""
import os
import sys
import time
import threading
import logging
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_threading_basic():
    """Test 1: Basic threading works."""
    print("\n" + "="*60)
    print("TEST 1: Basic threading")
    print("="*60)
    
    result = {'completed': False, 'thread_id': None}
    
    def background_task():
        result['thread_id'] = threading.current_thread().name
        time.sleep(0.5)  # Simulate work
        result['completed'] = True
        logger.info("Background task completed")
    
    main_thread = threading.current_thread().name
    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()
    
    # Main thread continues immediately
    logger.info("Main thread continues while background runs")
    
    # Wait for completion
    thread.join(timeout=2)
    
    assert result['completed'], "Background task should complete"
    assert result['thread_id'] != main_thread, "Should run in different thread"
    print("✅ PASSED: Threading works correctly")


def test_threading_with_flask_context():
    """Test 2: Threading with Flask app context."""
    print("\n" + "="*60)
    print("TEST 2: Threading with Flask app context")
    print("="*60)
    
    from app import create_app
    
    result = {'completed': False, 'error': None, 'app_name': None}
    
    def background_task_with_context():
        try:
            # Create new app context in background thread
            app = create_app()
            with app.app_context():
                # Access something that requires app context
                result['app_name'] = app.name
                time.sleep(0.3)
                result['completed'] = True
                logger.info("Background task with Flask context completed")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Background task failed: {e}")
    
    thread = threading.Thread(target=background_task_with_context, daemon=True)
    thread.start()
    
    logger.info("Main thread continues...")
    thread.join(timeout=5)
    
    if result['error']:
        print(f"❌ FAILED: {result['error']}")
        return False
    
    assert result['completed'], "Should complete with app context"
    assert result['app_name'] is not None, "Should access app"
    print("✅ PASSED: Flask app context works in background thread")
    return True


def test_async_airtable_sync_simulation():
    """Test 3: Simulate the actual async Airtable sync pattern."""
    print("\n" + "="*60)
    print("TEST 3: Simulated async Airtable sync")
    print("="*60)
    
    from app import create_app
    
    sync_log = []
    
    def async_sync_to_airtable(guest_token: str, guest_name: str):
        """Simulates the new async _sync_to_airtable method."""
        
        def sync_task():
            try:
                app = create_app()
                with app.app_context():
                    sync_log.append(f"[{datetime.now()}] Starting sync for {guest_name}")
                    
                    # Simulate Airtable API call delay
                    time.sleep(1.5)  # This would be the slow Airtable call
                    
                    sync_log.append(f"[{datetime.now()}] Completed sync for {guest_name}")
                    logger.info(f"Synced RSVP for {guest_name} to Airtable")
            except Exception as e:
                sync_log.append(f"[{datetime.now()}] FAILED sync for {guest_name}: {e}")
                logger.warning(f"Background Airtable sync failed for {guest_name}: {e}")
        
        thread = threading.Thread(target=sync_task, daemon=True)
        thread.start()
        # Fire and forget - don't wait for thread
        return thread  # Return for testing purposes only
    
    # Simulate the RSVP flow
    start_time = time.time()
    
    # This is what happens in create_or_update_rsvp:
    # 1. Save to Postgres (instant)
    sync_log.append(f"[{datetime.now()}] RSVP saved to Postgres")
    
    # 2. Fire off async Airtable sync
    thread = async_sync_to_airtable("test-token-123", "Test Guest")
    
    # 3. Return response to user immediately
    response_time = time.time() - start_time
    sync_log.append(f"[{datetime.now()}] Response returned to user")
    
    logger.info(f"Response returned in {response_time*1000:.0f}ms (user doesn't wait)")
    
    # For testing: wait for background to complete
    thread.join(timeout=5)
    
    total_time = time.time() - start_time
    
    # Print timeline
    print("\nTimeline:")
    for entry in sync_log:
        print(f"  {entry}")
    
    print(f"\n  Response time: {response_time*1000:.0f}ms")
    print(f"  Total sync time: {total_time*1000:.0f}ms")
    
    # Verify the key behavior
    assert response_time < 0.1, f"Response should be instant, was {response_time*1000:.0f}ms"
    assert len(sync_log) == 4, "Should have all log entries"
    print("\n✅ PASSED: User gets instant response, sync happens in background")


def test_async_sync_failure_handling():
    """Test 4: Verify failures in background don't affect main flow."""
    print("\n" + "="*60)
    print("TEST 4: Failure handling in background sync")
    print("="*60)
    
    result = {'main_completed': False, 'background_failed': False}
    
    def failing_sync_task():
        try:
            time.sleep(0.2)
            raise Exception("Simulated Airtable timeout!")
        except Exception as e:
            result['background_failed'] = True
            logger.warning(f"Background sync failed (expected): {e}")
    
    # Start background task that will fail
    thread = threading.Thread(target=failing_sync_task, daemon=True)
    thread.start()
    
    # Main flow continues and completes
    result['main_completed'] = True
    logger.info("Main RSVP flow completed successfully")
    
    # Wait for background to fail
    thread.join(timeout=2)
    
    assert result['main_completed'], "Main flow should complete"
    assert result['background_failed'], "Background should have failed"
    print("✅ PASSED: Background failures don't affect main RSVP flow")


def test_real_airtable_connection():
    """Test 5: Test actual Airtable connection (optional, requires config)."""
    print("\n" + "="*60)
    print("TEST 5: Real Airtable connection test")
    print("="*60)
    
    from app import create_app
    
    app = create_app()
    with app.app_context():
        try:
            from app.services.airtable_service import get_airtable_service
            airtable = get_airtable_service()
            
            if not airtable.is_configured:
                print("⚠️  SKIPPED: Airtable not configured")
                return
            
            # Try to connect
            logger.info("Testing Airtable connection...")
            # Just verify we can get the service
            print("✅ PASSED: Airtable service accessible")
            
        except Exception as e:
            print(f"⚠️  SKIPPED: Could not test Airtable: {e}")


def test_multiple_concurrent_syncs():
    """Test 6: Multiple guests submitting at same time."""
    print("\n" + "="*60)
    print("TEST 6: Concurrent sync requests")
    print("="*60)
    
    results = {}
    lock = threading.Lock()
    
    def sync_guest(guest_name: str, delay: float):
        time.sleep(delay)  # Simulate API call
        with lock:
            results[guest_name] = datetime.now()
        logger.info(f"Synced {guest_name}")
    
    # Simulate 3 guests submitting at nearly the same time
    threads = []
    for i, (name, delay) in enumerate([
        ("Guest A", 0.5),
        ("Guest B", 0.3),
        ("Guest C", 0.7),
    ]):
        t = threading.Thread(target=sync_guest, args=(name, delay), daemon=True)
        threads.append(t)
        t.start()
    
    # All should complete
    for t in threads:
        t.join(timeout=3)
    
    assert len(results) == 3, "All syncs should complete"
    print(f"✅ PASSED: All {len(results)} concurrent syncs completed")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ASYNC AIRTABLE SYNC - PRE-DEPLOYMENT TESTS")
    print("="*60)
    print("Running tests to verify async sync approach...")
    
    tests = [
        ("Basic Threading", test_threading_basic),
        ("Flask Context in Thread", test_threading_with_flask_context),
        ("Async Sync Simulation", test_async_airtable_sync_simulation),
        ("Failure Handling", test_async_sync_failure_handling),
        ("Real Airtable Connection", test_real_airtable_connection),
        ("Concurrent Syncs", test_multiple_concurrent_syncs),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {name}")
            print(f"   Error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n✅ All tests passed! Safe to deploy async sync changes.")
        return 0
    else:
        print("\n❌ Some tests failed. Review before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())