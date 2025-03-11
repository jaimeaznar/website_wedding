# app/forms/rsvp.py
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, RadioField, FieldList, FormField
from wtforms.validators import DataRequired, Optional, Length, ValidationError
from flask import current_app

class AllergenForm(FlaskForm):
    """Form for a single allergen selection."""
    allergen_id = SelectField('Allergen', coerce=int, validators=[Optional()])
    custom_allergen = StringField('Other', validators=[Optional(), Length(max=100)])
    
    class Meta:
        # CSRF protection is handled by the parent form
        csrf = False

class AdditionalGuestForm(FlaskForm):
    """Form for an additional guest."""
    name = StringField('Name', validators=[DataRequired(), Length(max=120)])
    is_child = BooleanField('Child')
    allergens = FieldList(FormField(AllergenForm))
    
    class Meta:
        # CSRF protection is handled by the parent form
        csrf = False

class RSVPForm(FlaskForm):
    """Form for RSVP submission."""
    is_attending = RadioField(
        'Will you attend?', 
        choices=[('yes', 'Yes, I will attend'), ('no', 'No, I cannot attend')],
        validators=[DataRequired()]
    )
    
    # Only required if attending
    hotel_name = StringField('Where are you staying?', validators=[Optional(), Length(max=200)])
    transport_to_church = BooleanField('Transport to church', default=False)
    transport_to_reception = BooleanField('Transport to reception', default=False)
    transport_to_hotel = BooleanField('Transport to hotel', default=False)
    
    # For family guests
    adults_count = SelectField('Number of Additional Adults', coerce=int, default=0)
    children_count = SelectField('Number of Children', coerce=int, default=0)
    
    # Dynamic fields for additional guests will be handled in the form processing
    
    def __init__(self, *args, **kwargs):
        """Initialize the form with custom choices based on guest type."""
        self.guest = kwargs.pop('guest', None)
        super(RSVPForm, self).__init__(*args, **kwargs)
        
        # Set choices for adults and children counts based on guest type
        max_adults = 10 if self.guest and self.guest.is_family else 0
        max_children = 10 if self.guest and self.guest.is_family else 0
        
        self.adults_count.choices = [(i, str(i)) for i in range(max_adults + 1)]
        self.children_count.choices = [(i, str(i)) for i in range(max_children + 1)]
    
    def validate_hotel_name(self, field):
        """Validate that hotel is provided if transport is requested."""
        if self.is_attending.data == 'yes':
            needs_transport = (
                self.transport_to_church.data or 
                self.transport_to_reception.data or 
                self.transport_to_hotel.data
            )
            if needs_transport and not field.data.strip():
                raise ValidationError('Please specify a hotel if you need transport services.')

class RSVPCancellationForm(FlaskForm):
    """Form for RSVP cancellation confirmation."""
    confirm_cancellation = BooleanField(
        'I confirm that I want to cancel my RSVP', 
        validators=[DataRequired()]
    )
    
    def validate_confirm_cancellation(self, field):
        """Ensure cancellation is confirmed."""
        if not field.data:
            raise ValidationError('You must confirm the cancellation.')