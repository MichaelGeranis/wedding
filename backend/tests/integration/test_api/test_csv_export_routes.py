"""Integration tests for CSV export routes."""

import csv
import io
from datetime import UTC, datetime

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.rsvp import RSVPCreate


def test_export_guests_csv_requires_auth(client: TestClient):
    """Test that CSV export requires authentication."""
    response = client.get("/api/admin/guests/export/csv")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_export_guests_csv_with_auth(client: TestClient, db_session: AsyncSession, admin_credentials: dict):
    """Test exporting guests as CSV with authentication."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]

    # Create some test RSVPs first
    rsvp1_data = {
        "guest_name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "attending": True,
        "dietary_restrictions": "Vegetarian",
    }

    rsvp2_data = {
        "guest_name": "Jane Smith",
        "email": "jane@example.com",
        "phone": "+9876543210",
        "attending": False,
    }

    # Submit RSVPs
    client.post("/api/rsvp", json=rsvp1_data)
    client.post("/api/rsvp", json=rsvp2_data)

    # Export CSV
    response = client.get(
        "/api/admin/guests/export/csv",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert "all_guests.csv" in response.headers["content-disposition"]

    # Parse CSV content
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Should have header + 2 data rows
    assert len(rows) >= 3
    assert rows[0][0] == "Guest Name"

    # Check that both guests are in the CSV
    guest_names = [row[0] for row in rows[1:]]
    assert "John Doe" in guest_names
    assert "Jane Smith" in guest_names


def test_export_guests_csv_filter_attending(client: TestClient, db_session: AsyncSession, admin_credentials: dict):
    """Test exporting only attending guests."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]

    # Create test RSVPs
    rsvp1_data = {
        "guest_name": "Attending Guest",
        "email": "attending@example.com",
        "phone": "+1111111111",
        "attending": True,
    }

    rsvp2_data = {
        "guest_name": "Not Attending Guest",
        "email": "notattending@example.com",
        "phone": "+2222222222",
        "attending": False,
    }

    client.post("/api/rsvp", json=rsvp1_data)
    client.post("/api/rsvp", json=rsvp2_data)

    # Export only attending guests
    response = client.get(
        "/api/admin/guests/export/csv?attending=true",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "guests_attending.csv" in response.headers["content-disposition"]

    # Parse CSV
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Check that only attending guest is included
    guest_names = [row[0] for row in rows[1:]]
    assert "Attending Guest" in guest_names
    assert "Not Attending Guest" not in guest_names


def test_export_guests_csv_filter_not_attending(client: TestClient, db_session: AsyncSession, admin_credentials: dict):
    """Test exporting only non-attending guests."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]

    # Create test RSVPs
    rsvp1_data = {
        "guest_name": "Attending Guest 2",
        "email": "attending2@example.com",
        "phone": "+3333333333",
        "attending": True,
    }

    rsvp2_data = {
        "guest_name": "Not Attending Guest 2",
        "email": "notattending2@example.com",
        "phone": "+4444444444",
        "attending": False,
    }

    client.post("/api/rsvp", json=rsvp1_data)
    client.post("/api/rsvp", json=rsvp2_data)

    # Export only not attending guests
    response = client.get(
        "/api/admin/guests/export/csv?attending=false",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "guests_not_attending.csv" in response.headers["content-disposition"]

    # Parse CSV
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Check that only non-attending guest is included
    guest_names = [row[0] for row in rows[1:]]
    assert "Not Attending Guest 2" in guest_names
    assert "Attending Guest 2" not in guest_names


def test_export_guest_summary_csv_requires_auth(client: TestClient):
    """Test that summary export requires authentication."""
    response = client.get("/api/admin/guests/export/summary")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_export_guest_summary_csv_with_auth(client: TestClient, db_session: AsyncSession, admin_credentials: dict):
    """Test exporting guest summary as CSV."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]

    # Create some test RSVPs
    rsvp1_data = {
        "guest_name": "Summary Guest 1",
        "email": "summary1@example.com",
        "phone": "+5555555555",
        "attending": True,
        "plus_one": True,
    }

    rsvp2_data = {
        "guest_name": "Summary Guest 2",
        "email": "summary2@example.com",
        "phone": "+6666666666",
        "attending": False,
    }

    client.post("/api/rsvp", json=rsvp1_data)
    client.post("/api/rsvp", json=rsvp2_data)

    # Export summary
    response = client.get(
        "/api/admin/guests/export/summary",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "wedding_rsvp_summary.csv" in response.headers["content-disposition"]

    # Parse CSV
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Check for summary sections
    assert rows[0][0] == "Wedding RSVP Summary"

    # Find statistics section
    stats_found = False
    for i, row in enumerate(rows):
        if row and row[0] == "Statistics":
            stats_found = True
            # Should have total count
            assert any("Total RSVPs" in r[0] for r in rows[i : i + 5] if r)
            break

    assert stats_found, "Statistics section not found"

    # Find guest list section
    guest_list_found = False
    for i, row in enumerate(rows):
        if row and row[0] == "Guest List":
            guest_list_found = True
            break

    assert guest_list_found, "Guest list section not found"


def test_export_empty_guest_list(client: TestClient, db_session: AsyncSession, admin_credentials: dict):
    """Test exporting CSV when there are no guests."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/admin/guests/export/csv",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK

    # Parse CSV
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Should only have header row
    assert len(rows) == 1
    assert rows[0][0] == "Guest Name"


def test_csv_contains_all_required_fields(client: TestClient, db_session: AsyncSession, admin_credentials: dict):
    """Test that CSV export contains all required fields."""
    # Login to get token
    login_response = client.post("/api/admin/login", json=admin_credentials)
    token = login_response.json()["access_token"]

    rsvp_data = {
        "guest_name": "Complete Data Guest",
        "email": "complete@example.com",
        "phone": "+7777777777",
        "attending": True,
        "dietary_restrictions": "No nuts",
        "plus_one": True,
        "message": "Test message",
    }

    client.post("/api/rsvp", json=rsvp_data)

    # Export CSV
    response = client.get(
        "/api/admin/guests/export/csv",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Parse CSV
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Check header has all expected columns
    header = rows[0]
    expected_columns = [
        "Guest Name",
        "Email",
        "Phone",
        "Attending",
        "Plus One",
        "Dietary Restrictions",
        "Message",
        "Confirmation Number",
        "Submitted At",
    ]

    for column in expected_columns:
        assert column in header, f"Column '{column}' not found in CSV header"

    # Check data row has values
    data_row = rows[1]
    assert data_row[0] == "Complete Data Guest"
    assert data_row[1] == "complete@example.com"
    assert data_row[2] == "7777777777"
    assert data_row[3] == "Yes"
    assert data_row[4] == "Yes"
    assert data_row[5] == "No nuts"
    assert data_row[6] == "Test message"
    assert data_row[7].startswith(f"WED-{datetime.now(UTC).year}-")  # Confirmation number
    assert len(data_row[8]) > 0  # Submitted at
