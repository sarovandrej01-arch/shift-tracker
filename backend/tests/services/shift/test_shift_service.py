import asyncio
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import InvalidDateRangeError, ShiftNotFoundError
from app.services.shift import ShiftService

NOW = datetime(2026, 10, 3, 15, 0, tzinfo=timezone.utc)


def _shift(**overrides: object) -> SimpleNamespace:
    data: dict[str, object] = {
        "id": 1,
        "employee_id": 1,
        "object_id": 1,
        "shift_date": date(2026, 10, 3),
        "source_message_id": 4,
        "confirmed_manually": False,
        "confirmed_by_user_id": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _service(shift: object | None = None) -> tuple[ShiftService, SimpleNamespace]:
    repository = AsyncMock()
    repository.get_by_id.return_value = shift if shift is not None else _shift()
    employees = AsyncMock()
    objects = AsyncMock()
    messages = AsyncMock()
    users = AsyncMock()
    employees.get_by_id.return_value = SimpleNamespace(id=1, full_name="Мехоношин")
    objects.get_by_id.return_value = SimpleNamespace(id=1, name="Тестовый объект")
    messages.get_by_id.return_value = SimpleNamespace(id=4)
    users.get_by_id.return_value = SimpleNamespace(id=8, full_name="Moderator")
    service = ShiftService(
        repository,
        AsyncMock(),
        employee_repository=employees,
        work_object_repository=objects,
        message_repository=messages,
        user_repository=users,
    )
    return service, SimpleNamespace(
        repository=repository,
        employees=employees,
        objects=objects,
        messages=messages,
        users=users,
    )


def test_list_shifts_passes_filters() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.repository.list.return_value = [_shift()]

        result = await service.list_shifts(
            offset=10,
            limit=5,
            employee_id=1,
            object_id=2,
            date_from=date(2026, 10, 1),
            date_to=date(2026, 10, 3),
            confirmed_manually=False,
        )

        assert result[0].source_message_id == 4
        assert result[0].confirmed_by_user_id is None
        parts.repository.list.assert_awaited_once_with(
            offset=10,
            limit=5,
            employee_id=1,
            object_id=2,
            date_from=date(2026, 10, 1),
            date_to=date(2026, 10, 3),
            confirmed_manually=False,
        )

    asyncio.run(scenario())


def test_list_shifts_rejects_inverted_dates() -> None:
    async def scenario() -> None:
        service, parts = _service()

        with pytest.raises(InvalidDateRangeError):
            await service.list_shifts(date_from=date(2026, 10, 4), date_to=date(2026, 10, 1))

        parts.repository.list.assert_not_awaited()

    asyncio.run(scenario())


def test_shift_detail_loads_relations_without_confirmer_for_automatic_shift() -> None:
    async def scenario() -> None:
        service, parts = _service(_shift(confirmed_manually=False, confirmed_by_user_id=None))

        detail = await service.get_shift_detail(1)

        assert detail.employee.full_name == "Мехоношин"
        assert detail.work_object.name == "Тестовый объект"
        assert detail.source_message.id == 4
        assert detail.confirmed_by_user is None
        parts.users.get_by_id.assert_not_awaited()

    asyncio.run(scenario())


def test_shift_detail_loads_confirmer_for_manual_shift() -> None:
    async def scenario() -> None:
        service, parts = _service(_shift(confirmed_manually=True, confirmed_by_user_id=8, source_message_id=None))

        detail = await service.get_shift_detail(1)

        assert detail.confirmed_by_user.full_name == "Moderator"
        assert detail.source_message is None
        parts.messages.get_by_id.assert_not_awaited()
        parts.users.get_by_id.assert_awaited_once_with(8)

    asyncio.run(scenario())


def test_shift_detail_not_found() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.repository.get_by_id.return_value = None

        with pytest.raises(ShiftNotFoundError):
            await service.get_shift_detail(99)

    asyncio.run(scenario())
