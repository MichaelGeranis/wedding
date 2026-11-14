"""Pydantic models for erasing guest data."""

from pydantic import BaseModel, Field


class GuestDataDeletionRequest(BaseModel):
    """Request to delete all guest data; must carry the confirmation phrase."""

    confirmation: str = Field(..., max_length=100, description="The phrase DELETE ALL GUEST DATA")


class GuestDataDeletionResponse(BaseModel):
    """What was deleted."""

    rsvps_deleted: int
    invited_guests_deleted: int
