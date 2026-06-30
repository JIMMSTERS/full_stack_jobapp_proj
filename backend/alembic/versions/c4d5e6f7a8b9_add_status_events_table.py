"""add status_events table

Revision ID: c4d5e6f7a8b9
Revises: 07253e632dc6
Create Date: 2026-06-30 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = '07253e632dc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'status_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('from_status', sa.String(length=50), nullable=True),
        sa.Column('to_status', sa.String(length=50), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('status_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_status_events_id'), ['id'], unique=False)
        batch_op.create_index(
            batch_op.f('ix_status_events_application_id'), ['application_id'], unique=False
        )

    # Backfill an initial "created" event for every existing application so
    # their timelines are not empty after this migration.
    op.execute(
        """
        INSERT INTO status_events (application_id, from_status, to_status, created_at)
        SELECT id, NULL, status, created_at FROM applications
        """
    )


def downgrade() -> None:
    with op.batch_alter_table('status_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_status_events_application_id'))
        batch_op.drop_index(batch_op.f('ix_status_events_id'))

    op.drop_table('status_events')
