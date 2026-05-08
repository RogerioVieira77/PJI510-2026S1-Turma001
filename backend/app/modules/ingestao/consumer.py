"""Consumer AMQP para a fila RabbitMQ de leituras de sensores.

Consome mensagens em modo contínuo (long-running) via protocolo AMQP (aio-pika)
e persiste as leituras no banco usando o pipeline existente (IngestaoService).

Registrado como background task no lifespan do FastAPI — latência < 5 s.

Campos esperados em cada mensagem da fila (JSON):
    sensor_id         - código externo do dispositivo (ex: "SENSOR-RES-001")
    tipo_sensor       - tipo do sensor (nivel_agua / pluviometro / temperatura / ...)
    valor             - valor numérico da medição
    unidade           - unidade de medida enviada pelo PJI510
    status            - status do sensor: normal | alerta | critico | erro  (opcional)
    timestamp         - ISO-8601 UTC (opcional; usa now() se ausente)
    ativo             - bool: se false, mensagem é descartada sem persistência (opcional, default true)
    fonte_alimentacao - fonte elétrica: rede | bateria (opcional)
    bateria_pct       - carga da bateria 0–100 (opcional)
    bms_nivel         - estado BMS: normal | alerta | critico (opcional)

Código de sensor no banco = f"{sensor_id}-{tipo_sensor}" (chave composta).
Conversão de unidade: m / metros → cm (×100); demais unidades são salvas como enviadas.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import aio_pika
import aio_pika.abc
import structlog
from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.modules.ingestao.models import Sensor
from app.modules.ingestao.schemas import (
    BmsNivelEnum,
    FonteAlimentacaoEnum,
    LeituraBatchCreate,
    LeituraCreate,
    UnidadeEnum,
)
from app.modules.ingestao.service import IngestaoService

log = structlog.get_logger()
_settings = get_settings()

# Status de sensor que indicam falha — descartamos para não poluir o histórico
_STATUS_IGNORADOS: frozenset[str] = frozenset({"erro"})

# Unidades enviadas pelo PJI510 para sensores de nível que precisam de conversão
_UNIDADES_METRO: frozenset[str] = frozenset({"m", "metros"})
_UNIDADES_CELSIUS: frozenset[str] = frozenset({"C", "c", "celsius"})

_RECONNECT_DELAY_S: int = 5


def _normalizar_unidade(valor: float, unidade_raw: str) -> tuple[float, str]:
    """Converte unidades PJI510 para unidades internas.

    Sensores de nível enviam metros — internamente usamos centímetros.
    Temperatura enviada como "C" → normalizado para "°C".
    Todas as demais unidades são mantidas conforme enviadas.
    """
    if unidade_raw in _UNIDADES_METRO:
        return round(valor * 100, 3), "cm"
    if unidade_raw in _UNIDADES_CELSIUS:
        return valor, "°C"
    return valor, unidade_raw


async def _processar_mensagem(msg: aio_pika.abc.AbstractIncomingMessage) -> None:
    """Processa uma mensagem AMQP: faz parse, lookup do sensor e persiste a leitura.

    Comportamento de ACK:
      - Sucesso           → msg.ack()  (via caller)
      - Erro de parse     → msg.reject(requeue=False)  — poison-pill → DLQ
      - Sensor inativo    → msg.reject(requeue=False)  — descarta silenciosamente
      - Erro transitório  → deixa expirar (nack/requeue feito pelo caller)
    """
    try:
        data: dict = json.loads(msg.body)

        sensor_id = str(data["sensor_id"]).strip()
        tipo_sensor = str(data.get("tipo_sensor", "")).strip()
        status_sensor = str(data.get("status", "normal")).lower().strip()

        # ── Campo `ativo` — sensor desligado: descarta sem persistir ─────────
        ativo = bool(data.get("ativo", True))
        if not ativo:
            log.warning(
                "consumer.sensor_auto_desligado",
                sensor_id=sensor_id,
            )
            await msg.reject(requeue=False)
            return

        if status_sensor in _STATUS_IGNORADOS:
            log.warning(
                "consumer.sensor_em_erro",
                sensor_id=sensor_id,
                status=status_sensor,
            )
            await msg.reject(requeue=False)
            return

        # Chave composta: {dispositivo_id}-{tipo_sensor}
        codigo = f"{sensor_id}-{tipo_sensor}"

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Sensor.id).where(
                    Sensor.codigo == codigo,
                    Sensor.ativo.is_(True),
                )
            )
            sensor_db_id: int | None = result.scalar_one_or_none()

            if sensor_db_id is None:
                log.warning("consumer.sensor_nao_encontrado", sensor_codigo=codigo)
                await msg.reject(requeue=False)
                return

            # Conversão de unidade
            unidade_raw = str(data.get("unidade", "")).strip()
            valor_raw = float(data["valor"])
            valor, unidade_str = _normalizar_unidade(valor_raw, unidade_raw)

            try:
                unidade = UnidadeEnum(unidade_str)
            except ValueError:
                log.warning(
                    "consumer.unidade_desconhecida",
                    sensor_codigo=codigo,
                    unidade=unidade_raw,
                    aceitas=[e.value for e in UnidadeEnum],
                )
                await msg.reject(requeue=False)
                return

            # Timestamp da mensagem (fallback: agora)
            agora = datetime.now(tz=timezone.utc)
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
                    pass

            # ── Campos de energia e estado (opcionais) ────────────────────
            fonte_raw = data.get("fonte_alimentacao")
            fonte: FonteAlimentacaoEnum | None = None
            if fonte_raw is not None:
                try:
                    fonte = FonteAlimentacaoEnum(str(fonte_raw).strip())
                except ValueError:
                    pass

            bateria_raw = data.get("bateria_pct")
            bateria_pct: int | None = None
            if bateria_raw is not None:
                try:
                    bateria_pct = max(0, min(100, int(bateria_raw)))
                except (TypeError, ValueError):
                    pass

            bms_raw = data.get("bms_nivel")
            bms: BmsNivelEnum | None = None
            if bms_raw is not None:
                try:
                    bms = BmsNivelEnum(str(bms_raw).strip())
                except ValueError:
                    pass

            leitura = LeituraCreate(
                sensor_id=sensor_db_id,
                timestamp=timestamp,
                valor=valor,
                unidade=unidade,
                fonte_alimentacao=fonte,
                bateria_pct=bateria_pct,
                bms_nivel=bms,
            )

            service = IngestaoService(session)
            await service.processar_lote(LeituraBatchCreate(leituras=[leitura]))
            await session.commit()

        log.debug(
            "consumer.leitura_persistida",
            sensor_codigo=codigo,
            valor=valor,
            unidade=unidade_str,
            timestamp=timestamp.isoformat(),
        )
        await msg.ack()

    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        log.error(
            "consumer.erro_parse_mensagem",
            error=str(exc),
            payload_preview=msg.body[:200].decode(errors="replace"),
        )
        await msg.reject(requeue=False)

    except Exception as exc:
        # Erros transitórios (BD fora, timeout) — requeue para nova tentativa
        log.error("consumer.erro_transiente", error=str(exc))
        await msg.nack(requeue=True)


async def consumir_fila_continuamente() -> None:
    """Long-running AMQP consumer — registrado no lifespan do FastAPI.

    Conecta à fila PJI510 e processa cada mensagem individualmente em sua
    própria sessão de banco. Reconecta automaticamente após falhas de rede.
    Encerra limpo ao receber CancelledError (shutdown da aplicação).
    """
    if not _settings.RABBITMQ_ENABLED:
        log.info("consumer.desabilitado")
        return

    log.info(
        "consumer.iniciando",
        host=_settings.RABBITMQ_HOST,
        vhost=_settings.RABBITMQ_VHOST,
        queue=_settings.RABBITMQ_QUEUE,
    )

    while True:
        try:
            connection = await aio_pika.connect_robust(
                host=_settings.RABBITMQ_HOST,
                port=_settings.RABBITMQ_PORT,
                virtualhost=_settings.RABBITMQ_VHOST,
                login=_settings.RABBITMQ_USER,
                password=_settings.RABBITMQ_PASSWORD,
                timeout=15,
            )
            log.info("consumer.conectado")

            async with connection:
                channel = await connection.channel()
                # prefetch_count=1 — processa uma mensagem por vez (backpressure)
                await channel.set_qos(prefetch_count=1)
                queue = await channel.declare_queue(
                    _settings.RABBITMQ_QUEUE, durable=True, passive=True
                )
                await queue.consume(_processar_mensagem)
                log.info("consumer.aguardando_mensagens", queue=_settings.RABBITMQ_QUEUE)
                # Mantém a coroutine viva até CancelledError no shutdown
                await asyncio.Future()

        except asyncio.CancelledError:
            log.info("consumer.encerrado")
            break

        except Exception as exc:
            log.error(
                "consumer.erro_conexao_reconectando",
                error=str(exc),
                delay_s=_RECONNECT_DELAY_S,
            )
            await asyncio.sleep(_RECONNECT_DELAY_S)
