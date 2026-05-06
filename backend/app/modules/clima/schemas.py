"""Clima schemas — TASK-111."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PrevisaoClimatica(BaseModel):
    """Resultado normalizado retornado pelos clients HTTP externos."""

    temperatura_c: Decimal | None = None
    umidade_pct: Decimal | None = None
    precipitacao_mm: Decimal | None = None
    velocidade_vento_ms: Decimal | None = None
    condicao: str | None = None


class PrevisaoClimaticaRead(PrevisaoClimatica):
    """Schema de resposta da API — mapeado da ORM LeituraClimatica."""

    id: int
    reservatorio_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
