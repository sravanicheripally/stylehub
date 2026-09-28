"""Add seller ownership to products

Revision ID: ddc8a5b27ea1
Revises: 9d2e3f4a5b6c
Create Date: 2026-09-25 21:48:47.685409

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ddc8a5b27ea1'
down_revision: Union[str, Sequence[str], None] = '9d2e3f4a5b6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'products',
        sa.Column(
            'seller_id',
            sa.Integer(),
            nullable=True
        )
    )

    op.create_foreign_key(
        'fk_products_seller_id_users',
        'products',
        'users',
        ['seller_id'],
        ['id']
    )

def downgrade() -> None:
    op.drop_constraint(
        'fk_products_seller_id_users',
        'products',
        type_='foreignkey'
    )

    op.drop_column(
        'products',
        'seller_id'
    )
