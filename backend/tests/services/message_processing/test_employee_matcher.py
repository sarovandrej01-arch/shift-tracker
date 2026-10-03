import asyncio
from unittest.mock import AsyncMock

from app.services.message_processing import EmployeeMatcher, EmployeeMatchStatus


class FakeEmployee:
    def __init__(self, employee_id: int, *, is_active: bool = True) -> None:
        self.id = employee_id
        self.is_active = is_active


def _matcher(repository: AsyncMock) -> EmployeeMatcher:
    return EmployeeMatcher(repository)


def test_telegram_user_id_match_stops_cascade() -> None:
    async def scenario() -> None:
        employee = FakeEmployee(1)
        repository = AsyncMock()
        repository.get_by_telegram_user_id.return_value = employee

        result = await _matcher(repository).match(
            telegram_user_id=123,
            text="Начало смены EMP-001",
            caption=None,
        )

        assert result.status is EmployeeMatchStatus.MATCHED
        assert result.employee is employee
        assert result.matched_by == "telegram_user_id"
        assert result.candidates == []
        repository.get_by_personnel_number.assert_not_called()
        repository.get_by_callsign.assert_not_called()
        repository.find_by_full_name.assert_not_called()

    asyncio.run(scenario())


def test_inactive_telegram_employee_falls_through_to_personnel_number() -> None:
    async def scenario() -> None:
        inactive = FakeEmployee(1, is_active=False)
        active = FakeEmployee(2)
        repository = AsyncMock()
        repository.get_by_telegram_user_id.return_value = inactive
        repository.get_by_personnel_number.side_effect = (
            lambda token: active if token == "EMP-002" else None
        )

        result = await _matcher(repository).match(
            telegram_user_id=123,
            text="Смена EMP-002",
            caption=None,
        )

        assert result.status is EmployeeMatchStatus.MATCHED
        assert result.employee is active
        assert result.matched_by == "personnel_number"
        repository.get_by_callsign.assert_not_called()
        repository.find_by_full_name.assert_not_called()

    asyncio.run(scenario())


def test_personnel_number_in_text() -> None:
    async def scenario() -> None:
        employee = FakeEmployee(1)
        repository = AsyncMock()
        repository.get_by_personnel_number.side_effect = (
            lambda token: employee if token == "EMP-001" else None
        )

        result = await _matcher(repository).match(
            telegram_user_id=None,
            text="Начало смены EMP-001",
            caption=None,
        )

        assert result.status is EmployeeMatchStatus.MATCHED
        assert result.employee is employee
        assert result.matched_by == "personnel_number"
        repository.get_by_telegram_user_id.assert_not_called()

    asyncio.run(scenario())


def test_personnel_number_in_caption() -> None:
    async def scenario() -> None:
        employee = FakeEmployee(1)
        repository = AsyncMock()
        repository.get_by_personnel_number.side_effect = (
            lambda token: employee if token == "EMP-001" else None
        )

        result = await _matcher(repository).match(
            telegram_user_id=None,
            text=None,
            caption="Смена EMP-001",
        )

        assert result.status is EmployeeMatchStatus.MATCHED
        assert result.employee is employee
        assert result.matched_by == "personnel_number"

    asyncio.run(scenario())


def test_callsign_match() -> None:
    async def scenario() -> None:
        employee = FakeEmployee(1)
        repository = AsyncMock()
        repository.get_by_personnel_number.return_value = None
        repository.get_by_callsign.side_effect = lambda token: [employee] if token == "Сокол" else []

        result = await _matcher(repository).match(
            telegram_user_id=None,
            text="Вышел на смену Сокол",
            caption=None,
        )

        assert result.status is EmployeeMatchStatus.MATCHED
        assert result.employee is employee
        assert result.matched_by == "callsign"
        repository.find_by_full_name.assert_not_called()

    asyncio.run(scenario())


def test_callsign_ambiguous_stops_before_full_name() -> None:
    async def scenario() -> None:
        first = FakeEmployee(1)
        second = FakeEmployee(2)
        repository = AsyncMock()
        repository.get_by_personnel_number.return_value = None
        repository.get_by_callsign.side_effect = lambda token: [first, second] if token == "Сокол" else []

        result = await _matcher(repository).match(
            telegram_user_id=None,
            text="Вышел на смену Сокол",
            caption=None,
        )

        assert result.status is EmployeeMatchStatus.AMBIGUOUS
        assert result.employee is None
        assert result.matched_by == "callsign"
        assert result.candidates == [first, second]
        repository.find_by_full_name.assert_not_called()

    asyncio.run(scenario())


