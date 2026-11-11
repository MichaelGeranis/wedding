from typing import cast

import pytest

from wedding_api.models.rsvp import RSVPCreate
from wedding_api.repositories.rsvp_repository_pg import RSVPRepository
from wedding_api.services.rsvp_service import RSVPService


class DummyRepo:
    def __init__(self, should_raise=False):
        self.should_raise = should_raise

    async def create_rsvp(self, rsvp):
        if self.should_raise:
            raise ValueError("An RSVP with this email already exists.")

        # Return a minimal response-like object
        class Resp:
            id = rsvp.guest_name
            guest_name = rsvp.guest_name
            email = rsvp.email
            phone = rsvp.phone
            attending = rsvp.attending
            dietary_restrictions = rsvp.dietary_restrictions
            plus_one = rsvp.plus_one
            message = rsvp.message
            confirmation_number = "WED-TEST-123"
            submitted_at = None
            updated_at = None

        return Resp()


class DummyDB:
    pass


@pytest.mark.anyio
async def test_service_maps_repository_valueerror(db_session, monkeypatch):
    service = RSVPService(db_session)
    # monkeypatch the repository instance inside service (use cast to satisfy type checkers)
    service.repository = cast(RSVPRepository, DummyRepo(should_raise=True))  # type: ignore[attr-defined]

    rsvp = RSVPCreate(
        guest_name="Test",
        email="dup@example.com",
        phone=None,
        attending=True,
        dietary_restrictions=None,
        plus_one=False,
        message=None,
    )

    with pytest.raises(ValueError) as exc:
        await service.submit_rsvp(rsvp)

    assert "already exists" in str(exc.value).lower()


@pytest.mark.anyio
async def test_service_returns_response_on_success(db_session, monkeypatch):
    service = RSVPService(db_session)
    service.repository = cast(RSVPRepository, DummyRepo(should_raise=False))  # type: ignore[attr-defined]

    rsvp = RSVPCreate(
        guest_name="OK",
        email="ok@example.com",
        phone=None,
        attending=False,
        dietary_restrictions=None,
        plus_one=False,
        message=None,
    )

    resp = await service.submit_rsvp(rsvp)

    assert resp.confirmation_number == "WED-TEST-123"


@pytest.mark.anyio
async def test_trimming_edge_cases(db_session, monkeypatch):
    """Ensure trimming and normalization work correctly for valid inputs."""
    service = RSVPService(db_session)
    service.repository = cast(RSVPRepository, DummyRepo(should_raise=False))  # type: ignore[attr-defined]

    rsvp = RSVPCreate(
        guest_name="  John Doe  ",  # Leading/trailing spaces should be trimmed
        email="  EX@EX.COM  ",  # Should be lowercased and trimmed
        phone=None,
        attending=False,
        dietary_restrictions=None,
        plus_one=False,
        message=None,
    )

    # Verify email is normalized to lowercase and trimmed
    resp = await service.submit_rsvp(rsvp)
    assert resp.email == "ex@ex.com"
    assert resp.guest_name == "John Doe"  # Trimmed


@pytest.mark.anyio
async def test_logging_on_duplicate(monkeypatch, db_session, caplog):
    """RSVPService should log a warning when duplicate ValueError is raised."""
    service = RSVPService(db_session)
    service.repository = cast(RSVPRepository, DummyRepo(should_raise=True))  # type: ignore[attr-defined]

    rsvp = RSVPCreate(
        guest_name="DupLog",
        email="duplog@example.com",
        phone=None,
        attending=True,
        dietary_restrictions=None,
        plus_one=False,
        message=None,
    )

    caplog.clear()
    with pytest.raises(ValueError):
        await service.submit_rsvp(rsvp)

    assert any("submission failed" in rec.message.lower() for rec in caplog.records)
