"""Invitation service with business logic."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.invitation import InvitationResponse
from wedding_api.repositories.invitation_repository_pg import InvitationRepository

logger = logging.getLogger(__name__)


class InvitationService:
    """Service for invitation operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize invitation service."""
        self.repository = InvitationRepository(db)

    async def get_invitation(self) -> InvitationResponse | None:
        """Get the wedding invitation."""
        logger.info("Fetching wedding invitation")

        invitation = await self.repository.get_invitation()

        if not invitation:
            logger.warning("Wedding invitation not found")
            return None

        logger.info("Wedding invitation retrieved successfully")
        return invitation
