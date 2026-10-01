from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.telegram_message import TelegramMessage
    from app.models.work_object import WorkObject


class Shift(TimestampMixin, Base):
    __tablename__ = "shifts"
    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "object_id",
            "shift_date",
            name="uq_shift_employee_object_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    object_id: Mapped[int] = mapped_column(ForeignKey("work_objects.id"), nullable=False)
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_message_id: Mapped[int | None] = mapped_column(ForeignKey("telegram_messages.id"))
    confirmed_manually: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )

    employee: Mapped[Employee] = relationship(back_populates="shifts")
    work_object: Mapped[WorkObject] = relationship(back_populates="shifts")
    source_message: Mapped[TelegramMessage | None] = relationship(back_populates="shifts")
