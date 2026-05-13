"""Cadastra 5 bombas de drenagem do Piscinão Romano.

Adiciona o valor 'estado_bomba' ao enum tipo_sensor_enum e insere
os 5 sensores BOMBA-DRE-001..005 vinculados ao RES-ROMANO.

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-13 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Expandir tipo_sensor_enum com 'estado_bomba' ───────────────────────
    # ALTER TYPE ADD VALUE não pode ser executado dentro de uma transação ativa.
    with op.get_context().autocommit_block():
        op.execute(
            sa.text("ALTER TYPE tipo_sensor_enum ADD VALUE IF NOT EXISTS 'estado_bomba'")
        )

    # ── 2. Inserir os 5 sensores de bomba vinculados ao Piscinão Romano ────────
    op.execute(
        sa.text(
            """
            INSERT INTO sensor
                (reservatorio_id, codigo, tipo, unidade, descricao, ativo, latitude, longitude)
            SELECT
                r.id,
                s.codigo,
                s.tipo::tipo_sensor_enum,
                s.unidade,
                s.descricao,
                TRUE,
                s.latitude,
                s.longitude
            FROM
                (SELECT id FROM reservatorio WHERE codigo = 'RES-ROMANO') r,
                (VALUES
                    ('BOMBA-DRE-001-estado_bomba', 'estado_bomba', 'bool',
                     'Bomba de Drenagem 1 — Piscinão Romano',
                     -23.477310::numeric, -46.382610::numeric),

                    ('BOMBA-DRE-002-estado_bomba', 'estado_bomba', 'bool',
                     'Bomba de Drenagem 2 — Piscinão Romano',
                     -23.477380::numeric, -46.382680::numeric),

                    ('BOMBA-DRE-003-estado_bomba', 'estado_bomba', 'bool',
                     'Bomba de Drenagem 3 — Piscinão Romano',
                     -23.477450::numeric, -46.382760::numeric),

                    ('BOMBA-DRE-004-estado_bomba', 'estado_bomba', 'bool',
                     'Bomba de Drenagem 4 — Piscinão Romano',
                     -23.477520::numeric, -46.382830::numeric),

                    ('BOMBA-DRE-005-estado_bomba', 'estado_bomba', 'bool',
                     'Bomba de Drenagem 5 — Piscinão Romano',
                     -23.477590::numeric, -46.382910::numeric)
                ) AS s(codigo, tipo, unidade, descricao, latitude, longitude)
            ON CONFLICT (codigo) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    # Remove os 5 sensores (cascata remove as leituras)
    op.execute(
        sa.text(
            """
            DELETE FROM sensor
            WHERE codigo IN (
                'BOMBA-DRE-001-estado_bomba',
                'BOMBA-DRE-002-estado_bomba',
                'BOMBA-DRE-003-estado_bomba',
                'BOMBA-DRE-004-estado_bomba',
                'BOMBA-DRE-005-estado_bomba'
            )
            """
        )
    )
    # Nota: não é possível remover valores de um enum PostgreSQL sem recriar o tipo.
    # O valor 'estado_bomba' permanece no enum após o downgrade.
