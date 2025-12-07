# app/models/reminder.py
from datetime import datetime, timezone
from app import db
from app.constants import Language


def _utc_now():
    """Helper to get current UTC time."""
    return datetime.now(timezone.utc)


class ReminderType:
    """Types of reminders that can be sent."""
    INITIAL = 'initial'          # 30 days before deadline
    FIRST_FOLLOWUP = 'first'     # 14 days before deadline
    SECOND_FOLLOWUP = 'second'   # 7 days before deadline
    FINAL = 'final'              # 3 days before deadline
    
    ALL_TYPES = [INITIAL, FIRST_FOLLOWUP, SECOND_FOLLOWUP, FINAL]
    
    @classmethod
    def get_days_before(cls, reminder_type):
        """Get the number of days before deadline for each reminder type."""
        mapping = {
            cls.INITIAL: 30,
            cls.FIRST_FOLLOWUP: 14,
            cls.SECOND_FOLLOWUP: 7,
            cls.FINAL: 3        
        }
        return mapping.get(reminder_type)


class ReminderStatus:
    """Status of reminder sending."""
    PENDING = 'pending'
    SENT = 'sent'
    FAILED = 'failed'
    SKIPPED = 'skipped'  # Skipped because guest already responded


class ReminderHistory(db.Model):
    """Track all reminders sent to guests."""
    __tablename__ = 'reminder_history'
    
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id', ondelete='CASCADE'), nullable=False)
    reminder_type = db.Column(db.String(20), nullable=False)  # initial, first, second, final, manual
    status = db.Column(db.String(20), nullable=False, default=ReminderStatus.PENDING)
    
    # Email details
    email_sent_to = db.Column(db.String(120))  # Email address used
    email_subject = db.Column(db.String(200))
    
    # Tracking
    scheduled_for = db.Column(db.DateTime)  # When it should be sent
    sent_at = db.Column(db.DateTime)  # When it was actually sent
    error_message = db.Column(db.Text)  # Error if failed
    
    # Admin tracking
    sent_by = db.Column(db.String(100))  # 'system' or admin email
    notes = db.Column(db.Text)  # Any admin notes
    
    created_at = db.Column(db.DateTime, default=_utc_now)
    
    # Relationships
    guest = db.relationship('Guest', backref='reminders')
    
    def __repr__(self):
        return f'<ReminderHistory {self.reminder_type} for guest {self.guest_id}>'
    
    @property
    def is_sent(self):
        """Check if reminder was successfully sent."""
        return self.status == ReminderStatus.SENT
    
    @property
    def can_retry(self):
        """Check if this reminder can be retried."""
        return self.status in [ReminderStatus.FAILED, ReminderStatus.PENDING]


class ReminderBatch(db.Model):
    """Track batch reminder operations."""
    __tablename__ = 'reminder_batch'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_type = db.Column(db.String(20), nullable=False)  # scheduled, manual
    reminder_type = db.Column(db.String(20), nullable=False)
    
    # Statistics
    total_guests = db.Column(db.Integer, default=0)
    sent_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    skipped_count = db.Column(db.Integer, default=0)
    
    # Execution details
    started_at = db.Column(db.DateTime, default=_utc_now)
    completed_at = db.Column(db.DateTime)
    executed_by = db.Column(db.String(100))  # 'scheduler' or admin email
    
    # Configuration used
    days_before_deadline = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<ReminderBatch {self.batch_type} {self.reminder_type} at {self.started_at}>'
    
    @property
    def is_complete(self):
        """Check if batch is complete."""
        return self.completed_at is not None
    
    @property
    def success_rate(self):
        """Calculate success rate."""
        if self.total_guests == 0:
            return 0
        return (self.sent_count / self.total_guests) * 100
    
    def update_stats(self):
        """Update batch statistics from individual reminder records."""
        from app import db
        
        # Get all reminders created during this batch
        reminders = ReminderHistory.query.filter(
            ReminderHistory.created_at >= self.started_at,
            ReminderHistory.reminder_type == self.reminder_type
        )
        
        if self.completed_at:
            reminders = reminders.filter(
                ReminderHistory.created_at <= self.completed_at
            )
        
        reminders = reminders.all()
        
        self.total_guests = len(reminders)
        self.sent_count = sum(1 for r in reminders if r.status == ReminderStatus.SENT)
        self.failed_count = sum(1 for r in reminders if r.status == ReminderStatus.FAILED)
        self.skipped_count = sum(1 for r in reminders if r.status == ReminderStatus.SKIPPED)
        
        db.session.commit()


class GuestReminderPreference(db.Model):
    """Track guest preferences for reminders."""
    __tablename__ = 'guest_reminder_preference'
    
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # Preferences
    opt_out = db.Column(db.Boolean, default=False)  # Guest opted out of reminders
    preferred_language = db.Column(db.String(2), default=Language.DEFAULT)
    max_reminders = db.Column(db.Integer, default=4)  # Maximum reminders to send
    
    # Tracking
    total_sent = db.Column(db.Integer, default=0)
    last_reminder_sent = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=_utc_now)
    updated_at = db.Column(db.DateTime, default=_utc_now, onupdate=_utc_now)
    
    # Relationships
    guest = db.relationship('Guest', backref=db.backref('reminder_preference', uselist=False))
    
    def __repr__(self):
        return f'<GuestReminderPreference for guest {self.guest_id}>'
    
    @property
    def can_send_reminder(self):
        """Check if we can send another reminder to this guest."""
        if self.opt_out:
            return False
        if self.total_sent >= self.max_reminders:
            return False
        return True
    
    def increment_sent_count(self):
        """Increment the sent count and update last sent time."""
        self.total_sent += 1
        self.last_reminder_sent = _utc_now()
        db.session.commit()