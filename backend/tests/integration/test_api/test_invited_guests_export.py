"""Integration tests for invited guests CSV export routes."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


def test_export_invited_guests_csv_requires_auth(client: TestClient) -> None:
    """Test that export endpoint requires authentication."""
    response = client.get("/api/admin/invited-guests/export/csv")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_export_invited_guests_csv_empty(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test CSV export with no invited guests."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]

    response = client.get("/api/admin/invited-guests/export/csv", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "content-disposition" in response.headers
    assert "invited_guests.csv" in response.headers["content-disposition"]

    # Should have header only
    lines = response.text.strip().split("\n")
    assert len(lines) == 1
    assert "ID,Guest Name,Phone,Notes,Invitation Sent,Added At,Last Updated" in lines[0]


def test_export_invited_guests_csv_with_data(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test CSV export with invited guests data."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create test guests
    guest1_data = {"name": "John Doe", "phone": "1234567890", "notes": "Close friend"}

    response1 = client.post("/api/admin/invited-guests", json=guest1_data, headers=headers)
    assert response1.status_code == status.HTTP_201_CREATED

    guest2_data = {"name": "Jane Smith", "phone": "0987654321", "notes": None}

    response2 = client.post("/api/admin/invited-guests", json=guest2_data, headers=headers)
    assert response2.status_code == status.HTTP_201_CREATED

    # Export CSV
    response = client.get("/api/admin/invited-guests/export/csv", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    # Verify CSV content
    csv_content = response.text
    assert "ID,Guest Name,Phone,Notes,Invitation Sent,Added At,Last Updated" in csv_content
    assert "John Doe" in csv_content
    assert "1234567890" in csv_content
    assert "Close friend" in csv_content
    assert "Jane Smith" in csv_content
    assert "0987654321" in csv_content

    # Clean up
    guest1_id = response1.json()["id"]
    guest2_id = response2.json()["id"]
    client.delete(f"/api/admin/invited-guests/{guest1_id}", headers=headers)
    client.delete(f"/api/admin/invited-guests/{guest2_id}", headers=headers)


def test_export_invited_guests_csv_includes_all_fields(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test that CSV export includes all required fields."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a guest with all fields
    guest_data = {
        "name": "Complete Guest",
        "phone": "5555555555",
        "notes": "Has all fields populated",
    }

    create_response = client.post("/api/admin/invited-guests", json=guest_data, headers=headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    guest_id = create_response.json()["id"]

    # Export CSV
    response = client.get("/api/admin/invited-guests/export/csv", headers=headers)

    assert response.status_code == status.HTTP_200_OK

    # Check all fields are present
    csv_lines = response.text.strip().split("\n")
    assert len(csv_lines) >= 2  # Header + at least one data row

    # Verify headers
    headers_line = csv_lines[0]
    assert "ID" in headers_line
    assert "Guest Name" in headers_line
    assert "Phone" in headers_line
    assert "Notes" in headers_line
    assert "Invitation Sent" in headers_line
    assert "Added At" in headers_line
    assert "Last Updated" in headers_line

    # Find the guest's row
    guest_row = None
    for line in csv_lines[1:]:
        if "Complete Guest" in line:
            guest_row = line
            break

    assert guest_row is not None
    assert "5555555555" in guest_row
    assert "Has all fields populated" in guest_row
    assert "No" in guest_row  # sent should be False by default

    # Clean up
    client.delete(f"/api/admin/invited-guests/{guest_id}", headers=headers)


def test_export_invited_guests_csv_special_characters(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test CSV export handles special characters correctly."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create guest with commas in notes (which need CSV escaping)
    guest_data = {"name": "Guest With Commas", "phone": "1234567890", "notes": "Has, commas, and stuff"}

    create_response = client.post("/api/admin/invited-guests", json=guest_data, headers=headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    guest_id = create_response.json()["id"]

    # Export CSV
    response = client.get("/api/admin/invited-guests/export/csv", headers=headers)

    assert response.status_code == status.HTTP_200_OK

    # CSV should properly handle notes with commas
    csv_content = response.text
    assert "Guest With Commas" in csv_content
    assert "commas" in csv_content
    assert "stuff" in csv_content

    # Clean up
    client.delete(f"/api/admin/invited-guests/{guest_id}", headers=headers)


def test_export_invited_guests_csv_sent_status(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    """Test CSV export shows correct invitation sent status."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create guest
    guest_data = {"name": "Test Guest", "phone": "1234567890", "notes": "Testing sent status"}

    create_response = client.post("/api/admin/invited-guests", json=guest_data, headers=headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    guest_id = create_response.json()["id"]

    # Update guest to mark as sent
    update_response = client.put(f"/api/admin/invited-guests/{guest_id}", json={"invitation_sent": True}, headers=headers)
    assert update_response.status_code == status.HTTP_200_OK

    # Export CSV
    response = client.get("/api/admin/invited-guests/export/csv", headers=headers)

    assert response.status_code == status.HTTP_200_OK

    # Find the guest's row
    csv_lines = response.text.strip().split("\n")
    guest_row = None
    for line in csv_lines[1:]:
        if "Test Guest" in line:
            guest_row = line
            break

    assert guest_row is not None
    assert "Yes" in guest_row  # sent should be True

    # Clean up
    client.delete(f"/api/admin/invited-guests/{guest_id}", headers=headers)
