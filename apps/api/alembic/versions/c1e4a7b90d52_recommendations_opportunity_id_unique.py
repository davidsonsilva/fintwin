"""recommendations_opportunity_id_unique

Revision ID: c1e4a7b90d52
Revises: a9c2e5f70b31
Create Date: 2026-08-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1e4a7b90d52'
down_revision: Union[str, None] = 'a9c2e5f70b31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_INDEX_NAME = 'ix_recommendations_opportunity_id'


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    # Nullable: recomendação do motor não nasce de bloco de oportunidade, e as
    # que já estão gravadas não têm um — nenhuma delas é reescrita.
    #
    # O índice único é o que decide a corrida entre dois cliques simultâneos no
    # mesmo card: revalidar em memória não basta, porque as duas requisições
    # passam pela checagem antes de qualquer INSERT confirmar. Índice único
    # (em vez de UNIQUE constraint) porque tanto sqlite quanto postgres tratam
    # NULLs como distintos aqui, que é o comportamento desejado.
    if not _has_column('recommendations', 'opportunity_id'):
        op.add_column('recommendations', sa.Column('opportunity_id', sa.String(length=80), nullable=True))
    if not _has_index('recommendations', _INDEX_NAME):
        op.create_index(_INDEX_NAME, 'recommendations', ['opportunity_id'], unique=True)


def downgrade() -> None:
    if _has_index('recommendations', _INDEX_NAME):
        op.drop_index(_INDEX_NAME, table_name='recommendations')
    if _has_column('recommendations', 'opportunity_id'):
        op.drop_column('recommendations', 'opportunity_id')
