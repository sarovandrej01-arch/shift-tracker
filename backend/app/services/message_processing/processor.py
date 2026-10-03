from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MessageReason, MessageStatus
from app.models.shift import Shift
from app.models.telegram_message import TelegramMessage
from app.repositories.processing_log.repository import ProcessingLogRepository
from app.repositories.shift.repository import ShiftRepository
from app.repositories.telegram_group.repository import TelegramGroupRepository
from app.repositories.telegram_message.repository import TelegramMessageRepository
from app.repositories.work_object.repository import WorkObjectRepository
from app.services.message_processing.employee_matcher import EmployeeMatcher, EmployeeMatchStatus
from app.services.message_processing.shift_detector import ShiftDetector, ShiftDetectionStatus


@dataclass(slots=True)
class IncomingTelegramMessage:
    telegram_chat_id: int
    telegram_message_id: int
    telegram_user_id: int | None
    telegram_username: str | None
    text: str | None
    caption: str | None
    photo_file_id: str | None
    telegram_created_at: datetime


@dataclass(slots=True)
class MessageProcessingResult:
    status: MessageStatus
    reason: MessageReason | None
    message: TelegramMessage | None = None
    shift: Shift | None = None


class MessageProcessor:
    def __init__(
        self,
        *,
        session: AsyncSession,
        telegram_message_repository: TelegramMessageRepository,
        telegram_group_repository: TelegramGroupRepository,
        work_object_repository: WorkObjectRepository,
        shift_repository: ShiftRepository,
        processing_log_repository: ProcessingLogRepository,
        employee_matcher: EmployeeMatcher,
        shift_detector: ShiftDetector,
    ) -> None:
        self.session = session
        self.telegram_message_repository = telegram_message_repository
        self.telegram_group_repository = telegram_group_repository
        self.work_object_repository = work_object_repository
        self.shift_repository = shift_repository
        self.processing_log_repository = processing_log_repository
        self.employee_matcher = employee_matcher
        self.shift_detector = shift_detector

    async def process(self, data: IncomingTelegramMessage) -> MessageProcessingResult:
        if data.telegram_created_at.tzinfo is None or data.telegram_created_at.utcoffset() is None:
            raise ValueError("telegram_created_at must be timezone-aware")

        existing = await self.telegram_message_repository.get_by_telegram_message(
            telegram_chat_id=data.telegram_chat_id,
            telegram_message_id=data.telegram_message_id,
        )
        if existing is not None:
            return MessageProcessingResult(
                status=MessageStatus.DUPLICATE,
                reason=MessageReason.MESSAGE_ALREADY_PROCESSED,
                message=existing,
            )

        try:
            return await self._process_new_message(data)
        except Exception:
            await self.session.rollback()
            raise

    async def _process_new_message(self, data: IncomingTelegramMessage) -> MessageProcessingResult:
        message = await self.telegram_message_repository.create(
            telegram_chat_id=data.telegram_chat_id,
            telegram_message_id=data.telegram_message_id,
            telegram_user_id=data.telegram_user_id,
            telegram_username=data.telegram_username,
            text=data.text,
            caption=data.caption,
            photo_file_id=data.photo_file_id,
            telegram_created_at=data.telegram_created_at,
            status=MessageStatus.PROCESSING,
        )
        await self.processing_log_repository.create(
            message_id=message.id,
            action="message_received",
            details=None,
            user_id=None,
        )

        if not data.photo_file_id:
            await self._finish_message(
                message=message,
                status=MessageStatus.REJECTED,
                reason=MessageReason.NO_PHOTO,
                action="rejected",
                details="Message does not contain a photo",
            )
            await self.session.commit()
            return MessageProcessingResult(
                status=MessageStatus.REJECTED,
                reason=MessageReason.NO_PHOTO,
                message=message,
            )

        group = await self.telegram_group_repository.get_by_telegram_chat_id(data.telegram_chat_id)
        if group is None or not group.is_active:
            return await self._review(
                message,
                MessageReason.GROUP_NOT_CONFIGURED,
                "Telegram group is not configured",
            )

        work_object = await self.work_object_repository.get_by_id(group.object_id)
        if work_object is None:
            await self._finish_message(
                message=message,
                status=MessageStatus.ERROR,
                reason=MessageReason.INTERNAL_ERROR,
                action="processing_error",
                details="Work object linked to the Telegram group is missing",
            )
            await self.session.commit()
            return MessageProcessingResult(
                status=MessageStatus.ERROR,
                reason=MessageReason.INTERNAL_ERROR,
                message=message,
            )
        if not work_object.is_active:
            return await self._review(
                message,
                MessageReason.GROUP_NOT_CONFIGURED,
                "Work object is inactive",
            )

        await self.telegram_message_repository.assign_work_object(message, work_object.id)
        await self.processing_log_repository.create(
            message_id=message.id,
            action="work_object_resolved",
            details=f"object_id={work_object.id}",
            user_id=None,
        )

        employee_result = await self.employee_matcher.match(
            telegram_user_id=data.telegram_user_id,
            text=data.text,
            caption=data.caption,
        )
        if employee_result.status is EmployeeMatchStatus.NOT_FOUND:
            await self._finish_message(
                message=message,
                status=MessageStatus.REVIEW,
                reason=MessageReason.EMPLOYEE_NOT_FOUND,
                action="employee_not_found",
            )
            await self.session.commit()
            return MessageProcessingResult(
                status=MessageStatus.REVIEW,
                reason=MessageReason.EMPLOYEE_NOT_FOUND,
                message=message,
            )
        if employee_result.status is EmployeeMatchStatus.AMBIGUOUS:
            candidate_ids = ",".join(str(candidate.id) for candidate in employee_result.candidates)
            await self._finish_message(
                message=message,
                status=MessageStatus.REVIEW,
                reason=MessageReason.EMPLOYEE_AMBIGUOUS,
                action="employee_ambiguous",
                details=f"candidate_ids={candidate_ids}",
            )
            await self.session.commit()
            return MessageProcessingResult(
                status=MessageStatus.REVIEW,
                reason=MessageReason.EMPLOYEE_AMBIGUOUS,
                message=message,
            )

        employee = employee_result.employee
        if employee is None:
            raise ValueError("employee match is missing the employee")

        await self.telegram_message_repository.assign_employee(message, employee.id)
        await self.processing_log_repository.create(
            message_id=message.id,
            action="employee_matched",
            details=f"employee_id={employee.id}; matched_by={employee_result.matched_by}",
            user_id=None,
        )

        shift_detection = self.shift_detector.detect(
            message_datetime=data.telegram_created_at,
            work_object=work_object,
        )
        if shift_detection.status is ShiftDetectionStatus.OUTSIDE_WINDOW:
            return await self._review(
                message,
                MessageReason.OUTSIDE_SHIFT_WINDOW,
                "Message is outside allowed shift window",
            )

        shift_date = shift_detection.shift_date
        if shift_date is None:
            raise ValueError("shift detection is missing the shift date")

        await self.telegram_message_repository.set_shift_date(message, shift_date)
        await self.processing_log_repository.create(
            message_id=message.id,
            action="shift_date_detected",
            details=f"shift_date={shift_date.isoformat()}",
            user_id=None,
        )

        existing_shift = await self.shift_repository.get_existing_shift(
            employee_id=employee.id,
            object_id=work_object.id,
            shift_date=shift_date,
        )
        if existing_shift is not None:
            await self._finish_message(
                message=message,
                status=MessageStatus.DUPLICATE,
                reason=MessageReason.SHIFT_ALREADY_EXISTS,
                action="duplicate_detected",
                details=f"existing_shift_id={existing_shift.id}",
            )
            await self.session.commit()
            return MessageProcessingResult(
                status=MessageStatus.DUPLICATE,
                reason=MessageReason.SHIFT_ALREADY_EXISTS,
                message=message,
            )

        shift = await self.shift_repository.create(
            employee_id=employee.id,
            object_id=work_object.id,
            shift_date=shift_date,
            source_message_id=message.id,
            confirmed_manually=False,
            confirmed_by_user_id=None,
        )
        await self._finish_message(
            message=message,
            status=MessageStatus.ACCEPTED,
            reason=None,
            action="accepted",
            details=f"shift_id={shift.id}",
        )
        await self.session.commit()
        return MessageProcessingResult(
            status=MessageStatus.ACCEPTED,
            reason=None,
            message=message,
            shift=shift,
        )

    async def _review(
        self,
        message: TelegramMessage,
        reason: MessageReason,
        details: str,
    ) -> MessageProcessingResult:
        await self._finish_message(
            message=message,
            status=MessageStatus.REVIEW,
            reason=reason,
            action="review_required",
            details=details,
        )
        await self.session.commit()
        return MessageProcessingResult(status=MessageStatus.REVIEW, reason=reason, message=message)

    async def _finish_message(
        self,
        *,
        message: TelegramMessage,
        status: MessageStatus,
        reason: MessageReason | None,
        action: str,
        details: str | None = None,
    ) -> None:
        await self.telegram_message_repository.set_status(message, status=status, reason=reason)
        await self.processing_log_repository.create(
            message_id=message.id,
            action=action,
            details=details,
            user_id=None,
        )
