"""Alertas externos — consumers AMQP para as 3 filas do PJI510.

Filas:
  - previsoes.fila        → PrevisaoChuva
  - defesa.situacao.fila  → SituacaoDefesaCivil
  - defesa.alertas.fila   → AlertaDefesaCivil

Comportamento de ACK (igual ao consumer de sensores):
  - Sucesso             → msg.ack()
  - Payload inválido    → msg.reject(requeue=False)   — descarta (poison-pill)
  - Erro transitório    → msg.nack(requeue=True)      — requeue para nova tentativa

Cada consumer tem seu próprio loop de reconexão com delay de 5 s.
"""
from __future__ import annotations

import asyncio
import json

import aio_pika
import structlog
from pydantic import ValidationError

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.modules.alertas_externos.schemas import (
    AlertaDefesaCivilPayload,
    PrevisaoChuvaPayload,
    SituacaoDefesaCivilPayload,
)
from app.modules.alertas_externos.service import salvar_alerta, salvar_previsao, salvar_situacao

log = structlog.get_logger()
_settings = get_settings()

_RECONNECT_DELAY_S: int = 5


# ── Handlers individuais ──────────────────────────────────────────────────────

async def _handle_previsao(msg: aio_pika.abc.AbstractIncomingMessage) -> None:
    try:
        data: dict = json.loads(msg.body)
        payload = PrevisaoChuvaPayload.model_validate(data)
        async with AsyncSessionLocal() as session:
            await salvar_previsao(payload, session)
        await msg.ack()

    except (json.JSONDecodeError, ValidationError, KeyError, TypeError, ValueError) as exc:
        log.error(
            "consumer_previsao.payload_invalido",
            error=str(exc),
            preview=msg.body[:200].decode(errors="replace"),
        )
        await msg.reject(requeue=False)

    except Exception as exc:
        log.error("consumer_previsao.erro_transiente", error=str(exc))
        await msg.nack(requeue=True)


async def _handle_situacao(msg: aio_pika.abc.AbstractIncomingMessage) -> None:
    try:
        data: dict = json.loads(msg.body)
        payload = SituacaoDefesaCivilPayload.model_validate(data)
        async with AsyncSessionLocal() as session:
            await salvar_situacao(payload, session)
        await msg.ack()

    except (json.JSONDecodeError, ValidationError, KeyError, TypeError, ValueError) as exc:
        log.error(
            "consumer_situacao.payload_invalido",
            error=str(exc),
            preview=msg.body[:200].decode(errors="replace"),
        )
        await msg.reject(requeue=False)

    except Exception as exc:
        log.error("consumer_situacao.erro_transiente", error=str(exc))
        await msg.nack(requeue=True)


async def _handle_alerta(msg: aio_pika.abc.AbstractIncomingMessage) -> None:
    try:
        data: dict = json.loads(msg.body)
        payload = AlertaDefesaCivilPayload.model_validate(data)
        async with AsyncSessionLocal() as session:
            await salvar_alerta(payload, session)
        await msg.ack()

    except (json.JSONDecodeError, ValidationError, KeyError, TypeError, ValueError) as exc:
        log.error(
            "consumer_alerta.payload_invalido",
            error=str(exc),
            preview=msg.body[:200].decode(errors="replace"),
        )
        await msg.reject(requeue=False)

    except Exception as exc:
        log.error("consumer_alerta.erro_transiente", error=str(exc))
        await msg.nack(requeue=True)


# ── Loops de consumo ──────────────────────────────────────────────────────────

async def _consumer_loop(
    queue_name: str,
    handler: object,
    log_name: str,
) -> None:
    """Loop genérico de consumer AMQP com reconexão automática."""
    log.info(f"{log_name}.iniciando", queue=queue_name)
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
            log.info(f"{log_name}.conectado", queue=queue_name)
            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=1)
                queue = await channel.declare_queue(queue_name, durable=True, passive=True)
                await queue.consume(handler)  # type: ignore[arg-type]
                log.info(f"{log_name}.aguardando_mensagens", queue=queue_name)
                await asyncio.Future()

        except asyncio.CancelledError:
            log.info(f"{log_name}.encerrado", queue=queue_name)
            break

        except Exception as exc:
            log.error(
                f"{log_name}.erro_conexao_reconectando",
                error=str(exc),
                delay_s=_RECONNECT_DELAY_S,
            )
            await asyncio.sleep(_RECONNECT_DELAY_S)


async def consumir_previsoes() -> None:
    if not _settings.RABBITMQ_ENABLED_ALERTAS_EXTERNOS:
        log.info("consumer_previsao.desabilitado")
        return
    await _consumer_loop(
        _settings.RABBITMQ_QUEUE_PREVISOES,
        _handle_previsao,
        "consumer_previsao",
    )


async def consumir_defesa_situacao() -> None:
    if not _settings.RABBITMQ_ENABLED_ALERTAS_EXTERNOS:
        log.info("consumer_situacao.desabilitado")
        return
    await _consumer_loop(
        _settings.RABBITMQ_QUEUE_DEFESA_SITUACAO,
        _handle_situacao,
        "consumer_situacao",
    )


async def consumir_defesa_alertas() -> None:
    if not _settings.RABBITMQ_ENABLED_ALERTAS_EXTERNOS:
        log.info("consumer_alerta.desabilitado")
        return
    await _consumer_loop(
        _settings.RABBITMQ_QUEUE_DEFESA_ALERTAS,
        _handle_alerta,
        "consumer_alerta",
    )
