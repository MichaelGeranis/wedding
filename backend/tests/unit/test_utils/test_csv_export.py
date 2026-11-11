"""Unit tests for CSV export utilities."""

import csv
import io
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from wedding_api.models.rsvp import RSVPResponse
from wedding_api.utils.csv_export import generate_guest_summary_csv, generate_rsvp_csv


@pytest.fixture
def sample_rsvps():
    """Create sample RSVP responses for testing."""
    return [
        RSVPResponse(
            id=uuid4(),
            guest_name="John Doe",
            email="john@example.com",
            phone="1234567890",
            attending=True,
            dietary_restrictions="Vegetarian",
            plus_one=True,
            message="Looking forward to it!",
            confirmation_number="WED-2026-ABC123",
            created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
        ),
        RSVPResponse(
            id=uuid4(),
            guest_name="Bob Smith",
            email="bob@example.com",
            phone="9876543210",
            attending=False,
            dietary_restrictions=None,
            plus_one=False,
            message=None,
            confirmation_number="WED-2026-XYZ789",
            created_at=datetime(2025, 1, 16, 14, 45, 0, tzinfo=UTC),
            updated_at=None,
        ),
        RSVPResponse(
            id=uuid4(),
            guest_name="Alice Johnson",
            email="alice@example.com",
            phone=None,
            attending=True,
            dietary_restrictions="Gluten-free",
            plus_one=False,
            message="Cannot wait!",
            confirmation_number="WED-2026-LMN456",
            created_at=datetime(2025, 1, 17, 9, 15, 0, tzinfo=UTC),
            updated_at=None,
        ),
    ]


