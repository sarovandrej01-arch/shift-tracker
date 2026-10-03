import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.bot.handlers.messages import handle_telegram_message
from app.bot.services.telegram_photo import DownloadedTelegramPhoto
from app.core.enums import MessageStatus
from app.services.message_processing import MessageProcessingResult


def _message(*, photo: list | None) -> SimpleNamespace:
    return SimpleNamespace(
        chat=SimpleNamespace(id=-100123),
        message_id=456,
        from_user=SimpleNamespace(id=7, username="ivan"),
        text=None,
        caption="смена",
        photo=photo,
        date=datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc),
    )


def _downloaded() -> DownloadedTelegramPhoto:
    return DownloadedTelegramPhoto(
        file_id="telegram-file-id",
        data=b"jpeg-bytes",
        content_type="image/jpeg",
        extension="jpg",
    )


def test_message_without_photo_skips_storage() -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        storage = AsyncMock()
        processor = AsyncMock()
        processor.process.return_value = MessageProcessingResult(
            status=MessageStatus.REJECTED,
            reason=None,
        )

        with patch(
            "app.bot.handlers.messages.TelegramMessageRepository",
            return_value=repository,
        ):
            await handle_telegram_message(
                message=_message(photo=None),
                bot=AsyncMock(),
                session=AsyncMock(),
                storage=storage,
                processor=processor,
            )

        storage.upload.assert_not_called()
        incoming = processor.process.await_args.args[0]
        assert incoming.photo_file_id is None
        assert incoming.photo_storage_key is None

    asyncio.run(scenario())


def test_photo_is_uploaded_before_processing() -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        storage = AsyncMock()
        processor = AsyncMock()
        processor.process.return_value = MessageProcessingResult(
            status=MessageStatus.ACCEPTED,
            reason=None,
        )

        with (
            patch(
                "app.bot.handlers.messages.TelegramMessageRepository",
                return_value=repository,
            ),
            patch(
                "app.bot.handlers.messages.download_largest_photo",
                AsyncMock(return_value=_downloaded()),
            ) as download,
        ):
            await handle_telegram_message(
                message=_message(photo=[SimpleNamespace(file_id="telegram-file-id")]),
                bot=AsyncMock(),
                session=AsyncMock(),
                storage=storage,
                processor=processor,
            )

        download.assert_awaited_once()
        storage.upload.assert_awaited_once()
        processor.process.assert_awaited_once()
        incoming = processor.process.await_args.args[0]
        assert incoming.photo_file_id == "telegram-file-id"
        assert incoming.photo_storage_key == "telegram/2026/10/03/-100123/456.jpg"
        assert storage.upload.await_args.kwargs["content_type"] == "image/jpeg"

    asyncio.run(scenario())


def test_duplicate_update_skips_download_and_processing() -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = SimpleNamespace(id=1)
        storage = AsyncMock()
        processor = AsyncMock()

        with (
            patch(
                "app.bot.handlers.messages.TelegramMessageRepository",
                return_value=repository,
            ),
            patch(
                "app.bot.handlers.messages.download_largest_photo",
                AsyncMock(),
            ) as download,
        ):
            result = await handle_telegram_message(
                message=_message(photo=[SimpleNamespace(file_id="telegram-file-id")]),
                bot=AsyncMock(),
                session=AsyncMock(),
                storage=storage,
                processor=processor,
            )

        assert result is None
        download.assert_not_called()
        storage.upload.assert_not_called()
        processor.process.assert_not_called()

    asyncio.run(scenario())


def test_storage_failure_does_not_call_processor() -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        storage = AsyncMock()
        storage.upload.side_effect = RuntimeError("s3 unavailable")
        processor = AsyncMock()

        with (
            patch(
                "app.bot.handlers.messages.TelegramMessageRepository",
                return_value=repository,
            ),
            patch(
                "app.bot.handlers.messages.download_largest_photo",
                AsyncMock(return_value=_downloaded()),
            ),
            pytest.raises(RuntimeError, match="s3 unavailable"),
        ):
            await handle_telegram_message(
                message=_message(photo=[SimpleNamespace(file_id="telegram-file-id")]),
                bot=AsyncMock(),
                session=AsyncMock(),
                storage=storage,
                processor=processor,
            )

        processor.process.assert_not_called()

    asyncio.run(scenario())


def test_processor_failure_deletes_uploaded_photo() -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        storage = AsyncMock()
        processor = AsyncMock()
        processor.process.side_effect = RuntimeError("processor failed")

        with (
            patch(
                "app.bot.handlers.messages.TelegramMessageRepository",
                return_value=repository,
            ),
            patch(
                "app.bot.handlers.messages.download_largest_photo",
                AsyncMock(return_value=_downloaded()),
            ),
            pytest.raises(RuntimeError, match="processor failed"),
        ):
            await handle_telegram_message(
                message=_message(photo=[SimpleNamespace(file_id="telegram-file-id")]),
                bot=AsyncMock(),
                session=AsyncMock(),
                storage=storage,
                processor=processor,
            )

        storage.delete.assert_awaited_once_with(key="telegram/2026/10/03/-100123/456.jpg")

    asyncio.run(scenario())


def test_cleanup_failure_preserves_processor_exception() -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_message.return_value = None
        storage = AsyncMock()
        storage.delete.side_effect = RuntimeError("cleanup failed")
        processor = AsyncMock()
        processor.process.side_effect = RuntimeError("processor failed")

        with (
            patch(
                "app.bot.handlers.messages.TelegramMessageRepository",
                return_value=repository,
            ),
            patch(
                "app.bot.handlers.messages.download_largest_photo",
                AsyncMock(return_value=_downloaded()),
            ),
            pytest.raises(RuntimeError, match="processor failed"),
        ):
            await handle_telegram_message(
                message=_message(photo=[SimpleNamespace(file_id="telegram-file-id")]),
                bot=AsyncMock(),
                session=AsyncMock(),
                storage=storage,
                processor=processor,
            )

    asyncio.run(scenario())
