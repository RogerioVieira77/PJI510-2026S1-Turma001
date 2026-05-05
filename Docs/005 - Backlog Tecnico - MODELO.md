# Backlog Técnico — PiscinãoMonitor

## Sistema de Monitoramento de Piscinões — Backlog de Construção

**Projeto:** PJI510 — Projeto Integrador em Engenharia da Computação — UNIVESP 2026/S1  
**Versão:** 1.0 | **Data:** 05/05/2026  
**Documento base:** 001 - Plano de Desenvolvimento | 002 - SRS | 003 - PRD | 004 - DevSpecs  
**Objetivo:** Transformar a estratégia técnica em fila executável de trabalho, organizada em épicos e tarefas com critérios de aceite verificáveis.

---

## Regras de Uso

1. A ordem dos épicos respeita **dependências técnicas**: EPIC-00 → EPIC-01 → EPIC-02 → EPIC-03 são pré-requisitos para todos os demais.
2. **Prioridades:** P0 = bloqueante para MVP | P1 = MVP completo | P2 = pós-MVP | P3 = entrega acadêmica
3. Uma tarefa é **concluída** somente quando todos os critérios de aceite estiverem verificados.
4. Cada commit deve referenciar o código da tarefa (`TASK-XX`) no corpo da mensagem.
5. Integrações com APIs externas (EPIC-11) só iniciam após o domínio principal estar estável (EPIC-05 concluído).

---

## Visão Geral dos Épicos

| EPIC | Nome | Prioridade | Tipo | Semanas |
|------|------|------------|------|---------|
| EPIC-00 | Bootstrap do Projeto | P0 | infra | 1-2 |
| EPIC-01 | Infraestrutura e Containerização | P0 | infra | 3-4 |
| EPIC-02 | Banco de Dados e TimescaleDB | P0 | data | 3-4 |
| EPIC-03 | Backend Core (Auth + Core) | P0 | backend | 5-6 |
| EPIC-04 | Módulo de Ingestão IoT | P0 | backend | 6-7 |
| EPIC-05 | Módulo de Processamento | P0 | backend | 7-8 |
| EPIC-06 | Módulo de Alertas e Notificações | P1 | backend | 8-9 |
| EPIC-07 | Endpoints Dashboard (Backend) | P1 | backend | 9-10 |
| EPIC-08 | Frontend Base e PWA | P1 | frontend | 9-10 |
| EPIC-09 | Dashboard Técnico | P1 | frontend | 10-11 |
| EPIC-10 | Dashboard Público | P1 | frontend | 11-12 |
| EPIC-11 | Integração Climática | P2 | backend | 13-14 |
| EPIC-12 | Testes e Qualidade | P2 | qa | 13-14 |
| EPIC-13 | Documentação Final e Entrega | P3 | docs | 15-16 |

---

## EPIC-00 — Bootstrap do Projeto

> Estrutura base do repositório, configuração de ambiente e scaffolding inicial de todos os serviços.

### TASK-00 — Inicialização do Repositório

- **Tipo:** infra
- **Prioridade:** P0
- **Dependências:** nenhuma
- **Entregáveis:**
  - Repositório Git inicializado com branch `main`
  - `.gitignore` cobrindo Python, Node.js, Docker, `.env`
  - `.env.example` com todas as variáveis necessárias documentadas
  - `README.md` com visão geral, pré-requisitos e quickstart
- **Critérios de Aceite:**
  - [ ] `git log` mostra commit inicial com estrutura de pastas
  - [ ] `.env.example` contém chaves: `DB_PASSWORD`, `SECRET_KEY`, `INGESTAO_API_KEY`, `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `REDIS_PASSWORD`
  - [ ] `.gitignore` impede que `.env` seja rastreado
  - [ ] `README.md` contém seções: Visão Geral, Pré-requisitos, Setup Rápido, Arquitetura

### TASK-01 — Scaffold de Diretórios

- **Tipo:** infra
- **Prioridade:** P0
- **Dependências:** TASK-00
- **Entregáveis:**
  - Estrutura de pastas completa conforme PRD seção 7 (`backend/app/modules/`, `frontend/src/`, `nginx/`, `scripts/`)
  - Arquivo `__init__.py` em cada pacote Python
  - `package.json` inicializado no frontend (sem dependências ainda)
- **Critérios de Aceite:**
  - [ ] `tree` da raiz do projeto bate com a estrutura documentada no PRD
  - [ ] Nenhum erro ao navegar pelos diretórios no terminal
  - [ ] `backend/app/modules/` contém: `ingestao/`, `processamento/`, `alertas/`, `dashboard/`, `clima/`, `auth/`, `core/`

### TASK-02 — Docker Compose Skeleton

- **Tipo:** infra
- **Prioridade:** P0
- **Dependências:** TASK-01
- **Entregáveis:**
  - `docker-compose.yml` com 6 serviços declarados (postgres, redis, backend, worker, frontend, nginx)
  - `docker-compose.override.yml` para desenvolvimento (volume mounts, hot reload)
  - Dockerfiles placeholder para `backend/` e `frontend/`
- **Critérios de Aceite:**
  - [ ] `docker compose config` valida sem erros
  - [ ] Healthchecks declarados para `postgres` e `redis`
  - [ ] `depends_on` com `condition: service_healthy` nos serviços backend e worker

### TASK-03 — Script de Geração de Chaves VAPID

- **Tipo:** infra
- **Prioridade:** P0
- **Dependências:** TASK-00
- **Entregáveis:**
  - `scripts/generate_vapid_keys.py` que gera par de chaves VAPID e imprime em formato `.env`
- **Critérios de Aceite:**
  - [ ] `python scripts/generate_vapid_keys.py` imprime `VAPID_PUBLIC_KEY=...` e `VAPID_PRIVATE_KEY=...`
  - [ ] Chaves geradas são válidas para uso com `pywebpush`

---

## EPIC-01 — Infraestrutura e Containerização

> Configuração completa de todos os serviços Docker em produção e NGINX com segurança OWASP.

### TASK-10 — Dockerfile Backend (Produção)

- **Tipo:** infra
- **Prioridade:** P0
- **Dependências:** TASK-02
- **Entregáveis:**
  - `backend/Dockerfile` multi-stage (builder + runtime) para Python 3.12-slim
  - Dependências instaladas via `pip` com `pyproject.toml`
  - Usuário não-root no container
- **Critérios de Aceite:**
  - [ ] `docker build -t piscinao-backend ./backend` conclui sem erros
  - [ ] Container roda como usuário `appuser` (não root)
  - [ ] Imagem final < 500 MB
  - [ ] `docker run --rm piscinao-backend python -c "import fastapi; print(fastapi.__version__)"` exibe versão

### TASK-11 — Dockerfile Frontend (Build + Serve)

- **Tipo:** infra
- **Prioridade:** P0
- **Dependências:** TASK-02
- **Entregáveis:**
  - `frontend/Dockerfile` multi-stage: Node 22-alpine para build, NGINX-alpine para serve
  - Build Vite gerado em `/usr/share/nginx/html`
- **Critérios de Aceite:**
  - [ ] `docker build -t piscinao-frontend ./frontend` conclui sem erros
  - [ ] Acesso a `http://localhost` retorna o `index.html` do React
  - [ ] Bundle JS gzipped ≤ 250 KB conforme RNF-08

