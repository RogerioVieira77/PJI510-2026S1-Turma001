"""Clima models."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LeituraClimatica(Base):
    """Hypertable TimescaleDB — dados meteorológicos do OpenWeather."""

    __tablename__ = "leitura_climatica"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reservatorio_id: Mapped[int] = mapped_column(
        ForeignKey("reservatorio.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    temperatura_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    umidade_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    precipitacao_mm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    velocidade_vento_ms: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    condicao: Mapped[str | None] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_leitura_climatica_res_ts", "reservatorio_id", "timestamp"),
    )

