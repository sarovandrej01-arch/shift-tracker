import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.bot.handlers.messages import handle_telegram_message
from app.bot.services.telegram_photo import DownloadedTelegramPhoto
from app.core.enums import MessageReason, MessageStatus
from app.services.message_processing import MessageProcessingResult


def _message(**overrides: object) -> SimpleNamespace:
    data = {
        "chat": SimpleNamespace(id=-100123),
        "message_id": 456,
        "from_user": SimpleNamespace(id=77, username="ivan"),
        "text": "Начало смены",
        "caption": None,
        "photo": None,
        "date": datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _downloaded() -> DownloadedTelegramPhoto:
    return DownloadedTelegramPhoto(
        file_id="telegram-file-id",
        data=b"jpeg-data",
        content_type="image/jpeg",
        extension="jpg",
    )


def _patch_repository(monkeypatch: pytest.MonkeyPatch, repository: AsyncMock) -> None:
    monkeypatch.setattr(
        "app.bot.handlers.messages.TelegramMessageRepository",
        lambda session: repository,
    )


def _patch_download(monkeypatch: pytest.MonkeyPatch, downloaded: DownloadedTelegramPhoto) -> AsyncMock:
    download = AsyncMock(return_value=downloaded)
    monkeypatch.setattr("app.bot.handlers.messages.download_largest_photo", download)
    return download


def test_duplicate_update_skips_download_and_processing(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = SimpleNamespace(id=1)
        _patch_repository(monkeypatch, repository)
        bot = AsyncMock()
        storage = AsyncMock()
        processor = AsyncMock()

        result = await handle_telegram_message(
            message=_message(photo=[SimpleNamespace(file_id="photo")]),
            bot=bot,
            session=AsyncMock(),
            storage=storage,
            processor=processor,
        )

        assert result is None
        bot.get_file.assert_not_called()
        storage.upload.assert_not_called()
        processor.process.assert_not_called()
        storage.delete.assert_not_called()

    asyncio.run(scenario())


def test_message_without_photo_goes_to_processor(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        _patch_repository(monkeypatch, repository)
        storage = AsyncMock()
        processor = AsyncMock()
        processor.process.return_value = MessageProcessingResult(
            status=MessageStatus.REJECTED,
            reason=MessageReason.NO_PHOTO,
        )
        message = _message()

        await handle_telegram_message(
            message=message,
            bot=AsyncMock(),
            session=AsyncMock(),
            storage=storage,
            processor=processor,
        )

        storage.upload.assert_not_called()
        storage.delete.assert_not_called()
        processor.process.assert_awaited_once()
        incoming = processor.process.await_args.args[0]
        assert incoming.photo_file_id is None
        assert incoming.photo_storage_key is None
        assert incoming.telegram_chat_id == message.chat.id
        assert incoming.telegram_message_id == message.message_id

    asyncio.run(scenario())


def test_photo_is_uploaded_before_processor(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        _patch_repository(monkeypatch, repository)
        _patch_download(monkeypatch, _downloaded())
        storage = AsyncMock()
        processor = AsyncMock()
        processor.process.return_value = MessageProcessingResult(
            status=MessageStatus.ACCEPTED,
            reason=None,
        )

        await handle_telegram_message(
            message=_message(photo=[SimpleNamespace(file_id="telegram-file-id")]),
            bot=AsyncMock(),
            session=AsyncMock(),
            storage=storage,
            processor=processor,
        )

        storage.upload.assert_awaited_once_with(
            key="telegram/2026/10/03/-100123/456.jpg",
            data=b"jpeg-data",
            content_type="image/jpeg",
        )
        incoming = processor.process.await_args.args[0]
        assert incoming.photo_file_id == "telegram-file-id"
        assert incoming.photo_storage_key == "telegram/2026/10/03/-100123/456.jpg"

    asyncio.run(scenario())


def test_storage_failure_does_not_call_processor(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        _patch_repository(monkeypatch, repository)
        _patch_download(monkeypatch, _downloaded())
        storage = AsyncMock()
        storage.upload.side_effect = RuntimeError("s3 unavailable")
        processor = AsyncMock()

        with pytest.raises(RuntimeError, match="s3 unavailable"):
            await handle_telegram_message(
                message=_message(photo=[SimpleNamespace(file_id="telegram-file-id")]),
                bot=AsyncMock(),
                session=AsyncMock(),
                storage=storage,
                processor=processor,
            )

        processor.process.assert_not_called()
        storage.delete.assert_not_called()

    asyncio.run(scenario())


def test_processor_failure_deletes_uploaded_photo(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        _patch_repository(monkeypatch, repository)
        _patch_download(monkeypatch, _downloaded())
        storage = AsyncMock()
        processor = AsyncMock()
        processor.process.side_effect = RuntimeError("processing failed")

        with pytest.raises(RuntimeError, match="processing failed"):
            await handle_telegram_message(
                message=_message(photo=[SimpleNamespace(file_id="telegram-file-id")]),
                bot=AsyncMock(),
                session=AsyncMock(),
                storage=storage,
                processor=processor,
            )

        storage.delete.assert_awaited_once_with(key="telegram/2026/10/03/-100123/456.jpg")

    asyncio.run(scenario())


def test_cleanup_failure_preserves_processor_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        _patch_repository(monkeypatch, repository)
        _patch_download(monkeypatch, _downloaded())
        storage = AsyncMock()
        storage.delete.side_effect = RuntimeError("cleanup failed")
        processor = AsyncMock()
        processor.process.side_effect = RuntimeError("processing failed")

        with pytest.raises(RuntimeError, match="processing failed"):
            await handle_telegram_message(
                message=_message(photo=[SimpleNamespace(file_id="telegram-file-id")]),
                bot=AsyncMock(),
                session=AsyncMock(),
                storage=storage,
                processor=processor,
            )

    asyncio.run(scenario())


def test_review_result_keeps_photo(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        _patch_repository(monkeypatch, repository)
        _patch_download(monkeypatch, _downloaded())
        storage = AsyncMock()
        processor = AsyncMock()
        processor.process.return_value = MessageProcessingResult(
            status=MessageStatus.REVIEW,
            reason=MessageReason.EMPLOYEE_NOT_FOUND,
        )

        await handle_telegram_message(
            message=_message(photo=[SimpleNamespace(file_id="telegram-file-id")]),
            bot=AsyncMock(),
            session=AsyncMock(),
            storage=storage,
            processor=processor,
        )

        storage.delete.assert_not_called()

    asyncio.run(scenario())


def test_duplicate_shift_result_keeps_photo(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        _patch_repository(monkeypatch, repository)
        _patch_download(monkeypatch, _downloaded())
        storage = AsyncMock()
        processor = AsyncMock()
        processor.process.return_value = MessageProcessingResult(
            status=MessageStatus.DUPLICATE,
            reason=MessageReason.SHIFT_ALREADY_EXISTS,
        )

        await handle_telegram_message(
            message=_message(photo=[SimpleNamespace(file_id="telegram-file-id")]),
            bot=AsyncMock(),
            session=AsyncMock(),
            storage=storage,
            processor=processor,
        )

        storage.delete.assert_not_called()

    asyncio.run(scenario())


def test_accepted_result_keeps_photo(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        _patch_repository(monkeypatch, repository)
        _patch_download(monkeypatch, _downloaded())
        storage = AsyncMock()
        processor = AsyncMock()
        processor.process.return_value = MessageProcessingResult(
            status=MessageStatus.ACCEPTED,
            reason=None,
        )

        await handle_telegram_message(
            message=_message(photo=[SimpleNamespace(file_id="telegram-file-id")]),
            bot=AsyncMock(),
            session=AsyncMock(),
            storage=storage,
            processor=processor,
        )

        storage.delete.assert_not_called()

    asyncio.run(scenario())


def test_naive_datetime_is_treated_as_utc(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        _patch_repository(monkeypatch, repository)
        storage = AsyncMock()
        processor = AsyncMock()
        processor.process.return_value = MessageProcessingResult(
            status=MessageStatus.REJECTED,
            reason=MessageReason.NO_PHOTO,
        )

        await handle_telegram_message(
            message=_message(date=datetime(2026, 10, 3, 12, 0)),
            bot=AsyncMock(),
            session=AsyncMock(),
            storage=storage,
            processor=processor,
        )

        incoming = processor.process.await_args.args[0]
        assert incoming.telegram_created_at.tzinfo is not None
        assert incoming.telegram_created_at.utcoffset() == timedelta(0)

    asyncio.run(scenario())