### TASK-12 — Configuração NGINX com Segurança OWASP

- **Tipo:** infra
- **Prioridade:** P0
- **Dependências:** TASK-10, TASK-11
- **Entregáveis:**
  - `nginx/nginx.conf` com worker_processes, events, gzip
  - `nginx/conf.d/piscinao.conf` com:
    - Proxy `/api/` → backend:8000
    - Proxy `/ws/` → backend:8000 (WebSocket upgrade)
    - Static files com `try_files $uri /index.html`
    - Headers de segurança: `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Content-Security-Policy`, `Strict-Transport-Security`
    - Rate limiting: zona `general` (burst 20), zona `api` (burst 50), zona `ingestao` (burst 10)
- **Critérios de Aceite:**
  - [ ] `nginx -t` valida configuração sem erros
  - [ ] `curl -I http://localhost/` retorna todos os 6 headers de segurança
  - [ ] `curl -X POST http://localhost/api/v1/ingestao/leituras` com 11 requests em sequência recebe `429 Too Many Requests`
  - [ ] WebSocket conecta via `ws://localhost/ws/publico/1`

### TASK-13 — SSL/TLS com Let's Encrypt (Opcional MVP)

- **Tipo:** infra
- **Prioridade:** P2
- **Dependências:** TASK-12
- **Entregáveis:**
  - Script `scripts/setup_ssl.sh` usando Certbot Docker para obter certificado
  - Configuração NGINX atualizada para porta 443 + redirect 80 → 443
- **Critérios de Aceite:**
  - [ ] `curl -I https://dominio.exemplo.com` retorna 200 com certificado válido
  - [ ] HSTS header presente com `max-age=31536000`

---

## EPIC-02 — Banco de Dados e TimescaleDB

> Configuração do PostgreSQL com TimescaleDB, todas as migrations via Alembic, e seeds de desenvolvimento.

### TASK-20 — Setup Alembic e Conexão Async

- **Tipo:** data
- **Prioridade:** P0
- **Dependências:** TASK-10
- **Entregáveis:**
  - `backend/alembic.ini` configurado com `sqlalchemy.url` via env var
  - `backend/alembic/env.py` com suporte a async SQLAlchemy
  - `backend/app/database.py` com `create_async_engine`, `AsyncSession`, `get_db` dependency
- **Critérios de Aceite:**
  - [ ] `alembic current` executa sem erros (banco vazio, revision `None`)
  - [ ] `alembic upgrade head` executa migration inicial sem erros
  - [ ] `alembic downgrade -1` reverte sem erros

### TASK-21 — Migration: Entidades Relacionais Base

- **Tipo:** data
- **Prioridade:** P0
- **Dependências:** TASK-20
- **Entregáveis:**
  - Migration Alembic criando as tabelas: `usuario`, `reservatorio`, `sensor`, `alerta`, `historico_alerta`, `push_subscription`, `email_subscription`
  - Models SQLAlchemy declarados em `app/modules/*/models.py`
- **Critérios de Aceite:**
  - [ ] `alembic upgrade head` cria todas as 7 tabelas no banco
  - [ ] Constraints de FK, UNIQUE e NOT NULL presentes conforme SRS seção 8
  - [ ] `alembic downgrade -1` remove todas as tabelas criadas
  - [ ] `alembic check` não indica pendências

### TASK-22 — Migration: Hypertables TimescaleDB

- **Tipo:** data
- **Prioridade:** P0
- **Dependências:** TASK-21
- **Entregáveis:**
  - `scripts/setup_timescaledb.sql` com:
    - `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;`
    - `SELECT create_hypertable('leitura_sensor', 'timestamp')` com chunk_time_interval de 7 dias
    - `SELECT create_hypertable('leitura_climatica', 'timestamp')` com chunk_time_interval de 7 dias
  - Migration Alembic criando tabelas `leitura_sensor` e `leitura_climatica` e executando `SELECT create_hypertable`
- **Critérios de Aceite:**
  - [ ] `SELECT * FROM timescaledb_information.hypertables;` retorna 2 hypertables
  - [ ] INSERT de 1000 registros em `leitura_sensor` executa em < 500ms
  - [ ] `SELECT show_chunks('leitura_sensor')` retorna chunks após inserções

### TASK-23 — Continuous Aggregates e Compressão

- **Tipo:** data
- **Prioridade:** P0
- **Dependências:** TASK-22
- **Entregáveis:**
  - Migration ou script SQL criando:
    - View `leitura_sensor_hourly` (média/min/max de `nivel_cm` por hora por sensor)
    - View `leitura_sensor_daily` (média/min/max de `nivel_cm` por dia por sensor)
  - Política de compressão ativada em `leitura_sensor` (segmentos > 7 dias)
  - Política de retenção configurada (dado bruto: 1 ano, agregado diário: 5 anos)
- **Critérios de Aceite:**
  - [ ] `SELECT * FROM timescaledb_information.continuous_aggregates;` retorna 2 views
  - [ ] Query em `leitura_sensor_hourly` para 30 dias retorna em < 200ms
  - [ ] `SELECT * FROM timescaledb_information.compression_settings;` mostra configuração ativa

### TASK-24 — Seeds de Desenvolvimento

