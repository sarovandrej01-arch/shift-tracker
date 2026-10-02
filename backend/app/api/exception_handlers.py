from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    EmployeeNotFoundError,
    EmployeePersonnelNumberAlreadyExistsError,
    EmployeeTelegramUserAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
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


async def work_object_already_exists_handler(
    _request: Request,
    _exc: WorkObjectAlreadyExistsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Work object with this name already exists"},
    )
