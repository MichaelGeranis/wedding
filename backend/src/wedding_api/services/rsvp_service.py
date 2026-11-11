"""RSVP service with business logic."""

import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.config import settings
from wedding_api.models.rsvp import RSVPCreate, RSVPListResponse, RSVPResponse
from wedding_api.repositories.invited_guest_repository_pg import InvitedGuestRepository
from wedding_api.repositories.rsvp_repository_pg import RSVPRepository

logger = logging.getLogger(__name__)


class RSVPService:
    """Service for RSVP business logic."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize RSVP service."""
        self.repository = RSVPRepository(db)
        self.invited_guest_repository = InvitedGuestRepository(db)

    async def submit_rsvp(self, rsvp_data: RSVPCreate) -> RSVPResponse:
        """Submit a new RSVP."""
        logger.info(f"Submitting RSVP for {getattr(rsvp_data, 'email', None) or rsvp_data.guest_name}")

        # Trim all string fields before saving (use Pydantic v2 API)
        for field, value in rsvp_data.model_dump().items():
            if isinstance(value, str):
                rsvp_data.__setattr__(field, value.strip())

        # Validate phone number against invited guests list if enabled
        if settings.require_invited_guest_validation:
            if not rsvp_data.phone:
                logger.warning(f"RSVP rejected - phone number required when validation is enabled: {getattr(rsvp_data, 'email', None) or rsvp_data.guest_name}")
                raise PermissionError("Phone number is required to submit an RSVP")

            # Normalize phone for comparison (digits only)
            phone_digits = re.sub(r"\D", "", rsvp_data.phone)

            invited_guest = await self.invited_guest_repository.get_invited_guest_by_phone(phone_digits)
            if not invited_guest:
                logger.warning(f"RSVP rejected - phone not in invited list: {rsvp_data.phone}")
                raise PermissionError("Your phone number is not in our invitation list. Please use another of your mobile numbers or contact the couple if you believe this is an error.")

            logger.info(f"Phone {rsvp_data.phone} validated against invited guest: {invited_guest.name}")

        try:
            response = await self.repository.create_rsvp(rsvp_data)

            logger.info(f"RSVP submitted successfully for {getattr(rsvp_data, 'email', None) or rsvp_data.guest_name} with confirmation {response.confirmation_number}")

            return response

        except ValueError as e:
            logger.warning(f"RSVP submission failed for {getattr(rsvp_data, 'email', None) or rsvp_data.guest_name}: {e}")
            raise

    async def get_rsvp_by_email(self, email: str) -> RSVPResponse | None:
        """Get RSVP by email address."""
        return await self.repository.get_rsvp_by_email(email)

    async def get_all_rsvps(self, attending: bool | None = None, limit: int = 100, offset: int = 0) -> RSVPListResponse:
        """Get all RSVPs with optional filtering."""
        logger.info(f"Fetching RSVPs (attending={attending}, limit={limit}, offset={offset})")

        rsvps, total = await self.repository.list_rsvps(attending_filter=attending, limit=limit, offset=offset)

        return RSVPListResponse(total=total, limit=limit, offset=offset, guests=rsvps)

    async def get_rsvp_statistics(self) -> dict[str, int]:
        """Get RSVP statistics."""
        logger.info("Fetching RSVP statistics")

        return await self.repository.get_rsvp_counts()

    async def get_children_count_deduplicated(self) -> int:
        """Get deduplicated children count (accounting for family groups)."""
        logger.info("Fetching deduplicated children count")

        return await self.repository.get_children_count_deduplicated()

    async def delete_rsvp(self, rsvp_id: str) -> bool:
        """Delete RSVP by id."""
        logger.info(f"Deleting RSVP {rsvp_id}")
        return await self.repository.delete_rsvp_by_id(rsvp_id)
