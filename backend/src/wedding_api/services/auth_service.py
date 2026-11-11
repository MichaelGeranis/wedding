"""Admin authentication service."""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.admin import AdminTokenResponse
from wedding_api.models.database import User
from wedding_api.utils.security import create_access_token, verify_password

logger = logging.getLogger(__name__)


class AuthService:
    """Service for admin authentication."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the auth service with database session."""
        self.db = db

    async def authenticate_admin(self, username: str, password: str) -> AdminTokenResponse | None:
        """Authenticate admin with username and password."""
        logger.info(f"Admin authentication attempt for user: {username}")

        result = await self.db.execute(select(User).where(User.username == username, User.is_active == True))  # noqa: E712
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Admin authentication failed: user '{username}' not found")
            return None

        if not verify_password(password, user.password_hash):
            logger.warning(f"Admin authentication failed: invalid password for user '{username}'")
            return None

        token, expiration = create_access_token(subject=username)

        logger.info(f"Admin '{username}' authenticated successfully")

        return AdminTokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=int((expiration - datetime.now(UTC)).total_seconds()),
        )

    def verify_admin_token(self, token: str) -> bool:
        """Verify an admin JWT token."""
        from wedding_api.utils.security import decode_access_token

        token_data = decode_access_token(token)

        if token_data is None:
            return False

        return True
