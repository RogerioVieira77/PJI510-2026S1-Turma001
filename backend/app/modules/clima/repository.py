"""ClimaRepository — TASK-111."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clima.models import LeituraClimatica
from app.modules.clima.schemas import PrevisaoClimatica


class ClimaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert(
        self, reservatorio_id: int, dados: PrevisaoClimatica
    ) -> LeituraClimatica:
        leitura = LeituraClimatica(
            reservatorio_id=reservatorio_id,
            timestamp=datetime.now(timezone.utc),
            temperatura_c=dados.temperatura_c,
            umidade_pct=dados.umidade_pct,
            precipitacao_mm=dados.precipitacao_mm,
            velocidade_vento_ms=dados.velocidade_vento_ms,
            condicao=dados.condicao,
        )
        self._session.add(leitura)
        await self._session.flush()
        return leitura

    async def get_latest(self, reservatorio_id: int) -> LeituraClimatica | None:
        stmt = (
            select(LeituraClimatica)
            .where(LeituraClimatica.reservatorio_id == reservatorio_id)
            .order_by(LeituraClimatica.timestamp.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