- **Tipo:** data
- **Prioridade:** P0
- **Dependências:** TASK-21
- **Entregáveis:**
  - `scripts/seed_dev.sql` inserindo:
    - 1 reservatório (`id=1`, nome="Piscinão Aricanduva", capacidade_m3=1500000, area_secao_m2=250000)
    - 2 sensores (`id=1` nível, `id=2` pluviometria)
    - 1 usuário admin (`admin@piscinao.local`, role=admin)
    - 500 leituras históricas simuladas nas últimas 48h em `leitura_sensor`
- **Critérios de Aceite:**
  - [ ] `psql ... -f scripts/seed_dev.sql` executa sem erros
  - [ ] `SELECT COUNT(*) FROM leitura_sensor;` retorna ≥ 500
  - [ ] `SELECT COUNT(*) FROM reservatorio;` retorna 1
  - [ ] `SELECT COUNT(*) FROM sensor;` retorna 2

---

## EPIC-03 — Backend Core (Auth + Core)

> FastAPI app factory, configurações, health checks e módulo de autenticação JWT + RBAC.

### TASK-30 — FastAPI App Factory e Configuração

- **Tipo:** backend
- **Prioridade:** P0
- **Dependências:** TASK-20
- **Entregáveis:**
  - `backend/app/main.py` com função `create_app()` que registra routers, middleware e exception handlers
  - `backend/app/config.py` com `class Settings(BaseSettings)` lendo todas as vars de `.env`
  - `backend/app/core/middleware.py` com CORS configurado (origins configurável via env)
  - `backend/app/core/exceptions.py` com handlers globais para `HTTPException` e `ValidationError`
- **Critérios de Aceite:**
  - [ ] `uvicorn app.main:app --reload` inicia sem erros
  - [ ] `GET /docs` retorna a UI do Swagger
  - [ ] `GET /openapi.json` retorna schema OpenAPI válido
  - [ ] Request com `Origin: http://evil.com` recebe `403` se não estiver em `CORS_ORIGINS`

### TASK-31 — Health Check Endpoints

- **Tipo:** backend
- **Prioridade:** P0
- **Dependências:** TASK-30
- **Entregáveis:**
  - `GET /health` → `{"status": "ok", "timestamp": "..."}`
  - `GET /health/db` → verifica conectividade PostgreSQL
  - `GET /health/redis` → verifica conectividade Redis
- **Critérios de Aceite:**
  - [ ] `curl localhost:8000/health` retorna HTTP 200 com JSON `{"status": "ok"}`
  - [ ] `curl localhost:8000/health/db` retorna `{"status": "ok", "db": "connected"}` quando banco está UP
  - [ ] `curl localhost:8000/health/db` retorna HTTP 503 quando banco está DOWN
  - [ ] NGINX healthcheck configurado com `GET /health`

### TASK-32 — Módulo Auth: Modelos e Schemas

- **Tipo:** backend
- **Prioridade:** P0
- **Dependências:** TASK-21
- **Entregáveis:**
  - `app/modules/auth/models.py`: model `Usuario` (id, email, password_hash, role, ativo, created_at)
  - `app/modules/auth/schemas.py`: `LoginRequest`, `TokenResponse`, `RefreshRequest`, `UserCreate`, `UserRead`
  - `app/core/security.py`: `hash_password()`, `verify_password()`, `create_access_token()`, `create_refresh_token()`, `decode_token()`
- **Critérios de Aceite:**
  - [ ] Passwords armazenados com bcrypt (factor ≥ 12)
  - [ ] JWT access token expira em 30 minutos
  - [ ] JWT refresh token expira em 7 dias
  - [ ] `decode_token()` lança exceção para token inválido ou expirado

### TASK-33 — Módulo Auth: Endpoints e RBAC

- **Tipo:** backend
- **Prioridade:** P0
- **Dependências:** TASK-32
- **Entregáveis:**
  - `POST /api/v1/auth/login` — recebe email/password, retorna access_token + refresh_token
  - `POST /api/v1/auth/refresh` — recebe refresh_token, retorna novo access_token
  - `GET /api/v1/auth/me` — retorna perfil do usuário autenticado
  - `backend/app/dependencies.py`: `get_current_user()` dependency que valida Bearer token
  - Decorator `require_role(roles: list[str])` para proteger endpoints por perfil (admin, gestor, operador)
- **Critérios de Aceite:**
  - [ ] `POST /login` com credenciais válidas retorna HTTP 200 com tokens
  - [ ] `POST /login` com senha errada retorna HTTP 401
  - [ ] `GET /auth/me` sem Bearer token retorna HTTP 401
  - [ ] `GET /auth/me` com token expirado retorna HTTP 401
  - [ ] Endpoint marcado com `require_role(["admin"])` retorna 403 para usuário `operador`

---

## EPIC-04 — Módulo de Ingestão IoT

> Endpoint de recebimento de leituras dos sensores com autenticação por API Key e validação Pydantic.

### TASK-40 — Schemas e Validação de Leituras

- **Tipo:** backend
- **Prioridade:** P0
- **Dependências:** TASK-22
- **Entregáveis:**
  - `app/modules/ingestao/schemas.py`:
    - `LeituraCreate`: sensor_id (int), timestamp (datetime), valor (float), unidade (str)
    - `LeituraBatchCreate`: leituras (list[LeituraCreate], max 100 itens)
    - `LeituraResponse`: id, sensor_id, timestamp, valor, unidade, created_at
  - Validações Pydantic: valor não negativo, timestamp não futuro, unidade em enum permitido
- **Critérios de Aceite:**
  - [ ] `LeituraCreate(valor=-1)` lança `ValidationError`
  - [ ] `LeituraCreate(timestamp=future_datetime)` lança `ValidationError`
  - [ ] `LeituraBatchCreate(leituras=[...] * 101)` lança `ValidationError` (max 100)
  - [ ] Schema documentado no OpenAPI com exemplos

### TASK-41 — Repository e Service de Ingestão

- **Tipo:** backend
- **Prioridade:** P0
- **Dependências:** TASK-40
- **Entregáveis:**
  - `app/modules/ingestao/repository.py`: `LeituraRepository.bulk_insert(leituras: list)` async
  - `app/modules/ingestao/service.py`: `IngestaoService.processar_lote(batch: LeituraBatchCreate)` que:
    1. Valida que todos os `sensor_id` existem no banco
    2. Persiste no hypertable via repository
    3. Publica evento `nova_leitura:{reservatorio_id}` no Redis pub/sub
