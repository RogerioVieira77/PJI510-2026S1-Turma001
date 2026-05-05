"""Auth service."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.auth.models import Usuario
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import LoginRequest, TokenResponse, UserCreate, UserRead


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AuthRepository(session)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self._repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.senha_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
            )
        if not user.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo",
            )
        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            user_id = decode_token(refresh_token, expected_type="refresh")
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc

        user = await self._repo.get_by_id(int(user_id))
        if not user or not user.ativo:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def register(self, payload: UserCreate) -> UserRead:
        existing = await self._repo.get_by_email(payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado",
            )
        usuario = Usuario(
            nome=payload.nome,
            email=payload.email,
            senha_hash=hash_password(payload.password),
            role=payload.role,
        )
        usuario = await self._repo.create(usuario)
        return UserRead.model_validate(usuario)

    async def get_user(self, user_id: int) -> UserRead:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        return UserRead.model_validate(user)

