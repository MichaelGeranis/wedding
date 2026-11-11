"""Main FastAPI application entry point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from wedding_api.api.routes import admin, invitation, invited_guests, monitoring, rsvp
from wedding_api.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager."""
    # Startup
    logger.info(f"Starting wedding API in {settings.environment} environment")
    logger.info(f"Database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'configured'}")

    yield

    # Shutdown
    logger.info("Shutting down wedding API")


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Wedding Planner API",
    description="API for wedding invitation and RSVP management",
    version="0.1.0",
    lifespan=lifespan,
)

# Add rate limiter state to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(monitoring.router)
app.include_router(invitation.router)
app.include_router(rsvp.router)
app.include_router(admin.router)
app.include_router(invited_guests.router)


@app.get("/api/health")
async def health_check() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "environment": settings.environment,
            "version": "0.1.0",
        },
    )


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Wedding Planner API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Return standardized JSON for HTTP exceptions raised in the app."""
    detail = exc.detail if hasattr(exc, "detail") else str(exc)
    error_code = exc.status_code
    return JSONResponse(status_code=exc.status_code, content={"error": str(error_code), "detail": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return standardized JSON for validation errors."""
    sanitized_errors = []
    messages: list[str] = []
    for err in exc.errors():
        e = err.copy()
        loc = e.get("loc", [])
        # Format location as dot-separated path when possible
        try:
            loc_str = ".".join(str(x) for x in loc)
        except Exception:
            loc_str = str(loc)

        msg = e.get("msg", "")
        messages.append(f"{loc_str}: {msg}" if loc_str else msg)

        ctx = e.get("ctx")
        if isinstance(ctx, dict):
            new_ctx = {}
            for k, v in ctx.items():
                try:
                    import json

                    json.dumps(v)
                    new_ctx[k] = v
                except Exception:
                    new_ctx[k] = str(v)
            e["ctx"] = new_ctx

        sanitized_errors.append(e)

    detail_str = "; ".join(messages) if messages else str(exc)

    # Return both a readable 'detail' string and the raw 'errors' for debugging
    return JSONResponse(
        status_code=422,
        content={"error": "422", "detail": detail_str, "errors": sanitized_errors},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return standardized JSON for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"error": "500", "detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "wedding_api.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.is_development,
    )
