"""Auth repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Usuario


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> Usuario | None:
        result = await self._session.execute(
            select(Usuario).where(Usuario.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Usuario | None:
        result = await self._session.execute(
            select(Usuario).where(Usuario.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, usuario: Usuario) -> Usuario:
        self._session.add(usuario)
        await self._session.flush()
        await self._session.refresh(usuario)
        return usuario

