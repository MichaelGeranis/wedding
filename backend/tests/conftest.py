"""Pytest configuration and fixtures."""

import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test environment variables before importing the app
os.environ["ENVIRONMENT"] = "development"
os.environ["API_PORT"] = "8000"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["FRONTEND_URL"] = "http://localhost:3000"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:5173"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"  # Use in-memory SQLite for tests
os.environ["POSTGRES_DB"] = "wedding_test_db"
os.environ["POSTGRES_USER"] = "wedding_test_user"
os.environ["POSTGRES_PASSWORD"] = "wedding_test_password"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRATION_MINUTES"] = "120"
os.environ["ADMIN_PASSWORD_HASH"] = "$2b$12$F0XaRBjlxUrIsN4VUwRRMuHawIAaVq43hJIo.1JhVfQm2l6Q9/ToS"
os.environ["RATE_LIMIT_RSVP"] = "1000/minute"
os.environ["RATE_LIMIT_ADMIN_LOGIN"] = "1000/minute"
os.environ["REQUIRE_INVITED_GUEST_VALIDATION"] = "false"
os.environ["EMAIL_ENABLED"] = "false"
os.environ["SMTP_HOST"] = "test.test.com"
os.environ["SMTP_PORT"] = "587"
os.environ["SMTP_USERNAME"] = "testuser@test.test.com"
os.environ["SMTP_PASSWORD"] = "test-smtp-password"
os.environ["SMTP_USE_TLS"] = "false"
os.environ["EMAIL_FROM_ADDRESS"] = "test@test.com"
os.environ["EMAIL_FROM_NAME"] = "Wedding Planner"
os.environ["ADMIN_EMAIL"] = "test@test.com"


from wedding_api.main import app  # noqa: E402
from wedding_api.models.database import Base, User  # noqa: E402
from wedding_api.models.rsvp import RSVPCreate  # noqa: E402
from wedding_api.utils.database import get_db  # noqa: E402


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with admin user."""
    engine = create_async_engine(os.getenv("DATABASE_URL"), echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create admin user for tests with hashed password
        # Hash for "admin123" - bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
        admin_user = User(username="admin", password_hash="$2b$12$F0XaRBjlxUrIsN4VUwRRMuHawIAaVq43hJIo.1JhVfQm2l6Q9/ToS", is_active=True)
        session.add(admin_user)
        await session.commit()

        yield session

    await engine.dispose()


@pytest.fixture
def client(db_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""

    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_rsvp_data() -> dict:
    """Sample RSVP data for testing."""
    return {
        "guest_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "attending": True,
        "dietary_restrictions": "No nuts",
        "plus_one": True,
        "message": "Looking forward to it!",
    }


@pytest.fixture
def admin_credentials() -> dict:
    """Admin login credentials for testing."""
    return {"username": "admin", "password": "admin123"}


@pytest.fixture
def sample_rsvp_create() -> RSVPCreate:
    """Sample RSVPCreate model for testing."""
    return RSVPCreate(
        guest_name="John Doe",
        email="john.doe@example.com",
        phone="+1234567890",
        attending=True,
        dietary_restrictions="No nuts",
        plus_one=True,
        message="Looking forward to it!",
    )
