"""Invited guest statistics models."""

from pydantic import BaseModel, Field


class InvitedGuestStats(BaseModel):
    """Schema for invited guest statistics."""

    total_invited_base: int = Field(..., description="Base number of invited guests (primary invitees)")
    total_children: int = Field(..., description="Total number of children (#child tags in notes)")
    total_plus_ones: int = Field(..., description="Total number of plus ones (#plusone tags in notes)")
    total_invited: int = Field(..., description="Total invited (base + children + plus ones)")