def test_full_name_match() -> None:
    async def scenario() -> None:
        employee = FakeEmployee(1)
        repository = AsyncMock()
        repository.get_by_personnel_number.return_value = None
        repository.get_by_callsign.return_value = []
        repository.find_by_full_name.side_effect = (
            lambda name: [employee] if name == "Иванов Иван Иванович" else []
        )

        result = await _matcher(repository).match(
            telegram_user_id=None,
            text="Иванов Иван Иванович",
            caption=None,
        )

        assert result.status is EmployeeMatchStatus.MATCHED
        assert result.employee is employee
        assert result.matched_by == "full_name"

    asyncio.run(scenario())


def test_full_name_ambiguous() -> None:
    async def scenario() -> None:
        first = FakeEmployee(1)
        second = FakeEmployee(2)
        repository = AsyncMock()
        repository.get_by_personnel_number.return_value = None
        repository.get_by_callsign.return_value = []
        repository.find_by_full_name.return_value = [first, second]

        result = await _matcher(repository).match(
            telegram_user_id=None,
            text="Иванов Иван Иванович",
            caption=None,
        )

        assert result.status is EmployeeMatchStatus.AMBIGUOUS
        assert result.employee is None
        assert result.matched_by == "full_name"
        assert result.candidates == [first, second]

    asyncio.run(scenario())


def test_not_found() -> None:
    async def scenario() -> None:
        repository = AsyncMock()
        repository.get_by_telegram_user_id.return_value = None
        repository.get_by_personnel_number.return_value = None
        repository.get_by_callsign.return_value = []
        repository.find_by_full_name.return_value = []

        result = await _matcher(repository).match(
            telegram_user_id=123,
            text="неизвестный текст",
            caption=None,
        )

        assert result.status is EmployeeMatchStatus.NOT_FOUND
        assert result.employee is None
        assert result.matched_by is None
        assert result.candidates == []

    asyncio.run(scenario())


def test_inactive_callsign_candidate_is_ignored() -> None:
    async def scenario() -> None:
        active = FakeEmployee(1)
        inactive = FakeEmployee(2, is_active=False)
        repository = AsyncMock()
        repository.get_by_personnel_number.return_value = None
        repository.get_by_callsign.side_effect = (
            lambda token: [active, inactive] if token == "Сокол" else []
        )

        result = await _matcher(repository).match(
            telegram_user_id=None,
            text="Сокол",
            caption=None,
        )

        assert result.status is EmployeeMatchStatus.MATCHED
        assert result.employee is active
        assert result.matched_by == "callsign"

    asyncio.run(scenario())


def test_telegram_user_id_wins_over_personnel_number() -> None:
    async def scenario() -> None:
        by_telegram = FakeEmployee(1)
        repository = AsyncMock()
        repository.get_by_telegram_user_id.return_value = by_telegram

        result = await _matcher(repository).match(
            telegram_user_id=123,
            text="Начало смены EMP-001",
            caption=None,
        )

        assert result.status is EmployeeMatchStatus.MATCHED
        assert result.employee is by_telegram
        assert result.matched_by == "telegram_user_id"
        repository.get_by_personnel_number.assert_not_called()

    asyncio.run(scenario())


def test_ambiguous_personnel_number_stops_before_full_name() -> None:
    async def scenario() -> None:
        first = FakeEmployee(1)
        second = FakeEmployee(2)
        repository = AsyncMock()

        def by_number(token: str) -> FakeEmployee | None:
            if token == "EMP-001":
                return first
            if token == "EMP-002":
                return second
            return None

        repository.get_by_personnel_number.side_effect = by_number

        result = await _matcher(repository).match(
            telegram_user_id=None,
            text="EMP-001 EMP-002 Иванов Иван Иванович",
            caption=None,
        )

        assert result.status is EmployeeMatchStatus.AMBIGUOUS
        assert result.matched_by == "personnel_number"
        assert result.employee is None
        assert result.candidates == [first, second]
        repository.get_by_callsign.assert_not_called()
        repository.find_by_full_name.assert_not_called()

    asyncio.run(scenario())
