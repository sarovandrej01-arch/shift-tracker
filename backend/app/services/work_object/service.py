from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.work_object import WorkObjectAlreadyExistsError, WorkObjectNotFoundError
from app.models.work_object import WorkObject
from app.repositories.work_object.repository import WorkObjectRepository
from app.schemas.work_object import WorkObjectCreate, WorkObjectUpdate, validate_timezone


def _required_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("name must not be empty")
    return normalized


def _non_negative(value: int, field: str) -> int:
    if value < 0:
        raise ValueError(f"{field} must be >= 0")
    return value


class WorkObjectService:
    def __init__(self, repository: WorkObjectRepository, session: AsyncSession) -> None:
        self.repository = repository
        self.session = session

    async def create_work_object(self, data: WorkObjectCreate) -> WorkObject:
        name = _required_name(data.name)
        timezone = validate_timezone(data.timezone)
        checkin_before_minutes = _non_negative(data.checkin_before_minutes, "checkin_before_minutes")
        checkin_after_minutes = _non_negative(data.checkin_after_minutes, "checkin_after_minutes")

        if await self.repository.exists_by_name(name):
            raise WorkObjectAlreadyExistsError

        try:
            work_object = await self.repository.create(
                name=name,
                shift_start_time=data.shift_start_time,
                checkin_before_minutes=checkin_before_minutes,
                checkin_after_minutes=checkin_after_minutes,
                timezone=timezone,
                is_active=data.is_active,
            )
            await self.session.commit()
            return work_object
        except Exception:
            await self.session.rollback()
            raise

    async def get_work_object(self, object_id: int) -> WorkObject:
        work_object = await self.repository.get_by_id(object_id)
        if work_object is None:
            raise WorkObjectNotFoundError
        return work_object

    async def list_work_objects(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[WorkObject]:
        if offset < 0 or not 1 <= limit <= 100:
            raise ValueError("offset must be >= 0 and limit must be between 1 and 100")
        normalized_search = search.strip() if search is not None else None
        if normalized_search == "":
            normalized_search = None
        return await self.repository.list(
            offset=offset,
            limit=limit,
            is_active=is_active,
            search=normalized_search,
        )

    async def update_work_object(self, object_id: int, data: WorkObjectUpdate) -> WorkObject:
        work_object = await self.repository.get_by_id(object_id)
        if work_object is None:
            raise WorkObjectNotFoundError

        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return work_object

        if "name" in changes:
            if changes["name"] is None:
                raise ValueError("name cannot be null")
            name = _required_name(str(changes["name"]))
            changes["name"] = name
            if await self.repository.exists_by_name(name, exclude_object_id=work_object.id):
                raise WorkObjectAlreadyExistsError

        if "timezone" in changes:
            if changes["timezone"] is None:
                raise ValueError("timezone cannot be null")
            changes["timezone"] = validate_timezone(str(changes["timezone"]))

        if "checkin_before_minutes" in changes:
            if changes["checkin_before_minutes"] is None:
                raise ValueError("checkin_before_minutes cannot be null")
            changes["checkin_before_minutes"] = _non_negative(
                int(changes["checkin_before_minutes"]),
                "checkin_before_minutes",
            )

        if "checkin_after_minutes" in changes:
            if changes["checkin_after_minutes"] is None:
                raise ValueError("checkin_after_minutes cannot be null")
            changes["checkin_after_minutes"] = _non_negative(
                int(changes["checkin_after_minutes"]),
                "checkin_after_minutes",
            )

        if "shift_start_time" in changes and changes["shift_start_time"] is None:
            raise ValueError("shift_start_time cannot be null")

        if "is_active" in changes and changes["is_active"] is None:
            raise ValueError("is_active cannot be null")

        try:
            work_object = await self.repository.update(work_object, changes)
            await self.session.commit()
            return work_object
        except Exception:
            await self.session.rollback()
            raise

    async def activate_work_object(self, object_id: int) -> WorkObject:
        work_object = await self.get_work_object(object_id)
        try:
            work_object = await self.repository.update(work_object, {"is_active": True})
            await self.session.commit()
            return work_object
        except Exception:
            await self.session.rollback()
            raise

    async def deactivate_work_object(self, object_id: int) -> WorkObject:
        work_object = await self.get_work_object(object_id)
        try:
            work_object = await self.repository.update(work_object, {"is_active": False})
            await self.session.commit()
            return work_object
        except Exception:
            await self.session.rollback()
            raise
