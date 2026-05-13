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

    async def get_latest_by_tipo(
        self, reservatorio_id: int, tipo: TipoSensorEnum
    ) -> list[tuple[Sensor, float | None, str | None, datetime | None]]:
        """Retorna lista de (sensor, valor, unidade, timestamp) da última leitura de cada sensor do tipo."""
        result = await self._session.execute(
            select(Sensor).where(
                Sensor.reservatorio_id == reservatorio_id,
                Sensor.tipo == tipo,
                Sensor.ativo.is_(True),
            ).order_by(Sensor.codigo)
        )
        sensors = list(result.scalars().all())

        out = []
        for sensor in sensors:
            lr = await self._session.execute(
                select(LeituraSensor.valor, LeituraSensor.timestamp)
                .where(LeituraSensor.sensor_id == sensor.id)
                .order_by(LeituraSensor.timestamp.desc())
                .limit(1)
            )
            row = lr.first()
            if row:
                out.append((sensor, float(row.valor), sensor.unidade, row.timestamp))
            else:
                out.append((sensor, None, sensor.unidade, None))
        return out

    async def get_latest_by_sensor_ids(
        self, sensor_ids: list[int]
    ) -> dict[int, tuple[float, str, datetime]]:
        """Retorna {sensor_id: (valor, unidade, timestamp)} da última leitura de cada sensor."""
        result: dict[int, tuple[float, str, datetime]] = {}
        for sid in sensor_ids:
            lr = await self._session.execute(
                select(Sensor.unidade, LeituraSensor.valor, LeituraSensor.timestamp)
                .join(Sensor, LeituraSensor.sensor_id == Sensor.id)
                .where(LeituraSensor.sensor_id == sid)
                .order_by(LeituraSensor.timestamp.desc())
                .limit(1)
            )
            row = lr.first()
            if row:
                result[sid] = (float(row.valor), row.unidade, row.timestamp)
        return result

    async def get_sensores_por_estacao(
        self, reservatorio_id: int
    ) -> dict[str, list[Sensor]]:
        """Agrupa sensores meteorológicos por prefixo de estação (ex: ESTACAO-MET-001)."""
        tipos_met = [
            TipoSensorEnum.temperatura,
            TipoSensorEnum.umidade,
            TipoSensorEnum.pressao,
            TipoSensorEnum.pluviometro,
            TipoSensorEnum.vento_velocidade,
            TipoSensorEnum.vento_direcao,
        ]
        result = await self._session.execute(
            select(Sensor).where(
                Sensor.reservatorio_id == reservatorio_id,
                Sensor.tipo.in_(tipos_met),
                Sensor.ativo.is_(True),
            ).order_by(Sensor.codigo)
        )
        sensors = list(result.scalars().all())

        groups: dict[str, list[Sensor]] = {}
        for s in sensors:
            # Ex: "ESTACAO-MET-001-temperatura" → prefixo "ESTACAO-MET-001"
            parts = s.codigo.rsplit("-", 1)
            prefix = parts[0] if len(parts) == 2 else s.codigo
            groups.setdefault(prefix, []).append(s)
        return groups

    async def get_all_sensores_with_latest_energia(
        self, reservatorio_id: int
    ) -> list[tuple[Sensor, str | None, int | None, str | None, datetime | None]]:
        """Retorna (sensor, fonte_alimentacao, bateria_pct, bms_nivel, ultima_leitura)
        para todos os sensores do reservatório, usando a leitura mais recente de cada um."""
        result = await self._session.execute(
            select(Sensor)
            .where(
                Sensor.reservatorio_id == reservatorio_id,
                Sensor.tipo != TipoSensorEnum.estado_bomba,
            )
            .order_by(Sensor.codigo)
        )
        sensors = list(result.scalars().all())

        out: list[tuple[Sensor, str | None, int | None, str | None, datetime | None]] = []
        for sensor in sensors:
            lr = await self._session.execute(
                select(
                    LeituraSensor.timestamp,
                    LeituraSensor.fonte_alimentacao,
                    LeituraSensor.bateria_pct,
                    LeituraSensor.bms_nivel,
                )
                .where(LeituraSensor.sensor_id == sensor.id)
                .order_by(LeituraSensor.timestamp.desc())
                .limit(1)
            )
            row = lr.first()
            out.append((
                sensor,
                row.fonte_alimentacao if row else None,
                row.bateria_pct if row else None,
                row.bms_nivel if row else None,
                row.timestamp if row else None,
            ))
        return out

    async def get_bombas_status(
        self, reservatorio_id: int
    ) -> list[tuple[Sensor, float | None, str | None, int | None, str | None, datetime | None]]:
        """Retorna (sensor, valor, fonte, bateria_pct, bms_nivel, timestamp)
        para todas as bombas de drenagem do reservatório."""
        result = await self._session.execute(
            select(Sensor)
            .where(
                Sensor.reservatorio_id == reservatorio_id,
                Sensor.tipo == TipoSensorEnum.estado_bomba,
            )
            .order_by(Sensor.codigo)
        )
        sensors = list(result.scalars().all())

        out: list[tuple[Sensor, float | None, str | None, int | None, str | None, datetime | None]] = []
        for sensor in sensors:
            lr = await self._session.execute(
                select(
                    LeituraSensor.valor,
                    LeituraSensor.timestamp,
                    LeituraSensor.fonte_alimentacao,
                    LeituraSensor.bateria_pct,
                    LeituraSensor.bms_nivel,
                )
                .where(LeituraSensor.sensor_id == sensor.id)
                .order_by(LeituraSensor.timestamp.desc())
                .limit(1)
            )
            row = lr.first()
            out.append((
                sensor,
                float(row.valor) if row else None,
                row.fonte_alimentacao if row else None,
                row.bateria_pct if row else None,
                row.bms_nivel if row else None,
                row.timestamp if row else None,
            ))
        return out
