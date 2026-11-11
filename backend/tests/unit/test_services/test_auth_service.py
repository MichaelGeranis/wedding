"""Unit tests for AuthService."""

from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.config import settings
from wedding_api.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_authenticate_admin_success(db_session: AsyncSession) -> None:
    """Test successful admin authentication."""
    service = AuthService(db_session)

    # The username "admin" with password "admin123" should match the test user
    token_response = await service.authenticate_admin("admin", "admin123")

    assert token_response is not None
    assert token_response.access_token is not None
    assert token_response.token_type == "bearer"
    assert token_response.expires_in > 0


@pytest.mark.asyncio
async def test_authenticate_admin_wrong_password(db_session: AsyncSession) -> None:
    """Test admin authentication with wrong password."""
    service = AuthService(db_session)

    token_response = await service.authenticate_admin("admin", "wrongpassword")

    assert token_response is None


@pytest.mark.asyncio
async def test_authenticate_admin_wrong_username(db_session: AsyncSession) -> None:
    """Test admin authentication with wrong username."""
    service = AuthService(db_session)

    token_response = await service.authenticate_admin("wronguser", "admin123")

    assert token_response is None


@pytest.mark.asyncio
async def test_authenticate_admin_empty_password(db_session: AsyncSession) -> None:
    """Test admin authentication with empty password."""
    service = AuthService(db_session)

    token_response = await service.authenticate_admin("admin", "")

    assert token_response is None


@pytest.mark.asyncio
async def test_token_expiration(db_session: AsyncSession) -> None:
    """Test that token has proper expiration."""
    service = AuthService(db_session)

    token_response = await service.authenticate_admin("admin", "admin123")

    assert token_response is not None
    # Token should expire roughly settings.jwt_expiration_minutes from now
    expected = settings.jwt_expiration_minutes * 60
    # allow small timing variance (a few seconds) between token creation and now
    assert abs(token_response.expires_in - expected) <= 5


@pytest.mark.asyncio
async def test_verify_admin_token_valid(db_session: AsyncSession) -> None:
    """Verify that a valid token created by authenticate_admin is accepted."""
    service = AuthService(db_session)

    token_response = await service.authenticate_admin("admin", "admin123")

    assert token_response is not None
    assert service.verify_admin_token(token_response.access_token) is True


@pytest.mark.asyncio
async def test_verify_admin_token_invalid_string(db_session: AsyncSession) -> None:
    """Invalid token strings should be rejected."""
    service = AuthService(db_session)

    assert service.verify_admin_token("not_a_valid_token") is False


@pytest.mark.asyncio
async def test_verify_admin_token_expired(db_session: AsyncSession) -> None:
    """Expired tokens should be rejected by verify_admin_token."""
    service = AuthService(db_session)

    expire = datetime.now(UTC) - timedelta(minutes=5)
    payload = {
        "sub": "admin",
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    assert service.verify_admin_token(token) is False


@pytest.mark.asyncio
async def test_verify_admin_token_wrong_secret(db_session: AsyncSession) -> None:
    """Tokens signed with the wrong secret should be rejected."""
    service = AuthService(db_session)

    expire = datetime.now(UTC) + timedelta(minutes=10)
    payload = {
        "sub": "admin",
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }

    token = jwt.encode(payload, "incorrect_secret", algorithm=settings.jwt_algorithm)

    assert service.verify_admin_token(token) is False


@pytest.mark.asyncio
async def test_verify_admin_token_empty_string(db_session: AsyncSession) -> None:
    """Empty token string should be rejected."""
    service = AuthService(db_session)

    assert service.verify_admin_token("") is False
