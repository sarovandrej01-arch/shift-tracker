import asyncio
from datetime import datetime, time, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest

from app.core.enums import MessageReason, MessageStatus
from app.schemas.telegram_message import TelegramMessageCreate
from app.services.message_processing import (
    IncomingTelegramMessage,
    MessageProcessor,
    ShiftDetector,
)
from app.services.message_processing.employee_matcher import EmployeeMatchResult, EmployeeMatchStatus
from app.services.message_processing.shift_detector import ShiftDetectionResult, ShiftDetectionStatus

MOSCOW = ZoneInfo("Europe/Moscow")
_UNSET = object()


def _incoming(**overrides: object) -> IncomingTelegramMessage:
    data = {
        "telegram_chat_id": -100123,
        "telegram_message_id": 50,
        "telegram_user_id": 77,
        "telegram_username": "ivan",
        "text": "Начало смены",
        "caption": None,
        "photo_file_id": "photo-1",
        "telegram_created_at": datetime(2026, 10, 2, 20, 30, tzinfo=MOSCOW),
        "photo_storage_key": None,
    }
    data.update(overrides)
    return IncomingTelegramMessage(**data)


def _message() -> SimpleNamespace:
    return SimpleNamespace(id=10, status=MessageStatus.PROCESSING, reason=None)


def _processor(
    *,
    group: object = _UNSET,
    work_object: object = _UNSET,
    employee_status: EmployeeMatchStatus = EmployeeMatchStatus.MATCHED,
    shift_status: ShiftDetectionStatus = ShiftDetectionStatus.MATCHED,
    existing_message: object | None = None,
    existing_shift: object | None = None,
    use_real_detector: bool = False,
) -> tuple[MessageProcessor, SimpleNamespace]:
    session = AsyncMock()
    messages = AsyncMock()
    groups = AsyncMock()
    objects = AsyncMock()
    shifts = AsyncMock()
    logs = AsyncMock()
    matcher = AsyncMock()
    detector = ShiftDetector() if use_real_detector else MagicMock()

    stored = _message()
    messages.get_by_telegram_message.return_value = existing_message
    messages.create.return_value = stored

    async def set_status(message: SimpleNamespace, *, status: MessageStatus, reason: MessageReason | None = None) -> SimpleNamespace:
        message.status = status
        message.reason = reason
        return message

    messages.set_status.side_effect = set_status
    messages.assign_work_object.side_effect = lambda message, object_id: message
    messages.assign_employee.side_effect = lambda message, employee_id: message
    messages.set_shift_date.side_effect = lambda message, shift_date: message

    if group is _UNSET:
        group = SimpleNamespace(id=1, object_id=3, is_active=True)
    groups.get_by_telegram_chat_id.return_value = group

    if work_object is _UNSET:
        work_object = SimpleNamespace(
            id=3,
            is_active=True,
            timezone="Europe/Moscow",
            shift_start_time=time(20, 0),
            checkin_before_minutes=60,
            checkin_after_minutes=300,
        )
    objects.get_by_id.return_value = work_object

    employee = SimpleNamespace(id=7, is_active=True)
    matcher.match.return_value = EmployeeMatchResult(
        status=employee_status,
        employee=employee if employee_status is EmployeeMatchStatus.MATCHED else None,
        matched_by="telegram_user_id" if employee_status is EmployeeMatchStatus.MATCHED else None,
        candidates=[SimpleNamespace(id=1), SimpleNamespace(id=4)]
        if employee_status is EmployeeMatchStatus.AMBIGUOUS
        else [],
    )

    if not use_real_detector:
        detector.detect.return_value = ShiftDetectionResult(
            status=shift_status,
            shift_date=datetime(2026, 10, 2).date() if shift_status is ShiftDetectionStatus.MATCHED else None,
            message_local_datetime=datetime(2026, 10, 2, 20, 30, tzinfo=MOSCOW),
        )

    created_shift = SimpleNamespace(id=99)
    shifts.get_existing_shift.return_value = existing_shift
    shifts.create.return_value = created_shift

    processor = MessageProcessor(
        session=session,
        telegram_message_repository=messages,
        telegram_group_repository=groups,
        work_object_repository=objects,
        shift_repository=shifts,
        processing_log_repository=logs,
        employee_matcher=matcher,
        shift_detector=detector,
    )
    parts = SimpleNamespace(
        session=session,
        messages=messages,
        groups=groups,
        objects=objects,
        shifts=shifts,
        logs=logs,
        matcher=matcher,
        detector=detector,
        employee=employee,
        created_shift=created_shift,
        stored=stored,
    )
    return processor, parts


