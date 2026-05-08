"""Dashboard schemas — EPIC-07."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ReservatorioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    codigo: str
    capacidade_m3: Decimal
    latitude: Decimal
    longitude: Decimal
    descricao: str | None = None


class ReservatorioSummary(ReservatorioRead):
    """ReservatorioRead enriched with current level and status."""

    nivel_pct: float | None = None
    status: str | None = None
    ultima_atualizacao: datetime | None = None


class StatusReservatorio(BaseModel):
    reservatorio_id: int
    nivel_cm: float
    nivel_pct: float
    volume_m3: float
    taxa_cm_min: float
    tempo_transbordo_min: float | None
    status: str
    divergencia_sensores: bool
    timestamp: str


class PontoHistorico(BaseModel):
    bucket: datetime
    media: float
    minimo: float
    maximo: float


class StatusPublico(BaseModel):
    id: int
    nome: str
    status: str
    nivel_pct: float
    ultima_atualizacao: str | None = None


class LeituraPublica(BaseModel):
    """Última leitura de um único sensor de nível, para o dashboard público."""
    sensor_id: int
    codigo: str
    descricao: str
    valor: float | None = None
    unidade: str | None = None
    timestamp: datetime | None = None


class EstacaoPublica(BaseModel):
    """Todas as últimas leituras de uma estação meteorológica, agrupadas."""
    codigo_estacao: str
    descricao: str
    temperatura: float | None = None
    umidade: float | None = None
    pressao: float | None = None
    pluviometro: float | None = None
    vento_velocidade: float | None = None
    vento_direcao: float | None = None
    timestamp: datetime | None = None


class LeituraSensoresPublico(BaseModel):
    """Payload completo do endpoint público de leituras."""
    sensores_nivel: list[LeituraPublica]
    estacoes: list[EstacaoPublica]
    atualizado_em: datetime
