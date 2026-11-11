"""Invited guest repository using PostgreSQL."""

import logging
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.database import RSVP, InvitedGuest
from wedding_api.models.invited_guest import InvitedGuestCreate, InvitedGuestResponse, InvitedGuestUpdate

logger = logging.getLogger(__name__)


def generate_guest_token() -> str:
    """Generate a secure random token for guest QR codes."""
    return secrets.token_urlsafe(32)  # 32 bytes = 256 bits of entropy


class InvitedGuestRepository:
    """Repository for invited guest data."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    async def create_invited_guest(self, guest_data: InvitedGuestCreate) -> InvitedGuestResponse:
        """Create a new invited guest."""
        try:
            guest = InvitedGuest(
                name=guest_data.name,
                phone=guest_data.phone,
                token=generate_guest_token(),
                notes=guest_data.notes,
                invitation_sent=getattr(guest_data, "invitation_sent", False) if hasattr(guest_data, "invitation_sent") else False,
                rsvp_received=getattr(guest_data, "rsvp_received", None) if hasattr(guest_data, "rsvp_received") else None,
            )

            # Determine if an RSVP already exists for this phone (normalize digits)
            phone_digits = "".join(c for c in (guest.phone or "") if c.isdigit())
            rsvp_received = False
            if phone_digits:
                r = await self.db.execute(select(RSVP).where(RSVP.phone == phone_digits))
                rsvp_received = r.scalar_one_or_none() is not None
            guest.rsvp_received = rsvp_received

            self.db.add(guest)
            await self.db.flush()
            await self.db.refresh(guest)

            logger.info(f"Created invited guest: {guest.name} (ID: {guest.id})")

            return InvitedGuestResponse(
                id=guest.id,
                name=guest.name,
                phone=guest.phone,
                token=guest.token,
                notes=guest.notes,
                invitation_sent=guest.invitation_sent,
                rsvp_received=guest.rsvp_received,
                created_at=guest.created_at,
                updated_at=guest.updated_at,
            )
        except Exception as e:
            logger.error(f"Error creating invited guest: {e}")
            raise

    async def get_invited_guest_by_id(self, guest_id: int) -> InvitedGuestResponse | None:
        """Get an invited guest by ID."""
        try:
            result = await self.db.execute(select(InvitedGuest).where(InvitedGuest.id == guest_id))
            guest = result.scalar_one_or_none()

            if not guest:
                return None

            return InvitedGuestResponse(
                id=guest.id,
                name=guest.name,
                phone=guest.phone,
                token=guest.token,
                notes=guest.notes,
                invitation_sent=guest.invitation_sent,
                rsvp_received=guest.rsvp_received,
                created_at=guest.created_at,
                updated_at=guest.updated_at,
            )
        except Exception as e:
            logger.error(f"Error getting invited guest by ID {guest_id}: {e}")
            raise

    async def get_invited_guest_by_phone(self, phone: str) -> InvitedGuestResponse | None:
        """Get an invited guest by phone number."""
        try:
            result = await self.db.execute(select(InvitedGuest).where(InvitedGuest.phone == phone))
            guest = result.scalar_one_or_none()

            if not guest:
                return None

            return InvitedGuestResponse(
                id=guest.id,
                name=guest.name,
                phone=guest.phone,
                token=guest.token,
                notes=guest.notes,
                invitation_sent=guest.invitation_sent,
                rsvp_received=guest.rsvp_received,
                created_at=guest.created_at,
                updated_at=guest.updated_at,
            )
        except Exception as e:
            logger.error(f"Error getting invited guest by phone {phone}: {e}")
            raise

    async def get_invited_guest_by_token(self, token: str) -> InvitedGuestResponse | None:
        """Get an invited guest by their unique token."""
        try:
            result = await self.db.execute(select(InvitedGuest).where(InvitedGuest.token == token))
            guest = result.scalar_one_or_none()

            if not guest:
                return None

            return InvitedGuestResponse(
                id=guest.id,
                name=guest.name,
                phone=guest.phone,
                token=guest.token,
                notes=guest.notes,
                invitation_sent=guest.invitation_sent,
                rsvp_received=guest.rsvp_received,
                created_at=guest.created_at,
                updated_at=guest.updated_at,
            )
        except Exception as e:
            logger.error(f"Error getting invited guest by token: {e}")
            raise

    async def list_invited_guests(self) -> list[InvitedGuestResponse]:
        """Get all invited guests."""
        try:
            result = await self.db.execute(select(InvitedGuest).order_by(InvitedGuest.created_at.desc()))
            guests = result.scalars().all()

            return [
                InvitedGuestResponse(
                    id=guest.id,
                    name=guest.name,
                    phone=guest.phone,
                    token=guest.token,
                    notes=guest.notes,
                    invitation_sent=guest.invitation_sent,
                    rsvp_received=guest.rsvp_received,
                    created_at=guest.created_at,
                    updated_at=guest.updated_at,
                )
                for guest in guests
            ]
        except Exception as e:
            logger.error(f"Error listing invited guests: {e}")
            raise

    async def update_invited_guest(self, guest_id: int, guest_data: InvitedGuestUpdate) -> InvitedGuestResponse | None:
        """Update an invited guest."""
        try:
            result = await self.db.execute(select(InvitedGuest).where(InvitedGuest.id == guest_id))
            guest = result.scalar_one_or_none()

            if not guest:
                return None

            # Update fields if provided
            if guest_data.name is not None:
                guest.name = guest_data.name
            if guest_data.phone is not None:
                guest.phone = guest_data.phone
            if guest_data.notes is not None:
                guest.notes = guest_data.notes
            invitation_sent_val = getattr(guest_data, "invitation_sent", None)
            if invitation_sent_val is not None:
                guest.invitation_sent = bool(invitation_sent_val)
            rsvp_received_val = getattr(guest_data, "rsvp_received", None)
            if rsvp_received_val is not None:
                guest.rsvp_received = bool(rsvp_received_val)

            await self.db.flush()
            await self.db.refresh(guest)

            logger.info(f"Updated invited guest ID {guest_id}")

            return InvitedGuestResponse(
                id=guest.id,
                name=guest.name,
                phone=guest.phone,
                token=guest.token,
                notes=guest.notes,
                invitation_sent=guest.invitation_sent,
                rsvp_received=guest.rsvp_received,
                created_at=guest.created_at,
                updated_at=guest.updated_at,
            )
        except Exception as e:
            logger.error(f"Error updating invited guest {guest_id}: {e}")
            raise

    async def delete_invited_guest(self, guest_id: int) -> bool:
        """Delete an invited guest by ID."""
        try:
            result = await self.db.execute(select(InvitedGuest).where(InvitedGuest.id == guest_id))
            guest = result.scalar_one_or_none()

            if not guest:
                return False

            await self.db.delete(guest)
            await self.db.flush()

            logger.info(f"Deleted invited guest ID {guest_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting invited guest {guest_id}: {e}")
            raise
