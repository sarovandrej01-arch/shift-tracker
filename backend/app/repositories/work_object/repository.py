from datetime import time

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.work_object import WorkObject

_UPDATABLE_FIELDS = frozenset(
    {
        "name",
        "shift_start_time",
        "checkin_before_minutes",
        "checkin_after_minutes",
        "timezone",
        "is_active",
    }
)


class WorkObjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, object_id: int) -> WorkObject | None:
        stmt = select(WorkObject).where(WorkObject.id == object_id)
        return await self.session.scalar(stmt)

    async def get_by_name(self, name: str) -> WorkObject | None:
        stmt = select(WorkObject).where(func.lower(WorkObject.name) == name.strip().lower())
        return await self.session.scalar(stmt)

    async def exists_by_name(
        self,
        name: str,
        *,
        exclude_object_id: int | None = None,
    ) -> bool:
        stmt = select(WorkObject.id).where(func.lower(WorkObject.name) == name.strip().lower())
        if exclude_object_id is not None:
            stmt = stmt.where(WorkObject.id != exclude_object_id)
        return await self.session.scalar(stmt) is not None

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[WorkObject]:
        stmt = select(WorkObject)
        if is_active is not None:
            stmt = stmt.where(WorkObject.is_active == is_active)
        if search is not None and search.strip():
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    WorkObject.name.ilike(pattern),
                    WorkObject.timezone.ilike(pattern),
                )
            )
        stmt = stmt.order_by(WorkObject.id).offset(offset).limit(limit)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        *,
        name: str,
        shift_start_time: time,
        checkin_before_minutes: int,
        checkin_after_minutes: int,
        timezone: str,
        is_active: bool = True,
    ) -> WorkObject:
        work_object = WorkObject(
            name=name,
            shift_start_time=shift_start_time,
            checkin_before_minutes=checkin_before_minutes,
            checkin_after_minutes=checkin_after_minutes,
            timezone=timezone,
            is_active=is_active,
        )
        self.session.add(work_object)
        await self.session.flush()
        await self.session.refresh(work_object)
        return work_object

    async def update(self, work_object: WorkObject, changes: dict[str, object]) -> WorkObject:
        for field, value in changes.items():
            if field in _UPDATABLE_FIELDS:
                setattr(work_object, field, value)
        await self.session.flush()
        await self.session.refresh(work_object)
        return work_object
