"""Unit tests for invited guest statistics calculation."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.invited_guest import InvitedGuestCreate
from wedding_api.services.invited_guest_service import InvitedGuestService


@pytest.mark.asyncio
async def test_get_stats_empty_list(db_session: AsyncSession) -> None:
    """Test stats calculation with no guests."""
    service = InvitedGuestService(db_session)

    stats = await service.get_invited_guest_stats()

    assert stats.total_invited_base == 0
    assert stats.total_children == 0
    assert stats.total_plus_ones == 0
    assert stats.total_invited == 0


@pytest.mark.asyncio
async def test_get_stats_base_guests_only(db_session: AsyncSession) -> None:
    """Test stats with only base guests, no tags."""
    service = InvitedGuestService(db_session)

    # Create guests without tags
    await service.create_invited_guest(InvitedGuestCreate(name="John Doe", phone="1234567890", notes="Close friend"))
    await service.create_invited_guest(InvitedGuestCreate(name="Jane Smith", phone="0987654321", notes=None))

    stats = await service.get_invited_guest_stats()

    assert stats.total_invited_base == 2
    assert stats.total_children == 0
    assert stats.total_plus_ones == 0
    assert stats.total_invited == 2


@pytest.mark.asyncio
async def test_get_stats_with_children(db_session: AsyncSession) -> None:
    """Test stats calculation with #child tags."""
    service = InvitedGuestService(db_session)

    # Create guests with #child tags
    await service.create_invited_guest(InvitedGuestCreate(name="Family A", phone="1111111111", notes="Bringing #child"))
    await service.create_invited_guest(InvitedGuestCreate(name="Family B", phone="2222222222", notes="Has 2 kids: #child #child"))
    await service.create_invited_guest(InvitedGuestCreate(name="Single Guest", phone="3333333333", notes="Just me"))

    stats = await service.get_invited_guest_stats()

    assert stats.total_invited_base == 3
    assert stats.total_children == 3
    assert stats.total_plus_ones == 0
    assert stats.total_invited == 6


@pytest.mark.asyncio
async def test_get_stats_with_plus_ones(db_session: AsyncSession) -> None:
    """Test stats calculation with #plusone tags."""
    service = InvitedGuestService(db_session)

    # Create guests with #plusone tags
    await service.create_invited_guest(InvitedGuestCreate(name="Guest A", phone="1111111111", notes="Bringing date #plusone"))
    await service.create_invited_guest(InvitedGuestCreate(name="Guest B", phone="2222222222", notes="Bringing friend #plusone"))

    stats = await service.get_invited_guest_stats()

    assert stats.total_invited_base == 2
    assert stats.total_children == 0
    assert stats.total_plus_ones == 2
    assert stats.total_invited == 4


@pytest.mark.asyncio
async def test_get_stats_with_mixed_tags(db_session: AsyncSession) -> None:
    """Test stats with both #child and #plusone tags."""
    service = InvitedGuestService(db_session)

    # Create guests with mixed tags
    await service.create_invited_guest(InvitedGuestCreate(name="Family", phone="1111111111", notes="Coming with spouse #plusone and kids #child #child"))
    await service.create_invited_guest(InvitedGuestCreate(name="Couple", phone="2222222222", notes="Partner invited #plusone"))
    await service.create_invited_guest(InvitedGuestCreate(name="Solo", phone="3333333333", notes="Just me"))

    stats = await service.get_invited_guest_stats()

    assert stats.total_invited_base == 3
    assert stats.total_children == 2
    assert stats.total_plus_ones == 2
    assert stats.total_invited == 7


@pytest.mark.asyncio
async def test_get_stats_case_insensitive(db_session: AsyncSession) -> None:
    """Test that tag matching is case-insensitive."""
    service = InvitedGuestService(db_session)

    # Create guests with various case tags
    await service.create_invited_guest(InvitedGuestCreate(name="Guest A", phone="1111111111", notes="Has #CHILD"))
    await service.create_invited_guest(InvitedGuestCreate(name="Guest B", phone="2222222222", notes="Has #Child"))
    await service.create_invited_guest(InvitedGuestCreate(name="Guest C", phone="3333333333", notes="Has #child"))
    await service.create_invited_guest(InvitedGuestCreate(name="Guest D", phone="4444444444", notes="Has #PLUSONE"))
    await service.create_invited_guest(InvitedGuestCreate(name="Guest E", phone="5555555555", notes="Has #PlusOne"))

    stats = await service.get_invited_guest_stats()

    assert stats.total_invited_base == 5
    assert stats.total_children == 3
    assert stats.total_plus_ones == 2
    assert stats.total_invited == 10


@pytest.mark.asyncio
async def test_get_stats_ignores_partial_matches(db_session: AsyncSession) -> None:
    """Test that partial word matches are not counted."""
    service = InvitedGuestService(db_session)

    # Create guests with text that contains but is not exactly the tags
    await service.create_invited_guest(InvitedGuestCreate(name="Guest A", phone="1111111111", notes="Has children but no tag"))
    await service.create_invited_guest(InvitedGuestCreate(name="Guest B", phone="2222222222", notes="childhood memories #child"))  # should count the tag
    await service.create_invited_guest(InvitedGuestCreate(name="Guest C", phone="3333333333", notes="plusones not counted"))

    stats = await service.get_invited_guest_stats()

    assert stats.total_invited_base == 3
    assert stats.total_children == 1  # Only the actual #child tag
    assert stats.total_plus_ones == 0  # "plusones" is not "#plusone"
    assert stats.total_invited == 4


@pytest.mark.asyncio
async def test_get_stats_multiple_tags_in_one_note(db_session: AsyncSession) -> None:
    """Test counting multiple tags in a single note."""
    service = InvitedGuestService(db_session)

    # Create guest with many tags
    await service.create_invited_guest(InvitedGuestCreate(name="Large Family", phone="1111111111", notes="#child #child #child #plusone"))

    stats = await service.get_invited_guest_stats()

    assert stats.total_invited_base == 1
    assert stats.total_children == 3
    assert stats.total_plus_ones == 1
    assert stats.total_invited == 5


@pytest.mark.asyncio
async def test_get_stats_with_none_notes(db_session: AsyncSession) -> None:
    """Test that None notes don't cause errors."""
    service = InvitedGuestService(db_session)

    # Create guests with None notes
    await service.create_invited_guest(InvitedGuestCreate(name="Guest A", phone="1111111111", notes=None))
    await service.create_invited_guest(InvitedGuestCreate(name="Guest B", phone="2222222222", notes="Has #child"))

    stats = await service.get_invited_guest_stats()

    assert stats.total_invited_base == 2
    assert stats.total_children == 1
    assert stats.total_plus_ones == 0
    assert stats.total_invited == 3
