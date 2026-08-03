"""opportunity_analyses

Revision ID: d5c8a1b3f902
Revises: a3f7d1c9b4e2
Create Date: 2026-08-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5c8a1b3f902'
down_revision: Union[str, None] = 'a3f7d1c9b4e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "opportunity_analyses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("scenario", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("selected_scenario", sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_opportunity_analyses_profile_generated",
        "opportunity_analyses",
        ["profile_id", "generated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_opportunity_analyses_profile_generated", table_name="opportunity_analyses")
    op.drop_table("opportunity_analyses")
