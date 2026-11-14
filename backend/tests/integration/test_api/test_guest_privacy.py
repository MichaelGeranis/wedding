"""Integration tests for how guests' personal data is kept, shown and erased."""

import logging
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_api.models.database import RSVP, Invitation, InvitedGuest


def _invitation(rsvp_deadline: str) -> Invitation:
    return Invitation(
        bride_name="Sarah",
        groom_name="Michael",
        wedding_date="2027-06-15",
        wedding_time="16:00",
        venue_name="The Grand Ballroom",
        venue_address="123 Main Street",
        venue_city="Athens",
        venue_state="Attica",
        venue_zip="10001",
        venue_maps_url="https://maps.google.com/venue",
        rsvp_deadline=rsvp_deadline,
        church_name="St. Mary Church",
        church_address="10 Church Rd",
        church_city="Athens",
        church_state="Attica",
        church_zip="10001",
        church_maps_url="https://maps.google.com/church",
    )


def _admin_headers(client: TestClient, admin_credentials: dict) -> dict[str, str]:
    token = client.post("/api/admin/login", json=admin_credentials).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_guest_info_whenrsvpdeadlinepassed_shouldreturn404(client: TestClient, db_session: AsyncSession) -> None:
    yesterday = (datetime.now(UTC).date() - timedelta(days=1)).isoformat()
    db_session.add(_invitation(yesterday))
    db_session.add(InvitedGuest(name="Late Guest", phone="6900000001", token="expired-token"))
    await db_session.commit()

    response = client.get("/api/rsvp/guest-info", params={"token": "expired-token"})

    assert response.status_code == 404
    assert "Late Guest" not in response.text


@pytest.mark.asyncio
async def test_get_guest_info_whenbeforersvpdeadline_shouldreturnguest(client: TestClient, db_session: AsyncSession) -> None:
    tomorrow = (datetime.now(UTC).date() + timedelta(days=1)).isoformat()
    db_session.add(_invitation(tomorrow))
    db_session.add(InvitedGuest(name="Early Guest", phone="6900000002", token="valid-token"))
    await db_session.commit()

    response = client.get("/api/rsvp/guest-info", params={"token": "valid-token"})

    assert response.status_code == 200
    assert response.json()["name"] == "Early Guest"


def test_submit_rsvp_whenguestgivesdetails_shouldnotlogthem(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)

    response = client.post(
        "/api/rsvp",
        json={
            "guest_name": "Eleni Papadopoulou",
            "email": "eleni.private@example.com",
            "phone": "+30 6912345678",
            "attending": True,
            "dietary_restrictions": "Coeliac",
            "plus_one": False,
        },
    )

    assert response.status_code == 201
    logged = "\n".join(record.getMessage() for record in caplog.records if not record.name.startswith("httpx"))
    for private in ("Eleni", "Papadopoulou", "eleni.private@example.com", "6912345678", "Coeliac"):
        assert private not in logged
    assert response.json()["confirmation_number"] in logged


@pytest.mark.asyncio
async def test_delete_all_guest_data_whenconfirmed_shoulderasersvpsandinvitedguests(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    db_session.add(InvitedGuest(name="Guest One", phone="6900000003", token="token-one"))
    db_session.add(InvitedGuest(name="Guest Two", phone="6900000004", token="token-two"))
    await db_session.commit()
    client.post("/api/rsvp", json={"guest_name": "Guest One", "phone": "6900000003", "attending": True})

    response = client.post(
        "/api/admin/guest-data/delete",
        json={"confirmation": "DELETE ALL GUEST DATA"},
        headers=_admin_headers(client, admin_credentials),
    )

    assert response.status_code == 200
    assert response.json() == {"rsvps_deleted": 1, "invited_guests_deleted": 2}
    assert (await db_session.execute(select(func.count()).select_from(RSVP))).scalar_one() == 0
    assert (await db_session.execute(select(func.count()).select_from(InvitedGuest))).scalar_one() == 0
    assert client.get("/api/rsvp/guest-info", params={"token": "token-two"}).status_code == 404


@pytest.mark.asyncio
async def test_delete_all_guest_data_whenphraseiswrong_shouldkeepeverything(client: TestClient, db_session: AsyncSession, admin_credentials: dict) -> None:
    db_session.add(InvitedGuest(name="Guest Kept", phone="6900000005", token="token-kept"))
    await db_session.commit()

    response = client.post(
        "/api/admin/guest-data/delete",
        json={"confirmation": "yes"},
        headers=_admin_headers(client, admin_credentials),
    )

    assert response.status_code == 400
    assert (await db_session.execute(select(func.count()).select_from(InvitedGuest))).scalar_one() == 1


def test_delete_all_guest_data_whennotsignedin_shouldreturn401(client: TestClient) -> None:
    response = client.post("/api/admin/guest-data/delete", json={"confirmation": "DELETE ALL GUEST DATA"})

    assert response.status_code == 401


def test_detailed_health_whendatabasefails_shouldnotexposetheerror(client: TestClient, db_session: AsyncSession, monkeypatch) -> None:
    async def failing_execute(*args, **kwargs):
        raise RuntimeError("could not connect to server at db.internal:5432 as user wedding")

    monkeypatch.setattr(db_session, "execute", failing_execute)

    response = client.get("/api/monitoring/health/detailed")

    assert response.json()["status"] == "unhealthy"
    assert "db.internal" not in response.text


def test_redact_guest_tokens_whenaccessloghastoken_shouldhideit() -> None:
    from wedding_api.main import RedactGuestTokens

    record = logging.LogRecord("uvicorn.access", logging.INFO, "", 0, '%s - "%s %s"', ("1.2.3.4", "GET", "/api/rsvp/guest-info?token=abc123&x=1"), None)

    RedactGuestTokens().filter(record)

    assert "abc123" not in record.getMessage()
    assert "token=[redacted]&x=1" in record.getMessage()
