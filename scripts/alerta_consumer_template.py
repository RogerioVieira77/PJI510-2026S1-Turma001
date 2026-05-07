"""
Template de Consumer AMQP — Alerta Romano
==========================================
Cole este módulo no repositório do Alerta Romano e adapte o callback
`processar_leitura()` com a lógica de avaliação de alertas.

Variáveis de ambiente esperadas:
  RABBITMQ_HOST     — hostname do broker (padrão: rabbitmq)
  RABBITMQ_PORT     — porta AMQP (padrão: 5672)
  RABBITMQ_VHOST    — virtual host (padrão: /pji510)
  ALERTA_CONSUMER_USER — usuário AMQP (padrão: alerta_consumer)
  ALERTA_CONSUMER_PASS — senha AMQP (obrigatório)

Dependência: aio-pika>=9.4
  pip install aio-pika
"""

import asyncio
import json
import logging
import os
from typing import Any

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger("alerta_consumer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# --- Configuração ---
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/pji510")
RABBITMQ_USER = os.getenv("ALERTA_CONSUMER_USER", "alerta_consumer")
RABBITMQ_PASS = os.getenv("ALERTA_CONSUMER_PASS", "")
QUEUE_NAME = os.getenv("QUEUE_NAME", "sensores.leituras")
PREFETCH_COUNT = int(os.getenv("PREFETCH_COUNT", "10"))


# ===========================================================
# ADAPTE ESTA FUNÇÃO com a lógica do Alerta Romano
# ===========================================================
async def processar_leitura(dados: dict[str, Any]) -> None:
    """
    Processa uma leitura de sensor.

    Estrutura esperada de `dados`:
      {
        "sensor_id": "SENSOR-RES-001",
        "tipo_sensor": "nivel_agua",   # nivel_agua | vazao | pluviometro | pressao | temperatura
        "valor": 3.72,
        "unidade": "metros",
        "timestamp": "2026-04-15T14:30:00Z",
        "localizacao": {"latitude": ..., "longitude": ..., "descricao": "..."},
        "status": "normal",            # normal | alerta | critico | erro
        "bateria_pct": 87
      }

    Substitua o conteúdo abaixo pela lógica real do Alerta Romano:
      - Salvar no banco de dados
      - Avaliar regras de alerta (nível crítico, vazão anormal, etc.)
      - Disparar notificações quando limiares ultrapassados
    """
    logger.info(
        "[%s] %s = %s %s (status: %s)",
        dados.get("sensor_id"),
        dados.get("tipo_sensor"),
        dados.get("valor"),
        dados.get("unidade"),
        dados.get("status"),
    )

    # TODO: implementar lógica do Alerta Romano aqui
    # Exemplo de regras:
    # if dados["tipo_sensor"] == "nivel_agua" and dados["valor"] > 6.5:
    #     await disparar_alerta(dados, nivel="critico")
    # if dados["tipo_sensor"] == "pluviometro" and dados["valor"] > 80:
    #     await disparar_alerta(dados, nivel="alerta")


# ===========================================================
# INFRAESTRUTURA — não precisa alterar abaixo desta linha
# ===========================================================
async def _on_message(message: AbstractIncomingMessage) -> None:
    """Callback interno: desserializa e despacha para processar_leitura."""
    async with message.process(requeue=False):
        try:
            dados = json.loads(message.body.decode())
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error("Mensagem inválida (routing_key=%s): %s", message.routing_key, exc)
            # requeue=False no context manager → mensagem vai para DLQ
            return

        try:
            await processar_leitura(dados)
        except Exception as exc:
            logger.error("Erro ao processar leitura (routing_key=%s): %s", message.routing_key, exc)
            # Re-raise para nack com requeue=True (falha transitória)
            raise


async def main() -> None:
    logger.info("Alerta Consumer iniciando...")
    connection = await aio_pika.connect_robust(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtualhost=RABBITMQ_VHOST,
        login=RABBITMQ_USER,
        password=RABBITMQ_PASS,
    )

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=PREFETCH_COUNT)

        queue = await channel.get_queue(QUEUE_NAME)
        await queue.consume(_on_message)

        logger.info("Consumindo fila '%s' (prefetch=%d)...", QUEUE_NAME, PREFETCH_COUNT)
        await asyncio.Future()  # mantém o consumer rodando indefinidamente


if __name__ == "__main__":
    asyncio.run(main())
