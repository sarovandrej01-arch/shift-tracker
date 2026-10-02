from fastapi import FastAPI

from app.api.exception_handlers import user_already_exists_handler, user_not_found_handler
from app.api.router import api_router
from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError

app = FastAPI(title="shift-tracker")
app.include_router(api_router)
app.add_exception_handler(UserNotFoundError, user_not_found_handler)
app.add_exception_handler(UserAlreadyExistsError, user_already_exists_handler)
