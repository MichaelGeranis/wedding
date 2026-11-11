"""RSVP data models and schemas."""

import html
import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, field_validator

# Regex patterns for validation
NAME_PATTERN = re.compile(r"^[\w\s\-'.]+$", re.UNICODE)
# Block SQL injection patterns
SQL_INJECTION_PATTERN = re.compile(r"(--|;|'|\"|\\|/\*|\*/|xp_|exec|execute|insert|update|delete|drop|union|select|from|where)", re.IGNORECASE)


def sanitize_text(value: str | None) -> str | None:
    """Sanitize text input to prevent XSS and injection attacks."""
    if value is None:
        return None
    value = value.strip()
    # HTML escape to prevent XSS
    value = html.escape(value)
    return value


def validate_no_sql_injection(value: str | None, field_name: str) -> str | None:
    """Check for SQL injection patterns in input."""
    if value is None:
        return None
    if SQL_INJECTION_PATTERN.search(value):
        raise ValueError(f"{field_name} contains invalid characters")
    return value


class RSVPCreate(BaseModel):
    """Schema for creating a new RSVP."""

    guest_name: str = Field(..., min_length=2, max_length=100, description="Full name of the guest")
    email: EmailStr | None = Field(None, max_length=255, description="Email address of the guest")
    phone: str | None = Field(None, min_length=10, max_length=30, description="Phone number (optional)")
    attending: bool = Field(..., description="Whether the guest will attend")
    dietary_restrictions: str | None = Field(None, max_length=300, description="Any dietary restrictions or allergies")
    plus_one: bool = Field(default=False, description="Whether bringing a plus-one")
    children_count: int = Field(default=0, ge=0, le=5, description="Number of children attending (0-5)")
    message: str | None = Field(None, max_length=500, description="Optional message to the couple")
    language: str = Field(default="en", max_length=5, description="User's preferred language (en or el)")

    @field_validator("guest_name", mode="before")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate and sanitize name fields."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not NAME_PATTERN.match(v):
            raise ValueError("Name contains invalid characters")

        validate_no_sql_injection(v, "Name")

        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr | None) -> str | None:
        """Normalize email to lowercase and validate. Accepts None."""
        if v is None:
            return None
        email = v.lower().strip()

        validate_no_sql_injection(email, "Email")

        return email

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
        if cleaned and cleaned[0] not in "0123456789+":
            raise ValueError("Invalid phone number format")

        return cleaned

    @field_validator("dietary_restrictions", "message", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v: str | None) -> str | None:
        """Sanitize text fields to prevent XSS and injection."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None

        validate_no_sql_injection(v, "Field")

        return sanitize_text(v)


class RSVPResponse(BaseModel):
    """Schema for RSVP response."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the RSVP")
    guest_name: str
    email: str | None = None
    phone: str | None = None
    attending: bool
    dietary_restrictions: str | None = None
    plus_one: bool = False
    children_count: int = Field(default=0, description="Number of children attending")
    message: str | None = None
    confirmation_number: str = Field(..., description="Confirmation number for the RSVP")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Timestamp when RSVP was submitted")
    updated_at: datetime | None = Field(None, description="Timestamp when RSVP was last updated")


class RSVPListResponse(BaseModel):
    """Schema for paginated list of RSVPs."""

    total: int = Field(..., description="Total number of RSVPs")
    limit: int = Field(..., description="Number of items per page")
    offset: int = Field(..., description="Current offset")
    guests: list[RSVPResponse] = Field(default_factory=list, description="List of RSVP responses")
