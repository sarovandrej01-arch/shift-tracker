from dataclasses import dataclass
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.shift import ShiftAlreadyExistsError, ShiftNotFoundError
from app.core.query_validation import ensure_date_order
from app.models.employee import Employee
from app.models.shift import Shift
from app.models.telegram_message import TelegramMessage
from app.models.user import User
from app.models.work_object import WorkObject
from app.repositories.employee.repository import EmployeeRepository
from app.repositories.shift.repository import ShiftRepository
from app.repositories.telegram_message.repository import TelegramMessageRepository
from app.repositories.user.repository import UserRepository
from app.repositories.work_object.repository import WorkObjectRepository


@dataclass(slots=True)
class ShiftDetail:
    shift: Shift
    employee: Employee | None
    work_object: WorkObject | None
    source_message: TelegramMessage | None
    confirmed_by_user: User | None


class ShiftService:
    def __init__(
        self,
        repository: ShiftRepository,
        session: AsyncSession,
        *,
        employee_repository: EmployeeRepository | None = None,
        work_object_repository: WorkObjectRepository | None = None,
        message_repository: TelegramMessageRepository | None = None,
        user_repository: UserRepository | None = None,
    ) -> None:
        self.repository = repository
        self.session = session
        self.employee_repository = employee_repository
        self.work_object_repository = work_object_repository
        self.message_repository = message_repository
        self.user_repository = user_repository

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

    async def get_shift_detail(self, shift_id: int) -> ShiftDetail:
        shift = await self.get_shift(shift_id)
        employee = None
        if self.employee_repository is not None:
            employee = await self.employee_repository.get_by_id(shift.employee_id)
        work_object = None
        if self.work_object_repository is not None:
            work_object = await self.work_object_repository.get_by_id(shift.object_id)
        source_message = None
        if shift.source_message_id is not None and self.message_repository is not None:
            source_message = await self.message_repository.get_by_id(shift.source_message_id)
        confirmed_by_user = None
        if shift.confirmed_by_user_id is not None and self.user_repository is not None:
            confirmed_by_user = await self.user_repository.get_by_id(shift.confirmed_by_user_id)
        return ShiftDetail(
            shift=shift,
            employee=employee,
            work_object=work_object,
            source_message=source_message,
            confirmed_by_user=confirmed_by_user,
        )

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
        ensure_date_order(date_from, date_to)
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
