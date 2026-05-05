# ── Stage 1: builder ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .[dev]

# ── Stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Dependências de runtime apenas
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copia pacotes instalados do builder
COPY --from=builder /install /usr/local

# Usuário não-root (critério TASK-10)
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home appuser

COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
