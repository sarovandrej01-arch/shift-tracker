import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_user_repository, get_user_service
from app.core.enums import UserRole
from app.core.exceptions import CannotModifyOwnAdminAccessError, LastActiveAdminError
from app.main import app
from app.services.auth.jwt import create_access_token

NOW = datetime(2026, 10, 3, 18, 0, tzinfo=timezone.utc)


@pytest.fixture
def client():
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


def _authorize(role: UserRole, user_id: int = 1) -> None:
    repository = AsyncMock()
    repository.get_by_id.return_value = SimpleNamespace(id=user_id, is_active=True, role=role)
    app.dependency_overrides[get_user_repository] = lambda: repository


def _user(**overrides: object) -> SimpleNamespace:
    data: dict[str, object] = {
        "id": 2,
        "email": "moderator@example.com",
        "full_name": "Moderator",
        "role": UserRole.MODERATOR,
        "is_active": True,
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _headers(user_id: int = 1) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def test_users_routes_require_a_token(client: TestClient) -> None:
    assert client.get("/api/v1/users").status_code == 401
    assert client.post("/api/v1/users", json={}).status_code == 401
    assert client.get("/api/v1/users").json()["detail"] == "Not authenticated"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/users"),
        ("post", "/api/v1/users"),
        ("patch", "/api/v1/users/2"),
        ("post", "/api/v1/users/2/activate"),
        ("post", "/api/v1/users/2/deactivate"),
    ],
)
def test_moderator_cannot_manage_users(client: TestClient, method: str, path: str) -> None:
    _authorize(UserRole.MODERATOR)
    response = client.request(method, path, headers=_headers(), json={})
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied"


def test_admin_can_list_and_create_users(client: TestClient) -> None:
    _authorize(UserRole.ADMIN)
    service = AsyncMock()
    service.list_users.return_value = [_user()]
    service.create_user.return_value = _user(id=3, email="new@example.com", full_name="New")
    app.dependency_overrides[get_user_service] = lambda: service

    listed = client.get("/api/v1/users", headers=_headers(), params={"role": "moderator", "limit": 20})
    assert listed.status_code == 200
    assert listed.json()[0]["email"] == "moderator@example.com"
    assert service.list_users.await_args.kwargs["role"] == UserRole.MODERATOR

    created = client.post(
        "/api/v1/users",
        headers=_headers(),
        json={
            "email": "new@example.com",
            "full_name": "New",
            "password": "long-password",
            "role": "moderator",
            "is_active": True,
        },
    )
    assert created.status_code == 201
    assert created.json()["id"] == 3


def test_admin_can_update_and_change_activity(client: TestClient) -> None:
    _authorize(UserRole.ADMIN, user_id=7)
    service = AsyncMock()
    service.update_user.return_value = _user(full_name="Updated")
    service.activate_user.return_value = _user(is_active=True)
    service.deactivate_user.return_value = _user(is_active=False)
    app.dependency_overrides[get_user_service] = lambda: service

    updated = client.patch(
        "/api/v1/users/2",
        headers=_headers(7),
        json={"full_name": "Updated"},
    )
    assert updated.status_code == 200
    assert service.update_user.await_args.kwargs["actor_id"] == 7

    assert client.post("/api/v1/users/2/activate", headers=_headers(7)).status_code == 200
    deactivated = client.post("/api/v1/users/2/deactivate", headers=_headers(7))
    assert deactivated.status_code == 200
    assert service.deactivate_user.await_args.kwargs["actor_id"] == 7


def test_admin_lockout_errors_are_conflicts(client: TestClient) -> None:
    _authorize(UserRole.ADMIN)
    service = AsyncMock()
    service.deactivate_user.side_effect = CannotModifyOwnAdminAccessError
    service.update_user.side_effect = LastActiveAdminError
    app.dependency_overrides[get_user_service] = lambda: service

    own = client.post("/api/v1/users/1/deactivate", headers=_headers())
    assert own.status_code == 409
    assert own.json()["detail"] == "You cannot remove your own administrator access"

    last = client.patch("/api/v1/users/1", headers=_headers(), json={"role": "moderator"})
    assert last.status_code == 409
    assert last.json()["detail"] == "Cannot remove the last active administrator"
