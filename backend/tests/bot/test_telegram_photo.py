import asyncio
from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.bot.services.telegram_photo import (
    build_telegram_photo_storage_key,
    download_largest_photo,
    select_largest_photo,
)


def test_selects_largest_photo_by_file_size() -> None:
    small = SimpleNamespace(file_id="small", width=100, height=100, file_size=10)
    large = SimpleNamespace(file_id="large", width=20, height=20, file_size=500)

    selected = select_largest_photo([small, large])

    assert selected.file_id == "large"


def test_storage_key_uses_message_date() -> None:
    key = build_telegram_photo_storage_key(
        telegram_chat_id=-100123,
        telegram_message_id=456,
        telegram_created_at=datetime(2026, 10, 3, 21, 15, tzinfo=timezone.utc),
    )

    assert key == "telegram/2026/10/03/-100123/456.jpg"


def test_download_largest_photo_returns_jpeg_bytes() -> None:
    async def scenario() -> None:
        message = SimpleNamespace(
            photo=[
                SimpleNamespace(file_id="small", width=10, height=10, file_size=1),
                SimpleNamespace(file_id="large", width=10, height=10, file_size=99),
            ]
        )
        bot = AsyncMock()
        bot.get_file.return_value = SimpleNamespace(file_path="photos/file.jpg")

        async def download_file(file_path: str, destination: BytesIO) -> None:
            assert file_path == "photos/file.jpg"
            destination.write(b"jpeg-bytes")

        bot.download_file.side_effect = download_file

        downloaded = await download_largest_photo(bot=bot, message=message)

        assert downloaded is not None
        assert downloaded.file_id == "large"
        assert downloaded.data == b"jpeg-bytes"
        assert downloaded.content_type == "image/jpeg"
        assert downloaded.extension == "jpg"
        bot.get_file.assert_awaited_once_with("large")

    asyncio.run(scenario())


def test_download_without_photo_returns_none() -> None:
    async def scenario() -> None:
        downloaded = await download_largest_photo(
            bot=AsyncMock(),
            message=SimpleNamespace(photo=None),
        )

        assert downloaded is None

    asyncio.run(scenario())


def test_missing_file_path_raises() -> None:
    async def scenario() -> None:
        bot = AsyncMock()
        bot.get_file.return_value = SimpleNamespace(file_path=None)
        message = SimpleNamespace(
            photo=[SimpleNamespace(file_id="only", width=1, height=1, file_size=1)]
        )

        with pytest.raises(RuntimeError, match="file path"):
            await download_largest_photo(bot=bot, message=message)

    asyncio.run(scenario())


def test_empty_download_raises() -> None:
    async def scenario() -> None:
        bot = AsyncMock()
        bot.get_file.return_value = SimpleNamespace(file_path="photos/file.jpg")
        message = SimpleNamespace(
            photo=[SimpleNamespace(file_id="only", width=1, height=1, file_size=1)]
        )

        with pytest.raises(RuntimeError, match="empty"):
            await download_largest_photo(bot=bot, message=message)

    asyncio.run(scenario())