- **Critérios de Aceite:**
  - [ ] 100 leituras em batch persistem em < 500ms (P95)
  - [ ] Leitura com `sensor_id` inexistente retorna erro 422 com mensagem clara
  - [ ] Evento Redis publicado após inserção verificado via `redis-cli SUBSCRIBE`

### TASK-42 — Router de Ingestão com API Key Auth

- **Tipo:** backend
- **Prioridade:** P0
- **Dependências:** TASK-41
- **Entregáveis:**
  - `app/modules/ingestao/router.py`:
    - `POST /api/v1/ingestao/leituras` autenticado por `X-API-Key` header
    - Dependency `get_api_key()` que valida contra `INGESTAO_API_KEY` env var
- **Critérios de Aceite:**
  - [ ] `POST /ingestao/leituras` com X-API-Key correta retorna HTTP 201
  - [ ] `POST /ingestao/leituras` sem X-API-Key retorna HTTP 401
  - [ ] `POST /ingestao/leituras` com X-API-Key errada retorna HTTP 403
  - [ ] Rate limit NGINX de 10 req/s na rota `/api/v1/ingestao/` funcionando

---

## EPIC-05 — Módulo de Processamento

> Cálculos das regras de negócio (RN-01 a RN-06) com base nas leituras ingeridas.

### TASK-50 — Políticas de Cálculo (RN-01 a RN-06)

- **Tipo:** backend
- **Prioridade:** P0
- **Dependências:** TASK-42
- **Entregáveis:**
  - `app/modules/processamento/policies.py` com funções puras:
    - `calcular_volume(nivel_cm: float, area_m2: float) -> float` — RN-01: $V = h \times A$
    - `calcular_taxa_variacao(leituras: list[float], timestamps: list[datetime]) -> float` — RN-02: Δh/Δt em cm/min
    - `estimar_tempo_transbordo(nivel_cm: float, capacidade_cm: float, taxa: float) -> Optional[float]` — RN-03: minutos até transbordo
    - `detectar_divergencia_sensores(leituras_sensores: dict[int, float]) -> bool` — RN-06: diferença > 10% entre sensores redundantes
    - `correlacionar_pluviometria(nivel_taxa: float, chuva_mm: float) -> str` — RN-05: classificação da correlação
- **Critérios de Aceite:**
  - [ ] `calcular_volume(nivel_cm=200, area_m2=250000)` retorna `500000.0` (m³)
  - [ ] `calcular_taxa_variacao` com nível constante retorna `0.0`
  - [ ] `estimar_tempo_transbordo` com taxa negativa ou zero retorna `None`
  - [ ] `detectar_divergencia_sensores({1: 100.0, 2: 115.0})` retorna `True` (15% > 10%)
  - [ ] Testes unitários para todos os 5 casos acima com ≥ 80% coverage

### TASK-51 — Service de Processamento

- **Tipo:** backend
- **Prioridade:** P0
- **Dependências:** TASK-50
- **Entregáveis:**
  - `app/modules/processamento/service.py`: `ProcessamentoService.processar_reservatorio(reservatorio_id: int)` que:
    1. Busca últimas N leituras do reservatório
    2. Aplica todas as políticas (TASK-50)
    3. Atualiza `reservatorio.status_calculado` e campos derivados
    4. Publica resultado no Redis pub/sub para WebSocket
- **Critérios de Aceite:**
  - [ ] Service chamado automaticamente via subscriber Redis quando nova leitura chega (TASK-41)
  - [ ] `reservatorio.nivel_atual_pct` atualizado corretamente após processamento
  - [ ] Log estruturado gerado para cada processamento com nível atual e taxa

### TASK-52 — Testes Unitários do Módulo de Processamento

- **Tipo:** qa
- **Prioridade:** P0
- **Dependências:** TASK-50, TASK-51
- **Entregáveis:**
  - `backend/tests/unit/test_processamento_policies.py` com ≥ 15 casos de teste
  - Coverage ≥ 80% para `policies.py` e `service.py`
- **Critérios de Aceite:**
  - [ ] `pytest tests/unit/test_processamento_policies.py -v` passa todos os testes
  - [ ] `pytest --cov=app/modules/processamento --cov-report=term` mostra ≥ 80%
  - [ ] Casos de borda testados: nivel=0, nivel=capacidade, taxa negativa, sensores ausentes

---

## EPIC-06 — Módulo de Alertas e Notificações

> Avaliação de thresholds, geração de alertas, ARQ worker e dispatch multicanal (Push + Email).

### TASK-60 — Modelos, Schemas e Thresholds (RN-04)

- **Tipo:** backend
- **Prioridade:** P1
- **Dependências:** TASK-51
- **Entregáveis:**
  - `app/modules/alertas/models.py`: `Alerta` (id, reservatorio_id, nivel, mensagem, status, created_at), `PushSubscription`, `EmailSubscription`
  - `app/modules/alertas/schemas.py`: `AlertaRead`, `AlertaCreate`, `PushSubscribeRequest`, `EmailSubscribeRequest`
  - Constantes de threshold em `policies.py`: ATENCAO=60%, ALERTA=80%, CRITICO=95% (conforme RN-04)
- **Critérios de Aceite:**
  - [ ] Thresholds documentados em código com referência à RN-04
  - [ ] Schema `AlertaRead` inclui: id, nivel (enum: ATENCAO/ALERTA/CRITICO/NORMAL), mensagem_pt, reservatorio_id, created_at
  - [ ] `alembic upgrade head` cria tabelas `alerta`, `push_subscription`, `email_subscription`

### TASK-61 — Service de Avaliação de Alertas

- **Tipo:** backend
- **Prioridade:** P1
- **Dependências:** TASK-60
- **Entregáveis:**
  - `app/modules/alertas/service.py`: `AlertaService.avaliar(reservatorio_id, nivel_pct)` que:
    1. Verifica se o nível cruzou um threshold (escalada ou desescalada)
    2. Cria registro em `alerta` apenas se houve mudança de nível
    3. Enfileira task ARQ para dispatch de notificações
  - Lógica de **de-escalada**: quando nível volta abaixo do threshold, emite alerta de normalização
