"""Unit tests for EmailService utilities."""

import smtplib

import pytest

from wedding_api.utils.email import EmailService


class FakeSMTP:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.started_tls = False
        self.logged_in = False
        self.sent_message = None
        self.raise_on_send = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, username, password):
        if username == "bad_user":
            raise smtplib.SMTPAuthenticationError(535, b"Auth failed")
        self.logged_in = True

    def send_message(self, msg):
        if self.raise_on_send:
            raise smtplib.SMTPException("send failed")
        self.sent_message = msg


@pytest.mark.asyncio
async def test_create_message_contains_headers_and_bodies() -> None:
    svc = EmailService()

    msg = svc._create_message("to@example.com", "Subject", "<b>hi</b>", "hi")

    assert "Subject" in msg["Subject"]
    assert "to@example.com" in msg["To"]
    # payload should include both plain and html parts
    payload = msg.get_payload()
    assert any(part.get_content_type() == "text/plain" for part in payload)
    assert any(part.get_content_type() == "text/html" for part in payload)


@pytest.mark.asyncio
async def test_send_email_disabled_returns_true(monkeypatch) -> None:
    svc = EmailService()
    svc.enabled = False
    result = await svc.send_email("a@b.com", "Sub", "<b>hi</b>")
    assert result is True


@pytest.mark.asyncio
async def test_send_email_missing_credentials_returns_false() -> None:
    svc = EmailService()
    svc.enabled = True
    svc.smtp_username = None
    svc.smtp_password = None

    result = await svc.send_email("a@b.com", "Sub", "<b>hi</b>")
    assert result is False


@pytest.mark.asyncio
async def test_send_email_success(monkeypatch) -> None:
    svc = EmailService()
    svc.enabled = True
    svc.smtp_host = "smtp.test"
    svc.smtp_port = 25
    svc.smtp_username = "user"
    svc.smtp_password = "pass"
    svc.smtp_use_tls = True

    def fake_smtp_factory(host, port):
        return FakeSMTP(host, port)

    monkeypatch.setattr(smtplib, "SMTP", fake_smtp_factory)

    result = await svc.send_email("to@example.com", "Hello", "<p>Hi</p>", "Hi")
    assert result is True


@pytest.mark.asyncio
async def test_send_email_auth_failure(monkeypatch) -> None:
    svc = EmailService()
    svc.enabled = True
    svc.smtp_host = "smtp.test"
    svc.smtp_port = 25
    svc.smtp_username = "bad_user"
    svc.smtp_password = "pass"

    monkeypatch.setattr(smtplib, "SMTP", lambda h, p: FakeSMTP(h, p))

    result = await svc.send_email("to@example.com", "Hello", "<p>Hi</p>")
    assert result is False


@pytest.mark.asyncio
async def test_send_email_smtp_exception(monkeypatch) -> None:
    svc = EmailService()
    svc.enabled = True
    svc.smtp_host = "smtp.test"
    svc.smtp_port = 25
    svc.smtp_username = "user"
    svc.smtp_password = "pass"

    def factory(host, port):
        inst = FakeSMTP(host, port)
        inst.raise_on_send = True
        return inst

    monkeypatch.setattr(smtplib, "SMTP", factory)

    result = await svc.send_email("to@example.com", "Hello", "<p>Hi</p>")
    assert result is False


@pytest.mark.asyncio
async def test_send_rsvp_confirmation_no_email(monkeypatch) -> None:
    svc = EmailService()
    # Should short-circuit and return True
    result = await svc.send_rsvp_confirmation(None, "Guest", "C123", True, {})
    assert result is True


@pytest.mark.asyncio
async def test_send_rsvp_confirmation_calls_send_email(monkeypatch) -> None:
    svc = EmailService()
    called = {}

    async def fake_send_email(to, subject, html, text=None):
        called["to"] = to
        called["subject"] = subject
        called["html"] = html
        called["text"] = text
        return True

    svc.send_email = fake_send_email

    result = await svc.send_rsvp_confirmation("g@e.com", "Guest", "C123", True, {"plus_one": True, "dietary_restrictions": "None", "message": "Hi"})
    assert result is True
    assert called["to"] == "g@e.com"
    assert called["subject"] == "RSVP Confirmed!"
    assert "Confirmation Number" in called["html"]


@pytest.mark.asyncio
async def test_send_admin_notification_missing_admin_email(monkeypatch) -> None:
    svc = EmailService()
    # Temporarily remove admin email from settings
    import wedding_api.config as cfg

    original = cfg.settings.admin_email
    cfg.settings.admin_email = None

    try:
        result = await svc.send_admin_notification("Guest", "g@e.com", True, {})
        assert result is False
    finally:
        cfg.settings.admin_email = original


@pytest.mark.asyncio
async def test_send_admin_notification_calls_send_email(monkeypatch) -> None:
    svc = EmailService()
    called = {}

    async def fake_send_email(to, subject, html, text=None):
        called["to"] = to
        called["subject"] = subject
        return True

    svc.send_email = fake_send_email

    # Ensure there is an admin email configured
    import wedding_api.config as cfg

    original = cfg.settings.admin_email
    cfg.settings.admin_email = "admin@test"

    try:
        result = await svc.send_admin_notification("Guest", "g@e.com", False, {"phone": "+1"})
        assert result is True
        assert called["to"] == "admin@test"
        assert "New RSVP" in called["subject"]
    finally:
        cfg.settings.admin_email = original
