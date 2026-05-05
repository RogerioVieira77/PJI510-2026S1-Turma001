"""migration inicial — tabelas relacionais base

Revision ID: 0001
Revises:
Create Date: 2026-05-05 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enums ────────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE role_enum AS ENUM ('admin', 'gestor', 'operador')")
    op.execute("CREATE TYPE tipo_sensor_enum AS ENUM ('nivel', 'vazao', 'chuva')")
    op.execute("CREATE TYPE nivel_alerta_enum AS ENUM ('atencao', 'alerta', 'emergencia')")
    op.execute("CREATE TYPE status_alerta_enum AS ENUM ('ativo', 'resolvido')")

    # ── usuario ──────────────────────────────────────────────────────────────
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "gestor", "operador", name="role_enum"),
            nullable=False,
            server_default="operador",
        ),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_usuario_email", "usuario", ["email"])

    # ── reservatorio ─────────────────────────────────────────────────────────
    op.create_table(
        "reservatorio",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(150), nullable=False, unique=True),
        sa.Column("codigo", sa.String(20), nullable=False, unique=True),
        sa.Column("capacidade_m3", sa.Numeric(14, 2), nullable=False),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("descricao", sa.Text, nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reservatorio_codigo", "reservatorio", ["codigo"])

    # ── sensor ───────────────────────────────────────────────────────────────
    op.create_table(
        "sensor",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("reservatorio_id", sa.Integer, sa.ForeignKey("reservatorio.id", ondelete="CASCADE"), nullable=False),
        sa.Column("codigo", sa.String(50), nullable=False, unique=True),
        sa.Column("tipo", sa.Enum("nivel", "vazao", "chuva", name="tipo_sensor_enum"), nullable=False),
        sa.Column("unidade", sa.String(20), nullable=False),
        sa.Column("descricao", sa.Text, nullable=True),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sensor_reservatorio_id", "sensor", ["reservatorio_id"])
    op.create_index("ix_sensor_codigo", "sensor", ["codigo"])

    # ── alerta ───────────────────────────────────────────────────────────────
    op.create_table(
        "alerta",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("reservatorio_id", sa.Integer, sa.ForeignKey("reservatorio.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nivel", sa.Enum("atencao", "alerta", "emergencia", name="nivel_alerta_enum"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ativo", "resolvido", name="status_alerta_enum"),
            nullable=False,
            server_default="ativo",
        ),
        sa.Column("mensagem", sa.Text, nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolvido_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alerta_reservatorio_id", "alerta", ["reservatorio_id"])

    # ── historico_alerta ──────────────────────────────────────────────────────
    op.create_table(
        "historico_alerta",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("alerta_id", sa.Integer, sa.ForeignKey("alerta.id", ondelete="CASCADE"), nullable=False),
        sa.Column("canal", sa.String(30), nullable=False),
        sa.Column("destinatario", sa.String(255), nullable=False),
        sa.Column("sucesso", sa.Boolean, nullable=False),
        sa.Column("erro", sa.Text, nullable=True),
        sa.Column("enviado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_historico_alerta_alerta_id", "historico_alerta", ["alerta_id"])

    # ── push_subscription ─────────────────────────────────────────────────────
    op.create_table(
        "push_subscription",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("endpoint", sa.Text, nullable=False, unique=True),
        sa.Column("p256dh", sa.String(255), nullable=False),
        sa.Column("auth", sa.String(100), nullable=False),
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── email_subscription ───────────────────────────────────────────────────
    op.create_table(
        "email_subscription",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("reservatorio_id", sa.Integer, sa.ForeignKey("reservatorio.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_email_subscription_email", "email_subscription", ["email"])


def downgrade() -> None:
    op.drop_table("email_subscription")
    op.drop_table("push_subscription")
    op.drop_table("historico_alerta")
    op.drop_table("alerta")
    op.drop_table("sensor")
    op.drop_table("reservatorio")
    op.drop_table("usuario")

    op.execute("DROP TYPE IF EXISTS status_alerta_enum")
    op.execute("DROP TYPE IF EXISTS nivel_alerta_enum")
    op.execute("DROP TYPE IF EXISTS tipo_sensor_enum")
    op.execute("DROP TYPE IF EXISTS role_enum")
