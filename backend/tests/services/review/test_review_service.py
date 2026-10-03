import asyncio
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.enums import MessageReason, MessageStatus
from app.core.exceptions import (
    EmployeeNotFoundError,
    ReviewConfirmationIncompleteError,
    ShiftAlreadyExistsError,
    TelegramMessageNotFoundError,
    TelegramMessageNotInReviewError,
    WorkObjectNotFoundError,
)
from app.schemas.review import ReviewConfirmRequest, ReviewRejectRequest
from app.services.review import ReviewService

NOW = datetime(2026, 10, 3, 15, 18, tzinfo=timezone.utc)


def _message(**overrides: object) -> SimpleNamespace:
    data: dict[str, object] = {
        "id": 10,
        "status": MessageStatus.REVIEW,
        "reason": MessageReason.EMPLOYEE_NOT_FOUND,
        "employee_id": None,
        "object_id": None,
        "shift_date": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _service(message: object | None = None) -> tuple[ReviewService, SimpleNamespace]:
    session = AsyncMock()
    messages = AsyncMock()
    employees = AsyncMock()
    objects = AsyncMock()
    shifts = AsyncMock()
    logs = AsyncMock()
    messages.get_by_id.return_value = message if message is not None else _message()

    async def update(stored: SimpleNamespace, changes: dict[str, object]) -> SimpleNamespace:
        for key, value in changes.items():
            setattr(stored, key, value)
        return stored

    messages.update.side_effect = update
    employees.get_by_id.return_value = SimpleNamespace(id=1, is_active=True)
    objects.get_by_id.return_value = SimpleNamespace(id=2, is_active=True)
    shifts.get_existing_shift.return_value = None
    shifts.create.return_value = SimpleNamespace(id=5)
    service = ReviewService(
        session=session,
        message_repository=messages,
        employee_repository=employees,
        work_object_repository=objects,
        shift_repository=shifts,
        processing_log_repository=logs,
    )
    return service, SimpleNamespace(
        session=session,
        messages=messages,
        employees=employees,
        objects=objects,
        shifts=shifts,
        logs=logs,
    )


def _confirm(**overrides: object) -> ReviewConfirmRequest:
    data = {"employee_id": 1, "object_id": 2, "shift_date": date(2026, 10, 3)}
    data.update(overrides)
    return ReviewConfirmRequest(**data)


def test_list_reviews_requests_only_review_messages_with_filters() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.messages.list.return_value = [_message()]

        result = await service.list_reviews(
            offset=20,
            limit=10,
            reason=MessageReason.OUTSIDE_SHIFT_WINDOW,
            employee_id=7,
            object_id=3,
            date_from=date(2026, 10, 1),
            date_to=date(2026, 10, 3),
        )

        assert len(result) == 1
        parts.messages.list.assert_awaited_once_with(
            offset=20,
            limit=10,
            status=MessageStatus.REVIEW,
            reason=MessageReason.OUTSIDE_SHIFT_WINDOW,
            employee_id=7,
            object_id=3,
            date_from=date(2026, 10, 1),
            date_to=date(2026, 10, 3),
        )

    asyncio.run(scenario())


def test_confirm_accepts_review_and_creates_manual_shift() -> None:
    async def scenario() -> None:
        message = _message()
        service, parts = _service(message)

        result = await service.confirm(10, _confirm(), user_id=4)

        assert result.message.status is MessageStatus.ACCEPTED
        assert result.message.reason is None
        assert result.message.employee_id == 1
        assert result.message.object_id == 2
        assert result.message.shift_date == date(2026, 10, 3)
        assert result.shift.id == 5
        parts.shifts.create.assert_awaited_once_with(
            employee_id=1,
            object_id=2,
            shift_date=date(2026, 10, 3),
            source_message_id=10,
            confirmed_manually=True,
            confirmed_by_user_id=4,
        )
        parts.logs.create.assert_awaited_once_with(
            message_id=10,
            user_id=4,
            action="manual_confirm",
            details="employee_id=1; object_id=2; shift_date=2026-10-03; shift_id=5",
        )
        parts.session.commit.assert_awaited_once()
        parts.session.rollback.assert_not_awaited()

    asyncio.run(scenario())


def test_confirm_uses_values_already_stored_on_the_message() -> None:
    async def scenario() -> None:
        service, parts = _service(
            _message(employee_id=8, object_id=9, shift_date=date(2026, 10, 2))
        )

        await service.confirm(10, ReviewConfirmRequest(), user_id=4)

        assert parts.shifts.create.await_args.kwargs["employee_id"] == 8
        assert parts.shifts.create.await_args.kwargs["object_id"] == 9
        assert parts.shifts.create.await_args.kwargs["shift_date"] == date(2026, 10, 2)

    asyncio.run(scenario())


def test_confirm_request_overrides_stored_values() -> None:
    async def scenario() -> None:
        service, parts = _service(
            _message(employee_id=8, object_id=9, shift_date=date(2026, 10, 2))
        )

        await service.confirm(10, _confirm(), user_id=4)

        assert parts.shifts.create.await_args.kwargs["employee_id"] == 1
        assert parts.shifts.create.await_args.kwargs["object_id"] == 2
        assert parts.shifts.create.await_args.kwargs["shift_date"] == date(2026, 10, 3)

    asyncio.run(scenario())


def test_confirm_message_not_found() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.messages.get_by_id.return_value = None

        with pytest.raises(TelegramMessageNotFoundError):
            await service.confirm(10, _confirm(), user_id=4)

        parts.shifts.create.assert_not_awaited()
        parts.session.commit.assert_not_awaited()

    asyncio.run(scenario())


def test_confirm_rejects_message_that_is_not_in_review() -> None:
    async def scenario() -> None:
        service, parts = _service(_message(status=MessageStatus.ACCEPTED))

        with pytest.raises(TelegramMessageNotInReviewError):
            await service.confirm(10, _confirm(), user_id=4)

        parts.shifts.create.assert_not_awaited()
        parts.session.commit.assert_not_awaited()

    asyncio.run(scenario())


def test_confirm_requires_employee_object_and_shift_date() -> None:
    async def scenario() -> None:
        service, parts = _service(_message())

        with pytest.raises(ReviewConfirmationIncompleteError) as exc_info:
            await service.confirm(10, ReviewConfirmRequest(employee_id=1), user_id=4)

        assert exc_info.value.missing_fields == ["object_id", "shift_date"]
        parts.shifts.create.assert_not_awaited()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("employee", "expected"),
    [
        (None, EmployeeNotFoundError),
        (SimpleNamespace(id=1, is_active=False), EmployeeNotFoundError),
    ],
)
def test_confirm_requires_active_employee(employee: object, expected: type[Exception]) -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.employees.get_by_id.return_value = employee

        with pytest.raises(expected):
            await service.confirm(10, _confirm(), user_id=4)

        parts.shifts.create.assert_not_awaited()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("work_object", "expected"),
    [
        (None, WorkObjectNotFoundError),
        (SimpleNamespace(id=2, is_active=False), WorkObjectNotFoundError),
    ],
)
def test_confirm_requires_active_work_object(work_object: object, expected: type[Exception]) -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.objects.get_by_id.return_value = work_object

        with pytest.raises(expected):
            await service.confirm(10, _confirm(), user_id=4)

        parts.shifts.create.assert_not_awaited()

    asyncio.run(scenario())


