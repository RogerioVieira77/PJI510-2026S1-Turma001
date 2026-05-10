"""Adiciona profundidade_m ao reservatorio.

Novo campo:
  - profundidade_m  NUMERIC(5,2)  NOT NULL  DEFAULT 8.0

Profundidade real do Piscinão Romano: 8 metros.
Esse valor é o denominador correto para calcular o percentual de ocupação
a partir das leituras dos sensores de nível (SENSOR-RES-001, SENSOR-RES-002),
que enviam o valor em metros indicando quantos metros de água há no reservatório.

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-10 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adiciona coluna com default para todos os reservatórios existentes
    op.add_column(
        "reservatorio",
        sa.Column(
            "profundidade_m",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="8.0",
        ),
    )

    # Define explicitamente 8.0 m para o Piscinão Romano
    op.execute(
        sa.text(
            "UPDATE reservatorio SET profundidade_m = 8.0 WHERE codigo = 'RES-ROMANO'"
        )
    )


def downgrade() -> None:
    op.drop_column("reservatorio", "profundidade_m")
