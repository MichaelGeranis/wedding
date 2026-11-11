"""Unit tests for security utilities."""

from datetime import UTC, datetime, timedelta, timezone

from jose import jwt

from wedding_api.config import settings
from wedding_api.utils.security import create_access_token, decode_access_token, generate_confirmation_number, get_password_hash, verify_password


def test_create_access_token() -> None:
    """Test creating JWT access token."""
    token, expiration = create_access_token("test_user")

    assert isinstance(token, str)
    assert len(token) > 0
    assert isinstance(expiration, datetime)
    assert expiration > datetime.now(UTC)


def test_decode_access_token_valid() -> None:
    """Test decoding valid JWT token."""
    token, _ = create_access_token("test_user")

    payload = decode_access_token(token)

    assert payload is not None
    assert payload.sub == "test_user"


def test_decode_access_token_invalid() -> None:
    """Test decoding invalid JWT token."""
    payload = decode_access_token("invalid_token")

    assert payload is None


def test_decode_access_token_expired() -> None:
    """Test decoding expired JWT token."""
    # Create a token that's already expired
    expire = datetime.now(UTC) - timedelta(minutes=1)
    payload_data = {
        "sub": "test_user",
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }

    token = jwt.encode(payload_data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    payload = decode_access_token(token)

    assert payload is None


def test_decode_access_token_wrong_secret() -> None:
    """Test decoding token with wrong secret."""
    # Create token with different secret
    payload_data = {
        "sub": "test_user",
        "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }

    token = jwt.encode(payload_data, "wrong_secret", algorithm=settings.jwt_algorithm)

    payload = decode_access_token(token)

    assert payload is None


def test_generate_confirmation_number() -> None:
    """Test generating confirmation numbers."""
    email = "test@example.com"
    timestamp = datetime(2025, 1, 1, 12, 0, 0)

    confirmation = generate_confirmation_number(email, timestamp)

    assert confirmation.startswith("WED-2025-")
    assert len(confirmation) == 15  # WED-YYYY-XXXXXX

    # Same inputs should generate same number
    confirmation2 = generate_confirmation_number(email, timestamp)
    assert confirmation == confirmation2


def test_generate_confirmation_number_different_emails() -> None:
    """Test that different emails generate different confirmation numbers."""
    timestamp = datetime(2025, 1, 1, 12, 0, 0)

    conf1 = generate_confirmation_number("test1@example.com", timestamp)
    conf2 = generate_confirmation_number("test2@example.com", timestamp)

    assert conf1 != conf2


def test_verify_password_correct() -> None:
    """Test password verification with correct password."""
    password = "test_password"
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True


def test_verify_password_incorrect() -> None:
    """Test password verification with incorrect password."""
    password = "test_password"
    hashed = get_password_hash(password)

    assert verify_password("wrong_password", hashed) is False


def test_verify_password_invalid_hash() -> None:
    """Test password verification with invalid hash."""
    assert verify_password("password", "not_a_hash") is False


def test_get_password_hash() -> None:
    """Test password hashing."""
    password = "test_password"

    hashed = get_password_hash(password)

    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert hashed != password
    # Bcrypt hashes start with $2b$
    assert hashed.startswith("$2b$")


def test_create_access_token_empty_subject() -> None:
    """Creating a token with an empty subject should still work."""
    token, _ = create_access_token("")

    payload = decode_access_token(token)

    assert payload is not None
    assert payload.sub == ""


def test_create_access_token_expiration_matches_settings() -> None:
    """Token expiration should be roughly settings.jwt_expiration_minutes from now."""
    before = datetime.now(UTC)
    token, expiration = create_access_token("test_user")
    after = datetime.now(UTC)

    # expiration should be between before + minutes and after + minutes
    expected_minutes = settings.jwt_expiration_minutes
    delta_min_before = expiration - (before + timedelta(minutes=expected_minutes))
    delta_min_after = expiration - (after + timedelta(minutes=expected_minutes))

    assert abs(delta_min_before.total_seconds()) < 5 or abs(delta_min_after.total_seconds()) < 5


def test_decode_access_token_missing_sub_field() -> None:
    """Tokens missing required fields should fail decoding."""
    expire = datetime.now(UTC) + timedelta(minutes=10)
    payload_data = {
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }

    token = jwt.encode(payload_data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    payload = decode_access_token(token)

    assert payload is None


def test_decode_access_token_non_int_timestamps() -> None:
    """Tokens with non-integer exp/iat should be rejected."""
    payload_data = {
        "sub": "test_user",
        "exp": "not_an_int",
        "iat": "also_not_int",
    }

    token = jwt.encode(payload_data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    payload = decode_access_token(token)

    assert payload is None


def test_generate_confirmation_number_email_none() -> None:
    """When email is None, generation should fallback to timestamp-based value and be deterministic."""
    timestamp = datetime(2025, 1, 1, 12, 0, 0)

    conf1 = generate_confirmation_number(None, timestamp)
    conf2 = generate_confirmation_number(None, timestamp)

    assert conf1 == conf2
    assert conf1.startswith("WED-2025-")


def test_generate_confirmation_number_timezone_aware() -> None:
    """Timezone-aware timestamps should produce deterministic codes for the same tz-aware input."""
    tz_ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)

    conf1 = generate_confirmation_number("a@b.com", tz_ts)
    conf2 = generate_confirmation_number("a@b.com", tz_ts)

    assert conf1 == conf2


def test_get_password_hash_unique_and_verify() -> None:
    """Multiple hashes for same password should differ but both verify."""
    password = "repeated_password"

    hashed1 = get_password_hash(password)
    hashed2 = get_password_hash(password)

    assert hashed1 != hashed2
    assert verify_password(password, hashed1) is True
    assert verify_password(password, hashed2) is True


def test_decode_access_token_with_additional_fields() -> None:
    """Extra fields in the token payload should be ignored and decoding still succeed."""
    expire = datetime.now(UTC) + timedelta(minutes=10)
    payload_data = {
        "sub": "test_user",
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
        "role": "admin",
    }

    token = jwt.encode(payload_data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    payload = decode_access_token(token)

    assert payload is not None
    assert payload.sub == "test_user"
