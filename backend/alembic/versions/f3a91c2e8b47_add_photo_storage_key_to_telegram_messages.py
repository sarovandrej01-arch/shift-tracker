"""add photo storage key to telegram messages

Revision ID: f3a91c2e8b47
Revises: ea5708e7e72d
Create Date: 2026-10-03 16:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a91c2e8b47"
down_revision: Union[str, Sequence[str], None] = "ea5708e7e72d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "telegram_messages",
        sa.Column("photo_storage_key", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("telegram_messages", "photo_storage_key")