def test_confirm_does_not_create_duplicate_shift() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.shifts.get_existing_shift.return_value = SimpleNamespace(id=9)

        with pytest.raises(ShiftAlreadyExistsError):
            await service.confirm(10, _confirm(), user_id=4)

        parts.shifts.create.assert_not_awaited()
        parts.session.commit.assert_not_awaited()
        parts.session.rollback.assert_awaited_once()

    asyncio.run(scenario())


def test_confirm_turns_integrity_error_into_conflict_and_rolls_back() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.shifts.create.side_effect = IntegrityError("INSERT", {}, Exception("duplicate"))

        with pytest.raises(ShiftAlreadyExistsError):
            await service.confirm(10, _confirm(), user_id=4)

        parts.messages.update.assert_not_awaited()
        parts.session.commit.assert_not_awaited()
        parts.session.rollback.assert_awaited_once()

    asyncio.run(scenario())


def test_confirm_rolls_back_when_shift_create_fails() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.shifts.create.side_effect = RuntimeError("shift failed")

        with pytest.raises(RuntimeError, match="shift failed"):
            await service.confirm(10, _confirm(), user_id=4)

        parts.messages.update.assert_not_awaited()
        parts.logs.create.assert_not_awaited()
        parts.session.commit.assert_not_awaited()
        parts.session.rollback.assert_awaited_once()

    asyncio.run(scenario())


