from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MessageReason, MessageStatus
from app.models.telegram_message import TelegramMessage

def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


_UPDATABLE_FIELDS = frozenset(
    {
        "status",
        "reason",
        "employee_id",
        "object_id",
        "shift_date",
    }
)


class TelegramMessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, message_id: int) -> TelegramMessage | None:
        stmt = select(TelegramMessage).where(TelegramMessage.id == message_id)
        return await self.session.scalar(stmt)

    async def get_by_telegram_message(
        self,
        telegram_chat_id: int,
        telegram_message_id: int,
    ) -> TelegramMessage | None:
        stmt = select(TelegramMessage).where(
            TelegramMessage.telegram_chat_id == telegram_chat_id,
            TelegramMessage.telegram_message_id == telegram_message_id,
        )
        return await self.session.scalar(stmt)

    async def exists_by_telegram_message(
        self,
        telegram_chat_id: int,
        telegram_message_id: int,
    ) -> bool:
        stmt = select(TelegramMessage.id).where(
            TelegramMessage.telegram_chat_id == telegram_chat_id,
            TelegramMessage.telegram_message_id == telegram_message_id,
        )
        return await self.session.scalar(stmt) is not None

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        status: MessageStatus | None = None,
        reason: MessageReason | None = None,
        employee_id: int | None = None,
        object_id: int | None = None,
    ) -> list[TelegramMessage]:
        stmt = select(TelegramMessage)
        if status is not None:
            stmt = stmt.where(TelegramMessage.status == status)
        if reason is not None:
            stmt = stmt.where(TelegramMessage.reason == reason)
        if employee_id is not None:
            stmt = stmt.where(TelegramMessage.employee_id == employee_id)
        if object_id is not None:
            stmt = stmt.where(TelegramMessage.object_id == object_id)
        stmt = stmt.order_by(TelegramMessage.id.desc()).offset(offset).limit(limit)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        *,
        telegram_chat_id: int,
        telegram_message_id: int,
        telegram_user_id: int | None,
        telegram_username: str | None,
        text: str | None,
        caption: str | None,
        photo_file_id: str | None,
        telegram_created_at: datetime,
        photo_storage_key: str | None = None,
        status: MessageStatus = MessageStatus.NEW,
    ) -> TelegramMessage:
        message = TelegramMessage(
            telegram_chat_id=telegram_chat_id,
            telegram_message_id=telegram_message_id,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            text=text,
            caption=caption,
            photo_file_id=photo_file_id,
            photo_storage_key=_blank_to_none(photo_storage_key),
            telegram_created_at=telegram_created_at,
            status=status,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def update(self, message: TelegramMessage, changes: dict[str, object]) -> TelegramMessage:
        for field, value in changes.items():
            if field in _UPDATABLE_FIELDS:
                setattr(message, field, value)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def set_status(
        self,
        message: TelegramMessage,
        *,
        status: MessageStatus,
        reason: MessageReason | None = None,
    ) -> TelegramMessage:
        message.status = status
        message.reason = reason
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def assign_employee(
        self,
        message: TelegramMessage,
        employee_id: int | None,
    ) -> TelegramMessage:
        message.employee_id = employee_id
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def assign_work_object(
        self,
        message: TelegramMessage,
        object_id: int | None,
    ) -> TelegramMessage:
        message.object_id = object_id
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def set_shift_date(
        self,
        message: TelegramMessage,
        shift_date: date | None,
    ) -> TelegramMessage:
        message.shift_date = shift_date
        await self.session.flush()
        await self.session.refresh(message)
        return message
