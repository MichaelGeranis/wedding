"""Admin API routes."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.config import settings
from wedding_api.dependencies import CurrentAdmin
from wedding_api.models.admin import AdminLoginRequest, AdminTokenResponse
from wedding_api.models.rsvp import RSVPListResponse
from wedding_api.services.auth_service import AuthService
from wedding_api.services.invited_guest_service import InvitedGuestService
from wedding_api.services.rsvp_service import RSVPService
from wedding_api.utils.csv_export import generate_guest_summary_csv, generate_rsvp_csv
from wedding_api.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=AdminTokenResponse)
@limiter.limit(settings.rate_limit_admin_login)
async def admin_login(request: Request, credentials: AdminLoginRequest, db: AsyncSession = Depends(get_db)) -> AdminTokenResponse:
    """Admin login endpoint."""
    service = AuthService(db)

    token_response = await service.authenticate_admin(credentials.username, credentials.password.get_secret_value())

    if not token_response:
        logger.warning(f"Failed admin login attempt for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Admin '{credentials.username}' logged in successfully")
    return token_response


@router.get("/guests", response_model=RSVPListResponse)
async def get_guests(
    admin: CurrentAdmin,
    db: AsyncSession = Depends(get_db),
    attending: Annotated[bool | None, Query(description="Filter by attendance status")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum results")] = 50,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
) -> RSVPListResponse:
    """Get list of all RSVPs (admin only)."""
    logger.info(f"Admin {admin} fetching guest list")

    service = RSVPService(db)
    guests = await service.get_all_rsvps(attending=attending, limit=limit, offset=offset)

    logger.info(f"Returned {len(guests.guests)} guests (total={guests.total}, attending filter={attending})")

    return guests


@router.get("/stats", response_model=dict[str, int])
async def get_rsvp_stats(admin: CurrentAdmin, db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    """Get RSVP statistics (admin only)."""
    logger.info(f"Admin {admin} fetching RSVP statistics")

    rsvp_service = RSVPService(db)
    rsvp_stats = await rsvp_service.get_rsvp_statistics()

    # Get deduplicated children count (handles family groups)
    children_deduplicated = await rsvp_service.get_children_count_deduplicated()

    # Extract counts
    plus_ones = int(rsvp_stats.get("plus_ones", 0) or 0)
    attending_rows = int(rsvp_stats.get("attending", 0) or 0)
    not_attending_rows = int(rsvp_stats.get("not_attending", 0) or 0)

    # Total RSVPs = number of RSVP submissions (not affected by children or plus ones)
    total_rsvps = attending_rows + not_attending_rows

    # Total people who responded (for pending calculation)
    people_responded = attending_rows + not_attending_rows + plus_ones + children_deduplicated

    # Get invited guest totals (includes children and plus ones parsed from invited list)
    invited_service = InvitedGuestService(db)
    invited_stats = await invited_service.get_invited_guest_stats()
    total_invited = int(getattr(invited_stats, "total_invited", 0) or 0)

    pending = max(0, total_invited - people_responded)

    # Build returned stats structure expected by frontend
    stats = {
        "total": total_rsvps,  # Number of RSVP submissions
        "attending": attending_rows + plus_ones + children_deduplicated,  # Total people attending
        "not_attending": not_attending_rows,
        "plus_ones": plus_ones,
        "children": children_deduplicated,
        "total_invited": total_invited,
        "pending": int(pending),
    }

    logger.info(f"RSVP stats: {stats}")

    return stats


@router.delete("/guests/{rsvp_id}", status_code=204)
async def delete_guest(admin: CurrentAdmin, rsvp_id: str, db: AsyncSession = Depends(get_db)) -> None:
    """Delete an RSVP by id (admin only)."""
    logger.info(f"Admin {admin} deleting RSVP {rsvp_id}")
    service = RSVPService(db)
    logger.info(f"Calling service.delete_rsvp for id: {rsvp_id}")
    deleted = await service.delete_rsvp(rsvp_id)
    logger.info(f"Service.delete_rsvp returned: {deleted} for id: {rsvp_id}")
    if not deleted:
        logger.warning(f"Delete not found for id: {rsvp_id}")
        raise HTTPException(status_code=404, detail="RSVP not found")
    logger.info(f"RSVP {rsvp_id} deleted successfully")
    return None


@router.get("/guests/export/csv")
async def export_guests_csv(
    admin: CurrentAdmin,
    db: AsyncSession = Depends(get_db),
    attending: Annotated[bool | None, Query(description="Filter by attendance status")] = None,
) -> Response:
    """Export guest list as CSV (admin only)."""
    logger.info(f"Admin {admin} exporting guest list to CSV (attending filter={attending})")

    service = RSVPService(db)

    guests = await service.get_all_rsvps(attending=attending, limit=10000, offset=0)

    csv_content = generate_rsvp_csv(guests.guests)

    if attending is True:
        filename = "guests_attending.csv"
    elif attending is False:
        filename = "guests_not_attending.csv"
    else:
        filename = "all_guests.csv"

    logger.info(f"Generated CSV with {len(guests.guests)} guests")

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/guests/export/summary")
async def export_guest_summary_csv(
    admin: CurrentAdmin,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export guest summary with statistics as CSV (admin only)."""
    logger.info(f"Admin {admin} exporting guest summary to CSV")

    service = RSVPService(db)

    stats = await service.get_rsvp_statistics()
    guests = await service.get_all_rsvps(attending=None, limit=10000, offset=0)

    csv_content = generate_guest_summary_csv(stats, guests.guests)

    logger.info(f"Generated summary CSV with {len(guests.guests)} guests and statistics")

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="wedding_rsvp_summary.csv"',
        },
    )
