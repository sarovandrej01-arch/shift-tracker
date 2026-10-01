from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.models.user import User

_UPDATABLE_FIELDS = frozenset({"email", "full_name", "hashed_password", "role", "is_active"})


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.lower())
        return await self.session.scalar(stmt)

    async def exists_by_email(
        self,
        email: str,
        *,
        exclude_user_id: int | None = None,
    ) -> bool:
        stmt = select(User.id).where(func.lower(User.email) == email.lower())
        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)
        return await self.session.scalar(stmt) is not None

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        role: UserRole | None = None,
    ) -> list[User]:
        stmt = select(User).order_by(User.id).offset(offset).limit(limit)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        if role is not None:
            stmt = stmt.where(User.role == role)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        *,
        email: str,
        full_name: str,
        hashed_password: str,
        role: UserRole,
        is_active: bool = True,
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            is_active=is_active,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User, changes: dict[str, object]) -> User:
        for field, value in changes.items():
            if field in _UPDATABLE_FIELDS:
                setattr(user, field, value)
        await self.session.flush()
        await self.session.refresh(user)
        return user
