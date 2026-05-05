"""Ingestao repository — TASK-41."""
from __future__ import annotations

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestao.models import LeituraSensor


class LeituraRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_insert(self, records: list[dict]) -> int:
        """Insert a batch of readings into the hypertable.

        Uses SQLAlchemy Core INSERT (bulk-optimised) for performance.
        """
        if not records:
            return 0
        await self._session.execute(insert(LeituraSensor), records)
        return len(records)
