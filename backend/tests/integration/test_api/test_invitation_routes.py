"""Integration tests for Invitation API routes."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.database import Invitation


@pytest.mark.anyio
async def test_get_invitation_success(client: TestClient, db_session: AsyncSession) -> None:
    """Test getting invitation details when it exists."""
    # Create an invitation in database
    invitation = Invitation(
        bride_name="Sarah",
        groom_name="Michael",
        wedding_date="2025-06-15",
        wedding_time="16:00",  # Use 24-hour format
        venue_name="The Grand Ballroom",
        venue_address="123 Main Street",
        venue_city="New York",
        venue_state="NY",
        venue_zip="10001",
        venue_maps_url="https://maps.google.com/venue",
        rsvp_deadline="2025-06-01",
        church_name="St. Mary Church",
        church_address="10 Church Rd",
        church_city="New York",
        church_state="NY",
        church_zip="10001",
        church_maps_url="https://maps.google.com/church",
    )
    db_session.add(invitation)
    await db_session.commit()

    # Get the invitation
    response = client.get("/api/invitation")

    assert response.status_code == 200
    data = response.json()

    # Verify invitation data
    assert data["bride_name"] == "Sarah"
    assert data["groom_name"] == "Michael"
    assert "2025-06-15" in data["wedding_date"]


def test_get_invitation_not_found(client: TestClient, db_session: AsyncSession) -> None:
    """Test getting invitation when it doesn't exist."""
    # Don't create an invitation - table is empty

    response = client.get("/api/invitation")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
