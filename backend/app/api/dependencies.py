from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.core.exceptions.auth import InactiveUserError, InvalidTokenError, PermissionDeniedError
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.employee import EmployeeRepository
from app.repositories.user import UserRepository
from app.repositories.work_object import WorkObjectRepository
from app.services.auth.jwt import decode_access_token
from app.services.auth.service import AuthService
from app.services.employee import EmployeeService
from app.services.user import UserService
from app.services.work_object import WorkObjectService

bearer_scheme = HTTPBearer()


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


def get_auth_service(
    repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(user_repository=repository)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    repository: UserRepository = Depends(get_user_repository),
) -> User:
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
