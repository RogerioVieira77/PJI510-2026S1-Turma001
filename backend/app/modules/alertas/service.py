"""Alertas service — TASK-61."""
from __future__ import annotations

from datetime import timezone
from datetime import datetime

import structlog
from arq.connections import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alertas.models import NivelAlertaEnum, Alerta
from app.modules.alertas.repository import AlertaRepository
from app.modules.processamento.policies import (
    THRESHOLD_ALERTA,
    THRESHOLD_ATENCAO,
    THRESHOLD_EMERGENCIA,
)

log = structlog.get_logger()


def _nivel_para_enum(nivel_pct: float) -> NivelAlertaEnum | None:
    """Map a percentage level to its NivelAlertaEnum (RN-04).

    Returns None when the level is below the ATENCAO threshold (i.e. normal).
    """
    if nivel_pct >= THRESHOLD_EMERGENCIA:
        return NivelAlertaEnum.emergencia
    if nivel_pct >= THRESHOLD_ALERTA:
        return NivelAlertaEnum.alerta
    if nivel_pct >= THRESHOLD_ATENCAO:
        return NivelAlertaEnum.atencao
    return None  # normal — below ATENCAO threshold


def _mensagem(nivel: NivelAlertaEnum, nivel_pct: float) -> str:
    msgs = {
        NivelAlertaEnum.atencao: f"Nível atingiu atenção: {nivel_pct:.1f}% (limiar {THRESHOLD_ATENCAO}%)",
        NivelAlertaEnum.alerta: f"Nível atingiu alerta: {nivel_pct:.1f}% (limiar {THRESHOLD_ALERTA}%)",
        NivelAlertaEnum.emergencia: f"EMERGÊNCIA: nível crítico {nivel_pct:.1f}% (limiar {THRESHOLD_EMERGENCIA}%)",
    }
    return msgs[nivel]


class AlertaService:
    def __init__(self, session: AsyncSession, arq: ArqRedis | None = None) -> None:
        self._repo = AlertaRepository(session)
        self._arq = arq

    async def avaliar(
        self, reservatorio_id: int, nivel_pct: float
    ) -> Alerta | None:
        """Evaluate thresholds and create/resolve alertas as needed (RN-04).

        Rules:
        - No duplicate alerta when the level stays in the same threshold band.
        - On escalation: resolve previous alerta (if any) + create new one.
        - On de-escalation to normal: resolve active alerta, no new record.
        - Enqueues ARQ tasks for push + email after creating a new alerta.
        """
        nivel_novo = _nivel_para_enum(nivel_pct)
        alerta_ativo = await self._repo.get_alerta_ativo(reservatorio_id)
        nivel_atual = alerta_ativo.nivel if alerta_ativo else None

        # No change — skip
        if nivel_novo == nivel_atual:
            return None

        now = datetime.now(timezone.utc)

        # Resolve previous alerta on any change
        if alerta_ativo is not None:
            await self._repo.resolve_alerta(alerta_ativo.id, now)
            log.info(
                "alertas.resolvido",
                alerta_id=alerta_ativo.id,
                reservatorio_id=reservatorio_id,
                nivel_anterior=nivel_atual,
            )

        # De-escalation to normal — nothing more to do
        if nivel_novo is None:
            log.info("alertas.normalizado", reservatorio_id=reservatorio_id)
            return None

        # Create new alerta
        mensagem = _mensagem(nivel_novo, nivel_pct)
        alerta = await self._repo.create_alerta(reservatorio_id, nivel_novo, mensagem)

        log.info(
            "alertas.criado",
            alerta_id=alerta.id,
            reservatorio_id=reservatorio_id,
            nivel=nivel_novo,
            nivel_pct=nivel_pct,
        )

        # Enqueue ARQ notification tasks
        if self._arq is not None:
            await self._arq.enqueue_job("enviar_push_notifications", alerta.id)
            await self._arq.enqueue_job("enviar_email_notifications", alerta.id)

        return alerta
