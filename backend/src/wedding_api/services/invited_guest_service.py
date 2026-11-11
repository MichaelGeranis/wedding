"""Service layer for invited guest management."""

import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.invited_guest import InvitedGuestCreate, InvitedGuestImportResponse, InvitedGuestListResponse, InvitedGuestResponse, InvitedGuestUpdate
from wedding_api.models.invited_guest_stats import InvitedGuestStats
from wedding_api.repositories.invited_guest_repository_pg import InvitedGuestRepository
from wedding_api.utils.csv_export import parse_invited_guests_csv

logger = logging.getLogger(__name__)


class InvitedGuestService:
    """Service for managing invited guests."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.repository = InvitedGuestRepository(db)

    async def create_invited_guest(self, guest_data: InvitedGuestCreate) -> InvitedGuestResponse:
        """Create a new invited guest."""
        logger.info(f"Creating invited guest: {guest_data.name}")
        return await self.repository.create_invited_guest(guest_data)

    async def get_invited_guest(self, guest_id: int) -> InvitedGuestResponse | None:
        """Get an invited guest by ID."""
        logger.info(f"Fetching invited guest ID: {guest_id}")
        return await self.repository.get_invited_guest_by_id(guest_id)

    async def check_phone_invited(self, phone: str) -> bool:
        """Check if a phone number is in the invited guest list."""
        logger.info(f"Checking if phone {phone} is invited")
        guest = await self.repository.get_invited_guest_by_phone(phone)
        return guest is not None

    async def get_guest_by_token(self, token: str) -> InvitedGuestResponse | None:
        """Get a guest by their unique token."""
        logger.info("Fetching guest by token")
        return await self.repository.get_invited_guest_by_token(token)

    async def list_invited_guests(self) -> InvitedGuestListResponse:
        """Get all invited guests."""
        logger.info("Fetching all invited guests")
        guests = await self.repository.list_invited_guests()
        return InvitedGuestListResponse(total=len(guests), guests=guests)

    async def update_invited_guest(self, guest_id: int, guest_data: InvitedGuestUpdate) -> InvitedGuestResponse | None:
        """Update an invited guest."""
        logger.info(f"Updating invited guest ID: {guest_id}")
        return await self.repository.update_invited_guest(guest_id, guest_data)

    async def delete_invited_guest(self, guest_id: int) -> bool:
        """Delete an invited guest."""
        logger.info(f"Deleting invited guest ID: {guest_id}")
        return await self.repository.delete_invited_guest(guest_id)

    async def get_invited_guest_stats(self) -> InvitedGuestStats:
        """Get statistics about invited guests including children and plus ones."""
        logger.info("Calculating invited guest statistics")
        guests = await self.repository.list_invited_guests()

        total_invited_base = len(guests)
        total_children = 0
        total_plus_ones = 0

        # Count #child and #plusone tags in notes
        for guest in guests:
            if guest.notes:
                # Count #child occurrences (case-insensitive)
                children_count = len(re.findall(r"#child\b", guest.notes, re.IGNORECASE))
                total_children += children_count

                # Count #plusone occurrences (case-insensitive)
                plusone_count = len(re.findall(r"#plusone\b", guest.notes, re.IGNORECASE))
                total_plus_ones += plusone_count

        total_invited = total_invited_base + total_children + total_plus_ones

        return InvitedGuestStats(
            total_invited_base=total_invited_base,
            total_children=total_children,
            total_plus_ones=total_plus_ones,
            total_invited=total_invited,
        )

    async def import_invited_guests_from_csv(self, csv_content: str) -> InvitedGuestImportResponse:
        """
        Import invited guests from CSV content.

        Skips rows where phone number already exists in database.
        """
        logger.info("Starting CSV import of invited guests")

        # Parse CSV
        rows, parse_errors = parse_invited_guests_csv(csv_content)

        if not rows and parse_errors:
            return InvitedGuestImportResponse(
                success_count=0,
                error_count=len(parse_errors),
                skipped_count=0,
                errors=[{"row": e["row"], "error": e["error"]} for e in parse_errors],
            )

        success_count = 0
        error_count = len(parse_errors)
        skipped_count = 0
        errors = [{"row": e["row"], "error": e["error"]} for e in parse_errors]

        for i, row in enumerate(rows):
            row_num = str(i + 2)  # Account for header row and 0-indexing
            try:
                # Check if phone already exists
                existing = await self.repository.get_invited_guest_by_phone(row.phone)
                if existing:
                    skipped_count += 1
                    logger.debug(f"Skipping duplicate phone: {row.phone}")
                    continue

                # Create the guest
                guest_data = InvitedGuestCreate(name=row.name, phone=row.phone, notes=row.notes)
                guest = await self.repository.create_invited_guest(guest_data)

                # Update invitation_sent and rsvp_received if needed
                if row.invitation_sent or row.rsvp_received:
                    update_data = InvitedGuestUpdate(invitation_sent=row.invitation_sent, rsvp_received=row.rsvp_received)
                    await self.repository.update_invited_guest(guest.id, update_data)

                success_count += 1

            except ValueError as e:
                error_count += 1
                errors.append({"row": row_num, "error": str(e)})
            except Exception as e:
                error_count += 1
                errors.append({"row": row_num, "error": f"Failed to import '{row.name}': {e}"})

        logger.info(f"CSV import completed: {success_count} success, {skipped_count} skipped, {error_count} errors")

        return InvitedGuestImportResponse(
            success_count=success_count,
            error_count=error_count,
            skipped_count=skipped_count,
            errors=errors,
        )
