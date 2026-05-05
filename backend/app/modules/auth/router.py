from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser, require_role
from app.modules.auth.models import RoleEnum
from app.modules.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserRead,
)
from app.modules.auth.service import AuthService

router = APIRouter()


def _svc(session: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    return AuthService(session)


@router.post("/login", response_model=TokenResponse, summary="Autenticar usuário")
async def login(payload: LoginRequest, svc: Annotated[AuthService, Depends(_svc)]) -> TokenResponse:
    return await svc.login(payload)


@router.post("/refresh", response_model=TokenResponse, summary="Renovar access token")
async def refresh(payload: RefreshRequest, svc: Annotated[AuthService, Depends(_svc)]) -> TokenResponse:
    return await svc.refresh(payload.refresh_token)


@router.get("/me", response_model=UserRead, summary="Perfil do usuário autenticado")
async def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=201,
    summary="Criar novo usuário (apenas admin)",
    dependencies=[require_role(RoleEnum.admin)],
)
async def register(
    payload: UserCreate,
    svc: Annotated[AuthService, Depends(_svc)],
) -> UserRead:
    return await svc.register(payload)


