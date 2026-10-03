from fastapi import FastAPI

from app.api.exception_handlers import (
    employee_not_found_handler,
    employee_personnel_number_already_exists_handler,
    employee_telegram_user_already_exists_handler,
    inactive_user_handler,
    invalid_credentials_handler,
    invalid_token_handler,
    permission_denied_handler,
    review_confirmation_incomplete_handler,
    shift_already_exists_handler,
    storage_error_handler,
    telegram_group_chat_already_exists_handler,
    telegram_group_not_found_handler,
    telegram_group_work_object_not_found_handler,
    telegram_message_not_found_handler,
    telegram_message_not_in_review_handler,
    telegram_message_photo_not_found_handler,
    user_already_exists_handler,
    user_not_found_handler,
    work_object_already_exists_handler,
    work_object_not_found_handler,
)
from app.api.router import api_router
from app.core.exceptions import (
    EmployeeNotFoundError,
    EmployeePersonnelNumberAlreadyExistsError,
    EmployeeTelegramUserAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
    ReviewConfirmationIncompleteError,
    ShiftAlreadyExistsError,
    StorageError,
    TelegramGroupChatAlreadyExistsError,
    TelegramGroupNotFoundError,
    TelegramGroupWorkObjectNotFoundError,
    TelegramMessageNotFoundError,
    TelegramMessageNotInReviewError,
    TelegramMessagePhotoNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
    WorkObjectAlreadyExistsError,
    WorkObjectNotFoundError,
)

app = FastAPI(title="shift-tracker")
app.include_router(api_router)
app.add_exception_handler(UserNotFoundError, user_not_found_handler)
app.add_exception_handler(UserAlreadyExistsError, user_already_exists_handler)
app.add_exception_handler(InvalidCredentialsError, invalid_credentials_handler)
app.add_exception_handler(InvalidTokenError, invalid_token_handler)
app.add_exception_handler(InactiveUserError, inactive_user_handler)
app.add_exception_handler(PermissionDeniedError, permission_denied_handler)
app.add_exception_handler(EmployeeNotFoundError, employee_not_found_handler)
app.add_exception_handler(
    EmployeePersonnelNumberAlreadyExistsError,
    employee_personnel_number_already_exists_handler,
)
app.add_exception_handler(
    EmployeeTelegramUserAlreadyExistsError,
    employee_telegram_user_already_exists_handler,
)
app.add_exception_handler(WorkObjectNotFoundError, work_object_not_found_handler)
app.add_exception_handler(WorkObjectAlreadyExistsError, work_object_already_exists_handler)
app.add_exception_handler(TelegramGroupNotFoundError, telegram_group_not_found_handler)
app.add_exception_handler(
    TelegramGroupChatAlreadyExistsError,
    telegram_group_chat_already_exists_handler,
)
app.add_exception_handler(
    TelegramGroupWorkObjectNotFoundError,
    telegram_group_work_object_not_found_handler,
)
app.add_exception_handler(TelegramMessageNotFoundError, telegram_message_not_found_handler)
app.add_exception_handler(TelegramMessagePhotoNotFoundError, telegram_message_photo_not_found_handler)
app.add_exception_handler(TelegramMessageNotInReviewError, telegram_message_not_in_review_handler)
app.add_exception_handler(ReviewConfirmationIncompleteError, review_confirmation_incomplete_handler)
app.add_exception_handler(ShiftAlreadyExistsError, shift_already_exists_handler)
app.add_exception_handler(StorageError, storage_error_handler)
