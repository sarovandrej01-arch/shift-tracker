from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import MessageReason, MessageStatus
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.processing_log import ProcessingLog
    from app.models.shift import Shift
    from app.models.work_object import WorkObject


def _enum_values(enum_cls: type[MessageStatus] | type[MessageReason]) -> list[str]:
    return [item.value for item in enum_cls]


class TelegramMessage(TimestampMixin, Base):
    __tablename__ = "telegram_messages"
    __table_args__ = (
        UniqueConstraint(
            "telegram_chat_id",
            "telegram_message_id",
            name="uq_telegram_message_chat_message",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger)
    telegram_username: Mapped[str | None] = mapped_column(String)
    text: Mapped[str | None] = mapped_column(Text)
    caption: Mapped[str | None] = mapped_column(Text)
    photo_file_id: Mapped[str | None] = mapped_column(String)
    photo_storage_key: Mapped[str | None] = mapped_column(String)
    telegram_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    object_id: Mapped[int | None] = mapped_column(ForeignKey("work_objects.id"))
    shift_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus, name="message_status", values_callable=_enum_values),
        nullable=False,
    )
    reason: Mapped[MessageReason | None] = mapped_column(
        Enum(MessageReason, name="message_reason", values_callable=_enum_values),
    )

    employee: Mapped[Employee | None] = relationship(back_populates="telegram_messages")
    work_object: Mapped[WorkObject | None] = relationship(back_populates="telegram_messages")
    shifts: Mapped[list[Shift]] = relationship(back_populates="source_message")
    processing_logs: Mapped[list[ProcessingLog]] = relationship(back_populates="message")
