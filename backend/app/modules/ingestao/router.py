"""Ingestao router — TASK-42."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.modules.ingestao.schemas import LeituraBatchCreate
from app.modules.ingestao.service import IngestaoService

router = APIRouter()
_settings = get_settings()


async def get_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    """Dependency: validate X-API-Key header for sensor ingestion."""
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header obrigatório",
        )
    if x_api_key != _settings.INGESTAO_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key inválida",
        )
    return x_api_key


@router.post(
    "/leituras",
    status_code=status.HTTP_201_CREATED,
    summary="Ingerir lote de leituras de sensores (máx. 100 por chamada)",
    responses={
        201: {"description": "Leituras inseridas com sucesso"},
        401: {"description": "X-API-Key ausente"},
        403: {"description": "API Key inválida"},
        422: {"description": "Dados inválidos ou sensor_id não encontrado"},
    },
)
async def ingerir_leituras(
    batch: LeituraBatchCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_api_key)],
) -> dict[str, int]:
    service = IngestaoService(session)
    count = await service.processar_lote(batch)
    return {"inseridos": count}
