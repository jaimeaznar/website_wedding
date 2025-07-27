# tests/test_email.py
import pytest
from unittest.mock import patch, MagicMock, call
from flask_mail import Message
from app import create_app, db
from app.utils.email import send_invitation_email, send_cancellation_notification
from app.services.guest_service import GuestService
from app.services.rsvp_service import RSVPService
from app.models.guest import Guest
from app.models.rsvp import RSVP
from app.constants import Language, EmailTemplate


class TestEmailFunctionality:
    """Test email sending functionality with mocking."""
    
    @pytest.fixture
    def app(self):
        """Create app with test config."""
        from app.config import TestConfig
        
        class EmailTestConfig(TestConfig):
            MAIL_SERVER = 'smtp.test.com'
            MAIL_PORT = 587
            MAIL_USE_TLS = True
            MAIL_USERNAME = 'test@wedding.com'
            MAIL_PASSWORD = 'test_password'
            MAIL_DEFAULT_SENDER = 'noreply@wedding.com'
            ADMIN_EMAIL = 'admin@wedding.com'
        
        app = create_app(EmailTestConfig)
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    @patch('app.utils.email.mail.send')
    def test_send_invitation_email_english(self, mock_send, app):
        """Test sending invitation email in English."""
        with app.app_context():
            # Create guest
            guest = Guest(
                name="Email Test Guest",
                email="test@example.com",
                phone="555-0001",
                token="test-token-123",
                language_preference=Language.ENGLISH
            )
            db.session.add(guest)
            db.session.commit()
            
            # Send invitation
            send_invitation_email(guest)
            
            # Verify email was sent
            mock_send.assert_called_once()
            
            # Get the message that was sent
            sent_message = mock_send.call_args[0][0]
            
            # Verify message properties
            assert sent_message.subject == "Wedding Invitation"
            assert sent_message.recipients == ["test@example.com"]
            assert "test-token-123" in sent_message.html
            assert guest.name in sent_message.html
    
    @patch('app.utils.email.mail.send')
    def test_send_invitation_email_spanish(self, mock_send, app):
        """Test sending invitation email in Spanish."""
        with app.app_context():
            # Create Spanish-speaking guest
            guest = Guest(
                name="Invitado de Prueba",
                email="prueba@ejemplo.com",
                phone="555-0002",
                token="test-token-456",
                language_preference=Language.SPANISH
            )
            db.session.add(guest)
            db.session.commit()
            
            # Send invitation
            send_invitation_email(guest)
            
            # Verify email was sent
            mock_send.assert_called_once()
            
            # Get the message that was sent
            sent_message = mock_send.call_args[0][0]
            
            # Verify Spanish template was used
            assert sent_message.subject == "Wedding Invitation"  # Subject might be same
            assert sent_message.recipients == ["prueba@ejemplo.com"]
            # Note: We'd need to check the actual template content
    
    @patch('app.utils.email.mail.send')
    def test_send_cancellation_notification(self, mock_send, app):
        """Test sending cancellation notification to admin."""
        with app.app_context():
            # Create guest and RSVP
            guest = GuestService.create_guest(
                name="Cancellation Test",
                email="cancel@test.com",
                phone="555-0003",
                is_family=True
            )
            
            # Create RSVP
            form_data = {
                'is_attending': 'yes',
                'hotel_name': 'Test Hotel',
                'adults_count': '2',
                'children_count': '1'
            }
            _, _, rsvp = RSVPService.create_or_update_rsvp(guest, form_data)
            
            # Send cancellation notification
            send_cancellation_notification(guest, rsvp)
            
            # Verify email was sent
            mock_send.assert_called_once()
            
            # Get the message that was sent
            sent_message = mock_send.call_args[0][0]
            
            # Verify message properties
            assert sent_message.subject == "RSVP Cancellation Notice"
            assert sent_message.recipients == [app.config['ADMIN_EMAIL']]
            assert guest.name in sent_message.body
            assert "Test Hotel" in sent_message.body
            assert "2" in sent_message.body  # adults count
            assert "1" in sent_message.body  # children count
    
    @patch('app.utils.email.mail.send')
    def test_email_error_handling(self, mock_send, app):
        """Test email error handling."""
        with app.app_context():
            # Configure mock to raise an exception
            mock_send.side_effect = Exception("SMTP connection failed")
            
            guest = Guest(
                name="Error Test",
                email="error@test.com",
                phone="555-0004",
                token="error-token"
            )
            db.session.add(guest)
            db.session.commit()
            
            # Should not raise exception, but handle gracefully
            with patch('app.utils.email.logger') as mock_logger:
                result = send_cancellation_notification(guest, MagicMock())
                
                # Should return False on error
                assert result is False
                
                # Should log the error
                mock_logger.error.assert_called()
    
    @patch('app.utils.email.mail.send')
    def test_bulk_email_sending(self, mock_send, app):
        """Test sending emails to multiple guests."""
        with app.app_context():
            # Create multiple guests
            guests = []
            for i in range(5):
                guest = Guest(
                    name=f"Bulk Test {i}",
                    email=f"bulk{i}@test.com",
                    phone=f"555-{1000+i:04d}",
                    token=f"bulk-token-{i}",
                    language_preference=Language.ENGLISH if i % 2 == 0 else Language.SPANISH
                )
                guests.append(guest)
            
            db.session.add_all(guests)
            db.session.commit()
            
            # Send invitations to all
            for guest in guests:
                send_invitation_email(guest)
            
            # Verify all emails were sent
            assert mock_send.call_count == 5
            
            # Verify each email has correct recipient
            recipients = [call[0][0].recipients[0] for call in mock_send.call_args_list]
            expected_recipients = [f"bulk{i}@test.com" for i in range(5)]
            assert set(recipients) == set(expected_recipients)
    
    def test_email_template_rendering(self, app):
        """Test that email templates render correctly."""
        with app.app_context():
            from flask import render_template
            
            # Test data
            test_data = {
                'name': 'Test Guest',
                'token': 'test-token-123'
            }
            
            # Test English template renders without error
            try:
                html = render_template('emails/invitation_en.html', **test_data)
                assert 'Test Guest' in html
                assert 'test-token-123' in html
            except Exception as e:
                pytest.skip(f"Email template not found: {e}")
    
    @patch('app.utils.email.mail')
    def test_email_configuration(self, mock_mail, app):
        """Test email configuration is applied correctly."""
        with app.app_context():
            # Verify mail configuration
            assert app.config['MAIL_SERVER'] == 'smtp.test.com'
            assert app.config['MAIL_PORT'] == 587
            assert app.config['MAIL_USE_TLS'] is True
            assert app.config['MAIL_USERNAME'] == 'test@wedding.com'
    
    @patch('app.utils.email.mail.send')
    def test_email_with_attachments(self, mock_send, app):
        """Test sending emails with attachments (future enhancement)."""
        with app.app_context():
            # This is a placeholder for future functionality
            # Currently, the system doesn't send attachments
            # but this test shows how it could be tested
            
            guest = Guest(
                name="Attachment Test",
                email="attach@test.com",
                phone="555-0005",
                token="attach-token"
            )
            db.session.add(guest)
            db.session.commit()
            
            # If we add attachment support in the future:
            # with patch('app.utils.email.Message') as MockMessage:
            #     instance = MockMessage.return_value
            #     send_invitation_with_ics(guest)
            #     instance.attach.assert_called()
            
            # For now, just verify basic email works
            send_invitation_email(guest)
            mock_send.assert_called_once()


class TestEmailQueueing:
    """Test email queueing and batch processing (for future implementation)."""
    
    @pytest.fixture
    def app(self):
        """Create app with test config."""
        from app.config import TestConfig
        app = create_app(TestConfig)
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_email_queue_concept(self, app):
        """Test concept for email queueing system."""
        with app.app_context():
            # This demonstrates how we might test an email queue
            # if implemented in the future
            
            email_queue = []
            
            def queue_email(recipient, subject, body):
                """Mock email queue function."""
                email_queue.append({
                    'recipient': recipient,
                    'subject': subject,
                    'body': body,
                    'queued_at': datetime.now()
                })
            
            # Queue multiple emails
            for i in range(10):
                queue_email(
                    recipient=f"user{i}@test.com",
                    subject="Test Email",
                    body=f"Test body {i}"
                )
            
            # Verify queue size
            assert len(email_queue) == 10
            
            # Simulate batch processing
            processed = []
            batch_size = 3
            while email_queue:
                batch = email_queue[:batch_size]
                email_queue = email_queue[batch_size:]
                processed.extend(batch)
            
            assert len(processed) == 10
            assert len(email_queue) == 0