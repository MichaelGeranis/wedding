"""Invitation API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.invitation import InvitationResponse
from wedding_api.services.invitation_service import InvitationService
from wedding_api.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["invitation"])


@router.get("/invitation", response_model=InvitationResponse)
async def get_invitation(db: AsyncSession = Depends(get_db)) -> InvitationResponse:
    """Get wedding invitation details."""

    service = InvitationService(db)
    invitation = await service.get_invitation()

    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wedding invitation not found")

    return invitation
