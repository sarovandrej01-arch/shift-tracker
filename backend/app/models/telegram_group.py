from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.work_object import WorkObject


class TelegramGroup(TimestampMixin, Base):
    __tablename__ = "telegram_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    object_id: Mapped[int] = mapped_column(ForeignKey("work_objects.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)

    work_object: Mapped[WorkObject] = relationship(back_populates="telegram_groups")
