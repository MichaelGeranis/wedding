"""Monitoring and health check API routes."""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Detailed health check including database connectivity."""
    checks: dict[str, dict[str, str]] = {}
    health_status: dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }

    # Check database connectivity
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        checks["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        # This endpoint is public: the error's text can name the database host or user, so it stays in the log.
        logger.error(f"Database health check failed: {type(e).__name__}")
        checks["database"] = {
            "status": "unhealthy",
            "message": "Database connection failed",
        }
        health_status["status"] = "unhealthy"

    # Add more health checks as needed
    checks["api"] = {
        "status": "healthy",
        "message": "API is responding",
    }

    return health_status
