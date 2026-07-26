"""agent_messages_confirmed_column

Revision ID: f1b2c3d4e5a6
Revises: e4a1f7c9d3b2
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1b2c3d4e5a6'
down_revision: Union[str, None] = 'e4a1f7c9d3b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'agent_messages',
        sa.Column('confirmed', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('agent_messages', 'confirmed')
