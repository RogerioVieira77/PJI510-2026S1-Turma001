"""FastAPI dependencies — autenticação e autorização."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.modules.auth.models import RoleEnum, Usuario
from app.modules.auth.repository import AuthRepository

_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(_bearer)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Usuario:
    token = credentials.credentials
    try:
        user_id = decode_token(token, expected_type="access")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    repo = AuthRepository(session)
    user = await repo.get_by_id(int(user_id))
    if not user or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo",
        )
    return user


CurrentUser = Annotated[Usuario, Depends(get_current_user)]


def require_role(*roles: RoleEnum):
    """Dependência que exige um dos roles informados."""

    async def _check(user: CurrentUser) -> Usuario:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente",
            )
        return user

    return Depends(_check)
