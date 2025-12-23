#!/usr/bin/env python3
"""
Manual testing script for reminder system with dynamic dates.

Run from project root:
    python tests/test_reminder_manual.py

This script simulates real scenarios to test the reminder system.
"""

import os
import sys
from datetime import datetime, timedelta, date

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.models.reminder import (
    ReminderType, ReminderStatus, ReminderHistory,
    ReminderBatch, GuestReminderPreference
)
from app.services.reminder_service import ReminderService
import secrets


class ReminderTestScenarios:
    """Test scenarios for the reminder system."""
    
    def __init__(self):
        self.app = create_app()
        self.created_guest_ids = []  # Store IDs, not objects (to avoid detached session issues)
    
    def setup_scenario(self, days_until_deadline: int, guests_config: list):
        """
        Set up a test scenario.
        
        Args:
            days_until_deadline: How many days until RSVP deadline
            guests_config: List of dicts with guest configurations
                [
                    {'name': 'Guest 1', 'has_rsvp': False},
                    {'name': 'Guest 2', 'has_rsvp': True, 'attending': True},
                    {'name': 'Guest 3', 'has_rsvp': True, 'cancelled': True},
                ]
        """
        with self.app.app_context():
            # Calculate deadline from today
            today = date.today()
            deadline = today + timedelta(days=days_until_deadline)
            
            # Update app config
            self.app.config['RSVP_DEADLINE'] = deadline.strftime('%Y-%m-%d')
            
            print(f"\n{'='*60}")
            print(f"SCENARIO SETUP")
            print(f"{'='*60}")
            print(f"Today's date:     {today}")
            print(f"RSVP Deadline:    {deadline} ({days_until_deadline} days from now)")
            print(f"Wedding Date:     {deadline + timedelta(days=30)}")
            print(f"{'='*60}\n")
            
            # Calculate when each reminder should be sent
            print("REMINDER SCHEDULE:")
            print("-" * 40)
            for reminder_type in ReminderType.ALL_TYPES:
                days_before = ReminderType.get_days_before(reminder_type)
                reminder_date = deadline - timedelta(days=days_before)
                days_from_now = (reminder_date - today).days
                
                status = "✓ TODAY!" if days_from_now == 0 else \
                         f"in {days_from_now} days" if days_from_now > 0 else \
                         f"{abs(days_from_now)} days ago"
                
                print(f"  {reminder_type:20} → {reminder_date} ({status})")
            print()
            
            # Create test guests
            print("CREATING TEST GUESTS:")
            print("-" * 40)
            
            for config in guests_config:
                guest = Guest(
                    name=config['name'],
                    email=config.get('email', f"{config['name'].lower().replace(' ', '.')}@test.com"),
                    phone=config.get('phone', f"555-{secrets.randbelow(10000):04d}"),
                    token=secrets.token_urlsafe(32),
                    language_preference=config.get('language', 'es')
                )
                db.session.add(guest)
                db.session.flush()
                
                self.created_guest_ids.append({'id': guest.id, 'name': guest.name})
                
                rsvp_status = "No RSVP"
                
                if config.get('has_rsvp'):
                    rsvp = RSVP(
                        guest_id=guest.id,
                        is_attending=config.get('attending', True),
                        is_cancelled=config.get('cancelled', False),
                        hotel_name=config.get('hotel', 'Test Hotel')
                    )
                    db.session.add(rsvp)
                    
                    if config.get('cancelled'):
                        rsvp_status = "RSVP Cancelled ❌"
                    elif config.get('attending'):
                        rsvp_status = "RSVP Attending ✓"
                    else:
                        rsvp_status = "RSVP Declined"
                
                if config.get('opted_out'):
                    pref = GuestReminderPreference(
                        guest_id=guest.id,
                        opt_out=True
                    )
                    db.session.add(pref)
                    rsvp_status += " (Opted out)"
                
                if config.get('already_reminded'):
                    reminder = ReminderHistory(
                        guest_id=guest.id,
                        reminder_type=config.get('already_reminded'),
                        status=ReminderStatus.SENT,
                        email_sent_to=guest.email
                    )
                    db.session.add(reminder)
                    rsvp_status += f" (Already sent: {config.get('already_reminded')})"
                
                print(f"  {guest.name:25} → {rsvp_status}")
            
            db.session.commit()
            print()
    
    def check_who_needs_reminder(self, reminder_type: str = None):
        """Check which guests need reminders."""
        with self.app.app_context():
            print(f"\n{'='*60}")
            print(f"WHO NEEDS REMINDERS?")
            print(f"{'='*60}\n")
            
            types_to_check = [reminder_type] if reminder_type else ReminderType.ALL_TYPES
            
            for rtype in types_to_check:
                guests = ReminderService.get_guests_needing_reminder(rtype)
                
                print(f"{rtype.upper()} Reminder ({ReminderType.get_days_before(rtype)} days before):")
                print("-" * 40)
                
                if guests:
                    for guest in guests:
                        print(f"  📧 {guest.name} ({guest.email})")
                else:
                    print("  (No guests need this reminder)")
                print()
    
    def check_should_send_today(self):
        """Check which reminders should be sent today."""
        with self.app.app_context():
            print(f"\n{'='*60}")
            print(f"SHOULD ANY REMINDERS BE SENT TODAY?")
            print(f"{'='*60}\n")
            
            any_scheduled = False
            
            for reminder_type in ReminderType.ALL_TYPES:
                should_send = ReminderService.should_send_reminder_today(reminder_type)
                
                if should_send:
                    any_scheduled = True
                    guests = ReminderService.get_guests_needing_reminder(reminder_type)
                    print(f"✓ {reminder_type.upper()}: YES! Would send to {len(guests)} guests")
                    for guest in guests:
                        print(f"    → {guest.name} ({guest.email})")
                else:
                    print(f"✗ {reminder_type.upper()}: No (not scheduled for today)")
            
            if not any_scheduled:
                print("\n⚠️  No reminders scheduled for today.")
                print("   Reminders are only sent on specific days before the deadline.")
    
    def simulate_dry_run(self):
        """Simulate what the scheduler would do (dry run)."""
        with self.app.app_context():
            print(f"\n{'='*60}")
            print(f"DRY RUN - SIMULATING SCHEDULER")
            print(f"{'='*60}\n")
            
            for reminder_type in ReminderType.ALL_TYPES:
                if ReminderService.should_send_reminder_today(reminder_type):
                    guests = ReminderService.get_guests_needing_reminder(reminder_type)
                    
                    print(f"📤 Would send {reminder_type.upper()} reminder to:")
                    for guest in guests:
                        print(f"   • {guest.name} <{guest.email}>")
                    print()
    
    def cleanup(self):
        """Clean up test data."""
        with self.app.app_context():
            print(f"\n{'='*60}")
            print(f"CLEANING UP TEST DATA")
            print(f"{'='*60}\n")
            
            for guest_info in self.created_guest_ids:
                try:
                    guest_id = guest_info['id']
                    guest_name = guest_info['name']
                    
                    # Delete related records first
                    ReminderHistory.query.filter_by(guest_id=guest_id).delete()
                    GuestReminderPreference.query.filter_by(guest_id=guest_id).delete()
                    
                    # Now delete the guest (cascade will handle RSVP)
                    guest = Guest.query.get(guest_id)
                    if guest:
                        db.session.delete(guest)
                        print(f"  Deleted: {guest_name}")
                except Exception as e:
                    print(f"  Error deleting {guest_info.get('name', 'unknown')}: {e}")
            
            db.session.commit()
            self.created_guest_ids = []
            print("\n✓ Cleanup complete")


