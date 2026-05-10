"""Alertas externos — serviço de persistência e consulta."""
from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alertas_externos.models import (
    AlertaDefesaCivil,
    PrevisaoChuva,
    SituacaoDefesaCivil,
)
from app.modules.alertas_externos.schemas import (
    AlertaDefesaCivilPayload,
    AlertasExternosRead,
    AlertaDefesaCivilRead,
    PrevisaoChuvaPayload,
    PrevisaoChuvaRead,
    SituacaoDefesaCivilPayload,
    SituacaoDefesaCivilRead,
)

log = structlog.get_logger()


async def salvar_previsao(payload: PrevisaoChuvaPayload, session: AsyncSession) -> None:
    ts = payload.timestamp or datetime.now(timezone.utc)
    row = PrevisaoChuva(
        regiao=payload.regiao,
        nivel=payload.nivel,
        descricao=payload.descricao,
        precipitacao_mm=payload.precipitacao_mm,
        timestamp=ts,
    )
    session.add(row)
    await session.commit()
    log.info(
        "alertas_externos.previsao_salva",
        regiao=payload.regiao,
        nivel=payload.nivel,
        precipitacao_mm=float(payload.precipitacao_mm),
    )


async def salvar_situacao(payload: SituacaoDefesaCivilPayload, session: AsyncSession) -> None:
    ts = payload.timestamp or datetime.now(timezone.utc)
    alertas = [a.model_dump() for a in payload.alertas_ativos]
    row = SituacaoDefesaCivil(
        status=payload.status,
        alertas_ativos=alertas,
        timestamp=ts,
    )
    session.add(row)
    await session.commit()
    log.info(
        "alertas_externos.situacao_salva",
        status=payload.status,
        n_alertas=len(alertas),
    )


async def salvar_alerta(payload: AlertaDefesaCivilPayload, session: AsyncSession) -> None:
    ts = payload.timestamp or datetime.now(timezone.utc)
    row = AlertaDefesaCivil(
        titulo=payload.titulo,
        descricao=payload.descricao,
        regiao=payload.regiao,
        valido_ate=payload.valido_ate,
        timestamp=ts,
    )
    session.add(row)
    await session.commit()
    log.info(
        "alertas_externos.alerta_salvo",
        titulo=payload.titulo,
        regiao=payload.regiao,
        valido_ate=payload.valido_ate.isoformat(),
    )


async def get_alertas_externos(session: AsyncSession) -> AlertasExternosRead:
    """Retorna os dados mais recentes de cada tipo para o endpoint público."""
    now = datetime.now(timezone.utc)

    # Situação mais recente
    res = await session.execute(
        select(SituacaoDefesaCivil).order_by(desc(SituacaoDefesaCivil.timestamp)).limit(1)
    )
    situacao_row = res.scalar_one_or_none()
    situacao = SituacaoDefesaCivilRead.model_validate(situacao_row) if situacao_row else None

    # Alertas ainda vigentes (valido_ate > now), mais recentes primeiro
    res = await session.execute(
        select(AlertaDefesaCivil)
        .where(AlertaDefesaCivil.valido_ate > now)
        .order_by(desc(AlertaDefesaCivil.timestamp))
    )
    alertas = [AlertaDefesaCivilRead.model_validate(r) for r in res.scalars().all()]

    # Previsão mais recente
    res = await session.execute(
        select(PrevisaoChuva).order_by(desc(PrevisaoChuva.timestamp)).limit(1)
    )
    previsao_row = res.scalar_one_or_none()
    previsao = PrevisaoChuvaRead.model_validate(previsao_row) if previsao_row else None

    return AlertasExternosRead(
        situacao_defesa_civil=situacao,
        alertas_defesa_civil=alertas,
        previsao_chuva=previsao,
    )
