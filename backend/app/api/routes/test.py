from fastapi import APIRouter

from app.core.enums import MessageReason, MessageStatus

router = APIRouter(prefix="/test", tags=["test"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("")
async def test_root() -> dict[str, str]:
    return {"message": "shift-tracker test endpoint"}


@router.get("/enums")
async def test_enums() -> dict[str, list[str]]:
    return {
        "message_status": [item.value for item in MessageStatus],
        "message_reason": [item.value for item in MessageReason],
    }
