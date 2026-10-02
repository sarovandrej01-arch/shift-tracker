from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.employee import (
    EmployeeNotFoundError,
    EmployeePersonnelNumberAlreadyExistsError,
    EmployeeTelegramUserAlreadyExistsError,
)
from app.models.employee import Employee
from app.repositories.employee.repository import EmployeeRepository
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


def _required_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("value must not be empty")
    return normalized


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class EmployeeService:
    def __init__(self, repository: EmployeeRepository, session: AsyncSession) -> None:
        self.repository = repository
        self.session = session

    async def create_employee(self, data: EmployeeCreate) -> Employee:
        full_name = _required_text(data.full_name)
        personnel_number = _required_text(data.personnel_number)
        telegram_username = _optional_text(data.telegram_username)
        callsign = _optional_text(data.callsign)

        if await self.repository.exists_by_personnel_number(personnel_number):
            raise EmployeePersonnelNumberAlreadyExistsError
        if data.telegram_user_id is not None and await self.repository.exists_by_telegram_user_id(
            data.telegram_user_id
        ):
            raise EmployeeTelegramUserAlreadyExistsError

        employee = await self.repository.create(
            full_name=full_name,
            personnel_number=personnel_number,
            telegram_user_id=data.telegram_user_id,
            telegram_username=telegram_username,
            callsign=callsign,
            is_active=data.is_active,
        )
        await self._commit()
        return employee

    async def get_employee(self, employee_id: int) -> Employee:
        employee = await self.repository.get_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError
        return employee

    async def list_employees(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[Employee]:
        if offset < 0 or not 1 <= limit <= 100:
            raise ValueError("offset must be >= 0 and limit must be between 1 and 100")
        normalized_search = _optional_text(search)
        return await self.repository.list(
            offset=offset,
            limit=limit,
            is_active=is_active,
            search=normalized_search,
        )

    async def update_employee(self, employee_id: int, data: EmployeeUpdate) -> Employee:
        employee = await self.repository.get_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError

        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return employee

        if "full_name" in changes:
            if changes["full_name"] is None:
                raise ValueError("full_name cannot be null")
            changes["full_name"] = _required_text(str(changes["full_name"]))

        if "personnel_number" in changes:
            if changes["personnel_number"] is None:
                raise ValueError("personnel_number cannot be null")
            personnel_number = _required_text(str(changes["personnel_number"]))
            changes["personnel_number"] = personnel_number
            if await self.repository.exists_by_personnel_number(
                personnel_number,
                exclude_employee_id=employee.id,
            ):
                raise EmployeePersonnelNumberAlreadyExistsError

        if "telegram_username" in changes:
            raw_username = changes["telegram_username"]
            changes["telegram_username"] = _optional_text(
                None if raw_username is None else str(raw_username)
            )

        if "callsign" in changes:
            raw_callsign = changes["callsign"]
            changes["callsign"] = _optional_text(None if raw_callsign is None else str(raw_callsign))

        if "telegram_user_id" in changes and changes["telegram_user_id"] is not None:
            telegram_user_id = int(changes["telegram_user_id"])
            changes["telegram_user_id"] = telegram_user_id
            if await self.repository.exists_by_telegram_user_id(
                telegram_user_id,
                exclude_employee_id=employee.id,
            ):
                raise EmployeeTelegramUserAlreadyExistsError

        employee = await self.repository.update(employee, changes)
        await self._commit()
        return employee

    async def activate_employee(self, employee_id: int) -> Employee:
        employee = await self.get_employee(employee_id)
        employee = await self.repository.update(employee, {"is_active": True})
        await self._commit()
        return employee

    async def deactivate_employee(self, employee_id: int) -> Employee:
        employee = await self.get_employee(employee_id)
        employee = await self.repository.update(employee, {"is_active": False})
        await self._commit()
        return employee

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
