# app/forms/admin.py - UPDATED WITH CONSTANTS
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, BooleanField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length
from app.constants import GuestLimit, Language, FileUpload

class LoginForm(FlaskForm):
    """Admin login form."""
    password = PasswordField('Password', validators=[DataRequired()])

class GuestForm(FlaskForm):
    """Form for adding/editing guests."""
    name = StringField('Name', validators=[
        DataRequired(), 
        Length(max=GuestLimit.MAX_NAME_LENGTH)
    ])
    phone = StringField('Phone Number', validators=[
        DataRequired(), 
        Length(max=GuestLimit.MAX_PHONE_LENGTH)
    ])
    has_plus_one = BooleanField('Has Plus One')
    is_family = BooleanField('Is Family')
    language_preference = SelectField(
        'Preferred Language',
        choices=[(Language.ENGLISH, 'English'), (Language.SPANISH, 'Spanish')],
        default=Language.DEFAULT
    )

class ImportForm(FlaskForm):
    """Form for importing guests from CSV."""
    file = FileField(
        'CSV File',
        validators=[
            FileRequired(),
            FileAllowed(FileUpload.ALLOWED_EXTENSIONS, 'CSV files only!')
        ]
    )