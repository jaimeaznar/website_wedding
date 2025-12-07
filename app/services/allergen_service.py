# app/services/allergen_service.py
import logging
from typing import Dict, Any, List
from app import db
from app.models.allergen import Allergen, GuestAllergen

logger = logging.getLogger(__name__)


class AllergenService:
    """Service class for handling allergen-related business logic."""
    
    @staticmethod
    def get_all_allergens() -> List[Allergen]:
        """Get all available allergens."""
        return Allergen.query.all()
    
    @staticmethod
    def create_allergen(name: str) -> Allergen:
        """
        Create a new allergen.
        
        Args:
            name: Name of the allergen
            
        Returns:
            The created allergen
            
        Raises:
            ValueError: If allergen already exists
        """
        # Check if already exists
        existing = Allergen.query.filter_by(name=name).first()
        if existing:
            raise ValueError(f"Allergen '{name}' already exists")
        
        allergen = Allergen(name=name)
        db.session.add(allergen)
        db.session.commit()
        
        logger.info(f"Created allergen: {name}")
        return allergen
    
    @staticmethod
    def process_guest_allergens(
        rsvp_id: int,
        guest_name: str,
        form_data: Dict[str, Any],
        prefix: str
    ) -> None:
        """
        Process allergens for a specific guest from form data.
        
        Args:
            rsvp_id: ID of the RSVP
            guest_name: Name of the guest
            form_data: Form data dictionary
            prefix: Form field prefix (e.g., 'main', 'adult_1')
        """
        if rsvp_id is None:
            logger.warning(f"Cannot process allergens: rsvp_id is None for {guest_name}")
            return
        
        logger.debug(f"Processing allergens for guest: {guest_name}, prefix: {prefix}, rsvp_id: {rsvp_id}")
        
        # Delete existing allergens for this guest
        existing_count = GuestAllergen.query.filter_by(
            rsvp_id=rsvp_id,
            guest_name=guest_name
        ).count()
        
        if existing_count > 0:
            logger.debug(f"Deleting {existing_count} existing allergens for {guest_name}")
            GuestAllergen.query.filter_by(
                rsvp_id=rsvp_id,
                guest_name=guest_name
            ).delete()
        
        # Process standard allergens
        allergen_field_name = f'allergens_{prefix}'
        
        # Handle different types of form data
        if hasattr(form_data, 'getlist'):
            allergen_ids = form_data.getlist(allergen_field_name)
        elif isinstance(form_data, dict):
            # Handle dictionary form data (for testing)
            allergen_value = form_data.get(allergen_field_name, [])
            if isinstance(allergen_value, list):
                allergen_ids = allergen_value
            else:
                allergen_ids = [allergen_value] if allergen_value else []
        else:
            allergen_ids = []
        
        logger.debug(f"Found allergen IDs for {allergen_field_name}: {allergen_ids}")
        
        allergens_added = 0
        for allergen_id in allergen_ids:
            try:
                allergen_id = int(allergen_id)
                # Verify the allergen exists
                allergen = Allergen.query.get(allergen_id)
                if allergen:
                    guest_allergen = GuestAllergen(
                        rsvp_id=rsvp_id,
                        guest_name=guest_name,
                        allergen_id=allergen_id
                    )
                    db.session.add(guest_allergen)
                    allergens_added += 1
                    logger.debug(f"Added allergen {allergen.name} for {guest_name}")
                else:
                    logger.warning(f"Allergen with ID {allergen_id} not found")
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid allergen ID for {guest_name}: {allergen_id}, {e}")
        
        # Process custom allergen
        custom_field_name = f'custom_allergen_{prefix}'
        custom_allergen = form_data.get(custom_field_name, '').strip()
        logger.debug(f"Custom allergen for {custom_field_name}: '{custom_allergen}'")
        
        if custom_allergen:
            guest_allergen = GuestAllergen(
                rsvp_id=rsvp_id,
                guest_name=guest_name,
                custom_allergen=custom_allergen
            )
            db.session.add(guest_allergen)
            allergens_added += 1
            logger.debug(f"Added custom allergen '{custom_allergen}' for {guest_name}")
        
        logger.info(f"Total allergens added for {guest_name}: {allergens_added}")
    
    @staticmethod
    def get_allergens_for_rsvp(rsvp_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all allergens for an RSVP, grouped by guest name.
        
        Args:
            rsvp_id: ID of the RSVP
            
        Returns:
            Dictionary with guest names as keys and list of allergen info as values
        """
        allergens = GuestAllergen.query.filter_by(rsvp_id=rsvp_id).all()
        
        grouped = {}
        for allergen in allergens:
            if allergen.guest_name not in grouped:
                grouped[allergen.guest_name] = []
            
            allergen_info = {
                'type': 'standard' if allergen.allergen_id else 'custom',
                'name': allergen.allergen.name if allergen.allergen else allergen.custom_allergen,
                'id': allergen.allergen_id
            }
            grouped[allergen.guest_name].append(allergen_info)
        
        return grouped
    
    @staticmethod
    def get_allergen_summary() -> Dict[str, int]:
        """
        Get a summary of all allergens across all RSVPs.
        
        Returns:
            Dictionary with allergen names as keys and counts as values
        """
        summary = {}
        
        # Count standard allergens
        standard_allergens = db.session.query(
            Allergen.name,
            db.func.count(GuestAllergen.id)
        ).join(
            GuestAllergen
        ).group_by(
            Allergen.name
        ).all()
        
        for name, count in standard_allergens:
            summary[name] = count
        
        # Count custom allergens
        custom_allergens = db.session.query(
            GuestAllergen.custom_allergen,
            db.func.count(GuestAllergen.id)
        ).filter(
            GuestAllergen.custom_allergen.isnot(None)
        ).group_by(
            GuestAllergen.custom_allergen
        ).all()
        
        for custom, count in custom_allergens:
            summary[f"Custom: {custom}"] = count
        
        return summary
    
    @staticmethod
    def get_guests_with_allergen(allergen_name: str) -> List[str]:
        """
        Get list of guest names who have a specific allergen.
        
        Args:
            allergen_name: Name of the allergen
            
        Returns:
            List of guest names
        """
        # Check standard allergens
        allergen = Allergen.query.filter_by(name=allergen_name).first()
        if allergen:
            guest_allergens = GuestAllergen.query.filter_by(allergen_id=allergen.id).all()
            return [ga.guest_name for ga in guest_allergens]
        
        # Check custom allergens
        guest_allergens = GuestAllergen.query.filter_by(custom_allergen=allergen_name).all()
        return [ga.guest_name for ga in guest_allergens]