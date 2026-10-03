from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing_log import ProcessingLog


def _required_action(action: str) -> str:
    normalized = action.strip()
    if not normalized:
        raise ValueError("action must not be empty")
    return normalized


def _optional_details(details: str | None) -> str | None:
    if details is None:
        return None
    normalized = details.strip()
    return normalized or None


class ProcessingLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, log_id: int) -> ProcessingLog | None:
        stmt = select(ProcessingLog).where(ProcessingLog.id == log_id)
        return await self.session.scalar(stmt)

    async def list_by_message(self, message_id: int) -> list[ProcessingLog]:
        stmt = (
            select(ProcessingLog)
            .where(ProcessingLog.message_id == message_id)
            .order_by(ProcessingLog.created_at, ProcessingLog.id)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def list(
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
        stmt = select(ProcessingLog)
        if message_id is not None:
            stmt = stmt.where(ProcessingLog.message_id == message_id)
        if user_id is not None:
            stmt = stmt.where(ProcessingLog.user_id == user_id)
        if action is not None and action.strip():
            stmt = stmt.where(ProcessingLog.action == action.strip())
        if date_from is not None:
            stmt = stmt.where(ProcessingLog.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(ProcessingLog.created_at <= date_to)
        stmt = stmt.order_by(ProcessingLog.created_at.desc(), ProcessingLog.id.desc()).offset(offset).limit(limit)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        *,
        message_id: int,
        action: str,
        details: str | None = None,
        user_id: int | None = None,
    ) -> ProcessingLog:
        log = ProcessingLog(
            message_id=message_id,
            action=_required_action(action),
            details=_optional_details(details),
            user_id=user_id,
        )
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log
