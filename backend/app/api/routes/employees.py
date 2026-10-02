from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    get_employee_service,
    require_admin,
    require_moderator_or_admin,
)
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.services.employee import EmployeeService

router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
async def create_employee(
    data: EmployeeCreate,
    _: User = Depends(require_admin),
    service: EmployeeService = Depends(get_employee_service),
) -> Employee:
    return await service.create_employee(data)


@router.get("", response_model=list[EmployeeRead])
async def list_employees(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    _: User = Depends(require_moderator_or_admin),
    service: EmployeeService = Depends(get_employee_service),
) -> list[Employee]:
    return await service.list_employees(
        offset=offset,
        limit=limit,
        is_active=is_active,
        search=search,
    )


@router.get("/{employee_id}", response_model=EmployeeRead)
async def get_employee(
    employee_id: int,
    _: User = Depends(require_moderator_or_admin),
    service: EmployeeService = Depends(get_employee_service),
) -> Employee:
    return await service.get_employee(employee_id)


@router.patch("/{employee_id}", response_model=EmployeeRead)
async def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    _: User = Depends(require_admin),
    service: EmployeeService = Depends(get_employee_service),
) -> Employee:
    return await service.update_employee(employee_id, data)


@router.post("/{employee_id}/activate", response_model=EmployeeRead)
async def activate_employee(
    employee_id: int,
    _: User = Depends(require_admin),
    service: EmployeeService = Depends(get_employee_service),
) -> Employee:
    return await service.activate_employee(employee_id)


@router.post("/{employee_id}/deactivate", response_model=EmployeeRead)
async def deactivate_employee(
    employee_id: int,
    _: User = Depends(require_admin),
    service: EmployeeService = Depends(get_employee_service),
) -> Employee:
    return await service.deactivate_employee(employee_id)
