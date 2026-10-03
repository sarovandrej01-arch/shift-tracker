from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.processing_log import ProcessingLogNotFoundError
from app.core.exceptions.telegram_message import TelegramMessageNotFoundError
from app.core.query_validation import ensure_aware_datetime, ensure_date_order
from app.models.processing_log import ProcessingLog
from app.repositories.processing_log.repository import ProcessingLogRepository
from app.repositories.telegram_message.repository import TelegramMessageRepository


def _optional_details(details: str | None) -> str | None:
    if details is None:
        return None
    normalized = details.strip()
    return normalized or None


class ProcessingLogService:
    def __init__(
        self,
        repository: ProcessingLogRepository,
        session: AsyncSession,
        message_repository: TelegramMessageRepository | None = None,
    ) -> None:
        self.repository = repository
        self.session = session
        self.message_repository = message_repository

    async def create_log(
        self,
        *,
        message_id: int,
        action: str,
        details: str | None = None,
        user_id: int | None = None,
    ) -> ProcessingLog:
        normalized_action = action.strip()
        if not normalized_action:
            raise ValueError("action must not be empty")

        try:
            log = await self.repository.create(
                message_id=message_id,
                action=normalized_action,
                details=_optional_details(details),
                user_id=user_id,
            )
            await self.session.commit()
            return log
        except Exception:
            await self.session.rollback()
            raise

    async def get_log(self, log_id: int) -> ProcessingLog:
        log = await self.repository.get_by_id(log_id)
        if log is None:
            raise ProcessingLogNotFoundError
        return log

    async def list_logs(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        message_id: int | None = None,
        user_id: int | None = None,
        action: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[ProcessingLog]:
        if offset < 0 or not 1 <= limit <= 100:
            raise ValueError("offset must be >= 0 and limit must be between 1 and 100")
        ensure_aware_datetime(date_from, "date_from")
        ensure_aware_datetime(date_to, "date_to")
        ensure_date_order(date_from, date_to)
        return await self.repository.list(
            offset=offset,
            limit=limit,
            message_id=message_id,
            user_id=user_id,
            action=action,
            date_from=date_from,
            date_to=date_to,
        )

    async def list_message_logs(self, message_id: int) -> list[ProcessingLog]:
        if self.message_repository is None:
            raise RuntimeError("message repository is not configured")
        message = await self.message_repository.get_by_id(message_id)
        if message is None:
            raise TelegramMessageNotFoundError
        return await self.repository.list_by_message(message_id)

    async def list_by_message(self, message_id: int) -> list[ProcessingLog]:
        return await self.repository.list_by_message(message_id)
