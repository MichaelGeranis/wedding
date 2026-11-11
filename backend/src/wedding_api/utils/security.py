"""Security utilities for password hashing and JWT tokens."""

import logging
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from wedding_api.config import settings
from wedding_api.models.admin import TokenPayload

logger = logging.getLogger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_access_token(subject: str) -> tuple[str, datetime]:
    """Create a JWT access token."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expiration_minutes)
    issued_at = datetime.now(UTC)

    payload = {
        "sub": subject,
        "exp": int(expire.timestamp()),
        "iat": int(issued_at.timestamp()),
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    return token, expire


def decode_access_token(token: str) -> TokenPayload | None:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        token_data = TokenPayload(**payload)
        return token_data
    except JWTError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        return None


def generate_confirmation_number(email: str | None, timestamp: datetime) -> str:
    """Generate a confirmation number for an RSVP."""
    # Use first 3 chars of email hash + last 3 chars of timestamp hash
    # If email is not provided, fallback to timestamp-based randomness
    email_hash = abs(hash(email)) % 1000 if email else abs(hash(timestamp.isoformat())) % 1000
    timestamp_hash = abs(hash(timestamp.isoformat())) % 1000

    year = timestamp.year
    code = f"{email_hash:03d}{timestamp_hash:03d}"

    return f"WED-{year}-{code.upper()}"
