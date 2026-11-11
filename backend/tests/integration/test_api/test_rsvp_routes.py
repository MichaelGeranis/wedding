"""Integration tests for RSVP API routes."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


def test_submit_rsvp_success(client: TestClient, db_session: AsyncSession, sample_rsvp_data: dict) -> None:
    """Test successful RSVP submission."""
    response = client.post("/api/rsvp", json=sample_rsvp_data)

    assert response.status_code == 201
    data = response.json()

    # Verify response structure
    assert "id" in data
    assert "confirmation_number" in data
    assert data["guest_name"] == sample_rsvp_data["guest_name"]
    assert data["email"] == sample_rsvp_data["email"].lower()  # Email should be normalized
    assert data["attending"] == sample_rsvp_data["attending"]
    assert data["confirmation_number"].startswith("WED-")


def test_submit_rsvp_validation_errors(client: TestClient, db_session: AsyncSession) -> None:
    """Test RSVP validation errors."""
    # guest_name too short (min_length=2)
    invalid_data = {
        "guest_name": "A",  # Too short - should fail validation
        "email": "test@example.com",
        "attending": True,
    }

    response = client.post("/api/rsvp", json=invalid_data)
    assert response.status_code == 422  # Validation error


def test_submit_rsvp_plus_one_without_name(client: TestClient, db_session: AsyncSession) -> None:
    """Test that plus-one requires name when attending."""
    data = {
        "guest_name": "Test Guest",
        "email": "test@example.com",
        "attending": True,
        "plus_one": True,
        # Missing plus_one_name
    }

    response = client.post("/api/rsvp", json=data)
    # Now allowed: plus_one is a boolean flag only, so request should succeed
    assert response.status_code == 201


def test_submit_rsvp_not_attending(client: TestClient, db_session: AsyncSession) -> None:
    """Test RSVP for guest not attending."""
    data = {
        "guest_name": "Test Guest",
        "email": "notattending@example.com",
        "attending": False,
        # No meal preference needed
    }

    response = client.post("/api/rsvp", json=data)
    assert response.status_code == 201

    result = response.json()
    assert result["attending"] is False


def test_submit_rsvp_with_dietary_restrictions(client: TestClient, db_session: AsyncSession) -> None:
    """Test RSVP with dietary restrictions."""
    data = {
        "guest_name": "Test Guest",
        "email": "dietary@example.com",
        "attending": True,
        "dietary_restrictions": "No nuts, gluten-free",
    }

    response = client.post("/api/rsvp", json=data)
    assert response.status_code == 201

    result = response.json()
    assert result["dietary_restrictions"] == "No nuts, gluten-free"


def test_submit_rsvp_email_normalization(client: TestClient, db_session: AsyncSession) -> None:
    """Test that email is normalized to lowercase."""
    data = {
        "guest_name": "Test Guest",
        "email": "Test.USER@Example.COM",
        "attending": True,
    }

    response = client.post("/api/rsvp", json=data)
    assert response.status_code == 201

    result = response.json()
    assert result["email"] == "test.user@example.com"


def test_submit_rsvp_duplicate_returns_friendly_error(client: TestClient, db_session: AsyncSession, sample_rsvp_data: dict) -> None:
    """Submitting a duplicate RSVP should return a 4xx and a friendly error message."""
    # First submission succeeds
    response1 = client.post("/api/rsvp", json=sample_rsvp_data)
    assert response1.status_code == 201

    # Second submission with the same payload should be rejected
    response2 = client.post("/api/rsvp", json=sample_rsvp_data)

    assert response2.status_code in (400, 409)
    data = response2.json()

    # API should return a helpful message in the 'detail' field
    assert isinstance(data, dict)
    # Standardized response contains 'error' and 'detail'
    assert "error" in data
    msg = data.get("detail") or ""
    assert "already exists" in msg.lower()


def test_duplicate_by_email_returns_conflict(client: TestClient, db_session: AsyncSession) -> None:
    """Two different submissions with same email must be rejected as duplicate."""
    data1 = {
        "guest_name": "Alice One",
        "email": "duplicate@example.com",
        "attending": True,
    }

    data2 = {
        "guest_name": "Alice Two",
        "email": "duplicate@example.com",  # same email
        "attending": False,
    }

    r1 = client.post("/api/rsvp", json=data1)
    assert r1.status_code == 201

    r2 = client.post("/api/rsvp", json=data2)
    assert r2.status_code == 409
    body = r2.json()
    assert "error" in body
    assert "already exists" in body.get("detail", "").lower()


def test_duplicate_by_phone_with_normalization(client: TestClient, db_session: AsyncSession) -> None:
    """Phone numbers should be normalized and duplicates rejected even with different formatting."""
    data1 = {
        "guest_name": "Phone One",
        "email": "phone1@example.com",
        "phone": "(555) 123-4567",
        "attending": True,
    }

    data2 = {
        "guest_name": "Phone Two",
        "email": "phone2@example.com",
        "phone": "5551234567",  # same digits, different formatting
        "attending": True,
    }

    r1 = client.post("/api/rsvp", json=data1)
    assert r1.status_code == 201

    r2 = client.post("/api/rsvp", json=data2)
    assert r2.status_code == 409
    body = r2.json()
    assert "error" in body
    assert "phone" in body.get("detail", "").lower() or "already exists" in body.get("detail", "").lower()


def test_duplicate_by_guest_name_returns_conflict(client: TestClient, db_session: AsyncSession) -> None:
    """Guest name duplicates should be rejected even if other fields differ."""
    data1 = {
        "guest_name": "Sam Same",
        "email": "sam1@example.com",
        "attending": True,
    }

    data2 = {
        "guest_name": "Sam Same",  # same guest name
        "email": "sam2@example.com",
        "attending": False,
    }

    r1 = client.post("/api/rsvp", json=data1)
    assert r1.status_code == 201

    r2 = client.post("/api/rsvp", json=data2)
    assert r2.status_code == 409
    body = r2.json()
    assert "error" in body
    assert "guest" in body.get("detail", "").lower() or "already exists" in body.get("detail", "").lower()


def test_phone_null_allows_multiple_submissions(client: TestClient, db_session: AsyncSession) -> None:
    """When phone is not provided (null), multiple RSVPs should be allowed (NULLs are not unique)."""
    data1 = {
        "guest_name": "No Phone One",
        "email": "nophone1@example.com",
        "attending": True,
    }

    data2 = {
        "guest_name": "No Phone Two",
        "email": "nophone2@example.com",
        "attending": False,
    }

    r1 = client.post("/api/rsvp", json=data1)
    assert r1.status_code == 201

    r2 = client.post("/api/rsvp", json=data2)
    # Should succeed because phone is NULL for both and NULLs are not considered equal in unique constraints
    assert r2.status_code == 201


def test_partial_phone_numbers_do_not_conflict(client: TestClient, db_session: AsyncSession) -> None:
    """Ensure that phone numbers that differ (e.g., missing last digit) are not treated as duplicates."""
    data1 = {
        "guest_name": "Partial Phone One",
        "email": "partial1@example.com",
        "phone": "555-123-4567",
        "attending": True,
    }

    data2 = {
        "guest_name": "Partial Phone Two",
        "email": "partial2@example.com",
        "phone": "555-123-4568",  # different last digit (valid length)
        "attending": True,
    }

    r1 = client.post("/api/rsvp", json=data1)
    assert r1.status_code == 201

    r2 = client.post("/api/rsvp", json=data2)
    # Should succeed because after normalization the numbers differ
    assert r2.status_code == 201
