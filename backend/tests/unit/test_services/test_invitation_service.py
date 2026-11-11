import pytest

from wedding_api.services.invitation_service import InvitationService


@pytest.mark.anyio
async def test_get_invitation_not_found(db_session, monkeypatch):
    svc = InvitationService(db_session)

    class DummyRepo:
        async def get_invitation(self):
            return None

    svc.repository = DummyRepo()  # type: ignore[attr-defined]

    result = await svc.get_invitation()
    assert result is None
