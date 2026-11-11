"""SQLAlchemy database models for PostgreSQL."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class User(Base):
    """Admin users for the application."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # Bcrypt hashed password
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=lambda: datetime.now(UTC))


class Invitation(Base):
    """Wedding invitation configuration."""

    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    bride_name: Mapped[str] = mapped_column(String(100))
    bride_name_gr: Mapped[str | None] = mapped_column(String(100), nullable=True)
    groom_name: Mapped[str] = mapped_column(String(100))
    groom_name_gr: Mapped[str | None] = mapped_column(String(100), nullable=True)
    wedding_date: Mapped[str] = mapped_column(String(10))
    wedding_time: Mapped[str] = mapped_column(String(10))
    # Church fields (English)
    church_name: Mapped[str] = mapped_column(String(200))
    church_address: Mapped[str] = mapped_column(Text)
    church_city: Mapped[str] = mapped_column(String(100))
    church_state: Mapped[str] = mapped_column(String(50))
    church_zip: Mapped[str] = mapped_column(String(20))
    church_maps_url: Mapped[str] = mapped_column(String(500))
    # Church fields (Greek)
    church_name_gr: Mapped[str | None] = mapped_column(String(200), nullable=True)
    church_address_gr: Mapped[str | None] = mapped_column(Text, nullable=True)
    church_city_gr: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Venue fields (English)
    venue_name: Mapped[str] = mapped_column(String(200))
    venue_address: Mapped[str] = mapped_column(Text)
    venue_city: Mapped[str] = mapped_column(String(100))
    venue_state: Mapped[str] = mapped_column(String(50))
    venue_zip: Mapped[str] = mapped_column(String(20))
    venue_maps_url: Mapped[str] = mapped_column(String(500))
    # Venue fields (Greek)
    venue_name_gr: Mapped[str | None] = mapped_column(String(200), nullable=True)
    venue_address_gr: Mapped[str | None] = mapped_column(Text, nullable=True)
    venue_city_gr: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Other fields
    rsvp_deadline: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=lambda: datetime.now(UTC))


class InvitedGuest(Base):
    """Pre-approved guest invitation list."""

    __tablename__ = "invited_guests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    family_group_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # Groups related guests (e.g., married couples)
    invitation_sent: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    rsvp_received: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=lambda: datetime.now(UTC))


class RSVP(Base):
    """Guest RSVP responses."""

    __tablename__ = "rsvps"
    __table_args__ = (CheckConstraint("children_count >= 0 AND children_count <= 5", name="check_children_count_range"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    guest_name: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), unique=True)
    attending: Mapped[bool] = mapped_column(Boolean, index=True)
    dietary_restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)
    plus_one: Mapped[bool] = mapped_column(Boolean, default=False)
    children_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # Number of children (0-5)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmation_number: Mapped[str] = mapped_column(String(50), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=lambda: datetime.now(UTC))
