"""Ingestao schemas — TASK-40."""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UnidadeEnum(str, enum.Enum):
    cm = "cm"
    m3_s = "m3/s"
    mm = "mm"
    pct = "%"
    m3 = "m3"


class LeituraCreate(BaseModel):
    sensor_id: int = Field(..., gt=0, description="ID do sensor")
    timestamp: datetime = Field(..., description="Momento da leitura (UTC)")
    valor: float = Field(..., ge=0.0, description="Valor medido (não negativo)")
    unidade: UnidadeEnum = Field(..., description="Unidade de medida")

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
