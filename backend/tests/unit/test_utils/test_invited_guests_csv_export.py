"""Unit tests for invited guests CSV export functionality."""

from datetime import UTC, datetime, timezone

from wedding_api.models.invited_guest import InvitedGuestResponse
from wedding_api.utils.csv_export import generate_invited_guests_csv


def test_generate_invited_guests_csv_with_data() -> None:
    """Test CSV generation with invited guests data."""
    guests = [
        InvitedGuestResponse(
            id=1,
            name="John Doe",
            phone="1234567890",
            token="test-token-1",
            notes="Close friend",
            invitation_sent=True,
            created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
        ),
        InvitedGuestResponse(
            id=2,
            name="Jane Smith",
            phone="+30 698 765 4321",
            token="test-token-2",
            notes=None,
            invitation_sent=False,
            created_at=datetime(2025, 1, 16, 14, 20, 0, tzinfo=UTC),
            updated_at=datetime(2025, 1, 17, 9, 15, 0, tzinfo=UTC),
        ),
    ]

    csv_content = generate_invited_guests_csv(guests)

    # Verify header
    lines = csv_content.strip().split("\n")
    assert len(lines) == 3  # Header + 2 data rows
    assert "ID,Guest Name,Phone,Notes,Invitation Sent,Added At,Last Updated" in lines[0]

    # Verify first guest
    assert "1,John Doe,1234567890,Close friend,Yes,2025-01-15 10:30:00," in lines[1]

    # Verify second guest
    assert "2,Jane Smith,+30 698 765 4321,,No,2025-01-16 14:20:00,2025-01-17 09:15:00" in lines[2]


def test_generate_invited_guests_csv_empty_list() -> None:
    """Test CSV generation with empty guest list."""
    guests = []

    csv_content = generate_invited_guests_csv(guests)

    # Should only have header
    lines = csv_content.strip().split("\n")
    assert len(lines) == 1
    assert "ID,Guest Name,Phone,Notes,Invitation Sent,Added At,Last Updated" in lines[0]


def test_generate_invited_guests_csv_special_characters() -> None:
    """Test CSV generation with special characters in notes."""
    guests = [
        InvitedGuestResponse(
            id=1,
            name='Test "Guest"',
            phone="1234567890",
            token="test-token-special",
            notes='Has "quotes" and, commas',
            invitation_sent=False,
            created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
        ),
    ]

    csv_content = generate_invited_guests_csv(guests)

    # CSV module should properly escape quotes and commas
    assert 'Test "Guest"' in csv_content or 'Test ""Guest""' in csv_content
    assert "quotes" in csv_content
    assert "commas" in csv_content


def test_generate_invited_guests_csv_none_values() -> None:
    """Test CSV generation with None values."""
    guests = [
        InvitedGuestResponse(
            id=1,
            name="Test Guest",
            phone="1234567890",
            token="test-token-none",
            notes=None,
            invitation_sent=False,
            created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
        ),
    ]

    csv_content = generate_invited_guests_csv(guests)

    # None values should be represented as empty strings
    lines = csv_content.strip().split("\n")
    assert "Test Guest,1234567890,,No" in lines[1]


def test_generate_invited_guests_csv_sent_status() -> None:
    """Test CSV generation with different sent statuses."""
    guests = [
        InvitedGuestResponse(
            id=1,
            name="Sent Guest",
            phone="1234567890",
            token="test-token-sent",
            notes="",
            invitation_sent=True,
            created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
        ),
        InvitedGuestResponse(
            id=2,
            name="Not Sent Guest",
            phone="0987654321",
            token="test-token-notsent",
            notes="",
            invitation_sent=False,
            created_at=datetime(2025, 1, 16, 14, 20, 0, tzinfo=UTC),
            updated_at=None,
        ),
    ]

    csv_content = generate_invited_guests_csv(guests)

    # Verify sent status is correctly represented
    assert ",Yes," in csv_content  # First guest
    assert ",No," in csv_content  # Second guest


def test_generate_invited_guests_csv_preserves_order() -> None:
    """Test that CSV preserves the order of guests."""
    guests = [
        InvitedGuestResponse(
            id=3,
            name="Third",
            phone="3333333333",
            token="test-token-3",
            notes="",
            invitation_sent=False,
            created_at=datetime(2025, 1, 17, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
        ),
        InvitedGuestResponse(
            id=1,
            name="First",
            phone="1111111111",
            token="test-token-1",
            notes="",
            invitation_sent=False,
            created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
        ),
        InvitedGuestResponse(
            id=2,
            name="Second",
            phone="2222222222",
            token="test-token-2",
            notes="",
            invitation_sent=False,
            created_at=datetime(2025, 1, 16, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
        ),
    ]

    csv_content = generate_invited_guests_csv(guests)

    lines = csv_content.strip().split("\n")
    # Order should be: Third, First, Second (as given)
    assert "3,Third" in lines[1]
    assert "1,First" in lines[2]
    assert "2,Second" in lines[3]


def test_generate_invited_guests_csv_long_notes() -> None:
    """Test CSV generation with long notes text."""
    long_notes = "This is a very long note " * 20  # Create a long string

    guests = [
        InvitedGuestResponse(
            id=1,
            name="Guest With Long Notes",
            phone="1234567890",
            token="test-token-long",
            notes=long_notes,
            invitation_sent=False,
            created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
        ),
    ]

    csv_content = generate_invited_guests_csv(guests)

    # Should contain the full notes text
    assert long_notes in csv_content
