"""Alertas externos — router público."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.alertas_externos import service as svc
from app.modules.alertas_externos.schemas import AlertasExternosRead

publico_alertas_router = APIRouter()


@publico_alertas_router.get("/alertas-externos", response_model=AlertasExternosRead)
async def alertas_externos(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AlertasExternosRead:
    """Retorna previsão de chuva, situação e alertas da Defesa Civil (sem auth)."""
    return await svc.get_alertas_externos(session)