def run_scenario_1():
    """
    Scenario 1: Deadline in 30 days (Initial reminder should trigger)
    """
    print("\n" + "="*70)
    print("SCENARIO 1: Deadline in 30 days - Initial Reminder Day")
    print("="*70)
    
    tester = ReminderTestScenarios()
    
    try:
        tester.setup_scenario(
            days_until_deadline=30,
            guests_config=[
                {'name': 'María García', 'has_rsvp': False},
                {'name': 'Juan Pérez', 'has_rsvp': False},
                {'name': 'Ana López', 'has_rsvp': True, 'attending': True},  # Should be excluded
                {'name': 'Carlos Ruiz', 'has_rsvp': True, 'cancelled': True},  # Should be included
                {'name': 'Elena Martín', 'has_rsvp': False, 'opted_out': True},  # Should be excluded
            ]
        )
        
        tester.check_who_needs_reminder(ReminderType.INITIAL)
        tester.check_should_send_today()
        tester.simulate_dry_run()
        
    finally:
        tester.cleanup()


def run_scenario_2():
    """
    Scenario 2: Deadline in 14 days (First follow-up should trigger)
    """
    print("\n" + "="*70)
    print("SCENARIO 2: Deadline in 14 days - First Follow-up Day")
    print("="*70)
    
    tester = ReminderTestScenarios()
    
    try:
        tester.setup_scenario(
            days_until_deadline=14,
            guests_config=[
                {'name': 'Pedro Sánchez', 'has_rsvp': False},
                {'name': 'Laura Fernández', 'has_rsvp': False, 
                 'already_reminded': ReminderType.INITIAL},  # Already got initial
                {'name': 'Miguel Torres', 'has_rsvp': True, 'attending': False},  # Declined
            ]
        )
        
        tester.check_who_needs_reminder(ReminderType.FIRST_FOLLOWUP)
        tester.check_should_send_today()
        
    finally:
        tester.cleanup()


