"""Erasing guests' personal data once it is no longer needed."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.guest_data import GuestDataDeletionResponse
from wedding_api.repositories.invited_guest_repository_pg import InvitedGuestRepository
from wedding_api.repositories.rsvp_repository_pg import RSVPRepository

logger = logging.getLogger(__name__)

# Typed by the admin to confirm, so a stray request cannot erase the guest list.
DELETE_ALL_CONFIRMATION = "DELETE ALL GUEST DATA"


class GuestDataService:
    """Deletes every RSVP and every invited guest, for after the wedding."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.rsvp_repository = RSVPRepository(db)
        self.invited_guest_repository = InvitedGuestRepository(db)

    async def delete_all(self, confirmation: str) -> GuestDataDeletionResponse:
        """Delete all guest data in one transaction. Raises ValueError unless the confirmation phrase matches."""
        if confirmation.strip() != DELETE_ALL_CONFIRMATION:
            raise ValueError(f'Type "{DELETE_ALL_CONFIRMATION}" to confirm')

        rsvps_deleted = await self.rsvp_repository.delete_all_rsvps()
        invited_guests_deleted = await self.invited_guest_repository.delete_all_invited_guests()
        logger.info(f"Deleted all guest data: {rsvps_deleted} RSVPs, {invited_guests_deleted} invited guests")
        return GuestDataDeletionResponse(rsvps_deleted=rsvps_deleted, invited_guests_deleted=invited_guests_deleted)
