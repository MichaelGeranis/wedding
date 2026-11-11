"""FastAPI dependencies for authentication and dependency injection."""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from wedding_api.utils.security import decode_access_token

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """Verify JWT token and return admin identifier."""
    token = credentials.credentials

    token_data = decode_access_token(token)

    if token_data is None:
        logger.warning("Invalid or expired JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data.sub


# Type alias for dependency injection
CurrentAdmin = Annotated[str, Depends(get_current_admin)]
