"""Unit tests for configuration."""

import pytest
from pydantic import ValidationError

from wedding_api.config import Settings, settings


def test_settings_environment() -> None:
    """Test that settings load correctly."""
    assert settings.environment == "development"
    assert settings.database_url is not None


def test_settings_cors_origins_list() -> None:
    """Test CORS origins list property."""
    origins_list = settings.cors_origins_list

    assert isinstance(origins_list, list)
    assert len(origins_list) > 0
    assert "http://localhost:5173" in origins_list


def test_settings_is_development() -> None:
    """Test is_development property."""
    assert settings.is_development is True


def test_settings_is_production() -> None:
    """Test is_production property."""
    assert settings.is_production is False


def test_settings_rate_limits() -> None:
    """Test rate limit settings."""
    assert settings.rate_limit_rsvp == "1000/minute"  # Set in test conftest
    assert settings.rate_limit_admin_login == "1000/minute"  # Set in test conftest


def test_settings_jwt_config() -> None:
    """Test JWT configuration."""
    assert settings.jwt_secret_key == "test-secret-key-for-testing-only"
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expiration_minutes == 120  # Set in test conftest


def test_settings_reject_demo_secret_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    """The public demo JWT secret must never be accepted in production."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "demo-only-jwt-secret-do-not-use-in-production")

    with pytest.raises(ValidationError, match="public demo value"):
        Settings()


def test_settings_accept_demo_secret_in_development(monkeypatch: pytest.MonkeyPatch) -> None:
    """The demo JWT secret is allowed for local development."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("JWT_SECRET_KEY", "demo-only-jwt-secret-do-not-use-in-production")

    assert Settings().jwt_secret_key.startswith("demo-")
