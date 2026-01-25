#!/usr/bin/env python3
"""
Generate personalized WhatsApp invitation messages for all guests.

This script reads guests from Airtable and generates a personalized
invitation message for each guest, storing it in the "Personal Message" column.

Usage:
    python generate_personal_messages.py [--dry-run] [--preview-only]

Options:
    --dry-run       Generate messages but don't update Airtable (shows what would be done)
    --preview-only  Only show a preview of 3 messages, don't process all guests
"""

import os
import sys
import argparse
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# =============================================================================
# MESSAGE TEMPLATES
# =============================================================================

# Base URL for generating RSVP links
BASE_URL = "https://wedding.aznarroa.com"

# Spanish template
TEMPLATE_ES = """
🎊 *¡Querido {name}!*

Irene y yo tenemos el placer de invitarte a nuestra boda, que celebraremos el 6 de junio de 2026.

Por favor, confirma tu asistencia antes del 6 de mayo de 2026 en este enlace personal e intransferible:

👉 {rsvp_link} 

Descubre todos los detalles de la boda en nuestra web:

🌐 https://wedding.aznarroa.com

¡Esperamos verte allí! 💒

P.D.: En breve recibirás también nuestra invitación impresa. ✉️

"""



# English template
TEMPLATE_EN = """
🎊 *Hello {name}!*

Irene and I have the pleasure of inviting you to our wedding, which will be held on June 6th, 2026.

Kindly confirm your attendance before May 6th, 2026 through this personal link:

👉 {rsvp_link}

All the information is available on our website:

🌐 https://wedding.aznarroa.com

We very much hope you can join us on this special day. 💒

P.S.: You will be receiving our printed invitation soon. ✉️

"""

# Template mapping
TEMPLATES: Dict[str, str] = {
    'es': TEMPLATE_ES,
    'en': TEMPLATE_EN,
}


# =============================================================================
# MESSAGE GENERATION
# =============================================================================

def generate_rsvp_link(token: str) -> str:
    """Generate the RSVP link from a token."""
    return f"{BASE_URL}/?token={token}"


def generate_personal_message(
    name: str,
    token: str,
    language: str = 'es'
) -> str:
    """
    Generate a personalized invitation message for a guest.
    
    Args:
        name: Guest's name (first name)
        token: RSVP token for generating the unique link
        language: 'es' for Spanish, 'en' for English
        
    Returns:
        Formatted message string
    """
    # Default to Spanish if language not recognized
    template = TEMPLATES.get(language.lower(), TEMPLATES['es'])
    
    # Generate the RSVP link
    rsvp_link = generate_rsvp_link(token)
    
    # Format the message
    message = template.format(
        name=name,
        rsvp_link=rsvp_link
    )
    
    return message


# =============================================================================
# AIRTABLE INTEGRATION
# =============================================================================

def get_airtable_table():
    """Initialize and return the Airtable table client."""
    try:
        from pyairtable import Api
    except ImportError:
        print("Error: pyairtable is not installed.")
        print("Run: pip install pyairtable")
        sys.exit(1)
    
    api_key = os.environ.get('AIRTABLE_API_KEY')
    base_id = os.environ.get('AIRTABLE_BASE_ID')
    table_name = os.environ.get('AIRTABLE_TABLE_NAME', 'Guests')
    
    if not api_key or not base_id:
        print("Error: Airtable credentials not configured.")
        print("Please set AIRTABLE_API_KEY and AIRTABLE_BASE_ID environment variables.")
        sys.exit(1)
    
    api = Api(api_key)
    return api.table(base_id, table_name)


def fetch_all_guests(table) -> list:
    """Fetch all guest records from Airtable."""
    print("Fetching guests from Airtable...")
    records = table.all()
    print(f"Found {len(records)} guests")
    return records


def update_personal_message(table, record_id: str, message: str) -> bool:
    """
    Update the Personal Message field for a guest in Airtable.
    
    Args:
        table: Airtable table client
        record_id: Airtable record ID
        message: The personalized message to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        table.update(record_id, {'Personal Message': message})
        return True
    except Exception as e:
        print(f"  Error updating record: {e}")
        return False


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_guests(dry_run: bool = False, preview_only: bool = False):
    """
    Process all guests and generate personal messages.
    
    Args:
        dry_run: If True, don't actually update Airtable
        preview_only: If True, only show preview of first 3 guests
    """
    # Get Airtable table
    table = get_airtable_table()
    
    # Fetch all guests
    records = fetch_all_guests(table)
    
    if not records:
        print("No guests found in Airtable.")
        return
    
    # Statistics
    stats = {
        'processed': 0,
        'updated': 0,
        'skipped_no_token': 0,
        'skipped_no_name': 0,
        'errors': 0,
    }
    
    # Limit for preview mode
    if preview_only:
        records = records[:3]
        print(f"\n📝 PREVIEW MODE - Showing first {len(records)} guests\n")
    
    print("-" * 60)
    
    for record in records:
        record_id = record['id']
        fields = record.get('fields', {})
        
        # Extract guest data
        name = fields.get('Name', '').strip()
        surname = fields.get('Surname', '').strip()
        token = fields.get('Token', '').strip()
        language = fields.get('Language', 'es').strip().lower()
        current_message = fields.get('Personal Message', '')
        
        # Display name for logging
        display_name = f"{name} {surname}".strip() or f"[Record: {record_id}]"
        
        # Validation
        if not token:
            print(f"⚠️  {display_name}: Skipping - no token")
            stats['skipped_no_token'] += 1
            continue
        
        if not name:
            print(f"⚠️  {display_name}: Skipping - no name")
            stats['skipped_no_name'] += 1
            continue
        
        # Generate the personalized message
        message = generate_personal_message(
            name=name,
            token=token,
            language=language
        )
        
        stats['processed'] += 1
        
        # Preview mode: show message
        if preview_only:
            print(f"\n👤 {display_name} ({language.upper()})")
            print("-" * 40)
            print(message)
            print("-" * 40)
            continue
        
        # Dry run or actual update
        if dry_run:
            print(f"✓ {display_name} ({language.upper()}): Would generate message")
        else:
            if update_personal_message(table, record_id, message):
                print(f"✅ {display_name} ({language.upper()}): Message updated")
                stats['updated'] += 1
            else:
                print(f"❌ {display_name}: Failed to update")
                stats['errors'] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total guests:       {len(records)}")
    print(f"Processed:          {stats['processed']}")
    
    if not preview_only:
        if dry_run:
            print(f"Would update:       {stats['processed']}")
        else:
            print(f"Updated:            {stats['updated']}")
        
        print(f"Skipped (no token): {stats['skipped_no_token']}")
        print(f"Skipped (no name):  {stats['skipped_no_name']}")
        print(f"Errors:             {stats['errors']}")
    
    if dry_run:
        print("\n⚠️  DRY RUN - No changes were made to Airtable")
        print("   Run without --dry-run to update records")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate personalized WhatsApp invitation messages for wedding guests.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview first 3 messages without updating
    python generate_personal_messages.py --preview-only
    
    # See what would be updated without making changes
    python generate_personal_messages.py --dry-run
    
    # Actually update all messages in Airtable
    python generate_personal_messages.py
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate messages but do not update Airtable'
    )
    
    parser.add_argument(
        '--preview-only',
        action='store_true',
        help='Only show preview of first 3 messages'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("WEDDING INVITATION MESSAGE GENERATOR")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'Preview' if args.preview_only else 'Dry Run' if args.dry_run else 'Live Update'}")
    print()
    
    try:
        process_guests(
            dry_run=args.dry_run,
            preview_only=args.preview_only
        )
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()