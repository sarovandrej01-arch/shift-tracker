from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.telegram_group import (
    TelegramGroupChatAlreadyExistsError,
    TelegramGroupNotFoundError,
    TelegramGroupWorkObjectNotFoundError,
)
from app.models.telegram_group import TelegramGroup
from app.repositories.telegram_group.repository import TelegramGroupRepository
from app.repositories.work_object.repository import WorkObjectRepository
from app.schemas.telegram_group import TelegramGroupCreate, TelegramGroupUpdate


def _required_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("name must not be empty")
    return normalized


class TelegramGroupService:
    def __init__(
        self,
        repository: TelegramGroupRepository,
        work_object_repository: WorkObjectRepository,
        session: AsyncSession,
    ) -> None:
        self.repository = repository
        self.work_object_repository = work_object_repository
        self.session = session

    async def create_telegram_group(self, data: TelegramGroupCreate) -> TelegramGroup:
        name = _required_name(data.name)
        if await self.repository.exists_by_telegram_chat_id(data.telegram_chat_id):
            raise TelegramGroupChatAlreadyExistsError
        await self._require_work_object(data.object_id)

        try:
            group = await self.repository.create(
                telegram_chat_id=data.telegram_chat_id,
                name=name,
                object_id=data.object_id,
                is_active=data.is_active,
            )
            await self.session.commit()
            return group
        except Exception:
            await self.session.rollback()
            raise

    async def get_telegram_group(self, group_id: int) -> TelegramGroup:
        group = await self.repository.get_by_id(group_id)
        if group is None:
            raise TelegramGroupNotFoundError
        return group

    async def list_telegram_groups(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        object_id: int | None = None,
        search: str | None = None,
    ) -> list[TelegramGroup]:
        if offset < 0 or not 1 <= limit <= 100:
            raise ValueError("offset must be >= 0 and limit must be between 1 and 100")
        normalized_search = search.strip() if search is not None else None
        if normalized_search == "":
            normalized_search = None
        return await self.repository.list(
            offset=offset,
            limit=limit,
            is_active=is_active,
            object_id=object_id,
            search=normalized_search,
        )

    async def update_telegram_group(
        self,
        group_id: int,
        data: TelegramGroupUpdate,
    ) -> TelegramGroup:
        group = await self.repository.get_by_id(group_id)
        if group is None:
            raise TelegramGroupNotFoundError

        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return group

        if "name" in changes:
            if changes["name"] is None:
                raise ValueError("name cannot be null")
            changes["name"] = _required_name(str(changes["name"]))

        if "telegram_chat_id" in changes:
            if changes["telegram_chat_id"] is None:
                raise ValueError("telegram_chat_id cannot be null")
            telegram_chat_id = int(changes["telegram_chat_id"])
            changes["telegram_chat_id"] = telegram_chat_id
            if await self.repository.exists_by_telegram_chat_id(
                telegram_chat_id,
                exclude_group_id=group.id,
            ):
                raise TelegramGroupChatAlreadyExistsError

        if "object_id" in changes:
            if changes["object_id"] is None:
                raise ValueError("object_id cannot be null")
            object_id = int(changes["object_id"])
            changes["object_id"] = object_id
            await self._require_work_object(object_id)

        if "is_active" in changes and changes["is_active"] is None:
            raise ValueError("is_active cannot be null")

        try:
            group = await self.repository.update(group, changes)
            await self.session.commit()
            return group
        except Exception:
            await self.session.rollback()
            raise

    async def activate_telegram_group(self, group_id: int) -> TelegramGroup:
        group = await self.get_telegram_group(group_id)
        try:
            group = await self.repository.update(group, {"is_active": True})
            await self.session.commit()
            return group
        except Exception:
            await self.session.rollback()
            raise

    async def deactivate_telegram_group(self, group_id: int) -> TelegramGroup:
        group = await self.get_telegram_group(group_id)
        try:
            group = await self.repository.update(group, {"is_active": False})
            await self.session.commit()
            return group
        except Exception:
            await self.session.rollback()
            raise

    async def _require_work_object(self, object_id: int) -> None:
        work_object = await self.work_object_repository.get_by_id(object_id)
        if work_object is None:
            raise TelegramGroupWorkObjectNotFoundError
