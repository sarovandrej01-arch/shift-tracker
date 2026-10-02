from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee

_UPDATABLE_FIELDS = frozenset(
    {
        "full_name",
        "personnel_number",
        "telegram_user_id",
        "telegram_username",
        "callsign",
        "is_active",
    }
)


class EmployeeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, employee_id: int) -> Employee | None:
        stmt = select(Employee).where(Employee.id == employee_id)
        return await self.session.scalar(stmt)

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> Employee | None:
        stmt = select(Employee).where(Employee.telegram_user_id == telegram_user_id)
        return await self.session.scalar(stmt)

    async def get_by_personnel_number(self, personnel_number: str) -> Employee | None:
        stmt = select(Employee).where(Employee.personnel_number == personnel_number.strip())
        return await self.session.scalar(stmt)

    async def get_by_callsign(self, callsign: str) -> list[Employee]:
        normalized = callsign.strip().lower()
        stmt = select(Employee).where(
            Employee.callsign.is_not(None),
            func.lower(Employee.callsign) == normalized,
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def find_by_full_name(self, full_name: str) -> list[Employee]:
        normalized = full_name.strip().lower()
        stmt = select(Employee).where(func.lower(Employee.full_name) == normalized)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def exists_by_personnel_number(
        self,
        personnel_number: str,
        *,
        exclude_employee_id: int | None = None,
    ) -> bool:
        stmt = select(Employee.id).where(Employee.personnel_number == personnel_number.strip())
        if exclude_employee_id is not None:
            stmt = stmt.where(Employee.id != exclude_employee_id)
        return await self.session.scalar(stmt) is not None

    async def exists_by_telegram_user_id(
        self,
        telegram_user_id: int,
        *,
        exclude_employee_id: int | None = None,
    ) -> bool:
        stmt = select(Employee.id).where(Employee.telegram_user_id == telegram_user_id)
        if exclude_employee_id is not None:
            stmt = stmt.where(Employee.id != exclude_employee_id)
        return await self.session.scalar(stmt) is not None

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[Employee]:
        stmt = select(Employee)
        if is_active is not None:
            stmt = stmt.where(Employee.is_active == is_active)
        if search is not None and search.strip():
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Employee.full_name.ilike(pattern),
                    Employee.personnel_number.ilike(pattern),
                    Employee.telegram_username.ilike(pattern),
                    Employee.callsign.ilike(pattern),
                )
            )
        stmt = stmt.order_by(Employee.id).offset(offset).limit(limit)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        *,
        full_name: str,
        personnel_number: str,
        telegram_user_id: int | None,
        telegram_username: str | None,
        callsign: str | None,
        is_active: bool = True,
    ) -> Employee:
        employee = Employee(
            full_name=full_name,
            personnel_number=personnel_number,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            callsign=callsign,
            is_active=is_active,
        )
        self.session.add(employee)
        await self.session.flush()
        await self.session.refresh(employee)
        return employee

    async def update(self, employee: Employee, changes: dict[str, object]) -> Employee:
        for field, value in changes.items():
            if field in _UPDATABLE_FIELDS:
                setattr(employee, field, value)
        await self.session.flush()
        await self.session.refresh(employee)
        return employee
