"""Alertas schemas — TASK-60."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.modules.alertas.models import NivelAlertaEnum, StatusAlertaEnum


class AlertaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reservatorio_id: int
    nivel: NivelAlertaEnum
    status: StatusAlertaEnum
    mensagem: str
    criado_em: datetime
    resolvido_em: datetime | None


class PushSubscribeRequest(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    usuario_id: int | None = None


class EmailSubscribeRequest(BaseModel):
    email: EmailStr
    reservatorio_id: int | None = None

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()
