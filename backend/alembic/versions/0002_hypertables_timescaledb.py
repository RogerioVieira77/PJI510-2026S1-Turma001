"""migration hypertables TimescaleDB — leitura_sensor e leitura_climatica

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-05 00:01:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Garante extensão TimescaleDB
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")

    # ── leitura_sensor ────────────────────────────────────────────────────────
    op.create_table(
        "leitura_sensor",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("sensor_id", sa.Integer, sa.ForeignKey("sensor.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valor", sa.Numeric(10, 3), nullable=False),
        sa.Column("nivel_percentual", sa.Numeric(5, 2), nullable=True),
    )
    op.create_index("ix_leitura_sensor_sensor_ts", "leitura_sensor", ["sensor_id", "timestamp"])
    # Converte para hypertable (chunk de 7 dias)
    op.execute(
        "SELECT create_hypertable('leitura_sensor', 'timestamp', "
        "chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE)"
    )

    # ── leitura_climatica ─────────────────────────────────────────────────────
    op.create_table(
        "leitura_climatica",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("reservatorio_id", sa.Integer, sa.ForeignKey("reservatorio.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperatura_c", sa.Numeric(5, 2), nullable=True),
        sa.Column("umidade_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("precipitacao_mm", sa.Numeric(7, 2), nullable=True),
        sa.Column("velocidade_vento_ms", sa.Numeric(6, 2), nullable=True),
    )
    op.create_index("ix_leitura_climatica_res_ts", "leitura_climatica", ["reservatorio_id", "timestamp"])
    op.execute(
        "SELECT create_hypertable('leitura_climatica', 'timestamp', "
        "chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE)"
    )


def downgrade() -> None:
    op.drop_table("leitura_climatica")
    op.drop_table("leitura_sensor")
