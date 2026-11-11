"""RSVP repository using PostgreSQL."""

import logging
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.database import RSVP, InvitedGuest
from wedding_api.models.rsvp import RSVPCreate, RSVPResponse

logger = logging.getLogger(__name__)


class RSVPRepository:
    """Repository for RSVP data."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    def _generate_confirmation_number(self) -> str:
        """Generate a unique confirmation number."""
        return f"WED-{datetime.now(UTC).year}-{uuid4().hex[:6].upper()}"

    async def create_rsvp(self, rsvp: RSVPCreate) -> RSVPResponse:
        """Create a new RSVP."""
        try:
            rsvp_id = uuid4()
            confirmation_number: str = self._generate_confirmation_number()
            now: datetime = datetime.now(UTC)

            email_norm = rsvp.email.lower().strip() if rsvp.email else None

            phone_val = None
            if getattr(rsvp, "phone", None):
                import re

                cleaned = re.sub(r"\D", "", str(rsvp.phone))
                if cleaned:
                    phone_val = cleaned

            rsvp_model = RSVP(
                id=rsvp_id,
                guest_name=rsvp.guest_name,
                email=email_norm,
                phone=phone_val,
                attending=rsvp.attending,
                dietary_restrictions=rsvp.dietary_restrictions,
                plus_one=rsvp.plus_one,
                children_count=rsvp.children_count,
                message=rsvp.message,
                confirmation_number=confirmation_number,
                created_at=now,
                updated_at=None,
            )

            self.db.add(rsvp_model)
            try:
                await self.db.flush()  # Flush to get ID without committing
                await self.db.refresh(rsvp_model)
            except IntegrityError as ie:
                # Map DB unique constraint errors to a friendly ValueError
                err_text = "".join(str(ie).splitlines()).lower()
                if "key (email)" in err_text:
                    msg = "An RSVP with this email already exists."
                elif "key (phone)" in err_text:
                    msg = "An RSVP with this phone number already exists."
                elif "key (guest_name)" in err_text or "guest_name" in err_text:
                    msg = "An RSVP with this guest name already exists."
                else:
                    msg = "An RSVP with the provided details already exists."

                logger.warning(f"IntegrityError while creating RSVP: {ie}; responding with friendly error")
                raise ValueError(msg) from ie

            logger.info(f"RSVP created for guest: {rsvp.guest_name}")

            # Update invited guest if exists
            if phone_val:
                result = await self.db.execute(select(InvitedGuest).where(InvitedGuest.phone == phone_val))
                invited_guest = result.scalar_one_or_none()
                if invited_guest:
                    invited_guest.rsvp_received = True
                    await self.db.flush()
                    logger.info(f"Marked invited guest with phone {phone_val} as having RSVP'd")

            return RSVPResponse(
                id=rsvp_model.id,
                guest_name=rsvp_model.guest_name,
                email=rsvp_model.email,
                phone=str(rsvp_model.phone) if rsvp_model.phone is not None else None,
                attending=rsvp_model.attending,
                dietary_restrictions=rsvp_model.dietary_restrictions,
                plus_one=rsvp_model.plus_one,
                children_count=rsvp_model.children_count,
                message=rsvp_model.message,
                confirmation_number=rsvp_model.confirmation_number,
                created_at=rsvp_model.created_at,
                updated_at=rsvp_model.updated_at,
            )
        except Exception as e:
            logger.error(f"Error creating RSVP: {e}")
            raise  # Let the dependency handle rollback

    async def get_rsvp_by_email(self, email: str) -> RSVPResponse | None:
        """Get RSVP by email."""
        try:
            if not email:
                return None
            result = await self.db.execute(select(RSVP).where(RSVP.email == email).order_by(RSVP.created_at.desc()).limit(1))
            rsvp_model = result.scalar_one_or_none()

            if not rsvp_model:
                return None

            return RSVPResponse(
                id=rsvp_model.id,
                guest_name=rsvp_model.guest_name,
                email=rsvp_model.email,
                phone=str(rsvp_model.phone) if rsvp_model.phone is not None else None,
                attending=rsvp_model.attending,
                dietary_restrictions=rsvp_model.dietary_restrictions,
                plus_one=rsvp_model.plus_one,
                children_count=rsvp_model.children_count,
                message=rsvp_model.message,
                confirmation_number=rsvp_model.confirmation_number,
                created_at=rsvp_model.created_at,
                updated_at=rsvp_model.updated_at,
            )
        except Exception as e:
            logger.error(f"Error getting RSVP by email: {e}")
            raise

    async def list_rsvps(self, attending_filter: bool | None, limit: int = 100, offset: int = 0) -> tuple[list[RSVPResponse], int]:
        """List all RSVPs with optional filtering."""
        try:
            # Build query
            query = select(RSVP)
            count_query = select(func.count()).select_from(RSVP)

            if attending_filter is not None:
                query = query.where(RSVP.attending == attending_filter)
                count_query = count_query.where(RSVP.attending == attending_filter)

            # Get total count
            total_result = await self.db.execute(count_query)
            total = total_result.scalar_one()

            # Get paginated results
            query = query.order_by(RSVP.created_at.desc()).limit(limit).offset(offset)
            result = await self.db.execute(query)
            rsvp_models = result.scalars().all()

            rsvps = [
                RSVPResponse(
                    id=rsvp.id,
                    guest_name=rsvp.guest_name,
                    email=rsvp.email,
                    phone=str(rsvp.phone) if rsvp.phone is not None else None,
                    attending=rsvp.attending,
                    dietary_restrictions=rsvp.dietary_restrictions,
                    plus_one=rsvp.plus_one,
                    children_count=rsvp.children_count,
                    message=rsvp.message,
                    confirmation_number=rsvp.confirmation_number,
                    created_at=rsvp.created_at,
                    updated_at=rsvp.updated_at,
                )
                for rsvp in rsvp_models
            ]

            logger.info(f"Retrieved {len(rsvps)} RSVPs")
            return rsvps, total
        except Exception as e:
            logger.error(f"Error listing RSVPs: {e}")
            raise

    async def get_rsvp_counts(self) -> dict[str, int]:
        """Get RSVP counts grouped by attendance status using efficient aggregation."""
        try:
            # Single query with conditional aggregation
            query = select(
                func.count().label("total"),
                func.sum(case((RSVP.attending, 1), else_=0)).label("attending"),
                func.sum(case((~RSVP.attending, 1), else_=0)).label("not_attending"),
                func.sum(case(((RSVP.attending & RSVP.plus_one), 1), else_=0)).label("plus_ones"),
                func.sum(case((RSVP.attending, RSVP.children_count), else_=0)).label("children_total"),
            )

            result = await self.db.execute(query)
            row = result.one()

            counts = {
                "total": int(row.total) if row.total else 0,
                "attending": int(row.attending) if row.attending else 0,
                "not_attending": int(row.not_attending) if row.not_attending else 0,
                "plus_ones": int(row.plus_ones) if row.plus_ones else 0,
                "children_total": int(row.children_total) if row.children_total else 0,
            }

            logger.info(f"RSVP counts retrieved: {counts}")
            return counts
        except Exception as e:
            logger.error(f"Error getting RSVP counts: {e}")
            raise

    async def get_children_count_deduplicated(self) -> int:
        """
        Get total children count with family group deduplication.

        If multiple RSVPs belong to the same family_group_id (via InvitedGuest),
        count their children only once per family group (take MAX to handle
        cases where one spouse reports children and the other doesn't).
        """
        try:
            from sqlalchemy import outerjoin

            # Left join RSVPs with InvitedGuests on phone to get family_group_id
            # Use COALESCE to group by family_group_id if it exists, otherwise by phone
            # Then take MAX(children_count) per group and SUM all groups
            subquery = (
                select(
                    func.coalesce(InvitedGuest.family_group_id, RSVP.phone).label("group_key"),
                    func.max(RSVP.children_count).label("max_children"),
                )
                .select_from(outerjoin(RSVP, InvitedGuest, RSVP.phone == InvitedGuest.phone))
                .where(RSVP.attending == True)  # noqa: E712
                .group_by(func.coalesce(InvitedGuest.family_group_id, RSVP.phone))
            ).subquery()

            query = select(func.coalesce(func.sum(subquery.c.max_children), 0))
            result = await self.db.execute(query)
            total_children = result.scalar_one()

            logger.info(f"Deduplicated children count: {total_children}")
            return int(total_children) if total_children else 0
        except Exception as e:
            logger.error(f"Error getting deduplicated children count: {e}")
            raise

    async def delete_rsvp_by_id(self, rsvp_id: str) -> bool:
        """Delete an RSVP by its UUID id."""
        try:
            from uuid import UUID as _UUID

            from sqlalchemy import delete

            logger.info(f"Attempting to delete RSVP with id: {rsvp_id}")

            try:
                uuid_val = _UUID(rsvp_id)
                logger.info(f"Parsed UUID value: {uuid_val}")
            except Exception:
                logger.warning(f"Invalid UUID provided for delete: {rsvp_id}")
                return False

            logger.info(f"Executing DELETE for UUID: {uuid_val}")
            result = await self.db.execute(delete(RSVP).where(RSVP.id == uuid_val))
            await self.db.commit()

            logger.info(f"Delete executed, result: {result}")

            try:
                rowcount_val = getattr(result, "rowcount", None)
                if rowcount_val is not None:
                    rowcount = int(rowcount_val)  # type: ignore[arg-type]
                    logger.info(f"Delete rowcount: {rowcount}")
                    return rowcount > 0
            except Exception:
                pass

            # Fallback: check if select returns None
            res = await self.db.execute(select(RSVP).where(RSVP.id == uuid_val))
            exists = res.scalar_one_or_none()
            logger.info(f"Post-delete existence check for {uuid_val}: {exists}")
            return exists is None
        except Exception as e:
            logger.error(f"Error deleting RSVP {rsvp_id}: {e}")
            raise
