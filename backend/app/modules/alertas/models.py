"""Alertas models."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NivelAlertaEnum(str, enum.Enum):
    atencao = "atencao"       # 60%
    alerta = "alerta"         # 80%
    emergencia = "emergencia" # 95%


class StatusAlertaEnum(str, enum.Enum):
    ativo = "ativo"
    resolvido = "resolvido"


class Alerta(Base):
    __tablename__ = "alerta"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reservatorio_id: Mapped[int] = mapped_column(
        ForeignKey("reservatorio.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nivel: Mapped[NivelAlertaEnum] = mapped_column(
        Enum(NivelAlertaEnum, name="nivel_alerta_enum"), nullable=False
    )
    status: Mapped[StatusAlertaEnum] = mapped_column(
        Enum(StatusAlertaEnum, name="status_alerta_enum"),
        nullable=False,
        default=StatusAlertaEnum.ativo,
    )
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolvido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HistoricoAlerta(Base):
    __tablename__ = "historico_alerta"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alerta_id: Mapped[int] = mapped_column(
        ForeignKey("alerta.id", ondelete="CASCADE"), nullable=False, index=True
    )
    canal: Mapped[str] = mapped_column(String(30), nullable=False)  # webpush | email
    destinatario: Mapped[str] = mapped_column(String(255), nullable=False)
    sucesso: Mapped[bool] = mapped_column(nullable=False)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)
    enviado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PushSubscription(Base):
    __tablename__ = "push_subscription"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    p256dh: Mapped[str] = mapped_column(String(255), nullable=False)
    auth: Mapped[str] = mapped_column(String(100), nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EmailSubscription(Base):
    __tablename__ = "email_subscription"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    reservatorio_id: Mapped[int | None] = mapped_column(
        ForeignKey("reservatorio.id", ondelete="SET NULL"), nullable=True
    )
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

