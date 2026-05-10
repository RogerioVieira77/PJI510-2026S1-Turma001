"""Cria tabelas para alertas externos: previsao_chuva, situacao_defesa_civil, alerta_defesa_civil.

Essas tabelas armazenam dados consumidos das novas filas RabbitMQ do PJI510:
  - previsoes.fila        → previsao_chuva
  - defesa.situacao.fila  → situacao_defesa_civil
  - defesa.alertas.fila   → alerta_defesa_civil

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-10 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Previsão de Chuva ─────────────────────────────────────────────────────
    op.create_table(
        "previsao_chuva",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("regiao", sa.String(100), nullable=False),
        sa.Column("nivel", sa.SmallInteger, nullable=False),          # 1-5
        sa.Column("descricao", sa.String(200), nullable=False),
        sa.Column("precipitacao_mm", sa.Numeric(6, 2), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_previsao_chuva_timestamp", "previsao_chuva", ["timestamp"])

    # ── Situação Defesa Civil ─────────────────────────────────────────────────
    op.create_table(
        "situacao_defesa_civil",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("status", sa.String(20), nullable=False),           # verde/amarelo/laranja/vermelho
        sa.Column("alertas_ativos", sa.JSON, nullable=False, server_default="[]"),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_situacao_defesa_civil_timestamp", "situacao_defesa_civil", ["timestamp"])

    # ── Alerta Defesa Civil ───────────────────────────────────────────────────
    op.create_table(
        "alerta_defesa_civil",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("titulo", sa.String(100), nullable=False),
        sa.Column("descricao", sa.String(500), nullable=False),
        sa.Column("regiao", sa.String(100), nullable=False),
        sa.Column("valido_ate", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_alerta_defesa_civil_valido_ate", "alerta_defesa_civil", ["valido_ate"])
    op.create_index("ix_alerta_defesa_civil_timestamp", "alerta_defesa_civil", ["timestamp"])


def downgrade() -> None:
    op.drop_table("alerta_defesa_civil")
    op.drop_table("situacao_defesa_civil")
    op.drop_table("previsao_chuva")
