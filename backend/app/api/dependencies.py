from functools import lru_cache

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.exceptions.auth import InactiveUserError, InvalidTokenError, MissingTokenError, PermissionDeniedError
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.employee import EmployeeRepository
from app.repositories.processing_log import ProcessingLogRepository
from app.repositories.shift import ShiftRepository
from app.repositories.telegram_group import TelegramGroupRepository
from app.repositories.telegram_message import TelegramMessageRepository
from app.repositories.user import UserRepository
from app.repositories.work_object import WorkObjectRepository
from app.repositories.dashboard import DashboardRepository
from app.services.dashboard import DashboardService
from app.services.message import MessageService
from app.services.processing_log import ProcessingLogService
from app.services.review import ReviewService
from app.services.shift import ShiftService
from app.services.auth.jwt import decode_access_token
from app.services.auth.service import AuthService
from app.services.employee import EmployeeService
from app.services.storage import ObjectStorage, S3Storage
from app.services.telegram_group import TelegramGroupService
from app.services.telegram_message import TelegramMessageService
from app.services.user import UserService
from app.services.work_object import WorkObjectService

bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    session: AsyncSession = Depends(get_db_session),
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository=repository, session=session)


def get_employee_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EmployeeRepository:
    return EmployeeRepository(session)


def get_employee_service(
    session: AsyncSession = Depends(get_db_session),
    repository: EmployeeRepository = Depends(get_employee_repository),
) -> EmployeeService:
    return EmployeeService(repository=repository, session=session)


def get_work_object_repository(
    session: AsyncSession = Depends(get_db_session),
) -> WorkObjectRepository:
    return WorkObjectRepository(session)


def get_work_object_service(
    session: AsyncSession = Depends(get_db_session),
    repository: WorkObjectRepository = Depends(get_work_object_repository),
) -> WorkObjectService:
    return WorkObjectService(repository=repository, session=session)


def get_telegram_group_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TelegramGroupRepository:
    return TelegramGroupRepository(session)


def get_telegram_group_service(
    session: AsyncSession = Depends(get_db_session),
    repository: TelegramGroupRepository = Depends(get_telegram_group_repository),
    work_object_repository: WorkObjectRepository = Depends(get_work_object_repository),
) -> TelegramGroupService:
    return TelegramGroupService(
        repository=repository,
        work_object_repository=work_object_repository,
        session=session,
    )


def get_telegram_message_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TelegramMessageRepository:
    return TelegramMessageRepository(session)


def get_telegram_message_service(
    session: AsyncSession = Depends(get_db_session),
    repository: TelegramMessageRepository = Depends(get_telegram_message_repository),
) -> TelegramMessageService:
    return TelegramMessageService(repository=repository, session=session)


def get_shift_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ShiftRepository:
    return ShiftRepository(session)


def get_shift_service(
    session: AsyncSession = Depends(get_db_session),
    repository: ShiftRepository = Depends(get_shift_repository),
    employee_repository: EmployeeRepository = Depends(get_employee_repository),
    work_object_repository: WorkObjectRepository = Depends(get_work_object_repository),
    message_repository: TelegramMessageRepository = Depends(get_telegram_message_repository),
    user_repository: UserRepository = Depends(get_user_repository),
) -> ShiftService:
    return ShiftService(
        repository=repository,
        session=session,
        employee_repository=employee_repository,
        work_object_repository=work_object_repository,
        message_repository=message_repository,
        user_repository=user_repository,
    )


def get_processing_log_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ProcessingLogRepository:
    return ProcessingLogRepository(session)


def get_processing_log_service(
    session: AsyncSession = Depends(get_db_session),
    repository: ProcessingLogRepository = Depends(get_processing_log_repository),
    message_repository: TelegramMessageRepository = Depends(get_telegram_message_repository),
) -> ProcessingLogService:
    return ProcessingLogService(
        repository=repository,
        session=session,
        message_repository=message_repository,
    )


@lru_cache
def get_object_storage() -> ObjectStorage:
    current = get_settings()
    return S3Storage(
        endpoint_url=current.s3_endpoint_url,
        access_key=current.s3_access_key,
        secret_key=current.s3_secret_key,
        bucket=current.s3_bucket,
        region=current.s3_region,
        presigned_url_expire_seconds=current.s3_presigned_url_expire_seconds,
        public_endpoint_url=current.s3_public_endpoint_url,
    )


def get_review_service(
    session: AsyncSession = Depends(get_db_session),
    message_repository: TelegramMessageRepository = Depends(get_telegram_message_repository),
    employee_repository: EmployeeRepository = Depends(get_employee_repository),
    work_object_repository: WorkObjectRepository = Depends(get_work_object_repository),
    shift_repository: ShiftRepository = Depends(get_shift_repository),
    processing_log_repository: ProcessingLogRepository = Depends(get_processing_log_repository),
) -> ReviewService:
    return ReviewService(
        session=session,
        message_repository=message_repository,
        employee_repository=employee_repository,
        work_object_repository=work_object_repository,
        shift_repository=shift_repository,
        processing_log_repository=processing_log_repository,
    )


def get_message_service(
    message_repository: TelegramMessageRepository = Depends(get_telegram_message_repository),
    employee_repository: EmployeeRepository = Depends(get_employee_repository),
    work_object_repository: WorkObjectRepository = Depends(get_work_object_repository),
    shift_repository: ShiftRepository = Depends(get_shift_repository),
    storage: ObjectStorage = Depends(get_object_storage),
) -> MessageService:
    return MessageService(
        message_repository=message_repository,
        employee_repository=employee_repository,
        work_object_repository=work_object_repository,
        shift_repository=shift_repository,
        storage=storage,
        presigned_url_expire_seconds=get_settings().s3_presigned_url_expire_seconds,
    )


def get_dashboard_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DashboardRepository:
    return DashboardRepository(session)


def get_dashboard_service(
    repository: DashboardRepository = Depends(get_dashboard_repository),
) -> DashboardService:
    return DashboardService(repository=repository)


def get_auth_service(
    repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(user_repository=repository)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    repository: UserRepository = Depends(get_user_repository),
) -> User:
    if credentials is None or not credentials.credentials:
        raise MissingTokenError
    user_id = decode_access_token(credentials.credentials)
    user = await repository.get_by_id(user_id)
    if user is None:
        raise InvalidTokenError
    if not user.is_active:
        raise InactiveUserError
    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedError
    return current_user


async def require_moderator_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in {UserRole.ADMIN, UserRole.MODERATOR}:
        raise PermissionDeniedError
    return current_user
