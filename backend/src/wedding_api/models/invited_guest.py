"""Invited guest data models and schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from wedding_api.models.rsvp import NAME_PATTERN, sanitize_text, validate_no_sql_injection


class GuestInfoFromToken(BaseModel):
    """Guest information returned when validating a token."""

    name: str = Field(..., description="Guest name")
    phone: str = Field(..., description="Guest phone number")


class InvitedGuestCreate(BaseModel):
    """Schema for creating an invited guest."""

    name: str = Field(..., min_length=2, max_length=100, description="Guest name")
    phone: str = Field(..., min_length=10, max_length=30, description="Guest phone number (digits only)")
    notes: str | None = Field(None, max_length=300, description="Optional notes about the guest")
    family_group_id: str | None = Field(None, max_length=50, description="Family group identifier for connected guests")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate and sanitize name field."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not NAME_PATTERN.match(v):
            raise ValueError("Name contains invalid characters")
        validate_no_sql_injection(v, "Name")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        cleaned = "".join(c for c in v if c.isdigit() or c == "+")
        if len(cleaned) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        if len(cleaned) > 20:
            raise ValueError("Phone number is too long")
        return cleaned

    @field_validator("notes", mode="before")
    @classmethod
    def sanitize_notes(cls, v: str | None) -> str | None:
        """Sanitize notes field."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        validate_no_sql_injection(v, "Notes")
        return sanitize_text(v)


class InvitedGuestUpdate(BaseModel):
    """Schema for updating an invited guest."""

    name: str | None = Field(None, min_length=2, max_length=100, description="Guest name")
    phone: str | None = Field(None, min_length=10, max_length=30, description="Guest phone number (digits only)")
    notes: str | None = Field(None, max_length=300, description="Optional notes about the guest")
    family_group_id: str | None = Field(None, max_length=50, description="Family group identifier for connected guests")
    invitation_sent: bool | None = Field(None, description="Whether an invitation was sent to this guest")
    rsvp_received: bool | None = Field(None, description="Whether an RSVP has arrived for this invited guest")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate and sanitize name field."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not NAME_PATTERN.match(v):
            raise ValueError("Name contains invalid characters")
        validate_no_sql_injection(v, "Name")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Validate phone number format."""
        if v is None:
            return None
        cleaned = "".join(c for c in v if c.isdigit() or c == "+")
        if len(cleaned) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        if len(cleaned) > 20:
            raise ValueError("Phone number is too long")
        return cleaned

    @field_validator("notes", mode="before")
    @classmethod
    def sanitize_notes(cls, v: str | None) -> str | None:
        """Sanitize notes field."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        validate_no_sql_injection(v, "Notes")
        return sanitize_text(v)


class InvitedGuestResponse(BaseModel):
    """Schema for invited guest response."""

    id: int = Field(..., description="Invited guest ID")
    name: str = Field(..., description="Guest name")
    phone: str = Field(..., description="Guest phone number")
    token: str = Field(..., description="Unique token for QR code")
    notes: str | None = Field(None, description="Notes about the guest")
    family_group_id: str | None = Field(None, description="Family group identifier for connected guests")
    invitation_sent: bool = Field(False, description="Whether an invitation was sent to this guest")
    rsvp_received: bool = Field(False, description="Whether an RSVP has arrived for this invited guest")
    created_at: datetime = Field(..., description="When the guest was added to the list")
    updated_at: datetime | None = Field(None, description="When the guest was last updated")


class InvitedGuestListResponse(BaseModel):
    """Schema for list of invited guests."""

    total: int = Field(..., description="Total number of invited guests")
    guests: list[InvitedGuestResponse] = Field(..., description="List of invited guests")


class CSVImportError(BaseModel):
    """Schema for a single CSV import error."""

    row: str = Field(..., description="Row number where error occurred")
    error: str = Field(..., description="Error message")


class InvitedGuestImportResponse(BaseModel):
    """Schema for CSV import response."""

    success_count: int = Field(..., description="Number of guests successfully imported")
    error_count: int = Field(..., description="Number of rows with errors")
    skipped_count: int = Field(..., description="Number of rows skipped (duplicates)")
    errors: list[CSVImportError] = Field(default_factory=list, description="List of errors encountered")
