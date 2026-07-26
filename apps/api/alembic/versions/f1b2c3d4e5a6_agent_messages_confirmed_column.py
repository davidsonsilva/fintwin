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


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    # Idempotente de propósito: um banco que tenha rodado a revisão e4a1f7c9d3b2
    # de uma versão anterior desta branch (quando ela ainda criava a coluna
    # `confirmed` inline) já tem a coluna: adicioná-la de novo quebraria com
    # "duplicate column". Checar antes evita depender de qual estado histórico
    # exato do e4 o banco aplicou (achado do Meta Harness na VS-09).
    if not _has_column('agent_messages', 'confirmed'):
        op.add_column(
            'agent_messages',
            sa.Column('confirmed', sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade() -> None:
    if _has_column('agent_messages', 'confirmed'):
        op.drop_column('agent_messages', 'confirmed')
