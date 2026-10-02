from app.core.exceptions.auth import InactiveUserError, InvalidCredentialsError
from app.models.user import User
from app.repositories.user.repository import UserRepository
from app.services.auth.jwt import create_access_token
from app.services.user.password import verify_password


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self.user_repository.get_by_email(email.strip().lower())
        if user is None:
            raise InvalidCredentialsError

        try:
            password_matches = verify_password(password, user.hashed_password)
        except Exception:
            password_matches = False
        if not password_matches:
            raise InvalidCredentialsError

        if not user.is_active:
            raise InactiveUserError
        return user

    async def login(self, email: str, password: str) -> str:
        user = await self.authenticate_user(email, password)
        return create_access_token(user.id)
