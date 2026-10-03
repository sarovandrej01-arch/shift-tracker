import logging
from datetime import datetime, timezone

from aiogram import Bot, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.services.telegram_photo import (
    build_telegram_photo_storage_key,
    download_largest_photo,
)
from app.repositories.telegram_message.repository import TelegramMessageRepository
from app.services.message_processing import IncomingTelegramMessage, MessageProcessingResult, MessageProcessor
from app.services.storage.base import ObjectStorage

logger = logging.getLogger(__name__)


def ensure_aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def handle_telegram_message(
    *,
    message: Message,
    bot: Bot,
    session: AsyncSession,
    storage: ObjectStorage,
    processor: MessageProcessor,
) -> MessageProcessingResult | None:
    repository = TelegramMessageRepository(session)
    existing = await repository.get_by_telegram_message(
        telegram_chat_id=message.chat.id,
        telegram_message_id=message.message_id,
    )
    if existing is not None:
        logger.info(
            "skip duplicate telegram update chat_id=%s message_id=%s",
            message.chat.id,
            message.message_id,
        )
        return None

    created_at = ensure_aware_datetime(message.date)
    photo_file_id = None
    storage_key = None
    if message.photo:
        downloaded = await download_largest_photo(bot=bot, message=message)
        if downloaded is None:
            raise RuntimeError("Telegram photo could not be downloaded")
        storage_key = build_telegram_photo_storage_key(
            telegram_chat_id=message.chat.id,
            telegram_message_id=message.message_id,
            telegram_created_at=created_at,
            extension=downloaded.extension,
        )
        await storage.upload(
            key=storage_key,
            data=downloaded.data,
            content_type=downloaded.content_type,
        )
        photo_file_id = downloaded.file_id

    incoming = IncomingTelegramMessage(
        telegram_chat_id=message.chat.id,
        telegram_message_id=message.message_id,
        telegram_user_id=message.from_user.id if message.from_user else None,
        telegram_username=message.from_user.username if message.from_user else None,
        text=message.text,
        caption=message.caption,
        photo_file_id=photo_file_id,
        telegram_created_at=created_at,
        photo_storage_key=storage_key,
    )
    try:
        result = await processor.process(incoming)
    except Exception:
        if storage_key is not None:
            try:
                await storage.delete(key=storage_key)
            except Exception:
                logger.exception(
                    "failed to delete uploaded photo after processing error chat_id=%s message_id=%s",
                    message.chat.id,
                    message.message_id,
                )
        raise

    logger.info(
        "processed telegram message chat_id=%s message_id=%s status=%s reason=%s",
        message.chat.id,
        message.message_id,
        result.status.value,
        result.reason.value if result.reason else None,
    )
    return result


def build_message_router(storage: ObjectStorage, session_factory, processor_factory) -> Router:
    message_router = Router()

    @message_router.message()
    async def on_message(message: Message, bot: Bot) -> None:
        async with session_factory() as session:
            processor = processor_factory(session)
            await handle_telegram_message(
                message=message,
                bot=bot,
                session=session,
                storage=storage,
                processor=processor,
            )

    return message_router
