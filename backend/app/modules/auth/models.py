"""Auth module — models, schemas, service, repository, router."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RoleEnum(str, enum.Enum):
    admin = "admin"
    gestor = "gestor"
    operador = "operador"


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(
        Enum(RoleEnum, name="role_enum"), nullable=False, default=RoleEnum.operador
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
