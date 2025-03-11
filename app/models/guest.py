from datetime import datetime
from app import db

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    token = db.Column(db.String(100), unique=True, nullable=False)
    language_preference = db.Column(db.String(2), default='en')
    has_plus_one = db.Column(db.Boolean, default=False)
    plus_one_used = db.Column(db.Boolean, default=False)
    is_family = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Updated relationship with cascade delete
    rsvp = db.relationship('RSVP', back_populates='guest', uselist=False, cascade='all, delete-orphan')