def run_scenario_3():
    """
    Scenario 3: Deadline in 3 days (Final reminder should trigger)
    """
    print("\n" + "="*70)
    print("SCENARIO 3: Deadline in 3 days - FINAL Reminder Day!")
    print("="*70)
    
    tester = ReminderTestScenarios()
    
    try:
        tester.setup_scenario(
            days_until_deadline=3,
            guests_config=[
                {'name': 'Isabel Moreno', 'has_rsvp': False},
                {'name': 'Fernando Díaz', 'has_rsvp': False},
            ]
        )
        
        tester.check_who_needs_reminder(ReminderType.FINAL)
        tester.check_should_send_today()
        tester.simulate_dry_run()
        
    finally:
        tester.cleanup()


def run_scenario_4():
    """
    Scenario 4: Deadline in 20 days (No reminder scheduled)
    """
    print("\n" + "="*70)
    print("SCENARIO 4: Deadline in 20 days - No Reminder Scheduled")
    print("="*70)
    
    tester = ReminderTestScenarios()
    
    try:
        tester.setup_scenario(
            days_until_deadline=20,
            guests_config=[
                {'name': 'Rosa Jiménez', 'has_rsvp': False},
                {'name': 'Antonio Vega', 'has_rsvp': False},
            ]
        )
        
        tester.check_who_needs_reminder()
        tester.check_should_send_today()
        
    finally:
        tester.cleanup()


def run_custom_scenario(days_until_deadline: int):
    """
    Run a custom scenario with specified days until deadline.
    """
    print("\n" + "="*70)
    print(f"CUSTOM SCENARIO: Deadline in {days_until_deadline} days")
    print("="*70)
    
    tester = ReminderTestScenarios()
    
    try:
        tester.setup_scenario(
            days_until_deadline=days_until_deadline,
            guests_config=[
                {'name': 'Test Guest 1', 'has_rsvp': False},
                {'name': 'Test Guest 2', 'has_rsvp': False},
                {'name': 'Test Guest 3 (with RSVP)', 'has_rsvp': True, 'attending': True},
            ]
        )
        
        tester.check_who_needs_reminder()
        tester.check_should_send_today()
        tester.simulate_dry_run()
        
    finally:
        tester.cleanup()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test reminder system with dynamic dates')
    parser.add_argument('--scenario', type=int, choices=[1, 2, 3, 4],
                       help='Run a specific scenario (1-4)')
    parser.add_argument('--days', type=int,
                       help='Run custom scenario with N days until deadline')
    parser.add_argument('--all', action='store_true',
                       help='Run all predefined scenarios')
    
    args = parser.parse_args()
    
    if args.days:
        run_custom_scenario(args.days)
    elif args.scenario == 1:
        run_scenario_1()
    elif args.scenario == 2:
        run_scenario_2()
    elif args.scenario == 3:
        run_scenario_3()
    elif args.scenario == 4:
        run_scenario_4()
    elif args.all:
        run_scenario_1()
        run_scenario_2()
        run_scenario_3()
        run_scenario_4()
    else:
        # Default: show menu
        print("\n" + "="*60)
        print("REMINDER SYSTEM TEST SCENARIOS")
        print("="*60)
        print("\nUsage:")
        print("  python test_reminder_manual.py --scenario 1   # 30 days (Initial)")
        print("  python test_reminder_manual.py --scenario 2   # 14 days (First follow-up)")
        print("  python test_reminder_manual.py --scenario 3   # 3 days (Final)")
        print("  python test_reminder_manual.py --scenario 4   # 20 days (No reminder)")
        print("  python test_reminder_manual.py --days 7       # Custom: 7 days")
        print("  python test_reminder_manual.py --all          # Run all scenarios")
        print()
        
        # Run scenario 1 as default demo
        print("Running Scenario 1 as demo...\n")
        run_scenario_1()