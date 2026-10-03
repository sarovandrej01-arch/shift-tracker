from aiogram import Dispatcher
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.messages import build_message_router
from app.db.session import async_session_maker
from app.repositories.employee.repository import EmployeeRepository
from app.repositories.processing_log.repository import ProcessingLogRepository
from app.repositories.shift.repository import ShiftRepository
from app.repositories.telegram_group.repository import TelegramGroupRepository
from app.repositories.telegram_message.repository import TelegramMessageRepository
from app.repositories.work_object.repository import WorkObjectRepository
from app.services.message_processing import EmployeeMatcher, MessageProcessor, ShiftDetector
from app.services.storage.base import ObjectStorage


def build_message_processor(session: AsyncSession) -> MessageProcessor:
    return MessageProcessor(
        session=session,
        telegram_message_repository=TelegramMessageRepository(session),
        telegram_group_repository=TelegramGroupRepository(session),
        work_object_repository=WorkObjectRepository(session),
        shift_repository=ShiftRepository(session),
        processing_log_repository=ProcessingLogRepository(session),
        employee_matcher=EmployeeMatcher(EmployeeRepository(session)),
        shift_detector=ShiftDetector(),
    )


def create_dispatcher(storage: ObjectStorage) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(
        build_message_router(
            storage,
            session_factory=async_session_maker,
            processor_factory=build_message_processor,
        )
    )
    return dispatcher
