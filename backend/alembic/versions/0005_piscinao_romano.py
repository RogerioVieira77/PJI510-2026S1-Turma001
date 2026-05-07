"""Cadastra Piscinão Romano: expande enum, adiciona lat/lng, insere dados reais.

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-07 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Limpar todos os dados fictícios de desenvolvimento ─────────────────
    # ondelete=CASCADE nas FKs: reservatorio → sensor → leitura_sensor
    #                                         → leitura_climatica
    #                                         → alerta → email_subscricao
    op.execute(sa.text("DELETE FROM reservatorio"))

    # ── 2. Adicionar lat/lng à tabela sensor (nullable — retrocompat) ─────────
    op.add_column("sensor", sa.Column("latitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("sensor", sa.Column("longitude", sa.Numeric(10, 7), nullable=True))

    # ── 3. Expandir tipo_sensor_enum ──────────────────────────────────────────
    # ALTER TYPE ADD VALUE não pode ser usado na mesma transação onde os novos
    # valores são utilizados. autocommit_block() faz COMMIT/BEGIN automaticamente.
    with op.get_context().autocommit_block():
        for val in (
            "nivel_agua",
            "pluviometro",
            "temperatura",
            "pressao",
            "umidade",
            "vento_direcao",
            "vento_velocidade",
        ):
            op.execute(sa.text(f"ALTER TYPE tipo_sensor_enum ADD VALUE IF NOT EXISTS '{val}'"))

    # ── 4. Inserir reservatório real ──────────────────────────────────────────
    op.execute(
        sa.text(
            """
            INSERT INTO reservatorio (nome, codigo, capacidade_m3, latitude, longitude, descricao)
            VALUES (
                'Piscinão Romano',
                'RES-ROMANO',
                120000.00,
                -23.4778200,
                -46.3829000,
                'Reservatório de detenção de cheias do Jardim Romano — operado pela PMSP/SIURB'
            )
            """
        )
    )

    # ── 5. Inserir 14 sensores reais com código composto ─────────────────────
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
                    ('SENSOR-RES-001-nivel_agua',        'nivel_agua',       'm',
                     'Sensor de nível — Piscinão Romano Norte',
                     -23.4774480::numeric, -46.3828150::numeric),

                    ('SENSOR-RES-002-nivel_agua',        'nivel_agua',       'm',
                     'Sensor de nível — Piscinão Romano Sul',
                     -23.4775090::numeric, -46.3829760::numeric),

                    ('ESTACAO-MET-001-temperatura',      'temperatura',      '°C',
                     'Temperatura do ar — Estação CEU Três Pontes',
                     -23.4788700::numeric, -46.3812500::numeric),

                    ('ESTACAO-MET-001-pluviometro',      'pluviometro',      'mm',
                     'Chuva acumulada — Estação CEU Três Pontes',
                     -23.4788700::numeric, -46.3812500::numeric),

                    ('ESTACAO-MET-001-umidade',          'umidade',          '%',
                     'Umidade relativa — Estação CEU Três Pontes',
                     -23.4788700::numeric, -46.3812500::numeric),

                    ('ESTACAO-MET-001-pressao',          'pressao',          'hPa',
                     'Pressão atmosférica — Estação CEU Três Pontes',
                     -23.4788700::numeric, -46.3812500::numeric),

                    ('ESTACAO-MET-001-vento_velocidade', 'vento_velocidade', 'km/h',
                     'Velocidade do vento — Estação CEU Três Pontes',
                     -23.4788700::numeric, -46.3812500::numeric),

                    ('ESTACAO-MET-001-vento_direcao',    'vento_direcao',    'graus',
                     'Direção do vento — Estação CEU Três Pontes',
                     -23.4788700::numeric, -46.3812500::numeric),

                    ('ESTACAO-MET-002-temperatura',      'temperatura',      '°C',
                     'Temperatura do ar — Estação Piscinão Romano',
                     -23.4774720::numeric, -46.3829240::numeric),

                    ('ESTACAO-MET-002-pluviometro',      'pluviometro',      'mm',
                     'Chuva acumulada — Estação Piscinão Romano',
                     -23.4774720::numeric, -46.3829240::numeric),

                    ('ESTACAO-MET-002-umidade',          'umidade',          '%',
                     'Umidade relativa — Estação Piscinão Romano',
                     -23.4774720::numeric, -46.3829240::numeric),

                    ('ESTACAO-MET-002-pressao',          'pressao',          'hPa',
                     'Pressão atmosférica — Estação Piscinão Romano',
                     -23.4774720::numeric, -46.3829240::numeric),

                    ('ESTACAO-MET-002-vento_velocidade', 'vento_velocidade', 'km/h',
                     'Velocidade do vento — Estação Piscinão Romano',
                     -23.4774720::numeric, -46.3829240::numeric),

                    ('ESTACAO-MET-002-vento_direcao',    'vento_direcao',    'graus',
                     'Direção do vento — Estação Piscinão Romano',
                     -23.4774720::numeric, -46.3829240::numeric)
                ) AS s(codigo, tipo, unidade, descricao, latitude, longitude)
            """
        )
    )


def downgrade() -> None:
    # Remove dados inseridos por esta migration
    op.execute(sa.text("DELETE FROM reservatorio WHERE codigo = 'RES-ROMANO'"))

    op.drop_column("sensor", "longitude")
    op.drop_column("sensor", "latitude")

    # Remoção de valores de ENUM em PostgreSQL requer recriação do tipo
    # com renaming — operação manual não suportada aqui.
    # Execute manualmente se necessário fazer downgrade completo.
