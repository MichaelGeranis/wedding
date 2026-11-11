"""Invited guest API routes."""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.config import settings
from wedding_api.dependencies import CurrentAdmin
from wedding_api.models.invited_guest import InvitedGuestCreate, InvitedGuestImportResponse, InvitedGuestListResponse, InvitedGuestResponse, InvitedGuestUpdate
from wedding_api.models.invited_guest_stats import InvitedGuestStats
from wedding_api.services.invited_guest_service import InvitedGuestService
from wedding_api.utils.csv_export import generate_invited_guests_csv
from wedding_api.utils.database import get_db
from wedding_api.utils.qr_code import generate_guest_qr_code

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/invited-guests", tags=["invited-guests"])


@router.post("", response_model=InvitedGuestResponse, status_code=status.HTTP_201_CREATED)
async def create_invited_guest(
    admin: CurrentAdmin,
    guest_data: InvitedGuestCreate,
    db: AsyncSession = Depends(get_db),
) -> InvitedGuestResponse:
    """Create a new invited guest (admin only)."""
    logger.info(f"Admin {admin} creating invited guest: {guest_data.name}")

    service = InvitedGuestService(db)
    guest = await service.create_invited_guest(guest_data)

    return guest


@router.get("", response_model=InvitedGuestListResponse)
async def list_invited_guests(
    admin: CurrentAdmin,
    db: AsyncSession = Depends(get_db),
) -> InvitedGuestListResponse:
    """Get list of all invited guests (admin only)."""
    logger.info(f"Admin {admin} fetching invited guest list")

    service = InvitedGuestService(db)
    guests = await service.list_invited_guests()

    return guests


@router.get("/stats", response_model=InvitedGuestStats)
async def get_invited_guest_stats(
    admin: CurrentAdmin,
    db: AsyncSession = Depends(get_db),
) -> InvitedGuestStats:
    """
    Get invited guest statistics including children and plus ones (admin only).
    Calculates total invited as: base guests + #child tags + #plusone tags in notes.
    """
    logger.info(f"Admin {admin} fetching invited guest statistics")

    service = InvitedGuestService(db)
    stats = await service.get_invited_guest_stats()

    return stats


@router.get("/export/csv")
async def export_invited_guests_csv(
    admin: CurrentAdmin,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export invited guests list as CSV (admin only)."""
    logger.info(f"Admin {admin} exporting invited guests as CSV")

    service = InvitedGuestService(db)
    result = await service.list_invited_guests()

    csv_content = generate_invited_guests_csv(result.guests)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="invited_guests.csv"'},
    )


@router.post("/import/csv", response_model=InvitedGuestImportResponse)
async def import_invited_guests_csv(
    admin: CurrentAdmin,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> InvitedGuestImportResponse:
    """
    Import invited guests from a CSV file (admin only).

    Expected CSV columns (case-insensitive):
    - Guest Name or Name (required)
    - Phone (required)
    - Notes (optional)
    - Invitation Sent (optional, Yes/No/True/False)
    - RSVP Received (optional, Yes/No/True/False)

    Guests with duplicate phone numbers will be skipped.
    """
    logger.info(f"Admin {admin} importing invited guests from CSV")

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV file")

    # Read file content
    try:
        content = await file.read()
        csv_content = content.decode("utf-8")
    except UnicodeDecodeError:
        # Try with latin-1 encoding as fallback
        try:
            csv_content = content.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to read file. Please ensure it is a valid CSV file with UTF-8 encoding.")

    if not csv_content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file is empty")

    service = InvitedGuestService(db)
    result = await service.import_invited_guests_from_csv(csv_content)

    return result


@router.get("/{guest_id}/qr-code")
async def get_guest_qr_code(
    admin: CurrentAdmin,
    guest_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Generate QR code for an invited guest (admin only).
    The QR code contains a URL to the RSVP form with a pre-filled token parameter.
    """
    logger.info(f"Admin {admin} generating QR code for guest ID: {guest_id}")

    service = InvitedGuestService(db)
    guest = await service.get_invited_guest(guest_id)

    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invited guest not found")

    qr_code_image = generate_guest_qr_code(guest.token, settings.frontend_url)

    return Response(
        content=qr_code_image,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="qr_code_{guest.name.replace(" ", "_")}.png"'},
    )


@router.get("/{guest_id}", response_model=InvitedGuestResponse)
async def get_invited_guest(
    admin: CurrentAdmin,
    guest_id: int,
    db: AsyncSession = Depends(get_db),
) -> InvitedGuestResponse:
    """Get an invited guest by ID (admin only)."""
    logger.info(f"Admin {admin} fetching invited guest ID: {guest_id}")

    service = InvitedGuestService(db)
    guest = await service.get_invited_guest(guest_id)

    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invited guest not found")

    return guest


@router.put("/{guest_id}", response_model=InvitedGuestResponse)
async def update_invited_guest(
    admin: CurrentAdmin,
    guest_id: int,
    guest_data: InvitedGuestUpdate,
    db: AsyncSession = Depends(get_db),
) -> InvitedGuestResponse:
    """Update an invited guest (admin only)."""
    logger.info(f"Admin {admin} updating invited guest ID: {guest_id}")

    service = InvitedGuestService(db)
    guest = await service.update_invited_guest(guest_id, guest_data)

    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invited guest not found")

    return guest


@router.delete("/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invited_guest(
    admin: CurrentAdmin,
    guest_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an invited guest (admin only)."""
    logger.info(f"Admin {admin} deleting invited guest ID: {guest_id}")

    service = InvitedGuestService(db)
    deleted = await service.delete_invited_guest(guest_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invited guest not found")

    return None
