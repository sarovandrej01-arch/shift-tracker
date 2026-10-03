import asyncio
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.enums import MessageReason, MessageStatus
from app.core.exceptions import StorageError, TelegramMessageNotFoundError, TelegramMessagePhotoNotFoundError
from app.services.message import MessageService



def _message(**overrides: object) -> SimpleNamespace:
    data: dict[str, object] = {
        "id": 10,
        "employee_id": 1,
        "object_id": 2,
        "photo_storage_key": "telegram/2026/10/03/-100/4.jpg",
        "status": MessageStatus.ACCEPTED,
        "reason": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _service(
    message: object | None = None,
    *,
    storage: AsyncMock | None = None,
) -> tuple[MessageService, SimpleNamespace]:
    messages = AsyncMock()
    employees = AsyncMock()
    objects = AsyncMock()
    shifts = AsyncMock()
    storage = storage or AsyncMock()
    messages.get_by_id.return_value = message if message is not None else _message()
    employees.get_by_id.return_value = SimpleNamespace(id=1, full_name="Мехоношин")
    objects.get_by_id.return_value = SimpleNamespace(id=2, name="Тестовый объект")
    shifts.get_by_source_message_id.return_value = SimpleNamespace(id=5, source_message_id=10)
    storage.get_presigned_url.return_value = "http://localhost:9000/shift-tracker/photo.jpg"
    service = MessageService(
        message_repository=messages,
        employee_repository=employees,
        work_object_repository=objects,
        shift_repository=shifts,
        storage=storage,
        presigned_url_expire_seconds=3600,
    )
    return service, SimpleNamespace(
        messages=messages,
        employees=employees,
        objects=objects,
        shifts=shifts,
        storage=storage,
    )


def test_list_messages_passes_filters_and_pagination() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.messages.list.return_value = [_message()]

        result = await service.list_messages(
            offset=5,
            limit=2,
            status=MessageStatus.REVIEW,
            reason=MessageReason.EMPLOYEE_NOT_FOUND,
            employee_id=1,
            object_id=2,
            telegram_chat_id=-5108163234,
            telegram_user_id=5614718277,
            date_from=date(2026, 10, 1),
            date_to=date(2026, 10, 3),
            shift_date_from=date(2026, 10, 3),
            shift_date_to=date(2026, 10, 3),
        )

        assert result[0].photo_storage_key == "telegram/2026/10/03/-100/4.jpg"
        parts.messages.list.assert_awaited_once_with(
            offset=5,
            limit=2,
            status=MessageStatus.REVIEW,
            reason=MessageReason.EMPLOYEE_NOT_FOUND,
            employee_id=1,
            object_id=2,
            telegram_chat_id=-5108163234,
            telegram_user_id=5614718277,
            date_from=date(2026, 10, 1),
            date_to=date(2026, 10, 3),
            shift_date_from=date(2026, 10, 3),
            shift_date_to=date(2026, 10, 3),
        )

    asyncio.run(scenario())


def test_list_messages_rejects_inverted_date_range() -> None:
    async def scenario() -> None:
        service, parts = _service()

        with pytest.raises(ValueError, match="date_from"):
            await service.list_messages(date_from=date(2026, 10, 4), date_to=date(2026, 10, 1))

        parts.messages.list.assert_not_awaited()

    asyncio.run(scenario())


def test_get_message_returns_employee_object_and_shift() -> None:
    async def scenario() -> None:
        service, parts = _service()

        detail = await service.get_message(10)

        assert detail.message.id == 10
        assert detail.employee.full_name == "Мехоношин"
        assert detail.work_object.name == "Тестовый объект"
        assert detail.shift.id == 5
        parts.shifts.get_by_source_message_id.assert_awaited_once_with(10)

    asyncio.run(scenario())


def test_get_message_skips_missing_relations() -> None:
    async def scenario() -> None:
        service, parts = _service(_message(employee_id=None, object_id=None))
        parts.shifts.get_by_source_message_id.return_value = None

        detail = await service.get_message(10)

        assert detail.employee is None
        assert detail.work_object is None
        assert detail.shift is None
        parts.employees.get_by_id.assert_not_awaited()
        parts.objects.get_by_id.assert_not_awaited()

    asyncio.run(scenario())


def test_get_message_not_found() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.messages.get_by_id.return_value = None

        with pytest.raises(TelegramMessageNotFoundError):
            await service.get_message(10)

    asyncio.run(scenario())


def test_photo_url_uses_storage_and_configured_expiry() -> None:
    async def scenario() -> None:
        service, parts = _service()

        photo = await service.get_photo_url(10)

        assert photo.message_id == 10
        assert photo.url == "http://localhost:9000/shift-tracker/photo.jpg"
        assert photo.expires_in == 3600
        parts.storage.get_presigned_url.assert_awaited_once_with(
            key="telegram/2026/10/03/-100/4.jpg",
            expires_seconds=3600,
        )

    asyncio.run(scenario())


def test_photo_url_message_not_found() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.messages.get_by_id.return_value = None

        with pytest.raises(TelegramMessageNotFoundError):
            await service.get_photo_url(10)

        parts.storage.get_presigned_url.assert_not_awaited()

    asyncio.run(scenario())


@pytest.mark.parametrize("storage_key", [None, "   "])
def test_photo_url_missing_storage_key(storage_key: str | None) -> None:
    async def scenario() -> None:
        service, parts = _service(_message(photo_storage_key=storage_key))

        with pytest.raises(TelegramMessagePhotoNotFoundError):
            await service.get_photo_url(10)

        parts.storage.get_presigned_url.assert_not_awaited()

    asyncio.run(scenario())


def test_photo_url_storage_error_propagates() -> None:
    async def scenario() -> None:
        storage = AsyncMock()
        storage.get_presigned_url.side_effect = StorageError("secret-key")
        service, _parts = _service(storage=storage)

        with pytest.raises(StorageError, match="secret-key"):
            await service.get_photo_url(10)

    asyncio.run(scenario())


def test_detail_shift_lookup_uses_message_primary_key() -> None:
    async def scenario() -> None:
        service, parts = _service(_message(id=42, employee_id=None, object_id=None))

        await service.get_message(42)

        parts.shifts.get_by_source_message_id.assert_awaited_once_with(42)

    asyncio.run(scenario())
