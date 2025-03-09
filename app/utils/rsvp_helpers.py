# app/utils/rsvp_helpers.py
from app import db
from app.models.allergen import GuestAllergen

def process_allergens(request_form, rsvp_id, guest_name, prefix):
    """
    Process allergens for a specific guest from form data.
    
    Args:
        request_form: Flask request form
        rsvp_id: ID of the RSVP
        guest_name: Name of the guest
        prefix: Form field prefix (e.g., 'main', 'adult_1', 'child_2')
    """
    # Process standard allergens
    allergen_ids = request_form.getlist(f'allergens_{prefix}')
    for allergen_id in allergen_ids:
        guest_allergen = GuestAllergen(
            rsvp_id=rsvp_id,
            guest_name=guest_name,
            allergen_id=allergen_id
        )
        db.session.add(guest_allergen)
    
    # Process custom allergen if provided
    custom_allergen = request_form.get(f'custom_allergen_{prefix}')
    if custom_allergen and custom_allergen.strip():
        guest_allergen = GuestAllergen(
            rsvp_id=rsvp_id,
            guest_name=guest_name,
            custom_allergen=custom_allergen.strip()
        )
        db.session.add(guest_allergen)