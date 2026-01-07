from datetime import datetime, timezone
from app import db


class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    token = db.Column(db.String(100), unique=True, nullable=False)
    language_preference = db.Column(db.String(2), default='en')
    personal_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Updated relationship with cascade delete
    rsvp = db.relationship('RSVP', back_populates='guest', uselist=False, cascade='all, delete-orphan')