- **Critérios de Aceite:**
  - [ ] Não cria alerta duplicado se nível permanece no mesmo threshold
  - [ ] Cria alerta de normalização quando nível cai de ALERTA para NORMAL
  - [ ] Task ARQ enfileirada verificável via `arq info`
  - [ ] Teste unitário para escalada e de-escalada

### TASK-62 — ARQ Worker e Tasks de Notificação

- **Tipo:** backend
- **Prioridade:** P1
- **Dependências:** TASK-61
- **Entregáveis:**
  - `app/worker/tasks.py` com:
    - `class WorkerSettings`: configuração ARQ (Redis URL, max_jobs, health_check_interval)
    - `async def enviar_push_notifications(ctx, alerta_id: int)` — busca subscribers e envia via adapter
    - `async def enviar_email_notifications(ctx, alerta_id: int)` — busca subscribers e envia via adapter
  - Container `worker` no Docker Compose executando `python -m arq app.worker.tasks.WorkerSettings`
- **Critérios de Aceite:**
  - [ ] `docker compose up worker` inicia sem erros
  - [ ] Task `enviar_push_notifications` aparece em `arq info` após ser enfileirada
  - [ ] Falhas de envio são logadas com alerta_id e tipo de erro (sem crashar o worker)
  - [ ] Worker respeita `max_jobs=10` (não sobrecarrega SMTP)

### TASK-63 — Adapter: Web Push (VAPID)

- **Tipo:** backend
- **Prioridade:** P1
- **Dependências:** TASK-62
- **Entregáveis:**
  - `app/modules/alertas/adapters/push.py`: `PushAdapter.send(subscription: dict, payload: dict)` usando `pywebpush`
  - `POST /api/v1/alertas/subscribe/push` — salva subscription do browser
  - `DELETE /api/v1/alertas/subscribe/push` — remove subscription
- **Critérios de Aceite:**
  - [ ] `PushAdapter.send()` com subscription válida envia notificação ao browser (testado manualmente)
  - [ ] `PushAdapter.send()` com subscription expirada captura `WebPushException` e remove do banco
  - [ ] `POST /subscribe/push` retorna HTTP 201 com subscription salva
  - [ ] Push recebido no browser inclui: título do alerta, nível (ATENÇÃO/ALERTA/CRÍTICO), nome do reservatório

### TASK-64 — Adapter: Email (SMTP) + Double Opt-In

- **Tipo:** backend
- **Prioridade:** P1
- **Dependências:** TASK-62
- **Entregáveis:**
  - `app/modules/alertas/adapters/email.py`: `EmailAdapter.send(to: str, subject: str, body: str)` usando `aiosmtplib`
  - `POST /api/v1/alertas/subscribe/email` — inicia double opt-in (envia email de confirmação)
  - `GET /api/v1/alertas/subscribe/email/confirmar?token=...` — confirma assinatura
  - `GET /api/v1/alertas/unsubscribe/email?token=...` — descadastra email
  - Template HTML de email com link de descadastro incluído no rodapé
- **Critérios de Aceite:**
  - [ ] `POST /subscribe/email` envia email de confirmação e retorna HTTP 202
  - [ ] Email não ativado não recebe notificações de alerta
  - [ ] Link de descadastro remove assinatura sem necessidade de login
  - [ ] `EmailAdapter.send()` usa conexão async com TLS (STARTTLS ou SSL)

### TASK-65 — CRUD de Alertas (Endpoints Técnicos)

- **Tipo:** backend
- **Prioridade:** P1
- **Dependências:** TASK-61
- **Entregáveis:**
  - `GET /api/v1/alertas` — lista alertas com filtros (reservatorio_id, nivel, período)
  - `GET /api/v1/alertas/{id}` — detalhe de alerta
  - `PATCH /api/v1/alertas/{id}/reconhecer` — marca como reconhecido (requer role gestor ou admin)
- **Critérios de Aceite:**
  - [ ] `GET /alertas?reservatorio_id=1&nivel=CRITICO` retorna apenas alertas críticos do reservatório 1
  - [ ] `PATCH /alertas/1/reconhecer` por usuário `operador` retorna HTTP 403
  - [ ] `PATCH /alertas/1/reconhecer` por usuário `gestor` retorna HTTP 200

---

## EPIC-07 — Endpoints Dashboard (Backend)

> Endpoints REST e WebSocket para alimentar os dashboards técnico e público.

### TASK-70 — Endpoints de Reservatórios

- **Tipo:** backend
- **Prioridade:** P1
- **Dependências:** TASK-51
- **Entregáveis:**
  - `GET /api/v1/reservatorios` — lista todos os reservatórios com status atual
  - `GET /api/v1/reservatorios/{id}` — detalhe de um reservatório
  - `GET /api/v1/reservatorios/{id}/status` — status calculado atual (nível%, volume, taxa, tempo_transbordo)
  - `GET /api/v1/reservatorios/{id}/historico?periodo=24h` — série histórica de leituras (1h, 6h, 24h, 7d, 30d)
  - `GET /api/v1/reservatorios/{id}/alertas` — alertas ativos do reservatório
- **Critérios de Aceite:**
  - [ ] `GET /reservatorios` retorna lista com campos: id, nome, coordenadas, capacidade_m3, nivel_atual_pct, status
  - [ ] `GET /reservatorios/1/historico?periodo=24h` retorna ≤ 1440 pontos (1 por minuto)
  - [ ] `GET /reservatorios/1/historico?periodo=7d` usa continuous aggregate (horário) para performance
  - [ ] Tempo de resposta P95 ≤ 200ms para todos os endpoints

### TASK-71 — Endpoint Público

- **Tipo:** backend
- **Prioridade:** P1
- **Dependências:** TASK-70
- **Entregáveis:**
  - `GET /api/v1/publico/status` — retorna lista simplificada de todos os reservatórios (sem auth)
  - Campos expostos: id, nome, status (NORMAL/ATENCAO/ALERTA/CRITICO), nivel_pct, ultima_atualizacao
  - **Sem** dados técnicos sensíveis (coordenadas GPS omitidas ou aproximadas)
- **Critérios de Aceite:**
  - [ ] `GET /publico/status` não requer header `Authorization`
  - [ ] Resposta cacheada no Redis por 30 segundos para reduzir carga
  - [ ] Schema não expõe dados de sensores individuais nem histórico

### TASK-72 — WebSocket Dashboard Técnico

