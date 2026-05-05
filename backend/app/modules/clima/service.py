"""ClimaService — TASK-111."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from app.modules.clima.client import ClimaServiceException, get_previsao_with_fallback
from app.modules.clima.models import LeituraClimatica
from app.modules.clima.repository import ClimaRepository
from app.modules.ingestao.models import Reservatorio

log = structlog.get_logger()


class ClimaService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def atualizar_todos_reservatorios(self) -> dict[str, int]:
        """Busca previsão climática para todos os reservatórios e persiste.

        Returns:
            Dicionário com contagens ``ok`` e ``erro``.
        """
        stmt = select(Reservatorio)
        result = await self._session.execute(stmt)
        reservatorios = result.scalars().all()

        repo = ClimaRepository(self._session)
        ok = 0
        erros = 0

        for res in reservatorios:
            lat = float(res.latitude)
            lon = float(res.longitude)
            try:
                dados = await get_previsao_with_fallback(lat, lon)
                await repo.insert(res.id, dados)
                ok += 1
                log.info(
                    "clima.service.atualizado",
                    reservatorio_id=res.id,
                    lat=lat,
                    lon=lon,
                )
            except ClimaServiceException as exc:
                erros += 1
                log.error(
                    "clima.service.erro",
                    reservatorio_id=res.id,
                    lat=lat,
                    lon=lon,
                    reason=str(exc),
                )

        await self._session.commit()
        return {"ok": ok, "erro": erros}


async def get_latest_clima(
    reservatorio_id: int, session: AsyncSession
) -> LeituraClimatica | None:
    """Retorna a leitura climática mais recente para um reservatório."""
    repo = ClimaRepository(session)
    return await repo.get_latest(reservatorio_id)
