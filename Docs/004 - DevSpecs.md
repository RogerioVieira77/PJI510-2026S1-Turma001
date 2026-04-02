# DevSpecs — Especificação Técnica e Arquitetura

## Sistema de Monitoramento de Piscinões (Pôlders) com IoT

**Projeto:** PJI510 — Projeto Integrador em Engenharia da Computação  
**Base documental:** 001 - Plano de Desenvolvimento  
**Versão:** 1.0  
**Data:** 02/04/2026  
**Status:** Em Desenvolvimento  

---

## Sumário

1. [Objetivo deste Documento](#1-objetivo-deste-documento)
2. [Visão Geral da Arquitetura](#2-visão-geral-da-arquitetura)
3. [Diagramas C4](#3-diagramas-c4)
4. [Diagrama de Fluxo de Dados](#4-diagrama-de-fluxo-de-dados)
5. [Stack Tecnológico com Justificativas](#5-stack-tecnológico-com-justificativas)
6. [Architecture Decision Records (ADRs)](#6-architecture-decision-records-adrs)
7. [Modelagem de Dados](#7-modelagem-de-dados)
8. [Regras de Negócio](#8-regras-de-negócio)
9. [Endpoints da API](#9-endpoints-da-api)
10. [Infraestrutura Docker](#10-infraestrutura-docker)
11. [Configuração NGINX](#11-configuração-nginx)
12. [Estrutura de Diretórios](#12-estrutura-de-diretórios)
13. [Glossário Ubíquo](#13-glossário-ubíquo)
14. [Referências](#14-referências)

---

## 1. Objetivo deste Documento

Este documento traduz as decisões estratégicas do Plano de Desenvolvimento em especificações técnicas detalhadas. Define a arquitetura do sistema, o stack tecnológico com justificativas formais (ADRs), a modelagem de dados, as regras de negócio com fórmulas matemáticas, os endpoints da API, e a infraestrutura de deploy.

**Público-alvo:** equipe de desenvolvimento, orientador acadêmico, banca avaliadora.

---

## 2. Visão Geral da Arquitetura

### 2.1 Decisão Arquitetural: Monolito Modular

O sistema adota uma arquitetura de **monolito modular** — uma aplicação backend unificada com separação interna por domínios de negócio (módulos).

**Justificativa:**

- Equipe acadêmica reduzida — microserviços exigem overhead operacional desproporcional
- Deploy e debugging significativamente mais simples com um único processo backend
- Módulos podem ser extraídos em serviços independentes futuramente se necessário
- Transações cross-domain são frequentes (ex: ingestão de leitura → cálculo → alerta)
- Docker Compose já fornece isolamento suficiente entre serviços (banco, cache, worker)

### 2.2 Padrão por Módulo

Cada módulo do backend segue a mesma composição baseada em Clean Architecture simplificada:

```
backend/modules/<modulo>/
├── models.py       # Mapeamento ORM (SQLAlchemy)
├── schemas.py      # Contratos de entrada/saída (Pydantic)
├── repository.py   # Persistência e queries
├── service.py      # Regras de negócio e orquestração
├── router.py       # Endpoints HTTP (FastAPI Router)
└── policies.py     # Autorização contextual (RBAC)
```

**Responsabilidade de cada camada:**

| Camada | Responsabilidade | Não deve conter |
|--------|-----------------|-----------------|
| `router.py` | HTTP, validação de entrada, paginação, autenticação | Regras de negócio |
| `schemas.py` | Contratos Pydantic (request/response) | Lógica de persistência |
| `service.py` | Regras de negócio, transações, orquestração | Queries SQL diretas |
| `repository.py` | Persistência, queries reutilizáveis | Regras de negócio |
| `models.py` | Mapeamento ORM para tabelas | Validação de entrada |
| `policies.py` | Autorização contextual por papel e tenant | Lógica de dados |

---

## 3. Diagramas C4

### 3.1 Nível 1 — Diagrama de Contexto

Visão de alto nível do sistema e suas interações com atores e sistemas externos.

```mermaid
graph TB
    subgraph Atores
        CID["👤 Cidadão<br><i>Morador do entorno do piscinão</i>"]
        GES["👤 Gestor / Defesa Civil<br><i>Monitora reservatórios e gerencia alertas</i>"]
        ADM["👤 Administrador<br><i>Configura sistema, sensores e thresholds</i>"]
    end

    subgraph "Sistemas Externos"
        SENS["📡 Sensores IoT<br><i>Gateway LoRa/WiFi → Broker MQTT</i>"]
        CLIMA["🌤️ API Climática<br><i>CPTEC/INPE + OpenWeatherMap</i>"]
        EMAIL["📧 Servidor SMTP<br><i>Envio de alertas por email</i>"]
        PUSH["🔔 Web Push Service<br><i>FCM / VAPID</i>"]
    end

    SIS["🏗️ Sistema de Monitoramento<br>de Piscinões<br><i>Plataforma Web IoT</i>"]

    SENS -->|"Leituras de sensores<br>(nível, pluviometria)"| SIS
    CLIMA -->|"Previsão meteorológica<br>(temperatura, chuva)"| SIS
    SIS -->|"Alertas por email"| EMAIL
    SIS -->|"Push notifications"| PUSH

    CID -->|"Consulta status<br>Inscreve-se em alertas"| SIS
    GES -->|"Monitora dashboards<br>Configura alertas"| SIS
    ADM -->|"Gerencia sensores<br>Configura sistema"| SIS
```

### 3.2 Nível 2 — Diagrama de Containers

Decomposição do sistema em containers (processos/serviços deployáveis).

```mermaid
graph TB
    subgraph "Dispositivos IoT"
        S1["📡 Sensor Nível 1<br><i>Ultrassônico</i>"]
        S2["📡 Sensor Nível 2<br><i>Ultrassônico</i>"]
        PL["🌧️ Pluviômetro<br><i>Estação meteorológica</i>"]
        GW["📟 Gateway<br><i>LoRa/WiFi → MQTT</i>"]
    end

    subgraph "Servidor Ubuntu 24.04 LTS (Docker)"

        NGINX["🔀 NGINX<br><i>Reverse Proxy<br>SSL Termination<br>Static Files</i><br>Port: 80/443"]

        FRONT["⚛️ Frontend React<br><i>SPA (TypeScript + Vite)<br>Dashboard Técnico<br>Dashboard Público<br>PWA</i><br>Servido como static files pelo NGINX"]

        BACK["🐍 Backend FastAPI<br><i>API REST + WebSocket<br>Python 3.12 + Pydantic v2<br>Módulos: Ingestão, Processamento,<br>Alertas, Dashboard, Clima, Auth</i><br>Port: 8000"]

        DB[("🐘 PostgreSQL 16<br>+ TimescaleDB 2.x<br><i>Dados relacionais +<br>Séries temporais (hypertables)<br>Continuous Aggregates</i><br>Port: 5432")]

        REDIS[("⚡ Redis 7<br><i>Cache de estado<br>Pub/Sub real-time<br>Broker ARQ</i><br>Port: 6379")]

        WORKER["⚙️ ARQ Worker<br><i>Background Tasks<br>Dispatch de alertas<br>(email, push)</i>"]
    end

    subgraph "APIs Externas"
        CPTEC["🌤️ CPTEC/INPE API"]
        OWM["🌦️ OpenWeatherMap API"]
        SMTP["📧 SMTP Server"]
        VAPID["🔔 Web Push (VAPID)"]
    end

    S1 & S2 & PL --> GW
    GW -->|"MQTT → Abstração"| BACK

    NGINX -->|"Serve static files"| FRONT
    NGINX -->|"Proxy /api/*"| BACK
    NGINX -->|"WebSocket /ws/*"| BACK

    BACK -->|"SQL Async (asyncpg)"| DB
    BACK -->|"Cache + Pub/Sub"| REDIS
    BACK -->|"Enfileira tasks"| REDIS

    WORKER -->|"Consome tasks"| REDIS
    WORKER -->|"Envia emails"| SMTP
    WORKER -->|"Push notifications"| VAPID

    BACK -->|"Consulta previsão"| CPTEC
    BACK -->|"Fallback clima"| OWM
```

### 3.3 Nível 3 — Diagrama de Componentes do Backend

Decomposição interna do container Backend FastAPI em módulos.

```mermaid
graph TB
    subgraph "Backend FastAPI"
        direction TB

        subgraph "Core"
            AUTH["🔐 Auth<br><i>JWT + Refresh Token<br>RBAC + API Key</i>"]
            MW["🛡️ Middleware<br><i>CORS, Rate Limit,<br>Logging, Error Handler</i>"]
            DB_CORE["🔌 Database<br><i>Session Factory<br>Connection Pool (asyncpg)</i>"]
        end

        subgraph "Módulo Ingestão"
            ING_R["📥 Router<br>POST /api/v1/ingestao/leituras"]
            ING_S["⚙️ Service<br>Validação + Persistência"]
            ING_REPO["💾 Repository<br>Hypertable insert"]
        end

        subgraph "Módulo Processamento"
            PROC_S["🔬 Service<br>Cálculos hidrológicos"]
            PROC_RULES["📏 Rules Engine<br>Volume, Taxa variação,<br>Estimativa transbordo"]
        end

        subgraph "Módulo Alertas"
            ALT_R["📡 Router<br>GET/POST /api/v1/alertas"]
            ALT_S["⚙️ Service<br>Avaliação de thresholds"]
            ALT_DISP["📤 Dispatcher<br>Multicanal (Push, Email)"]
            ALT_REPO["💾 Repository<br>Histórico de alertas"]
        end

        subgraph "Módulo Dashboard"
            DASH_R["📊 Router<br>GET /api/v1/dashboard/*<br>WS /ws/dashboard/*"]
            DASH_S["⚙️ Service<br>Agregações + Status"]
            DASH_WS["🔄 WebSocket Manager<br>Broadcast real-time"]
        end

        subgraph "Módulo Clima"
            CLIMA_S["🌤️ Service<br>Consulta APIs externas"]
            CLIMA_ADAPT["🔌 Adapters<br>CPTEC + OpenWeatherMap"]
            CLIMA_REPO["💾 Repository<br>Cache de previsões"]
        end
    end

    ING_R --> ING_S --> ING_REPO
    ING_S --> PROC_S
    PROC_S --> PROC_RULES
    PROC_RULES -->|"Se threshold atingido"| ALT_S
    ALT_S --> ALT_DISP
    ALT_S --> ALT_REPO
    DASH_S --> DASH_WS
    CLIMA_S --> CLIMA_ADAPT
    CLIMA_S --> CLIMA_REPO

    ING_REPO --> DB_CORE
    ALT_REPO --> DB_CORE
    CLIMA_REPO --> DB_CORE
    DASH_S --> DB_CORE
```

---

## 4. Diagrama de Fluxo de Dados

### 4.1 Fluxo Principal: Ingestão → Processamento → Alerta → Dashboard

```mermaid
flowchart TD
    subgraph "Camada IoT (Campo)"
        SN1["📡 Sensor Nível 1"]
        SN2["📡 Sensor Nível 2"]
        PLV["🌧️ Pluviômetro"]
        GW["📟 Gateway LoRa/WiFi"]
    end

    subgraph "Camada de Mensageria (Abstraída)"
        MQTT["📨 Broker MQTT<br><i>Abstração: o backend consome<br>via endpoint REST</i>"]
    end

    subgraph "Camada de Aplicação (Docker)"
        ING["📥 Endpoint de Ingestão<br>POST /api/v1/ingestao/leituras<br><i>Autenticação: API Key</i>"]
        VAL{{"✅ Validação Pydantic<br>Payload válido?"}}
        PERSIST["💾 Persistência<br>TimescaleDB Hypertable<br><i>leitura_sensor</i>"]

        PROC["🔬 Motor de Processamento"]
        CALC_VOL["📐 Cálculo de Volume<br>V = f(h, geometria)"]
        CALC_TAXA["📈 Taxa de Variação<br>Δh/Δt"]
        CALC_TRANS["⏱️ Estimativa Transbordo<br>T = (H_max - h) / (Δh/Δt)"]
        REDUND["🔄 Redundância Sensores<br>Média + Divergência > 10%?"]

        RULES{{"⚖️ Motor de Regras<br>Threshold atingido?"}}
        ALERT_Y["🟡 Alerta Amarelo<br>Nível > 60%"]
        ALERT_O["🟠 Alerta Laranja<br>Nível > 80% OU T < 2h"]
        ALERT_R["🔴 Alerta Vermelho<br>Nível > 90% OU T < 30min"]
        NO_ALERT["🟢 Normal<br>Sem alerta"]

        DISPATCH["📤 Dispatcher de Alertas"]
        WS_PUSH["🔄 WebSocket Broadcast<br>Dashboard real-time"]
    end

    subgraph "Camada de Notificação"
        WEB_PUSH["🔔 Web Push (VAPID)"]
        EMAIL_NOT["📧 Email (SMTP)"]
        SMS_FUT["📱 SMS (futuro)"]
        WA_FUT["💬 WhatsApp (futuro)"]
    end

    subgraph "Camada de Apresentação"
        DASH_TEC["📊 Dashboard Técnico<br><i>Gráficos, mapa, histórico</i>"]
        DASH_PUB["🚦 Dashboard Público<br><i>Semáforo, tendência</i>"]
    end

    SN1 & SN2 & PLV --> GW --> MQTT --> ING
    ING --> VAL
    VAL -->|"❌ Inválido"| REJECT["⛔ Rejeitar<br>HTTP 422"]
    VAL -->|"✅ Válido"| PERSIST
    PERSIST --> PROC
    PROC --> REDUND
    REDUND --> CALC_VOL & CALC_TAXA
    CALC_TAXA --> CALC_TRANS
    CALC_VOL & CALC_TRANS --> RULES
    RULES -->|"Normal"| NO_ALERT
    RULES -->|"Amarelo"| ALERT_Y
    RULES -->|"Laranja"| ALERT_O
    RULES -->|"Vermelho"| ALERT_R
    ALERT_Y & ALERT_O & ALERT_R --> DISPATCH
    DISPATCH --> WEB_PUSH & EMAIL_NOT
    DISPATCH -.->|"Adapter pattern<br>(futuro)"| SMS_FUT & WA_FUT
    NO_ALERT --> WS_PUSH
    DISPATCH --> WS_PUSH
    WS_PUSH --> DASH_TEC & DASH_PUB
```

### 4.2 Fluxo Secundário: Integração com API Climática

```mermaid
flowchart LR
    CRON["⏰ Scheduler<br>A cada 30 min"]
    CPTEC["🌤️ CPTEC/INPE API"]
    OWM["🌦️ OpenWeatherMap API"]
    ADAPTER["🔌 Adapter Pattern"]
    PERSIST["💾 leitura_climatica<br>TimescaleDB"]
    CORR["🔬 Correlação<br>Pluviometria × Nível"]

    CRON --> ADAPTER
    ADAPTER -->|"Primária"| CPTEC
    ADAPTER -->|"Fallback"| OWM
    CPTEC & OWM --> PERSIST
    PERSIST --> CORR
    CORR -->|"Se chuva prevista > threshold<br>E nível subindo"| ALERT["⚠️ Antecipar Alerta"]
```

---

## 5. Stack Tecnológico com Justificativas

### 5.1 Tabela Completa

| Camada | Tecnologia | Versão | Justificativa Resumida | Ref. ADR |
|--------|-----------|--------|----------------------|---------|
| **Sistema Operacional** | Ubuntu LTS | 24.04 | Requisito do projeto; LTS garante suporte até 2034 | — |
| **Containerização** | Docker + Compose | 27.x + 2.x | Isolamento de processos, reprodutibilidade de ambiente, deploy simplificado | — |
| **Web Server** | NGINX | 1.27 | Reverse proxy, SSL termination, static file serving, WebSocket upgrade, rate limiting | ADR-004 |
| **Backend** | Python + FastAPI | 3.12 + 0.115 | Async nativo, Pydantic v2 para validação de payloads IoT, ecossistema científico (numpy, pandas), geração automática de OpenAPI | ADR-001 |
| **ORM** | SQLAlchemy 2.0 Async | 2.0 | Padrão da indústria; suporte a SQL raw para queries TimescaleDB; tipagem robusta; Alembic para migrations | ADR-002 |
| **Driver PostgreSQL** | asyncpg | 0.30 | Driver async nativo de alta performance para PostgreSQL | ADR-002 |
| **Migrations** | Alembic | 1.x | Versionamento de schema, rollback seguro, integrado com SQLAlchemy | ADR-002 |
| **Validação** | Pydantic | 2.x | Validação de schemas IoT; serialização/desserialização performática; integrado com FastAPI | ADR-001 |
| **Banco de Dados** | PostgreSQL + TimescaleDB | 16 + 2.x | Relacional + séries temporais unificados; SQL padrão; hypertables com compressão; continuous aggregates; ACID para alertas | ADR-002 |
| **Cache / Broker** | Redis | 7.x | Cache de último estado dos sensores; pub/sub para WebSocket; broker para ARQ worker | ADR-003 |
| **Tasks Assíncronas** | ARQ | 0.26 | Async-native (alinhado com FastAPI); Redis como broker; código limpo para documentação | ADR-003 |
| **Frontend** | React + TypeScript + Vite | 18 + 5.x + 6.x | SPA servido como estático pelo NGINX; sem runtime Node no servidor; Vite para build rápido; TypeScript para type-safety | ADR-005 |
| **UI Framework** | Tailwind CSS + shadcn/ui | 4.x | Utility-first CSS; componentes acessíveis e customizáveis; sem vendor lock-in | ADR-005 |
| **Data Fetching** | TanStack Query | 5.x | Cache inteligente de requests; refetch automático; background updates; TypeScript | ADR-005 |
| **Estado Global** | Zustand | 5.x | ~1KB gzip; simples; TypeScript-nativo; sem boilerplate (vs. Redux) | ADR-005 |
| **Gráficos** | Recharts | 2.x | Componentes React declarativos; smooth real-time updates; TypeScript; leve (25KB gzip) | ADR-006 |
| **Mapas** | Leaflet + react-leaflet + OSM | 1.9 + 4.x | OSS gratuito; tiles OpenStreetMap sem API key; popular em projetos IoT acadêmicos | ADR-006 |
| **PWA** | vite-plugin-pwa + Workbox | 0.21 | Service Worker para offline; Web Push (VAPID); app instalável | ADR-005 |
| **Real-time** | WebSocket (FastAPI) | — | Conexão persistente para updates do dashboard; latência mínima | ADR-004 |
| **API Climática** | CPTEC/INPE + OWM | — | Dados meteorológicos brasileiros (primária) + cobertura global (fallback) | — |
| **Alertas Push** | Web Push (VAPID) | — | Push notifications sem app nativo; integrado com PWA | ADR-003 |
| **Alertas Email** | SMTP (aiosmtplib) | — | Canal universal; bibliotecas async disponíveis para FastAPI | ADR-003 |

---

## 6. Architecture Decision Records (ADRs)

### ADR-001: Backend Framework — Python + FastAPI

**Status:** Aceita  
**Data:** 02/04/2026  
**Contexto:** O sistema precisa de uma API backend que suporte ingestão assíncrona de dados IoT, processamento de regras de negócio com cálculos numéricos e comunicação real-time via WebSocket.

#### Opções Consideradas

**Opção A: Python + FastAPI**
- Prós: Async nativo (ASGI); Pydantic v2 para validação rigorosa de payloads; ecossistema científico (numpy, pandas, scipy para cálculos hidrológicos); geração automática de OpenAPI/Swagger; comunidade ativa; WebSocket nativo
- Contras: Performance inferior a Go/Rust para CPU-bound; GIL do Python limita paralelismo real

**Opção B: Node.js + Fastify**
- Prós: Excelente I/O assíncrono; grande ecossistema JavaScript; possibilidade de compartilhar tipos com frontend TypeScript
- Contras: Ecossistema científico limitado (vs. Python/numpy); tipagem com TypeScript é add-on; menos familiar para cálculos numéricos

**Opção C: Go + Gin/Fiber**
- Prós: Performance superior; goroutines nativas; binário compilado leve
- Contras: Ecossistema científico imaturo; verbosidade para validação de schemas; curva de aprendizado para equipe acadêmica; menos produtivo para prototipagem

#### Decisão

**Adotar Python 3.12 + FastAPI 0.115+**

#### Consequências
- **Positivas:** Produtividade alta; validação de dados IoT robusta com Pydantic; cálculos hidrológicos com numpy/scipy; documentação OpenAPI automática (útil para TCC); vasta literatura e exemplos acadêmicos
- **Negativas:** Para cenários de CPU-bound intensivo (muitos piscinões simultâneos), pode ser necessário escalar horizontalmente
- **Riscos:** Mitigáveis via processamento assíncrono (ARQ worker) para tarefas pesadas

#### Referências
- RAMÍREZ, S. FastAPI Documentation. Disponível em: https://fastapi.tiangolo.com/
- Python Software Foundation. Python 3.12 Documentation. Disponível em: https://docs.python.org/3.12/

---

### ADR-002: Banco de Dados — PostgreSQL + TimescaleDB

**Status:** Aceita  
**Data:** 02/04/2026  
**Contexto:** O sistema requer armazenamento de dados relacionais (usuários, reservatórios, configurações) e séries temporais de alta frequência (leituras de sensores a cada minuto). Precisa suportar queries de agregação temporal (médias por hora, por dia) com performance adequada.

#### Opções Consideradas

**Opção A: PostgreSQL 16 + TimescaleDB 2.x**
- Prós: Banco único para relacional + séries temporais; SQL padrão; hypertables com particionamento automático; compressão ~100:1; continuous aggregates pré-computados; ACID completo; ecossistema maduro (backups, replicação, monitoramento)
- Contras: Throughput de escrita menor que InfluxDB para cardinalities extremas (>1M séries)

**Opção B: PostgreSQL + InfluxDB (separados)**
- Prós: InfluxDB otimizado para séries temporais com maior throughput de escrita
- Contras: Dois bancos para manter; dialeto SQL diferente; licenciamento cloud-only para v3; overhead operacional duplicado; custo injustificável para TCC

**Opção C: MongoDB (time-series collections)**
- Prós: Flexibilidade de schema; time-series collections nativas desde v5
- Contras: Sem ACID completo para transações cross-collection; curva de aprendizado para modelagem correta; menos adequado para dados relacionais (usuários, configurações)

#### Decisão

**Adotar PostgreSQL 16 + TimescaleDB 2.x como banco unificado**

#### Consequências
- **Positivas:** Simplicidade operacional (1 banco); SQL padrão (vantagem acadêmica); hypertables com compressão e retenção automática; continuous aggregates reduzem carga de queries no dashboard; ACID garante integridade em alertas
- **Negativas:** Para volumes extremos (>100K sensores), pode necessitar sharding
- **Riscos:** Configuração de chunk_interval e compressão requer tuning — mitigável com defaults recomendados pela documentação TimescaleDB

**ORM e Migrations:**
- SQLAlchemy 2.0 Async com asyncpg como driver
- Alembic para versionamento de schema (migrations)
- SQL raw para queries específicas de TimescaleDB (CREATE HYPERTABLE, continuous aggregates)

#### Referências
- TIMESCALE, Inc. TimescaleDB Documentation. Disponível em: https://docs.timescale.com/
- BAYER, M. SQLAlchemy 2.0 Documentation. Disponível em: https://docs.sqlalchemy.org/

---

### ADR-003: Tasks Assíncronas e Sistema de Alertas

**Status:** Aceita  
**Data:** 02/04/2026  
**Contexto:** O sistema precisa despachar alertas multicanal (push, email) de forma assíncrona, sem bloquear o fluxo de ingestão de dados. O dispatch pode falhar (email timeout, serviço push indisponível) e precisa de retry com backoff.

#### Opções Consideradas

**Opção A: ARQ + Redis**
- Prós: Async-native (await/async); Redis como broker (já no stack); código limpo e idiomático para FastAPI; retry com exponential backoff built-in; leve (~10KB)
- Contras: Sem UI de monitoramento (vs. Celery Flower); comunidade menor

**Opção B: Celery + Redis**
- Prós: Produção comprovada (Netflix, Spotify); Flower UI para monitoramento; periodic tasks (cron-like); múltiplos brokers
- Contras: Configuração complexa; API síncrona (não alinhada com FastAPI async); boilerplate extenso; difícil de explicar em documentação acadêmica

**Opção C: FastAPI BackgroundTasks (nativo)**
- Prós: Zero dependência extra; integrado nativamente
- Contras: Sem retry; sem persistência de tasks (perde jobs se processo cair); sem monitoramento; não escala para múltiplos workers

#### Decisão

**Adotar ARQ + Redis para produção; FastAPI BackgroundTasks como fallback simplificado para desenvolvimento local**

#### Consequências
- **Positivas:** Código async coerente com todo o stack; retry com exponential backoff; Redis já presente; documentação acadêmica mais clara
- **Negativas:** Monitoramento de tasks requer logs + Redis CLI (sem dashboard UI)
- **Riscos:** Para volumes muito altos de alertas, Redis pode acumular fila — mitigável com TTL em tasks e monitoramento de queue length

**Canais de alerta implementados:**

| Canal | MVP | Fase Futura | Tecnologia |
|-------|-----|------------|------------|
| Web Push | ✅ | — | VAPID Keys + Web Push Protocol |
| Email | ✅ | — | aiosmtplib (async SMTP client) |
| SMS | Adapter ready | ✅ | Twilio API (adapter pattern) |
| WhatsApp | Adapter ready | ✅ | Twilio/WhatsApp Business API (adapter pattern) |

#### Referências
- LONG, S. ARQ Documentation. Disponível em: https://arq-docs.helpmanual.io/
- CELERY PROJECT. Celery Documentation. Disponível em: https://docs.celeryq.dev/

---

### ADR-004: Web Server e Real-Time

**Status:** Aceita  
**Data:** 02/04/2026  
**Contexto:** O sistema precisa servir: (1) arquivos estáticos do frontend React, (2) proxy reverso para a API FastAPI, (3) upgrade de conexão para WebSocket (dashboard real-time), (4) SSL termination. O servidor é Ubuntu 24.04 LTS.

#### Opções Consideradas

**Opção A: NGINX como reverse proxy + static server**
- Prós: Padrão da indústria; desempenho excepcional para static files; WebSocket upgrade suportado; SSL termination; rate limiting nativo; cache configurável; configuração declarativa
- Contras: Configuração de WebSocket requer atenção a timeouts e upgrade headers

**Opção B: Caddy**
- Prós: SSL automático (Let's Encrypt); configuração simplificada
- Contras: Menos documentação; comunidade menor em contexto acadêmico; menos controle fino sobre WebSocket

**Opção C: Traefik**
- Prós: Service discovery automático com Docker; dashboard de monitoramento
- Contras: Overkill para projeto com poucos serviços; configuração complexa para cenários simples; mais adequado para Kubernetes

#### Decisão

**Adotar NGINX 1.27 como reverse proxy unificado**

#### Consequências
- **Positivas:** Performance comprovada; WebSocket upgrade configurável; serve React SPA como static files (sem processo Node); SSL termination centralizada; rate limiting protege API; headers de segurança OWASP
- **Negativas:** Configuração manual (vs. Caddy auto-SSL)
- **Riscos:** WebSocket timeout padrão de 60s pode desconectar clientes — mitigável com `proxy_read_timeout 86400`

**Real-time strategy:** WebSocket (FastAPI nativo) via NGINX proxy com upgrade de protocolo.

#### Referências
- NGINX, Inc. NGINX Documentation. Disponível em: https://nginx.org/en/docs/
- NGINX, Inc. WebSocket proxying. Disponível em: https://nginx.org/en/docs/http/websocket.html

---

### ADR-005: Frontend Framework e SPA

**Status:** Aceita  
**Data:** 02/04/2026  
**Contexto:** O sistema precisa de dois dashboards (técnico e público) com gráficos de séries temporais, mapas interativos, atualização em tempo real (WebSocket) e capacidade de funcionar como PWA. O frontend será servido como arquivos estáticos pelo NGINX.

#### Opções Consideradas

**Opção A: React 18 + Vite + TypeScript**
- Prós: Build estático (NGINX serve diretamente, sem Node runtime); bundle leve (~43KB core); HMR ultrarrápido com Vite; ecossistema maduro de componentes; TypeScript para type-safety; PWA via vite-plugin-pwa
- Contras: Sem Server-Side Rendering nativo (irrelevante para dashboards internos)

**Opção B: Next.js 15**
- Prós: SSR/SSG/ISR; full-stack framework; image optimization
- Contras: Requer runtime Node.js no servidor (NGINX → Node → FastAPI = triple hop); bundle maior (~180KB); complexidade adicional sem benefício para SPA; overhead operacional

**Opção C: Vue 3 + Vite**
- Prós: Sintaxe concisa; ótima documentação
- Contras: Ecossistema de componentes UI menor que React; menos familiaridade da equipe

#### Decisão

**Adotar React 18 + TypeScript 5.x + Vite 6.x + Tailwind CSS 4.x**

#### Consequências
- **Positivas:** Build estático puro — NGINX serve sem processo Node; bundle mínimo; HMR instantâneo; TypeScript previne bugs em dados de sensores; Tailwind garante responsividade; shadcn/ui fornece componentes acessíveis
- **Negativas:** SEO limitado (irrelevante — dashboards não precisam ser indexados por buscadores)
- **Riscos:** Complexidade de WebSocket reconexão — mitigável com hook customizado de auto-reconnect

**Bibliotecas complementares:**
- **TanStack Query v5**: Cache inteligente de API calls; refetch automático; background updates
- **Zustand v5**: Estado global leve (~1KB); sem boilerplate; TypeScript-nativo
- **shadcn/ui**: Componentes acessíveis baseados em Radix UI + Tailwind CSS

#### Referências
- META. React Documentation. Disponível em: https://react.dev/
- VITE. Vite Documentation. Disponível em: https://vite.dev/
- TAILWIND LABS. Tailwind CSS Documentation. Disponível em: https://tailwindcss.com/docs

---

### ADR-006: Visualização de Dados — Gráficos e Mapas

**Status:** Aceita  
**Data:** 02/04/2026  
**Contexto:** O dashboard técnico requer gráficos de séries temporais (nível d'água, pluviometria, volume) com atualização em tempo real, além de um mapa interativo mostrando a localização dos reservatórios e seu status visual.

#### Opções Consideradas — Gráficos

**Opção A: Recharts**
- Prós: API declarativa React-nativa (composable); TypeScript first-class; smooth animations para dados real-time; responsive; 25KB gzip
- Contras: Customização limitada para gráficos exóticos (não necessários neste projeto)

**Opção B: Apache ECharts**
- Prós: Extremely customizável; otimizado para 1M+ pontos
- Contras: API imperativa (não React-idiomatic); 82KB gzip; documentação primarily in Chinese; overkill para TCC

**Opção C: Chart.js**
- Prós: Popular; 11KB gzip
- Contras: Canvas-based (re-render completo em updates); wrapper React necessário; acessibilidade limitada

#### Opções Consideradas — Mapas

**Opção A: Leaflet + OpenStreetMap**
- Prós: OSS gratuito; tiles OpenStreetMap sem API key; 39KB gzip; popular em projetos IoT acadêmicos; react-leaflet para integração React
- Contras: Customização visual menor que Mapbox

**Opção B: Mapbox GL JS**
- Prós: Mapas vetoriais de alta qualidade; estilização avançada
- Contras: Requer API key paga; difícil justificar custo em projeto acadêmico

#### Decisão

**Adotar Recharts para gráficos + Leaflet/OpenStreetMap para mapas**

#### Consequências
- **Positivas:** Custo zero (ambos OSS); Recharts se integra naturalmente com React state updates (WebSocket); Leaflet não requer API keys
- **Negativas:** Leaflet usa raster tiles (menor qualidade visual que Mapbox vector tiles)

#### Referências
- RECHARTS. Recharts Documentation. Disponível em: https://recharts.org/
- AGAFONKIN, V. Leaflet — an open-source JavaScript library for interactive maps. Disponível em: https://leafletjs.com/

---

## 7. Modelagem de Dados

### 7.1 Modelo Entidade-Relacionamento

```mermaid
erDiagram
    RESERVATORIO {
        int id PK
        varchar nome
        text descricao
        float latitude
        float longitude
        float capacidade_m3
        float cota_transbordo_m
        float cota_alerta_amarelo_m
        float cota_alerta_laranja_m
        float cota_alerta_vermelho_m
        float area_secao_m2
        varchar endereco
        boolean ativo
        timestamp created_at
        timestamp updated_at
    }

    SENSOR {
        int id PK
        int reservatorio_id FK
        varchar tipo "nivel | pluviometro | meteorologico"
        varchar identificador_externo "ID do gateway"
        varchar descricao
        varchar posicao "Poste 1 | Poste 2"
        varchar unidade_medida "metros | mm"
        varchar status "ativo | inativo | manutencao"
        timestamp ultima_leitura_em
        timestamp created_at
    }

    LEITURA_SENSOR {
        bigint id PK
        int sensor_id FK
        float valor
        varchar unidade "metros | mm"
        timestamp timestamp "Partição TimescaleDB"
        boolean valido
    }

    LEITURA_CLIMATICA {
        bigint id PK
        int reservatorio_id FK
        float temperatura_c
        float umidade_pct
        float previsao_chuva_mm
        varchar condicao
        varchar fonte "CPTEC | OpenWeatherMap"
        timestamp timestamp "Partição TimescaleDB"
    }

    ALERTA {
        int id PK
        int reservatorio_id FK
        varchar nivel "amarelo | laranja | vermelho"
        text mensagem
        float nivel_agua_m
        float taxa_variacao_cm_min
        float tempo_estimado_transbordo_min
        varchar status "ativo | resolvido | expirado"
        timestamp disparado_em
        timestamp resolvido_em
        jsonb canais_notificados
    }

    CONFIGURACAO_ALERTA {
        int id PK
        int reservatorio_id FK
        float threshold_amarelo_pct
        float threshold_laranja_pct
        float threshold_vermelho_pct
        float taxa_variacao_critica_cm_min
        int tempo_transbordo_alerta_laranja_min
        int tempo_transbordo_alerta_vermelho_min
        boolean habilitado
        timestamp updated_at
    }

    USUARIO {
        int id PK
        varchar nome
        varchar email
        varchar senha_hash
        varchar papel "admin | gestor | operador"
        boolean ativo
        timestamp created_at
        timestamp ultimo_login
    }

    INSCRICAO_ALERTA {
        int id PK
        int reservatorio_id FK
        varchar canal "push | email | sms | whatsapp"
        varchar contato "endpoint push | email | telefone"
        varchar token_confirmacao
        boolean confirmado
        timestamp created_at
    }

    RESERVATORIO ||--o{ SENSOR : "possui"
    RESERVATORIO ||--o{ LEITURA_CLIMATICA : "tem leituras de"
    RESERVATORIO ||--o{ ALERTA : "gera"
    RESERVATORIO ||--|| CONFIGURACAO_ALERTA : "tem configuração"
    RESERVATORIO ||--o{ INSCRICAO_ALERTA : "recebe inscrições"
    SENSOR ||--o{ LEITURA_SENSOR : "produz"
```

### 7.2 Detalhamento das Tabelas Críticas

#### Tabela `leitura_sensor` — Hypertable TimescaleDB

Esta é a tabela de maior volume do sistema. Cada sensor produz 1 leitura/minuto. Com 3 sensores, o sistema gera ~4.320 registros/dia ou ~130.000/mês.

```sql
-- Criação da tabela
CREATE TABLE leitura_sensor (
    id          BIGSERIAL,
    sensor_id   INTEGER NOT NULL REFERENCES sensor(id),
    valor       DOUBLE PRECISION NOT NULL,
    unidade     VARCHAR(20) NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valido      BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (id, timestamp)
);

-- Conversão para hypertable com chunks de 1 dia
SELECT create_hypertable('leitura_sensor', 'timestamp',
    chunk_time_interval => INTERVAL '1 day'
);

-- Compressão automática para dados > 7 dias
ALTER TABLE leitura_sensor SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'sensor_id',
    timescaledb.compress_orderby = 'timestamp DESC'
);
SELECT add_compression_policy('leitura_sensor', INTERVAL '7 days');

-- Política de retenção: manter 1 ano de dados
SELECT add_retention_policy('leitura_sensor', INTERVAL '365 days');

-- Continuous Aggregate: médias de 5 minutos
CREATE MATERIALIZED VIEW leitura_sensor_5min
WITH (timescaledb.continuous) AS
SELECT
    sensor_id,
    time_bucket('5 minutes', timestamp) AS bucket,
    AVG(valor) AS valor_medio,
    MIN(valor) AS valor_min,
    MAX(valor) AS valor_max,
    COUNT(*) AS num_leituras
FROM leitura_sensor
WHERE valido = TRUE
GROUP BY sensor_id, bucket;

-- Refresh automático do aggregate
SELECT add_continuous_aggregate_policy('leitura_sensor_5min',
    start_offset    => INTERVAL '1 hour',
    end_offset      => INTERVAL '1 minute',
    schedule_interval => INTERVAL '5 minutes'
);
```

#### Índices Adicionais

```sql
-- Consulta de último valor por sensor (dashboard real-time)
CREATE INDEX idx_leitura_sensor_last
ON leitura_sensor (sensor_id, timestamp DESC);

-- Alertas ativos por reservatório
CREATE INDEX idx_alerta_ativo
ON alerta (reservatorio_id, status) WHERE status = 'ativo';

-- Inscrições confirmadas por reservatório e canal
CREATE INDEX idx_inscricao_ativa
ON inscricao_alerta (reservatorio_id, canal) WHERE confirmado = TRUE;
```

---

## 8. Regras de Negócio

### 8.1 Catálogo de Regras

| ID | Regra | Tipo | Criticidade | Fórmula / Condição |
|----|-------|------|-------------|-------------------|
| RN-01 | Cálculo de volume do reservatório | Cálculo | Alta | $V = h \times A_{seção}$ |
| RN-02 | Taxa de variação do nível | Cálculo | Alta | $\frac{\Delta h}{\Delta t} = \frac{h_{atual} - h_{anterior}}{t_{atual} - t_{anterior}}$ |
| RN-03 | Estimativa de tempo para transbordo | Cálculo | Crítica | $T_{transbordo} = \frac{h_{transbordo} - h_{atual}}{\Delta h / \Delta t}$ |
| RN-04 | Níveis de alerta hierárquicos | Fluxo | Crítica | Vide seção 8.2 |
| RN-05 | Correlação pluviometria × nível | Cálculo | Alta | Se $P > P_{threshold}$ **E** $\frac{\Delta h}{\Delta t} > 0$ → antecipar alerta |
| RN-06 | Redundância de sensores | Validação | Alta | $\|h_{s1} - h_{s2}\| / \bar{h} > 0.10$ → sinalizar falha |

### 8.2 Detalhamento: RN-04 — Níveis de Alerta

O sistema implementa 4 níveis de alerta hierárquicos, baseados na combinação de **percentual de capacidade** e **estimativa de tempo para transbordo**.

| Nível | Cor | Condição de Disparo | Ação |
|-------|-----|---------------------|------|
| **Normal** | 🟢 Verde | $h \leq 60\%$ da capacidade **E** $\frac{\Delta h}{\Delta t} \leq 0$ | Nenhuma |
| **Atenção** | 🟡 Amarelo | $h > 60\%$ **OU** $\frac{\Delta h}{\Delta t} > X$ cm/min | Registro + Dashboard |
| **Alerta** | 🟠 Laranja | $h > 80\%$ **OU** $T_{transbordo} < 120$ min | Registro + Push + Email |
| **Emergência** | 🔴 Vermelho | $h > 90\%$ **OU** $T_{transbordo} < 30$ min | Registro + Push + Email + Todos os canais |

**Notas:**
- O símbolo $h$ representa o **percentual do nível atual** em relação à cota de transbordo
- $X$ (taxa de variação crítica) é **configurável por reservatório** via tabela `configuracao_alerta`
- A **escalação é automática**: se o nível sobe de Amarelo para Laranja, um novo alerta é criado com o nível correto
- A **desescalação** ocorre automaticamente quando o nível desce abaixo do threshold, marcando o alerta anterior como "resolvido"

### 8.3 Detalhamento: RN-01 — Cálculo de Volume

Para o modelo simplificado (MVP), assume-se seção transversal constante:

$$V_{atual} = h_{atual} \times A_{seção}$$

Onde:
- $V_{atual}$ = volume atual de água no reservatório (m³)
- $h_{atual}$ = nível de água medido pelos sensores (m)
- $A_{seção}$ = área da seção transversal do reservatório (m²), obtida do cadastro

**Percentual de capacidade:**

$$\%_{capacidade} = \frac{V_{atual}}{V_{max}} \times 100 = \frac{h_{atual}}{h_{transbordo}} \times 100$$

> **Nota acadêmica:** Modelos mais precisos utilizariam a equação de Manning para vazão em canais abertos ou as equações de Saint-Venant para escoamento não permanente. Estas abordagens são mencionadas como **trabalho futuro**.

### 8.4 Detalhamento: RN-06 — Redundância de Sensores

O sistema instala 2 sensores de nível por piscinão para garantir confiabilidade dos dados.

**Lógica de processamento:**

1. Calcular a média dos 2 sensores: $\bar{h} = \frac{h_{s1} + h_{s2}}{2}$
2. Calcular a divergência relativa: $D = \frac{|h_{s1} - h_{s2}|}{\bar{h}}$
3. Se $D > 10\%$:
   - Sinalizar **falha de sensor** no dashboard técnico
   - Registrar evento de manutenção
   - Utilizar o sensor com histórico mais consistente (menor desvio padrão nas últimas 24h)
4. Se $D \leq 10\%$: usar a média $\bar{h}$ como valor de referência

---

## 9. Endpoints da API

### 9.1 Ingestão de Dados (Interno)

| Método | Path | Descrição | Auth |
|--------|------|-----------|------|
| `POST` | `/api/v1/ingestao/leituras` | Recebe batch de leituras do gateway MQTT | API Key |

**Request Body:**
```json
{
  "gateway_id": "GW-001",
  "timestamp": "2026-04-02T14:30:00Z",
  "leituras": [
    {
      "sensor_id": "SN-001",
      "tipo": "nivel",
      "valor": 2.45,
      "unidade": "metros"
    },
    {
      "sensor_id": "SN-002",
      "tipo": "nivel",
      "valor": 2.42,
      "unidade": "metros"
    },
    {
      "sensor_id": "PLV-001",
      "tipo": "pluviometro",
      "valor": 12.5,
      "unidade": "mm"
    }
  ]
}
```

**Responses:** `201 Created` | `422 Unprocessable Entity` | `401 Unauthorized`

### 9.2 Dashboard Técnico

| Método | Path | Descrição | Auth |
|--------|------|-----------|------|
| `GET` | `/api/v1/reservatorios` | Lista todos os reservatórios com status atual | JWT (gestor) |
| `GET` | `/api/v1/reservatorios/{id}/status` | Status atual (nível, volume, alertas ativos) | JWT (gestor) |
| `GET` | `/api/v1/reservatorios/{id}/historico` | Série temporal de leituras (query params: periodo, agregacao) | JWT (gestor) |
| `GET` | `/api/v1/reservatorios/{id}/alertas` | Histórico de alertas com filtros | JWT (gestor) |
| `GET` | `/api/v1/dashboard/overview` | Visão geral de todos os reservatórios | JWT (gestor) |
| `PUT` | `/api/v1/reservatorios/{id}/configuracao-alerta` | Atualizar thresholds de alerta | JWT (admin) |
| `WS` | `/ws/dashboard/{reservatorio_id}` | Updates em tempo real (nível, alertas) | JWT (gestor) |

### 9.3 Dashboard Público

| Método | Path | Descrição | Auth |
|--------|------|-----------|------|
| `GET` | `/api/v1/publico/status` | Status simplificado de todos os reservatórios (semáforo) | Nenhuma |
| `GET` | `/api/v1/publico/reservatorios/{id}` | Detalhe público (nível, tendência, último alerta) | Nenhuma |
| `WS` | `/ws/publico/{reservatorio_id}` | Updates em tempo real (versão simplificada) | Nenhuma |

### 9.4 Alertas e Inscrições

| Método | Path | Descrição | Auth |
|--------|------|-----------|------|
| `POST` | `/api/v1/alertas/inscricao` | Cidadão se inscreve para alertas | Nenhuma |
| `GET` | `/api/v1/alertas/inscricao/confirmar/{token}` | Confirma inscrição (double opt-in) | Nenhuma |
| `DELETE` | `/api/v1/alertas/inscricao/{id}` | Cancela inscrição | Token único |
| `GET` | `/api/v1/alertas/historico` | Histórico global de alertas | JWT (gestor) |

### 9.5 Integração Climática

| Método | Path | Descrição | Auth |
|--------|------|-----------|------|
| `GET` | `/api/v1/clima/atual/{reservatorio_id}` | Dados climáticos mais recentes para o reservatório | JWT (gestor) |
| `GET` | `/api/v1/clima/previsao/{reservatorio_id}` | Previsão das próximas horas | JWT (gestor) |

### 9.6 Administração

| Método | Path | Descrição | Auth |
|--------|------|-----------|------|
| `POST` | `/api/v1/auth/login` | Autenticação (retorna JWT + refresh token) | — |
| `POST` | `/api/v1/auth/refresh` | Renovar access token | Refresh token |
| `GET` | `/api/v1/admin/sensores` | Listar sensores cadastrados | JWT (admin) |
| `GET` | `/api/v1/admin/sensores/{id}/status` | Status e última leitura do sensor | JWT (admin) |
| `GET` | `/api/v1/health` | Health check do sistema | Nenhuma |
| `GET` | `/api/v1/health/db` | Health check do banco de dados | API Key |
| `GET` | `/api/v1/health/redis` | Health check do Redis | API Key |

---

## 10. Infraestrutura Docker

### 10.1 Visão Macro — docker-compose.yml

```yaml
# docker-compose.yml — Visão macro do ambiente

version: "3.9"

services:

  # ── Reverse Proxy + Static Files ────────────────────────
  nginx:
    image: nginx:1.27-alpine
    container_name: piscinao-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro          # SSL (produção)
      - ./frontend/dist:/app/dist:ro                # React SPA build
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - piscinao-net
    restart: unless-stopped

  # ── Backend FastAPI ─────────────────────────────────────
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: piscinao-backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://piscinao:${DB_PASSWORD}@postgres:5432/piscinao
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - API_KEY_INGESTAO=${API_KEY_INGESTAO}
      - CPTEC_BASE_URL=https://brasilapi.com.br/api/cptec/v1
      - OWM_API_KEY=${OWM_API_KEY}
      - VAPID_PRIVATE_KEY=${VAPID_PRIVATE_KEY}
      - VAPID_PUBLIC_KEY=${VAPID_PUBLIC_KEY}
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
    expose:
      - "8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 10s
    networks:
      - piscinao-net
    restart: unless-stopped

  # ── ARQ Worker (Background Tasks) ──────────────────────
  arq-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: piscinao-worker
    command: arq app.worker.WorkerSettings
    environment:
      - DATABASE_URL=postgresql+asyncpg://piscinao:${DB_PASSWORD}@postgres:5432/piscinao
      - REDIS_URL=redis://redis:6379/0
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - VAPID_PRIVATE_KEY=${VAPID_PRIVATE_KEY}
      - VAPID_PUBLIC_KEY=${VAPID_PUBLIC_KEY}
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    networks:
      - piscinao-net
    restart: unless-stopped

  # ── PostgreSQL 16 + TimescaleDB ─────────────────────────
  postgres:
    image: timescale/timescaledb:latest-pg16
    container_name: piscinao-postgres
    environment:
      - POSTGRES_DB=piscinao
      - POSTGRES_USER=piscinao
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/01-init.sql:ro
    expose:
      - "5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U piscinao -d piscinao"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s
    networks:
      - piscinao-net
    restart: unless-stopped

  # ── Redis 7 ────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: piscinao-redis
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    expose:
      - "6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    networks:
      - piscinao-net
    restart: unless-stopped

# ── Volumes ──────────────────────────────────────────────
volumes:
  pg_data:
    name: piscinao-pg-data
  redis_data:
    name: piscinao-redis-data

# ── Network ──────────────────────────────────────────────
networks:
  piscinao-net:
    name: piscinao-network
    driver: bridge
```

### 10.2 Diagrama de Infraestrutura

```mermaid
graph TB
    subgraph "Host: Ubuntu 24.04 LTS"
        subgraph "Docker Compose"
            NGINX["🔀 NGINX<br>:80 / :443"]
            BACK["🐍 FastAPI<br>:8000"]
            WORKER["⚙️ ARQ Worker"]
            PG[("🐘 PostgreSQL<br>+ TimescaleDB<br>:5432")]
            REDIS[("⚡ Redis<br>:6379")]
        end
    end

    INTERNET["🌐 Internet<br>Usuários + API Clima"]
    IOT["📡 Gateway IoT"]

    INTERNET -->|":80/:443"| NGINX
    IOT -->|"POST /api/v1/ingestao"| NGINX


    NGINX -->|"/api/* → proxy_pass"| BACK
    NGINX -->|"/ws/* → WebSocket upgrade"| BACK
    NGINX -->|"/* → static files"| DIST[("📁 /app/dist<br>React SPA")]

    BACK -->|"asyncpg"| PG
    BACK -->|"aioredis"| REDIS
    WORKER -->|"asyncpg"| PG
    WORKER -->|"arq consume"| REDIS
    BACK -->|"arq enqueue"| REDIS
```

---

## 11. Configuração NGINX

### 11.1 Arquivo de Configuração Completo

```nginx
# nginx/nginx.conf — Configuração do NGINX para o Sistema de Monitoramento

upstream fastapi_backend {
    server backend:8000;
}

# Rate limiting zone (proteção contra abuso)
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=ingestao_limit:10m rate=10r/s;

server {
    listen 80;
    server_name _;

    # ── Security Headers (OWASP) ──────────────────────────
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://*.tile.openstreetmap.org; connect-src 'self' ws: wss:;" always;

    # Ocultar versão do NGINX
    server_tokens off;

    # Tamanho máximo de upload (payloads de sensores)
    client_max_body_size 1m;

    # ── 1. React SPA (Static Files) ──────────────────────
    root /app/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache agressivo para assets estáticos (JS, CSS, imagens)
    location ~* \.(js|css|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot|ico)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # ── 2. API REST (Reverse Proxy) ──────────────────────
    location /api/ {
        limit_req zone=api_limit burst=50 nodelay;

        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # ── 3. Endpoint de Ingestão (Rate limit específico) ──
    location /api/v1/ingestao/ {
        limit_req zone=ingestao_limit burst=20 nodelay;

        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ── 4. WebSocket (Dashboard Real-time) ───────────────
    location /ws/ {
        proxy_pass http://fastapi_backend;

        # Headers obrigatórios para WebSocket upgrade
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Headers de identificação
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout longo para conexões persistentes (24h)
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;

        # Desabilitar buffering para streaming
        proxy_buffering off;
    }

    # ── 5. Health Check (monitoramento) ──────────────────
    location /api/v1/health {
        proxy_pass http://fastapi_backend;
        access_log off;
    }

    # ── 6. Bloquear acesso a arquivos sensíveis ──────────
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1000;
    gzip_comp_level 6;
}
```

---

## 12. Estrutura de Diretórios

### 12.1 Estrutura Completa do Projeto

```
piscinao-monitor/
├── README.md
├── docker-compose.yml
├── docker-compose.dev.yml              # Override para desenvolvimento
├── .env.example                        # Template de variáveis
├── .gitignore
│
├── docs/                               # Documentação técnica
│   ├── 001 - Plano de desenvolvimento.md
│   ├── 002 - SRS.md
│   ├── 003 - PRD.md
│   ├── 004 - DevSpecs.md              # Este documento
│   └── 005 - Backlog Tecnico.md
│
├── backend/                            # Python + FastAPI
│   ├── Dockerfile
│   ├── pyproject.toml                  # Dependências (Poetry/pip)
│   ├── alembic.ini                     # Configuração Alembic
│   ├── alembic/                        # Migrations
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # Bootstrap FastAPI
│   │   ├── config.py                   # Settings (Pydantic BaseSettings)
│   │   ├── database.py                 # Session factory + engine
│   │   ├── dependencies.py             # Dependency injection
│   │   ├── worker.py                   # ARQ WorkerSettings
│   │   │
│   │   ├── core/                       # Código compartilhado
│   │   │   ├── auth/                   # JWT + RBAC + API Key
│   │   │   │   ├── jwt.py
│   │   │   │   ├── rbac.py
│   │   │   │   └── api_key.py
│   │   │   ├── middleware/             # CORS, logging, error handler
│   │   │   ├── exceptions/            # Classes de erro customizadas
│   │   │   ├── pagination/            # Paginação genérica
│   │   │   └── websocket/             # Connection Manager
│   │   │       └── manager.py
│   │   │
│   │   ├── modules/                    # Módulos de domínio
│   │   │   ├── ingestao/              # Ingestão de dados IoT
│   │   │   │   ├── models.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── service.py
│   │   │   │   └── router.py
│   │   │   │
│   │   │   ├── processamento/         # Cálculos hidrológicos
│   │   │   │   ├── service.py
│   │   │   │   └── rules_engine.py
│   │   │   │
│   │   │   ├── alertas/               # Sistema de alertas
│   │   │   │   ├── models.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── service.py
│   │   │   │   ├── router.py
│   │   │   │   ├── dispatcher.py      # Multicanal dispatch
│   │   │   │   └── adapters/          # Adapter pattern
│   │   │   │       ├── base.py        # Interface abstrata
│   │   │   │       ├── email.py
│   │   │   │       ├── web_push.py
│   │   │   │       ├── sms.py         # Futuro (Twilio)
│   │   │   │       └── whatsapp.py    # Futuro (Twilio)
│   │   │   │
│   │   │   ├── dashboard/             # API para dashboards
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   └── router.py
│   │   │   │
│   │   │   ├── clima/                 # Integração APIs externas
│   │   │   │   ├── models.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   └── adapters/
│   │   │   │       ├── base.py
│   │   │   │       ├── cptec.py       # CPTEC/INPE
│   │   │   │       └── openweather.py # OpenWeatherMap
│   │   │   │
│   │   │   └── auth/                  # Autenticação
│   │   │       ├── models.py
│   │   │       ├── schemas.py
│   │   │       ├── service.py
│   │   │       └── router.py
│   │   │
│   │   └── tasks/                     # ARQ background tasks
│   │       ├── alert_dispatch.py
│   │       └── clima_sync.py
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_ingestao/
│       ├── test_processamento/
│       ├── test_alertas/
│       └── test_dashboard/
│
├── frontend/                           # React + TypeScript + Vite
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── index.html
│   │
│   ├── public/
│   │   ├── manifest.json              # PWA manifest
│   │   └── icons/
│   │
│   └── src/
│       ├── main.tsx                    # Entry point
│       ├── App.tsx                     # Router principal
│       │
│       ├── components/                 # Componentes compartilhados
│       │   ├── ui/                     # shadcn/ui components
│       │   ├── layout/                 # Header, Sidebar, Footer
│       │   ├── charts/                 # WaterLevelChart, RainfallChart
│       │   │   ├── WaterLevelChart.tsx
│       │   │   ├── RainfallChart.tsx
│       │   │   └── VolumeChart.tsx
│       │   ├── maps/                   # ReservoirMap
│       │   │   └── ReservoirMap.tsx
│       │   └── alerts/                 # AlertBadge, AlertHistory
│       │       └── AlertBadge.tsx
│       │
│       ├── features/                   # Módulos por feature
│       │   ├── dashboard-tecnico/      # Dashboard técnico
│       │   │   ├── pages/
│       │   │   ├── components/
│       │   │   └── hooks/
│       │   ├── dashboard-publico/      # Dashboard público
│       │   │   ├── pages/
│       │   │   ├── components/
│       │   │   └── hooks/
│       │   ├── alertas/                # Inscrição e histórico
│       │   └── auth/                   # Login (gestores)
│       │
│       ├── hooks/                      # Hooks globais
│       │   ├── useRealtimeSensors.ts   # WebSocket hook
│       │   ├── useAlerts.ts
│       │   └── useAuth.ts
│       │
│       ├── lib/                        # Utilitários
│       │   ├── api.ts                  # Axios/fetch client
│       │   ├── websocket.ts            # WS connection manager
│       │   └── formatters.ts           # Formatação de datas, números
│       │
│       ├── stores/                     # Zustand stores
│       │   ├── sensorStore.ts
│       │   └── alertStore.ts
│       │
│       └── types/                      # TypeScript types
│           ├── sensor.ts
│           ├── reservoir.ts
│           └── alert.ts
│
├── nginx/                              # Configuração NGINX
│   ├── nginx.conf
│   └── certs/                          # Certificados SSL (gitignored)
│
└── scripts/                            # Scripts auxiliares
    ├── init-db.sql                     # Inicialização do banco (hypertables)
    ├── seed.py                         # Dados de desenvolvimento
    ├── setup.sh                        # Bootstrap do ambiente
    └── reset-db.sh                     # Reset do banco
```

---

## 13. Glossário Ubíquo

Vocabulário compartilhado entre domínio de negócio e implementação técnica.

| Termo | Definição | Contexto | Sinônimos a Evitar |
|-------|-----------|----------|-------------------|
| **Piscinão** | Reservatório de detenção de águas pluviais para amortecimento de cheias urbanas | Domínio hidráulico | Lagoa, represa, barragem |
| **Pôlder** | Termo técnico para áreas de proteção contra inundação; utilizado como sinônimo de piscinão neste projeto | Engenharia civil | — |
| **Reservatório** | Entidade principal do sistema; representa um piscinão cadastrado com seus sensores e configurações | Contexto do sistema | Piscinão (são intercambiáveis no sistema) |
| **Cota de transbordo** | Nível máximo de água (em metros) que o reservatório suporta antes de transbordar | Domínio hidráulico | Nível máximo, capacidade (impreciso) |
| **Nível d'água** | Altura da lâmina d'água medida pelos sensores, em metros, a partir do fundo do reservatório | Medição IoT | Profundidade (ambíguo) |
| **Taxa de variação** | Velocidade de subida/descida do nível d'água, expressa em cm/min ($\Delta h / \Delta t$) | Cálculo | Velocidade de enchimento |
| **Estimativa de transbordo** | Tempo estimado (em minutos) para que o nível d'água atinja a cota de transbordo, baseado na taxa de variação atual | Cálculo | Previsão de enchente |
| **Hypertable** | Tabela do TimescaleDB otimizada para séries temporais, com particionamento automático por tempo | Infraestrutura | Tabela particionada |
| **Continuous Aggregate** | View materializada do TimescaleDB que pré-computa agregações (médias, min, max) em intervalos regulares | Infraestrutura | Cache de agregação |
| **Leitura** | Um ponto de dado produzido por um sensor em um instante de tempo (valor + unidade + timestamp) | IoT | Medição, amostra |
| **Gateway** | Dispositivo intermediário que coleta dados dos sensores (via LoRa/WiFi) e os encaminha ao broker MQTT | IoT | Concentrador, hub |
| **Alerta** | Notificação automática disparada quando um threshold é atingido, com nível de severidade (amarelo/laranja/vermelho) | Domínio | Aviso, notificação (parcialmente) |
| **Inscrição** | Registro voluntário de um cidadão para receber alertas de um reservatório específico, por um canal de comunicação | Domínio | Cadastro (ambíguo) |
| **Dashboard técnico** | Interface web para gestores e Defesa Civil, com gráficos completos, histórico e configuração | Produto | Painel administrativo |
| **Dashboard público** | Interface web simplificada para cidadãos, com semáforo de risco e informações acessíveis | Produto | Painel público |
| **PWA** | Progressive Web App — aplicação web que pode ser instalada como app no dispositivo, com suporte a push notifications e cache offline | Frontend | App web |

---

## 14. Referências

### Arquitetura de Software

BASS, L.; CLEMENTS, P.; KAZMAN, R. **Software Architecture in Practice**. 4. ed. Boston: Addison-Wesley, 2021.

RICHARDS, M.; FORD, N. **Fundamentals of Software Architecture**. Sebastopol: O'Reilly Media, 2020.

NYGARD, M. T. ADR — Architecture Decision Records. Disponível em: https://adr.github.io/. Acesso em: 01 abr. 2026.

BROWN, S. **The C4 Model for Visualising Software Architecture**. Disponível em: https://c4model.com/. Acesso em: 01 abr. 2026.

### Stack Tecnológico

RAMÍREZ, S. **FastAPI Documentation**. Disponível em: https://fastapi.tiangolo.com/. Acesso em: 01 abr. 2026.

BAYER, M. **SQLAlchemy 2.0 Documentation**. Disponível em: https://docs.sqlalchemy.org/. Acesso em: 01 abr. 2026.

TIMESCALE, Inc. **TimescaleDB Documentation**. Disponível em: https://docs.timescale.com/. Acesso em: 01 abr. 2026.

META. **React Documentation**. Disponível em: https://react.dev/. Acesso em: 01 abr. 2026.

VITE. **Vite Documentation**. Disponível em: https://vite.dev/. Acesso em: 01 abr. 2026.

TAILWIND LABS. **Tailwind CSS Documentation**. Disponível em: https://tailwindcss.com/docs. Acesso em: 01 abr. 2026.

NGINX, Inc. **NGINX Documentation**. Disponível em: https://nginx.org/en/docs/. Acesso em: 01 abr. 2026.

DOCKER, Inc. **Docker Documentation**. Disponível em: https://docs.docker.com/. Acesso em: 01 abr. 2026.

LONG, S. **ARQ Documentation**. Disponível em: https://arq-docs.helpmanual.io/. Acesso em: 01 abr. 2026.

RECHARTS. **Recharts Documentation**. Disponível em: https://recharts.org/. Acesso em: 01 abr. 2026.

AGAFONKIN, V. **Leaflet** — an open-source JavaScript library for interactive maps. Disponível em: https://leafletjs.com/. Acesso em: 01 abr. 2026.

### Domínio — Hidrologia e Drenagem

TUCCI, C. E. M. **Hidrologia: ciência e aplicação**. 4. ed. Porto Alegre: ABRH/UFRGS, 2009.

CANHOLI, A. P. **Drenagem urbana e controle de enchentes**. 2. ed. São Paulo: Oficina de Textos, 2014.

### IoT

ATZORI, L.; IERA, A.; MORABITO, G. The Internet of Things: a survey. **Computer Networks**, v. 54, n. 15, p. 2787-2805, 2010.

OASIS Standard. **MQTT Version 5.0**. 2019. Disponível em: https://mqtt.org/. Acesso em: 01 abr. 2026.
