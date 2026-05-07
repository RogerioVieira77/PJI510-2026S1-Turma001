"""Consumer AMQP para a fila RabbitMQ de leituras de sensores.

Consome mensagens diretamente via protocolo AMQP (aio-pika) e persiste
as leituras no banco usando o pipeline existente (IngestaoService).

A conexao eh aberta a cada execucao do cron (abordagem batch/polling),
o que evita reconexoes persistentes no worker ARQ.

Campos esperados em cada mensagem da fila (JSON):
    sensor_id   - codigo externo do sensor (mapeado para Sensor.codigo)
    tipo_sensor - tipo do sensor (nivel_agua / vazao / pluviometro / pressao / temperatura)
    valor       - valor numerico da medicao
    unidade     - unidade de medida (cm / m3/s / mm / % / m3)
    status      - status do sensor: normal | alerta | critico | erro  (opcional)
    timestamp   - ISO-8601 UTC (opcional; usa now() se ausente)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import aio_pika
import aio_pika.abc
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.modules.ingestao.models import Sensor
from app.modules.ingestao.schemas import LeituraBatchCreate, LeituraCreate, UnidadeEnum
from app.modules.ingestao.service import IngestaoService

log = structlog.get_logger()
_settings = get_settings()

# "erro" indica falha no sensor - descartamos para nao poluir o historico
_STATUS_IGNORADOS: frozenset[str] = frozenset({"erro"})


class RabbitMQAmqpConsumer:
    """Consome mensagens de sensores via AMQP direto (aio-pika)."""

    def __init__(self) -> None:
        self._host = _settings.RABBITMQ_HOST
        self._port = _settings.RABBITMQ_PORT
        self._vhost = _settings.RABBITMQ_VHOST
        self._user = _settings.RABBITMQ_USER
        self._password = _settings.RABBITMQ_PASSWORD
        self._queue_name = _settings.RABBITMQ_QUEUE
        self._batch_size = _settings.RABBITMQ_BATCH_SIZE

    async def fetch_and_process(self, session: AsyncSession) -> int:
        """Abre conexao AMQP, drena ate batch_size mensagens e processa.

        Retorna o numero de leituras efetivamente inseridas.
        Mensagens processadas com sucesso sao ACKd; erros de parse sao NACKd
        (descartados sem requeue para evitar poison-pill loop).
        """
        connection = await aio_pika.connect_robust(
            host=self._host,
            port=self._port,
            virtualhost=self._vhost,
            login=self._user,
            password=self._password,
            timeout=15,
        )
        leituras: list[LeituraCreate] = []
        acked_msgs: list[aio_pika.abc.AbstractIncomingMessage] = []
        nacked_msgs: list[aio_pika.abc.AbstractIncomingMessage] = []

        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=self._batch_size)
            queue = await channel.declare_queue(
                self._queue_name, durable=True, passive=True
            )

            agora = datetime.now(tz=timezone.utc)

            for _ in range(self._batch_size):
                msg = await queue.get(fail=False)  # None if empty
                if msg is None:
                    break

                parse_ok, leitura = await self._parse_message(msg, session, agora)
                if parse_ok and leitura is not None:
                    leituras.append(leitura)
                    acked_msgs.append(msg)
                else:
                    nacked_msgs.append(msg)

            # Persiste antes do ACK - garantia transacional
            count = 0
            if leituras:
                service = IngestaoService(session)
                count = await service.processar_lote(
                    LeituraBatchCreate(leituras=leituras)
                )

            for m in acked_msgs:
                await m.ack()
            for m in nacked_msgs:
                await m.nack(requeue=False)

            return count

    async def _parse_message(
        self,
        msg: aio_pika.abc.AbstractIncomingMessage,
        session: AsyncSession,
        agora: datetime,
    ) -> tuple[bool, LeituraCreate | None]:
        """Parse a single AMQP message into a LeituraCreate.

        Returns (True, leitura) on success or (False, None) on unrecoverable error.
        """
        try:
            data: dict = json.loads(msg.body)

            sensor_codigo = str(data["sensor_id"])
            status_sensor = str(data.get("status", "normal")).lower().strip()

            if status_sensor in _STATUS_IGNORADOS:
                log.warning(
                    "consumer.sensor_em_erro",
                    sensor_codigo=sensor_codigo,
                    status=status_sensor,
                )
                return False, None

            # Mapeia codigo externo -> ID interno (Sensor.codigo)
            result = await session.execute(
                select(Sensor.id).where(
                    Sensor.codigo == sensor_codigo,
                    Sensor.ativo.is_(True),
                )
            )
            sensor_db_id: int | None = result.scalar_one_or_none()

            if sensor_db_id is None:
                log.warning(
                    "consumer.sensor_nao_encontrado",
                    sensor_codigo=sensor_codigo,
                )
                return False, None

            # Valida unidade contra o enum
            unidade_raw = str(data.get("unidade", "")).strip()
            try:
                unidade = UnidadeEnum(unidade_raw)
            except ValueError:
                log.warning(
                    "consumer.unidade_desconhecida",
                    sensor_codigo=sensor_codigo,
                    unidade=unidade_raw,
                    aceitas=[e.value for e in UnidadeEnum],
                )
                return False, None

            # Usa timestamp da mensagem se disponivel e valido
            timestamp = agora
            ts_raw = data.get("timestamp")
            if ts_raw:
                try:
                    parsed_ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
                    if parsed_ts.tzinfo is None:
                        parsed_ts = parsed_ts.replace(tzinfo=timezone.utc)
                    if parsed_ts <= agora:
                        timestamp = parsed_ts
                except (ValueError, TypeError):
                    pass  # fallback to agora

            leitura = LeituraCreate(
                sensor_id=sensor_db_id,
                timestamp=timestamp,
                valor=float(data["valor"]),
                unidade=unidade,
            )

            log.debug(
                "consumer.leitura_preparada",
                sensor_codigo=sensor_codigo,
                tipo_sensor=data.get("tipo_sensor"),
                valor=data["valor"],
                unidade=unidade_raw,
                status=status_sensor,
            )
            return True, leitura

        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            log.error(
                "consumer.erro_parse_mensagem",
                error=str(exc),
                payload_preview=msg.body[:200].decode(errors="replace"),
            )
            return False, None
