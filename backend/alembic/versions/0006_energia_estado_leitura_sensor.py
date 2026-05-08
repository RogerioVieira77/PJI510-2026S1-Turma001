"""Adiciona campos de energia e estado à leitura_sensor.

Novos campos:
  - fonte_alimentacao  VARCHAR(10)  NULL  ('rede' | 'bateria')
  - bateria_pct        SMALLINT     NULL  (0..100)
  - bms_nivel          VARCHAR(10)  NULL  ('normal' | 'alerta' | 'critico')

O campo `ativo` é um controle de envio no simulador/consumer — não é
persistido nesta tabela; o flag operacional já existe em `sensor.ativo`.

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-07 00:02:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "leitura_sensor",
        sa.Column(
            "fonte_alimentacao",
            sa.String(10),
            nullable=True,
            comment="Fonte elétrica do sensor no momento da leitura: rede | bateria",
        ),
    )
    op.add_column(
        "leitura_sensor",
        sa.Column(
            "bateria_pct",
            sa.SmallInteger(),
            nullable=True,
            comment="Carga da bateria de emergência (0–100 %)",
        ),
    )
    op.add_column(
        "leitura_sensor",
        sa.Column(
            "bms_nivel",
            sa.String(10),
            nullable=True,
            comment="Estado de saúde informado pelo BMS: normal | alerta | critico",
        ),
    )

    # Restrições CHECK para garantir integridade nos valores controlados
    op.create_check_constraint(
        "ck_leitura_sensor_fonte_alimentacao",
        "leitura_sensor",
        "fonte_alimentacao IS NULL OR fonte_alimentacao IN ('rede', 'bateria')",
    )
    op.create_check_constraint(
        "ck_leitura_sensor_bateria_pct",
        "leitura_sensor",
        "bateria_pct IS NULL OR (bateria_pct >= 0 AND bateria_pct <= 100)",
    )
    op.create_check_constraint(
        "ck_leitura_sensor_bms_nivel",
        "leitura_sensor",
        "bms_nivel IS NULL OR bms_nivel IN ('normal', 'alerta', 'critico')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_leitura_sensor_bms_nivel", "leitura_sensor", type_="check"
    )
    op.drop_constraint(
        "ck_leitura_sensor_bateria_pct", "leitura_sensor", type_="check"
    )
    op.drop_constraint(
        "ck_leitura_sensor_fonte_alimentacao", "leitura_sensor", type_="check"
    )
    op.drop_column("leitura_sensor", "bms_nivel")
    op.drop_column("leitura_sensor", "bateria_pct")
    op.drop_column("leitura_sensor", "fonte_alimentacao")
