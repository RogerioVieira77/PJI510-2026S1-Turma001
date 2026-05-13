"""Corrige capacidade do Piscinão Romano de 120.000 para 20.000 m³.

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-13 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE reservatorio SET capacidade_m3 = 20000.00 WHERE codigo = 'RES-ROMANO'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE reservatorio SET capacidade_m3 = 120000.00 WHERE codigo = 'RES-ROMANO'"
        )
    )
