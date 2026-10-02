from fastapi import FastAPI

from app.api.exception_handlers import (
    inactive_user_handler,
    invalid_credentials_handler,
    invalid_token_handler,
    permission_denied_handler,
    user_already_exists_handler,
    user_not_found_handler,
)
from app.api.router import api_router
from app.core.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

app = FastAPI(title="shift-tracker")
app.include_router(api_router)
app.add_exception_handler(UserNotFoundError, user_not_found_handler)
app.add_exception_handler(UserAlreadyExistsError, user_already_exists_handler)
app.add_exception_handler(InvalidCredentialsError, invalid_credentials_handler)
app.add_exception_handler(InvalidTokenError, invalid_token_handler)
app.add_exception_handler(InactiveUserError, inactive_user_handler)
app.add_exception_handler(PermissionDeniedError, permission_denied_handler)
