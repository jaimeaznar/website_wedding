# app/services/rsvp_service.py
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple, List
from flask import current_app
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP, AdditionalGuest
from app.models.allergen import GuestAllergen
from app.services.allergen_service import AllergenService
from app.constants import (
    DateFormat, LogMessage, DEFAULT_CONFIG
)

logger = logging.getLogger(__name__)


class RSVPService:
    """Service class for handling RSVP-related business logic."""
    
    @staticmethod
    def get_rsvp_by_guest_id(guest_id: int) -> Optional[RSVP]:
        """Get RSVP for a specific guest."""
        return RSVP.query.filter_by(guest_id=guest_id).first()
    
    @staticmethod
    def is_rsvp_deadline_passed() -> bool:
        """Check if the RSVP deadline has passed."""
        rsvp_deadline_str = current_app.config.get('RSVP_DEADLINE', DEFAULT_CONFIG['RSVP_DEADLINE'])
        if not rsvp_deadline_str:
            return False
        
        try:
            rsvp_deadline = datetime.strptime(rsvp_deadline_str, DateFormat.DATABASE).date()
            today = date.today()
            return today > rsvp_deadline
        except (ValueError, TypeError):
            logger.error(LogMessage.ERROR_VALIDATION.format(error=f"Invalid RSVP_DEADLINE format: {rsvp_deadline_str}"))
            return False
    
    @staticmethod
    def get_rsvp_deadline_formatted() -> str:
        """Get formatted RSVP deadline for display."""
        rsvp_deadline_str = current_app.config.get('RSVP_DEADLINE', DEFAULT_CONFIG['RSVP_DEADLINE'])
        if not rsvp_deadline_str:
            return "Not specified"
        
        try:
            rsvp_deadline = datetime.strptime(rsvp_deadline_str, DateFormat.DATABASE).date()
            return rsvp_deadline.strftime(DateFormat.DISPLAY)
        except (ValueError, TypeError):
            return rsvp_deadline_str
    
    @staticmethod
    def _sync_to_airtable(guest: Guest) -> None:
        """
        Sync RSVP data to Airtable (if configured).
        
        This runs in a background-safe way - failures don't affect the main RSVP flow.
        
        Args:
            guest: The guest whose RSVP should be synced
        """
        try:
            from app.services.airtable_service import get_airtable_service
            
            airtable = get_airtable_service()
            
            # Check if Airtable is configured
            if not airtable.is_configured:
                logger.debug("Airtable not configured, skipping sync")
                return
            
            # Sync the RSVP to Airtable
            airtable.sync_rsvp_to_airtable(guest.token)
            logger.info(f"Synced RSVP for {guest.name} to Airtable")
            
        except ImportError:
            logger.debug("Airtable service not available, skipping sync")
        except Exception as e:
            # Log but don't fail - Airtable sync is optional
            logger.warning(f"Failed to sync RSVP to Airtable for {guest.name}: {e}")
    
    @staticmethod
    def create_or_update_rsvp(
        guest: Guest,
        form_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[RSVP]]:
        """
        Create or update an RSVP based on form data.
        
        Args:
            guest: The guest making the RSVP
            form_data: Dictionary containing form data
            
        Returns:
            Tuple of (success, message, rsvp_object)
        """
        try:
            # Check if RSVP deadline has passed
            if RSVPService.is_rsvp_deadline_passed():
                return False, "The RSVP deadline has passed.", None
            
            # Get or create RSVP
            rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
            if not rsvp:
                rsvp = RSVP(guest_id=guest.id)
                db.session.add(rsvp)
                db.session.flush()  # Get ID for new RSVP
            else:
                # Check if editable
                if not rsvp.is_editable:
                    return False, "This RSVP can no longer be edited.", rsvp
            
            # Update basic attendance
            is_attending = form_data.get('is_attending') == 'yes'
            rsvp.is_attending = is_attending
            
            # Clear existing data
            if rsvp.id:
                GuestAllergen.query.filter_by(rsvp_id=rsvp.id).delete()
                AdditionalGuest.query.filter_by(rsvp_id=rsvp.id).delete()
            
            # Process attendance details
            if is_attending:
                # Hotel and transport
                rsvp.hotel_name = form_data.get('hotel_name', '').strip() or None
                rsvp.transport_to_church = 'transport_to_church' in form_data
                rsvp.transport_to_reception = 'transport_to_reception' in form_data
                rsvp.transport_to_hotel = 'transport_to_hotel' in form_data
                
                # Process allergens for main guest
                AllergenService.process_guest_allergens(
                    rsvp.id, guest.name, form_data, 'main'
                )
                
                # Process plus one if applicable
                if guest.has_plus_one and not guest.is_family:
                    plus_one_name = form_data.get('plus_one_name', '').strip()
                    if plus_one_name:
                        rsvp.plus_one_name = plus_one_name
                        guest.plus_one_used = True
                        
                        # Create additional guest entry
                        plus_one = AdditionalGuest(
                            rsvp_id=rsvp.id,
                            name=plus_one_name,
                            is_child=False
                        )
                        db.session.add(plus_one)
                        
                        # Process allergens
                        AllergenService.process_guest_allergens(
                            rsvp.id, plus_one_name, form_data, 'plus_one'
                        )
                
                # Process family members if applicable
                if guest.is_family:
                    RSVPService._process_family_members(rsvp, form_data)
            else:
                # Reset fields for non-attending
                rsvp.hotel_name = None
                rsvp.transport_to_church = False
                rsvp.transport_to_reception = False
                rsvp.transport_to_hotel = False
                rsvp.adults_count = 0
                rsvp.children_count = 0
            
            # Update timestamp
            rsvp.last_updated = datetime.now()
            
            # Commit changes
            db.session.commit()
            
            message = "Your RSVP has been submitted successfully!"
            if not is_attending:
                message = "Your response has been recorded."
            
            logger.info(f"RSVP {'created' if not rsvp.id else 'updated'} for guest {guest.name}")
            
            # Sync to Airtable (async-safe, won't fail the main flow)
            RSVPService._sync_to_airtable(guest)
            
            return True, message, rsvp
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing RSVP for guest {guest.name}: {str(e)}", exc_info=True)
            return False, f"Error submitting RSVP: {str(e)}", None
    
    @staticmethod
    def _process_family_members(rsvp: RSVP, form_data: Dict[str, Any]) -> None:
        """Process family member information from form data."""
        try:
            rsvp.adults_count = int(form_data.get('adults_count', 0))
            rsvp.children_count = int(form_data.get('children_count', 0))
        except (ValueError, TypeError):
            rsvp.adults_count = 0
            rsvp.children_count = 0
        
        # Process adults
        for i in range(rsvp.adults_count):
            name = form_data.get(f'adult_name_{i}', '').strip()
            if name:
                guest_obj = AdditionalGuest(
                    rsvp_id=rsvp.id,
                    name=name,
                    is_child=False
                )
                db.session.add(guest_obj)
                
                # Process allergens
                AllergenService.process_guest_allergens(
                    rsvp.id, name, form_data, f'adult_{i}'
                )
        
        # Process children
        for i in range(rsvp.children_count):
            name = form_data.get(f'child_name_{i}', '').strip()
            if name:
                guest_obj = AdditionalGuest(
                    rsvp_id=rsvp.id,
                    name=name,
                    is_child=True
                )
                db.session.add(guest_obj)
                
                # Process allergens
                AllergenService.process_guest_allergens(
                    rsvp.id, name, form_data, f'child_{i}'
                )
    
    @staticmethod
    def cancel_rsvp(guest: Guest) -> Tuple[bool, str]:
        """
        Cancel an RSVP for a guest.
        
        Args:
            guest: The guest cancelling their RSVP
            
        Returns:
            Tuple of (success, message)
        """
        rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
        if not rsvp:
            return False, "No RSVP found to cancel."
        
        # Check if deadline passed
        if RSVPService.is_rsvp_deadline_passed():
            return False, "The RSVP deadline has passed. Please contact the wedding administrators."
        
        # Check if cancellation is allowed
        if not rsvp.is_editable:
            return False, "Cancellations are not possible at this time. Please contact the wedding administrators."
        
        # Perform cancellation
        rsvp.is_cancelled = True
        rsvp.is_attending = False
        rsvp.cancellation_date = datetime.now()
        
        # Support for test compatibility
        if hasattr(rsvp, 'cancelled_at'):
            rsvp.cancelled_at = rsvp.cancellation_date
        
        try:
            db.session.commit()
            
            
            logger.info(f"RSVP cancelled for guest {guest.name}")
            
            # Sync cancellation to Airtable
            RSVPService._sync_to_airtable(guest)
            
            return True, "Your RSVP has been cancelled."
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cancelling RSVP for guest {guest.name}: {str(e)}")
            return False, f"Error cancelling RSVP: {str(e)}"
    
    @staticmethod
    def get_rsvp_summary_for_guest(guest: Guest) -> Dict[str, Any]:
        """
        Get a summary of the RSVP status for a guest.
        
        Args:
            guest: The guest to get summary for
            
        Returns:
            Dictionary containing RSVP summary
        """
        rsvp = RSVP.query.filter_by(guest_id=guest.id).first()
        
        if not rsvp:
            return {
                'has_rsvp': False,
                'status': 'pending'
            }
        
        return {
            'has_rsvp': True,
            'status': 'cancelled' if rsvp.is_cancelled else ('attending' if rsvp.is_attending else 'declined'),
            'is_editable': rsvp.is_editable,
            'guest_count': 1 + len(rsvp.additional_guests) if rsvp.is_attending else 0,
            'last_updated': rsvp.last_updated
        }
    
    @staticmethod
    def get_all_rsvps() -> List[RSVP]:
        """Get all RSVPs."""
        return RSVP.query.all()
    
    @staticmethod
    def get_attending_rsvps() -> List[RSVP]:
        """Get all attending RSVPs."""
        return RSVP.query.filter_by(is_attending=True, is_cancelled=False).all()
    
    @staticmethod
    def get_transport_summary() -> Dict[str, int]:
        """Get summary of transport requirements."""
        attending_rsvps = RSVPService.get_attending_rsvps()
        
        summary = {
            'to_church': 0,
            'to_reception': 0,
            'to_hotel': 0,
            'total_requiring_transport': 0
        }
        
        guests_requiring_transport = set()
        
        for rsvp in attending_rsvps:
            if rsvp.transport_to_church:
                summary['to_church'] += 1
                guests_requiring_transport.add(rsvp.guest_id)
            if rsvp.transport_to_reception:
                summary['to_reception'] += 1
                guests_requiring_transport.add(rsvp.guest_id)
            if rsvp.transport_to_hotel:
                summary['to_hotel'] += 1
                guests_requiring_transport.add(rsvp.guest_id)
        
        summary['total_requiring_transport'] = len(guests_requiring_transport)
        
        return summary