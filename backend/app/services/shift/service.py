from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.shift import ShiftAlreadyExistsError, ShiftNotFoundError
from app.models.shift import Shift
from app.repositories.shift.repository import ShiftRepository


class ShiftService:
    def __init__(self, repository: ShiftRepository, session: AsyncSession) -> None:
        self.repository = repository
        self.session = session

    async def create_shift(
        self,
        *,
        employee_id: int,
        object_id: int,
        shift_date: date,
        source_message_id: int | None = None,
        confirmed_manually: bool = False,
        confirmed_by_user_id: int | None = None,
    ) -> Shift:
        existing = await self.repository.get_existing_shift(
            employee_id=employee_id,
            object_id=object_id,
            shift_date=shift_date,
        )
        if existing is not None:
            raise ShiftAlreadyExistsError

        try:
            shift = await self.repository.create(
                employee_id=employee_id,
                object_id=object_id,
                shift_date=shift_date,
                source_message_id=source_message_id,
                confirmed_manually=confirmed_manually,
                confirmed_by_user_id=confirmed_by_user_id,
            )
            await self.session.commit()
            return shift
        except Exception:
            await self.session.rollback()
            raise

    async def get_shift(self, shift_id: int) -> Shift:
        shift = await self.repository.get_by_id(shift_id)
        if shift is None:
            raise ShiftNotFoundError
        return shift

    async def get_existing_shift(
        self,
        employee_id: int,
        object_id: int,
        shift_date: date,
    ) -> Shift | None:
        return await self.repository.get_existing_shift(
            employee_id=employee_id,
            object_id=object_id,
            shift_date=shift_date,
        )

    async def list_shifts(
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
        if offset < 0 or not 1 <= limit <= 100:
            raise ValueError("offset must be >= 0 and limit must be between 1 and 100")
        if date_from is not None and date_to is not None and date_from > date_to:
            raise ValueError("date_from must be less than or equal to date_to")
        return await self.repository.list(
            offset=offset,
            limit=limit,
            employee_id=employee_id,
            object_id=object_id,
            date_from=date_from,
            date_to=date_to,
            confirmed_manually=confirmed_manually,
        )

    async def mark_manual_confirmation(self, shift_id: int, user_id: int) -> Shift:
        shift = await self.repository.get_by_id(shift_id)
        if shift is None:
            raise ShiftNotFoundError
        try:
            shift = await self.repository.mark_manual_confirmation(shift, user_id)
            await self.session.commit()
            return shift
        except Exception:
            await self.session.rollback()
            raise
