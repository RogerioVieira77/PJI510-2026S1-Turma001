"""Ingestao models."""
from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoSensorEnum(str, enum.Enum):
    nivel = "nivel"
    vazao = "vazao"
    chuva = "chuva"
    # Tipos reais PJI510
    nivel_agua = "nivel_agua"
    pluviometro = "pluviometro"
    temperatura = "temperatura"
    pressao = "pressao"
    umidade = "umidade"
    vento_direcao = "vento_direcao"
    vento_velocidade = "vento_velocidade"


class Reservatorio(Base):
    __tablename__ = "reservatorio"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    capacidade_m3: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sensores: Mapped[list[Sensor]] = relationship("Sensor", back_populates="reservatorio")


class Sensor(Base):
    __tablename__ = "sensor"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reservatorio_id: Mapped[int] = mapped_column(
        ForeignKey("reservatorio.id", ondelete="CASCADE"), nullable=False, index=True
    )
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    tipo: Mapped[TipoSensorEnum] = mapped_column(
        Enum(TipoSensorEnum, name="tipo_sensor_enum"), nullable=False
    )
    unidade: Mapped[str] = mapped_column(String(20), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)

    reservatorio: Mapped[Reservatorio] = relationship("Reservatorio", back_populates="sensores")


class LeituraSensor(Base):
    """Hypertable TimescaleDB — particionada por timestamp."""

    __tablename__ = "leitura_sensor"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sensor_id: Mapped[int] = mapped_column(
        ForeignKey("sensor.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, nullable=False
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    nivel_percentual: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    # ── Campos de energia e estado (PJI510) ───────────────────────────────────
    fonte_alimentacao: Mapped[str | None] = mapped_column(String(10), nullable=True)
    bateria_pct: Mapped[int | None] = mapped_column(SmallInteger(), nullable=True)
    bms_nivel: Mapped[str | None] = mapped_column(String(10), nullable=True)

    __table_args__ = (
        Index("ix_leitura_sensor_sensor_ts", "sensor_id", "timestamp"),
    )

