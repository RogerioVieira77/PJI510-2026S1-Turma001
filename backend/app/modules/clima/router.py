"""Clima router \u2014 TASK-111.

Montado em /api/v1/reservatorios, expondo GET /{id}/clima.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.clima.schemas import PrevisaoClimaticaRead
from app.modules.clima.service import get_latest_clima

router = APIRouter()


@router.get(
    "/{reservatorio_id}/clima",
    response_model=PrevisaoClimaticaRead,
    summary="Dados clim\u00e1ticos mais recentes do reservat\u00f3rio",
)
async def get_clima(
    reservatorio_id: int,
    session: AsyncSession = Depends(get_db),
) -> PrevisaoClimaticaRead:
    leitura = await get_latest_clima(reservatorio_id, session)
    if leitura is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum dado clim\u00e1tico dispon\u00edvel para este reservat\u00f3rio.",
        )
    return PrevisaoClimaticaRead.model_validate(leitura)
