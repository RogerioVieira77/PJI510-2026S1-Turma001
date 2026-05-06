"""Auth schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.modules.auth.models import RoleEnum


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)
    role: RoleEnum = RoleEnum.operador


class UserRead(BaseModel):
    id: int
    nome: str
    email: EmailStr
    role: RoleEnum
    ativo: bool

    model_config = {"from_attributes": True}

