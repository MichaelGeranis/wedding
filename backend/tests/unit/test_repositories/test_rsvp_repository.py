"""Unit tests for RSVP repository."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.rsvp import RSVPCreate
from wedding_api.repositories.rsvp_repository_pg import RSVPRepository


@pytest.mark.anyio
async def test_create_rsvp(db_session: AsyncSession, sample_rsvp_create: RSVPCreate) -> None:
    """Test creating a new RSVP."""
    repo = RSVPRepository(db_session)

    # Create RSVP
    result = await repo.create_rsvp(sample_rsvp_create)

    # Verify result
    assert result.guest_name == sample_rsvp_create.guest_name
    assert result.email == sample_rsvp_create.email.lower()  # Email normalized
    assert result.attending == sample_rsvp_create.attending
    assert result.confirmation_number.startswith("WED-")
    assert result.id is not None


@pytest.mark.anyio
async def test_get_rsvp_by_email(db_session: AsyncSession, sample_rsvp_create: RSVPCreate) -> None:
    """Test getting RSVP by email."""
    repo = RSVPRepository(db_session)

    # Create RSVP
    created = await repo.create_rsvp(sample_rsvp_create)

    # Get by email
    result = await repo.get_rsvp_by_email(sample_rsvp_create.email)

    # Verify result
    assert result is not None
    assert result.id == created.id
    assert result.email == sample_rsvp_create.email.lower()


@pytest.mark.anyio
async def test_get_rsvp_by_email_not_found(db_session: AsyncSession) -> None:
    """Test getting RSVP by email when it doesn't exist."""
    repo = RSVPRepository(db_session)

    result = await repo.get_rsvp_by_email("nonexistent@example.com")

    assert result is None
