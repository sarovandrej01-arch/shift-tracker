from app.core.exceptions.auth import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
)
from app.core.exceptions.employee import (
    EmployeeNotFoundError,
    EmployeePersonnelNumberAlreadyExistsError,
    EmployeeTelegramUserAlreadyExistsError,
)
from app.core.exceptions.telegram_message import (
    TelegramMessageAlreadyExistsError,
    TelegramMessageNotFoundError,
)
from app.core.exceptions.telegram_group import (
    TelegramGroupChatAlreadyExistsError,
    TelegramGroupNotFoundError,
    TelegramGroupWorkObjectNotFoundError,
)
from app.core.exceptions.user import InvalidUserPasswordError, UserAlreadyExistsError, UserNotFoundError
from app.core.exceptions.work_object import WorkObjectAlreadyExistsError, WorkObjectNotFoundError

__all__ = [
    "EmployeeNotFoundError",
    "EmployeePersonnelNumberAlreadyExistsError",
    "EmployeeTelegramUserAlreadyExistsError",
    "InactiveUserError",
    "InvalidCredentialsError",
    "InvalidTokenError",
    "InvalidUserPasswordError",
    "PermissionDeniedError",
    "TelegramGroupChatAlreadyExistsError",
    "TelegramMessageAlreadyExistsError",
    "TelegramMessageNotFoundError",
    "TelegramGroupNotFoundError",
    "TelegramGroupWorkObjectNotFoundError",
    "UserAlreadyExistsError",
    "UserNotFoundError",
    "WorkObjectAlreadyExistsError",
    "WorkObjectNotFoundError",
]
