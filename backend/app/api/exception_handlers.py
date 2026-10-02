from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
    UserAlreadyExistsError,
    UserNotFoundError,
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