- **Tipo:** backend
- **Prioridade:** P1
- **Dependências:** TASK-70
- **Entregáveis:**
  - `WS /ws/dashboard/{reservatorio_id}` — requer JWT Bearer no handshake (query param `token`)
  - Publica mensagem JSON a cada nova leitura processada com status completo
  - Desconecta cliente após token expirado
- **Critérios de Aceite:**
  - [ ] `wscat -c "ws://localhost/ws/dashboard/1?token=VALID_JWT"` conecta e recebe mensagens
  - [ ] `wscat -c "ws://localhost/ws/dashboard/1?token=INVALID"` recebe `4001 Unauthorized`
  - [ ] Múltiplos clientes WS para o mesmo reservatório recebem mensagens simultaneamente
  - [ ] Mensagem inclui: nivel_cm, nivel_pct, volume_m3, taxa_cm_min, tempo_transbordo_min, status, timestamp

### TASK-73 — WebSocket Dashboard Público

- **Tipo:** backend
- **Prioridade:** P1
- **Dependências:** TASK-71
- **Entregáveis:**
  - `WS /ws/publico/{reservatorio_id}` — sem autenticação
  - Publica apenas: status (NORMAL/ATENCAO/ALERTA/CRITICO), nivel_pct, ultima_atualizacao
- **Critérios de Aceite:**
  - [ ] `wscat -c "ws://localhost/ws/publico/1"` conecta sem token
  - [ ] Mensagem pública não inclui taxa, tempo de transbordo ou dados de sensores individuais
  - [ ] Rate limit de 1 conexão simultânea por IP (NGINX limit_conn)

---

## EPIC-08 — Frontend Base e PWA

> Scaffolding do projeto React, configuração de dependências, autenticação e Service Worker.

### TASK-80 — Setup Vite + React + TypeScript

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-02
- **Entregáveis:**
  - `frontend/` com `npm create vite@latest` (React + TypeScript)
  - Dependências instaladas: `react-router-dom`, `@tanstack/react-query`, `zustand`, `axios`, `recharts`, `leaflet`, `react-leaflet`
  - `tailwind.config.ts` configurado com purge correto
  - `shadcn/ui` inicializado (`npx shadcn-ui@latest init`)
  - `tsconfig.json` com `strict: true`, path aliases `@/` → `src/`
- **Critérios de Aceite:**
  - [ ] `npm run dev` inicia servidor de dev sem erros
  - [ ] `npm run build` gera `dist/` sem erros de TypeScript
  - [ ] `npm run type-check` (tsc --noEmit) passa sem erros
  - [ ] Bundle final gzipped ≤ 250 KB

### TASK-81 — Axios Client com JWT Interceptor

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-80, TASK-33
- **Entregáveis:**
  - `src/api/client.ts`: Axios instance com `baseURL=/api/v1`
  - Request interceptor: adiciona `Authorization: Bearer <token>` de `useAuthStore`
  - Response interceptor: captura `401`, tenta refresh token; se falhar, redireciona para `/login`
- **Critérios de Aceite:**
  - [ ] Request para endpoint autenticado sem token retorna 401 e redireciona para `/login`
  - [ ] Request com token expirado dispara refresh automaticamente sem o usuário perceber
  - [ ] Após logout (`clearAuth()` no Zustand), requests não enviam token

### TASK-82 — Zustand Auth Store + Rotas Protegidas

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-81
- **Entregáveis:**
  - `src/store/auth.ts`: Zustand store com `token`, `refreshToken`, `user`, `setAuth()`, `clearAuth()`
  - Token persistido no `localStorage` (com `zustand/middleware/persist`)
  - `src/App.tsx` com `react-router-dom` configurando rotas:
    - `/` → `PublicDashboard` (sem proteção)
    - `/dashboard` → `TechDashboard` (requer auth: role gestor/admin)
    - `/login` → `Login`
    - `/admin` → `Admin` (requer auth: role admin)
- **Critérios de Aceite:**
  - [ ] Acesso a `/dashboard` sem token redireciona para `/login`
  - [ ] Após login bem-sucedido, token salvo no localStorage persiste após refresh de página
  - [ ] `clearAuth()` remove token do localStorage e do store
  - [ ] Usuário `operador` acessando `/admin` recebe página 403

### TASK-83 — PWA: Manifest e Service Worker

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-80
- **Entregáveis:**
  - `vite.config.ts` com `vite-plugin-pwa` configurado: `registerType: 'autoUpdate'`, estratégia `CacheFirst` para assets
  - `public/manifest.json`: name, short_name, theme_color, background_color, icons (192×192, 512×512, maskable)
  - `src/sw.ts` com precache de shell (index.html, JS, CSS) e runtime cache para `/api/v1/publico/status`
  - Ícones da aplicação gerados em todos os tamanhos requeridos
- **Critérios de Aceite:**
  - [ ] Chrome DevTools > Application > Manifest: sem erros
  - [ ] Chrome DevTools > Application > Service Workers: worker ativo
  - [ ] Com rede offline (DevTools Network throttle), `PublicDashboard` carrega do cache
  - [ ] "Add to Home Screen" disponível em dispositivo Android/iOS

### TASK-84 — Hook de Push Subscription (VAPID)

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-83, TASK-63
- **Entregáveis:**
  - `src/hooks/usePushSubscription.ts`:
    - `subscribe()`: solicita permissão, cria subscription via `PushManager.subscribe()`, envia para `POST /alertas/subscribe/push`
    - `unsubscribe()`: remove subscription local e `DELETE /alertas/subscribe/push`
    - Estado: `isSubscribed`, `isLoading`, `error`
- **Critérios de Aceite:**
  - [ ] `subscribe()` chama `Notification.requestPermission()` antes de criar subscription
  - [ ] VAPID `applicationServerKey` carregado de variável de ambiente `VITE_VAPID_PUBLIC_KEY`
  - [ ] Se permissão negada pelo usuário, `error` é definido com mensagem amigável
  - [ ] Push recebida no browser enquanto aba está fechada (testado em Chrome)

---

## EPIC-09 — Dashboard Técnico

> Interface completa para gestores e operadores com mapa, gráficos e dados em tempo real.

