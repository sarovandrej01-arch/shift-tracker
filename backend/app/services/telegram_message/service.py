from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MessageReason, MessageStatus
from app.core.exceptions.telegram_message import (
    TelegramMessageAlreadyExistsError,
    TelegramMessageNotFoundError,
)
from app.models.telegram_message import TelegramMessage
from app.repositories.telegram_message.repository import TelegramMessageRepository
from app.schemas.telegram_message import TelegramMessageCreate


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class TelegramMessageService:
    def __init__(self, repository: TelegramMessageRepository, session: AsyncSession) -> None:
        self.repository = repository
        self.session = session

    async def create_message(self, data: TelegramMessageCreate) -> TelegramMessage:
        existing = await self.repository.get_by_telegram_message(
            telegram_chat_id=data.telegram_chat_id,
            telegram_message_id=data.telegram_message_id,
        )
        if existing is not None:
            raise TelegramMessageAlreadyExistsError

        try:
            message = await self.repository.create(
                telegram_chat_id=data.telegram_chat_id,
                telegram_message_id=data.telegram_message_id,
                telegram_user_id=data.telegram_user_id,
                telegram_username=_optional_text(data.telegram_username),
                text=_optional_text(data.text),
                caption=_optional_text(data.caption),
                photo_file_id=_optional_text(data.photo_file_id),
                telegram_created_at=data.telegram_created_at,
                status=MessageStatus.NEW,
            )
            await self.session.commit()
            return message
        except Exception:
            await self.session.rollback()
            raise

    async def get_message(self, message_id: int) -> TelegramMessage:
        message = await self.repository.get_by_id(message_id)
        if message is None:
            raise TelegramMessageNotFoundError
        return message

    async def get_by_telegram_message(
        self,
        telegram_chat_id: int,
        telegram_message_id: int,
    ) -> TelegramMessage | None:
        return await self.repository.get_by_telegram_message(
            telegram_chat_id=telegram_chat_id,
            telegram_message_id=telegram_message_id,
        )

    async def list_messages(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        status: MessageStatus | None = None,
        reason: MessageReason | None = None,
        employee_id: int | None = None,
        object_id: int | None = None,
    ) -> list[TelegramMessage]:
        if offset < 0 or not 1 <= limit <= 100:
            raise ValueError("offset must be >= 0 and limit must be between 1 and 100")
        return await self.repository.list(
            offset=offset,
            limit=limit,
            status=status,
            reason=reason,
            employee_id=employee_id,
            object_id=object_id,
        )

    async def update_status(
        self,
        message: TelegramMessage,
        *,
        status: MessageStatus,
        reason: MessageReason | None = None,
    ) -> TelegramMessage:
        try:
            message = await self.repository.set_status(message, status=status, reason=reason)
            await self.session.commit()
            return message
        except Exception:
            await self.session.rollback()
            raise
