"""Add server defaults for product fields

Revision ID: 9d2e3f4a5b6c
Revises: 8c1d2e3f4a5b
Create Date: 2026-09-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d2e3f4a5b6c"
down_revision: Union[str, Sequence[str], None] = "8c1d2e3f4a5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "products",
        "is_active",
        existing_type=sa.Boolean(),
        server_default=sa.true(),
    )
    op.alter_column(
        "products",
        "created_at",
        existing_type=sa.DateTime(),
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )
    op.alter_column(
        "products",
        "updated_at",
        existing_type=sa.DateTime(),
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )


def downgrade() -> None:
    op.alter_column(
        "products",
        "updated_at",
        existing_type=sa.DateTime(),
        server_default=None,
    )
    op.alter_column(
        "products",
        "created_at",
        existing_type=sa.DateTime(),
        server_default=None,
    )
    op.alter_column(
        "products",
        "is_active",
        existing_type=sa.Boolean(),
        server_default=None,
    )
