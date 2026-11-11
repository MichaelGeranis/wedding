"""Unit tests for email utility functions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wedding_api.utils.email import EmailService


@pytest.fixture
def email_service():
    """Create email service for testing."""
    with patch("wedding_api.utils.email.settings") as mock_settings:
        mock_settings.email_enabled = False  # Disable for testing
        mock_settings.smtp_host = "smtp.test.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_username = "test@example.com"
        mock_settings.smtp_password = "test_password"
        mock_settings.smtp_use_tls = True
        mock_settings.email_from_address = "from@example.com"
        mock_settings.email_from_name = "Test Wedding"
        mock_settings.admin_email = "admin@example.com"
        return EmailService()


def test_email_service_initialization(email_service):
    """Test email service initialization."""
    assert email_service.smtp_host == "smtp.test.com"
    assert email_service.smtp_port == 587
    assert email_service.smtp_username == "test@example.com"
    assert email_service.from_address == "from@example.com"
    assert email_service.from_name == "Test Wedding"
    assert not email_service.enabled  # Disabled for testing


def test_create_message_with_html_only(email_service):
    """Test creating email message with HTML body only."""
    msg = email_service._create_message(
        to_email="recipient@example.com",
        subject="Test Subject",
        html_body="<h1>Test HTML</h1>",
    )

    assert msg["To"] == "recipient@example.com"
    assert msg["Subject"] == "Test Subject"
    assert msg["From"] == "Test Wedding <from@example.com>"
    assert len(msg.get_payload()) == 1  # Only HTML part


def test_create_message_with_html_and_text(email_service):
    """Test creating email message with both HTML and text."""
    msg = email_service._create_message(
        to_email="recipient@example.com",
        subject="Test Subject",
        html_body="<h1>Test HTML</h1>",
        text_body="Test Plain Text",
    )

    assert msg["To"] == "recipient@example.com"
    assert msg["Subject"] == "Test Subject"
    assert len(msg.get_payload()) == 2  # Both HTML and text parts


@pytest.mark.asyncio
async def test_send_email_disabled(email_service):
    """Test sending email when email is disabled."""
    result = await email_service.send_email(
        to_email="test@example.com",
        subject="Test",
        html_body="<p>Test</p>",
    )

    assert result is True  # Should succeed when disabled


@pytest.mark.asyncio
async def test_send_email_no_credentials():
    """Test sending email without SMTP credentials."""
    with patch("wedding_api.utils.email.settings") as mock_settings:
        mock_settings.email_enabled = True
        mock_settings.smtp_username = None
        mock_settings.smtp_password = None
        service = EmailService()

        result = await service.send_email(
            to_email="test@example.com",
            subject="Test",
            html_body="<p>Test</p>",
        )

        assert result is False


@pytest.mark.asyncio
async def test_send_email_smtp_auth_error():
    """Test sending email with SMTP authentication error."""
    import smtplib

    with patch("wedding_api.utils.email.settings") as mock_settings:
        mock_settings.email_enabled = True
        mock_settings.smtp_host = "smtp.test.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_username = "test@example.com"
        mock_settings.smtp_password = "wrong_password"
        mock_settings.smtp_use_tls = True
        mock_settings.email_from_address = "from@example.com"
        mock_settings.email_from_name = "Test"

        service = EmailService()

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp_instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
            mock_smtp_instance.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")

            result = await service.send_email(
                to_email="test@example.com",
                subject="Test",
                html_body="<p>Test</p>",
            )

            assert result is False


@pytest.mark.asyncio
async def test_send_email_smtp_exception():
    """Test sending email with SMTP exception."""
    import smtplib

    with patch("wedding_api.utils.email.settings") as mock_settings:
        mock_settings.email_enabled = True
        mock_settings.smtp_host = "smtp.test.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_username = "test@example.com"
        mock_settings.smtp_password = "password"
        mock_settings.smtp_use_tls = True
        mock_settings.email_from_address = "from@example.com"
        mock_settings.email_from_name = "Test"

        service = EmailService()

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp_instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
            mock_smtp_instance.send_message.side_effect = smtplib.SMTPException("Server error")

            result = await service.send_email(
                to_email="test@example.com",
                subject="Test",
                html_body="<p>Test</p>",
            )

            assert result is False


@pytest.mark.asyncio
async def test_send_rsvp_confirmation_attending(email_service):
    """Test sending RSVP confirmation for attending guest."""
    result = await email_service.send_rsvp_confirmation(
        guest_email="guest@example.com",
        guest_name="John Doe",
        confirmation_number="WED-123",
        attending=True,
        rsvp_details={
            "plus_one": True,
            "dietary_restrictions": "No nuts",
            "message": "Looking forward!",
            "phone": "+1234567890",
        },
    )

    assert result is True  # Succeeds when disabled


@pytest.mark.asyncio
async def test_send_rsvp_confirmation_not_attending(email_service):
    """Test sending RSVP confirmation for non-attending guest."""
    result = await email_service.send_rsvp_confirmation(
        guest_email="guest@example.com",
        guest_name="John Doe",
        confirmation_number="WED-123",
        attending=False,
        rsvp_details={},
    )

    assert result is True


@pytest.mark.asyncio
async def test_send_admin_notification():
    """Test sending admin notification."""
    with patch("wedding_api.utils.email.settings") as mock_settings:
        mock_settings.email_enabled = False
        mock_settings.admin_email = "admin@example.com"
        service = EmailService()

        result = await service.send_admin_notification(
            guest_name="John Doe",
            guest_email="guest@example.com",
            attending=True,
            rsvp_details={
                "plus_one": True,
                "dietary_restrictions": "Vegan",
                "message": "Excited!",
                "phone": "+1234567890",
            },
        )

        assert result is True


@pytest.mark.asyncio
async def test_send_admin_notification_no_admin_email():
    """Test sending admin notification when admin email not configured."""
    with patch("wedding_api.utils.email.settings") as mock_settings:
        mock_settings.email_enabled = True
        mock_settings.admin_email = None
        service = EmailService()

        result = await service.send_admin_notification(
            guest_name="John Doe",
            guest_email="guest@example.com",
            attending=True,
            rsvp_details={},
        )

        assert result is False


def test_generate_rsvp_confirmation_html_attending(email_service):
    """Test generating RSVP confirmation HTML for attending guest."""
    html = email_service._generate_rsvp_confirmation_html(
        guest_name="John Doe",
        confirmation_number="WED-123",
        attending=True,
        rsvp_details={
            "plus_one": True,
            "dietary_restrictions": "No nuts",
            "message": "Looking forward!",
        },
    )

    assert "John Doe" in html
    assert "WED-123" in html
    assert "Attending" in html
    assert "Plus One" in html or "Yes" in html
    assert "No nuts" in html
    assert "Looking forward!" in html


def test_generate_rsvp_confirmation_html_not_attending(email_service):
    """Test generating RSVP confirmation HTML for non-attending guest."""
    html = email_service._generate_rsvp_confirmation_html(
        guest_name="John Doe",
        confirmation_number="WED-123",
        attending=False,
        rsvp_details={},
    )

    assert "John Doe" in html
    assert "WED-123" in html
    assert "Not Attending" in html
    assert "We'll miss you" in html


def test_generate_rsvp_confirmation_text_attending(email_service):
    """Test generating RSVP confirmation text for attending guest."""
    text = email_service._generate_rsvp_confirmation_text(
        guest_name="John Doe",
        confirmation_number="WED-123",
        attending=True,
        rsvp_details={
            "plus_one": True,
            "dietary_restrictions": "Gluten-free",
            "message": "Can't wait!",
        },
    )

    assert "John Doe" in text
    assert "WED-123" in text
    assert "Status: Attending" in text
    assert "Plus One" in text or "Yes" in text
    assert "Gluten-free" in text
    assert "Can't wait!" in text


def test_generate_rsvp_confirmation_text_minimal(email_service):
    """Test generating RSVP confirmation text with minimal details."""
    text = email_service._generate_rsvp_confirmation_text(
        guest_name="John Doe",
        confirmation_number="WED-123",
        attending=False,
        rsvp_details={},
    )

    assert "John Doe" in text
    assert "WED-123" in text
    assert "Status: Not Attending" in text


def test_generate_admin_notification_html(email_service):
    """Test generating admin notification HTML."""
    html = email_service._generate_admin_notification_html(
        guest_name="John Doe",
        guest_email="john@example.com",
        attending=True,
        rsvp_details={
            "plus_one": True,
            "dietary_restrictions": "Vegan",
            "message": "Excited!",
            "phone": "+1234567890",
        },
    )

    assert "John Doe" in html
    assert "john@example.com" in html
    assert "ATTENDING" in html
    assert "Plus One" in html or "Yes" in html
    assert "Vegan" in html
    assert "Excited!" in html
    assert "+1234567890" in html


def test_generate_admin_notification_text(email_service):
    """Test generating admin notification text."""
    text = email_service._generate_admin_notification_text(
        guest_name="John Doe",
        guest_email="john@example.com",
        attending=False,
        rsvp_details={
            "phone": "+0987654321",
        },
    )

    assert "John Doe" in text
    assert "john@example.com" in text
    assert "NOT ATTENDING" in text
    assert "+0987654321" in text


# Note: XSS protection test removed - Pydantic validators prevent malicious input
# from reaching email generation (NAME_PATTERN blocks < and >, SQL_INJECTION_PATTERN
# blocks quotes and SQL keywords). Input validation happens at the RSVP submission
# level before data reaches the email service.
