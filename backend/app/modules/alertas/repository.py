"""Alertas repository — TASK-61."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alertas.models import (
    Alerta,
    EmailSubscription,
    NivelAlertaEnum,
    PushSubscription,
    StatusAlertaEnum,
)


class AlertaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Alertas ────────────────────────────────────────────────────────────

    async def get_alerta_ativo(self, reservatorio_id: int) -> Alerta | None:
        """Return the most recent active alerta for a reservoir, if any."""
        result = await self._session.execute(
            select(Alerta)
            .where(
                Alerta.reservatorio_id == reservatorio_id,
                Alerta.status == StatusAlertaEnum.ativo,
            )
            .order_by(Alerta.criado_em.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_alerta(
        self,
        reservatorio_id: int,
        nivel: NivelAlertaEnum,
        mensagem: str,
    ) -> Alerta:
        alerta = Alerta(
            reservatorio_id=reservatorio_id,
            nivel=nivel,
            mensagem=mensagem,
            status=StatusAlertaEnum.ativo,
        )
        self._session.add(alerta)
        await self._session.flush()  # populate id
        await self._session.refresh(alerta)
        return alerta

    async def resolve_alerta(self, alerta_id: int, resolvido_em: datetime) -> None:
        await self._session.execute(
            update(Alerta)
            .where(Alerta.id == alerta_id)
            .values(status=StatusAlertaEnum.resolvido, resolvido_em=resolvido_em)
        )

    async def get_by_id(self, alerta_id: int) -> Alerta | None:
        return await self._session.get(Alerta, alerta_id)

    async def list_alertas(
        self,
        reservatorio_id: int | None,
        nivel: NivelAlertaEnum | None,
        start: datetime | None,
        end: datetime | None,
        skip: int,
        limit: int,
    ) -> list[Alerta]:
        stmt = select(Alerta).order_by(Alerta.criado_em.desc())
        if reservatorio_id is not None:
            stmt = stmt.where(Alerta.reservatorio_id == reservatorio_id)
        if nivel is not None:
            stmt = stmt.where(Alerta.nivel == nivel)
        if start is not None:
            stmt = stmt.where(Alerta.criado_em >= start)
        if end is not None:
            stmt = stmt.where(Alerta.criado_em <= end)
        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def reconhecer(self, alerta_id: int) -> Alerta | None:
        """Mark alerta as resolved (reconhecido)."""
        alerta = await self.get_by_id(alerta_id)
        if alerta is None:
            return None
        alerta.status = StatusAlertaEnum.resolvido
        alerta.resolvido_em = datetime.now(__import__("datetime").timezone.utc)
        await self._session.flush()
        await self._session.refresh(alerta)
        return alerta

    # ── Push Subscriptions ─────────────────────────────────────────────────

    async def upsert_push(
        self,
        endpoint: str,
        p256dh: str,
        auth: str,
        usuario_id: int | None,
    ) -> PushSubscription:
        existing = await self._session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )
        sub = existing.scalar_one_or_none()
        if sub is None:
            sub = PushSubscription(
                endpoint=endpoint, p256dh=p256dh, auth=auth, usuario_id=usuario_id
            )
            self._session.add(sub)
        else:
            sub.p256dh = p256dh
            sub.auth = auth
            sub.usuario_id = usuario_id
        await self._session.flush()
        await self._session.refresh(sub)
        return sub

    async def delete_push(self, endpoint: str) -> bool:
        result = await self._session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return False
        await self._session.delete(sub)
        return True

    async def get_all_push(self) -> list[PushSubscription]:
        result = await self._session.execute(select(PushSubscription))
        return list(result.scalars().all())

    async def get_push_by_endpoint(self, endpoint: str) -> PushSubscription | None:
        result = await self._session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )
        return result.scalar_one_or_none()

    # ── Email Subscriptions ────────────────────────────────────────────────

    async def get_email_sub(self, email: str) -> EmailSubscription | None:
        result = await self._session.execute(
            select(EmailSubscription).where(EmailSubscription.email == email)
        )
        return result.scalar_one_or_none()

    async def create_email_sub(
        self, email: str, reservatorio_id: int | None
    ) -> EmailSubscription:
        sub = EmailSubscription(
            email=email,
            reservatorio_id=reservatorio_id,
            ativo=False,  # requires double opt-in confirmation
        )
        self._session.add(sub)
        await self._session.flush()
        await self._session.refresh(sub)
        return sub

    async def activate_email_sub(self, email: str) -> bool:
        result = await self._session.execute(
            select(EmailSubscription).where(EmailSubscription.email == email)
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return False
        sub.ativo = True
        await self._session.flush()
        return True

    async def delete_email_sub(self, email: str) -> bool:
        result = await self._session.execute(
            select(EmailSubscription).where(EmailSubscription.email == email)
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return False
        await self._session.delete(sub)
        return True

    async def get_active_email_subs(
        self, reservatorio_id: int | None = None
    ) -> list[EmailSubscription]:
        stmt = select(EmailSubscription).where(EmailSubscription.ativo.is_(True))
        if reservatorio_id is not None:
            stmt = stmt.where(
                (EmailSubscription.reservatorio_id == reservatorio_id)
                | (EmailSubscription.reservatorio_id.is_(None))
            )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
