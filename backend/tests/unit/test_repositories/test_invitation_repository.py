"""Unit tests for InvitationRepository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.database import Invitation
from wedding_api.models.invitation import InvitationResponse
from wedding_api.repositories.invitation_repository_pg import InvitationRepository


@pytest.mark.anyio
async def test_get_invitation(db_session: AsyncSession) -> None:
    """Test getting invitation when it exists."""
    # Create invitation in database
    invitation = Invitation(
        bride_name="Sarah",
        groom_name="Michael",
        wedding_date="2025-06-15",
        wedding_time="16:00",  # Updated to match model
        venue_name="The Grand Ballroom",
        venue_address="123 Main Street",
        venue_city="Springfield",  # Added required field
        venue_state="IL",  # Added required field
        venue_zip="62701",  # Added required field
        rsvp_deadline="2025-06-10",  # Added required field
        church_name="St. Mary Church",
        church_address="10 Church Rd",
        church_city="New York",
        church_state="NY",
        church_zip="10001",
        church_maps_url="None",
        venue_maps_url="None",
    )
    db_session.add(invitation)
    await db_session.commit()

    # Get invitation
    repo = InvitationRepository(db_session)
    result = await repo.get_invitation()

    assert result is not None
    assert result.bride_name == "Sarah"
    assert result.groom_name == "Michael"


@pytest.mark.anyio
async def test_get_invitation_not_found(db_session: AsyncSession) -> None:
    """Test getting invitation when it doesn't exist."""
    repo = InvitationRepository(db_session)
    invitation = await repo.get_invitation()

    assert invitation is None


@pytest.mark.anyio
async def test_create_or_update_invitation_new(db_session: AsyncSession) -> None:
    """Test creating a new invitation."""
    invitation_data = InvitationResponse(
        bride_name="Jane",
        groom_name="John",
        wedding_date="2025-12-25",
        ceremony_time="15:00",  # Updated to match model
        venue_name="City Hall",
        venue_address="456 Oak St",
        venue_city="Metropolis",  # Added required field
        venue_state="NY",  # Added required field
        venue_zip="10001",  # Added required field
        rsvp_deadline="2025-12-20",  # Added required field
        church_name="St. Mary Church",
        church_address="10 Church Rd",
        church_city="New York",
        church_state="NY",
        church_zip="10001",
        church_maps_url="None",
        venue_maps_url="None",
    )

    repo = InvitationRepository(db_session)
    result = await repo.save_invitation(invitation_data)

    # Verify created invitation
    assert result.bride_name == "Jane"
    assert result.groom_name == "John"

    # Verify it was saved to database
    saved = await repo.get_invitation()
    assert saved is not None
    assert saved.bride_name == "Jane"


@pytest.mark.anyio
async def test_create_or_update_invitation_existing(db_session: AsyncSession) -> None:
    """Test updating an existing invitation."""
    # Create initial invitation
    initial = Invitation(
        bride_name="Jane",
        groom_name="John",
        wedding_date="2025-12-25",
        wedding_time="15:00",  # Updated to match model
        venue_name="City Hall",
        venue_address="456 Oak St",
        venue_city="Metropolis",  # Added required field
        venue_state="NY",  # Added required field
        venue_zip="10001",  # Added required field
        rsvp_deadline="2025-12-20",  # Added required field
        church_name="St. Mary Church",
        church_address="10 Church Rd",
        church_city="New York",
        church_state="NY",
        church_zip="10001",
        church_maps_url="None",
        venue_maps_url="None",
    )
    db_session.add(initial)
    await db_session.commit()

    updated_data = InvitationResponse(
        bride_name="Jane",
        groom_name="John",
        wedding_date="2025-12-25",
        ceremony_time="15:00",
        venue_name="City Hall",
        venue_address="456 Oak St",
        venue_city="Metropolis",  # Added required field
        venue_state="NY",  # Added required field
        venue_zip="10001",  # Added required field
        rsvp_deadline="2025-12-21",
        church_name="St. Mary Church",
        church_address="10 Church Rd",
        church_city="New York",
        church_state="NY",
        church_zip="10001",
        church_maps_url="None",
        venue_maps_url="None",
    )

    repo = InvitationRepository(db_session)
    result = await repo.save_invitation(updated_data)

    # Verify updates
    assert result.rsvp_deadline == "2025-12-21"

    # Verify it's saved
    saved = await repo.get_invitation()
    assert saved is not None
    assert saved.venue_name == "City Hall"


@pytest.mark.anyio
async def test_delete_invitation(db_session: AsyncSession) -> None:
    """Test deleting an invitation."""
    invitation = Invitation(
        bride_name="Jane",
        groom_name="John",
        wedding_date="2025-12-25",
        wedding_time="15:00",
        venue_name="City Hall",
        venue_address="456 Oak St",
        venue_city="Metropolis",  # Added required field
        venue_state="NY",  # Added required field
        venue_zip="10001",  # Added required field
        rsvp_deadline="2025-12-20",  # Added required field
        church_name="St. Mary Church",
        church_address="10 Church Rd",
        church_city="New York",
        church_state="NY",
        church_zip="10001",
        church_maps_url="None",
        venue_maps_url="None",
    )
    db_session.add(invitation)
    await db_session.commit()

    repo = InvitationRepository(db_session)
    await repo.delete_invitation(invitation.id)

    result = await repo.get_invitation()
    assert result is None
