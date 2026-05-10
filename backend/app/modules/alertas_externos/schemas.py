"""Alertas externos — schemas Pydantic."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Schemas de entrada (payload das filas RabbitMQ) ──────────────────────────

class AlertaAtivoPayload(BaseModel):
    regiao: str
    descricao: str
    severidade: str  # normal | atencao | critico


class PrevisaoChuvaPayload(BaseModel):
    regiao: str = Field(min_length=1, max_length=100)
    nivel: int = Field(ge=1, le=5)
    descricao: str = Field(min_length=1, max_length=200)
    precipitacao_mm: float = Field(ge=0, le=300)
    timestamp: datetime | None = None


class SituacaoDefesaCivilPayload(BaseModel):
    status: str  # verde | amarelo | laranja | vermelho
    alertas_ativos: list[AlertaAtivoPayload] = Field(default_factory=list, max_length=5)
    timestamp: datetime | None = None


class AlertaDefesaCivilPayload(BaseModel):
    titulo: str = Field(min_length=1, max_length=100)
    descricao: str = Field(min_length=1, max_length=500)
    regiao: str = Field(min_length=1, max_length=100)
    valido_ate: datetime
    timestamp: datetime | None = None


# ── Schemas de saída (endpoint público) ──────────────────────────────────────

class PrevisaoChuvaRead(BaseModel):
    id: int
    regiao: str
    nivel: int
    descricao: str
    precipitacao_mm: float
    timestamp: datetime

    model_config = {"from_attributes": True}


class SituacaoDefesaCivilRead(BaseModel):
    id: int
    status: str
    alertas_ativos: list[Any]
    timestamp: datetime

    model_config = {"from_attributes": True}


class AlertaDefesaCivilRead(BaseModel):
    id: int
    titulo: str
    descricao: str
    regiao: str
    valido_ate: datetime
    timestamp: datetime

    model_config = {"from_attributes": True}


class AlertasExternosRead(BaseModel):
    """Payload completo do endpoint público de alertas externos."""
    situacao_defesa_civil: SituacaoDefesaCivilRead | None = None
    alertas_defesa_civil: list[AlertaDefesaCivilRead] = []
    previsao_chuva: PrevisaoChuvaRead | None = None
