"""Testes de integração — Módulo de Alertas — TASK-121.

Cenários cobertos:
  1. Listagem de alertas autenticada (gestor) — retorna lista
  2. Listagem de alertas sem autenticação → 401
  3. Detalhe de alerta existente (gestor)
  4. Detalhe de alerta inexistente → 404
  5. Reconhecimento de alerta por gestor → 200 (status resolvido)
  6. Reconhecimento de alerta por operador → 403  (RBAC)
  7. Criação de alerta via AlertaRepository diretamente + listagem filtra por reservatório
  8. Listagem filtrada por nível
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alertas.models import Alerta, NivelAlertaEnum, StatusAlertaEnum
from app.modules.alertas.repository import AlertaRepository
from tests.conftest import _login

pytestmark = pytest.mark.asyncio

_ALERTAS_URL = "/api/v1/alertas"


async def _criar_alerta(
    db: AsyncSession, reservatorio_id: int, nivel: NivelAlertaEnum = NivelAlertaEnum.atencao
) -> Alerta:
    repo = AlertaRepository(db)
    alerta = await repo.create_alerta(
        reservatorio_id=reservatorio_id,
        nivel=nivel,
        mensagem=f"Teste nível {nivel.value}",
    )
    await db.commit()
    return alerta


# ── 1. Listagem autenticada (gestor) ────────────────────────────────────────

async def test_listar_alertas_gestor(client: AsyncClient, seed, db: AsyncSession):
    await _criar_alerta(db, seed["reservatorio"].id)
    token = await _login(client, "gestor@test.com")
    resp = await client.get(_ALERTAS_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# ── 2. Listagem sem autenticação → 401 ──────────────────────────────────────

async def test_listar_alertas_sem_auth_retorna_401(client: AsyncClient, seed):
    resp = await client.get(_ALERTAS_URL)
    assert resp.status_code == 401


# ── 3. Detalhe de alerta existente ──────────────────────────────────────────

async def test_detalhe_alerta_existente(client: AsyncClient, seed, db: AsyncSession):
    alerta = await _criar_alerta(db, seed["reservatorio"].id, NivelAlertaEnum.alerta)
    token = await _login(client, "gestor@test.com")
    resp = await client.get(
        f"{_ALERTAS_URL}/{alerta.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == alerta.id
    assert body["nivel"] == "alerta"


# ── 4. Detalhe de alerta inexistente → 404 ──────────────────────────────────

async def test_detalhe_alerta_inexistente_retorna_404(client: AsyncClient, seed):
    token = await _login(client, "gestor@test.com")
    resp = await client.get(
        f"{_ALERTAS_URL}/999999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ── 5. Reconhecimento por gestor → 200 ──────────────────────────────────────

async def test_reconhecer_alerta_gestor(client: AsyncClient, seed, db: AsyncSession):
    alerta = await _criar_alerta(db, seed["reservatorio"].id, NivelAlertaEnum.emergencia)
    token = await _login(client, "gestor@test.com")
    resp = await client.patch(
        f"{_ALERTAS_URL}/{alerta.id}/reconhecer",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "resolvido"
    assert body["resolvido_em"] is not None


# ── 6. Reconhecimento por operador → 403  (RBAC) ────────────────────────────

async def test_reconhecer_alerta_operador_retorna_403(
    client: AsyncClient, seed, db: AsyncSession
):
    alerta = await _criar_alerta(db, seed["reservatorio"].id, NivelAlertaEnum.atencao)
    token = await _login(client, "operador@test.com")
    resp = await client.patch(
        f"{_ALERTAS_URL}/{alerta.id}/reconhecer",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


# ── 7. Filtro por reservatório ───────────────────────────────────────────────

async def test_listar_alertas_filtro_reservatorio(
    client: AsyncClient, seed, db: AsyncSession
):
    rid = seed["reservatorio"].id
    await _criar_alerta(db, rid, NivelAlertaEnum.atencao)
    token = await _login(client, "gestor@test.com")
    resp = await client.get(
        _ALERTAS_URL,
        params={"reservatorio_id": rid},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    alertas = resp.json()
    assert all(a["reservatorio_id"] == rid for a in alertas)


# ── 8. Filtro por nível ──────────────────────────────────────────────────────

async def test_listar_alertas_filtro_nivel(client: AsyncClient, seed, db: AsyncSession):
    rid = seed["reservatorio"].id
    await _criar_alerta(db, rid, NivelAlertaEnum.emergencia)
    await _criar_alerta(db, rid, NivelAlertaEnum.atencao)
    token = await _login(client, "gestor@test.com")
    resp = await client.get(
        _ALERTAS_URL,
        params={"nivel": "emergencia"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    alertas = resp.json()
    assert all(a["nivel"] == "emergencia" for a in alertas)
