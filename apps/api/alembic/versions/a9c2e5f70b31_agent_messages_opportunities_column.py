"""agent_messages_opportunities_column

Revision ID: a9c2e5f70b31
Revises: e7d3b5a91c40
Create Date: 2026-08-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9c2e5f70b31'
down_revision: Union[str, None] = 'e7d3b5a91c40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    # Nullable e sem backfill: mensagem gravada antes desta coluna continua
    # sendo lida e renderizada como resposta sem blocos estruturados. Reescrever
    # o histórico para "parecer" que sempre houve oportunidades seria inventar
    # conteúdo que a IA nunca produziu.
    if not _has_column('agent_messages', 'opportunities'):
        op.add_column('agent_messages', sa.Column('opportunities', sa.JSON(), nullable=True))


def downgrade() -> None:
    if _has_column('agent_messages', 'opportunities'):
        op.drop_column('agent_messages', 'opportunities')
