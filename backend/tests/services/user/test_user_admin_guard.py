import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.core.enums import UserRole
from app.core.exceptions import CannotModifyOwnAdminAccessError, LastActiveAdminError
from app.scripts.create_admin import build_admin_create
from app.schemas.user import UserUpdate
from app.services.user.service import UserService


class FakeUsers:
    def __init__(self, user: SimpleNamespace, active_admins: int = 1) -> None:
        self.user = user
        self.active_admins = active_admins
        self.updated: dict[str, object] | None = None

    async def get_by_id(self, user_id: int) -> SimpleNamespace | None:
        if self.user.id != user_id:
            return None
        return self.user

    async def exists_by_email(self, email: str, *, exclude_user_id: int | None = None) -> bool:
        return False

    async def count_active_admins(self) -> int:
        return self.active_admins

    async def update(self, user: SimpleNamespace, changes: dict[str, object]) -> SimpleNamespace:
        self.updated = changes
        for field, value in changes.items():
            setattr(user, field, value)
        return user


def _admin(user_id: int = 1) -> SimpleNamespace:
    return SimpleNamespace(id=user_id, role=UserRole.ADMIN, is_active=True, email="admin@example.com")


def _service(user: SimpleNamespace, active_admins: int = 1) -> tuple[UserService, FakeUsers]:
    repository = FakeUsers(user, active_admins)
    return UserService(repository=repository, session=AsyncMock()), repository


def test_build_admin_create_uses_admin_role() -> None:
    data = build_admin_create(
        email=" Admin@Example.com ",
        full_name=" Admin ",
        password="long-password",
        password_repeat="long-password",
    )
    assert data.email == "Admin@example.com"
    assert data.full_name == "Admin"
    assert data.role == UserRole.ADMIN
    assert data.is_active is True


def test_build_admin_create_rejects_mismatched_or_short_password() -> None:
    with pytest.raises(ValueError, match="do not match"):
        build_admin_create(
            email="admin@example.com",
            full_name="Admin",
            password="long-password",
            password_repeat="other-password",
        )
    with pytest.raises(ValidationError):
        build_admin_create(
            email="admin@example.com",
            full_name="Admin",
            password="short",
            password_repeat="short",
        )


def test_admin_cannot_deactivate_self() -> None:
    async def scenario() -> None:
        service, repository = _service(_admin())
        with pytest.raises(CannotModifyOwnAdminAccessError):
            await service.deactivate_user(1, actor_id=1)
        assert repository.updated is None

    asyncio.run(scenario())


def test_admin_cannot_demote_self() -> None:
    async def scenario() -> None:
        service, _repository = _service(_admin())
        with pytest.raises(CannotModifyOwnAdminAccessError):
            await service.update_user(1, UserUpdate(role=UserRole.MODERATOR), actor_id=1)

    asyncio.run(scenario())


def test_cannot_remove_the_last_active_admin() -> None:
    async def scenario() -> None:
        service, repository = _service(_admin(user_id=2), active_admins=1)
        with pytest.raises(LastActiveAdminError):
            await service.deactivate_user(2, actor_id=1)
        assert repository.updated is None

    asyncio.run(scenario())


def test_another_admin_can_deactivate_an_admin_when_one_remains() -> None:
    async def scenario() -> None:
        service, repository = _service(_admin(user_id=2), active_admins=2)
        await service.deactivate_user(2, actor_id=1)
        assert repository.updated == {"is_active": False}

    asyncio.run(scenario())
