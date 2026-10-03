import asyncio
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.dialects import postgresql

from app.repositories.dashboard.repository import DashboardRepository
from app.repositories.processing_log.repository import ProcessingLogRepository
from app.repositories.shift.repository import ShiftRepository


def _execute_result() -> MagicMock:
    result = MagicMock()
    result.one.return_value = MagicMock(
        total=0,
        new=0,
        processing=0,
        accepted=0,
        review=0,
        rejected=0,
        duplicate=0,
        error=0,
        automatic=0,
        manual=0,
    )
    result.all.return_value = []
    return result


def test_dashboard_counts_use_sql_aggregation() -> None:
    async def scenario() -> None:
        session = AsyncMock()
        session.execute = AsyncMock(return_value=_execute_result())
        repository = DashboardRepository(session)

        await repository.message_status_counts(date_from=date(2026, 10, 3), date_to=date(2026, 10, 3), object_id=1)
        message_sql = str(session.execute.await_args.args[0].compile(dialect=postgresql.dialect()))
        assert "count" in message_sql.lower()
        assert "FILTER" in message_sql
        assert "telegram_messages.created_at" in message_sql

        await repository.shift_confirmation_counts(
            date_from=date(2026, 10, 3),
            date_to=date(2026, 10, 3),
            object_id=1,
        )
        shift_sql = str(session.execute.await_args.args[0].compile(dialect=postgresql.dialect()))
        assert "count" in shift_sql.lower()
        assert "FILTER" in shift_sql
        assert "shifts.shift_date" in shift_sql

        await repository.message_counts_by_object(date_from=date(2026, 10, 3), date_to=date(2026, 10, 3))
        grouped_sql = str(session.execute.await_args.args[0].compile(dialect=postgresql.dialect()))
        assert "GROUP BY" in grouped_sql
        assert "count" in grouped_sql.lower()

    asyncio.run(scenario())


def test_shift_list_orders_by_date_then_id() -> None:
    async def scenario() -> None:
        session = AsyncMock()
        result = MagicMock()
        result.all.return_value = []
        session.scalars = AsyncMock(return_value=result)
        repository = ShiftRepository(session)

        await repository.list(
            offset=5,
            limit=10,
            employee_id=1,
            object_id=2,
            date_from=date(2026, 10, 1),
            date_to=date(2026, 10, 3),
            confirmed_manually=False,
        )

        sql = str(session.scalars.await_args.args[0])
        assert "ORDER BY shifts.shift_date DESC, shifts.id DESC" in sql
        assert "shifts.employee_id" in sql
        assert "shifts.confirmed_manually" in sql

    asyncio.run(scenario())


def test_message_logs_are_ordered_chronologically() -> None:
    async def scenario() -> None:
        session = AsyncMock()
        result = MagicMock()
        result.all.return_value = []
        session.scalars = AsyncMock(return_value=result)
        repository = ProcessingLogRepository(session)

        await repository.list_by_message(4)

        sql = str(session.scalars.await_args.args[0])
        assert "ORDER BY processing_logs.created_at, processing_logs.id" in sql
        assert "DESC" not in sql

    asyncio.run(scenario())
