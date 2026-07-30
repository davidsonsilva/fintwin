"""profile_name_column

Revision ID: a3f7d1c9b4e2
Revises: 59331c899349
Create Date: 2026-07-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f7d1c9b4e2'
down_revision: Union[str, None] = '59331c899349'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _has_column('profiles', 'name'):
        op.add_column('profiles', sa.Column('name', sa.String(length=120), nullable=True))


def downgrade() -> None:
    if _has_column('profiles', 'name'):
        op.drop_column('profiles', 'name')
