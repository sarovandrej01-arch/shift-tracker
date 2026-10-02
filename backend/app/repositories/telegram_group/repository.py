from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telegram_group import TelegramGroup

_UPDATABLE_FIELDS = frozenset(
    {
        "telegram_chat_id",
        "name",
        "object_id",
        "is_active",
    }
)


class TelegramGroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, group_id: int) -> TelegramGroup | None:
        stmt = select(TelegramGroup).where(TelegramGroup.id == group_id)
        return await self.session.scalar(stmt)

    async def get_by_telegram_chat_id(self, telegram_chat_id: int) -> TelegramGroup | None:
        stmt = select(TelegramGroup).where(TelegramGroup.telegram_chat_id == telegram_chat_id)
        return await self.session.scalar(stmt)

    async def exists_by_telegram_chat_id(
        self,
        telegram_chat_id: int,
        *,
        exclude_group_id: int | None = None,
    ) -> bool:
        stmt = select(TelegramGroup.id).where(TelegramGroup.telegram_chat_id == telegram_chat_id)
        if exclude_group_id is not None:
            stmt = stmt.where(TelegramGroup.id != exclude_group_id)
        return await self.session.scalar(stmt) is not None

    async def get_by_name(self, name: str) -> TelegramGroup | None:
        stmt = select(TelegramGroup).where(func.lower(TelegramGroup.name) == name.strip().lower())
        return await self.session.scalar(stmt)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        object_id: int | None = None,
        search: str | None = None,
    ) -> list[TelegramGroup]:
        stmt = select(TelegramGroup)
        if is_active is not None:
            stmt = stmt.where(TelegramGroup.is_active == is_active)
        if object_id is not None:
            stmt = stmt.where(TelegramGroup.object_id == object_id)
        if search is not None and search.strip():
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(TelegramGroup.name.ilike(pattern))
        stmt = stmt.order_by(TelegramGroup.id).offset(offset).limit(limit)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        *,
        telegram_chat_id: int,
        name: str,
        object_id: int,
        is_active: bool = True,
    ) -> TelegramGroup:
        group = TelegramGroup(
            telegram_chat_id=telegram_chat_id,
            name=name,
            object_id=object_id,
            is_active=is_active,
        )
        self.session.add(group)
        await self.session.flush()
        await self.session.refresh(group)
        return group

    async def update(self, group: TelegramGroup, changes: dict[str, object]) -> TelegramGroup:
        for field, value in changes.items():
            if field in _UPDATABLE_FIELDS:
                setattr(group, field, value)
        await self.session.flush()
        await self.session.refresh(group)
        return group
