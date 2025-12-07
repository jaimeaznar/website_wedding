# app/constants.py
"""
Centralized constants for the wedding website application.
All magic strings, numbers, and configuration values should be defined here.
"""

from enum import Enum


class RSVPStatus:
    """RSVP status constants."""
    PENDING = 'pending'
    ATTENDING = 'attending'
    DECLINED = 'declined'
    CANCELLED = 'cancelled'


class Language:
    """Supported languages."""
    ENGLISH = 'en'
    SPANISH = 'es'
    DEFAULT = SPANISH
    SUPPORTED = [ENGLISH, SPANISH]


class DateFormat:
    """Date format strings."""
    DISPLAY = '%B %d, %Y'  # e.g., "April 15, 2026"
    DATABASE = '%Y-%m-%d'  # e.g., "2026-04-15"
    DATETIME_DISPLAY = '%Y-%m-%d %H:%M'
    LOG_FORMAT = '%Y%m%d'


class TimeLimit:
    """Time-based constants in various units."""
    # RSVP edit window
    RSVP_EDIT_HOURS = 24
    
    # Session/cookie durations (in seconds)
    ADMIN_SESSION_TIMEOUT = 1800  # 30 minutes
    REMEMBER_ME_DAYS = 30
    
    # Rate limiting
    RATE_LIMIT_WINDOW = 300  # 5 minutes
    RATE_LIMIT_MAX_REQUESTS = 30
    ADMIN_RATE_LIMIT_MAX_REQUESTS = 5
    
    # Cache durations (in seconds)
    CACHE_TIMEOUT = 3600  # 1 hour
    
    # Auto-dismiss flash messages (in milliseconds)
    FLASH_MESSAGE_TIMEOUT = 5000  # 5 seconds


class GuestLimit:
    """Guest-related limits."""
    MAX_ADULTS_FAMILY = 10
    MAX_CHILDREN_FAMILY = 10
    MAX_ADULTS_NON_FAMILY = 0
    MAX_CHILDREN_NON_FAMILY = 0
    MAX_NAME_LENGTH = 120
    MAX_PHONE_LENGTH = 20
    MAX_EMAIL_LENGTH = 120
    TOKEN_LENGTH = 32  # URL-safe token length


class FormLimit:
    """Form field limits."""
    MAX_HOTEL_NAME_LENGTH = 200
    MAX_ALLERGEN_NAME_LENGTH = 50
    MAX_CUSTOM_ALLERGEN_LENGTH = 100
    MIN_PASSWORD_LENGTH = 8


class HttpStatus:
    """HTTP status codes."""
    OK = 200
    REDIRECT = 302
    FORBIDDEN = 403
    NOT_FOUND = 404
    TOO_MANY_REQUESTS = 429
    SERVER_ERROR = 500


class FlashCategory:
    """Flash message categories."""
    SUCCESS = 'success'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'
    DANGER = 'danger'


class EmailTemplate:
    """Email template names."""
    INVITATION_EN = 'emails/invitation_en.html'
    INVITATION_ES = 'emails/invitation_es.html'
    REMINDER_EN = 'emails/reminder_en.html'
    REMINDER_ES = 'emails/reminder_es.html'
    CANCELLATION_NOTIFICATION = 'emails/cancellation_notification.html'


class LogMessage:
    """Standardized log messages."""
    # Guest operations
    GUEST_CREATED = "Created guest: {name} (ID: {id})"
    GUEST_UPDATED = "Updated guest: {name} (ID: {id})"
    GUEST_DELETED = "Deleted guest: {name} (ID: {id})"
    GUEST_IMPORT_SUCCESS = "Successfully imported {count} guests"
    GUEST_IMPORT_ERROR = "Failed to import guests: {error}"
    
    # RSVP operations
    RSVP_CREATED = "RSVP created for guest {name}"
    RSVP_UPDATED = "RSVP updated for guest {name}"
    RSVP_CANCELLED = "RSVP cancelled for guest {name}"
    RSVP_ACCESS = "RSVP form accessed with token: {token}"
    RSVP_GUEST_FOUND = "Guest found: {name} (ID: {id})"
    RSVP_DEADLINE_PASSED = "RSVP deadline has passed"
    
    # Admin operations
    ADMIN_LOGIN_SUCCESS = "Admin login successful: {ip}"
    ADMIN_LOGIN_FAILED = "Failed admin login attempt: {ip}"
    ADMIN_LOGOUT = "Admin logout: {ip}"
    ADMIN_UNAUTHORIZED = "Unauthorized admin access attempt: {ip}"
    
    # Allergen operations
    ALLERGEN_CREATED = "Created allergen: {name}"
    ALLERGEN_ADDED = "Added allergen {allergen} for {guest}"
    ALLERGEN_PROCESSING = "Processing allergens for guest: {guest}, prefix: {prefix}, rsvp_id: {rsvp_id}"
    
    # Error messages
    ERROR_GENERIC = "Error {operation}: {error}"
    ERROR_DATABASE = "Database error: {error}"
    ERROR_VALIDATION = "Validation error: {error}"


