"""Invitation data models and schemas."""

from pydantic import BaseModel, Field


class InvitationResponse(BaseModel):
    """Schema for invitation response."""

    bride_name: str = Field(..., description="Name of the bride")
    bride_name_gr: str | None = Field(None, description="Name of the bride (Greek)")
    groom_name: str = Field(..., description="Name of the groom")
    groom_name_gr: str | None = Field(None, description="Name of the groom (Greek)")
    wedding_date: str = Field(..., description="Date of the wedding (YYYY-MM-DD)")
    ceremony_time: str = Field(..., description="Time of the ceremony (HH:MM)")
    # Church fields (English)
    church_name: str | None = Field(None, description="Name of the church")
    church_address: str | None = Field(None, description="Full address of the church")
    church_city: str | None = Field(None, description="City of the church")
    church_state: str | None = Field(None, description="State of the church")
    church_zip: str | None = Field(None, description="ZIP code of the church")
    church_maps_url: str | None = Field(None, description="Google Maps URL for the church")
    # Church fields (Greek)
    church_name_gr: str | None = Field(None, description="Name of the church (Greek)")
    church_address_gr: str | None = Field(None, description="Full address of the church (Greek)")
    church_city_gr: str | None = Field(None, description="City of the church (Greek)")
    # Venue fields (English)
    venue_name: str = Field(..., description="Name of the wedding venue/cocktails")
    venue_address: str = Field(..., description="Full address of the venue")
    venue_city: str = Field(..., description="City of the wedding venue")
    venue_state: str = Field(..., description="State of the wedding venue")
    venue_zip: str = Field(..., description="ZIP code of the wedding venue")
    venue_maps_url: str | None = Field(None, description="Google Maps URL for the venue")
    # Venue fields (Greek)
    venue_name_gr: str | None = Field(None, description="Name of the wedding venue (Greek)")
    venue_address_gr: str | None = Field(None, description="Full address of the venue (Greek)")
    venue_city_gr: str | None = Field(None, description="City of the wedding venue (Greek)")
    # Other fields
    rsvp_deadline: str = Field(..., description="RSVP deadline (YYYY-MM-DD)")
