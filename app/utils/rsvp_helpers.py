# app/utils/rsvp_helpers.py - DEPRECATED
"""
This file is deprecated. All functionality has been moved to the service layer.

The allergen processing logic is now in:
- app/services/allergen_service.py

The RSVP processing logic is now in:
- app/services/rsvp_service.py

Please use the service classes instead of these helper functions.
"""

# Keep imports for backward compatibility during migration
from app.services.allergen_service import AllergenService

# Backward compatibility wrapper
def process_allergens(request_form, rsvp_id, guest_name, prefix):
    """
    DEPRECATED: Use AllergenService.process_guest_allergens() instead.
    
    This function is kept for backward compatibility only.
    """
    return AllergenService.process_guest_allergens(rsvp_id, guest_name, request_form, prefix)