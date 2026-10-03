from dataclasses import dataclass
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MessageReason, MessageStatus
from app.core.exceptions.employee import EmployeeNotFoundError
from app.core.exceptions.review import ReviewConfirmationIncompleteError
from app.core.exceptions.shift import ShiftAlreadyExistsError
from app.core.exceptions.telegram_message import (
    TelegramMessageNotFoundError,
    TelegramMessageNotInReviewError,
)
from app.core.exceptions.work_object import WorkObjectNotFoundError
from app.models.shift import Shift
from app.models.telegram_message import TelegramMessage
from app.repositories.employee.repository import EmployeeRepository
from app.repositories.processing_log.repository import ProcessingLogRepository
from app.repositories.shift.repository import ShiftRepository
from app.repositories.telegram_message.repository import TelegramMessageRepository
from app.repositories.work_object.repository import WorkObjectRepository
from app.schemas.review import ReviewConfirmRequest, ReviewRejectRequest


@dataclass(slots=True)
class ReviewConfirmation:
    message: TelegramMessage
    shift: Shift


def _validate_pagination(offset: int, limit: int) -> None:
    if offset < 0 or not 1 <= limit <= 100:
        raise ValueError("offset must be >= 0 and limit must be between 1 and 100")


def _validate_date_range(date_from: date | None, date_to: date | None) -> None:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise ValueError("date_from must be less than or equal to date_to")


class ReviewService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        message_repository: TelegramMessageRepository,
        employee_repository: EmployeeRepository,
        work_object_repository: WorkObjectRepository,
        shift_repository: ShiftRepository,
        processing_log_repository: ProcessingLogRepository,
    ) -> None:
        self.session = session
        self.message_repository = message_repository
        self.employee_repository = employee_repository
        self.work_object_repository = work_object_repository
        self.shift_repository = shift_repository
        self.processing_log_repository = processing_log_repository

    async def list_reviews(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        reason: MessageReason | None = None,
        employee_id: int | None = None,
        object_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[TelegramMessage]:
        _validate_pagination(offset, limit)
        _validate_date_range(date_from, date_to)
        return await self.message_repository.list(
            offset=offset,
            limit=limit,
            status=MessageStatus.REVIEW,
            reason=reason,
            employee_id=employee_id,
            object_id=object_id,
            date_from=date_from,
            date_to=date_to,
        )

    async def confirm(
        self,
        message_id: int,
        data: ReviewConfirmRequest,
        *,
        user_id: int,
    ) -> ReviewConfirmation:
        message = await self._get_review_message(message_id)
        employee_id, object_id, shift_date = self._resolve_confirmation_data(message, data)
        await self._require_active_employee(employee_id)
        await self._require_active_work_object(object_id)

        try:
            existing_shift = await self.shift_repository.get_existing_shift(
                employee_id=employee_id,
                object_id=object_id,
                shift_date=shift_date,
            )
            if existing_shift is not None:
                raise ShiftAlreadyExistsError

            try:
                shift = await self.shift_repository.create(
                    employee_id=employee_id,
                    object_id=object_id,
                    shift_date=shift_date,
                    source_message_id=message.id,
                    confirmed_manually=True,
                    confirmed_by_user_id=user_id,
                )
            except IntegrityError as exc:
                raise ShiftAlreadyExistsError from exc

            message = await self.message_repository.update(
                message,
                {
                    "employee_id": employee_id,
                    "object_id": object_id,
                    "shift_date": shift_date,
                    "status": MessageStatus.ACCEPTED,
                    "reason": None,
                },
            )
            await self.processing_log_repository.create(
                message_id=message.id,
                user_id=user_id,
                action="manual_confirm",
                details=(
                    f"employee_id={employee_id}; object_id={object_id}; "
                    f"shift_date={shift_date.isoformat()}; shift_id={shift.id}"
                ),
            )
            await self.session.commit()
            return ReviewConfirmation(message=message, shift=shift)
        except Exception:
            await self.session.rollback()
            raise

    async def reject(
        self,
        message_id: int,
        data: ReviewRejectRequest,
        *,
        user_id: int,
    ) -> TelegramMessage:
        message = await self._get_review_message(message_id)
        try:
            message = await self.message_repository.update(
                message,
                {"status": MessageStatus.REJECTED},
            )
            await self.processing_log_repository.create(
                message_id=message.id,
                user_id=user_id,
                action="manual_reject",
                details=data.comment,
            )
            await self.session.commit()
            return message
        except Exception:
            await self.session.rollback()
            raise

    async def _get_review_message(self, message_id: int) -> TelegramMessage:
        message = await self.message_repository.get_by_id(message_id)
        if message is None:
            raise TelegramMessageNotFoundError
        if message.status is not MessageStatus.REVIEW:
            raise TelegramMessageNotInReviewError
        return message

    async def _require_active_employee(self, employee_id: int) -> None:
        employee = await self.employee_repository.get_by_id(employee_id)
        if employee is None or not employee.is_active:
            raise EmployeeNotFoundError

    async def _require_active_work_object(self, object_id: int) -> None:
        work_object = await self.work_object_repository.get_by_id(object_id)
        if work_object is None or not work_object.is_active:
            raise WorkObjectNotFoundError

    @staticmethod
    def _resolve_confirmation_data(
        message: TelegramMessage,
        data: ReviewConfirmRequest,
    ) -> tuple[int, int, date]:
        employee_id = data.employee_id if data.employee_id is not None else message.employee_id
        object_id = data.object_id if data.object_id is not None else message.object_id
        shift_date = data.shift_date if data.shift_date is not None else message.shift_date
        missing: list[str] = []
        if employee_id is None:
            missing.append("employee_id")
        if object_id is None:
            missing.append("object_id")
        if shift_date is None:
            missing.append("shift_date")
        if missing or employee_id is None or object_id is None or shift_date is None:
            raise ReviewConfirmationIncompleteError(missing)
        return employee_id, object_id, shift_date
