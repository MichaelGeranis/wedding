"""Integration tests for invited guest statistics routes."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


def test_get_stats_requires_auth(client: TestClient) -> None:
    """Test that stats endpoint requires authentication."""
    response = client.get("/api/admin/invited-guests/stats")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_stats_empty(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test stats with no invited guests."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/admin/invited-guests/stats", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_invited_base"] == 0
    assert data["total_children"] == 0
    assert data["total_plus_ones"] == 0
    assert data["total_invited"] == 0


def test_get_stats_with_guests(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test stats calculation with guests and tags."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create guests with various tags
    guests_data = [
        {"name": "Family A", "phone": "1111111111", "notes": "Bringing kids #child #child"},
        {"name": "Couple", "phone": "2222222222", "notes": "Partner invited #plusone"},
        {"name": "Solo Guest", "phone": "3333333333", "notes": "Just me"},
        {"name": "Large Family", "phone": "4444444444", "notes": "#child #child #child #plusone"},
    ]

    for guest_data in guests_data:
        response = client.post("/api/admin/invited-guests", json=guest_data, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED

    # Get stats
    response = client.get("/api/admin/invited-guests/stats", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_invited_base"] == 4  # 4 base guests
    assert data["total_children"] == 5  # 2 + 3 children
    assert data["total_plus_ones"] == 2  # 1 + 1 plus ones
    assert data["total_invited"] == 11  # 4 + 5 + 2

    # Clean up
    list_response = client.get("/api/admin/invited-guests", headers=headers)
    guests = list_response.json()["guests"]
    for guest in guests:
        client.delete(f"/api/admin/invited-guests/{guest['id']}", headers=headers)


def test_get_stats_case_insensitive(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test that tag matching is case-insensitive."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create guests with various case tags
    guests_data = [
        {"name": "Guest A", "phone": "1111111111", "notes": "#CHILD"},
        {"name": "Guest B", "phone": "2222222222", "notes": "#Child"},
        {"name": "Guest C", "phone": "3333333333", "notes": "#child"},
        {"name": "Guest D", "phone": "4444444444", "notes": "#PLUSONE"},
        {"name": "Guest E", "phone": "5555555555", "notes": "#PlusOne"},
    ]

    for guest_data in guests_data:
        response = client.post("/api/admin/invited-guests", json=guest_data, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED

    # Get stats
    response = client.get("/api/admin/invited-guests/stats", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_invited_base"] == 5
    assert data["total_children"] == 3
    assert data["total_plus_ones"] == 2
    assert data["total_invited"] == 10

    # Clean up
    list_response = client.get("/api/admin/invited-guests", headers=headers)
    guests = list_response.json()["guests"]
    for guest in guests:
        client.delete(f"/api/admin/invited-guests/{guest['id']}", headers=headers)


def test_get_stats_ignores_partial_matches(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test that partial word matches are not counted."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create guests with text that contains but is not exactly the tags
    guests_data = [
        {"name": "Guest A", "phone": "1111111111", "notes": "Has children but no tag"},
        {"name": "Guest B", "phone": "2222222222", "notes": "childhood memories #child"},
        {"name": "Guest C", "phone": "3333333333", "notes": "plusones not counted"},
    ]

    for guest_data in guests_data:
        response = client.post("/api/admin/invited-guests", json=guest_data, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED

    # Get stats
    response = client.get("/api/admin/invited-guests/stats", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_invited_base"] == 3
    assert data["total_children"] == 1  # Only the actual #child tag
    assert data["total_plus_ones"] == 0
    assert data["total_invited"] == 4

    # Clean up
    list_response = client.get("/api/admin/invited-guests", headers=headers)
    guests = list_response.json()["guests"]
    for guest in guests:
        client.delete(f"/api/admin/invited-guests/{guest['id']}", headers=headers)
