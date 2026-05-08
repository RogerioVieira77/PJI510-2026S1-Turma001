"""Ingestao schemas — TASK-40."""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FonteAlimentacaoEnum(str, enum.Enum):
    rede = "rede"
    bateria = "bateria"


class BmsNivelEnum(str, enum.Enum):
    normal = "normal"
    alerta = "alerta"
    critico = "critico"


class UnidadeEnum(str, enum.Enum):
    # Unidades do sistema interno
    cm = "cm"
    m3_s = "m3/s"
    mm = "mm"
    pct = "%"
    m3 = "m3"
    # Unidades da fila PJI510 (sensores externos)
    metros = "metros"
    m = "m"            # abreviação usada nas mensagens reais da fila
    m3_s_unicode = "m\u00b3/s"   # m³/s
    mm_h = "mm/h"
    kPa = "kPa"
    celsius = "\u00b0C"          # °C
    hPa = "hPa"
    km_h = "km/h"
    graus = "graus"


class LeituraCreate(BaseModel):
    sensor_id: int = Field(..., gt=0, description="ID do sensor")
    timestamp: datetime = Field(..., description="Momento da leitura (UTC)")
    valor: float = Field(..., description="Valor medido")
    unidade: UnidadeEnum = Field(..., description="Unidade de medida")
    # ── Campos de energia e estado (PJI510) ──────────────────────────────────
    ativo: bool = Field(default=True, description="Sensor ligado/apto para enviar leituras")
    fonte_alimentacao: FonteAlimentacaoEnum | None = Field(default=None, description="Fonte elétrica atual")
    bateria_pct: int | None = Field(default=None, ge=0, le=100, description="Carga da bateria (0–100 %)")
    bms_nivel: BmsNivelEnum | None = Field(default=None, description="Estado de saúde do BMS")

    @field_validator("timestamp")
    @classmethod
    def timestamp_not_future(cls, v: datetime) -> datetime:
        now = datetime.now(tz=timezone.utc)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v > now:
            raise ValueError("timestamp não pode ser no futuro")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sensor_id": 1,
                "timestamp": "2026-05-05T10:00:00Z",
                "valor": 350.5,
                "unidade": "cm",
            }
        }
    )


class LeituraBatchCreate(BaseModel):
    leituras: Annotated[
        list[LeituraCreate],
        Field(min_length=1, max_length=100, description="Lote de leituras (máx. 100)"),
    ]


class LeituraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: int
    timestamp: datetime
    valor: float
