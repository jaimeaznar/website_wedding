# app/services/whatsapp_service.py
"""
WhatsApp messaging service using Twilio API.

This service handles:
- Sending RSVP links to guests via WhatsApp
- Sending reminder messages
- Phone number validation and normalization
- Message template management
"""

from __future__ import annotations

import os
import re
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

# Import types only for type checking (avoids circular imports)
if TYPE_CHECKING:
    from app.services.airtable_service import AirtableGuest, AirtableService

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of WhatsApp messages."""
    RSVP_LINK = "rsvp_link"
    REMINDER_1 = "reminder_1"  # 30 days
    REMINDER_2 = "reminder_2"  # 14 days
    REMINDER_3 = "reminder_3"  # 7 days
    REMINDER_4 = "reminder_4"  # 3 days (final)


@dataclass
class MessageResult:
    """Result of a WhatsApp message send attempt."""
    success: bool
    message_sid: Optional[str] = None
    error: Optional[str] = None
    phone: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'message_sid': self.message_sid,
            'error': self.error,
            'phone': self.phone,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


class PhoneNumberError(Exception):
    """Raised when phone number is invalid."""
    pass


class WhatsAppService:
    """
    Service for sending WhatsApp messages via Twilio.
    
    Requires Twilio account with WhatsApp enabled (sandbox or business).
    """
    
    # Default country code (Spain)
    DEFAULT_COUNTRY_CODE = "+34"
    
    # Message templates (Spanish and English)
    TEMPLATES = {
        MessageType.RSVP_LINK: {
            'es': (
                "🎊 *¡Hola {name}!*\n\n"
                "Estás invitado/a a la boda de *Irene y Jaime* el 6 de junio de 2026.\n\n"
                "Por favor, confirma tu asistencia antes del *6 de mayo de 2026* "
                "haciendo clic en el siguiente enlace:\n\n"
                "👉 {rsvp_link}\n\n"
                "Descubre todos los detalles de la boda en nuestra web:\n"
                "🌐 https://wedding.aznarroa.com\n\n"
                "¡Esperamos verte allí! 💒"
            ),
            'en': (
                "🎊 *Hello {name}!*\n\n"
                "You are invited to *Irene and Jaime's* wedding on June 6th, 2026.\n\n"
                "Please confirm your attendance before *May 6th, 2026* "
                "by clicking the following link:\n\n"
                "👉 {rsvp_link}\n\n"
                "Discover all the wedding details on our website:\n"
                "🌐 https://wedding.aznarroa.com\n\n"
                "We hope to see you there! 💒"
            ),
        },
        MessageType.REMINDER_1: {
            'es': (
                "👋 *Hola {name}*\n\n"
                "Te recordamos que aún no has confirmado tu asistencia a la boda "
                "de *Irene y Jaime*.\n\n"
                "Quedan *30 días* para la fecha límite (6 de mayo).\n\n"
                "👉 {rsvp_link}\n\n"
                "📍 Más información: https://wedding.aznarroa.com\n\n"
                "¡Gracias! 🙏"
            ),
            'en': (
                "👋 *Hello {name}*\n\n"
                "This is a reminder that you haven't yet confirmed your attendance "
                "to *Irene and Jaime's* wedding.\n\n"
                "There are *30 days* left until the deadline (May 6th).\n\n"
                "👉 {rsvp_link}\n\n"
                "📍 More info: https://wedding.aznarroa.com\n\n"
                "Thank you! 🙏"
            ),
        },
        MessageType.REMINDER_2: {
            'es': (
                "⏰ *Hola {name}*\n\n"
                "Quedan solo *2 semanas* para confirmar tu asistencia a la boda "
                "de Irene y Jaime.\n\n"
                "Por favor, responde antes del 6 de mayo:\n\n"
                "👉 {rsvp_link}\n\n"
                "📍 Detalles de la boda: https://wedding.aznarroa.com\n\n"
                "¡Gracias por tu respuesta! 💐"
            ),
            'en': (
                "⏰ *Hello {name}*\n\n"
                "Only *2 weeks* left to confirm your attendance to "
                "Irene and Jaime's wedding.\n\n"
                "Please respond before May 6th:\n\n"
                "👉 {rsvp_link}\n\n"
                "📍 Wedding details: https://wedding.aznarroa.com\n\n"
                "Thank you for your response! 💐"
            ),
        },
        MessageType.REMINDER_3: {
            'es': (
                "📅 *Hola {name}*\n\n"
                "¡Solo queda *1 semana* para confirmar!\n\n"
                "Necesitamos tu respuesta para la boda de Irene y Jaime. "
                "Por favor, confirma lo antes posible:\n\n"
                "👉 {rsvp_link}\n\n"
                "📍 Info: https://wedding.aznarroa.com\n\n"
                "¡Gracias! 🌸"
            ),
            'en': (
                "📅 *Hello {name}*\n\n"
                "Only *1 week* left to confirm!\n\n"
                "We need your response for Irene and Jaime's wedding. "
                "Please confirm as soon as possible:\n\n"
                "👉 {rsvp_link}\n\n"
                "📍 Info: https://wedding.aznarroa.com\n\n"
                "Thank you! 🌸"
            ),
        },
        MessageType.REMINDER_4: {
            'es': (
                "🚨 *¡Hola {name}!*\n\n"
                "*¡ÚLTIMO RECORDATORIO!*\n\n"
                "Quedan solo *3 días* para confirmar tu asistencia a la boda. "
                "Después del 6 de mayo no podremos garantizar tu plaza.\n\n"
                "👉 {rsvp_link}\n\n"
                "📍 https://wedding.aznarroa.com\n\n"
                "Si tienes algún problema, contacta con nosotros. ❤️"
            ),
            'en': (
                "🚨 *Hello {name}!*\n\n"
                "*FINAL REMINDER!*\n\n"
                "Only *3 days* left to confirm your attendance to the wedding. "
                "After May 6th we cannot guarantee your spot.\n\n"
                "👉 {rsvp_link}\n\n"
                "📍 https://wedding.aznarroa.com\n\n"
                "If you have any issues, please contact us. ❤️"
            ),
        },
    }
    
    def __init__(self):
        """Initialize WhatsApp service with Twilio credentials."""
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
        
        # Base URL for RSVP links
        self.base_url = os.environ.get('BASE_URL', 'https://wedding.aznarroa.com')
        
        self._client = None
    
    @property
    def is_configured(self) -> bool:
        """Check if Twilio credentials are configured."""
        return bool(self.account_sid and self.auth_token and self.whatsapp_number)
    
    @property
    def client(self):
        """Lazy-load Twilio client."""
        if self._client is None:
            if not self.is_configured:
                raise ValueError(
                    "Twilio is not configured. Please set "
                    "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_NUMBER "
                    "environment variables."
                )
            
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client initialized")
            except ImportError:
                raise ImportError(
                    "twilio is not installed. Run: pip install twilio"
                )
        
        return self._client
    
    # =========================================================================
    # PHONE NUMBER HANDLING
    # =========================================================================
    
    @classmethod
    def normalize_phone(
        cls, 
        phone: str, 
        default_country_code: Optional[str] = None
    ) -> str:
        """
        Normalize phone number to E.164 format for WhatsApp.
        
        Args:
            phone: Phone number in various formats
            default_country_code: Country code to use if not present (default: +34)
            
        Returns:
            Normalized phone number (e.g., +34612345678)
            
        Raises:
            PhoneNumberError: If phone number is invalid
        """
        if not phone:
            raise PhoneNumberError("Phone number is empty")
        
        default_country_code = default_country_code or cls.DEFAULT_COUNTRY_CODE
        
        # Remove all non-digit characters except leading +
        original = phone
        phone = phone.strip()
        
        # Check if starts with +
        has_plus = phone.startswith('+')
        
        # Remove all non-digits
        digits_only = re.sub(r'\D', '', phone)
        
        if not digits_only:
            raise PhoneNumberError(f"No digits found in phone number: {original}")
        
        # Handle different cases
        if has_plus:
            # Already has country code with +
            normalized = f"+{digits_only}"
        elif digits_only.startswith('00'):
            # International format with 00 prefix
            normalized = f"+{digits_only[2:]}"
        elif digits_only.startswith('34') and len(digits_only) == 11:
            # Spanish number without + (34 + 9 digits)
            normalized = f"+{digits_only}"
        elif len(digits_only) == 9 and digits_only[0] in '67':
            # Spanish mobile without country code (starts with 6 or 7)
            normalized = f"{default_country_code}{digits_only}"
        elif len(digits_only) == 9 and digits_only[0] == '9':
            # Spanish landline (won't work with WhatsApp, but normalize anyway)
            normalized = f"{default_country_code}{digits_only}"
            logger.warning(f"Landline number detected: {normalized} - may not work with WhatsApp")
        else:
            # Assume it needs country code
            normalized = f"{default_country_code}{digits_only}"
        
        # Validate final format
        if not cls.validate_phone(normalized):
            raise PhoneNumberError(f"Invalid phone number format: {original} -> {normalized}")
        
        return normalized
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Validate phone number is in correct E.164 format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid
        """
        # E.164 format: + followed by 7-15 digits
        pattern = r'^\+[1-9]\d{6,14}$'
        return bool(re.match(pattern, phone))
    
    @classmethod
    def format_for_whatsapp(cls, phone: str) -> str:
        """
        Format phone number for Twilio WhatsApp API.
        
        Args:
            phone: Normalized phone number
            
        Returns:
            WhatsApp format: whatsapp:+34612345678
        """
        normalized = cls.normalize_phone(phone)
        return f"whatsapp:{normalized}"
    
    @classmethod
    def detect_language_from_phone(cls, phone: str) -> str:
        """
        Detect language preference based on phone country code.
        
        Spanish (+34) -> 'es'
        All other country codes -> 'en'
        
        Args:
            phone: Phone number (normalized or not)
            
        Returns:
            'es' for Spanish numbers, 'en' for all others
        """
        try:
            normalized = cls.normalize_phone(phone)
            # Check if it's a Spanish number
            if normalized.startswith('+34'):
                return 'es'
            else:
                return 'en'
        except PhoneNumberError:
            # Default to English if we can't parse the number
            return 'en'
    
    @classmethod
    def get_language_for_guest(cls, phone: str, preferred_language: Optional[str] = None) -> str:
        """
        Determine the language to use for a guest.
        
        Priority:
        1. If preferred_language is explicitly set and valid, use it
        2. Otherwise, detect from phone country code
        
        Args:
            phone: Guest's phone number
            preferred_language: Guest's preferred language from Airtable (optional)
            
        Returns:
            'es' or 'en'
        """
        # If language is explicitly set in Airtable, respect it
        if preferred_language and preferred_language in ('es', 'en'):
            return preferred_language
        
        # Otherwise, detect from phone number
        return cls.detect_language_from_phone(phone)
    
    # =========================================================================
    # MESSAGE SENDING
    # =========================================================================
    
    def send_message(
        self,
        to_phone: str,
        message: str,
    ) -> MessageResult:
        """
        Send a WhatsApp message.
        
        Args:
            to_phone: Recipient phone number
            message: Message body
            
        Returns:
            MessageResult with success status and details
        """
        try:
            # Normalize phone number
            normalized_phone = self.normalize_phone(to_phone)
            whatsapp_to = f"whatsapp:{normalized_phone}"
            whatsapp_from = f"whatsapp:{self.whatsapp_number}"
            
            # Send via Twilio
            twilio_message = self.client.messages.create(
                body=message,
                from_=whatsapp_from,
                to=whatsapp_to
            )
            
            logger.info(f"WhatsApp sent to {normalized_phone}: SID={twilio_message.sid}")
            
            return MessageResult(
                success=True,
                message_sid=twilio_message.sid,
                phone=normalized_phone,
                timestamp=datetime.now()
            )
            
        except PhoneNumberError as e:
            logger.error(f"Invalid phone number: {e}")
            return MessageResult(
                success=False,
                error=str(e),
                phone=to_phone,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to send WhatsApp: {e}")
            return MessageResult(
                success=False,
                error=str(e),
                phone=to_phone,
                timestamp=datetime.now()
            )
    
    def send_rsvp_link(
        self,
        name: str,
        phone: str,
        token: str,
        language: Optional[str] = None,
        personal_message: Optional[str] = None
    ) -> MessageResult:
        """
        Send RSVP link to a guest.
        
        Args:
            name: Guest's name
            phone: Guest's phone number
            token: RSVP token for generating link
            language: 'es' or 'en' (auto-detected from phone if not provided)
            
        Returns:
            MessageResult
        """
       # If personal message exists, use it as the ENTIRE message
        if personal_message:
            logger.info(f"Sending personal message to {name} ({phone})")
            return self.send_message(phone, personal_message)
        
        # Otherwise use default template
        lang = self.get_language_for_guest(phone, language)
        
        rsvp_link = f"{self.base_url}/rsvp/{token}"
        
        template = self.TEMPLATES[MessageType.RSVP_LINK].get(lang, 
                self.TEMPLATES[MessageType.RSVP_LINK]['en'])
        
        message = template.format(name=name, rsvp_link=rsvp_link)
        
        logger.info(f"Sending RSVP link to {name} ({phone}) in {lang.upper()}")
        
        return self.send_message(phone, message)
    
    def send_reminder(
        self,
        name: str,
        phone: str,
        token: str,
        reminder_number: int,
        language: Optional[str] = None
    ) -> MessageResult:
        """
        Send a reminder message to a guest.
        
        Args:
            name: Guest's name
            phone: Guest's phone number
            token: RSVP token for generating link
            reminder_number: Which reminder (1, 2, 3, or 4)
            language: 'es' or 'en' (auto-detected from phone if not provided)
            
        Returns:
            MessageResult
        """
        # Auto-detect language from phone country code if not provided
        lang = self.get_language_for_guest(phone, language)
        
        rsvp_link = f"{self.base_url}/rsvp/{token}"
        
        message_type = getattr(MessageType, f"REMINDER_{reminder_number}", MessageType.REMINDER_1)
        
        template = self.TEMPLATES[message_type].get(lang,
                   self.TEMPLATES[message_type]['en'])
        
        message = template.format(name=name, rsvp_link=rsvp_link)
        
        logger.info(f"Sending reminder {reminder_number} to {name} ({phone}) in {lang.upper()}")
        
        return self.send_message(phone, message)
    
    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================
    
    def send_rsvp_links_to_all(
        self,
        guests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send RSVP links to multiple guests.
        
        Args:
            guests: List of dicts with 'name', 'phone', 'token', 'language'
            
        Returns:
            Summary of results
        """
        results = {
            'total': len(guests),
            'sent': 0,
            'failed': 0,
            'details': []
        }
        
        for guest in guests:
            result = self.send_rsvp_link(
                name=guest['name'],
                phone=guest['phone'],
                token=guest['token'],
                language=guest.get('language', 'es')
            )
            
            if result.success:
                results['sent'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'name': guest['name'],
                'phone': guest['phone'],
                **result.to_dict()
            })
        
        logger.info(f"Bulk send complete: {results['sent']}/{results['total']} sent")
        return results
    
    def send_reminders_to_all(
        self,
        guests: List[Dict[str, Any]],
        reminder_number: int
    ) -> Dict[str, Any]:
        """
        Send reminders to multiple guests.
        
        Args:
            guests: List of dicts with 'name', 'phone', 'token', 'language'
            reminder_number: Which reminder (1, 2, 3, or 4)
            
        Returns:
            Summary of results
        """
        results = {
            'total': len(guests),
            'sent': 0,
            'failed': 0,
            'reminder_number': reminder_number,
            'details': []
        }
        
        for guest in guests:
            result = self.send_reminder(
                name=guest['name'],
                phone=guest['phone'],
                token=guest['token'],
                reminder_number=reminder_number,
                language=guest.get('language', 'es')
            )
            
            if result.success:
                results['sent'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'name': guest['name'],
                'phone': guest['phone'],
                **result.to_dict()
            })
        
        logger.info(f"Reminder {reminder_number} complete: {results['sent']}/{results['total']} sent")
        return results
    
    # =========================================================================
    # INTEGRATION WITH AIRTABLE
    # =========================================================================
    
    def send_rsvp_link_and_update_airtable(
        self,
        airtable_guest: AirtableGuest,
        airtable_service: AirtableService
    ) -> MessageResult:
        """
        Send RSVP link and update Airtable record.
        
        Args:
            airtable_guest: Guest from Airtable
            airtable_service: Airtable service instance
            
        Returns:
            MessageResult
        """
        # Ensure guest has token
        token = airtable_guest.token
        if not token:
            token = airtable_service.generate_token_for_guest(airtable_guest.record_id)
        
        # Send WhatsApp
        result = self.send_rsvp_link(
            name=airtable_guest.name,
            phone=airtable_guest.phone,
            token=token,
            language=airtable_guest.language,
            personal_message=airtable_guest.personal_message
        )
        
        # Update Airtable if successful
        if result.success:
            airtable_service.update_link_sent(
                record_id=airtable_guest.record_id,
                sent_at=result.timestamp
            )
        
        return result
    
    def send_reminder_and_update_airtable(
        self,
        airtable_guest: AirtableGuest,
        airtable_service: AirtableService,
        reminder_number: int
    ) -> MessageResult:
        """
        Send reminder and update Airtable record.
        
        Args:
            airtable_guest: Guest from Airtable
            airtable_service: Airtable service instance
            reminder_number: Which reminder (1, 2, 3, or 4)
            
        Returns:
            MessageResult
        """
        if not airtable_guest.token:
            logger.error(f"Guest {airtable_guest.name} has no token")
            return MessageResult(
                success=False,
                error="Guest has no RSVP token",
                phone=airtable_guest.phone,
                timestamp=datetime.now()
            )
        
        # Send WhatsApp
        result = self.send_reminder(
            name=airtable_guest.name,
            phone=airtable_guest.phone,
            token=airtable_guest.token,
            reminder_number=reminder_number,
            language=airtable_guest.language
        )
        
        # Update Airtable if successful
        if result.success:
            airtable_service.update_reminder_sent(
                record_id=airtable_guest.record_id,
                reminder_number=reminder_number,
                sent_at=result.timestamp
            )
        
        return result


# Singleton instance
_whatsapp_service: Optional[WhatsAppService] = None


def get_whatsapp_service() -> WhatsAppService:
    """Get the singleton WhatsAppService instance."""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service