import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError

from wedding_api.models.rsvp import RSVPCreate
from wedding_api.repositories.rsvp_repository_pg import RSVPRepository


@pytest.mark.anyio
async def test_unique_constraint_on_rsvp(db_session: object, sample_rsvp_create: RSVPCreate) -> None:
    """Ensure unique constraint prevents duplicate RSVP by guest_name, phone or email."""
    repo = RSVPRepository(db_session)

    # Create first RSVP
    await repo.create_rsvp(sample_rsvp_create)

    # Attempt to create duplicate - repository now raises ValueError with friendly message
    with pytest.raises(ValueError) as excinfo:
        await repo.create_rsvp(sample_rsvp_create)

    assert "already exists" in str(excinfo.value).lower()
