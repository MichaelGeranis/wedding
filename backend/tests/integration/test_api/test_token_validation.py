"""Integration tests for token validation endpoint."""

import pytest
from fastapi.testclient import TestClient

from wedding_api.models.database import InvitedGuest


@pytest.mark.asyncio
async def test_get_guest_info_with_valid_token(client: TestClient, db_session) -> None:
    """Test getting guest info with a valid token."""
    # Create an invited guest with a token
    guest = InvitedGuest(
        name="Test Guest",
        phone="1234567890",
        token="test-token-123",
        notes="Test notes",
        invitation_sent=False,
    )
    db_session.add(guest)
    await db_session.commit()

    # Request guest info with the token
    response = client.get("/api/rsvp/guest-info", params={"token": "test-token-123"})

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Guest"
    assert data["phone"] == "1234567890"


def test_get_guest_info_with_invalid_token(client: TestClient) -> None:
    """Test getting guest info with an invalid token."""
    response = client.get("/api/rsvp/guest-info", params={"token": "invalid-token"})

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Invalid or expired token"


def test_get_guest_info_without_token(client: TestClient) -> None:
    """Test getting guest info without providing a token."""
    response = client.get("/api/rsvp/guest-info")

    # FastAPI should return 422 for missing required query parameter
    assert response.status_code == 422
