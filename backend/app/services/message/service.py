from dataclasses import dataclass
from datetime import date

from app.core.enums import MessageReason, MessageStatus
from app.core.exceptions.telegram_message import (
    TelegramMessageNotFoundError,
    TelegramMessagePhotoNotFoundError,
)
from app.models.employee import Employee
from app.models.shift import Shift
from app.models.telegram_message import TelegramMessage
from app.models.work_object import WorkObject
from app.repositories.employee.repository import EmployeeRepository
from app.repositories.shift.repository import ShiftRepository
from app.repositories.telegram_message.repository import TelegramMessageRepository
from app.repositories.work_object.repository import WorkObjectRepository
from app.services.storage.base import ObjectStorage


@dataclass(slots=True)
class MessageDetail:
    message: TelegramMessage
    employee: Employee | None
    work_object: WorkObject | None
    shift: Shift | None


@dataclass(slots=True)
class MessagePhotoUrl:
    message_id: int
    url: str
    expires_in: int


def _validate_pagination(offset: int, limit: int) -> None:
    if offset < 0 or not 1 <= limit <= 100:
        raise ValueError("offset must be >= 0 and limit must be between 1 and 100")


def _validate_date_range(
    date_from: date | None,
    date_to: date | None,
    *,
    label: str,
) -> None:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise ValueError(f"{label}_from must be less than or equal to {label}_to")


class MessageService:
    def __init__(
        self,
        *,
        message_repository: TelegramMessageRepository,
        employee_repository: EmployeeRepository,
        work_object_repository: WorkObjectRepository,
        shift_repository: ShiftRepository,
        storage: ObjectStorage,
        presigned_url_expire_seconds: int,
    ) -> None:
        self.message_repository = message_repository
        self.employee_repository = employee_repository
        self.work_object_repository = work_object_repository
        self.shift_repository = shift_repository
        self.storage = storage
        self.presigned_url_expire_seconds = presigned_url_expire_seconds

    async def list_messages(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        status: MessageStatus | None = None,
        reason: MessageReason | None = None,
        employee_id: int | None = None,
        object_id: int | None = None,
        telegram_chat_id: int | None = None,
        telegram_user_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        shift_date_from: date | None = None,
        shift_date_to: date | None = None,
    ) -> list[TelegramMessage]:
        _validate_pagination(offset, limit)
        _validate_date_range(date_from, date_to, label="date")
        _validate_date_range(shift_date_from, shift_date_to, label="shift_date")
        return await self.message_repository.list(
            offset=offset,
            limit=limit,
            status=status,
            reason=reason,
            employee_id=employee_id,
            object_id=object_id,
            telegram_chat_id=telegram_chat_id,
            telegram_user_id=telegram_user_id,
            date_from=date_from,
            date_to=date_to,
            shift_date_from=shift_date_from,
            shift_date_to=shift_date_to,
        )

    async def get_message(self, message_id: int) -> MessageDetail:
        message = await self.message_repository.get_by_id(message_id)
        if message is None:
            raise TelegramMessageNotFoundError
        employee = None
        if message.employee_id is not None:
            employee = await self.employee_repository.get_by_id(message.employee_id)
        work_object = None
        if message.object_id is not None:
            work_object = await self.work_object_repository.get_by_id(message.object_id)
        shift = await self.shift_repository.get_by_source_message_id(message.id)
        return MessageDetail(
            message=message,
            employee=employee,
            work_object=work_object,
            shift=shift,
        )

    async def get_photo_url(self, message_id: int) -> MessagePhotoUrl:
        message = await self.message_repository.get_by_id(message_id)
        if message is None:
            raise TelegramMessageNotFoundError
        storage_key = message.photo_storage_key
        if storage_key is None or not storage_key.strip():
            raise TelegramMessagePhotoNotFoundError
        url = await self.storage.get_presigned_url(
            key=storage_key,
            expires_seconds=self.presigned_url_expire_seconds,
        )
        return MessagePhotoUrl(
            message_id=message.id,
            url=url,
            expires_in=self.presigned_url_expire_seconds,
        )
