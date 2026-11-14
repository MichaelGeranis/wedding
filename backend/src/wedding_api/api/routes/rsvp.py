"""RSVP API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.config import settings
from wedding_api.models.invited_guest import GuestInfoFromToken
from wedding_api.models.rsvp import RSVPCreate, RSVPResponse
from wedding_api.services.invited_guest_service import InvitedGuestService
from wedding_api.services.rsvp_service import RSVPService
from wedding_api.utils.database import get_db
from wedding_api.utils.email import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["rsvp"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/rsvp", response_model=RSVPResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_rsvp)
async def submit_rsvp(request: Request, rsvp_data: RSVPCreate, db: AsyncSession = Depends(get_db)) -> RSVPResponse:
    """Submit an RSVP for the wedding."""
    service = RSVPService(db)

    try:
        rsvp = await service.submit_rsvp(rsvp_data)
        logger.info(f"RSVP submitted: {rsvp.confirmation_number}")

        # Send confirmation email to guest (non-blocking)
        try:
            # The guest's confirmation repeats what they wrote, to their own address.
            rsvp_details = {
                "plus_one": rsvp.plus_one,
                "dietary_restrictions": rsvp.dietary_restrictions,
                "message": rsvp.message,
            }

            await email_service.send_rsvp_confirmation(
                guest_email=rsvp.email,
                guest_name=rsvp.guest_name,
                confirmation_number=rsvp.confirmation_number,
                attending=rsvp.attending,
                rsvp_details=rsvp_details,
                language=rsvp_data.language,
            )

            await email_service.send_admin_notification(
                guest_name=rsvp.guest_name,
                attending=rsvp.attending,
                rsvp_details={"plus_one": rsvp.plus_one, "children_count": rsvp.children_count},
            )

        except Exception as email_error:
            logger.error(f"Failed to send email notifications for {rsvp.confirmation_number}: {type(email_error).__name__}")

        return rsvp

    except PermissionError as e:
        logger.warning("RSVP rejected - not invited")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        logger.warning("Duplicate RSVP attempt")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting RSVP: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while submitting your RSVP. Please try again.",
        )


@router.get("/rsvp/guest-info", response_model=GuestInfoFromToken)
@limiter.limit(settings.rate_limit_guest_info)
async def get_guest_info_by_token(request: Request, token: str, db: AsyncSession = Depends(get_db)) -> GuestInfoFromToken:
    """
    Validate a guest token and return guest information for RSVP form pre-fill.
    This is a public endpoint that allows guests with a valid QR code token
    to retrieve their name and phone number to pre-fill the RSVP form.
    Tokens stop working after the RSVP deadline, and lookups are rate limited per address.
    """
    logger.info("Guest info requested with token")

    service = InvitedGuestService(db)
    guest = await service.get_guest_by_token(token)

    if not guest:
        logger.warning("Invalid token used for guest info lookup")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired token")

    logger.info(f"Guest info retrieved for invited guest ID {guest.id}")

    return GuestInfoFromToken(name=guest.name, phone=guest.phone)
