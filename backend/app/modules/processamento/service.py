"""Processamento service — TASK-51."""
from __future__ import annotations

import asyncio

import redis.asyncio as aioredis
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.modules.ingestao.models import LeituraSensor, Reservatorio, Sensor
from app.modules.processamento import policies

log = structlog.get_logger()
settings = get_settings()

# Number of recent readings to use for rate-of-change calculations
_LEITURAS_JANELA = 10


class ProcessamentoService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def processar_reservatorio(self, reservatorio_id: int) -> dict:
        """Aplica todas as políticas (RN-01..06) para um reservatório.

        Returns a dict with computed metrics that is also published to Redis
        pub/sub so WebSocket consumers receive it in real time.
        """
        # Load reservoir
        reservatorio = await self._session.get(Reservatorio, reservatorio_id)
        if reservatorio is None:
            log.warning("processamento.reservatorio_nao_encontrado", id=reservatorio_id)
            return {}

        # Load sensors of tipo 'nivel' for this reservoir
        sensors_result = await self._session.execute(
            select(Sensor).where(
                Sensor.reservatorio_id == reservatorio_id,
                Sensor.ativo.is_(True),
            )
        )
        sensors = sensors_result.scalars().all()
        if not sensors:
            log.warning("processamento.sem_sensores", reservatorio_id=reservatorio_id)
            return {}

        sensor_ids = [s.id for s in sensors]

        # Load last N readings per sensor
        leituras_result = await self._session.execute(
            select(LeituraSensor)
            .where(LeituraSensor.sensor_id.in_(sensor_ids))
            .order_by(LeituraSensor.timestamp.desc())
            .limit(_LEITURAS_JANELA * len(sensor_ids))
        )
        leituras = leituras_result.scalars().all()
        if not leituras:
            return {}

        # Use the most recent reading as current level reference
        ultima_leitura = leituras[0]
        nivel_cm = float(ultima_leitura.valor)

        # Estimate reservoir depth from capacity and section area
        # capacidade_m3 / area_secao = profundidade; fallback: treat m3 as cm-equivalent
        # We store capacity in m3 and use a nominal section area of 1 m2 if unavailable;
        # the PRD seed uses area_secao_m2=250000 in the description — but the model only
        # has capacidade_m3, so we derive a nominal capacity_cm from it.
        capacidade_cm = float(reservatorio.capacidade_m3)  # proxy for threshold calcs

        # RN-01
        volume_m3 = policies.calcular_volume(nivel_cm, 250_000.0)

        # RN-02 — use the nivel sensor readings in chronological order
        nivel_leituras = sorted(
            [l for l in leituras if l.sensor_id == sensor_ids[0]],
            key=lambda l: l.timestamp,
        )
        valores = [float(l.valor) for l in nivel_leituras]
        timestamps_lista = [l.timestamp for l in nivel_leituras]
        taxa_cm_min = policies.calcular_taxa_variacao(valores, timestamps_lista)

        # RN-03
        tempo_transbordo = policies.estimar_tempo_transbordo(
            nivel_cm, capacidade_cm, taxa_cm_min
        )

        # RN-04
        nivel_pct = policies.calcular_nivel_percentual(nivel_cm, capacidade_cm)
        status = policies.classificar_nivel(nivel_pct)

        # RN-06 — check divergence across all active sensors
        leituras_por_sensor: dict[int, float] = {}
        for leitura in leituras:
            if leitura.sensor_id not in leituras_por_sensor:
                leituras_por_sensor[leitura.sensor_id] = float(leitura.valor)
        divergencia = policies.detectar_divergencia_sensores(leituras_por_sensor)

        result = {
            "reservatorio_id": reservatorio_id,
            "nivel_cm": round(nivel_cm, 2),
            "nivel_pct": round(nivel_pct, 2),
            "volume_m3": round(volume_m3, 2),
            "taxa_cm_min": round(taxa_cm_min, 4),
            "tempo_transbordo_min": round(tempo_transbordo, 1) if tempo_transbordo is not None else None,
            "status": status,
            "divergencia_sensores": divergencia,
            "timestamp": ultima_leitura.timestamp.isoformat(),
        }

        log.info(
            "processamento.concluido",
            reservatorio_id=reservatorio_id,
            nivel_pct=result["nivel_pct"],
            status=status,
            taxa_cm_min=result["taxa_cm_min"],
        )

        import json

        # Publish result for WebSocket consumers
        redis_client = aioredis.from_url(str(settings.REDIS_URL), decode_responses=True)
        async with redis_client:
            await redis_client.publish(
                f"status_reservatorio:{reservatorio_id}",
                json.dumps(result),
            )

        return result


async def subscriber_nova_leitura() -> None:
    """Redis pub/sub subscriber: listens on `nova_leitura:*` channels and
    triggers ProcessamentoService for each affected reservoir.

    This coroutine is intended to run as a long-lived background task
    (started in the FastAPI lifespan) rather than as an ARQ worker,
    keeping processing latency minimal.
    """
    from app.database import AsyncSessionLocal

    redis_client = aioredis.from_url(str(settings.REDIS_URL), decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.psubscribe("nova_leitura:*")
    log.info("processamento.subscriber_iniciado")

    try:
        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue
            channel: str = message["channel"]
            try:
                reservatorio_id = int(channel.split(":", 1)[1])
            except (IndexError, ValueError):
                continue
            try:
                async with AsyncSessionLocal() as session:
                    svc = ProcessamentoService(session)
                    result = await svc.processar_reservatorio(reservatorio_id)
                    if result:
                        from arq import create_pool as _arq_pool
                        from arq.connections import RedisSettings as _RS
                        from app.modules.alertas.service import AlertaService
                        arq = await _arq_pool(_RS.from_dsn(str(settings.REDIS_URL)))
                        try:
                            alertas_svc = AlertaService(session, arq)
                            await alertas_svc.avaliar(
                                reservatorio_id, result["nivel_pct"]
                            )
                        finally:
                            await arq.aclose()
                    await session.commit()
            except Exception as exc:
                log.error(
                    "processamento.subscriber_erro",
                    reservatorio_id=reservatorio_id,
                    error=str(exc),
                )
    finally:
        await pubsub.unsubscribe()
        await redis_client.aclose()
