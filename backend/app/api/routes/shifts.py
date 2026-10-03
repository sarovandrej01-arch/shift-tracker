from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_shift_service, require_moderator_or_admin
from app.models.shift import Shift
from app.models.user import User
from app.schemas.employee import EmployeeRead
from app.schemas.shift import ShiftRead
from app.schemas.shift_detail import ShiftDetailRead
from app.schemas.telegram_message import TelegramMessageRead
from app.schemas.user import UserRead
from app.schemas.work_object import WorkObjectRead
from app.services.shift import ShiftDetail, ShiftService

router = APIRouter(prefix="/shifts", tags=["shifts"])


def _detail_response(detail: ShiftDetail) -> ShiftDetailRead:
    return ShiftDetailRead(
        **ShiftRead.model_validate(detail.shift).model_dump(),
        employee=EmployeeRead.model_validate(detail.employee) if detail.employee is not None else None,
        work_object=WorkObjectRead.model_validate(detail.work_object) if detail.work_object is not None else None,
        source_message=(
            TelegramMessageRead.model_validate(detail.source_message)
            if detail.source_message is not None
            else None
        ),
        confirmed_by_user=(
            UserRead.model_validate(detail.confirmed_by_user)
            if detail.confirmed_by_user is not None
            else None
        ),
    )


@router.get("", response_model=list[ShiftRead])
async def list_shifts(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    employee_id: int | None = Query(default=None),
    object_id: int | None = Query(default=None),
    date_from: date | None = Query(default=None, description="Inclusive lower bound for shift_date"),
    date_to: date | None = Query(default=None, description="Inclusive upper bound for shift_date"),
    confirmed_manually: bool | None = Query(default=None),
    _: User = Depends(require_moderator_or_admin),
    service: ShiftService = Depends(get_shift_service),
) -> list[Shift]:
    return await service.list_shifts(
        offset=offset,
        limit=limit,
        employee_id=employee_id,
        object_id=object_id,
        date_from=date_from,
        date_to=date_to,
        confirmed_manually=confirmed_manually,
    )


@router.get("/{shift_id}", response_model=ShiftDetailRead)
async def get_shift(
    shift_id: int,
    _: User = Depends(require_moderator_or_admin),
    service: ShiftService = Depends(get_shift_service),
) -> ShiftDetailRead:
    return _detail_response(await service.get_shift_detail(shift_id))
