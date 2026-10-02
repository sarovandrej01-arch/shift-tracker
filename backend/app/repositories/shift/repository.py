from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift import Shift


class ShiftRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, shift_id: int) -> Shift | None:
        stmt = select(Shift).where(Shift.id == shift_id)
        return await self.session.scalar(stmt)

    async def get_existing_shift(
        self,
        employee_id: int,
        object_id: int,
        shift_date: date,
    ) -> Shift | None:
        stmt = select(Shift).where(
            Shift.employee_id == employee_id,
            Shift.object_id == object_id,
            Shift.shift_date == shift_date,
        )
        return await self.session.scalar(stmt)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        employee_id: int | None = None,
        object_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        confirmed_manually: bool | None = None,
    ) -> list[Shift]:
        stmt = select(Shift)
        if employee_id is not None:
            stmt = stmt.where(Shift.employee_id == employee_id)
        if object_id is not None:
            stmt = stmt.where(Shift.object_id == object_id)
        if date_from is not None:
            stmt = stmt.where(Shift.shift_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Shift.shift_date <= date_to)
        if confirmed_manually is not None:
            stmt = stmt.where(Shift.confirmed_manually == confirmed_manually)
        stmt = stmt.order_by(Shift.shift_date.desc(), Shift.id.desc()).offset(offset).limit(limit)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        *,
        employee_id: int,
        object_id: int,
        shift_date: date,
        source_message_id: int | None = None,
        confirmed_manually: bool = False,
        confirmed_by_user_id: int | None = None,
    ) -> Shift:
        shift = Shift(
            employee_id=employee_id,
            object_id=object_id,
            shift_date=shift_date,
            source_message_id=source_message_id,
            confirmed_manually=confirmed_manually,
            confirmed_by_user_id=confirmed_by_user_id,
        )
        self.session.add(shift)
        await self.session.flush()
        await self.session.refresh(shift)
        return shift

    async def mark_manual_confirmation(self, shift: Shift, user_id: int) -> Shift:
        shift.confirmed_manually = True
        shift.confirmed_by_user_id = user_id
        await self.session.flush()
        await self.session.refresh(shift)
        return shift
