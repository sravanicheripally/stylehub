"""Add server defaults for category fields

Revision ID: 8c1d2e3f4a5b
Revises: 072f25b9f8a5
Create Date: 2026-09-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c1d2e3f4a5b"
down_revision: Union[str, Sequence[str], None] = "072f25b9f8a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "categories",
        "is_active",
        existing_type=sa.Boolean(),
        server_default=sa.true(),
    )
    op.alter_column(
        "categories",
        "created_at",
        existing_type=sa.DateTime(),
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )


def downgrade() -> None:
    op.alter_column(
        "categories",
        "created_at",
        existing_type=sa.DateTime(),
        server_default=None,
    )
    op.alter_column(
        "categories",
        "is_active",
        existing_type=sa.Boolean(),
        server_default=None,
    )
