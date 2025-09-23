#!/usr/bin/env python3
"""
scheduler.py - Automated reminder scheduler
Run this script daily via cron to send scheduled reminders automatically.

Example cron entry (run daily at 9 AM):
0 9 * * * /path/to/venv/bin/python /path/to/scheduler.py

Or run manually:
python scheduler.py
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

# Import Flask app and services
from app import create_app, db
from app.services.reminder_service import ReminderService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_scheduled_reminders():
    """
    Run all scheduled reminders for today.
    This function checks which reminders should be sent based on the RSVP deadline
    and sends them automatically.
    """
    logger.info("=" * 60)
    logger.info(f"Starting scheduled reminder run at {datetime.now()}")
    logger.info("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Run the scheduled reminders
            results = ReminderService.run_scheduled_reminders()
            
            if results:
                logger.info("\n📊 REMINDER RESULTS:")
                for reminder_type, result in results.items():
                    logger.info(f"\n{reminder_type.upper()} Reminder:")
                    logger.info(f"  Total: {result['total']}")
                    logger.info(f"  Sent: {result['sent']}")
                    logger.info(f"  Failed: {result['failed']}")
                    logger.info(f"  Skipped: {result['skipped']}")
                    
                    if result['details']:
                        logger.debug("  Details:")
                        for detail in result['details']:
                            logger.debug(f"    {detail['guest']}: {detail['status']} - {detail['message']}")
            else:
                logger.info("No reminders scheduled for today.")
            
            logger.info("\n✅ Scheduled reminder run completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error during scheduled reminder run: {str(e)}", exc_info=True)
            sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Scheduled reminder run finished")
    logger.info("=" * 60)


def check_configuration():
    """Check if the configuration is properly set up for reminders."""
    logger.info("Checking configuration...")
    
    required_vars = [
        'DATABASE_URL',
        'ADMIN_EMAIL',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'RSVP_DEADLINE',
        'WEDDING_DATE'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
            logger.warning(f"  ⚠️  {var} is not configured")
        else:
            logger.info(f"  ✅ {var} is configured")
    
    if missing:
        logger.error(f"\n❌ Missing required configuration: {', '.join(missing)}")
        logger.error("Please configure these variables in your .env file")
        return False
    
    # Check email configuration
    mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = os.getenv('MAIL_PORT', '587')
    logger.info(f"\n📧 Email Configuration:")
    logger.info(f"  Server: {mail_server}:{mail_port}")
    logger.info(f"  Username: {os.getenv('MAIL_USERNAME')}")
    
    # Check RSVP deadline
    deadline = os.getenv('RSVP_DEADLINE')
    try:
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
        days_until_deadline = (deadline_date - datetime.now().date()).days
        logger.info(f"\n📅 RSVP Deadline: {deadline_date} ({days_until_deadline} days from now)")
        
        if days_until_deadline < 0:
            logger.warning("  ⚠️  RSVP deadline has already passed!")
            return False
        
    except ValueError:
        logger.error(f"  ❌ Invalid RSVP_DEADLINE format: {deadline}")
        logger.error("  Expected format: YYYY-MM-DD")
        return False
    
    return True


def dry_run():
    """
    Perform a dry run to show what would be sent without actually sending.
    """
    logger.info("\n🔍 DRY RUN MODE - No emails will be sent")
    
    app = create_app()
    
    with app.app_context():
        from app.models.reminder import ReminderType
        
        for reminder_type in [
            ReminderType.INITIAL,
            ReminderType.FIRST_FOLLOWUP,
            ReminderType.SECOND_FOLLOWUP,
            ReminderType.FINAL
        ]:
            should_send = ReminderService.should_send_reminder_today(reminder_type)
            
            if should_send:
                guests = ReminderService.get_guests_needing_reminder(reminder_type)
                
                logger.info(f"\n📧 {reminder_type.upper()} Reminder:")
                logger.info(f"  Would send to {len(guests)} guests:")
                
                for guest in guests[:5]:  # Show first 5 as example
                    logger.info(f"    - {guest.name} ({guest.email or 'no email'})")
                
                if len(guests) > 5:
                    logger.info(f"    ... and {len(guests) - 5} more")
            else:
                logger.info(f"\n⏭️  {reminder_type.upper()} Reminder: Not scheduled for today")


def main():
    """Main entry point for the scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Wedding RSVP Reminder Scheduler')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be sent without sending')
    parser.add_argument('--check', action='store_true',
                       help='Check configuration only')
    parser.add_argument('--force', action='store_true',
                       help='Force run even if not scheduled')
    
    args = parser.parse_args()
    
    # Always check configuration first
    if not check_configuration():
        logger.error("\n❌ Configuration check failed. Exiting.")
        sys.exit(1)
    
    logger.info("\n✅ Configuration check passed")
    
    if args.check:
        # Just check configuration and exit
        logger.info("\nConfiguration check complete. Use --dry-run or no args to run scheduler.")
        sys.exit(0)
    
    if args.dry_run:
        # Perform dry run
        dry_run()
    else:
        # Run actual scheduler
        run_scheduled_reminders()
    
    logger.info("\n✅ Scheduler completed successfully")


if __name__ == "__main__":
    main()