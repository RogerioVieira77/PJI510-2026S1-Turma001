"""Testes de integração — Módulo de Ingestão IoT — TASK-120.

Cenários cobertos:
  1. Ingestão bem-sucedida (batch com 1 leitura)
  2. Ingestão bem-sucedida (batch com N leituras)
  3. X-API-Key ausente → 401
  4. X-API-Key inválida → 403
  5. Sensor inexistente → 422
  6. Batch com mais de 100 leituras → 422
  7. Leitura com timestamp no futuro → 422
  8. Valor negativo → 422
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from tests.conftest import _login, api_key_headers

pytestmark = pytest.mark.asyncio

_ENDPOINT = "/api/v1/ingestao/leituras"


def _ts(offset_s: int = -10) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


# ── 1. Ingestão bem-sucedida — lote de 1 item ───────────────────────────────

async def test_ingestao_sucesso_batch_simples(client: AsyncClient, seed):
    sensor_id = seed["sensor"].id
    payload = {
        "leituras": [
            {"sensor_id": sensor_id, "timestamp": _ts(), "valor": 200.0, "unidade": "cm"}
        ]
    }
    resp = await client.post(_ENDPOINT, json=payload, headers=api_key_headers())
    assert resp.status_code == 201
    assert resp.json()["inseridos"] == 1


# ── 2. Ingestão bem-sucedida — lote com múltiplas leituras ──────────────────

async def test_ingestao_sucesso_batch_multiplo(client: AsyncClient, seed):
    sensor_id = seed["sensor"].id
    leituras = [
        {"sensor_id": sensor_id, "timestamp": _ts(-i * 10), "valor": 200.0 + i, "unidade": "cm"}
        for i in range(5)
    ]
    resp = await client.post(_ENDPOINT, json={"leituras": leituras}, headers=api_key_headers())
    assert resp.status_code == 201
    assert resp.json()["inseridos"] == 5


# ── 3. X-API-Key ausente → 401 ───────────────────────────────────────────────

async def test_ingestao_sem_api_key_retorna_401(client: AsyncClient, seed):
    sensor_id = seed["sensor"].id
    payload = {
        "leituras": [
            {"sensor_id": sensor_id, "timestamp": _ts(), "valor": 100.0, "unidade": "cm"}
        ]
    }
    resp = await client.post(_ENDPOINT, json=payload)
    assert resp.status_code == 401


# ── 4. X-API-Key inválida → 403 ──────────────────────────────────────────────

async def test_ingestao_api_key_invalida_retorna_403(client: AsyncClient, seed):
    sensor_id = seed["sensor"].id
    payload = {
        "leituras": [
            {"sensor_id": sensor_id, "timestamp": _ts(), "valor": 100.0, "unidade": "cm"}
        ]
    }
    resp = await client.post(_ENDPOINT, json=payload, headers=api_key_headers("chave-errada"))
    assert resp.status_code == 403


# ── 5. Sensor inexistente → 422 ──────────────────────────────────────────────

async def test_ingestao_sensor_inexistente_retorna_422(client: AsyncClient, seed):
    payload = {
        "leituras": [
            {"sensor_id": 999999, "timestamp": _ts(), "valor": 100.0, "unidade": "cm"}
        ]
    }
    resp = await client.post(_ENDPOINT, json=payload, headers=api_key_headers())
    assert resp.status_code == 422


# ── 6. Batch com mais de 100 itens → 422 ────────────────────────────────────

async def test_ingestao_batch_excede_limite_retorna_422(client: AsyncClient, seed):
    sensor_id = seed["sensor"].id
    leituras = [
        {"sensor_id": sensor_id, "timestamp": _ts(-i * 5), "valor": 100.0, "unidade": "cm"}
        for i in range(101)
    ]
    resp = await client.post(_ENDPOINT, json={"leituras": leituras}, headers=api_key_headers())
    assert resp.status_code == 422


# ── 7. Timestamp no futuro → 422 ─────────────────────────────────────────────

async def test_ingestao_timestamp_futuro_retorna_422(client: AsyncClient, seed):
    sensor_id = seed["sensor"].id
    payload = {
        "leituras": [
            {
                "sensor_id": sensor_id,
                "timestamp": _ts(offset_s=3600),  # 1 hora no futuro
                "valor": 100.0,
                "unidade": "cm",
            }
        ]
    }
    resp = await client.post(_ENDPOINT, json=payload, headers=api_key_headers())
    assert resp.status_code == 422


# ── 8. Valor negativo → 422 ──────────────────────────────────────────────────

async def test_ingestao_valor_negativo_retorna_422(client: AsyncClient, seed):
    sensor_id = seed["sensor"].id
    payload = {
        "leituras": [
            {"sensor_id": sensor_id, "timestamp": _ts(), "valor": -1.0, "unidade": "cm"}
        ]
    }
    resp = await client.post(_ENDPOINT, json=payload, headers=api_key_headers())
    assert resp.status_code == 422
