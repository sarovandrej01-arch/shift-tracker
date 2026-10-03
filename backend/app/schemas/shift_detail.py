from app.schemas.employee import EmployeeRead
from app.schemas.shift import ShiftRead
from app.schemas.telegram_message import TelegramMessageRead
from app.schemas.user import UserRead
from app.schemas.work_object import WorkObjectRead


class ShiftDetailRead(ShiftRead):
    employee: EmployeeRead | None = None
    work_object: WorkObjectRead | None = None
    source_message: TelegramMessageRead | None = None
    confirmed_by_user: UserRead | None = None
