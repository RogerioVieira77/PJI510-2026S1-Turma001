"""ARQ background tasks — TASK-62."""
from __future__ import annotations

import json

import structlog
from arq import cron
from arq.connections import RedisSettings
from pywebpush import WebPushException
from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.modules.alertas.adapters.email import EmailAdapter, render_alerta_email
from app.modules.alertas.adapters.webpush import PushAdapter
from app.modules.alertas.models import Alerta
from app.modules.alertas.repository import AlertaRepository
from app.modules.clima.service import ClimaService
from app.modules.ingestao.models import Reservatorio

log = structlog.get_logger()
_settings = get_settings()

_NIVEL_LABELS = {
    "atencao": "ATENÇÃO",
    "alerta": "ALERTA",
    "emergencia": "EMERGÊNCIA",
}


async def startup(ctx: dict) -> None:  # noqa: D401
    ctx["settings"] = _settings


async def shutdown(ctx: dict) -> None:  # noqa: D401
    pass


async def enviar_push_notifications(ctx: dict, alerta_id: int) -> None:
    """ARQ task: send Web Push notifications to all subscribers for an alerta."""
    async with AsyncSessionLocal() as session:
        alerta: Alerta | None = await session.get(Alerta, alerta_id)
        if alerta is None:
            log.warning("worker.push.alerta_nao_encontrado", alerta_id=alerta_id)
            return

        reservatorio: Reservatorio | None = await session.get(
            Reservatorio, alerta.reservatorio_id
        )
        nome = reservatorio.nome if reservatorio else f"Reservatório {alerta.reservatorio_id}"

        repo = AlertaRepository(session)
        subs = await repo.get_all_push()
        if not subs:
            return

        payload = {
            "title": f"PisciniaoMonitor — {_NIVEL_LABELS.get(alerta.nivel.value, alerta.nivel.value)}",
            "body": alerta.mensagem,
            "reservatorio": nome,
            "nivel": alerta.nivel.value,
            "alerta_id": alerta_id,
        }

        for sub in subs:
            subscription_info = {
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            }
            try:
                PushAdapter.send(subscription_info, payload)
                log.info("worker.push.enviado", alerta_id=alerta_id, endpoint=sub.endpoint[:40])
            except WebPushException as exc:
                status_code = getattr(getattr(exc, "response", None), "status_code", None)
                if status_code == 410:
                    # Subscription expired — remove it
                    await repo.delete_push(sub.endpoint)
                    log.info("worker.push.subscription_removida", endpoint=sub.endpoint[:40])
                else:
                    log.error(
                        "worker.push.erro",
                        alerta_id=alerta_id,
                        error=str(exc),
                    )
            except Exception as exc:  # noqa: BLE001
                log.error("worker.push.erro_inesperado", alerta_id=alerta_id, error=str(exc))

        await session.commit()


async def enviar_email_notifications(ctx: dict, alerta_id: int) -> None:
    """ARQ task: send email notifications to all active email subscribers."""
    async with AsyncSessionLocal() as session:
        alerta: Alerta | None = await session.get(Alerta, alerta_id)
        if alerta is None:
            log.warning("worker.email.alerta_nao_encontrado", alerta_id=alerta_id)
            return

        reservatorio: Reservatorio | None = await session.get(
            Reservatorio, alerta.reservatorio_id
        )
        nome = reservatorio.nome if reservatorio else f"Reservatório {alerta.reservatorio_id}"

        repo = AlertaRepository(session)
        subs = await repo.get_active_email_subs(alerta.reservatorio_id)
        if not subs:
            return

        nivel_label = _NIVEL_LABELS.get(alerta.nivel.value, alerta.nivel.value)
        # Extract nivel_pct from the mensagem (approximate fallback)
        nivel_pct_str = alerta.mensagem.split(":")[-1].split("%")[0].strip().split()[-1]
        try:
            nivel_pct = float(nivel_pct_str)
        except ValueError:
            nivel_pct = 0.0

        base_url = _settings.CORS_ORIGINS[0] if _settings.CORS_ORIGINS else "http://localhost"

        for sub in subs:
            try:
                import hmac as _hmac
                import hashlib as _hashlib
                import base64 as _base64

                token = _base64.urlsafe_b64encode(
                    _hmac.new(
                        _settings.SECRET_KEY.encode(),
                        sub.email.encode(),
                        _hashlib.sha256,
                    ).digest()
                ).decode().rstrip("=")

                unsubscribe_url = f"{base_url}/api/v1/alertas/unsubscribe/email?token={token}&email={sub.email}"
                body = render_alerta_email(
                    reservatorio_nome=nome,
                    nivel_label=nivel_label,
                    nivel_pct=nivel_pct,
                    mensagem=alerta.mensagem,
                    unsubscribe_url=unsubscribe_url,
                )
                await EmailAdapter.send(
                    to=sub.email,
                    subject=f"[PisciniaoMonitor] {nivel_label} — {nome}",
                    body_html=body,
                )
                log.info("worker.email.enviado", alerta_id=alerta_id, to=sub.email)
            except Exception as exc:  # noqa: BLE001
                log.error(
                    "worker.email.erro",
                    alerta_id=alerta_id,
                    to=sub.email,
                    error=str(exc),
                )


async def atualizar_clima(ctx: dict) -> None:
    """ARQ cron task: atualiza dados clim\u00e1ticos a cada 30 minutos."""
    async with AsyncSessionLocal() as session:
        service = ClimaService(session)
        result = await service.atualizar_todos_reservatorios()
        log.info("worker.clima.atualizado", ok=result["ok"], erro=result["erro"])


class WorkerSettings:
    functions = [enviar_push_notifications, enviar_email_notifications]
    cron_jobs = [cron(atualizar_clima, minute={0, 30})]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(str(_settings.REDIS_URL))
    max_jobs = 10
    health_check_interval = 30
