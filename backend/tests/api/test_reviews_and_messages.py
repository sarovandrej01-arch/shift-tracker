from datetime import date, datetime, time, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_message_service, get_review_service, require_moderator_or_admin
from app.core.enums import MessageReason, MessageStatus
from app.core.exceptions import (
    ReviewConfirmationIncompleteError,
    ShiftAlreadyExistsError,
    StorageError,
    TelegramMessageNotFoundError,
    TelegramMessageNotInReviewError,
)
from app.main import app
from app.services.message import MessageDetail, MessagePhotoUrl, MessageService
from app.services.review import ReviewConfirmation

NOW = datetime(2026, 10, 3, 15, 18, tzinfo=timezone.utc)


@pytest.fixture
def client():
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


def _authorize() -> None:
    app.dependency_overrides[require_moderator_or_admin] = lambda: SimpleNamespace(id=4)


def _message(**overrides: object) -> SimpleNamespace:
    data: dict[str, object] = {
        "id": 10,
        "telegram_message_id": 4,
        "telegram_chat_id": -5108163234,
        "telegram_user_id": 5614718277,
        "telegram_username": "Assura58",
        "text": None,
        "caption": "Мехоношин",
        "photo_file_id": "photo-1",
        "photo_storage_key": "telegram/2026/10/03/-5108163234/4.jpg",
        "telegram_created_at": NOW,
        "edited_at": None,
        "employee_id": 1,
        "object_id": 1,
        "shift_date": date(2026, 10, 3),
        "status": MessageStatus.REVIEW,
        "reason": MessageReason.EMPLOYEE_NOT_FOUND,
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _shift() -> SimpleNamespace:
    return SimpleNamespace(
        id=5,
        employee_id=1,
        object_id=1,
        shift_date=date(2026, 10, 3),
        source_message_id=10,
        confirmed_manually=True,
        confirmed_by_user_id=4,
        created_at=NOW,
        updated_at=NOW,
    )


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


def test_openapi_lists_review_and_message_routes(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "get" in paths["/api/v1/reviews"]
    assert "post" in paths["/api/v1/reviews/{message_id}/confirm"]
    assert "post" in paths["/api/v1/reviews/{message_id}/reject"]
    assert "get" in paths["/api/v1/messages"]
    assert "get" in paths["/api/v1/messages/{message_id}"]
    assert "get" in paths["/api/v1/messages/{message_id}/photo-url"]


def test_list_reviews_returns_review_fields(client: TestClient) -> None:
    service = AsyncMock()
    service.list_reviews.return_value = [_message()]
    app.dependency_overrides[get_review_service] = lambda: service
    _authorize()

    response = client.get(
        "/api/v1/reviews",
        params={
            "offset": 0,
            "limit": 10,
            "reason": "employee_not_found",
            "employee_id": 1,
            "object_id": 1,
            "date_from": "2026-10-03",
            "date_to": "2026-10-03",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body[0]["status"] == "review"
    assert body[0]["reason"] == "employee_not_found"
    assert body[0]["caption"] == "Мехоношин"
    assert body[0]["photo_storage_key"] == "telegram/2026/10/03/-5108163234/4.jpg"
    assert body[0]["employee_id"] == 1
    assert body[0]["object_id"] == 1
    assert body[0]["shift_date"] == "2026-10-03"
    kwargs = service.list_reviews.await_args.kwargs
    assert kwargs["reason"] is MessageReason.EMPLOYEE_NOT_FOUND
    assert kwargs["employee_id"] == 1
    assert kwargs["object_id"] == 1
    assert kwargs["limit"] == 10


def test_confirm_review_returns_message_and_shift(client: TestClient) -> None:
    accepted = _message(status=MessageStatus.ACCEPTED, reason=None)
    service = AsyncMock()
    service.confirm.return_value = ReviewConfirmation(message=accepted, shift=_shift())
    app.dependency_overrides[get_review_service] = lambda: service
    _authorize()

    response = client.post(
        "/api/v1/reviews/10/confirm",
        json={"employee_id": 1, "object_id": 1, "shift_date": "2026-10-03"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"]["status"] == "accepted"
    assert body["message"]["reason"] is None
    assert body["shift"]["confirmed_manually"] is True
    assert body["shift"]["confirmed_by_user_id"] == 4
    assert body["shift"]["source_message_id"] == 10
    assert service.confirm.await_args.kwargs["user_id"] == 4


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (TelegramMessageNotFoundError, 404),
        (TelegramMessageNotInReviewError, 409),
        (ShiftAlreadyExistsError, 409),
        (ReviewConfirmationIncompleteError(["employee_id", "shift_date"]), 422),
    ],
)
def test_confirm_review_errors(client: TestClient, error: Exception, status_code: int) -> None:
    service = AsyncMock()
    service.confirm.side_effect = error
    app.dependency_overrides[get_review_service] = lambda: service
    _authorize()

    response = client.post(
        "/api/v1/reviews/10/confirm",
        json={"employee_id": 1, "object_id": 1, "shift_date": "2026-10-03"},
    )

    assert response.status_code == status_code


def test_reject_review_returns_rejected_message(client: TestClient) -> None:
    rejected = _message(status=MessageStatus.REJECTED, reason=MessageReason.EMPLOYEE_NOT_FOUND)
    service = AsyncMock()
    service.reject.return_value = rejected
    app.dependency_overrides[get_review_service] = lambda: service
    _authorize()

    response = client.post("/api/v1/reviews/10/reject", json={"comment": "Test rejection"})

    assert response.status_code == 200
    assert response.json()["message"]["status"] == "rejected"
    assert response.json()["message"]["reason"] == "employee_not_found"
    assert service.reject.await_args.kwargs["user_id"] == 4
    assert service.reject.await_args.args[1].comment == "Test rejection"


def test_list_messages_returns_pipeline_fields(client: TestClient) -> None:
    service = AsyncMock()
    service.list_messages.return_value = [_message(status=MessageStatus.ACCEPTED, reason=None)]
    app.dependency_overrides[get_message_service] = lambda: service
    _authorize()

    response = client.get(
        "/api/v1/messages",
        params={"status": "accepted", "employee_id": 1, "object_id": 1, "limit": 5, "offset": 0},
    )

    assert response.status_code == 200
    item = response.json()[0]
    assert item["photo_storage_key"] == "telegram/2026/10/03/-5108163234/4.jpg"
    assert item["caption"] == "Мехоношин"
    assert item["status"] == "accepted"
    assert item["reason"] is None
    assert item["employee_id"] == 1
    assert item["object_id"] == 1
    assert item["shift_date"] == "2026-10-03"
    assert service.list_messages.await_args.kwargs["status"] is MessageStatus.ACCEPTED
    assert service.list_messages.await_args.kwargs["limit"] == 5


def test_message_detail_includes_related_records(client: TestClient) -> None:
    service = AsyncMock()
    service.get_message.return_value = MessageDetail(
        message=_message(status=MessageStatus.ACCEPTED, reason=None),
        employee=_employee(),
        work_object=_work_object(),
        shift=_shift(),
    )
    app.dependency_overrides[get_message_service] = lambda: service
    _authorize()

    response = client.get("/api/v1/messages/10")

    assert response.status_code == 200
    body = response.json()
    assert body["employee"]["full_name"] == "Мехоношин"
    assert body["work_object"]["name"] == "Тестовый объект"
    assert body["shift"]["source_message_id"] == 10
    assert body["photo_storage_key"].endswith("4.jpg")


def test_message_detail_not_found(client: TestClient) -> None:
    service = AsyncMock()
    service.get_message.side_effect = TelegramMessageNotFoundError
    app.dependency_overrides[get_message_service] = lambda: service
    _authorize()

    response = client.get("/api/v1/messages/99")

    assert response.status_code == 404
    assert response.json()["detail"] == "Telegram message not found"


def test_photo_url_response(client: TestClient) -> None:
    service = AsyncMock()
    service.get_photo_url.return_value = MessagePhotoUrl(
        message_id=10,
        url="http://localhost:9000/shift-tracker/telegram/4.jpg",
        expires_in=3600,
    )
    app.dependency_overrides[get_message_service] = lambda: service
    _authorize()

    response = client.get("/api/v1/messages/10/photo-url")

    assert response.status_code == 200
    assert response.json() == {
        "message_id": 10,
        "url": "http://localhost:9000/shift-tracker/telegram/4.jpg",
        "expires_in": 3600,
    }


def test_photo_url_storage_error_does_not_leak_secrets(client: TestClient) -> None:
    messages = AsyncMock()
    messages.get_by_id.return_value = _message()
    storage = AsyncMock()
    storage.get_presigned_url.side_effect = StorageError("aws_secret_access_key=super-secret")
    app.dependency_overrides[get_message_service] = lambda: MessageService(
        message_repository=messages,
        employee_repository=AsyncMock(),
        work_object_repository=AsyncMock(),
        shift_repository=AsyncMock(),
        storage=storage,
        presigned_url_expire_seconds=3600,
    )
    _authorize()

    response = client.get("/api/v1/messages/10/photo-url")

    assert response.status_code == 502
    assert response.json()["detail"] == "Photo storage is unavailable"
    assert "super-secret" not in response.text


def test_photo_url_missing_key_returns_404(client: TestClient) -> None:
    messages = AsyncMock()
    messages.get_by_id.return_value = _message(photo_storage_key=None)
    app.dependency_overrides[get_message_service] = lambda: MessageService(
        message_repository=messages,
        employee_repository=AsyncMock(),
        work_object_repository=AsyncMock(),
        shift_repository=AsyncMock(),
        storage=AsyncMock(),
        presigned_url_expire_seconds=3600,
    )
    _authorize()

    response = client.get("/api/v1/messages/10/photo-url")

    assert response.status_code == 404
    assert response.json()["detail"] == "Telegram message photo not found"


def test_photo_url_unknown_message_returns_404(client: TestClient) -> None:
    service = AsyncMock()
    service.get_photo_url.side_effect = TelegramMessageNotFoundError
    app.dependency_overrides[get_message_service] = lambda: service
    _authorize()

    response = client.get("/api/v1/messages/10/photo-url")

    assert response.status_code == 404
    assert response.json()["detail"] == "Telegram message not found"
