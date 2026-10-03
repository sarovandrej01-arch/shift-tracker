import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum

from app.models.employee import Employee
from app.repositories.employee.repository import EmployeeRepository

_TOKEN_PATTERN = re.compile(r"[A-Za-zА-Яа-я0-9_-]+")


class EmployeeMatchStatus(str, Enum):
    MATCHED = "matched"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"


@dataclass(slots=True)
class EmployeeMatchResult:
    status: EmployeeMatchStatus
    employee: Employee | None = None
    matched_by: str | None = None
    candidates: list[Employee] = field(default_factory=list)


def _combined_text(text: str | None, caption: str | None) -> str:
    parts = [value.strip() for value in (text, caption) if value and value.strip()]
    return "\n".join(parts)


def _tokens(combined_text: str) -> list[str]:
    return list(dict.fromkeys(_TOKEN_PATTERN.findall(combined_text)))


def _unique_active_employees(employees: Iterable[Employee]) -> list[Employee]:
    unique: list[Employee] = []
    seen: set[int] = set()
    for employee in employees:
        if not employee.is_active or employee.id in seen:
            continue
        seen.add(employee.id)
        unique.append(employee)
    return unique


def _decision(candidates: list[Employee], matched_by: str) -> EmployeeMatchResult | None:
    if not candidates:
        return None
    if len(candidates) == 1:
        return EmployeeMatchResult(
            status=EmployeeMatchStatus.MATCHED,
            employee=candidates[0],
            matched_by=matched_by,
        )
    return EmployeeMatchResult(
        status=EmployeeMatchStatus.AMBIGUOUS,
        matched_by=matched_by,
        candidates=candidates,
    )


class EmployeeMatcher:
    def __init__(self, employee_repository: EmployeeRepository) -> None:
        self.employee_repository = employee_repository

    async def match(
        self,
        *,
        telegram_user_id: int | None,
        text: str | None,
        caption: str | None,
    ) -> EmployeeMatchResult:
        if telegram_user_id is not None:
            employee = await self.employee_repository.get_by_telegram_user_id(telegram_user_id)
            if employee is not None and employee.is_active:
                return EmployeeMatchResult(
                    status=EmployeeMatchStatus.MATCHED,
                    employee=employee,
                    matched_by="telegram_user_id",
                )

        combined = _combined_text(text, caption)
        if not combined:
            return EmployeeMatchResult(status=EmployeeMatchStatus.NOT_FOUND)

        personnel_result = await self._match_personnel_number(combined)
        if personnel_result is not None:
            return personnel_result

        callsign_result = await self._match_callsign(combined)
        if callsign_result is not None:
            return callsign_result

        return await self._match_full_name(combined)

    async def _match_personnel_number(self, combined: str) -> EmployeeMatchResult | None:
        found: list[Employee] = []
        for token in _tokens(combined):
            employee = await self.employee_repository.get_by_personnel_number(token)
            if employee is not None:
                found.append(employee)
        return _decision(_unique_active_employees(found), "personnel_number")

    async def _match_callsign(self, combined: str) -> EmployeeMatchResult | None:
        found: list[Employee] = []
        for token in _tokens(combined):
            found.extend(await self.employee_repository.get_by_callsign(token))
        return _decision(_unique_active_employees(found), "callsign")

    async def _match_full_name(self, combined: str) -> EmployeeMatchResult:
        normalized = " ".join(combined.split())
        candidates = _unique_active_employees(
            await self.employee_repository.find_by_full_name(normalized)
        )
        if not candidates:
            found: list[Employee] = []
            for line in combined.splitlines():
                line_normalized = " ".join(line.split())
                if not line_normalized or line_normalized == normalized:
                    continue
                found.extend(await self.employee_repository.find_by_full_name(line_normalized))
            candidates = _unique_active_employees(found)
        decision = _decision(candidates, "full_name")
        if decision is None:
            return EmployeeMatchResult(status=EmployeeMatchStatus.NOT_FOUND)
        return decision
