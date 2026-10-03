from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    EmployeeNotFoundError,
    EmployeePersonnelNumberAlreadyExistsError,
    EmployeeTelegramUserAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidDateRangeError,
    InvalidTokenError,
    MissingTokenError,
    PermissionDeniedError,
    ReviewConfirmationIncompleteError,
    ShiftAlreadyExistsError,
    ShiftNotFoundError,
    StorageError,
    TelegramGroupChatAlreadyExistsError,
    TelegramGroupNotFoundError,
    TelegramGroupWorkObjectNotFoundError,
    TelegramMessageNotFoundError,
    TelegramMessageNotInReviewError,
    TelegramMessagePhotoNotFoundError,
    CannotModifyOwnAdminAccessError,
    LastActiveAdminError,
    UserAlreadyExistsError,
    UserNotFoundError,
    WorkObjectAlreadyExistsError,
    WorkObjectNotFoundError,
)

_BEARER_HEADER = {"WWW-Authenticate": "Bearer"}


async def user_not_found_handler(_request: Request, _exc: UserNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "User not found"})


async def user_already_exists_handler(
    _request: Request,
    _exc: UserAlreadyExistsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "User with this email already exists"},
    )


async def cannot_modify_own_admin_access_handler(
    _request: Request,
    _exc: CannotModifyOwnAdminAccessError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "You cannot remove your own administrator access"},
    )


async def last_active_admin_handler(
    _request: Request,
    _exc: LastActiveAdminError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Cannot remove the last active administrator"},
    )


async def invalid_credentials_handler(
    _request: Request,
    _exc: InvalidCredentialsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid credentials"},
        headers=_BEARER_HEADER,
    )


async def invalid_token_handler(_request: Request, _exc: InvalidTokenError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid or expired token"},
        headers=_BEARER_HEADER,
    )


async def missing_token_handler(_request: Request, _exc: MissingTokenError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": "Not authenticated"},
        headers=_BEARER_HEADER,
    )


async def inactive_user_handler(_request: Request, _exc: InactiveUserError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": "User is inactive"})


async def permission_denied_handler(
    _request: Request,
    _exc: PermissionDeniedError,
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": "Permission denied"})


async def employee_not_found_handler(
    _request: Request,
    _exc: EmployeeNotFoundError,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Employee not found"})


async def employee_personnel_number_already_exists_handler(
    _request: Request,
    _exc: EmployeePersonnelNumberAlreadyExistsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Employee with this personnel number already exists"},
    )


async def employee_telegram_user_already_exists_handler(
    _request: Request,
    _exc: EmployeeTelegramUserAlreadyExistsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Employee with this Telegram user ID already exists"},
    )


async def work_object_not_found_handler(
    _request: Request,
    _exc: WorkObjectNotFoundError,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Work object not found"})


async def telegram_group_not_found_handler(
    _request: Request,
    _exc: TelegramGroupNotFoundError,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Telegram group not found"})


async def telegram_group_chat_already_exists_handler(
    _request: Request,
    _exc: TelegramGroupChatAlreadyExistsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Telegram group with this chat ID already exists"},
    )


async def telegram_group_work_object_not_found_handler(
    _request: Request,
    _exc: TelegramGroupWorkObjectNotFoundError,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Work object not found"})


async def work_object_already_exists_handler(
    _request: Request,
    _exc: WorkObjectAlreadyExistsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Work object with this name already exists"},
    )


async def telegram_message_not_found_handler(
    _request: Request,
    _exc: TelegramMessageNotFoundError,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Telegram message not found"})


async def telegram_message_photo_not_found_handler(
    _request: Request,
    _exc: TelegramMessagePhotoNotFoundError,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Telegram message photo not found"})


async def telegram_message_not_in_review_handler(
    _request: Request,
    _exc: TelegramMessageNotInReviewError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Telegram message is not in review"},
    )


async def review_confirmation_incomplete_handler(
    _request: Request,
    exc: ReviewConfirmationIncompleteError,
) -> JSONResponse:
    missing = ", ".join(exc.missing_fields)
    return JSONResponse(
        status_code=422,
        content={"detail": f"Missing confirmation data: {missing}"},
    )


async def shift_already_exists_handler(
    _request: Request,
    _exc: ShiftAlreadyExistsError,
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": "Shift already exists"})


async def shift_not_found_handler(_request: Request, _exc: ShiftNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Shift not found"})


async def invalid_date_range_handler(
    _request: Request,
    exc: InvalidDateRangeError,
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.detail})


async def storage_error_handler(_request: Request, _exc: StorageError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": "Photo storage is unavailable"})
