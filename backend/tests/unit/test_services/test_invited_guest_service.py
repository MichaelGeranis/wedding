"""Unit tests for InvitedGuestService."""

import asyncio
from datetime import UTC, datetime

import pytest

from wedding_api.models.invited_guest import InvitedGuestCreate, InvitedGuestResponse, InvitedGuestUpdate
from wedding_api.models.invited_guest_stats import InvitedGuestStats
from wedding_api.services.invited_guest_service import InvitedGuestService


class FakeRepo:
    def __init__(self):
        self._store = {}
        self._next_id = 1

    async def create_invited_guest(self, guest_data: InvitedGuestCreate) -> InvitedGuestResponse:
        now = datetime.now(UTC)
        obj = InvitedGuestResponse(
            id=self._next_id,
            name=guest_data.name,
            phone=guest_data.phone,
            token=f"token-{self._next_id}",
            notes=guest_data.notes,
            invitation_sent=False,
            rsvp_received=False,
            created_at=now,
            updated_at=None,
        )
        self._store[self._next_id] = obj
        self._next_id += 1
        return obj

    async def get_invited_guest_by_id(self, guest_id: int) -> InvitedGuestResponse | None:
        return self._store.get(guest_id)

    async def get_invited_guest_by_phone(self, phone: str) -> InvitedGuestResponse | None:
        for v in self._store.values():
            if v.phone == phone:
                return v
        return None

    async def get_invited_guest_by_token(self, token: str) -> InvitedGuestResponse | None:
        for v in self._store.values():
            if v.token == token:
                return v
        return None

    async def list_invited_guests(self) -> list[InvitedGuestResponse]:
        return list(self._store.values())

    async def update_invited_guest(self, guest_id: int, guest_data: InvitedGuestUpdate) -> InvitedGuestResponse | None:
        existing = self._store.get(guest_id)
        if not existing:
            return None
        if guest_data.name is not None:
            existing.name = guest_data.name
        if guest_data.phone is not None:
            existing.phone = guest_data.phone
        if guest_data.notes is not None:
            existing.notes = guest_data.notes
        if guest_data.invitation_sent is not None:
            existing.invitation_sent = guest_data.invitation_sent
        if guest_data.rsvp_received is not None:
            existing.rsvp_received = guest_data.rsvp_received
        existing.updated_at = datetime.now(UTC)
        return existing

    async def delete_invited_guest(self, guest_id: int) -> bool:
        return self._store.pop(guest_id, None) is not None


@pytest.mark.asyncio
async def test_create_and_get_invited_guest(monkeypatch) -> None:
    fake = FakeRepo()
    service = InvitedGuestService.__new__(InvitedGuestService)
    service.repository = fake

    create = InvitedGuestCreate(name="John Doe", phone="+1234567890", notes="#child #plusone")

    created = await service.create_invited_guest(create)

    assert created.id == 1
    assert created.name == "John Doe"

    fetched = await service.get_invited_guest(1)
    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_check_phone_invited_and_get_by_token(monkeypatch) -> None:
    fake = FakeRepo()
    service = InvitedGuestService.__new__(InvitedGuestService)
    service.repository = fake

    create = InvitedGuestCreate(name="Alice", phone="+1112223333", notes=None)
    created = await service.create_invited_guest(create)

    assert await service.check_phone_invited("+1112223333") is True
    assert await service.check_phone_invited("+9999999999") is False

    by_token = await service.get_guest_by_token(created.token)
    assert by_token is not None
    assert by_token.phone == "+1112223333"


@pytest.mark.asyncio
async def test_list_update_delete_and_stats(monkeypatch) -> None:
    fake = FakeRepo()
    service = InvitedGuestService.__new__(InvitedGuestService)
    service.repository = fake

    # Create multiple guests with notes containing tags
    await service.create_invited_guest(InvitedGuestCreate(name="Guest One", phone="+1000000001", notes="#child"))
    await service.create_invited_guest(InvitedGuestCreate(name="Guest Two", phone="+1000000002", notes="#plusone #child"))
    await service.create_invited_guest(InvitedGuestCreate(name="Guest Three", phone="+1000000003", notes=None))

    listing = await service.list_invited_guests()
    assert listing.total == 3

    # Stats should count children and plus ones
    stats = await service.get_invited_guest_stats()
    assert isinstance(stats, InvitedGuestStats)
    assert stats.total_children == 2
    assert stats.total_plus_ones == 1
    assert stats.total_invited_base == 3
    assert stats.total_invited == 6  # 3 base + 2 children + 1 plusone

    # Update a guest
    updated = await service.update_invited_guest(2, InvitedGuestUpdate(name="John Smith", invitation_sent=True))
    assert updated is not None
    assert updated.name == "John Smith"
    assert updated.invitation_sent is True

    # Delete a guest
    deleted = await service.delete_invited_guest(3)
    assert deleted is True
    listing2 = await service.list_invited_guests()
    assert listing2.total == 2
