"""Ingestao service — TASK-40."""
from __future__ import annotations

import structlog
import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.modules.alertas.models import NivelAlertaEnum
from app.modules.alertas.repository import AlertaRepository
from app.modules.ingestao.models import Sensor
from app.modules.ingestao.repository import LeituraRepository
from app.modules.ingestao.schemas import BmsNivelEnum, LeituraBatchCreate

settings = get_settings()
log = structlog.get_logger()

# Mapeamento BMS → NivelAlertaEnum para criação de alertas operacionais
_BMS_PARA_NIVEL: dict[str, NivelAlertaEnum] = {
    BmsNivelEnum.alerta: NivelAlertaEnum.atencao,
    BmsNivelEnum.critico: NivelAlertaEnum.emergencia,
}


class IngestaoService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LeituraRepository(session)

    async def processar_lote(self, batch: LeituraBatchCreate) -> int:
        """Validate, persist and publish a batch of sensor readings.

        Leituras com `ativo=False` são descartadas silenciosamente (não contam
        em `inseridos`). Leituras com `bms_nivel=alerta|critico` disparam a
        criação de um Alerta operacional na tabela `alerta`.

        Raises HTTP 422 if any sensor_id (for active readings) is unknown or
        belongs to an inactive sensor in the database.
        Publishes `nova_leitura:{reservatorio_id}` to Redis pub/sub.
        """
        # ── 1. Separar leituras ativas das descartadas ────────────────────────
        leituras_ativas = [l for l in batch.leituras if l.ativo]
        descartadas = len(batch.leituras) - len(leituras_ativas)
        if descartadas:
            log.warning(
                "ingestao.leituras_descartadas_ativo_false",
                quantidade=descartadas,
            )

        if not leituras_ativas:
            return 0

        sensor_ids = list({leitura.sensor_id for leitura in leituras_ativas})

        # ── 2. Validar sensor_ids — devem existir e estar ativos no banco ──────
        result = await self._session.execute(
            select(Sensor.id, Sensor.reservatorio_id, Sensor.codigo).where(
                Sensor.id.in_(sensor_ids),
                Sensor.ativo.is_(True),
            )
        )
        rows = result.all()
        found_ids = {row.id for row in rows}
        sensor_to_reservatorio: dict[int, int] = {
            row.id: row.reservatorio_id for row in rows
        }
        sensor_to_codigo: dict[int, str] = {row.id: row.codigo for row in rows}

        missing = set(sensor_ids) - found_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"sensor_ids não encontrados ou inativos: {sorted(missing)}",
            )

        # ── 3. Montar registros com os novos campos de energia/estado ─────────
        records = [
            {
                "sensor_id": leitura.sensor_id,
                "timestamp": leitura.timestamp,
                "valor": leitura.valor,
                "nivel_percentual": None,
                "fonte_alimentacao": leitura.fonte_alimentacao.value
                if leitura.fonte_alimentacao is not None
                else None,
                "bateria_pct": leitura.bateria_pct,
                "bms_nivel": leitura.bms_nivel.value
                if leitura.bms_nivel is not None
                else None,
            }
            for leitura in leituras_ativas
        ]
        count = await self._repo.bulk_insert(records)

        # ── 4. Alertas BMS ────────────────────────────────────────────────────
        alerta_repo = AlertaRepository(self._session)
        for leitura in leituras_ativas:
            if leitura.bms_nivel is None:
                continue
            nivel_alerta = _BMS_PARA_NIVEL.get(leitura.bms_nivel)
            if nivel_alerta is None:
                continue

            reservatorio_id = sensor_to_reservatorio[leitura.sensor_id]
            codigo = sensor_to_codigo[leitura.sensor_id]
            bateria_info = (
                f", bateria_pct={leitura.bateria_pct}%"
                if leitura.bateria_pct is not None
                else ""
            )
            if leitura.bms_nivel == BmsNivelEnum.critico:
                mensagem = (
                    f"BMS crítico no sensor {codigo}: "
                    f"intervenção imediata necessária{bateria_info}"
                )
            else:
                mensagem = (
                    f"BMS em alerta no sensor {codigo}: "
                    f"bateria requer atenção{bateria_info}"
                )

            await alerta_repo.create_alerta(
                reservatorio_id=reservatorio_id,
                nivel=nivel_alerta,
                mensagem=mensagem,
            )
            log.warning(
                "ingestao.alerta_bms_criado",
                sensor_codigo=codigo,
                bms_nivel=leitura.bms_nivel,
                nivel_alerta=nivel_alerta,
            )

        # ── 5. Publicar evento no Redis por reservatório afetado ──────────────
        reservatorio_ids = {sensor_to_reservatorio[sid] for sid in sensor_ids}
        redis_client = aioredis.from_url(str(settings.REDIS_URL), decode_responses=True)
        async with redis_client:
            for rid in reservatorio_ids:
                await redis_client.publish(f"nova_leitura:{rid}", str(rid))

        return count

