from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

from aiogram import Bot
from aiogram.types import Message, PhotoSize


@dataclass(slots=True)
class DownloadedTelegramPhoto:
    file_id: str
    data: bytes
    content_type: str
    extension: str


def select_largest_photo(photos: Sequence[PhotoSize]) -> PhotoSize:
    return max(photos, key=lambda photo: (photo.file_size or 0, photo.width * photo.height))


def build_telegram_photo_storage_key(
    *,
    telegram_chat_id: int,
    telegram_message_id: int,
    telegram_created_at: datetime,
    extension: str = "jpg",
) -> str:
    normalized_extension = extension.strip().lstrip(".") or "jpg"
    created_on = telegram_created_at.date()
    return (
        f"telegram/{created_on:%Y/%m/%d}/{telegram_chat_id}/"
        f"{telegram_message_id}.{normalized_extension}"
    )


async def download_largest_photo(
    *,
    bot: Bot,
    message: Message,
) -> DownloadedTelegramPhoto | None:
    photos = message.photo
    if not photos:
        return None

    photo = select_largest_photo(photos)
    telegram_file = await bot.get_file(photo.file_id)
    if not telegram_file.file_path:
        raise RuntimeError("Telegram file path is missing")

    buffer = BytesIO()
    await bot.download_file(telegram_file.file_path, destination=buffer)
    data = buffer.getvalue()
    if not data:
        raise RuntimeError("Telegram photo download is empty")

    return DownloadedTelegramPhoto(
        file_id=photo.file_id,
        data=data,
        content_type="image/jpeg",
        extension="jpg",
    )
