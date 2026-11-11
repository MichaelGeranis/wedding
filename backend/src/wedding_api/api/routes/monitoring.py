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
        logger.error(f"Database health check failed: {e}")
        checks["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }
        health_status["status"] = "unhealthy"

    # Add more health checks as needed
    checks["api"] = {
        "status": "healthy",
        "message": "API is responding",
    }

    return health_status