class ErrorMessage:
    """User-facing error messages."""
    GENERIC_ERROR = "An unexpected error occurred. Please try again."
    INVALID_TOKEN = "Invalid or expired link. Please check your invitation."
    RSVP_DEADLINE_PASSED = "The RSVP deadline has passed. Please contact us for assistance."
    RSVP_NOT_EDITABLE = "Changes are not possible at this time."
    INVALID_PASSWORD = "Invalid password"
    MISSING_REQUIRED_FIELDS = "Please fill in all required fields."
    GUEST_NOT_FOUND = "Guest not found."
    RSVP_NOT_FOUND = "No RSVP found."
    
    # Form validation
    NAME_REQUIRED = "Name is required"
    PHONE_REQUIRED = "Phone number is required"
    EMAIL_INVALID = "Please enter a valid email address"
    HOTEL_REQUIRED_WITH_TRANSPORT = "Please specify a hotel if you need transport services."
    ATTENDANCE_REQUIRED = "Please indicate whether you will attend."
    GUEST_COUNT_NEGATIVE = "Guest count cannot be negative."
    TOO_MANY_ADULTS = "Please contact us directly if you need to bring more than {max} additional adults."
    TOO_MANY_CHILDREN = "Please contact us directly if you need to bring more than {max} children."
    CSV_MISSING_HEADERS = "Missing required headers: {headers}"
    CSV_INVALID_FORMAT = "Invalid CSV format: {error}"
    ALLERGEN_EXISTS = "Allergen '{name}' already exists"


class SuccessMessage:
    """User-facing success messages."""
    RSVP_SUBMITTED = "Your RSVP has been submitted successfully!"
    RSVP_DECLINED = "Your response has been recorded."
    RSVP_CANCELLED = "Your RSVP has been cancelled."
    GUEST_ADDED = "Guest added successfully"
    GUEST_UPDATED = "Guest updated successfully"
    GUEST_DELETED = "Guest deleted successfully"
    GUESTS_IMPORTED = "Successfully imported {count} guests"
    LOGIN_SUCCESS = "Login successful"
    LOGOUT_SUCCESS = "You have been logged out"


class DatabaseConfig:
    """Database-related constants."""
    POOL_SIZE = 5
    MAX_OVERFLOW = 10
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 1800  # 30 minutes


class FileUpload:
    """File upload constants."""
    ALLOWED_EXTENSIONS = ['csv']
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    CSV_ENCODING = 'utf-8-sig'


class Security:
    """Security-related constants."""
    CSRF_TOKEN_LENGTH = 32
    SESSION_COOKIE_NAME = 'wedding_session'
    ADMIN_COOKIE_NAME = 'admin_authenticated'
    COOKIE_SECURE = True  # Set to False for development
    COOKIE_HTTPONLY = True
    COOKIE_SAMESITE = 'Lax'


class Template:
    """Template file paths."""
    # Main pages
    HOME = 'home.html'
    SCHEDULE = 'schedule.html'
    VENUE = 'venue.html'
    ACCOMMODATION = 'accommodation.html'
    ACTIVITIES = 'activities.html'
    GALLERY = 'gallery.html'
    
    # RSVP pages
    RSVP_FORM = 'rsvp.html'
    RSVP_LANDING = 'rsvp_landing.html'
    RSVP_ACCEPTED = 'rsvp_accepted.html'
    RSVP_DECLINED = 'rsvp_declined.html'
    RSVP_CANCELLED = 'rsvp_cancelled.html'
    RSVP_CANCEL = 'rsvp_cancel.html'
    RSVP_DEADLINE_PASSED = 'rsvp_deadline_passed.html'
    RSVP_PREVIOUSLY_CANCELLED = 'rsvp_previously_cancelled.html'
    RSVP_PREVIOUSLY_DECLINED = 'rsvp_previously_declined.html'
    
    # Admin pages
    ADMIN_LOGIN = 'admin/login.html'
    ADMIN_DASHBOARD = 'admin/dashboard.html'
    ADMIN_GUEST_FORM = 'admin/guest_form.html'
    ADMIN_DIETARY_REPORT = 'admin/dietary_report.html'
    ADMIN_TRANSPORT_REPORT = 'admin/transport_report.html'
    
    # Error pages
    ERROR_403 = 'errors/403.html'
    ERROR_404 = 'errors/404.html'
    ERROR_500 = 'errors/500.html'


class CSSClass:
    """CSS class names for consistency."""
    ALERT_SUCCESS = 'alert-success'
    ALERT_ERROR = 'alert-error'
    ALERT_WARNING = 'alert-warning'
    ALERT_INFO = 'alert-info'
    BTN_PRIMARY = 'btn-primary'
    BTN_SECONDARY = 'btn-secondary'
    BTN_DANGER = 'btn-danger'
    FORM_CONTROL = 'form-control'
    INVALID_FEEDBACK = 'invalid-feedback'


# Default configuration values
DEFAULT_CONFIG = {
    'REMINDER_DAYS_BEFORE': 30,
    'WARNING_CUTOFF_DAYS': 7,
    'WEDDING_DATE': '2026-06-06',
    'RSVP_DEADLINE': '2026-05-06',
    'ADMIN_EMAIL': 'admin@wedding.com',
    'ADMIN_PHONE': '123-456-7890',
    'WARNING_MESSAGE_TIMEOUT': 0,
    'WEDDING_TITLE': "Irene & Jaime's Wedding",  # ADD THIS LINE
}
