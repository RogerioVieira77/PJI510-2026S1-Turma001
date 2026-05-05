"""pytest fixtures — EPIC-12.

Fornece:
  - ``app``     — instância FastAPI com lifespan desabilitado
  - ``client``  — httpx.AsyncClient apontando para o app em memória
  - ``db``      — AsyncSession com rollback automático por teste
  - ``seed``    — dados mínimos (reservatório + sensor + usuários)
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app as _fastapi_app
from app.modules.alertas.models import Alerta, NivelAlertaEnum, StatusAlertaEnum
from app.modules.auth.models import RoleEnum, Usuario
from app.modules.ingestao.models import Reservatorio, Sensor, TipoSensorEnum

_settings = get_settings()

# ── Engine de teste (mesma URL de produção, mas transação por teste) ────────

_test_engine = create_async_engine(
    str(_settings.DATABASE_URL),
    echo=False,
    pool_pre_ping=True,
)
_TestSessionLocal = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Escopo de sessão para evitar re-criação de loop entre testes."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    """Cria todas as tabelas no banco de teste (uma vez por sessão pytest)."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Session com SAVEPOINT — faz rollback total após cada teste."""
    async with _test_engine.connect() as conn:
        await conn.begin()
        nested = await conn.begin_nested()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await nested.rollback()
            await conn.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient com override de get_db → db fixture (transação isolada)."""

    async def _override_get_db():
        yield db

    _fastapi_app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=_fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    _fastapi_app.dependency_overrides.clear()


# ── Dados semente mínimos ────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def seed(db: AsyncSession):
    """Cria reservatório, sensor, usuário gestor e usuário operador."""
    reservatorio = Reservatorio(
        nome="Piscinão Norte",
        codigo="RES-001",
        capacidade_m3=50_000,
        latitude=-23.5,
        longitude=-46.6,
    )
    db.add(reservatorio)
    await db.flush()

    sensor = Sensor(
        reservatorio_id=reservatorio.id,
        codigo="SENS-001",
        tipo=TipoSensorEnum.nivel,
        unidade="cm",
        ativo=True,
    )
    db.add(sensor)

    gestor = Usuario(
        nome="Gestor Teste",
        email="gestor@test.com",
        hashed_password=hash_password("Senha1234"),
        role=RoleEnum.gestor,
        ativo=True,
    )
    operador = Usuario(
        nome="Operador Teste",
        email="operador@test.com",
        hashed_password=hash_password("Senha1234"),
        role=RoleEnum.operador,
        ativo=True,
    )
    db.add_all([gestor, operador])
    await db.flush()
    await db.commit()

    return {
        "reservatorio": reservatorio,
        "sensor": sensor,
        "gestor": gestor,
        "operador": operador,
    }


async def _login(client: AsyncClient, email: str, password: str = "Senha1234") -> str:
    """Helper: faz login e retorna access_token."""
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def api_key_headers(key: str | None = None) -> dict[str, str]:
    """Retorna header X-API-Key com a chave correta (ou sobrescrita para testes negativos)."""
    return {"x-api-key": key if key is not None else _settings.INGESTAO_API_KEY}

