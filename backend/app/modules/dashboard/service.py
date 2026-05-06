"""Dashboard service — EPIC-07."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schemas import (
    PontoHistorico,
    ReservatorioSummary,
    StatusPublico,
    StatusReservatorio,
)
from app.modules.processamento import policies
from app.modules.processamento.service import ProcessamentoService

log = structlog.get_logger()
settings = get_settings()

_CACHE_KEY = "cache:publico:status"
_CACHE_TTL = 30  # seconds

_PERIODOS: dict[str, timedelta] = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


async def get_status(
    reservatorio_id: int, session: AsyncSession
) -> StatusReservatorio | None:
    """Recalculate and return the full status for a reservoir (TASK-70)."""
    svc = ProcessamentoService(session)
    result = await svc.processar_reservatorio(reservatorio_id)
    if not result:
        return None
    return StatusReservatorio(**result)


async def get_historico(
    reservatorio_id: int, periodo: str, session: AsyncSession
) -> list[PontoHistorico]:
    """Return time-series for the given period using the appropriate source (TASK-70)."""
    delta = _PERIODOS.get(periodo, timedelta(hours=24))
    now = datetime.now(timezone.utc)
    start = now - delta

    repo = DashboardRepository(session)
    sensor_ids = await repo.get_nivel_sensor_ids(reservatorio_id)
    if not sensor_ids:
        return []

    if delta <= timedelta(hours=24):
        # Raw hypertable data (≤1440 pts for 24h)
        leituras = await repo.get_historico_raw(sensor_ids, start, now)
        return [
            PontoHistorico(
                bucket=l.timestamp,
                media=float(l.valor),
                minimo=float(l.valor),
                maximo=float(l.valor),
            )
            for l in leituras
        ]
    elif delta <= timedelta(days=7):
        # Hourly continuous aggregate
        rows = await repo.get_historico_hourly(sensor_ids, start, now)
    else:
        # Daily continuous aggregate
        rows = await repo.get_historico_daily(sensor_ids, start, now)

    return [
        PontoHistorico(
            bucket=row["bucket"],
            media=float(row["media"]),
            minimo=float(row["minimo"]),
            maximo=float(row["maximo"]),
        )
        for row in rows
    ]


async def list_reservatorios(session: AsyncSession) -> list[ReservatorioSummary]:
    """List all reservoirs with their current level and status (TASK-70)."""
    repo = DashboardRepository(session)
    reservatorios = await repo.get_all()
    summaries: list[ReservatorioSummary] = []
    for r in reservatorios:
        nivel_cm, ts = await repo.get_latest_nivel(r.id)
        if nivel_cm is not None:
            cap_cm = float(r.capacidade_m3)  # same proxy as ProcessamentoService
            nivel_pct: float | None = policies.calcular_nivel_percentual(nivel_cm, cap_cm)
            status_str: str | None = policies.classificar_nivel(nivel_pct)
        else:
            nivel_pct = None
            status_str = None
            ts = None

        summary = ReservatorioSummary.model_validate(r).model_copy(
            update={"nivel_pct": nivel_pct, "status": status_str, "ultima_atualizacao": ts}
        )
        summaries.append(summary)
    return summaries


async def get_publico_status(session: AsyncSession) -> list[StatusPublico]:
    """Return simplified status for all reservoirs, cached 30s in Redis (TASK-71)."""
    redis_client = aioredis.from_url(str(settings.REDIS_URL), decode_responses=True)
    async with redis_client:
        cached = await redis_client.get(_CACHE_KEY)
        if cached:
            return [StatusPublico(**item) for item in json.loads(cached)]

        repo = DashboardRepository(session)
        reservatorios = await repo.get_all()
        items: list[StatusPublico] = []
        for r in reservatorios:
            nivel_cm, ts = await repo.get_latest_nivel(r.id)
            if nivel_cm is not None:
                cap_cm = float(r.capacidade_m3)
                nivel_pct = policies.calcular_nivel_percentual(nivel_cm, cap_cm)
                status_str = policies.classificar_nivel(nivel_pct)
                ultima = ts.isoformat() if ts else None
            else:
                nivel_pct = 0.0
                status_str = "normal"
                ultima = None
            items.append(
                StatusPublico(
                    id=r.id,
                    nome=r.nome,
                    status=status_str,
                    nivel_pct=round(nivel_pct, 2),
                    ultima_atualizacao=ultima,
                )
            )

        await redis_client.set(
            _CACHE_KEY,
            json.dumps([i.model_dump() for i in items], default=str),
            ex=_CACHE_TTL,
        )
        return items
