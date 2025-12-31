# app/services/admin_service.py
import logging
from typing import Dict, Any, List
from app import db
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.models.allergen import Allergen, GuestAllergen
from app.services.guest_service import GuestService
from app.services.rsvp_service import RSVPService
from app.services.allergen_service import AllergenService

logger = logging.getLogger(__name__)


class AdminService:
    """Service class for admin-related business logic."""
    
    @staticmethod
    def verify_admin_password(password: str) -> bool:
        """
        Verify admin password against stored configuration.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        from app.admin_auth import verify_admin_password as auth_verify
        
        try:
            # Use the centralized admin auth module
            return auth_verify(password)
        except Exception as e:
            logger.error(f"Error verifying admin password: {str(e)}")
            return False
    
    @staticmethod
    def get_dashboard_data() -> Dict[str, Any]:
        """
        Get all data needed for the admin dashboard.
        
        Returns:
            Dictionary containing all dashboard data
        """
        # Get basic data
        guests = GuestService.get_all_guests()
        rsvps = RSVPService.get_all_rsvps()
        allergens = AllergenService.get_all_allergens()
        
        # Get statistics
        statistics = GuestService.get_guest_statistics()
        
        # Add allergen model references for template
        dashboard_data = {
            'guests': guests,
            'rsvps': rsvps,
            'allergens': allergens,
            'GuestAllergen': GuestAllergen,
            'Allergen': Allergen,
            **statistics  # Unpack all statistics
        }
        
        return dashboard_data
    
    @staticmethod
    def get_detailed_rsvp_report() -> List[Dict[str, Any]]:
        """
        Get detailed RSVP report for export.
        
        Returns:
            List of dictionaries containing RSVP details
        """
        report = []
        rsvps = RSVP.query.all()
        
        for rsvp in rsvps:
            guest = rsvp.guest
            
            # Get allergens grouped by guest
            allergens = AllergenService.get_allergens_for_rsvp(rsvp.id)
            
            rsvp_data = {
                'guest_name': guest.name,
                'guest_phone': guest.phone,
                'language': guest.language_preference,
                'status': 'Cancelled' if rsvp.is_cancelled else ('Attending' if rsvp.is_attending else 'Declined'),
                'adults_count': rsvp.adults_count if rsvp.is_attending else 0,
                'children_count': rsvp.children_count if rsvp.is_attending else 0,
                'total_guests': 1 + len(rsvp.additional_guests) if rsvp.is_attending else 0,
                'hotel': rsvp.hotel_name if rsvp.is_attending else None,
                'transport_reception': rsvp.transport_to_reception if rsvp.is_attending else False,
                'transport_hotel': rsvp.transport_to_hotel if rsvp.is_attending else False,
                'additional_guests': [],
                'allergens': allergens,
                'last_updated': rsvp.last_updated.strftime('%Y-%m-%d %H:%M'),
                'created_at': rsvp.created_at.strftime('%Y-%m-%d %H:%M')
            }
            
            # Add additional guest details
            if rsvp.is_attending:
                for additional in rsvp.additional_guests:
                    rsvp_data['additional_guests'].append({
                        'name': additional.name,
                        'is_child': additional.is_child
                    })
            
            report.append(rsvp_data)
        
        return report
    
    @staticmethod
    def get_dietary_report() -> Dict[str, Any]:
        """
        Get dietary restrictions report for catering.
        
        Returns:
            Dictionary containing dietary information
        """
        # Get allergen summary
        allergen_summary = AllergenService.get_allergen_summary()
        
        # Get detailed list per allergen
        detailed_allergens = {}
        for allergen in Allergen.query.all():
            guests = AllergenService.get_guests_with_allergen(allergen.name)
            if guests:
                detailed_allergens[allergen.name] = guests
        
        # Get custom allergens
        custom_allergens = db.session.query(
            GuestAllergen.custom_allergen,
            GuestAllergen.guest_name
        ).filter(
            GuestAllergen.custom_allergen.isnot(None)
        ).all()
        
        custom_grouped = {}
        for custom, guest_name in custom_allergens:
            if custom not in custom_grouped:
                custom_grouped[custom] = []
            custom_grouped[custom].append(guest_name)
        
        return {
            'summary': allergen_summary,
            'standard_allergens': detailed_allergens,
            'custom_allergens': custom_grouped,
            'total_guests_with_restrictions': len(set(
                ga.guest_name for ga in GuestAllergen.query.all()
            ))
        }
    
    @staticmethod
    def get_transport_report() -> Dict[str, Any]:
        """
        Get detailed transport requirements report.
        
        Returns:
            Dictionary containing transport information
        """
        transport_summary = RSVPService.get_transport_summary()
        
        # Get detailed lists
        attending_rsvps = RSVPService.get_attending_rsvps()
        
        to_church = []
        to_reception = []
        to_hotel = []
        hotels = {}
        
        for rsvp in attending_rsvps:
            guest_info = {
                'name': rsvp.guest.name,
                'phone': rsvp.guest.phone,
                'hotel': rsvp.hotel_name,
                'guest_count': 1 + len(rsvp.additional_guests)
            }
            
            if rsvp.transport_to_reception:
                to_reception.append(guest_info)
            if rsvp.transport_to_hotel:
                to_hotel.append(guest_info)
            
            # Group by hotel
            if rsvp.hotel_name:
                if rsvp.hotel_name not in hotels:
                    hotels[rsvp.hotel_name] = []
                hotels[rsvp.hotel_name].append(guest_info)
        
        return {
            'summary': transport_summary,
            'to_church': to_church,
            'to_reception': to_reception,
            'to_hotel': to_hotel,
            'hotels': hotels
        }
    
    @staticmethod
    def get_pending_rsvps() -> List[Guest]:
        """
        Get list of guests who haven't responded yet.
        
        Returns:
            List of guests without RSVPs
        """
        # Get all guest IDs that have RSVPs
        guest_ids_with_rsvp = db.session.query(RSVP.guest_id).all()
        guest_ids_with_rsvp = [id[0] for id in guest_ids_with_rsvp]
        
        # Get guests without RSVPs
        pending_guests = Guest.query.filter(
            ~Guest.id.in_(guest_ids_with_rsvp)
        ).all()
        
        return pending_guests
    
    @staticmethod
    def generate_csv_template() -> str:
        """
        Generate CSV template for guest import.
        
        Returns:
            CSV content as string
        """
        return 'name,phone,language\n'