def test_confirm_rolls_back_when_log_create_fails() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.logs.create.side_effect = RuntimeError("log failed")

        with pytest.raises(RuntimeError, match="log failed"):
            await service.confirm(10, _confirm(), user_id=4)

        parts.shifts.create.assert_awaited()
        parts.messages.update.assert_awaited()
        parts.session.commit.assert_not_awaited()
        parts.session.rollback.assert_awaited_once()

    asyncio.run(scenario())


def test_reject_keeps_reason_and_writes_audit_log() -> None:
    async def scenario() -> None:
        message = _message(reason=MessageReason.OUTSIDE_SHIFT_WINDOW)
        service, parts = _service(message)

        result = await service.reject(
            10,
            ReviewRejectRequest(comment="  Сотрудник не относится к этому объекту  "),
            user_id=4,
        )

        assert result.status is MessageStatus.REJECTED
        assert result.reason is MessageReason.OUTSIDE_SHIFT_WINDOW
        assert parts.messages.update.await_args.args[1] == {"status": MessageStatus.REJECTED}
        parts.logs.create.assert_awaited_once_with(
            message_id=10,
            user_id=4,
            action="manual_reject",
            details="Сотрудник не относится к этому объекту",
        )
        parts.session.commit.assert_awaited_once()
        parts.session.rollback.assert_not_awaited()

    asyncio.run(scenario())


def test_reject_without_comment_stores_empty_details() -> None:
    async def scenario() -> None:
        service, parts = _service()

        await service.reject(10, ReviewRejectRequest(comment="   "), user_id=4)

        assert parts.logs.create.await_args.kwargs["details"] is None
        assert parts.logs.create.await_args.kwargs["user_id"] == 4

    asyncio.run(scenario())


def test_reject_message_not_found() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.messages.get_by_id.return_value = None

        with pytest.raises(TelegramMessageNotFoundError):
            await service.reject(10, ReviewRejectRequest(), user_id=4)

        parts.session.commit.assert_not_awaited()

    asyncio.run(scenario())


def test_reject_message_that_is_not_in_review() -> None:
    async def scenario() -> None:
        service, parts = _service(_message(status=MessageStatus.DUPLICATE))

        with pytest.raises(TelegramMessageNotInReviewError):
            await service.reject(10, ReviewRejectRequest(comment="Test rejection"), user_id=4)

        parts.logs.create.assert_not_awaited()
        parts.session.commit.assert_not_awaited()

    asyncio.run(scenario())


def test_reject_rolls_back_when_log_create_fails() -> None:
    async def scenario() -> None:
        service, parts = _service()
        parts.logs.create.side_effect = RuntimeError("log failed")

        with pytest.raises(RuntimeError, match="log failed"):
            await service.reject(10, ReviewRejectRequest(comment="Test rejection"), user_id=4)

        parts.session.commit.assert_not_awaited()
        parts.session.rollback.assert_awaited_once()

    asyncio.run(scenario())
