"""Alertas externos — modelos SQLAlchemy."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, JSON, Numeric, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PrevisaoChuva(Base):
    __tablename__ = "previsao_chuva"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    regiao: Mapped[str] = mapped_column(String(100), nullable=False)
    nivel: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-5
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    precipitacao_mm: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SituacaoDefesaCivil(Base):
    __tablename__ = "situacao_defesa_civil"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # verde/amarelo/laranja/vermelho
    alertas_ativos: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AlertaDefesaCivil(Base):
    __tablename__ = "alerta_defesa_civil"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    regiao: Mapped[str] = mapped_column(String(100), nullable=False)
    valido_ate: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
