from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, Time, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.shift import Shift
    from app.models.telegram_group import TelegramGroup
    from app.models.telegram_message import TelegramMessage


class WorkObject(TimestampMixin, Base):
    __tablename__ = "work_objects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    shift_start_time: Mapped[time] = mapped_column(Time, nullable=False)
    checkin_before_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    checkin_after_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    timezone: Mapped[str] = mapped_column(
        String,
        default="Europe/Moscow",
        server_default="Europe/Moscow",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)

    telegram_groups: Mapped[list[TelegramGroup]] = relationship(back_populates="work_object")
    shifts: Mapped[list[Shift]] = relationship(back_populates="work_object")
    telegram_messages: Mapped[list[TelegramMessage]] = relationship(back_populates="work_object")
