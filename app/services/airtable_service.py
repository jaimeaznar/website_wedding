# app/services/airtable_service.py
"""
Airtable integration service for wedding guest management.

This service handles:
- Reading guests from Airtable
- Syncing guests between Airtable and local database
- Updating RSVP status in Airtable when guests respond
- Tracking reminder dates in Airtable
- Generating and storing tokens for RSVP links
"""

import os
import secrets
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AirtableStatus(str, Enum):
    """RSVP status values in Airtable."""
    PENDING = "Pending"
    ATTENDING = "Attending"
    DECLINED = "Declined"
    CANCELLED = "Cancelled"


class ReminderField(str, Enum):
    """Reminder field names in Airtable."""
    REMINDER_1 = "Reminder 1"  # 30 days
    REMINDER_2 = "Reminder 2"  # 14 days
    REMINDER_3 = "Reminder 3"  # 7 days
    REMINDER_4 = "Reminder 4"  # 3 days


@dataclass
class AirtableGuest:
    """Data class representing a guest record from Airtable."""
    record_id: str
    name: str
    phone: str
    language: str
    token: Optional[str]
    status: str
    rsvp_date: Optional[datetime]
    adults_count: Optional[int]
    children_count: Optional[int]
    hotel: Optional[str]
    dietary_notes: Optional[str]
    transport_church: bool
    transport_reception: bool
    transport_hotel: bool
    link_sent: Optional[datetime]
    reminder_1: Optional[datetime]
    reminder_2: Optional[datetime]
    reminder_3: Optional[datetime]
    reminder_4: Optional[datetime]
    
    @classmethod
    def from_airtable_record(cls, record: Dict[str, Any]) -> 'AirtableGuest':
        """Create AirtableGuest from Airtable API response record."""
        fields = record.get('fields', {})
        
        def parse_date(date_str: Optional[str]) -> Optional[datetime]:
            """Parse ISO date string from Airtable."""
            if not date_str:
                return None
            try:
                # Airtable returns dates as ISO strings
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return None
        
        return cls(
            record_id=record['id'],
            name=fields.get('Name', ''),
            phone=fields.get('Phone', ''),
            language=fields.get('Language', 'es'),
            token=fields.get('Token'),
            status=fields.get('Status', AirtableStatus.PENDING),
            rsvp_date=parse_date(fields.get('RSVP Date')),
            adults_count=fields.get('Adults Count'),
            children_count=fields.get('Children Count'),
            hotel=fields.get('Hotel'),
            dietary_notes=fields.get('Dietary Notes'),
            transport_church=fields.get('Transport Church', False),
            transport_reception=fields.get('Transport Reception', False),
            transport_hotel=fields.get('Transport Hotel', False),
            link_sent=parse_date(fields.get('Link Sent')),
            reminder_1=parse_date(fields.get('Reminder 1')),
            reminder_2=parse_date(fields.get('Reminder 2')),
            reminder_3=parse_date(fields.get('Reminder 3')),
            reminder_4=parse_date(fields.get('Reminder 4')),
        )


