"""Adiciona coluna condicao em leitura_climatica

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-05 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "leitura_climatica",
        sa.Column("condicao", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("leitura_climatica", "condicao")
