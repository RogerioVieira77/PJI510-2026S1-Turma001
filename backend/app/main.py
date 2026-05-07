from __future__ import annotations

from contextlib import asynccontextmanager

import redis.asyncio as aioredis
import structlog
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.core.exceptions import add_exception_handlers
from app.database import AsyncSessionLocal
import asyncio

from app.modules.auth.router import router as auth_router
from app.modules.ingestao.router import router as ingestao_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.dashboard.router import publico_router, ws_router
from app.modules.alertas.router import router as alertas_router
from app.modules.clima.router import router as clima_router
from app.modules.processamento.service import subscriber_nova_leitura
from app.modules.ingestao.consumer import consumir_fila_continuamente

log = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    log.info("startup", env=settings.APP_ENV)
    task_processamento = asyncio.create_task(subscriber_nova_leitura())
    task_consumer = asyncio.create_task(consumir_fila_continuamente())
    yield
    task_processamento.cancel()
    task_consumer.cancel()
    for task in (task_processamento, task_consumer):
        try:
            await task
        except asyncio.CancelledError:
            pass
    log.info("shutdown")


app = FastAPI(
    title="Alerta Romano API",
    version="0.1.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_exception_handlers(app)

# Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(ingestao_router, prefix="/api/v1/ingestao", tags=["ingestao"])
app.include_router(dashboard_router, prefix="/api/v1/reservatorios", tags=["dashboard"])
app.include_router(publico_router, prefix="/api/v1/publico", tags=["publico"])
app.include_router(alertas_router, prefix="/api/v1/alertas", tags=["alertas"])
app.include_router(clima_router, prefix="/api/v1/reservatorios", tags=["clima"])
app.include_router(ws_router, prefix="/ws", tags=["websocket"])


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/api/v1/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/api/v1/health/db", tags=["infra"])
async def health_db() -> dict[str, str]:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "db": "unreachable"},
        )


@app.get("/api/v1/health/redis", tags=["infra"])
async def health_redis() -> dict[str, str]:
    try:
        client = aioredis.from_url(str(settings.REDIS_URL))
        await client.ping()
        await client.aclose()
        return {"status": "ok", "redis": "connected"}
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "redis": "unreachable"},
        )
