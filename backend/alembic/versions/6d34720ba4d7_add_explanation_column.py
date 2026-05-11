"""add explanation column to receipts

Revision ID: 6d34720ba4d7
Revises: 210bbc94ba38
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '6d34720ba4d7'
down_revision: Union[str, None] = '210bbc94ba38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('receipts', sa.Column('explanation', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('receipts', 'explanation')