### TASK-90 — Componente: Mapa Leaflet com Reservatórios

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-82, TASK-70
- **Entregáveis:**
  - `src/components/ReservoirMap.tsx`: mapa Leaflet com `react-leaflet`
  - Marcadores coloridos por status: verde (NORMAL), amarelo (ATENCAO), laranja (ALERTA), vermelho (CRITICO)
  - Popup ao clicar: nome, nível%, status, última atualização
  - Tiles OpenStreetMap
- **Critérios de Aceite:**
  - [ ] Mapa renderiza na página sem erros de console
  - [ ] Marcadores mudam de cor quando status do reservatório muda (via WebSocket)
  - [ ] Mapa é responsivo e funciona em tela de 320px de largura (mobile)
  - [ ] Tiles carregados via HTTPS (sem mixed content warning)

### TASK-91 — Componente: Gráfico de Nível (Série Temporal)

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-70
- **Entregáveis:**
  - `src/components/LevelChart.tsx`: Recharts `LineChart` com eixo X de tempo
  - Seletor de período: 1h / 6h / 24h / 7d / 30d
  - Linhas de referência horizontal nos thresholds: 60%, 80%, 95%
  - Tooltip com timestamp e valor exato
- **Critérios de Aceite:**
  - [ ] Troca de período refaz a query e atualiza o gráfico
  - [ ] Linhas de threshold visíveis com labels "Atenção / Alerta / Crítico"
  - [ ] Gráfico responsivo (`ResponsiveContainer width="100%"`)
  - [ ] Loading skeleton exibido durante fetch

### TASK-92 — Painel de Indicadores em Tempo Real

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-72
- **Entregáveis:**
  - `src/components/SensorStatusPanel.tsx`: cards com dados do WebSocket (`/ws/dashboard/{id}`)
  - Cards: Nível Atual (%), Volume Atual (m³), Taxa de Variação (cm/min), Estimativa de Transbordo (min), Status dos Sensores
  - Hook `src/hooks/useWebSocket.ts` com reconexão automática (exponential backoff)
- **Critérios de Aceite:**
  - [ ] Dados atualizados sem necessidade de reload quando nova leitura chega
  - [ ] Desconexão WebSocket exibe banner "Conexão perdida — reconectando..."
  - [ ] Reconexão automática em até 30 segundos
  - [ ] "Estimativa de transbordo" exibe "—" quando taxa ≤ 0

### TASK-93 — Tabela de Histórico de Alertas com Exportação CSV

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-65
- **Entregáveis:**
  - Tabela paginada com colunas: Data/Hora, Reservatório, Nível, Mensagem, Status (Ativo/Reconhecido)
  - Filtros: reservatório, nível, período
  - Botão "Exportar CSV" gerando arquivo com todos os alertas do filtro atual
- **Critérios de Aceite:**
  - [ ] Paginação com 20 itens por página
  - [ ] CSV exportado abre corretamente no Excel com encoding UTF-8 BOM
  - [ ] Filtro por `nivel=CRITICO` exibe apenas alertas críticos

---

## EPIC-10 — Dashboard Público

> Interface cidadã com semáforo de risco, tendência e inscrição para alertas. WCAG AA.

