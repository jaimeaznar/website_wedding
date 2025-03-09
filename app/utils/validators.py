# app/utils/validators.py
class RSVPValidator:
    """Validator for RSVP form data"""
    
    def __init__(self, form_data, guest):
        self.form = form_data
        self.guest = guest
        self.errors = []
    
    def validate(self):
        """Validate all aspects of the RSVP form"""
        if not self.form:
            self.errors.append("No form data received.")
            return False, self.errors
            
        self._validate_attendance()
        
        # Only validate other fields if attending
        if self.form.get('is_attending') == 'yes':
            self._validate_transport()
            self._validate_allergens()
            self._validate_hotel()
            
            if self.guest.is_family:
                self._validate_family_members()
        
        return len(self.errors) == 0, self.errors
    
    def _validate_attendance(self):
        """Validate attendance selection"""
        if 'is_attending' not in self.form:
            self.errors.append("Please indicate whether you will attend.")
            return
        
        attendance = self.form.get('is_attending')
        if not attendance or attendance not in ['yes', 'no']:
            self.errors.append("Invalid attendance selection.")
    
    def _validate_hotel(self):
        """Validate hotel information"""
        hotel_name = self.form.get('hotel_name', '').strip()
        needs_transport = (
            self.form.get('transport_to_church') == 'on' or 
            self.form.get('transport_to_hotel') == 'on'
        )
        
        if needs_transport and not hotel_name:
            self.errors.append("Hotel name is required when requesting transport.")
    
    def _validate_transport(self):
        """Validate transport selections"""
        hotel = self.form.get('hotel_name', '').strip()
        needs_transport_to_church = self.form.get('transport_to_church') == 'on'
        needs_transport_to_hotel = self.form.get('transport_to_hotel') == 'on'
        
        if (needs_transport_to_church or needs_transport_to_hotel) and not hotel:
            self.errors.append("Please specify a hotel if you need transport services.")

    def _validate_allergens(self):
        """Validate allergen information"""
        allergens = self.form.getlist('allergens_main')
        custom_allergen = self.form.get('custom_allergen_main', '').strip()
        
        if allergens and not isinstance(allergens, list):
            self.errors.append("Invalid allergen selection format.")
    
    def _validate_family_members(self):
        """Validate family members information"""
        try:
            adults_count = int(self.form.get('adults_count', 0))
            children_count = int(self.form.get('children_count', 0))
            
            if adults_count < 0 or children_count < 0:
                self.errors.append("Guest count cannot be negative.")
                return
            
            if adults_count > 10:
                self.errors.append("Please contact us directly if you need to bring more than 10 additional adults.")
            
            if children_count > 10:
                self.errors.append("Please contact us directly if you need to bring more than 10 children.")
            
            # Validate that names are provided for each guest
            for i in range(adults_count):
                name = self.form.get(f'adult_name_{i}', '').strip()
                if not name:
                    self.errors.append(f"Please provide a name for additional adult #{i+1}")
            
            for i in range(children_count):
                name = self.form.get(f'child_name_{i}', '').strip()
                if not name:
                    self.errors.append(f"Please provide a name for child #{i+1}")
                
        except ValueError:
            self.errors.append("Invalid number format for guest count.")
