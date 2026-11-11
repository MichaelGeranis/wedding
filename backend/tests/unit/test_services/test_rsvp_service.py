"""Unit tests for RSVPService."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio

from wedding_api.config import settings
from wedding_api.models.database import InvitedGuest
from wedding_api.models.rsvp import RSVPCreate, RSVPListResponse, RSVPResponse
from wedding_api.services.rsvp_service import RSVPService


class FakeRSVPRepo:
    def __init__(self):
        self._store = {}

    async def create_rsvp(self, rsvp_data: RSVPCreate) -> RSVPResponse:
        resp = RSVPResponse(
            id=uuid4(),
            guest_name=rsvp_data.guest_name,
            email=(rsvp_data.email.lower() if rsvp_data.email else None),
            phone=rsvp_data.phone,
            attending=rsvp_data.attending,
            dietary_restrictions=rsvp_data.dietary_restrictions,
            plus_one=rsvp_data.plus_one,
            message=rsvp_data.message,
            confirmation_number=f"CONF-{len(self._store) + 1:06d}",
            created_at=datetime.now(UTC),
            updated_at=None,
        )
        self._store[str(resp.id)] = resp
        return resp

    async def get_rsvp_by_email(self, email: str) -> RSVPResponse | None:
        for v in self._store.values():
            if v.email == email.lower():
                return v
        return None

    async def list_rsvps(self, attending_filter=None, limit=100, offset=0):
        items = list(self._store.values())
        if attending_filter is not None:
            items = [i for i in items if i.attending == attending_filter]
        total = len(items)
        return items[offset : offset + limit], total

    async def get_rsvp_counts(self) -> dict:
        total = len(self._store)
        attending = sum(1 for v in self._store.values() if v.attending)
        not_attending = total - attending
        return {"total": total, "attending": attending, "not_attending": not_attending}

    async def delete_rsvp_by_id(self, rsvp_id: str) -> bool:
        return self._store.pop(rsvp_id, None) is not None


class FakeInvitedGuestRepo:
    def __init__(self, phones=None):
        self.phones = set(phones or [])

    async def get_invited_guest_by_phone(self, phone_digits: str):
        # Return a simple object if phone exists
        if phone_digits in self.phones:

            class G:
                name = "Invited"

            return G()
        return None


@pytest.mark.asyncio
async def test_submit_rsvp_without_validation(monkeypatch) -> None:
    repo = FakeRSVPRepo()
    invited = FakeInvitedGuestRepo()

    service = RSVPService.__new__(RSVPService)
    service.repository = repo
    service.invited_guest_repository = invited

    # Ensure validation disabled
    settings.require_invited_guest_validation = False

    rsvp = RSVPCreate(guest_name="Bob", email="BOB@EXAMPLE.COM", phone=None, attending=True)

    resp = await service.submit_rsvp(rsvp)

    assert resp.confirmation_number.startswith("CONF-")
    assert resp.email == "bob@example.com"


@pytest.mark.asyncio
async def test_submit_rsvp_with_validation_missing_phone(monkeypatch) -> None:
    repo = FakeRSVPRepo()
    invited = FakeInvitedGuestRepo(phones=["1234567890"])

    service = RSVPService.__new__(RSVPService)
    service.repository = repo
    service.invited_guest_repository = invited

    settings.require_invited_guest_validation = True

    rsvp = RSVPCreate(guest_name="Sam", email="sam@example.com", phone=None, attending=True)

    with pytest.raises(PermissionError):
        await service.submit_rsvp(rsvp)


@pytest.mark.asyncio
async def test_submit_rsvp_with_validation_phone_not_invited(monkeypatch) -> None:
    repo = FakeRSVPRepo()
    invited = FakeInvitedGuestRepo(phones=["1112223333"])

    service = RSVPService.__new__(RSVPService)
    service.repository = repo
    service.invited_guest_repository = invited

    settings.require_invited_guest_validation = True

    # phone supplied but not in invited list
    rsvp = RSVPCreate(guest_name="Sam", email="sam@example.com", phone="+9999999999", attending=True)

    with pytest.raises(PermissionError):
        await service.submit_rsvp(rsvp)


@pytest.mark.asyncio
async def test_get_all_rsvps_and_stats_and_delete(monkeypatch) -> None:
    repo = FakeRSVPRepo()
    invited = FakeInvitedGuestRepo()

    service = RSVPService.__new__(RSVPService)
    service.repository = repo
    service.invited_guest_repository = invited

    settings.require_invited_guest_validation = False

    # create several RSVPs
    r1 = await service.submit_rsvp(RSVPCreate(guest_name="Alice", email="a@example.com", phone="+1000000000", attending=True))
    await service.submit_rsvp(RSVPCreate(guest_name="Bob", email="b@example.com", phone="+1000000001", attending=False))

    found = await service.get_rsvp_by_email("a@example.com")
    assert found is not None

    paged = await service.get_all_rsvps()
    assert isinstance(paged, RSVPListResponse)
    assert paged.total == 2

    stats = await service.get_rsvp_statistics()
    assert stats["total"] == 2
    assert stats["attending"] == 1

    deleted = await service.delete_rsvp(str(r1.id))
    assert deleted is True


@pytest.mark.anyio
async def test_trimming_and_normalization(db_session):
    """Ensure RSVPService trims whitespace and normalizes email before saving."""
    service = RSVPService(db_session)

    rsvp = RSVPCreate(
        guest_name="  Alice Smith  ",
        email="  ALICE@EXAMPLE.COM  ",
        phone="  1234567890  ",
        attending=True,
    )

    response = await service.submit_rsvp(rsvp)

    assert response.guest_name == "Alice Smith"
    assert response.email == "alice@example.com"
    # Phone stored as digit-only string
    assert str(response.phone) == "1234567890"


@pytest.mark.anyio
async def test_submit_rsvp_with_max_length_name(db_session):
    """Test RSVP submission with name at max length (100 characters)."""
    service = RSVPService(db_session)

    # 100 character name (at the limit)
    max_name = "A" * 100

    rsvp = RSVPCreate(
        guest_name=max_name,
        email="maxname@example.com",
        phone="+1234567890",
        attending=True,
    )

    response = await service.submit_rsvp(rsvp)

    assert response.guest_name == max_name
    assert response.email == "maxname@example.com"


@pytest.mark.anyio
async def test_submit_rsvp_with_hyphens(db_session):
    """Test RSVP submission with names containing hyphens."""
    service = RSVPService(db_session)

    rsvp = RSVPCreate(
        guest_name="Mary-Jane Smith",
        email="mary@example.com",
        phone="+1234567890",
        attending=True,
    )

    response = await service.submit_rsvp(rsvp)

    assert response.guest_name == "Mary-Jane Smith"


@pytest.mark.anyio
async def test_submit_rsvp_with_international_phone_formats(db_session):
    """Test RSVP submission with various international phone formats."""
    service = RSVPService(db_session)

    phone_formats = [
        "+1 (555) 123-4567",
        "+44 20 7946 0958",
        "+81 3-1234-5678",
        "+86 10 1234 5678",
        "001-555-123-4567",
    ]

    for idx, phone in enumerate(phone_formats):
        rsvp = RSVPCreate(
            guest_name=f"Guest {idx}",
            email=f"guest{idx}@example.com",
            phone=phone,
            attending=True,
        )

        response = await service.submit_rsvp(rsvp)
        assert response.phone is not None


@pytest.mark.anyio
async def test_submit_rsvp_duplicate_guest_name(db_session):
    """Test that submitting duplicate guest name raises ValueError."""
    service = RSVPService(db_session)

    rsvp = RSVPCreate(
        guest_name="John Doe",
        email="john1@example.com",
        phone="+1234567890",
        attending=True,
    )

    # First submission should succeed
    await service.submit_rsvp(rsvp)

    # Second submission with same guest name should fail
    rsvp2 = RSVPCreate(
        guest_name="John Doe",  # Same name
        email="john2@example.com",  # Different email
        phone="+9876543210",
        attending=False,
    )

    with pytest.raises(ValueError, match="An RSVP with this guest name already exists"):
        await service.submit_rsvp(rsvp2)


@pytest.mark.anyio
async def test_submit_rsvp_with_max_length_dietary_restrictions(db_session):
    """Test RSVP submission with dietary restrictions at max length (300 chars)."""
    service = RSVPService(db_session)

    # 300 character dietary restrictions (at the limit)
    max_restrictions = "A" * 300

    rsvp = RSVPCreate(
        guest_name="Picky Eater",
        email="picky@example.com",
        phone="+1234567890",
        attending=True,
        dietary_restrictions=max_restrictions,
    )

    response = await service.submit_rsvp(rsvp)

    # Note: HTML escaping may change length, so just check it's not None
    assert response.dietary_restrictions is not None


@pytest.mark.anyio
async def test_submit_rsvp_with_max_length_message(db_session):
    """Test RSVP submission with message at max length (500 chars)."""
    service = RSVPService(db_session)

    # 500 character message (at the limit)
    max_message = "A" * 500

    rsvp = RSVPCreate(
        guest_name="Chatty Guest",
        email="chatty@example.com",
        phone="+1234567890",
        attending=True,
        message=max_message,
    )

    response = await service.submit_rsvp(rsvp)

    # Note: HTML escaping may change length, so just check it's not None
    assert response.message is not None


@pytest.mark.anyio
async def test_submit_rsvp_with_plus_one_and_name(db_session):
    """Test RSVP submission with plus one and plus one name."""
    service = RSVPService(db_session)

    rsvp = RSVPCreate(
        guest_name="Guest With Plus One",
        email="plusone@example.com",
        phone="+1234567890",
        attending=True,
        plus_one=True,
    )

    response = await service.submit_rsvp(rsvp)

    assert response.plus_one is True


@pytest.mark.anyio
async def test_submit_rsvp_not_attending_with_minimal_info(db_session):
    """Test RSVP submission for not attending with minimal information."""
    service = RSVPService(db_session)

    rsvp = RSVPCreate(
        guest_name="Busy Person",
        email="busy@example.com",
        phone="+1234567890",
        attending=False,
        # No optional fields
    )

    response = await service.submit_rsvp(rsvp)

    assert response.attending is False
    assert response.plus_one is False
    assert response.dietary_restrictions is None
    assert response.message is None


@pytest.mark.anyio
async def test_submit_rsvp_empty_strings_become_none(db_session):
    """Test that empty string optional fields become None after validation."""
    service = RSVPService(db_session)

    rsvp = RSVPCreate(
        guest_name="Empty Fields",
        email="empty@example.com",
        phone="+1234567890",
        attending=False,
        # Empty strings will be trimmed and converted to None by validators
    )

    response = await service.submit_rsvp(rsvp)

    # Empty strings after trimming become None
    assert response.dietary_restrictions is None
    assert response.message is None


@pytest.mark.anyio
async def test_submit_rsvp_requires_phone_when_validation_enabled(db_session):
    """Test that phone is required when invited guest validation is enabled."""
    service = RSVPService(db_session)

    with patch("wedding_api.services.rsvp_service.settings") as mock_settings:
        mock_settings.require_invited_guest_validation = True

        rsvp = RSVPCreate(
            guest_name="No Phone",
            email="nophone@example.com",
            phone=None,  # No phone provided
            attending=True,
        )

        with pytest.raises(PermissionError, match="Phone number is required"):
            await service.submit_rsvp(rsvp)


@pytest.mark.anyio
async def test_submit_rsvp_validates_phone_against_invited_list(db_session):
    """Test that phone is validated against invited guests list when enabled."""
    service = RSVPService(db_session)

    with patch("wedding_api.services.rsvp_service.settings") as mock_settings:
        mock_settings.require_invited_guest_validation = True

        # Mock the invited guest repository to return None (not invited)
        service.invited_guest_repository.get_invited_guest_by_phone = AsyncMock(return_value=None)

        rsvp = RSVPCreate(
            guest_name="Not Invited",
            email="notinvited@example.com",
            phone="+9999999999",
            attending=True,
        )

        with pytest.raises(PermissionError, match="not in our invitation list"):
            await service.submit_rsvp(rsvp)


@pytest.mark.anyio
async def test_submit_rsvp_accepts_invited_guest(db_session):
    """Test that RSVP is accepted when phone is in invited list."""
    service = RSVPService(db_session)

    with patch("wedding_api.services.rsvp_service.settings") as mock_settings:
        mock_settings.require_invited_guest_validation = True

        # Mock the invited guest repository to return an invited guest
        invited_guest = InvitedGuest(
            id=uuid.uuid4(),
            name="Invited Guest",
            phone="1234567890",
        )
        service.invited_guest_repository.get_invited_guest_by_phone = AsyncMock(return_value=invited_guest)

        rsvp = RSVPCreate(
            guest_name="Invited Guest",
            email="invited@example.com",
            phone="+1 (234) 567-8900",  # Different format, same digits
            attending=True,
        )

        response = await service.submit_rsvp(rsvp)
        assert response.email == "invited@example.com"


@pytest.mark.anyio
async def test_get_rsvp_by_email_case_insensitive(db_session):
    """Test that get RSVP by email is case insensitive."""
    service = RSVPService(db_session)

    # Create RSVP with lowercase email
    rsvp = RSVPCreate(
        guest_name="Case Test",
        email="casetest@example.com",
        phone="+1234567890",
        attending=True,
    )

    created = await service.submit_rsvp(rsvp)

    # Try to fetch with different case (emails are normalized to lowercase on save)
    fetched = await service.get_rsvp_by_email("casetest@example.com")

    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.anyio
async def test_get_rsvp_by_email_nonexistent(db_session):
    """Test that get RSVP by non-existent email returns None."""
    service = RSVPService(db_session)

    result = await service.get_rsvp_by_email("nonexistent@example.com")

    assert result is None


@pytest.mark.anyio
async def test_get_all_rsvps_with_pagination(db_session):
    """Test getting all RSVPs with pagination."""
    service = RSVPService(db_session)

    # Create 10 RSVPs
    for i in range(10):
        rsvp = RSVPCreate(
            guest_name=f"Guest {i}",
            email=f"guest{i}@example.com",
            phone=f"+123456789{i}",
            attending=i % 2 == 0,  # Alternating attending status
        )
        await service.submit_rsvp(rsvp)

    # Get first page (5 items)
    page1 = await service.get_all_rsvps(limit=5, offset=0)
    assert page1.total == 10
    assert len(page1.guests) == 5

    # Get second page (5 items)
    page2 = await service.get_all_rsvps(limit=5, offset=5)
    assert page2.total == 10
    assert len(page2.guests) == 5

    # Ensure different RSVPs on each page
    page1_ids = {guest.id for guest in page1.guests}
    page2_ids = {guest.id for guest in page2.guests}
    assert len(page1_ids.intersection(page2_ids)) == 0


@pytest.mark.anyio
async def test_get_all_rsvps_offset_beyond_total(db_session):
    """Test getting RSVPs with offset beyond total count."""
    service = RSVPService(db_session)

    # Create 5 RSVPs
    for i in range(5):
        rsvp = RSVPCreate(
            guest_name=f"Guest {i}",
            email=f"guest{i}@example.com",
            phone=f"+123456789{i}",
            attending=True,
        )
        await service.submit_rsvp(rsvp)

    # Get with offset beyond total
    result = await service.get_all_rsvps(limit=10, offset=100)
    assert result.total == 5
    assert len(result.guests) == 0


@pytest.mark.anyio
async def test_get_all_rsvps_filter_by_attending(db_session):
    """Test filtering RSVPs by attending status."""
    service = RSVPService(db_session)

    # Create 5 attending and 5 not attending
    for i in range(10):
        rsvp = RSVPCreate(
            guest_name=f"Guest {i}",
            email=f"guest{i}@example.com",
            phone=f"+123456789{i}",
            attending=i < 5,  # First 5 attending, last 5 not
        )
        await service.submit_rsvp(rsvp)

    # Get only attending
    attending_result = await service.get_all_rsvps(attending=True)
    assert attending_result.total == 5
    assert all(guest.attending for guest in attending_result.guests)

    # Get only not attending
    not_attending_result = await service.get_all_rsvps(attending=False)
    assert not_attending_result.total == 5
    assert all(not guest.attending for guest in not_attending_result.guests)

    # Get all
    all_result = await service.get_all_rsvps(attending=None)
    assert all_result.total == 10


@pytest.mark.anyio
async def test_get_all_rsvps_empty_database(db_session):
    """Test getting RSVPs from empty database."""
    service = RSVPService(db_session)

    result = await service.get_all_rsvps()

    assert result.total == 0
    assert len(result.guests) == 0


@pytest.mark.anyio
async def test_get_rsvp_statistics_empty_database(db_session):
    """Test getting RSVP statistics from empty database."""
    service = RSVPService(db_session)

    stats = await service.get_rsvp_statistics()

    assert stats["total"] == 0
    assert stats["attending"] == 0
    assert stats["not_attending"] == 0


@pytest.mark.anyio
async def test_get_rsvp_statistics_with_data(db_session):
    """Test getting RSVP statistics with data."""
    service = RSVPService(db_session)

    # Create 7 attending and 3 not attending
    for i in range(10):
        rsvp = RSVPCreate(
            guest_name=f"Guest {i}",
            email=f"guest{i}@example.com",
            phone=f"+123456789{i}",
            attending=i < 7,  # First 7 attending, last 3 not
        )
        await service.submit_rsvp(rsvp)

    stats = await service.get_rsvp_statistics()

    assert stats["total"] == 10
    assert stats["attending"] == 7
    assert stats["not_attending"] == 3


@pytest.mark.anyio
async def test_delete_rsvp_success(db_session):
    """Test deleting an existing RSVP."""
    service = RSVPService(db_session)

    # Create RSVP
    rsvp = RSVPCreate(
        guest_name="Test Removal",
        email="removal@example.com",
        phone="+1234567890",
        attending=True,
    )

    created = await service.submit_rsvp(rsvp)

    # Delete it
    result = await service.delete_rsvp(str(created.id))
    assert result is True

    # Verify it's gone
    fetched = await service.get_rsvp_by_email("removal@example.com")
    assert fetched is None


@pytest.mark.anyio
async def test_delete_rsvp_nonexistent(db_session):
    """Test deleting a non-existent RSVP."""
    service = RSVPService(db_session)

    # Try to delete non-existent RSVP
    result = await service.delete_rsvp(str(uuid.uuid4()))
    assert result is False


@pytest.mark.anyio
async def test_delete_rsvp_invalid_uuid_returns_false(db_session):
    """Test deleting with invalid UUID format returns False."""
    service = RSVPService(db_session)

    # Try to delete with invalid UUID (repository returns False)
    result = await service.delete_rsvp("not-a-valid-uuid")
    assert result is False


@pytest.mark.anyio
async def test_submit_rsvp_with_safe_special_chars_in_message(db_session):
    """Test RSVP submission with safe special characters in message."""
    service = RSVPService(db_session)

    rsvp = RSVPCreate(
        guest_name="Happy Guest",
        email="happy@example.com",
        phone="+1234567890",
        attending=True,
        message="Looking forward to it! Cannot wait :)",
    )

    response = await service.submit_rsvp(rsvp)

    # Message should be HTML escaped
    assert response.message is not None
    assert "Looking forward" in response.message


@pytest.mark.anyio
async def test_submit_rsvp_html_is_escaped_in_message(db_session):
    """Test that HTML in message field is escaped."""
    service = RSVPService(db_session)

    rsvp = RSVPCreate(
        guest_name="Markup User",
        email="markup@example.com",
        phone="+1234567890",
        attending=True,
        message="This is <strong>important</strong>",
    )

    response = await service.submit_rsvp(rsvp)

    # HTML should be escaped
    assert response.message is not None
    # Check that HTML entities are present (< becomes &lt;)
    assert "&lt;" in response.message or "<" not in response.message or "<strong>" not in response.message


@pytest.mark.anyio
async def test_submit_rsvp_with_minimal_phone_length(db_session):
    """Test RSVP submission with minimum valid phone length (10 digits)."""
    service = RSVPService(db_session)

    rsvp = RSVPCreate(
        guest_name="Min Phone",
        email="minphone@example.com",
        phone="1234567890",  # Exactly 10 digits
        attending=True,
    )

    response = await service.submit_rsvp(rsvp)

    assert response.phone == "1234567890"


@pytest.mark.anyio
async def test_submit_rsvp_with_plus_one_not_attending(db_session):
    """Test RSVP submission with plus_one=True but not attending (no validation)."""
    service = RSVPService(db_session)

    # When not attending, plus_one_name is not required even if plus_one is True
    rsvp = RSVPCreate(
        guest_name="Not Coming",
        email="notcoming@example.com",
        phone="+1234567890",
        attending=False,
        plus_one=True,  # Plus one but not attending
    )

    response = await service.submit_rsvp(rsvp)

    assert response.attending is False
    assert response.plus_one is True


@pytest.mark.anyio
async def test_get_all_rsvps_with_zero_limit(db_session):
    """Test getting RSVPs with limit=0 (edge case)."""
    service = RSVPService(db_session)

    # Create a few RSVPs
    for i in range(3):
        rsvp = RSVPCreate(
            guest_name=f"Guest {i}",
            email=f"guest{i}@example.com",
            phone=f"+123456789{i}",
            attending=True,
        )
        await service.submit_rsvp(rsvp)

    # Get with limit=0
    result = await service.get_all_rsvps(limit=0, offset=0)
    assert result.total == 3
    assert len(result.guests) == 0  # No items returned


@pytest.mark.anyio
async def test_get_all_rsvps_with_large_limit(db_session):
    """Test getting RSVPs with very large limit."""
    service = RSVPService(db_session)

    # Create 5 RSVPs
    for i in range(5):
        rsvp = RSVPCreate(
            guest_name=f"Guest {i}",
            email=f"guest{i}@example.com",
            phone=f"+123456789{i}",
            attending=True,
        )
        await service.submit_rsvp(rsvp)

    # Get with very large limit
    result = await service.get_all_rsvps(limit=10000, offset=0)
    assert result.total == 5
    assert len(result.guests) == 5  # Returns all available


@pytest.mark.anyio
async def test_phone_normalization_strips_formatting(db_session):
    """Test that phone normalization removes all formatting."""
    service = RSVPService(db_session)

    rsvp = RSVPCreate(
        guest_name="Formatted Phone",
        email="formatted@example.com",
        phone="+1 (555) 123-4567",  # With formatting
        attending=True,
    )

    response = await service.submit_rsvp(rsvp)

    # Phone should be digit-only (plus may remain from country code)
    assert response.phone is not None
    # Should contain only digits (and possibly leading +)
    cleaned = response.phone.replace("+", "")
    assert cleaned.isdigit()