### TASK-100 — Componente: Semáforo de Status (WCAG AA)

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-82, TASK-71
- **Entregáveis:**
  - `src/components/AlertBadge.tsx`: componente semáforo com 4 estados
  - Cores: verde (#22C55E), amarelo (#EAB308), laranja (#F97316), vermelho (#EF4444)
  - Texto em PT-BR acessível: "Normal", "Atenção", "Alerta", "Situação Crítica"
  - Ícone + cor + texto (não depende apenas de cor para acessibilidade — WCAG 1.4.1)
- **Critérios de Aceite:**
  - [ ] Contraste WCAG AA verificado com ferramenta (mínimo 4.5:1 para texto normal)
  - [ ] Componente usa `role="status"` e `aria-label` descritivo
  - [ ] Estado CRITICO exibe ícone pulsante para chamar atenção
  - [ ] Funciona corretamente em tema escuro e claro

### TASK-101 — Componente: Indicador de Tendência

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-73
- **Entregáveis:**
  - Indicador visual de tendência: ↑ subindo / → estável / ↓ caindo
  - Baseado na `taxa_variacao` recebida do WebSocket público
  - Texto: "Nível subindo" / "Nível estável" / "Nível caindo"
- **Critérios de Aceite:**
  - [ ] Ícone + texto (não apenas ícone) para acessibilidade
  - [ ] Transição suave ao mudar de estado

### TASK-102 — Formulário de Inscrição para Alertas

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-63, TASK-64, TASK-84
- **Entregáveis:**
  - `src/components/AlertSubscribeForm.tsx` com duas opções:
    - "Receber Push no navegador" (botão que chama `usePushSubscription.subscribe()`)
    - "Receber por Email" (campo email + botão que chama `POST /subscribe/email`)
  - Feedback: "Inscrição realizada! Verifique seu email para confirmar." (email) / "Notificações ativas!" (push)
- **Critérios de Aceite:**
  - [ ] Botão Push desabilitado em browsers sem suporte a `PushManager`
  - [ ] Formulário de email valida formato antes de enviar
  - [ ] Mensagens de sucesso/erro claras e acessíveis (não apenas cor)

### TASK-103 — Banner Offline e Última Atualização

- **Tipo:** frontend
- **Prioridade:** P1
- **Dependências:** TASK-83
- **Entregáveis:**
  - Banner amarelo exibido quando browser está offline (`navigator.onLine` + evento `offline`)
  - Timestamp "Última atualização: HH:MM:SS" atualizado a cada mensagem WebSocket
  - Dados em cache exibidos normalmente com aviso "Dados podem estar desatualizados"
- **Critérios de Aceite:**
  - [ ] Banner aparece imediatamente ao perder conexão
  - [ ] Banner desaparece ao reconectar
  - [ ] Timestamp mostra a diferença relativa: "há 2 minutos" quando dado é antigo

---

## EPIC-11 — Integração Climática

> Client HTTP para CPTEC/INPE com fallback OpenWeatherMap e scheduler de atualização.

### TASK-110 — HTTP Client CPTEC/INPE

- **Tipo:** backend
- **Prioridade:** P2
- **Dependências:** TASK-51
- **Entregáveis:**
  - `app/modules/clima/client.py`: `CPTECClient.get_previsao(lat, lon)` usando `httpx` async
  - `app/modules/clima/client.py`: `OpenWeatherClient.get_previsao(lat, lon)` como fallback
  - Lógica de fallback: tenta CPTEC, se timeout/erro, usa OpenWeatherMap
  - Timeout de 5s para cada request; retry 2x com backoff
- **Critérios de Aceite:**
  - [ ] `CPTECClient.get_previsao(-23.5, -46.6)` retorna dados de previsão ou lança `ClimaServiceException`
  - [ ] Fallback automático para OpenWeatherMap quando CPTEC retorna 5xx
  - [ ] Chave API OpenWeatherMap carregada de `OPENWEATHER_API_KEY` env var (nunca hardcoded)

### TASK-111 — Service e Scheduler Climático

- **Tipo:** backend
- **Prioridade:** P2
- **Dependências:** TASK-110, TASK-22
- **Entregáveis:**
  - `app/modules/clima/service.py`: `ClimaService.atualizar_todos_reservatorios()` persiste dados em `leitura_climatica`
  - Scheduler via APScheduler (ou cron job ARQ) rodando a cada 30 minutos
  - `GET /api/v1/reservatorios/{id}/clima` expõe dados climáticos mais recentes
- **Critérios de Aceite:**
  - [ ] Dados climáticos persistidos em `leitura_climatica` a cada 30 minutos
  - [ ] `GET /reservatorios/1/clima` retorna: temperatura, umidade, precipitacao_mm, condicao
  - [ ] Falha na API climática não interrompe o processamento de leituras de sensores (isolation)

---

## EPIC-12 — Testes e Qualidade

> Suite de testes unitários e de integração cobrindo os módulos críticos do MVP.

### TASK-120 — Testes de Integração: Ingestão

- **Tipo:** qa
- **Prioridade:** P2
- **Dependências:** TASK-42
- **Entregáveis:**
  - `backend/tests/integration/test_ingestao.py` usando `httpx.AsyncClient` com banco de teste
  - Cenários: ingestão bem-sucedida (batch), API Key inválida, sensor inexistente, batch > 100 itens
- **Critérios de Aceite:**
  - [ ] `pytest tests/integration/test_ingestao.py -v` passa sem erros
  - [ ] Banco de teste isolado (usando fixture com rollback por teste)
  - [ ] ≥ 5 cenários de teste cobertos

### TASK-121 — Testes de Integração: Alertas

- **Tipo:** qa
- **Prioridade:** P2
- **Dependências:** TASK-65
- **Entregáveis:**
  - `backend/tests/integration/test_alertas.py`
  - Cenários: listagem de alertas, reconhecimento por gestor, rejeição por operador, criação de alerta via processamento
- **Critérios de Aceite:**
  - [ ] `pytest tests/integration/test_alertas.py -v` passa sem erros
  - [ ] Teste de RBAC verifica que `operador` recebe 403 em endpoint restrito

### TASK-122 — Teste PWA: Offline e Push

- **Tipo:** qa
- **Prioridade:** P2
- **Dependências:** TASK-83, TASK-84
- **Entregáveis:**
  - Checklist de testes manuais documentado em `Docs/QA_CHECKLIST.md`
  - Cobertura: offline mode, add to home screen, push notification recebida com aba fechada
- **Critérios de Aceite:**
  - [ ] Checklist executado e aprovado em Chrome Android (real ou emulado)
  - [ ] Todos os itens do checklist marcados como PASS

---

## EPIC-13 — Documentação Final e Entrega

> Finalização de toda documentação técnica e acadêmica para entrega do TCC.

### TASK-130 — README de Deploy e Operação

- **Tipo:** docs
- **Prioridade:** P3
- **Dependências:** EPIC-01 concluído
- **Entregáveis:**
  - `README.md` atualizado com:
    - Pré-requisitos (Docker ≥ 24, Docker Compose V2)
    - Setup em 5 passos (clone, .env, docker compose up, seed, acesso)
    - URLs dos serviços (app, API docs, health check)
    - Variáveis de ambiente documentadas (nome, descrição, exemplo)
    - Comandos de manutenção (logs, backup, restore)
- **Critérios de Aceite:**
  - [ ] Desenvolvedor novo consegue subir o sistema seguindo apenas o README
  - [ ] Todos os comandos testados em ambiente limpo (Ubuntu 24.04)

### TASK-131 — Revisão Final dos Documentos

- **Tipo:** docs
- **Prioridade:** P3
- **Dependências:** todos os EPICs P0 e P1 concluídos
- **Entregáveis:**
  - Revisão de coerência entre 001 (Plano), 002 (SRS), 003 (PRD), 004 (DevSpecs), 005 (Backlog)
  - Atualização do cronograma real vs planejado
  - Glossário consistente entre todos os documentos
- **Critérios de Aceite:**
  - [ ] Nenhuma contradição de nomenclatura entre os documentos
  - [ ] Cronograma atualizado com datas reais de conclusão por EPIC
  - [ ] Todos os RFs do SRS mapeados para pelo menos uma TASK no Backlog

### TASK-132 — Apresentação Acadêmica

- **Tipo:** docs
- **Prioridade:** P3
- **Dependências:** TASK-131
- **Entregáveis:**
  - Slides da apresentação final (formato PPTX ou PDF) com:
    - Contexto e problema (enchentes RMSP, piscinões)
    - Solução proposta e arquitetura
    - Demonstração ao vivo (ou vídeo)
    - Resultados e métricas alcançadas
    - Dificuldades e aprendizados
- **Critérios de Aceite:**
  - [ ] Apresentação de 15-20 minutos
  - [ ] Demo ao vivo funcional (ou vídeo de fallback gravado)
  - [ ] Diagrama de arquitetura incluído nos slides

---

## Resumo de Tarefas por Tipo

| Tipo | Quantidade | Tarefas |
|------|-----------|---------|
| infra | 7 | TASK-00, 01, 02, 03, 10, 11, 12, 13 |
| data | 5 | TASK-20, 21, 22, 23, 24 |
| backend | 20 | TASK-30 a 35, 40 a 42, 50 a 52, 60 a 65, 70 a 73, 110, 111 |
| frontend | 13 | TASK-80 a 84, 90 a 93, 100 a 103 |
| qa | 5 | TASK-52, 120, 121, 122 |
| docs | 3 | TASK-130, 131, 132 |

---

*Documento gerado como parte do Projeto Integrador PJI510 — UNIVESP 2026/S1*

