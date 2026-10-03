from app.core.exceptions.auth import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    MissingTokenError,
    PermissionDeniedError,
)
from app.core.exceptions.employee import (
    EmployeeNotFoundError,
    EmployeePersonnelNumberAlreadyExistsError,
    EmployeeTelegramUserAlreadyExistsError,
)
from app.core.exceptions.processing_log import ProcessingLogNotFoundError
from app.core.exceptions.query import InvalidDateRangeError
from app.core.exceptions.review import ReviewConfirmationIncompleteError
from app.core.exceptions.shift import ShiftAlreadyExistsError, ShiftNotFoundError
from app.core.exceptions.storage import StorageConfigurationError, StorageError
from app.core.exceptions.telegram_message import (
    TelegramMessageAlreadyExistsError,
    TelegramMessageNotFoundError,
    TelegramMessageNotInReviewError,
    TelegramMessagePhotoNotFoundError,
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
    "InvalidDateRangeError",
    "InvalidTokenError",
    "MissingTokenError",
    "InvalidUserPasswordError",
    "PermissionDeniedError",
    "ProcessingLogNotFoundError",
    "ReviewConfirmationIncompleteError",
    "ShiftAlreadyExistsError",
    "ShiftNotFoundError",
    "StorageConfigurationError",
    "StorageError",
    "TelegramGroupChatAlreadyExistsError",
    "TelegramMessageAlreadyExistsError",
    "TelegramMessageNotFoundError",
    "TelegramMessageNotInReviewError",
    "TelegramMessagePhotoNotFoundError",
    "TelegramGroupNotFoundError",
    "TelegramGroupWorkObjectNotFoundError",
    "UserAlreadyExistsError",
    "UserNotFoundError",
    "WorkObjectAlreadyExistsError",
    "WorkObjectNotFoundError",
]