def _actions(parts: SimpleNamespace) -> list[str]:
    return [call.kwargs["action"] for call in parts.logs.create.await_args_list]


def test_message_create_schema_accepts_storage_key() -> None:
    empty = TelegramMessageCreate(
        telegram_chat_id=1,
        telegram_message_id=2,
        telegram_created_at=datetime(2026, 10, 3, tzinfo=timezone.utc),
        photo_storage_key=None,
    )
    filled = TelegramMessageCreate(
        telegram_chat_id=1,
        telegram_message_id=2,
        telegram_created_at=datetime(2026, 10, 3, tzinfo=timezone.utc),
        photo_storage_key="  telegram/2026/10/03/photo.jpg  ",
    )

    assert empty.photo_storage_key is None
    assert filled.photo_storage_key == "telegram/2026/10/03/photo.jpg"


def test_successful_processing_commits_once() -> None:
    async def scenario() -> None:
        processor, parts = _processor()
        result = await processor.process(_incoming())

        assert result.status is MessageStatus.ACCEPTED
        assert result.reason is None
        assert result.shift is parts.created_shift
        parts.messages.assign_work_object.assert_awaited()
        parts.messages.assign_employee.assert_awaited()
        parts.messages.set_shift_date.assert_awaited()
        parts.shifts.create.assert_awaited()
        parts.session.commit.assert_awaited_once()
        parts.session.rollback.assert_not_awaited()
        assert _actions(parts) == [
            "message_received",
            "work_object_resolved",
            "employee_matched",
            "shift_date_detected",
            "accepted",
        ]
        assert all(call.kwargs["user_id"] is None for call in parts.logs.create.await_args_list)

    asyncio.run(scenario())


def test_storage_key_is_passed_to_repository() -> None:
    async def scenario() -> None:
        processor, parts = _processor()
        await processor.process(
            _incoming(
                photo_file_id="telegram-file-id",
                photo_storage_key="telegram/2026/10/03/photo.jpg",
            )
        )

        parts.messages.create.assert_awaited_once()
        assert parts.messages.create.await_args.kwargs["photo_storage_key"] == "telegram/2026/10/03/photo.jpg"

    asyncio.run(scenario())


def test_missing_storage_key_does_not_reject_photo() -> None:
    async def scenario() -> None:
        processor, parts = _processor()
        result = await processor.process(
            _incoming(photo_file_id="telegram-file-id", photo_storage_key=None)
        )

        assert result.status is MessageStatus.ACCEPTED
        assert parts.messages.create.await_args.kwargs["photo_storage_key"] is None

    asyncio.run(scenario())


def test_no_photo_rejects_before_matching() -> None:
    async def scenario() -> None:
        processor, parts = _processor()
        result = await processor.process(_incoming(photo_file_id=None, photo_storage_key=None))

        assert result.status is MessageStatus.REJECTED
        assert result.reason is MessageReason.NO_PHOTO
        parts.matcher.match.assert_not_called()
        parts.shifts.create.assert_not_called()
        parts.session.commit.assert_awaited_once()

    asyncio.run(scenario())


def test_missing_group_goes_to_review() -> None:
    async def scenario() -> None:
        processor, parts = _processor(group=None)
        result = await processor.process(_incoming())

        assert result.status is MessageStatus.REVIEW
        assert result.reason is MessageReason.GROUP_NOT_CONFIGURED
        parts.matcher.match.assert_not_called()

    asyncio.run(scenario())


def test_inactive_group_goes_to_review() -> None:
    async def scenario() -> None:
        processor, parts = _processor(group=SimpleNamespace(id=1, object_id=3, is_active=False))
        result = await processor.process(_incoming())

        assert result.status is MessageStatus.REVIEW
        assert result.reason is MessageReason.GROUP_NOT_CONFIGURED
        parts.matcher.match.assert_not_called()

    asyncio.run(scenario())


