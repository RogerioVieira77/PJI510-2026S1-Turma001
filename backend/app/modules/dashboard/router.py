"""Dashboard router — EPIC-07 (TASK-70/71/72/73)."""
from __future__ import annotations

import json
from typing import Annotated

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import decode_token
from app.database import get_db
from app.dependencies import CurrentUser
from app.modules.alertas.repository import AlertaRepository
from app.modules.alertas.schemas import AlertaRead
from app.modules.dashboard import service as svc
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schemas import (
    PontoHistorico,
    ReservatorioRead,
    ReservatorioSummary,
    StatusPublico,
    StatusReservatorio,
    LeituraSensoresPublico,
)

log = structlog.get_logger()
settings = get_settings()

# ── REST: /api/v1/reservatorios ───────────────────────────────────────────────
router = APIRouter()

# ── REST: /api/v1/publico ───────────────────────────────────────────────────
publico_router = APIRouter()

# ── WebSocket: /ws ─────────────────────────────────────────────────────────────
ws_router = APIRouter()

_PERIODOS_VALIDOS = {"1h", "6h", "24h", "7d", "30d"}


# ── Reservatórios ────────────────────────────────────────────────────────────

@router.get("", response_model=list[ReservatorioSummary])
async def listar_reservatorios(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[ReservatorioSummary]:
    return await svc.list_reservatorios(session)


@router.get("/{reservatorio_id}", response_model=ReservatorioRead)
async def detalhe_reservatorio(
    reservatorio_id: int,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReservatorioRead:
    repo = DashboardRepository(session)
    r = await repo.get_by_id(reservatorio_id)
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservatório não encontrado",
        )
    return ReservatorioRead.model_validate(r)


@router.get("/{reservatorio_id}/status", response_model=StatusReservatorio)
async def status_reservatorio(
    reservatorio_id: int,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> StatusReservatorio:
    result = await svc.get_status(reservatorio_id, session)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservatório não encontrado ou sem dados",
        )
    return result


@router.get("/{reservatorio_id}/historico", response_model=list[PontoHistorico])
async def historico_reservatorio(
    reservatorio_id: int,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    periodo: str = Query("24h", description="1h | 6h | 24h | 7d | 30d"),
) -> list[PontoHistorico]:
    if periodo not in _PERIODOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"periodo deve ser um de: {', '.join(sorted(_PERIODOS_VALIDOS))}",
        )
    return await svc.get_historico(reservatorio_id, periodo, session)


@router.get("/{reservatorio_id}/alertas", response_model=list[AlertaRead])
async def alertas_reservatorio(
    reservatorio_id: int,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[AlertaRead]:
    repo = AlertaRepository(session)
    alertas = await repo.list_alertas(
        reservatorio_id=reservatorio_id,
        nivel=None,
        start=None,
        end=None,
        skip=skip,
        limit=limit,
    )
    return [AlertaRead.model_validate(a) for a in alertas]


# ── Público ─────────────────────────────────────────────────────────────────

@publico_router.get("/status", response_model=list[StatusPublico])
async def status_publico(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[StatusPublico]:
    """Status simplificado de todos os reservatórios (sem auth, cache 30s)."""
    return await svc.get_publico_status(session)


@publico_router.get("/leituras/{reservatorio_id}", response_model=LeituraSensoresPublico)
async def leituras_publico(
    reservatorio_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LeituraSensoresPublico:
    """Últimas leituras de sensores de nível e estações meteorológicas (sem auth)."""
    return await svc.get_leituras_publico(reservatorio_id, session)


# ── WebSocket ────────────────────────────────────────────────────────────────

@ws_router.websocket("/dashboard/{reservatorio_id}")
async def ws_dashboard(
    websocket: WebSocket,
    reservatorio_id: int,
    token: str | None = Query(None),
) -> None:
    """WebSocket técnico: requer JWT válido no query param ?token= (TASK-72)."""
    if not token:
        await websocket.close(code=4001, reason="Unauthorized: token não fornecido")
        return
    try:
        decode_token(token, expected_type="access")
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized: token inválido ou expirado")
        return

    await websocket.accept()
    log.info("ws.dashboard.conectado", reservatorio_id=reservatorio_id)

    redis_client = aioredis.from_url(str(settings.REDIS_URL), decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"status_reservatorio:{reservatorio_id}")
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                await websocket.send_text(message["data"])
            except (WebSocketDisconnect, Exception):
                break
    finally:
        await pubsub.unsubscribe(f"status_reservatorio:{reservatorio_id}")
        await redis_client.aclose()
        log.info("ws.dashboard.desconectado", reservatorio_id=reservatorio_id)


@ws_router.websocket("/publico/{reservatorio_id}")
async def ws_publico(
    websocket: WebSocket,
    reservatorio_id: int,
) -> None:
    """WebSocket público: sem auth, campos limitados (TASK-73)."""
    await websocket.accept()
    log.info("ws.publico.conectado", reservatorio_id=reservatorio_id)

    redis_client = aioredis.from_url(str(settings.REDIS_URL), decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"status_reservatorio:{reservatorio_id}")
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                data = json.loads(message["data"])
                public_payload = json.dumps(
                    {
                        "status": data.get("status"),
                        "nivel_pct": data.get("nivel_pct"),
                        "ultima_atualizacao": data.get("timestamp"),
                    }
                )
                await websocket.send_text(public_payload)
            except (WebSocketDisconnect, Exception):
                break
    finally:
        await pubsub.unsubscribe(f"status_reservatorio:{reservatorio_id}")
        await redis_client.aclose()
        log.info("ws.publico.desconectado", reservatorio_id=reservatorio_id)
