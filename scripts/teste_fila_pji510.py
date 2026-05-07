"""Script de validação de conectividade com a fila PJI510.

Execute dentro do container worker ANTES de ativar RABBITMQ_ENABLED=true:

    docker compose exec worker python scripts/teste_fila_pji510.py

Ou diretamente no servidor (com aio-pika instalado):

    python3 scripts/teste_fila_pji510.py

O script executa 3 passos:
  1. Teste de porta TCP (rede alcançável?)
  2. Autenticação AMQP + inspeção da fila
  3. Leitura de até 3 mensagens sem ACK (peek — não consome)
"""
from __future__ import annotations

import asyncio
import json
import os
import socket
import sys


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/pji510")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "alerta_consumer")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "sensores.leituras")

RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"


def ok(msg: str) -> None:
    print(f"  {GREEN}✓{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}✗{RESET} {msg}")


def info(msg: str) -> None:
    print(f"  {YELLOW}→{RESET} {msg}")


# ---------------------------------------------------------------------------
# Passo 1 — TCP
# ---------------------------------------------------------------------------
def step1_tcp() -> bool:
    print(f"\n{BOLD}[1/3] Teste de conectividade TCP{RESET}")
    info(f"Conectando em {RABBITMQ_HOST}:{RABBITMQ_PORT} ...")
    try:
        s = socket.create_connection((RABBITMQ_HOST, RABBITMQ_PORT), timeout=5)
        s.close()
        ok(f"Porta {RABBITMQ_PORT} alcançável em {RABBITMQ_HOST}")
        return True
    except OSError as exc:
        fail(f"Falha na conexão TCP: {exc}")
        info("Verifique se o container worker está na rede 'pji510' (docker-compose.yml)")
        return False


# ---------------------------------------------------------------------------
# Passo 2 — Autenticação AMQP + inspeção da fila
# ---------------------------------------------------------------------------
async def step2_amqp() -> bool:
    print(f"\n{BOLD}[2/3] Autenticação AMQP e inspeção da fila{RESET}")
    info(f"VHost={RABBITMQ_VHOST}  User={RABBITMQ_USER}  Queue={RABBITMQ_QUEUE}")

    try:
        import aio_pika  # noqa: PLC0415
    except ImportError:
        fail("aio-pika não instalado. Execute: pip install aio-pika")
        return False

    try:
        conn = await aio_pika.connect(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            virtualhost=RABBITMQ_VHOST,
            login=RABBITMQ_USER,
            password=RABBITMQ_PASSWORD,
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        fail(f"Falha na autenticação AMQP: {exc}")
        info("Verifique RABBITMQ_USER / RABBITMQ_PASSWORD / RABBITMQ_VHOST no .env")
        return False

    ok("Autenticado com sucesso")

    try:
        async with conn:
            channel = await conn.channel()
            queue = await channel.declare_queue(RABBITMQ_QUEUE, passive=True)
            ok(
                f"Fila '{RABBITMQ_QUEUE}' encontrada — "
                f"{queue.declaration_result.message_count} mensagem(ns) aguardando"
            )
            return True
    except Exception as exc:  # noqa: BLE001
        fail(f"Erro ao inspecionar a fila: {exc}")
        info(f"Confirme que a fila '{RABBITMQ_QUEUE}' existe no vhost '{RABBITMQ_VHOST}'")
        return False


# ---------------------------------------------------------------------------
# Passo 3 — Peek: lê até 3 mensagens sem ACK (requeue=True)
# ---------------------------------------------------------------------------
async def step3_peek() -> None:
    print(f"\n{BOLD}[3/3] Preview de mensagens (peek — sem ACK){RESET}")

    try:
        import aio_pika  # noqa: PLC0415
    except ImportError:
        fail("aio-pika não instalado")
        return

    try:
        conn = await aio_pika.connect(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            virtualhost=RABBITMQ_VHOST,
            login=RABBITMQ_USER,
            password=RABBITMQ_PASSWORD,
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        fail(f"Conexão falhou: {exc}")
        return

    shown = 0
    async with conn:
        channel = await conn.channel()
        await channel.set_qos(prefetch_count=3)
        queue = await channel.declare_queue(RABBITMQ_QUEUE, passive=True)

        for _ in range(3):
            msg = await queue.get(fail=False)
            if msg is None:
                break
            try:
                data = json.loads(msg.body)
                ok(
                    f"sensor_id={data.get('sensor_id')}  "
                    f"tipo={data.get('tipo_sensor')}  "
                    f"valor={data.get('valor')} {data.get('unidade')}  "
                    f"status={data.get('status')}"
                )
                shown += 1
            except Exception:  # noqa: BLE001
                info(f"Payload não-JSON: {msg.body[:80]!r}")
            finally:
                # REQUEUE — não consome, apenas visualiza
                await msg.nack(requeue=True)

    if shown == 0:
        info("Fila vazia no momento (nenhuma mensagem para visualizar)")
    else:
        ok(f"{shown} mensagem(ns) visualizada(s) — devolvidas à fila")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main() -> None:
    print(f"\n{BOLD}=== Teste de Integração Fila PJI510 ==={RESET}")
    print(f"Host: {RABBITMQ_HOST}:{RABBITMQ_PORT}  VHost: {RABBITMQ_VHOST}")

    if not RABBITMQ_PASSWORD:
        print(f"\n{RED}AVISO: RABBITMQ_PASSWORD não definida no ambiente!{RESET}")
        print("       Defina a variável antes de executar:")
        print("       export RABBITMQ_PASSWORD='...'")
        sys.exit(1)

    tcp_ok = step1_tcp()
    if not tcp_ok:
        print(f"\n{RED}Abortando — sem conectividade TCP.{RESET}")
        sys.exit(1)

    amqp_ok = await step2_amqp()
    if not amqp_ok:
        print(f"\n{RED}Abortando — falha na autenticação AMQP.{RESET}")
        sys.exit(1)

    await step3_peek()

    print(f"\n{GREEN}{BOLD}Todos os testes passaram!{RESET}")
    print("Para ativar o consumer, adicione ao .env do servidor:")
    print("  RABBITMQ_ENABLED=true")
    print("E reinicie o worker:")
    print("  docker compose up -d worker\n")


if __name__ == "__main__":
    asyncio.run(main())
