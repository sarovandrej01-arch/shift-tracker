import asyncio
from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import InvalidDateRangeError
from app.repositories.dashboard.repository import (
    MessageStatusCounts,
    ObjectMessageCounts,
    ObjectShiftCounts,
    ShiftConfirmationCounts,
)
from app.services.dashboard import DashboardService


def _messages(**overrides: int) -> MessageStatusCounts:
    data = {
        "total": 0,
        "new": 0,
        "processing": 0,
        "accepted": 0,
        "review": 0,
        "rejected": 0,
        "duplicate": 0,
        "error": 0,
    }
    data.update(overrides)
    return MessageStatusCounts(**data)


def _shifts(**overrides: int) -> ShiftConfirmationCounts:
    data = {"total": 0, "automatic": 0, "manual": 0}
    data.update(overrides)
    return ShiftConfirmationCounts(**data)


def _service() -> tuple[DashboardService, AsyncMock]:
    repository = AsyncMock()
    repository.message_status_counts.return_value = _messages()
    repository.shift_confirmation_counts.return_value = _shifts()
    repository.message_counts_by_object.return_value = []
    repository.shift_counts_by_object.return_value = []
    repository.object_names.return_value = {}
    return DashboardService(repository, today=lambda: date(2026, 10, 3)), repository


def test_summary_defaults_to_business_today() -> None:
    async def scenario() -> None:
        service, repository = _service()

        summary = await service.summary()

        assert summary.period.date_from == date(2026, 10, 3)
        assert summary.period.date_to == date(2026, 10, 3)
        assert repository.message_status_counts.await_args.kwargs["date_from"] == date(2026, 10, 3)
        assert repository.shift_confirmation_counts.await_args.kwargs["object_id"] is None

    asyncio.run(scenario())


def test_summary_counts_and_object_filter() -> None:
    async def scenario() -> None:
        service, repository = _service()
        repository.message_status_counts.return_value = _messages(
            total=10,
            accepted=5,
            review=2,
            rejected=1,
            duplicate=1,
            error=1,
        )
        repository.shift_confirmation_counts.return_value = _shifts(total=5, automatic=4, manual=1)
        repository.message_counts_by_object.return_value = [
            ObjectMessageCounts(object_id=1, messages_total=10, accepted=5, review=2, rejected=1)
        ]
        repository.shift_counts_by_object.return_value = [type("Row", (), {"object_id": 1, "shifts_total": 5})()]
        repository.object_names.return_value = {1: "Тестовый объект"}

        summary = await service.summary(
            date_from=date(2026, 10, 3),
            date_to=date(2026, 10, 3),
            object_id=1,
        )

        assert summary.messages.accepted == 5
        assert summary.messages.review == 2
        assert summary.shifts.automatic == 4
        assert summary.shifts.manual == 1
        assert summary.by_object[0].object_name == "Тестовый объект"
        assert summary.by_object[0].shifts_total == 5
        assert repository.message_status_counts.await_args.kwargs["object_id"] == 1

    asyncio.run(scenario())


def test_empty_period_is_zero() -> None:
    async def scenario() -> None:
        service, _repository = _service()

        summary = await service.summary(date_from=date(2026, 1, 1), date_to=date(2026, 1, 2))

        assert summary.messages.total == 0
        assert summary.messages.accepted == 0
        assert summary.shifts.total == 0
        assert summary.shifts.automatic == 0
        assert summary.shifts.manual == 0
        assert summary.by_object == []

    asyncio.run(scenario())


def test_inverted_dashboard_dates_do_not_query() -> None:
    async def scenario() -> None:
        service, repository = _service()

        with pytest.raises(InvalidDateRangeError):
            await service.summary(date_from=date(2026, 10, 4), date_to=date(2026, 10, 1))

        repository.message_status_counts.assert_not_awaited()

    asyncio.run(scenario())
