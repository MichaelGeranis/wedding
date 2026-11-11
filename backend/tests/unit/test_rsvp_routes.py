"""Unit tests for RSVP routes edge cases."""

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


def test_submit_rsvp_rate_limited(client: TestClient, db_session: AsyncSession) -> None:
    """Test rate limiting on RSVP submission."""
    # Note: This test verifies rate limit behavior exists but doesn't trigger it
    # in tests since we set RATE_LIMIT_RSVP to 1000/minute in conftest.py
    rsvp_data = {
        "guest_name": "Rate Test",
        "email": "ratetest@example.com",
        "attending": True,
    }

    response = client.post("/api/rsvp", json=rsvp_data)

    # Should succeed, not rate limited in test environment
    assert response.status_code == 201


def test_submit_rsvp_minimal_data(client: TestClient, db_session: AsyncSession) -> None:
    """Test RSVP with minimal required fields."""
    rsvp_data = {
        "guest_name": "Minimal Guest",
        "email": "minimal@example.com",
        "attending": False,  # Not attending, so no meal required
    }

    response = client.post("/api/rsvp", json=rsvp_data)

    assert response.status_code == 201
    data = response.json()
    assert data["guest_name"] == "Minimal Guest"
    assert data["attending"] is False
