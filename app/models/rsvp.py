# app/models/rsvp.py
from datetime import datetime, timedelta
from app import db
from flask import current_app

class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    is_attending = db.Column(db.Boolean, default=False)
    is_cancelled = db.Column(db.Boolean, default=False)
    adults_count = db.Column(db.Integer, default=1)
    children_count = db.Column(db.Integer, default=0)
    plus_one_name = db.Column(db.String(120))
    hotel_name = db.Column(db.String(200))
    transport_to_church = db.Column(db.Boolean, default=False)
    transport_to_reception = db.Column(db.Boolean, default=False)
    transport_to_hotel = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    cancellation_date = db.Column(db.DateTime)
    
    guest = db.relationship('Guest', back_populates='rsvp')
    additional_guests = db.relationship('AdditionalGuest', backref='rsvp', cascade='all, delete-orphan')
    allergens = db.relationship('GuestAllergen', backref='rsvp', cascade='all, delete-orphan')

    @property
    def is_editable(self):
        """Check if RSVP can be edited (more than a week before wedding)"""
        wedding_date = datetime.strptime(current_app.config['WEDDING_DATE'], '%Y-%m-%d')
        cutoff_date = wedding_date - timedelta(days=7)
        return datetime.now() < cutoff_date

    def cancel(self):
        """Cancel RSVP if within allowed timeframe"""
        if not self.is_editable:
            return False
        self.is_cancelled = True
        self.is_attending = False
        self.cancellation_date = datetime.now()
        return True

class AdditionalGuest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rsvp_id = db.Column(db.Integer, db.ForeignKey('rsvp.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    is_child = db.Column(db.Boolean, default=False)