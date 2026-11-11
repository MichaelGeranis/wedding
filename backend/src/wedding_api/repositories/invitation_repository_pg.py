"""Invitation repository using PostgreSQL."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.database import Invitation as InvitationModel
from wedding_api.models.invitation import InvitationResponse

logger = logging.getLogger(__name__)


class InvitationRepository:
    """Repository for wedding invitation data."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    async def get_invitation(self) -> InvitationResponse | None:
        """Get the wedding invitation."""
        try:
            result = await self.db.execute(select(InvitationModel).limit(1))
            invitation_model = result.scalar_one_or_none()

            if not invitation_model:
                logger.info("No invitation found in database")
                return None

            church_address_gr = None
            if invitation_model.church_address_gr:
                church_address_gr = f"{invitation_model.church_address_gr}, {invitation_model.church_city_gr or invitation_model.church_city} {invitation_model.church_zip}"

            venue_address_gr = None
            if invitation_model.venue_address_gr:
                venue_address_gr = f"{invitation_model.venue_address_gr}, {invitation_model.venue_city_gr or invitation_model.venue_city} {invitation_model.venue_zip}"

            return InvitationResponse(
                bride_name=invitation_model.bride_name,
                bride_name_gr=invitation_model.bride_name_gr,
                groom_name=invitation_model.groom_name,
                groom_name_gr=invitation_model.groom_name_gr,
                wedding_date=invitation_model.wedding_date,
                ceremony_time=invitation_model.wedding_time,
                church_name=invitation_model.church_name,
                church_address=(f"{invitation_model.church_address}, {invitation_model.church_city} {invitation_model.church_zip}, {invitation_model.church_state}"),
                church_city=invitation_model.church_city,
                church_state=invitation_model.church_state,
                church_zip=invitation_model.church_zip,
                church_maps_url=invitation_model.church_maps_url,
                church_name_gr=invitation_model.church_name_gr,
                church_address_gr=church_address_gr,
                church_city_gr=invitation_model.church_city_gr,
                venue_name=invitation_model.venue_name,
                venue_address=f"{invitation_model.venue_address}, {invitation_model.venue_city} {invitation_model.venue_zip}, {invitation_model.venue_state}",
                venue_city=invitation_model.venue_city,
                venue_state=invitation_model.venue_state,
                venue_zip=invitation_model.venue_zip,
                venue_maps_url=invitation_model.venue_maps_url,
                venue_name_gr=invitation_model.venue_name_gr,
                venue_address_gr=venue_address_gr,
                venue_city_gr=invitation_model.venue_city_gr,
                rsvp_deadline=invitation_model.rsvp_deadline,
            )
        except Exception as e:
            logger.error(f"Error getting invitation: {e}")
            raise

    async def save_invitation(self, invitation: InvitationResponse) -> InvitationResponse:
        """Save or update wedding invitation."""
        try:
            result = await self.db.execute(select(InvitationModel).limit(1))
            invitation_model = result.scalar_one_or_none()

            if invitation_model:
                invitation_model.bride_name = invitation.bride_name
                invitation_model.bride_name_gr = invitation.bride_name_gr
                invitation_model.groom_name = invitation.groom_name
                invitation_model.groom_name_gr = invitation.groom_name_gr
                invitation_model.wedding_date = invitation.wedding_date
                invitation_model.wedding_time = invitation.ceremony_time
                invitation_model.church_name = invitation.church_name
                invitation_model.church_address = invitation.church_address
                invitation_model.church_city = invitation.church_city
                invitation_model.church_state = invitation.church_state
                invitation_model.church_zip = invitation.church_zip
                invitation_model.church_maps_url = invitation.church_maps_url
                invitation_model.church_name_gr = invitation.church_name_gr
                invitation_model.church_address_gr = invitation.church_address_gr
                invitation_model.church_city_gr = invitation.church_city_gr
                invitation_model.venue_name = invitation.venue_name
                invitation_model.venue_address = invitation.venue_address
                invitation_model.venue_city = invitation.venue_city
                invitation_model.venue_state = invitation.venue_state
                invitation_model.venue_zip = invitation.venue_zip
                invitation_model.venue_maps_url = invitation.venue_maps_url
                invitation_model.venue_name_gr = invitation.venue_name_gr
                invitation_model.venue_address_gr = invitation.venue_address_gr
                invitation_model.venue_city_gr = invitation.venue_city_gr
                invitation_model.rsvp_deadline = invitation.rsvp_deadline
            else:
                invitation_model = InvitationModel(
                    bride_name=invitation.bride_name,
                    bride_name_gr=invitation.bride_name_gr,
                    groom_name=invitation.groom_name,
                    groom_name_gr=invitation.groom_name_gr,
                    wedding_date=invitation.wedding_date,
                    wedding_time=invitation.ceremony_time,
                    church_name=invitation.church_name,
                    church_address=invitation.church_address,
                    church_city=invitation.church_city,
                    church_state=invitation.church_state,
                    church_zip=invitation.church_zip,
                    church_maps_url=invitation.church_maps_url,
                    church_name_gr=invitation.church_name_gr,
                    church_address_gr=invitation.church_address_gr,
                    church_city_gr=invitation.church_city_gr,
                    venue_name=invitation.venue_name,
                    venue_address=invitation.venue_address,
                    venue_city=invitation.venue_city,
                    venue_state=invitation.venue_state,
                    venue_zip=invitation.venue_zip,
                    venue_maps_url=invitation.venue_maps_url,
                    venue_name_gr=invitation.venue_name_gr,
                    venue_address_gr=invitation.venue_address_gr,
                    venue_city_gr=invitation.venue_city_gr,
                    rsvp_deadline=invitation.rsvp_deadline,
                )
                self.db.add(invitation_model)

            await self.db.flush()  # Flush to persist without committing
            await self.db.refresh(invitation_model)

            logger.info("Invitation saved successfully")
            return InvitationResponse(
                bride_name=invitation_model.bride_name,
                bride_name_gr=invitation_model.bride_name_gr,
                groom_name=invitation_model.groom_name,
                groom_name_gr=invitation_model.groom_name_gr,
                wedding_date=invitation_model.wedding_date,
                ceremony_time=invitation_model.wedding_time,
                church_name=invitation_model.church_name,
                church_address=invitation_model.church_address,
                church_city=invitation_model.church_city,
                church_state=invitation_model.church_state,
                church_zip=invitation_model.church_zip,
                church_maps_url=invitation_model.church_maps_url,
                church_name_gr=invitation_model.church_name_gr,
                church_address_gr=invitation_model.church_address_gr,
                church_city_gr=invitation_model.church_city_gr,
                venue_name=invitation_model.venue_name,
                venue_address=invitation_model.venue_address,
                venue_city=invitation_model.venue_city,
                venue_state=invitation_model.venue_state,
                venue_zip=invitation_model.venue_zip,
                venue_maps_url=invitation_model.venue_maps_url,
                venue_name_gr=invitation_model.venue_name_gr,
                venue_address_gr=invitation_model.venue_address_gr,
                venue_city_gr=invitation_model.venue_city_gr,
                rsvp_deadline=invitation_model.rsvp_deadline,
            )
        except Exception as e:
            logger.error(f"Error saving invitation: {e}")
            raise  # Let the dependency handle rollback

    async def delete_invitation(self, invitation_id: int) -> None:
        """Delete an invitation by ID."""
        try:
            result = await self.db.execute(select(InvitationModel).where(InvitationModel.id == invitation_id))
            invitation_model = result.scalar_one_or_none()

            if invitation_model:
                await self.db.delete(invitation_model)
                await self.db.flush()  # Flush deletion without committing
                logger.info(f"Invitation with ID {invitation_id} deleted successfully")
            else:
                logger.warning(f"Invitation with ID {invitation_id} not found")
        except Exception as e:
            logger.error(f"Error deleting invitation: {e}")
            raise  # Let the dependency handle rollback
