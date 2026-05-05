"""migration continuous aggregates e políticas de compressão/retenção

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-05 00:02:00.000000
"""
from __future__ import annotations

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Continuous Aggregate: horário ─────────────────────────────────────────
    op.execute("""
        CREATE MATERIALIZED VIEW leitura_sensor_hourly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 hour', timestamp) AS bucket,
            sensor_id,
            AVG(valor)  AS media,
            MIN(valor)  AS minimo,
            MAX(valor)  AS maximo,
            COUNT(*)    AS total_leituras
        FROM leitura_sensor
        GROUP BY bucket, sensor_id
        WITH NO DATA
    """)

    op.execute("""
        SELECT add_continuous_aggregate_policy(
            'leitura_sensor_hourly',
            start_offset => INTERVAL '3 hours',
            end_offset   => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour'
        )
    """)

    # ── Continuous Aggregate: diário ──────────────────────────────────────────
    op.execute("""
        CREATE MATERIALIZED VIEW leitura_sensor_daily
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', timestamp) AS bucket,
            sensor_id,
            AVG(valor)  AS media,
            MIN(valor)  AS minimo,
            MAX(valor)  AS maximo,
            COUNT(*)    AS total_leituras
        FROM leitura_sensor
        GROUP BY bucket, sensor_id
        WITH NO DATA
    """)

    op.execute("""
        SELECT add_continuous_aggregate_policy(
            'leitura_sensor_daily',
            start_offset => INTERVAL '3 days',
            end_offset   => INTERVAL '1 day',
            schedule_interval => INTERVAL '1 day'
        )
    """)

    # ── Compressão: dado bruto > 7 dias ───────────────────────────────────────
    op.execute("ALTER TABLE leitura_sensor SET (timescaledb.compress, timescaledb.compress_segmentby = 'sensor_id')")
    op.execute("""
        SELECT add_compression_policy('leitura_sensor', INTERVAL '7 days')
    """)

    # ── Retenção: dado bruto 1 ano, climatico 1 ano ───────────────────────────
    op.execute("SELECT add_retention_policy('leitura_sensor', INTERVAL '1 year')")
    op.execute("SELECT add_retention_policy('leitura_climatica', INTERVAL '1 year')")


def downgrade() -> None:
    op.execute("SELECT remove_retention_policy('leitura_climatica', if_exists => TRUE)")
    op.execute("SELECT remove_retention_policy('leitura_sensor', if_exists => TRUE)")
    op.execute("SELECT remove_compression_policy('leitura_sensor', if_exists => TRUE)")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS leitura_sensor_daily")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS leitura_sensor_hourly")
