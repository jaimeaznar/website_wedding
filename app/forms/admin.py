# app/forms/admin.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, BooleanField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, Optional, Length

class LoginForm(FlaskForm):
    """Admin login form."""
    password = PasswordField('Password', validators=[DataRequired()])

class GuestForm(FlaskForm):
    """Form for adding/editing guests."""
    name = StringField('Name', validators=[DataRequired(), Length(max=120)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    has_plus_one = BooleanField('Has Plus One')
    is_family = BooleanField('Is Family')
    language_preference = SelectField(
        'Preferred Language',
        choices=[('en', 'English'), ('es', 'Spanish')],
        default='en'
    )

class ImportForm(FlaskForm):
    """Form for importing guests from CSV."""
    file = FileField(
        'CSV File',
        validators=[
            FileRequired(),
            FileAllowed(['csv'], 'CSV files only!')
        ]
    )