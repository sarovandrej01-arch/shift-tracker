from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.core.exceptions.user import UserAlreadyExistsError, UserNotFoundError
from app.models.user import User
from app.repositories.user.repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.services.user.password import hash_password


class UserService:
    def __init__(self, repository: UserRepository, session: AsyncSession) -> None:
        self.repository = repository
        self.session = session

    async def create_user(self, data: UserCreate) -> User:
        email = data.email.strip().lower()
        if await self.repository.exists_by_email(email):
            raise UserAlreadyExistsError

        user = await self.repository.create(
            email=email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role,
            is_active=data.is_active,
        )
        await self._commit()
        return user

    async def get_user(self, user_id: int) -> User:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError
        return user

    async def get_user_by_email(self, email: str) -> User:
        user = await self.repository.get_by_email(email.strip().lower())
        if user is None:
            raise UserNotFoundError
        return user

    async def list_users(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        role: UserRole | None = None,
    ) -> list[User]:
        if offset < 0 or not 1 <= limit <= 100:
            raise ValueError("offset must be >= 0 and limit must be between 1 and 100")
        return await self.repository.list(
            offset=offset,
            limit=limit,
            is_active=is_active,
            role=role,
        )

    async def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError

        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return user

        if "email" in changes and changes["email"] is not None:
            email = str(changes["email"]).strip().lower()
            changes["email"] = email
            if await self.repository.exists_by_email(email, exclude_user_id=user.id):
                raise UserAlreadyExistsError

        if "password" in changes:
            password = changes.pop("password")
            if password is not None:
                changes["hashed_password"] = hash_password(str(password))

        user = await self.repository.update(user, changes)
        await self._commit()
        return user

    async def deactivate_user(self, user_id: int) -> User:
        user = await self.get_user(user_id)
        user = await self.repository.update(user, {"is_active": False})
        await self._commit()
        return user

    async def activate_user(self, user_id: int) -> User:
        user = await self.get_user(user_id)
        user = await self.repository.update(user, {"is_active": True})
        await self._commit()
        return user

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
