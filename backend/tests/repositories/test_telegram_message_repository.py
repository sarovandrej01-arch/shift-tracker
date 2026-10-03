import asyncio
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.core.enums import MessageReason, MessageStatus
from app.repositories.shift.repository import ShiftRepository
from app.repositories.telegram_message.repository import TelegramMessageRepository


def test_message_list_filters_and_orders_newest_first() -> None:
    async def scenario() -> None:
        session = AsyncMock()
        result = MagicMock()
        result.all.return_value = []
        session.scalars = AsyncMock(return_value=result)
        repository = TelegramMessageRepository(session)

        await repository.list(
            offset=5,
            limit=10,
            status=MessageStatus.REVIEW,
            reason=MessageReason.EMPLOYEE_NOT_FOUND,
            employee_id=1,
            object_id=2,
            telegram_chat_id=-5108163234,
            telegram_user_id=5614718277,
            date_from=date(2026, 10, 1),
            date_to=date(2026, 10, 3),
            shift_date_from=date(2026, 10, 2),
            shift_date_to=date(2026, 10, 4),
        )

        statement = session.scalars.await_args.args[0]
        sql = str(statement)
        assert "telegram_messages.status" in sql
        assert "telegram_messages.reason" in sql
        assert "telegram_messages.employee_id" in sql
        assert "telegram_messages.object_id" in sql
        assert "telegram_messages.telegram_chat_id" in sql
        assert "telegram_messages.telegram_user_id" in sql
        assert "telegram_messages.created_at >=" in sql
        assert "telegram_messages.created_at <" in sql
        assert "telegram_messages.shift_date >=" in sql
        assert "telegram_messages.shift_date <=" in sql
        assert "ORDER BY telegram_messages.created_at DESC, telegram_messages.id DESC" in sql
        compiled = statement.compile()
        assert compiled.params["param_1"] == 10 or compiled.params.get("limit_1") == 10 or 10 in compiled.params.values()
        assert 5 in compiled.params.values()
        assert datetime(2026, 10, 1, tzinfo=timezone.utc) in compiled.params.values()
        assert datetime(2026, 10, 4, tzinfo=timezone.utc) in compiled.params.values()

    asyncio.run(scenario())


def test_shift_lookup_by_source_message() -> None:
    async def scenario() -> None:
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=None)
        repository = ShiftRepository(session)

        found = await repository.get_by_source_message_id(10)

        assert found is None
        statement = session.scalar.await_args.args[0]
        sql = str(statement)
        assert "shifts.source_message_id" in sql
        assert "ORDER BY shifts.id DESC" in sql
        assert 10 in statement.compile().params.values()

    asyncio.run(scenario())
