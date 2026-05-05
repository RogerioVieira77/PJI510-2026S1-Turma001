"""Dashboard repository — EPIC-07."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestao.models import LeituraSensor, Reservatorio, Sensor, TipoSensorEnum


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Reservatorio]:
        result = await self._session.execute(
            select(Reservatorio).order_by(Reservatorio.nome)
        )
        return list(result.scalars().all())

    async def get_by_id(self, reservatorio_id: int) -> Reservatorio | None:
        return await self._session.get(Reservatorio, reservatorio_id)

    async def get_nivel_sensor_ids(self, reservatorio_id: int) -> list[int]:
        result = await self._session.execute(
            select(Sensor.id).where(
                Sensor.reservatorio_id == reservatorio_id,
                Sensor.tipo == TipoSensorEnum.nivel,
                Sensor.ativo.is_(True),
            )
        )
        return list(result.scalars().all())

    async def get_latest_nivel(
        self, reservatorio_id: int
    ) -> tuple[float | None, datetime | None]:
        """Return (nivel_cm, timestamp) from the most recent active nivel sensor reading."""
        result = await self._session.execute(
            select(LeituraSensor.valor, LeituraSensor.timestamp)
            .join(Sensor, LeituraSensor.sensor_id == Sensor.id)
            .where(
                Sensor.reservatorio_id == reservatorio_id,
                Sensor.tipo == TipoSensorEnum.nivel,
                Sensor.ativo.is_(True),
            )
            .order_by(LeituraSensor.timestamp.desc())
            .limit(1)
        )
        row = result.first()
        if row is None:
            return None, None
        return float(row.valor), row.timestamp

    async def get_historico_raw(
        self, sensor_ids: list[int], start: datetime, end: datetime
    ) -> list[LeituraSensor]:
        result = await self._session.execute(
            select(LeituraSensor)
            .where(
                LeituraSensor.sensor_id.in_(sensor_ids),
                LeituraSensor.timestamp >= start,
                LeituraSensor.timestamp <= end,
            )
            .order_by(LeituraSensor.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_historico_hourly(
        self, sensor_ids: list[int], start: datetime, end: datetime
    ) -> list:
        result = await self._session.execute(
            text("""
                SELECT bucket,
                       AVG(media)  AS media,
                       MIN(minimo) AS minimo,
                       MAX(maximo) AS maximo
                FROM leitura_sensor_hourly
                WHERE sensor_id = ANY(:ids)
                  AND bucket >= :start
                  AND bucket <= :end
                GROUP BY bucket
                ORDER BY bucket ASC
            """),
            {"ids": sensor_ids, "start": start, "end": end},
        )
        return list(result.mappings().all())

    async def get_historico_daily(
        self, sensor_ids: list[int], start: datetime, end: datetime
    ) -> list:
        result = await self._session.execute(
            text("""
                SELECT bucket,
                       AVG(media)  AS media,
                       MIN(minimo) AS minimo,
                       MAX(maximo) AS maximo
                FROM leitura_sensor_daily
                WHERE sensor_id = ANY(:ids)
                  AND bucket >= :start
                  AND bucket <= :end
                GROUP BY bucket
                ORDER BY bucket ASC
            """),
            {"ids": sensor_ids, "start": start, "end": end},
        )
        return list(result.mappings().all())
