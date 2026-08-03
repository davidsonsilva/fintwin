"""recommendations_registry

Substitui `opportunity_analyses` pelo registro de recomendações com ciclo de
vida (pending/approved/rejected/expired/superseded), origem (motor ou conversa)
e encadeamento de versões.

A tabela anterior nasceu na mesma data e nunca saiu do ambiente local, então a
migração recria em vez de converter — não há histórico a preservar.

Revision ID: e7d3b5a91c40
Revises: d5c8a1b3f902
Create Date: 2026-08-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7d3b5a91c40'
down_revision: Union[str, None] = 'd5c8a1b3f902'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_opportunity_analyses_profile_generated", table_name="opportunity_analyses")
    op.drop_table("opportunity_analyses")

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("scenario", sa.String(length=30), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("selected_scenario", sa.String(length=30), nullable=True),
        sa.Column("supersedes_id", sa.String(length=36), nullable=True),
        sa.Column("superseded_by_id", sa.String(length=36), nullable=True),
        sa.Column("plan_id", sa.String(length=36), nullable=True),
        sa.Column("conversation_id", sa.String(length=36), nullable=True),
        sa.Column("message_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # O card Insight pergunta sempre a mesma coisa: qual a pendente mais nova
    # deste perfil.
    op.create_index(
        "ix_recommendations_profile_status_generated",
        "recommendations",
        ["profile_id", "status", "generated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_recommendations_profile_status_generated", table_name="recommendations")
    op.drop_table("recommendations")

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
