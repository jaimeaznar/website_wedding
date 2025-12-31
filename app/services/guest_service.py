# app/services/guest_service.py
import secrets
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.utils.import_guests import process_guest_csv
from app.constants import (GuestLimit, Language, LogMessage, ErrorMessage)

logger = logging.getLogger(__name__)


class GuestService:
    """Service class for handling guest-related business logic."""
    
    @staticmethod
    def create_guest(
        name: str,
        phone: str,
        language_preference: str = Language.DEFAULT
    ) -> Guest:
        """
        Create a new guest with a unique token.
        
        Args:
            name: Guest's full name
            phone: Guest's phone number
            language_preference: Preferred language (en/es)
            
        Returns:
            Guest: The created guest object
            
        Raises:
            ValueError: If required fields are missing
            IntegrityError: If guest with same phone exists
        """
        if not name or not phone:
            raise ValueError(ErrorMessage.MISSING_REQUIRED_FIELDS)
        
        if len(name) > GuestLimit.MAX_NAME_LENGTH:
            raise ValueError(f"Name exceeds maximum length of {GuestLimit.MAX_NAME_LENGTH} characters")
        if len(phone) > GuestLimit.MAX_PHONE_LENGTH:
            raise ValueError(f"Phone exceeds maximum length of {GuestLimit.MAX_PHONE_LENGTH} characters")
        
        # Generate unique token
        token = secrets.token_urlsafe(GuestLimit.TOKEN_LENGTH)
        
        # Ensure token is unique
        while Guest.query.filter_by(token=token).first():
            token = secrets.token_urlsafe(GuestLimit.TOKEN_LENGTH)
        
        guest = Guest(
            name=name.strip(),
            phone=phone.strip(),
            token=token,
            language_preference=language_preference
        )
        
        try:
            db.session.add(guest)
            db.session.commit()
            logger.info(LogMessage.GUEST_CREATED.format(name=guest.name, id=guest.id))
            return guest
        except IntegrityError as e:
            db.session.rollback()
            logger.error(LogMessage.ERROR_DATABASE.format(error=str(e)))
            raise
    
    @staticmethod
    def get_guest_by_token(token: str) -> Optional[Guest]:
        """
        Retrieve a guest by their unique token.
        
        Args:
            token: The guest's unique token
            
        Returns:
            Guest or None if not found
        """
        return Guest.query.filter_by(token=token).first()
    
    @staticmethod
    def get_guest_by_id(guest_id: int) -> Optional[Guest]:
        """
        Retrieve a guest by their ID.
        
        Args:
            guest_id: The guest's database ID
            
        Returns:
            Guest or None if not found
        """
        return Guest.query.get(guest_id)
    
    @staticmethod
    def find_guest_by_phone(phone: Optional[str] = None) -> Optional[Guest]:
        """
        Find a guest by phone number.
        
        Args:
            phone: Phone number to search
            
        Returns:
            Guest or None if not found
        """

        
        query = Guest.query
        
        if phone:
            return query.filter(
                (Guest.phone == phone)
            ).first()
        
        else:
            return query.filter_by(phone=phone).first()
    
    @staticmethod
    def get_all_guests() -> List[Guest]:
        """
        Retrieve all guests.
        
        Returns:
            List of all guests
        """
        return Guest.query.all()
    
    @staticmethod
    def get_guest_statistics() -> Dict[str, Any]:
        """
        Calculate statistics about guests and RSVPs.
        
        Returns:
            Dictionary containing guest statistics
        """
        guests = Guest.query.all()
        rsvps = RSVP.query.all()
        
        total_guests = len(guests)
        total_people_attending = 0
        transport_stats = {
            'to_church': 0,
            'to_reception': 0,
            'to_hotel': 0,
            'hotels': set()
        }
        
        responses_received = 0
        attending_count = 0
        declined_count = 0
        cancelled_count = 0
        
        for rsvp in rsvps:
            if rsvp.is_cancelled:
                cancelled_count += 1
            else:
                responses_received += 1
                
                if rsvp.is_attending:
                    attending_count += 1
                    # Count main guest + additional guests
                    total_people_attending += 1 + len(rsvp.additional_guests)
                    
                    # Count transport needs
                    if rsvp.transport_to_reception:
                        transport_stats['to_reception'] += 1
                    if rsvp.transport_to_hotel:
                        transport_stats['to_hotel'] += 1
                    
                    # Add hotel to set if specified
                    if rsvp.hotel_name:
                        transport_stats['hotels'].add(rsvp.hotel_name)
                else:
                    declined_count += 1
        
        pending_count = total_guests - responses_received - cancelled_count
        
        return {
            'total_guests': total_guests,
            'total_attending': total_people_attending,
            'responses_received': responses_received,
            'attending_count': attending_count,
            'declined_count': declined_count,
            'pending_count': pending_count,
            'cancelled_count': cancelled_count,
            'transport_stats': transport_stats
        }
    
    @staticmethod
    def import_guests_from_csv(file_content: bytes) -> List[Guest]:
        """
        Import guests from a CSV file.
        
        Args:
            file_content: CSV file content as bytes
            
        Returns:
            List of created guests
            
        Raises:
            ValueError: If CSV format is invalid
            IntegrityError: If duplicate guests found
        """
        try:
            # Process CSV to get guest objects
            guests = process_guest_csv(file_content)
            
            # Add all guests to session
            for guest in guests:
                db.session.add(guest)
            
            # Commit all at once
            db.session.commit()
            logger.info(f"Successfully imported {len(guests)} guests")
            
            return guests
        except (ValueError, IntegrityError) as e:
            db.session.rollback()
            logger.error(f"Failed to import guests: {str(e)}")
            raise
    
    @staticmethod
    def update_guest(
        guest_id: int,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        language_preference: Optional[str] = None
    ) -> Guest:
        """
        Update guest information.
        
        Args:
            guest_id: ID of guest to update
            name: New name (optional)
            phone: New phone (optional)
            language_preference: New language preference (optional)
            
        Returns:
            Updated guest object
            
        Raises:
            ValueError: If guest not found
        """
        guest = Guest.query.get(guest_id)
        if not guest:
            raise ValueError(f"Guest with ID {guest_id} not found")
        
        # Update fields if provided
        if name is not None:
            guest.name = name.strip()
        if phone is not None:
            guest.phone = phone.strip()
        if language_preference is not None:
            guest.language_preference = language_preference
        
        try:
            db.session.commit()
            logger.info(f"Updated guest: {guest.name} (ID: {guest.id})")
            return guest
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Failed to update guest {guest_id}: {str(e)}")
            raise
    
    @staticmethod
    def delete_guest(guest_id: int) -> bool:
        """
        Delete a guest and their associated RSVP.
        
        Args:
            guest_id: ID of guest to delete
            
        Returns:
            True if deleted, False if not found
        """
        guest = Guest.query.get(guest_id)
        if not guest:
            return False
        
        try:
            # The cascade delete should handle RSVP removal
            db.session.delete(guest)
            db.session.commit()
            logger.info(f"Deleted guest: {guest.name} (ID: {guest_id})")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete guest {guest_id}: {str(e)}")
            raise