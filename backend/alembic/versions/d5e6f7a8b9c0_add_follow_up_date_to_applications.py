"""add follow_up_date to applications

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-06-30 15:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('follow_up_date', sa.Date(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.drop_column('follow_up_date')