class AirtableService:
    """
    Service for interacting with Airtable API.
    
    Manages guest data synchronization between Airtable and the local database.
    """
    
    def __init__(self):
        """Initialize Airtable service with credentials from environment."""
        self.api_key = os.environ.get('AIRTABLE_API_KEY')
        self.base_id = os.environ.get('AIRTABLE_BASE_ID')
        self.table_name = os.environ.get('AIRTABLE_TABLE_NAME', 'Guests')
        
        self._client = None
        self._table = None
    
    @property
    def is_configured(self) -> bool:
        """Check if Airtable credentials are configured."""
        return bool(self.api_key and self.base_id)
    
    @property
    def table(self):
        """Lazy-load Airtable table client."""
        if self._table is None:
            if not self.is_configured:
                raise ValueError(
                    "Airtable is not configured. "
                    "Please set AIRTABLE_API_KEY and AIRTABLE_BASE_ID environment variables."
                )
            
            try:
                from pyairtable import Api
                api = Api(self.api_key)
                self._table = api.table(self.base_id, self.table_name)
                logger.info(f"Connected to Airtable base {self.base_id}, table {self.table_name}")
            except ImportError:
                raise ImportError(
                    "pyairtable is not installed. "
                    "Run: pip install pyairtable"
                )
        
        return self._table
    
    # =========================================================================
    # READ OPERATIONS
    # =========================================================================
    
    def get_all_guests(self) -> List[AirtableGuest]:
        """
        Fetch all guests from Airtable.
        
        Returns:
            List of AirtableGuest objects
        """
        try:
            records = self.table.all()
            guests = [AirtableGuest.from_airtable_record(r) for r in records]
            logger.info(f"Fetched {len(guests)} guests from Airtable")
            return guests
        except Exception as e:
            logger.error(f"Failed to fetch guests from Airtable: {e}")
            raise
    
    def get_guest_by_phone(self, phone: str) -> Optional[AirtableGuest]:
        """
        Find a guest by phone number.
        
        Args:
            phone: Phone number to search (with country code)
            
        Returns:
            AirtableGuest or None
        """
        try:
            # Airtable formula to match phone
            formula = f"{{Phone}} = '{phone}'"
            records = self.table.all(formula=formula)
            
            if records:
                return AirtableGuest.from_airtable_record(records[0])
            return None
        except Exception as e:
            logger.error(f"Failed to find guest by phone: {e}")
            raise
    
    def get_guest_by_token(self, token: str) -> Optional[AirtableGuest]:
        """
        Find a guest by their RSVP token.
        
        Args:
            token: Unique RSVP token
            
        Returns:
            AirtableGuest or None
        """
        try:
            formula = f"{{Token}} = '{token}'"
            records = self.table.all(formula=formula)
            
            if records:
                return AirtableGuest.from_airtable_record(records[0])
            return None
        except Exception as e:
            logger.error(f"Failed to find guest by token: {e}")
            raise
    
    def get_guests_pending_rsvp(self) -> List[AirtableGuest]:
        """
        Get all guests who haven't responded yet.
        
        Returns:
            List of guests with Pending status
        """
        try:
            formula = f"{{Status}} = '{AirtableStatus.PENDING}'"
            records = self.table.all(formula=formula)
            guests = [AirtableGuest.from_airtable_record(r) for r in records]
            logger.info(f"Found {len(guests)} guests with pending RSVP")
            return guests
        except Exception as e:
            logger.error(f"Failed to fetch pending guests: {e}")
            raise
    
    def get_guests_needing_link(self) -> List[AirtableGuest]:
        """
        Get guests who need their RSVP link sent (have token but Link Sent is empty).
        
        Returns:
            List of guests needing link sent
        """
        try:
            # Has token but link not sent yet
            formula = "AND({Token} != '', {Link Sent} = '')"
            records = self.table.all(formula=formula)
            guests = [AirtableGuest.from_airtable_record(r) for r in records]
            logger.info(f"Found {len(guests)} guests needing RSVP link")
            return guests
        except Exception as e:
            logger.error(f"Failed to fetch guests needing link: {e}")
            raise
    
    def get_guests_needing_reminder(self, reminder_number: int) -> List[AirtableGuest]:
        """
        Get guests who need a specific reminder.
        
        Args:
            reminder_number: 1, 2, 3, or 4 (corresponding to 30, 14, 7, 3 days)
            
        Returns:
            List of guests needing this reminder
        """
        try:
            reminder_field = f"Reminder {reminder_number}"
            # Status is Pending AND this reminder hasn't been sent
            formula = f"AND({{Status}} = '{AirtableStatus.PENDING}', {{{reminder_field}}} = BLANK())"
            records = self.table.all(formula=formula)
            guests = [AirtableGuest.from_airtable_record(r) for r in records]
            logger.info(f"Found {len(guests)} guests needing reminder {reminder_number}")
            return guests
        except Exception as e:
            logger.error(f"Failed to fetch guests needing reminder: {e}")
            raise
    
    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================
    
    def generate_token_for_guest(self, record_id: str) -> str:
        """
        Generate and save a unique token for a guest.
        
        Args:
            record_id: Airtable record ID
            
        Returns:
            The generated token
        """
        try:
            # Generate unique token
            token = secrets.token_urlsafe(32)
            
            # Ensure uniqueness
            while self.get_guest_by_token(token):
                token = secrets.token_urlsafe(32)
            
            # Update Airtable record
            self.table.update(record_id, {'Token': token})
            logger.info(f"Generated token for record {record_id}")
            
            return token
        except Exception as e:
            logger.error(f"Failed to generate token: {e}")
            raise
    
    def generate_tokens_for_all(self) -> Dict[str, str]:
        """
        Generate tokens for all guests who don't have one.
        
        Returns:
            Dict mapping record_id to generated token
        """
        try:
            # Find guests without tokens
            formula = "OR({Token} = '', {Token} = BLANK())"
            records = self.table.all(formula=formula)
            
            results = {}
            for record in records:
                record_id = record['id']
                token = self.generate_token_for_guest(record_id)
                results[record_id] = token
            
            logger.info(f"Generated tokens for {len(results)} guests")
            return results
        except Exception as e:
            logger.error(f"Failed to generate tokens for all: {e}")
            raise
    
    def update_link_sent(self, record_id: str, sent_at: Optional[datetime] = None) -> None:
        """
        Mark that the RSVP link was sent to a guest.
        
        Args:
            record_id: Airtable record ID
            sent_at: When the link was sent (defaults to now)
        """
        try:
            sent_at = sent_at or datetime.now()
            self.table.update(record_id, {
                'Link Sent': sent_at.isoformat()
            })
            logger.info(f"Updated Link Sent for record {record_id}")
        except Exception as e:
            logger.error(f"Failed to update Link Sent: {e}")
            raise
    
    def update_reminder_sent(
        self, 
        record_id: str, 
        reminder_number: int,
        sent_at: Optional[datetime] = None
    ) -> None:
        """
        Mark that a reminder was sent to a guest.
        
        Args:
            record_id: Airtable record ID
            reminder_number: Which reminder (1, 2, 3, or 4)
            sent_at: When the reminder was sent (defaults to now)
        """
        try:
            sent_at = sent_at or datetime.now()
            reminder_field = f"Reminder {reminder_number}"
            
            self.table.update(record_id, {
                reminder_field: sent_at.isoformat()
            })
            logger.info(f"Updated {reminder_field} for record {record_id}")
        except Exception as e:
            logger.error(f"Failed to update reminder: {e}")
            raise
    
    def update_rsvp_status(
        self,
        record_id: str,
        status: AirtableStatus,
        rsvp_date: Optional[datetime] = None,
        adults_count: Optional[int] = None,
        children_count: Optional[int] = None,
        hotel: Optional[str] = None,
        dietary_notes: Optional[str] = None,
        transport_church: Optional[bool] = None,
        transport_reception: Optional[bool] = None,
        transport_hotel: Optional[bool] = None,
    ) -> None:
        """
        Update RSVP information in Airtable when a guest responds.
        
        Args:
            record_id: Airtable record ID
            status: New status (Attending, Declined, Cancelled)
            rsvp_date: When the RSVP was submitted
            adults_count: Number of adults attending
            children_count: Number of children attending
            hotel: Hotel name
            dietary_notes: Dietary restrictions/notes
            transport_church: Needs transport to church
            transport_reception: Needs transport to reception
            transport_hotel: Needs transport back to hotel
        """
        try:
            rsvp_date = rsvp_date or datetime.now()
            
            fields = {
                'Status': status.value,
                'RSVP Date': rsvp_date.strftime('%Y-%m-%d'),
            }
            
            # Only update optional fields if provided
            if adults_count is not None:
                fields['Adults Count'] = adults_count
            if children_count is not None:
                fields['Children Count'] = children_count
            if hotel is not None:
                fields['Hotel'] = hotel
            if dietary_notes is not None:
                fields['Dietary Notes'] = dietary_notes
            if transport_church is not None:
                fields['Transport Church'] = transport_church
            if transport_reception is not None:
                fields['Transport Reception'] = transport_reception
            if transport_hotel is not None:
                fields['Transport Hotel'] = transport_hotel
            
            self.table.update(record_id, fields)
            logger.info(f"Updated RSVP status to {status.value} for record {record_id}")
        except Exception as e:
            logger.error(f"Failed to update RSVP status: {e}")
            raise
    
    def mark_attending(
        self,
        record_id: str,
        adults_count: int = 1,
        children_count: int = 0,
        hotel: Optional[str] = None,
        dietary_notes: Optional[str] = None,
        transport_church: bool = False,
        transport_reception: bool = False,
        transport_hotel: bool = False,
    ) -> None:
        """Convenience method to mark a guest as attending."""
        self.update_rsvp_status(
            record_id=record_id,
            status=AirtableStatus.ATTENDING,
            adults_count=adults_count,
            children_count=children_count,
            hotel=hotel,
            dietary_notes=dietary_notes,
            transport_church=transport_church,
            transport_reception=transport_reception,
            transport_hotel=transport_hotel,
        )
    
    def mark_declined(self, record_id: str) -> None:
        """Convenience method to mark a guest as declined."""
        self.update_rsvp_status(
            record_id=record_id,
            status=AirtableStatus.DECLINED,
        )
    
    def mark_cancelled(self, record_id: str) -> None:
        """Convenience method to mark a guest as cancelled."""
        self.update_rsvp_status(
            record_id=record_id,
            status=AirtableStatus.CANCELLED,
        )
    
    # =========================================================================
    # SYNC OPERATIONS
    # =========================================================================
    
    def sync_guest_to_local_db(self, airtable_guest: AirtableGuest) -> 'Guest':
        """
        Sync a single Airtable guest to the local database.
        
        Creates or updates the guest and their RSVP in the local DB.
        
        Args:
            airtable_guest: Guest data from Airtable
            
        Returns:
            Local Guest object
        """
        from app import db
        from app.models.guest import Guest
        from app.models.rsvp import RSVP
        
        # Try to find existing guest by token or phone
        local_guest = None
        if airtable_guest.token:
            local_guest = Guest.query.filter_by(token=airtable_guest.token).first()
        if not local_guest and airtable_guest.phone:
            local_guest = Guest.query.filter_by(phone=airtable_guest.phone).first()
        
        if local_guest:
            # Update existing guest
            local_guest.name = airtable_guest.name
            local_guest.phone = airtable_guest.phone
            local_guest.language_preference = airtable_guest.language
            if airtable_guest.token:
                local_guest.token = airtable_guest.token
            logger.debug(f"Updated local guest: {local_guest.name}")
        else:
            # Create new guest
            token = airtable_guest.token or secrets.token_urlsafe(32)
            local_guest = Guest(
                name=airtable_guest.name,
                phone=airtable_guest.phone,
                token=token,
                language_preference=airtable_guest.language,
            )
            db.session.add(local_guest)
            db.session.flush()  # Get the guest ID
            logger.debug(f"Created local guest: {local_guest.name}")
        
        # Sync RSVP status if not Pending
        if airtable_guest.status and airtable_guest.status != AirtableStatus.PENDING:
            rsvp = RSVP.query.filter_by(guest_id=local_guest.id).first()
            
            if not rsvp:
                rsvp = RSVP(guest_id=local_guest.id)
                db.session.add(rsvp)
            
            # Set RSVP fields based on Airtable status
            if airtable_guest.status == AirtableStatus.ATTENDING:
                rsvp.is_attending = True
                rsvp.is_cancelled = False
            elif airtable_guest.status == AirtableStatus.DECLINED:
                rsvp.is_attending = False
                rsvp.is_cancelled = False
            elif airtable_guest.status == AirtableStatus.CANCELLED:
                rsvp.is_attending = False
                rsvp.is_cancelled = True
                rsvp.cancellation_date = airtable_guest.rsvp_date or datetime.now()
            
            # Sync other RSVP fields
            if airtable_guest.hotel:
                rsvp.hotel_name = airtable_guest.hotel
            if airtable_guest.adults_count is not None:
                rsvp.adults_count = airtable_guest.adults_count
            if airtable_guest.children_count is not None:
                rsvp.children_count = airtable_guest.children_count
            rsvp.transport_to_church = airtable_guest.transport_church
            rsvp.transport_to_reception = airtable_guest.transport_reception
            rsvp.transport_to_hotel = airtable_guest.transport_hotel
            
            if airtable_guest.rsvp_date:
                rsvp.created_at = airtable_guest.rsvp_date
                rsvp.last_updated = airtable_guest.rsvp_date
            
            logger.debug(f"Synced RSVP status for {local_guest.name}: {airtable_guest.status}")
        
        db.session.commit()
        return local_guest
    
    def sync_all_to_local_db(self) -> Tuple[int, int]:
        """
        Sync all Airtable guests to the local database.
        
        Returns:
            Tuple of (created_count, updated_count)
        """
        from app import db
        from app.models.guest import Guest
        
        airtable_guests = self.get_all_guests()
        
        created = 0
        updated = 0
        
        for ag in airtable_guests:
            # Check if exists
            existing = None
            if ag.token:
                existing = Guest.query.filter_by(token=ag.token).first()
            if not existing and ag.phone:
                existing = Guest.query.filter_by(phone=ag.phone).first()
            
            self.sync_guest_to_local_db(ag)
            
            if existing:
                updated += 1
            else:
                created += 1
        
        logger.info(f"Synced from Airtable: {created} created, {updated} updated")
        return created, updated
    
    def sync_rsvp_to_airtable(self, token: str) -> None:
        """
        Sync local RSVP data back to Airtable.
        
        Call this after an RSVP is submitted through the website.
        
        Args:
            token: Guest's RSVP token
        """
        from app.models.guest import Guest
        from app.models.rsvp import RSVP
        from app.models.allergen import GuestAllergen
        
        # Get local guest and RSVP
        local_guest = Guest.query.filter_by(token=token).first()
        if not local_guest:
            logger.warning(f"No local guest found with token {token}")
            return
        
        rsvp = RSVP.query.filter_by(guest_id=local_guest.id).first()
        if not rsvp:
            logger.warning(f"No RSVP found for guest {local_guest.name}")
            return
        
        # Find Airtable record
        airtable_guest = self.get_guest_by_token(token)
        if not airtable_guest:
            logger.warning(f"No Airtable record found with token {token}")
            return
        
        # Determine status
        if rsvp.is_cancelled:
            status = AirtableStatus.CANCELLED
        elif rsvp.is_attending:
            status = AirtableStatus.ATTENDING
        else:
            status = AirtableStatus.DECLINED
        
        # Gather dietary notes
        dietary_notes = ""
        allergens = GuestAllergen.query.filter_by(rsvp_id=rsvp.id).all()
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
        
        # Update Airtable
        self.update_rsvp_status(
            record_id=airtable_guest.record_id,
            status=status,
            rsvp_date=rsvp.created_at,
            adults_count=adults,
            children_count=children,
            hotel=rsvp.hotel_name,
            dietary_notes=dietary_notes,
            transport_church=rsvp.transport_to_church,
            transport_reception=rsvp.transport_to_reception,
            transport_hotel=rsvp.transport_to_hotel,
        )
        
        logger.info(f"Synced RSVP for {local_guest.name} to Airtable")
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics from Airtable.
        
        Returns:
            Dictionary with guest/RSVP statistics
        """
        try:
            all_guests = self.get_all_guests()
            
            stats = {
                'total_guests': len(all_guests),
                'pending': 0,
                'attending': 0,
                'declined': 0,
                'cancelled': 0,
                'total_people': 0,
                'links_sent': 0,
                'links_not_sent': 0,
            }
            
            for guest in all_guests:
                if guest.status == AirtableStatus.PENDING:
                    stats['pending'] += 1
                elif guest.status == AirtableStatus.ATTENDING:
                    stats['attending'] += 1
                    # Count total people
                    stats['total_people'] += (guest.adults_count or 1) + (guest.children_count or 0)
                elif guest.status == AirtableStatus.DECLINED:
                    stats['declined'] += 1
                elif guest.status == AirtableStatus.CANCELLED:
                    stats['cancelled'] += 1
                
                if guest.link_sent:
                    stats['links_sent'] += 1
                elif guest.token:
                    stats['links_not_sent'] += 1
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise


# Singleton instance for easy access
_airtable_service: Optional[AirtableService] = None


def get_airtable_service() -> AirtableService:
    """Get the singleton AirtableService instance."""
    global _airtable_service
    if _airtable_service is None:
        _airtable_service = AirtableService()
    return _airtable_service