def test_inactive_work_object_goes_to_review() -> None:
    async def scenario() -> None:
        processor, parts = _processor(
            work_object=SimpleNamespace(
                id=3,
                is_active=False,
                timezone="Europe/Moscow",
                shift_start_time=time(20, 0),
                checkin_before_minutes=60,
                checkin_after_minutes=300,
            )
        )
        result = await processor.process(_incoming())

        assert result.status is MessageStatus.REVIEW
        assert result.reason is MessageReason.GROUP_NOT_CONFIGURED
        parts.detector.detect.assert_not_called()

    asyncio.run(scenario())


def test_employee_not_found() -> None:
    async def scenario() -> None:
        processor, parts = _processor(employee_status=EmployeeMatchStatus.NOT_FOUND)
        result = await processor.process(_incoming())

        assert result.status is MessageStatus.REVIEW
        assert result.reason is MessageReason.EMPLOYEE_NOT_FOUND
        parts.detector.detect.assert_not_called()

    asyncio.run(scenario())


def test_employee_ambiguous() -> None:
    async def scenario() -> None:
        processor, parts = _processor(employee_status=EmployeeMatchStatus.AMBIGUOUS)
        result = await processor.process(_incoming())

        assert result.status is MessageStatus.REVIEW
        assert result.reason is MessageReason.EMPLOYEE_AMBIGUOUS
        details = parts.logs.create.await_args_list[-1].kwargs["details"]
        assert details == "candidate_ids=1,4"
        parts.detector.detect.assert_not_called()

    asyncio.run(scenario())


def test_outside_shift_window_does_not_create_shift() -> None:
    async def scenario() -> None:
        processor, parts = _processor(shift_status=ShiftDetectionStatus.OUTSIDE_WINDOW)
        result = await processor.process(_incoming())

        assert result.status is MessageStatus.REVIEW
        assert result.reason is MessageReason.OUTSIDE_SHIFT_WINDOW
        parts.shifts.create.assert_not_called()

    asyncio.run(scenario())


def test_duplicate_shift() -> None:
    async def scenario() -> None:
        processor, parts = _processor(existing_shift=SimpleNamespace(id=5))
        result = await processor.process(_incoming())

        assert result.status is MessageStatus.DUPLICATE
        assert result.reason is MessageReason.SHIFT_ALREADY_EXISTS
        parts.shifts.create.assert_not_called()
        assert parts.logs.create.await_args_list[-1].kwargs["details"] == "existing_shift_id=5"

    asyncio.run(scenario())


def test_duplicate_telegram_update_does_not_rewrite_message() -> None:
    async def scenario() -> None:
        existing = SimpleNamespace(id=4, status=MessageStatus.ACCEPTED, reason=None)
        processor, parts = _processor(existing_message=existing)
        result = await processor.process(_incoming())

        assert result.status is MessageStatus.DUPLICATE
        assert result.reason is MessageReason.MESSAGE_ALREADY_PROCESSED
        assert result.message is existing
        assert existing.status is MessageStatus.ACCEPTED
        parts.messages.create.assert_not_called()
        parts.messages.set_status.assert_not_called()
        parts.logs.create.assert_not_called()
        parts.session.commit.assert_not_called()

    asyncio.run(scenario())


def test_night_shift_uses_previous_shift_date() -> None:
    async def scenario() -> None:
        processor, parts = _processor(use_real_detector=True)
        result = await processor.process(
            _incoming(telegram_created_at=datetime(2026, 10, 3, 0, 30, tzinfo=MOSCOW))
        )

        assert result.status is MessageStatus.ACCEPTED
        assert parts.shifts.create.await_args.kwargs["shift_date"].isoformat() == "2026-10-02"

    asyncio.run(scenario())


def test_unexpected_error_rolls_back() -> None:
    async def scenario() -> None:
        processor, parts = _processor()
        parts.shifts.create.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            await processor.process(_incoming())

        parts.session.rollback.assert_awaited_once()
        parts.session.commit.assert_not_called()

    asyncio.run(scenario())
