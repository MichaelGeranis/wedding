"""Integration tests for Admin API routes."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


def test_admin_login_success(client: TestClient, admin_credentials: dict) -> None:
    """Test successful admin login."""
    response = client.post("/api/admin/login", json=admin_credentials)

    assert response.status_code == 200
    data = response.json()

    # Verify token response
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_admin_login_invalid_password(client: TestClient) -> None:
    """Test admin login with invalid password."""
    response = client.post("/api/admin/login", json={"username": "admin", "password": "wrongpassword"})

    assert response.status_code == 401
    assert "invalid credentials" in response.json()["detail"].lower()


def test_get_guests_without_auth(client: TestClient, db_session: AsyncSession) -> None:
    """Test that getting guests without auth returns 401."""
    response = client.get("/api/admin/guests")

    assert response.status_code == 401  # No authorization header


def test_get_guests_with_invalid_token(client: TestClient, db_session: AsyncSession) -> None:
    """Test that getting guests with invalid token returns 401."""
    response = client.get("/api/admin/guests", headers={"Authorization": "Bearer invalid_token"})

    assert response.status_code == 401


def test_get_guests_success(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test getting guest list with valid auth."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]

    # Create some RSVPs first
    client.post(
        "/api/rsvp",
        json={
            "guest_name": "Guest 1",
            "email": "guest1@example.com",
            "attending": True,
        },
    )
    client.post(
        "/api/rsvp",
        json={"guest_name": "Guest 2", "email": "guest2@example.com", "attending": False},
    )

    # Get guests
    response = client.get("/api/admin/guests", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "guests" in data
    assert data["total"] == 2
    assert len(data["guests"]) == 2


def test_get_guests_filter_attending(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test filtering guests by attendance status."""
    # Login
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]

    # Create RSVPs
    client.post(
        "/api/rsvp",
        json={
            "guest_name": "Attending",
            "email": "attending@example.com",
            "attending": True,
        },
    )
    client.post(
        "/api/rsvp",
        json={
            "guest_name": "Not Attending",
            "email": "notattending@example.com",
            "attending": False,
        },
    )

    # Get only attending guests
    response = client.get("/api/admin/guests?attending=true", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert len(data["guests"]) == 1
    assert data["guests"][0]["attending"] is True


def test_get_guests_pagination(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test guest list pagination."""
    # Login
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]

    # Create multiple RSVPs
    for i in range(5):
        client.post(
            "/api/rsvp",
            json={
                "guest_name": f"Guest {i}",
                "email": f"guest{i}@example.com",
                "attending": True,
            },
        )

    # Get first page (limit 2)
    response = client.get("/api/admin/guests?limit=2&offset=0", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["guests"]) == 2

    # Get second page
    response = client.get("/api/admin/guests?limit=2&offset=2", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["offset"] == 2
    assert len(data["guests"]) == 2


def test_get_rsvp_stats(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test getting RSVP statistics."""
    # Login
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]

    # Create RSVPs
    for i in range(3):
        client.post(
            "/api/rsvp",
            json={
                "guest_name": f"Attending {i}",
                "email": f"attending{i}@example.com",
                "attending": True,
            },
        )

    for i in range(2):
        client.post(
            "/api/rsvp",
            json={
                "guest_name": f"Not Attending {i}",
                "email": f"notattending{i}@example.com",
                "attending": False,
            },
        )

    # Get stats
    response = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    assert "attending" in data
    assert "not_attending" in data
    assert "total" in data
    assert data["attending"] == 3
    assert data["not_attending"] == 2
    assert data["total"] == 5


def test_stats_without_auth(client: TestClient) -> None:
    """Test that stats endpoint requires auth."""
    response = client.get("/api/admin/stats")

    assert response.status_code == 401  # No authorization header
