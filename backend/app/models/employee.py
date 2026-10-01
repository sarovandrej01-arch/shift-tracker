from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.shift import Shift
    from app.models.telegram_message import TelegramMessage


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    personnel_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    telegram_username: Mapped[str | None] = mapped_column(String)
    callsign: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)

    shifts: Mapped[list[Shift]] = relationship(back_populates="employee")
    telegram_messages: Mapped[list[TelegramMessage]] = relationship(back_populates="employee")
