from datetime import date, datetime, time, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_dashboard_service,
    get_message_service,
    get_processing_log_service,
    get_review_service,
    get_shift_service,
    get_user_repository,
    require_moderator_or_admin,
)
from app.core.enums import UserRole
from app.main import app
from app.schemas.dashboard import (
    DashboardMessageCounts,
    DashboardPeriodRead,
    DashboardShiftCounts,
    DashboardSummaryRead,
)
from app.services.auth.jwt import create_access_token
from app.services.dashboard import DashboardService
from app.services.message import MessageService
from app.services.processing_log import ProcessingLogService
from app.services.review import ReviewService
from app.services.shift import ShiftDetail, ShiftService

NOW = datetime(2026, 10, 3, 15, 0, tzinfo=timezone.utc)


@pytest.fixture
def client():
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


def _authorize(role: UserRole = UserRole.ADMIN) -> None:
    app.dependency_overrides[require_moderator_or_admin] = lambda: SimpleNamespace(id=1, role=role)


def _shift(**overrides: object) -> SimpleNamespace:
    data: dict[str, object] = {
        "id": 1,
        "employee_id": 1,
        "object_id": 1,
        "shift_date": date(2026, 10, 3),
        "source_message_id": 4,
        "confirmed_manually": False,
        "confirmed_by_user_id": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _employee() -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        full_name="Мехоношин",
        personnel_number="TEST001",
        telegram_user_id=5614718277,
        telegram_username="Assura58",
        callsign="Мехоношин",
        is_active=True,
        created_at=NOW,
        updated_at=NOW,
    )


def _work_object() -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        name="Тестовый объект",
        shift_start_time=time(20, 0),
        checkin_before_minutes=180,
        checkin_after_minutes=240,
        timezone="Europe/Moscow",
        is_active=True,
        created_at=NOW,
        updated_at=NOW,
    )


def _message() -> SimpleNamespace:
    return SimpleNamespace(
        id=4,
        telegram_message_id=4,
        telegram_chat_id=-5108163234,
        telegram_user_id=5614718277,
        telegram_username="Assura58",
        text=None,
        caption="Мехоношин",
        photo_file_id="photo",
        photo_storage_key="telegram/2026/10/03/-5108163234/4.jpg",
        telegram_created_at=NOW,
        edited_at=None,
        employee_id=1,
        object_id=1,
        shift_date=date(2026, 10, 3),
        status="accepted",
        reason=None,
        created_at=NOW,
        updated_at=NOW,
    )


def _user() -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        email="moderator@example.com",
        full_name="Smoke Moderator",
        role=UserRole.MODERATOR,
        is_active=True,
        created_at=NOW,
        updated_at=NOW,
    )


def test_openapi_lists_shift_log_and_dashboard_routes(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "get" in paths["/api/v1/shifts"]
    assert "get" in paths["/api/v1/shifts/{shift_id}"]
    assert "get" in paths["/api/v1/logs"]
    assert "get" in paths["/api/v1/messages/{message_id}/logs"]
    assert "get" in paths["/api/v1/dashboard/summary"]
    assert paths["/api/v1/shifts"]["get"].get("security")


def test_new_routes_require_a_token(client: TestClient) -> None:
    for path in ("/api/v1/shifts", "/api/v1/logs", "/api/v1/dashboard/summary", "/api/v1/messages/1/logs"):
        response = client.get(path)
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"


def test_inactive_user_is_forbidden(client: TestClient) -> None:
    repository = AsyncMock()
    repository.get_by_id.return_value = SimpleNamespace(id=1, is_active=False, role=UserRole.ADMIN)
    app.dependency_overrides[get_user_repository] = lambda: repository

    response = client.get("/api/v1/shifts", headers={"Authorization": f"Bearer {create_access_token(1)}"})

    assert response.status_code == 403


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.MODERATOR])
def test_staff_can_list_shifts(client: TestClient, role: UserRole) -> None:
    repository = AsyncMock()
    repository.get_by_id.return_value = SimpleNamespace(id=1, is_active=True, role=role)
    service = AsyncMock()
    service.list_shifts.return_value = [_shift()]
    app.dependency_overrides[get_user_repository] = lambda: repository
    app.dependency_overrides[get_shift_service] = lambda: service

    response = client.get(
        "/api/v1/shifts",
        headers={"Authorization": f"Bearer {create_access_token(1)}"},
        params={"employee_id": 1, "object_id": 1, "confirmed_manually": False, "limit": 5, "offset": 0},
    )

    assert response.status_code == 200
    item = response.json()[0]
    assert item["source_message_id"] == 4
    assert item["confirmed_by_user_id"] is None
    assert item["confirmed_manually"] is False
    assert service.list_shifts.await_args.kwargs["employee_id"] == 1
    assert service.list_shifts.await_args.kwargs["confirmed_manually"] is False


def test_shift_detail_includes_relations(client: TestClient) -> None:
    service = AsyncMock()
    service.get_shift_detail.return_value = ShiftDetail(
        shift=_shift(confirmed_manually=True, confirmed_by_user_id=1),
        employee=_employee(),
        work_object=_work_object(),
        source_message=_message(),
        confirmed_by_user=_user(),
    )
    app.dependency_overrides[get_shift_service] = lambda: service
    _authorize()

    response = client.get("/api/v1/shifts/1")

    assert response.status_code == 200
    body = response.json()
    assert body["employee"]["full_name"] == "Мехоношин"
    assert body["work_object"]["name"] == "Тестовый объект"
    assert body["source_message"]["id"] == 4
    assert body["confirmed_by_user"]["id"] == 1


