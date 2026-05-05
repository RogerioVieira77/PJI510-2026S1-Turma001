"""Ingestao service — TASK-41."""
from __future__ import annotations

import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.modules.ingestao.models import Sensor
from app.modules.ingestao.repository import LeituraRepository
from app.modules.ingestao.schemas import LeituraBatchCreate

settings = get_settings()


class IngestaoService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LeituraRepository(session)

    async def processar_lote(self, batch: LeituraBatchCreate) -> int:
        """Validate, persist and publish a batch of sensor readings.

        Raises HTTP 422 if any sensor_id is unknown.
        Publishes `nova_leitura:{reservatorio_id}` to Redis pub/sub
        for each affected reservoir so downstream consumers can react.
        """
        sensor_ids = list({leitura.sensor_id for leitura in batch.leituras})

        # Validate sensor_ids and fetch reservatorio mapping in one query
        result = await self._session.execute(
            select(Sensor.id, Sensor.reservatorio_id).where(Sensor.id.in_(sensor_ids))
        )
        rows = result.all()
        found_ids = {row.id for row in rows}
        sensor_to_reservatorio: dict[int, int] = {
            row.id: row.reservatorio_id for row in rows
        }

        missing = set(sensor_ids) - found_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"sensor_ids não encontrados: {sorted(missing)}",
            )

        records = [
            {
                "sensor_id": leitura.sensor_id,
                "timestamp": leitura.timestamp,
                "valor": leitura.valor,
                "nivel_percentual": None,
            }
            for leitura in batch.leituras
        ]
        count = await self._repo.bulk_insert(records)

        # Publish once per affected reservoir
        reservatorio_ids = {sensor_to_reservatorio[sid] for sid in sensor_ids}
        redis_client = aioredis.from_url(str(settings.REDIS_URL), decode_responses=True)
        async with redis_client:
            for rid in reservatorio_ids:
                await redis_client.publish(f"nova_leitura:{rid}", str(rid))

        return count
