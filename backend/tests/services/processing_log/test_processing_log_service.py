import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import InvalidDateRangeError, TelegramMessageNotFoundError
from app.services.processing_log import ProcessingLogService

NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)


def _log(**overrides: object) -> SimpleNamespace:
    data: dict[str, object] = {
        "id": 1,
        "message_id": 4,
        "user_id": None,
        "action": "message_received",
        "details": None,
        "created_at": NOW,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _service() -> tuple[ProcessingLogService, SimpleNamespace]:
    repository = AsyncMock()
    messages = AsyncMock()
    messages.get_by_id.return_value = SimpleNamespace(id=4)
    service = ProcessingLogService(repository, AsyncMock(), message_repository=messages)
    return service, SimpleNamespace(repository=repository, messages=messages)


def test_list_logs_passes_filters() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.repository.list.return_value = [_log(user_id=3, details="shift_id=1")]
        start = datetime(2026, 10, 3, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 10, 3, 23, 59, tzinfo=timezone.utc)

        result = await service.list_logs(
            offset=2,
            limit=10,
            message_id=4,
            user_id=3,
            action="manual_confirm",
            date_from=start,
            date_to=end,
        )

        assert result[0].details == "shift_id=1"
        assert result[0].user_id == 3
        parts.repository.list.assert_awaited_once_with(
            offset=2,
            limit=10,
            message_id=4,
            user_id=3,
            action="manual_confirm",
            date_from=start,
            date_to=end,
        )

    asyncio.run(scenario())


def test_list_logs_rejects_inverted_or_naive_datetimes() -> None:
    async def scenario() -> None:
        service, parts = _service()
        start = datetime(2026, 10, 4, tzinfo=timezone.utc)
        end = datetime(2026, 10, 3, tzinfo=timezone.utc)

        with pytest.raises(InvalidDateRangeError):
            await service.list_logs(date_from=start, date_to=end)
        with pytest.raises(InvalidDateRangeError, match="timezone-aware"):
            await service.list_logs(date_from=datetime(2026, 10, 3))

        parts.repository.list.assert_not_awaited()

    asyncio.run(scenario())


def test_message_logs_are_loaded_chronologically_from_repository() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.repository.list_by_message.return_value = [
            _log(id=1, action="message_received", created_at=NOW),
            _log(id=2, action="accepted", created_at=NOW, details="shift_id=1"),
        ]

        result = await service.list_message_logs(4)

        assert [item.action for item in result] == ["message_received", "accepted"]
        assert result[1].details == "shift_id=1"
        parts.repository.list_by_message.assert_awaited_once_with(4)

    asyncio.run(scenario())


def test_message_logs_missing_message() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.messages.get_by_id.return_value = None

        with pytest.raises(TelegramMessageNotFoundError):
            await service.list_message_logs(4)

        parts.repository.list_by_message.assert_not_awaited()

    asyncio.run(scenario())