def test_shift_detail_not_found(client: TestClient) -> None:
    service = ShiftService(AsyncMock(), AsyncMock())
    service.repository.get_by_id.return_value = None
    app.dependency_overrides[get_shift_service] = lambda: service
    _authorize()

    response = client.get("/api/v1/shifts/99")

    assert response.status_code == 404
    assert response.json()["detail"] == "Shift not found"


def test_inverted_shift_dates_return_422(client: TestClient) -> None:
    app.dependency_overrides[get_shift_service] = lambda: ShiftService(AsyncMock(), AsyncMock())
    _authorize()

    response = client.get("/api/v1/shifts", params={"date_from": "2026-10-04", "date_to": "2026-10-01"})

    assert response.status_code == 422


def test_logs_keep_details_and_user(client: TestClient) -> None:
    service = AsyncMock()
    service.list_logs.return_value = [
        SimpleNamespace(
            id=2,
            message_id=4,
            user_id=1,
            action="manual_confirm",
            details="shift_id=1",
            created_at=NOW,
        )
    ]
    app.dependency_overrides[get_processing_log_service] = lambda: service
    _authorize()

    response = client.get("/api/v1/logs", params={"message_id": 4, "user_id": 1, "action": "manual_confirm"})

    assert response.status_code == 200
    item = response.json()[0]
    assert item["details"] == "shift_id=1"
    assert item["user_id"] == 1
    assert item["created_at"].startswith("2026-10-03")
    assert service.list_logs.await_args.kwargs["action"] == "manual_confirm"


def test_message_logs_keep_pipeline_order(client: TestClient) -> None:
    service = AsyncMock()
    service.list_message_logs.return_value = [
        SimpleNamespace(id=1, message_id=4, user_id=None, action="message_received", details=None, created_at=NOW),
        SimpleNamespace(id=2, message_id=4, user_id=None, action="accepted", details="shift_id=1", created_at=NOW),
    ]
    app.dependency_overrides[get_processing_log_service] = lambda: service
    _authorize()

    response = client.get("/api/v1/messages/4/logs")

    assert response.status_code == 200
    assert [item["action"] for item in response.json()] == ["message_received", "accepted"]


def test_message_logs_missing_message(client: TestClient) -> None:
    messages = AsyncMock()
    messages.get_by_id.return_value = None
    app.dependency_overrides[get_processing_log_service] = lambda: ProcessingLogService(
        AsyncMock(),
        AsyncMock(),
        message_repository=messages,
    )
    _authorize()

    response = client.get("/api/v1/messages/99/logs")

    assert response.status_code == 404


def test_naive_log_dates_return_422(client: TestClient) -> None:
    app.dependency_overrides[get_processing_log_service] = lambda: ProcessingLogService(AsyncMock(), AsyncMock())
    _authorize()

    response = client.get("/api/v1/logs", params={"date_from": "2026-10-03T00:00:00"})

    assert response.status_code == 422


def test_dashboard_summary_response(client: TestClient) -> None:
    service = AsyncMock()
    service.summary.return_value = DashboardSummaryRead(
        period=DashboardPeriodRead(date_from=date(2026, 10, 3), date_to=date(2026, 10, 3)),
        messages=DashboardMessageCounts(
            total=10,
            accepted=5,
            review=2,
            rejected=1,
            duplicate=1,
            error=1,
        ),
        shifts=DashboardShiftCounts(total=5, automatic=4, manual=1),
    )
    app.dependency_overrides[get_dashboard_service] = lambda: service
    _authorize(UserRole.MODERATOR)

    response = client.get(
        "/api/v1/dashboard/summary",
        params={"date_from": "2026-10-03", "date_to": "2026-10-03", "object_id": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["messages"]["accepted"] == 5
    assert body["shifts"]["manual"] == 1
    assert service.summary.await_args.kwargs["object_id"] == 1


def test_inverted_message_and_review_dates_return_422(client: TestClient) -> None:
    app.dependency_overrides[get_message_service] = lambda: MessageService(
        message_repository=AsyncMock(),
        employee_repository=AsyncMock(),
        work_object_repository=AsyncMock(),
        shift_repository=AsyncMock(),
        storage=AsyncMock(),
        presigned_url_expire_seconds=3600,
    )
    app.dependency_overrides[get_review_service] = lambda: ReviewService(
        session=AsyncMock(),
        message_repository=AsyncMock(),
        employee_repository=AsyncMock(),
        work_object_repository=AsyncMock(),
        shift_repository=AsyncMock(),
        processing_log_repository=AsyncMock(),
    )
    _authorize()

    messages = client.get("/api/v1/messages", params={"date_from": "2026-10-04", "date_to": "2026-10-01"})
    reviews = client.get("/api/v1/reviews", params={"date_from": "2026-10-04", "date_to": "2026-10-01"})

    assert messages.status_code == 422
    assert reviews.status_code == 422


def test_dashboard_inverted_dates_return_422(client: TestClient) -> None:
    app.dependency_overrides[get_dashboard_service] = lambda: DashboardService(AsyncMock(), today=lambda: date(2026, 10, 3))
    _authorize()

    response = client.get("/api/v1/dashboard/summary", params={"date_from": "2026-10-04", "date_to": "2026-10-01"})

    assert response.status_code == 422
