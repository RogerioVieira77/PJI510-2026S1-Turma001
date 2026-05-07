"""Alertas router — TASK-63, TASK-64, TASK-65."""
from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Annotated

import structlog
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import CurrentUser, require_role
from app.modules.alertas.adapters.email import EmailAdapter, render_confirm_email
from app.modules.alertas.models import NivelAlertaEnum, StatusAlertaEnum
from app.modules.alertas.repository import AlertaRepository
from app.modules.alertas.schemas import (
    AlertaRead,
    EmailSubscribeRequest,
    PushSubscribeRequest,
)
from app.modules.auth.models import RoleEnum

log = structlog.get_logger()
router = APIRouter()
_settings = get_settings()


def _make_email_token(email: str) -> str:
    """HMAC-SHA256 token derived from email + SECRET_KEY (no expiry for unsubscribe)."""
    raw = hmac.new(
        _settings.SECRET_KEY.encode(),
        email.encode(),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _verify_email_token(token: str, email: str) -> bool:
    expected = _make_email_token(email)
    # Pad for comparison
    def _pad(s: str) -> str:
        return s + "=" * (-len(s) % 4)

    try:
        return hmac.compare_digest(
            base64.urlsafe_b64decode(_pad(token)),
            base64.urlsafe_b64decode(_pad(expected)),
        )
    except Exception:  # noqa: BLE001
        return False


async def _get_arq():
    pool = await create_pool(RedisSettings.from_dsn(str(_settings.REDIS_URL)))
    try:
        yield pool
    finally:
        await pool.aclose()


# ── CRUD Alertas (TASK-65) ───────────────────────────────────────────────


@router.get("", response_model=list[AlertaRead])
async def listar_alertas(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    reservatorio_id: int | None = Query(None),
    nivel: NivelAlertaEnum | None = Query(None),
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[AlertaRead]:
    repo = AlertaRepository(session)
    alertas = await repo.list_alertas(reservatorio_id, nivel, start, end, skip, limit)
    return [AlertaRead.model_validate(a) for a in alertas]


@router.get("/{alerta_id}", response_model=AlertaRead)
async def detalhe_alerta(
    alerta_id: int,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AlertaRead:
    repo = AlertaRepository(session)
    alerta = await repo.get_by_id(alerta_id)
    if alerta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta não encontrado")
    return AlertaRead.model_validate(alerta)


@router.patch(
    "/{alerta_id}/reconhecer",
    response_model=AlertaRead,
    dependencies=[require_role(RoleEnum.admin, RoleEnum.gestor)],
)
async def reconhecer_alerta(
    alerta_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AlertaRead:
    repo = AlertaRepository(session)
    alerta = await repo.reconhecer(alerta_id)
    if alerta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta não encontrado")
    await session.commit()
    return AlertaRead.model_validate(alerta)


# ── Web Push subscriptions (TASK-63) ─────────────────────────────────────────


@router.post("/subscribe/push", status_code=status.HTTP_201_CREATED)
async def subscribe_push(
    body: PushSubscribeRequest,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    repo = AlertaRepository(session)
    sub = await repo.upsert_push(
        endpoint=body.endpoint,
        p256dh=body.p256dh,
        auth=body.auth,
        usuario_id=current_user.id,
    )
    await session.commit()
    return {"id": sub.id, "endpoint": sub.endpoint}


@router.delete("/subscribe/push", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def unsubscribe_push(
    body: PushSubscribeRequest,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    repo = AlertaRepository(session)
    removed = await repo.delete_push(body.endpoint)
    await session.commit()
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription não encontrada")


# ── Email subscriptions — double opt-in (TASK-64) ─────────────────────────


@router.post("/subscribe/email", status_code=status.HTTP_202_ACCEPTED)
async def subscribe_email(
    body: EmailSubscribeRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    repo = AlertaRepository(session)
    existing = await repo.get_email_sub(body.email)
    if existing and existing.ativo:
        # Idempotent: already subscribed
        return {"message": "Já inscrito"}

    if existing is None:
        await repo.create_email_sub(body.email, body.reservatorio_id)
        await session.commit()

    # Generate confirmation token
    token = _make_email_token(body.email)
    base_url = _settings.CORS_ORIGINS[0] if _settings.CORS_ORIGINS else "http://localhost"
    confirm_url = f"{base_url}/api/v1/alertas/subscribe/email/confirmar?token={token}&email={body.email}"
    unsubscribe_url = f"{base_url}/api/v1/alertas/unsubscribe/email?token={token}&email={body.email}"

    try:
        await EmailAdapter.send(
            to=body.email,
            subject="[Alerta Romano] Confirme sua inscrição de alertas",
            body_html=render_confirm_email(confirm_url, unsubscribe_url),
        )
    except Exception as exc:  # noqa: BLE001
        log.error("alertas.subscribe_email.erro_smtp", email=body.email, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao enviar e-mail de confirmação",
        ) from exc

    return {"message": "E-mail de confirmação enviado"}


@router.get("/subscribe/email/confirmar")
async def confirmar_email(
    token: str = Query(...),
    email: str = Query(...),
    session: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict:
    if not _verify_email_token(token, email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido")
    repo = AlertaRepository(session)
    ok = await repo.activate_email_sub(email)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inscription não encontrada"
        )
    await session.commit()
    return {"message": "Inscrição confirmada com sucesso"}


@router.get("/unsubscribe/email")
async def unsubscribe_email(
    token: str = Query(...),
    email: str = Query(...),
    session: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict:
    if not _verify_email_token(token, email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido")
    repo = AlertaRepository(session)
    removed = await repo.delete_email_sub(email)
    if removed:
        await session.commit()
    return {"message": "Descadastro realizado"}