def test_generate_rsvp_csv_with_data(sample_rsvps):
    """Test generating CSV with sample RSVP data."""
    csv_content = generate_rsvp_csv(sample_rsvps)

    # Parse CSV content
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Check header and rows
    assert len(rows) == 4  # 1 header + 3 data rows
    assert rows[0] == [
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

    # Check first data row (John Doe)
    assert rows[1][0] == "John Doe"
    assert rows[1][1] == "john@example.com"
    assert rows[1][2] == "1234567890"
    assert rows[1][3] == "Yes"
    assert rows[1][4] == "Yes"
    assert rows[1][5] == "Vegetarian"
    assert rows[1][6] == "Looking forward to it!"
    assert rows[1][7] == "WED-2026-ABC123"
    assert rows[1][8] == "2025-01-15 10:30:00"

    # Check second data row (Bob Smith - not attending)
    assert rows[2][0] == "Bob Smith"
    assert rows[2][3] == "No"
    assert rows[2][4] == "No"
    assert rows[2][5] == ""  # No dietary restrictions
    assert rows[2][6] == ""  # No message

    # Check third data row (Alice - no phone)
    assert rows[3][0] == "Alice Johnson"
    assert rows[3][2] == ""  # No phone


def test_generate_rsvp_csv_empty_list():
    """Test generating CSV with empty RSVP list."""
    csv_content = generate_rsvp_csv([])

    # Parse CSV content
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Should only have header
    assert len(rows) == 1
    assert rows[0][0] == "Guest Name"


def test_generate_rsvp_csv_with_special_characters():
    """Test generating CSV with special characters in data."""
    rsvp = RSVPResponse(
        id=uuid4(),
        guest_name='Test "Quote" User',
        email="test@example.com",
        phone="1234567890",
        attending=True,
        dietary_restrictions="No nuts, shellfish",
        plus_one=False,
        message="Message with, comma",
        confirmation_number="WED-2026-TST001",
        created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
        updated_at=None,
    )

    csv_content = generate_rsvp_csv([rsvp])

    # Parse CSV content
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # CSV module should handle special characters properly
    assert len(rows) == 2
    assert rows[1][0] == 'Test "Quote" User'
    assert rows[1][5] == "No nuts, shellfish"  # dietary_restrictions
    assert rows[1][6] == "Message with, comma"  # message


def test_generate_guest_summary_csv_with_data(sample_rsvps):
    """Test generating summary CSV with statistics and guest list."""
    stats = {
        "total": 3,
        "attending": 2,
        "not_attending": 1,
        "plus_ones": 1,
    }

    csv_content = generate_guest_summary_csv(stats, sample_rsvps)

    # Parse CSV content
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Check structure
    assert len(rows) > 10  # Header, stats, blank lines, guest list

    # Check title
    assert rows[0][0] == "Wedding RSVP Summary"

    # Check statistics section
    stats_found = False
    for i, row in enumerate(rows):
        if row and row[0] == "Statistics":
            stats_found = True
            assert rows[i + 1] == ["Total RSVPs", "3"]
            assert rows[i + 2] == ["Attending", "2"]
            assert rows[i + 3] == ["Not Attending", "1"]
            assert rows[i + 4] == ["Plus Ones", "1"]
            break

    assert stats_found, "Statistics section not found in CSV"

    # Check guest list header
    guest_list_found = False
    for i, row in enumerate(rows):
        if row and row[0] == "Guest List":
            guest_list_found = True
            # Next row should be headers
            assert rows[i + 1][0] == "Guest Name"
            # Following rows should be data
            assert rows[i + 2][0] == "John Doe"
            break

    assert guest_list_found, "Guest list section not found in CSV"


def test_generate_guest_summary_csv_empty_stats():
    """Test generating summary CSV with empty statistics."""
    stats = {
        "total": 0,
        "attending": 0,
        "not_attending": 0,
        "plus_ones": 0,
    }

    csv_content = generate_guest_summary_csv(stats, [])

    # Parse CSV content
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Check that stats show zeros
    for i, row in enumerate(rows):
        if row and row[0] == "Total RSVPs":
            assert row[1] == "0"
            break


def test_generate_guest_summary_csv_includes_timestamp():
    """Test that summary CSV includes generation timestamp."""
    csv_content = generate_guest_summary_csv({"total": 0, "attending": 0, "not_attending": 0}, [])

    # Parse CSV content
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Find Generated At row
    timestamp_found = False
    for row in rows:
        if row and row[0] == "Generated At":
            timestamp_found = True
            # Should have a timestamp value
            assert len(row[1]) > 0
            # Should be in format YYYY-MM-DD HH:MM:SS
            assert "-" in row[1]
            assert ":" in row[1]
            break

    assert timestamp_found, "Timestamp not found in summary CSV"


def test_generate_rsvp_csv_handles_none_values():
    """Test that CSV generation handles None values gracefully."""
    rsvp = RSVPResponse(
        id=uuid4(),
        guest_name="Minimal User",
        email="minimal@example.com",
        phone=None,
        attending=False,
        dietary_restrictions=None,
        plus_one=False,
        message=None,
        confirmation_number="WED-2026-MIN001",
        created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
        updated_at=None,
    )

    csv_content = generate_rsvp_csv([rsvp])

    # Parse CSV content
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Check that None values are converted to empty strings
    assert rows[1][2] == ""  # phone
    assert rows[1][5] == ""  # dietary_restrictions
    assert rows[1][6] == ""  # message
    assert rows[1][7] == "WED-2026-MIN001"  # confirmation_number


def test_csv_content_is_valid_csv():
    """Test that generated CSV content is valid and parseable."""
    rsvp = RSVPResponse(
        id=uuid4(),
        guest_name="Test User",
        email="test@example.com",
        phone="1234567890",
        attending=True,
        dietary_restrictions="None",
        plus_one=False,
        message="Test message",
        confirmation_number="WED-2026-TEST",
        created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
        updated_at=None,
    )

    csv_content = generate_rsvp_csv([rsvp])

    # Should not raise any exception when parsing
    try:
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)
        assert len(rows) == 2  # Header + 1 data row
    except csv.Error as e:
        pytest.fail(f"Generated CSV is not valid: {e}")


def test_generate_rsvp_csv_with_long_text():
    """Test CSV generation with very long text in fields."""
    long_message = "A" * 1000  # Very long message

    rsvp = RSVPResponse(
        id=uuid4(),
        guest_name="Long Message User",
        email="long@example.com",
        phone="1234567890",
        attending=True,
        dietary_restrictions="Very long dietary restrictions: " + "B" * 500,
        plus_one=False,
        message=long_message,
        confirmation_number="WED-2026-LONG",
        created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
        updated_at=None,
    )

    csv_content = generate_rsvp_csv([rsvp])

    # Parse CSV content
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Should handle long text without issues
    assert len(rows) == 2
    assert rows[1][6] == long_message  # message column


def test_generate_rsvp_csv_preserves_order():
    """Test that CSV preserves the order of RSVPs."""
    rsvps = [
        RSVPResponse(
            id=uuid4(),
            guest_name=f"Guest {i}",
            email=f"guest{i}@example.com",
            phone=f"123456789{i}",
            attending=True,
            dietary_restrictions=None,
            plus_one=False,
            message=None,
            confirmation_number=f"WED-2026-{i:03d}",
            created_at=datetime(2025, 1, 15 + i, 10, 30, 0, tzinfo=UTC),
            updated_at=None,
        )
        for i in range(5)
    ]

    csv_content = generate_rsvp_csv(rsvps)

    # Parse CSV content
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    # Check order is preserved
    for i in range(5):
        assert rows[i + 1][0] == f"Guest {i}"
        assert rows[i + 1][7] == f"WED-2026-{i:03d}"  # confirmation_number column
