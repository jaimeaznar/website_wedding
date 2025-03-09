# app/models/allergen.py
from app import db

class Allergen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class GuestAllergen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rsvp_id = db.Column(db.Integer, db.ForeignKey('rsvp.id'), nullable=False)
    guest_name = db.Column(db.String(120), nullable=False)  # Name of the person with the allergy
    allergen_id = db.Column(db.Integer, db.ForeignKey('allergen.id'))
    custom_allergen = db.Column(db.String(100))  # For non-standard allergens
    allergen = db.relationship('Allergen', backref='guest_allergens')