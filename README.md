# PiscinãoMonitor — Sistema de Monitoramento de Piscinões com IoT

> **PJI510 — Projeto Integrador em Engenharia da Computação | UNIVESP 2026/S1 — Turma 001**

Sistema de monitoramento em tempo real de **reservatórios de detenção (piscinões/pôlders)** da Região Metropolitana de São Paulo, com ingestão de sensores IoT, motor de regras hidrológico, alertas multicanal e dashboards web com suporte offline (PWA).

---

## Sumário

1. [Pré-requisitos](#1-pré-requisitos)
2. [Setup em 5 Passos](#2-setup-em-5-passos)
3. [URLs dos Serviços](#3-urls-dos-serviços)
4. [Variáveis de Ambiente](#4-variáveis-de-ambiente)
5. [Comandos de Manutenção](#5-comandos-de-manutenção)
6. [Arquitetura e Stack](#6-arquitetura-e-stack)
7. [Documentação Técnica](#7-documentação-técnica)

---

## 1. Pré-requisitos

| Ferramenta | Versão mínima | Verificação |
|-----------|--------------|-------------|
| Docker | 24.x | `docker --version` |
| Docker Compose | V2 (plugin integrado) | `docker compose version` |
| Git | 2.40+ | `git --version` |
| Python | 3.12 *(somente para scripts utilitários)* | `python3 --version` |

> **Recursos de hardware recomendados:** 4 GB RAM livre, 10 GB de disco.

---

## 2. Setup em 5 Passos

### Passo 1 — Clonar o repositório

```bash
git clone https://github.com/<org>/PJI510-2026S1-Turma001.git
cd PJI510-2026S1-Turma001
```

### Passo 2 — Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` preenchendo **obrigatoriamente** os campos marcados com `TROQUE_POR_*`:

```
POSTGRES_PASSWORD=<senha-forte>
REDIS_PASSWORD=<senha-forte>
SECRET_KEY=<string-aleatória-128-chars>   # python -c "import secrets; print(secrets.token_hex(64))"
INGESTAO_API_KEY=<api-key-sensores>       # python -c "import secrets; print(secrets.token_hex(32))"
```

### Passo 3 — Gerar chaves VAPID (Push Notifications)

```bash
python scripts/generate_vapid_keys.py
```

Copie as chaves `VAPID_PUBLIC_KEY` e `VAPID_PRIVATE_KEY` geradas para o `.env`.

> Pule este passo se não for testar Push Notifications.

### Passo 4 — Subir todos os serviços

```bash
docker compose up -d
```

Aguarde todos os containers ficarem `healthy` (≈ 60 s):

```bash
docker compose ps
```

Saída esperada:

```
NAME          STATUS
postgres      Up (healthy)
redis         Up (healthy)
backend       Up (healthy)
worker        Up
frontend      Up
nginx         Up
```

### Passo 5 — Aplicar migrations e dados de desenvolvimento

```bash
# Executar todas as migrations Alembic
docker compose exec backend alembic upgrade head

# Popular banco com dados de desenvolvimento (reservatórios e sensores de exemplo)
docker compose exec postgres psql -U piscinao -d piscinao_db \
  -f /docker-entrypoint-initdb.d/seed_dev.sql
```

O sistema está pronto. Acesse `http://localhost`.

---

## 3. URLs dos Serviços

| Serviço | URL | Autenticação |
|---------|-----|-------------|
| Dashboard Público | http://localhost | Nenhuma |
| Dashboard Técnico | http://localhost/dashboard | JWT (gestor/admin) |
| Admin | http://localhost/admin | JWT (admin) |
| API REST (Swagger UI) | http://localhost/api/v1/docs | Nenhuma para leitura |
| API REST (ReDoc) | http://localhost/api/v1/redoc | Nenhuma |
| Health Check | http://localhost/api/v1/health | Nenhuma |
| WebSocket Público | ws://localhost/ws/publico/{id} | Nenhuma |
| WebSocket Autenticado | ws://localhost/ws/autenticado/{id} | JWT (query param `token`) |

---

## 4. Variáveis de Ambiente

Todas as variáveis são definidas no arquivo `.env` (baseado em `.env.example`).

### Banco de Dados

| Variável | Descrição | Exemplo |
|---------|-----------|---------|
| `POSTGRES_USER` | Usuário do PostgreSQL | `piscinao` |
| `POSTGRES_PASSWORD` | Senha do PostgreSQL | `Senha@2026!` |
| `POSTGRES_DB` | Nome do banco de dados | `piscinao_db` |
| `DATABASE_URL` | URL completa SQLAlchemy Async | `postgresql+asyncpg://piscinao:...@postgres:5432/piscinao_db` |

### Redis

| Variável | Descrição | Exemplo |
|---------|-----------|---------|
| `REDIS_PASSWORD` | Senha do Redis | `Redis@2026!` |
| `REDIS_URL` | URL completa de conexão | `redis://:Redis@2026!@redis:6379/0` |

### Segurança JWT

| Variável | Descrição | Padrão |
|---------|-----------|--------|
| `SECRET_KEY` | Chave secreta para assinar tokens JWT | *(obrigatório)* |
| `ALGORITHM` | Algoritmo JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração do access token | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Expiração do refresh token | `7` |

### Ingestão IoT

| Variável | Descrição | Exemplo |
|---------|-----------|---------|
| `INGESTAO_API_KEY` | API Key para autenticar sensores no endpoint `POST /api/v1/ingestao/leituras` | `abc123...` |

### Web Push (VAPID)

| Variável | Descrição | Como obter |
|---------|-----------|------------|
| `VAPID_PUBLIC_KEY` | Chave pública VAPID (base64url) | `python scripts/generate_vapid_keys.py` |
| `VAPID_PRIVATE_KEY` | Chave privada VAPID | Idem |
| `VAPID_SUBJECT` | Contato do servidor (mailto ou URL) | `mailto:admin@piscinao.local` |

### Email (SMTP)

| Variável | Descrição | Exemplo |
|---------|-----------|---------|
| `SMTP_HOST` | Servidor SMTP | `smtp.gmail.com` |
| `SMTP_PORT` | Porta SMTP | `587` |
| `SMTP_USER` | Usuário SMTP | `alertas@exemplo.com` |
| `SMTP_PASSWORD` | Senha SMTP | *(obrigatório para email)* |
| `SMTP_FROM` | Endereço de exibição | `PiscinãoMonitor <alertas@exemplo.com>` |
| `SMTP_TLS` | Usar TLS (STARTTLS) | `true` |

### Integração Climática

| Variável | Descrição | Como obter |
|---------|-----------|------------|
| `OPENWEATHER_API_KEY` | API Key do OpenWeatherMap (fallback climático) | [openweathermap.org](https://openweathermap.org/api) — gratuito |

> A integração primária usa CPTEC/INPE (sem chave). OpenWeatherMap é acionado automaticamente se o CPTEC falhar.

---

## 5. Comandos de Manutenção

### Logs

```bash
# Logs em tempo real de todos os serviços
docker compose logs -f

# Logs de um serviço específico
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f nginx
```

### Testes

```bash
# Executar todos os testes do backend
docker compose exec backend pytest -v

# Executar apenas testes de integração
docker compose exec backend pytest tests/integration/ -v

# Executar com relatório de cobertura
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

### Banco de Dados

```bash
# Acesso direto ao PostgreSQL
docker compose exec postgres psql -U piscinao -d piscinao_db

# Criar nova migration Alembic
docker compose exec backend alembic revision --autogenerate -m "descricao_da_mudanca"

# Aplicar migrations pendentes
docker compose exec backend alembic upgrade head

# Ver histórico de migrations
docker compose exec backend alembic history

# Reverter última migration
docker compose exec backend alembic downgrade -1
```

### Backup e Restore

```bash
# Backup completo do banco de dados
docker compose exec postgres pg_dump -U piscinao piscinao_db \
  | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Restaurar backup
gunzip -c backup_YYYYMMDD_HHMMSS.sql.gz \
  | docker compose exec -T postgres psql -U piscinao piscinao_db
```

### Operações de Serviço

```bash
# Reiniciar um serviço sem parar os demais
docker compose restart backend

# Parar todos os serviços (preserva volumes/dados)
docker compose stop

# Remover tudo incluindo volumes (DESTRÓI OS DADOS)
docker compose down -v

# Rebuild após mudança no código
docker compose build backend
docker compose up -d backend
```

### Usuário Admin Inicial

O seed de desenvolvimento cria um usuário admin padrão. Para criar manualmente via API:

```bash
# Obter token admin (usuário criado pelo seed)
curl -s -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@piscinao.local","password":"Admin@2026!"}' \
  | python -m json.tool

# Criar novo usuário gestor (requer token admin)
curl -s -X POST http://localhost/api/v1/auth/register \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Gestor DAEE","email":"gestor@piscinao.local","password":"Gestor@2026!","role":"gestor"}'
```

### Simulação de Leitura de Sensor (desenvolvimento)

```bash
# Enviar leitura de sensor via API (substitua INGESTAO_API_KEY e sensor_id)
curl -s -X POST http://localhost/api/v1/ingestao/leituras \
  -H "X-API-Key: <INGESTAO_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "leituras": [
      {"sensor_id": 1, "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'", "valor": 350.0, "unidade": "cm"}
    ]
  }'
```

---

## 6. Arquitetura e Stack

```
┌─────────────────────────────────────────────────────────────┐
│                         NGINX 1.27                           │
│  /              → frontend (React SPA)                       │
│  /api/v1/       → backend:8000 (FastAPI)                     │
│  /ws/           → backend:8000 (WebSocket)                   │
└────────────┬──────────────────────────┬─────────────────────┘
             │                          │
    ┌────────▼────────┐      ┌──────────▼──────────┐
    │  Backend/FastAPI│      │   ARQ Worker (async) │
    │  Python 3.12    │      │   Tasks + Cron Jobs  │
    └────────┬────────┘      └──────────┬──────────┘
             │                          │
    ┌────────▼──────────────────────────▼──────┐
    │  PostgreSQL 16 + TimescaleDB 2.x          │
    │  Hypertables: leitura_sensor,             │
    │               leitura_climatica           │
    └───────────────────────────────────────────┘
             │
    ┌────────▼────────┐
    │   Redis 7        │
    │   Cache + Queue  │
    └─────────────────┘
```

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| Backend API | Python + FastAPI + Pydantic v2 | 3.12 + 0.115 |
| ORM / Migrations | SQLAlchemy Async + Alembic | 2.0 + 1.15 |
| Banco de dados | PostgreSQL + TimescaleDB | 16 + 2.x |
| Cache / Filas | Redis + ARQ | 7 + 0.26 |
| Auth | JWT (python-jose) + bcrypt | — |
| Frontend | React + TypeScript + Vite | 18 + 5.x + 6.x |
| UI | Tailwind CSS v4 + shadcn/ui | 4.x |
| Gráficos / Mapas | Recharts + Leaflet | 2.x + 1.9 |
| PWA | vite-plugin-pwa + Workbox | — |
| Reverse Proxy | NGINX | 1.27 |
| Containerização | Docker + Docker Compose | 27.x + V2 |

---

## 7. Documentação Técnica

| Documento | Conteúdo |
|-----------|----------|
| [001 - Plano de Desenvolvimento](Docs/001%20-%20Plano%20de%20desenvolvimento.md) | Objetivos, escopo, cronograma (planejado vs real), riscos |
| [002 - SRS](Docs/002%20-%20Software%20Requirements%20Specification%20-%20SRS%20-%20MODELO.md) | RF01–RF31, requisitos não-funcionais, User Stories, modelo ER |
| [003 - PRD](Docs/003%20-%20Pesquisa%20e%20Desenvolvimento%20-%20PRD%20-%20MODELO.md) | Estado da arte, decisões arquiteturais (ADR-001–006) |
| [004 - DevSpecs](Docs/004%20-%20DevSpecs.md) | Diagrama C4, ADRs, ER detalhado, endpoints, Docker |
| [005 - Backlog Técnico](Docs/005%20-%20Backlog%20Tecnico%20-%20MODELO.md) | 14 épicos, 53 tarefas, critérios de aceite |
| [QA Checklist](Docs/QA_CHECKLIST.md) | 35 casos de teste manuais: PWA, offline, push, responsividade |
| [Slides](Docs/Slides-Apresentacao.md) | Apresentação acadêmica final |

---

*Projeto Integrador PJI510 — UNIVESP 2026/S1 — Turma 001*
