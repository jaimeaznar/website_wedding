# app/utils/rsvp_processor.py
from app import db
from app.models.rsvp import RSVP, AdditionalGuest
from app.models.allergen import GuestAllergen
from app.utils.rsvp_helpers import process_allergens
from app.utils.validators import RSVPValidator

class RSVPFormProcessor:
    def __init__(self, form_data, guest):
        self.form = form_data
        self.guest = guest
        self.rsvp = None

    def process(self):
        """Main processing method with validation"""
        # First validate the form data
        validator = RSVPValidator(self.form, self.guest)
        is_valid, errors = validator.validate()
        
        if not is_valid:
            return False, "\n".join(errors)
        
        # If validation passes, process the form
        try:
            self._get_or_create_rsvp()
            self._process_attendance()
            
            if self.rsvp.is_attending:
                self._process_hotel_info()
                self._process_transport()
                self._process_main_guest_allergens()
                
            
            db.session.commit()
            return True, "Your RSVP has been updated successfully!"
        except Exception as e:
            db.session.rollback()
            return False, f"There was an error updating your RSVP: {str(e)}"

    def _get_or_create_rsvp(self):
        """Get existing RSVP or create new one"""
        self.rsvp = RSVP.query.filter_by(guest_id=self.guest.id).first()
        if not self.rsvp:
            self.rsvp = RSVP(guest_id=self.guest.id)
            db.session.add(self.rsvp)

    def _process_attendance(self):
        """Process basic attendance information"""
        self.rsvp.is_attending = self.form.get('is_attending') == 'yes'

    def _process_hotel_info(self):
        """Process hotel information"""
        self.rsvp.hotel_name = self.form.get('hotel_name', '').strip() or None

    def _process_transport(self):
        """Process transport options"""
        self.rsvp.transport_to_church = bool(self.form.get('transport_to_church'))
        self.rsvp.transport_to_reception = bool(self.form.get('transport_to_reception'))
        self.rsvp.transport_to_hotel = bool(self.form.get('transport_to_hotel'))

    def _process_main_guest_allergens(self):
        """Process allergens for main guest"""
        GuestAllergen.query.filter_by(rsvp_id=self.rsvp.id, guest_name=self.guest.name).delete()
        process_allergens(self.form, self.rsvp.id, self.guest.name, 'main')

    def _process_additional_guests(self):
        """Process additional guests and their allergens"""
        # Set counts
        self.rsvp.adults_count = int(self.form.get('adults_count', 0))
        self.rsvp.children_count = int(self.form.get('children_count', 0))
        
        # Clear existing
        AdditionalGuest.query.filter_by(rsvp_id=self.rsvp.id).delete()
        
        # Process adults
        self._process_guest_group('adult', self.rsvp.adults_count, False)
        
        # Process children
        self._process_guest_group('child', self.rsvp.children_count, True)

    def _process_guest_group(self, prefix, count, is_child):
        """Process a group of guests (adults or children)"""
        for i in range(count):
            name = self.form.get(f'{prefix}_name_{i}')
            if name:
                guest = AdditionalGuest(
                    rsvp_id=self.rsvp.id,
                    name=name,
                    is_child=is_child
                )
                db.session.add(guest)
                process_allergens(self.form, self.rsvp.id, name, f'{prefix}_{i}')