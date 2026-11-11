"""Unit tests for data models."""

from wedding_api.models.admin import AdminLoginRequest, AdminTokenResponse
from wedding_api.models.invitation import InvitationResponse
from wedding_api.models.rsvp import RSVPCreate


def test_admin_login_request() -> None:
    """Test AdminLoginRequest model."""
    login = AdminLoginRequest(username="admin", password="test_password")

    assert login.username == "admin"
    assert login.password.get_secret_value() == "test_password"


def test_admin_token_response() -> None:
    """Test AdminTokenResponse model."""
    token_response = AdminTokenResponse(access_token="test_token", token_type="bearer", expires_in=3600)

    assert token_response.access_token == "test_token"
    assert token_response.token_type == "bearer"
    assert token_response.expires_in == 3600


def test_invitation_response_model() -> None:
    """Test InvitationResponse model validation."""
    invitation = InvitationResponse(
        bride_name="Jane Smith",
        groom_name="John Doe",
        wedding_date="2025-06-15",
        ceremony_time="15:00",
        venue_name="Beautiful Garden Estate",
        venue_address="123 Wedding Lane, Love City, LC 12345",
        venue_city="Love City",
        venue_state="LC",
        venue_zip="12345",
        rsvp_deadline="2025-06-10",
    )

    assert invitation.bride_name == "Jane Smith"
    assert invitation.groom_name == "John Doe"
    assert invitation.wedding_date == "2025-06-15"
    assert invitation.ceremony_time == "15:00"
    assert invitation.venue_name == "Beautiful Garden Estate"
    assert invitation.venue_address == "123 Wedding Lane, Love City, LC 12345"
    assert invitation.venue_city == "Love City"
    assert invitation.venue_state == "LC"
    assert invitation.venue_zip == "12345"
    assert invitation.rsvp_deadline == "2025-06-10"


def test_rsvp_create_model_with_all_fields() -> None:
    """Test RSVPCreate model with all fields provided."""
    rsvp = RSVPCreate(
        guest_name="Test Guest",
        email="test@example.com",
        phone="+1234567890",
        attending=True,
        dietary_restrictions="No peanuts, vegetarian",
        plus_one=True,
        message="Looking forward to the wedding!",
    )

    assert rsvp.guest_name == "Test Guest"
    assert rsvp.email == "test@example.com"
    assert rsvp.phone == "+1234567890"
    assert rsvp.attending is True
    assert rsvp.dietary_restrictions == "No peanuts, vegetarian"
    assert rsvp.plus_one is True
    assert rsvp.message == "Looking forward to the wedding!"


def test_rsvp_create_model_with_minimal_fields() -> None:
    """Test RSVPCreate model with only required fields."""
    rsvp = RSVPCreate(
        guest_name="Test Guest",
        email="test@example.com",
        phone=None,
        dietary_restrictions=None,
        message=None,
        attending=True,
    )

    assert rsvp.guest_name == "Test Guest"
    assert rsvp.email == "test@example.com"
    assert rsvp.attending is True


def test_rsvp_create_model_not_attending() -> None:
    """Test RSVPCreate model when not attending."""
    rsvp = RSVPCreate(
        guest_name="Test Guest",
        email="test@example.com",
        attending=False,
    )

    assert rsvp.guest_name == "Test Guest"
    assert rsvp.email == "test@example.com"
    assert rsvp.attending is False


def test_rsvp_create_model_with_plus_one() -> None:
    """Test RSVPCreate model with plus-one fields."""
    rsvp = RSVPCreate(
        guest_name="Test Guest",
        email="test@example.com",
        phone="+1234567890",
        dietary_restrictions="No peanuts",
        plus_one=True,
        message="Looking forward to the wedding!",
        attending=True,
    )

    assert rsvp.plus_one is True


def test_admin_login_request_with_secret_password() -> None:
    """Test AdminLoginRequest with SecretStr."""
    from pydantic import SecretStr

    login = AdminLoginRequest(username="admin", password=SecretStr("test_password"))

    assert login.username == "admin"
    assert login.password.get_secret_value() == "test_password"
