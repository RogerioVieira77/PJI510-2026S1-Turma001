# Sistema de Monitoramento de Piscinões — PRD

## Pesquisa e Desenvolvimento — Product Requirements Document

**Projeto:** PJI510 — Projeto Integrador em Engenharia da Computação  
**Instituição:** UNIVESP — Universidade Virtual do Estado de São Paulo  
**Versão:** 1.0  
**Data:** 05/05/2026  
**Status:** Em Desenvolvimento  
**Base documental:** 001 - Plano de Desenvolvimento | 002 - SRS | 004 - DevSpecs  

---

## Sumário Executivo

Este documento traduz os requisitos levantados no SRS em **decisões de arquitetura de solução** para o PiscinãoMonitor — sistema de monitoramento em tempo real de reservatórios de detenção hidráulica (piscinões) na Região Metropolitana de São Paulo.

O sistema responde a um problema social concreto e recorrente: enchentes urbanas causam mortes, prejuízos e deslocamentos em massa anualmente. Os piscinões são a principal infraestrutura de mitigação da RMSP, mas carecem de monitoramento inteligente e acessível à população.

O PiscinãoMonitor prioriza:

1. **Confiabilidade de dados** — séries temporais persistidas com TimescaleDB, redundância de sensores
2. **Alertas proativos** — notificações automáticas multicanal antes que o transbordo ocorra
3. **Acesso democrático** — dashboard público sem login, funcional em qualquer smartphone via PWA
4. **Operabilidade simples** — monolito modular em Docker, sem orquestração complexa para equipe reduzida

---

## Sumário

1. [Contexto e Motivação](#1-contexto-e-motivação)
2. [Estado da Arte](#2-estado-da-arte)
3. [Fundamentação Teórica](#3-fundamentação-teórica)
4. [Visão do Produto](#4-visão-do-produto)
5. [Decisão Arquitetural](#5-decisão-arquitetural)
6. [Stack Tecnológica com Justificativas](#6-stack-tecnológica-com-justificativas)
7. [Estrutura de Diretórios](#7-estrutura-de-diretórios)
8. [Infraestrutura Docker](#8-infraestrutura-docker)
9. [ADRs — Architecture Decision Records](#9-adrs--architecture-decision-records)
10. [Metodologia de Desenvolvimento](#10-metodologia-de-desenvolvimento)
11. [Referências Bibliográficas](#11-referências-bibliográficas)

---

## 1. Contexto e Motivação

### 1.1 O Problema das Enchentes Urbanas na RMSP

A Região Metropolitana de São Paulo (RMSP) é uma das metrópoles mais vulneráveis a enchentes urbanas do mundo. Fatores estruturais contribuem para esse cenário:

- **Impermeabilização do solo**: mais de 70% da superfície da cidade é pavimentada, impedindo a infiltração natural da água das chuvas
- **Adensamento em áreas de risco**: ocupação histórica de várzeas e fundos de vale por populações vulneráveis
- **Intensificação das chuvas**: eventos extremos têm aumentado em frequência e intensidade, com episódios de até 100 mm em 2 horas
- **Infraestrutura de drenagem insuficiente**: sistemas de micro e macro drenagem projetados décadas atrás, subdimensionados para o crescimento urbano atual

Segundo o Centro de Gerenciamento de Emergências (CGE) da Prefeitura de São Paulo, em 2023 foram registrados **73 pontos de alagamento** somente na capital. Dados do DAEE-SP indicam que enchentes causam anualmente prejuízos superiores a **R$ 1 bilhão** na RMSP, além de dezenas de mortes e deslocamentos de famílias inteiras.

### 1.2 Os Piscinões como Solução Estrutural

Os **piscinões** (reservatórios de detenção hidráulica, também chamados de pôlders) são a principal estratégia de infraestrutura para conter cheias na RMSP. Funcionam como grandes "esponjas" que absorvem temporariamente o excesso de água durante chuvas intensas, liberando-a gradualmente após o pico do evento.

O DAEE-SP opera atualmente mais de 30 piscinões na RMSP, com capacidade total superior a 20 milhões de m³. Os maiores reservatórios incluem:

| Piscinão | Localização | Capacidade (m³) |
|----------|-------------|-----------------|
| Aricanduva | Zona Leste — SP | 1.500.000 |
| Cabuçu | Guarulhos | 860.000 |
| Guarapiranga | Santo André | 600.000 |
| Sacomã | Zona Sudeste — SP | 450.000 |

### 1.3 A Lacuna de Monitoramento

Apesar de sua importância, os piscinões sofrem com ausência de monitoramento contínuo acessível ao público:

1. **Sem visibilidade pública**: a população que mora no entorno não tem acesso a informações em tempo real sobre o nível dos reservatórios
2. **Alertas reativos**: os alertas são emitidos apenas quando a enchente já está em curso, sem antecipação baseada em tendência
3. **Dados não integrados**: sensores existentes (quando presentes) não têm dados consolidados ou acessíveis via API pública
4. **Comunicação técnica inacessível**: quando existem, os dados são apresentados em linguagem técnica incompreensível para a população

O PiscinãoMonitor endereça essa lacuna com uma solução IoT + Web que monitora o nível dos reservatórios em tempo real e comunica o risco em linguagem acessível.

---

## 2. Estado da Arte

### 2.1 Sistemas Existentes no Brasil

#### AlertaRio (Rio de Janeiro)

O sistema AlertaRio, operado pela Prefeitura do Rio de Janeiro, é o mais desenvolvido de monitoramento hidrometeorológico no Brasil. Opera com uma rede de +130 pluviômetros automáticos e fornece alertas em 5 níveis. Suas limitações incluem: foco exclusivo em pluviometria (não monitora nível de reservatórios), interface orientada a técnicos, sem PWA ou notificações push para a população.

#### CEMADEN — Sistema de Alerta de Desastres

O CEMADEN (Centro Nacional de Monitoramento e Alertas de Desastres Naturais) opera rede nacional de sensores de pluviometria e disponibiliza dados via portal web e API. Possui cobertura ampla, mas não monitora infraestrutura específica (piscinões) e não tem dashboards públicos em linguagem acessível.

#### SATVerde — DAEE-SP

O DAEE-SP opera o SATVerde (Sistema de Alerta de Cheias) com telemetria de níveis de rios. Os dados são acessíveis apenas para técnicos, sem interface pública nem notificações automáticas.

#### SCADA Industrial (Supervisory Control and Data Acquisition)

Sistemas SCADA tradicionais são usados em algumas instalações de controle hídrico para automação e supervisão. São altamente eficientes para operação industrial, mas apresentam custo elevado (dezenas de milhares de reais), complexidade de implantação e são orientados a operadores, não ao público geral.

### 2.2 Soluções Internacionais de Referência

| Sistema | País | Características | Limitação |
|---------|------|-----------------|-----------|
| FloodSmart (FEMA) | EUA | Portal de risco de inundação baseado em mapas | Dados históricos, não tempo real |
| Waterwatch | Austrália | Monitoramento de níveis de rios em tempo real | Foco em rios, não reservatórios urbanos |
| Thames Barrier Monitoring | UK | Monitoramento de estruturas de contenção | Proprietário, não replicável |

### 2.3 Lacunas Identificadas e Oportunidade

Nenhum dos sistemas analisados oferece simultaneamente:
- Monitoramento específico de **reservatórios de detenção urbana** (piscinões)
- Interface **pública e acessível** com semáforo de risco
- **Alertas push** para cidadãos residentes no entorno
- **PWA** com funcionamento offline
- **Stack aberta e replicável** por equipes técnicas municipais

O PiscinãoMonitor preenche esse vazio com uma solução de **custo de implantação minimizado**, baseada inteiramente em tecnologias open-source.

---

## 3. Fundamentação Teórica

### 3.1 Internet das Coisas (IoT) e Protocolos

O projeto utiliza sensores IoT para coleta de dados físicos (nível d'água, pluviometria) e os integra ao sistema via protocolo **MQTT** (Message Queuing Telemetry Transport).

MQTT é um protocolo de mensageria leve baseado no padrão publish/subscribe, projetado para dispositivos com recursos limitados e redes de baixa largura de banda. Suas características relevantes para o projeto:

- **QoS (Quality of Service)**: três níveis de garantia de entrega (0, 1, 2)
- **Persistência de sessão**: mensagens retidas para dispositivos que ficam offline temporariamente
- **Topologia de tópicos**: hierarquia flexível (ex.: `piscinao/{id}/nivel`)
- **Overhead mínimo**: cabeçalho de apenas 2 bytes, eficiente para redes celulares 4G em campo

O gateway IoT (fora do escopo direto do MVP) conecta os sensores ao broker MQTT e expõe os dados via endpoint REST que o sistema consome.

### 3.2 Banco de Dados de Séries Temporais — TimescaleDB

O PiscinãoMonitor gera dados de **séries temporais**: sequências de leituras indexadas por tempo com alta frequência de escrita. Bancos relacionais tradicionais degradam significativamente ao lidar com tabelas de bilhões de linhas de séries temporais sem otimização específica.

**TimescaleDB** é uma extensão open-source do PostgreSQL que resolve este problema via:

- **Hypertables**: particionamento automático por tempo — o banco divide a tabela em chunks (ex.: 1 semana) transparentemente
- **Compressão nativa**: redução de até 90% no espaço em disco para dados de séries temporais
- **Continuous aggregates**: views materializadas que pré-computam agregações (médias horárias, diárias) automaticamente
- **Retention policies**: exclusão automática de dados antigos com base em política de tempo
- **100% PostgreSQL**: todo o ecossistema PostgreSQL (ORMs, ferramentas, drivers) funciona sem modificação

### 3.3 Modelos Hidrológicos Simplificados

Para o MVP, o sistema implementa cálculos hidrológicos simplificados que assumem **seção transversal constante** do reservatório:

$$V = h \times A_{seção}$$

Este modelo é adequado para monitoramento de tendência e disparo de alertas, embora não represente com precisão a geometria real dos grandes piscinões (que possuem seções variáveis). Versões futuras poderiam incorporar o modelo de Manning ou curvas cota-volume específicas fornecidas pelo DAEE.

### 3.4 Progressive Web Apps (PWA)

A entrega como **PWA** é uma decisão estratégica baseada nas características do público-alvo:

- **Sem necessidade de instalação via app store**: usuário instala diretamente pelo browser
- **Service Worker**: intercepta requests de rede, permite funcionamento offline
- **Web Push Notifications**: notificações push nativas via VAPID, sem SDK proprietário
- **Add to Home Screen**: ícone na tela inicial do celular, experiência próxima a app nativo
- **Manifest.json**: metadados da aplicação (ícone, splash screen, orientação)

A especificação VAPID (Voluntary Application Server Identification) garante que apenas servidores autorizados enviem notificações para um dispositivo inscrito, sem intermediário de plataforma (Apple Push / Firebase).

### 3.5 Arquitetura de Monolito Modular

O conceito de **monolito modular** (Modular Monolith) estabelece que os módulos do sistema têm fronteiras de domínio bem definidas (sem dependências cruzadas nas camadas internas), mas são **implantados como um único processo**. Isso combina:

- A **simplicidade operacional** de um monolito (um processo, um deploy, um banco de dados)
- A **organização de código** de uma arquitetura orientada a serviços (domínios isolados, testáveis independentemente)

Esta abordagem é endossada pela literatura de Domain-Driven Design (Evans, 2003) e pela prática de times como o Stack Overflow, que opera como monolito modular servindo bilhões de pageviews.

---

## 4. Visão do Produto

### 4.1 Declaração de Visão

> O PiscinãoMonitor é um sistema de monitoramento em tempo real de reservatórios de detenção hidráulica que democratiza o acesso à informação sobre risco de enchentes na RMSP, fornecendo dados precisos para técnicos da Defesa Civil e alertas acessíveis para a população, contribuindo para salvar vidas e reduzir prejuízos causados por eventos de chuva extrema.

### 4.2 Objetivos Mensuráveis do Produto

| Objetivo | Métrica | Meta MVP |
|----------|---------|----------|
| Latência de alerta | Tempo entre leitura crítica e notificação push entregue | ≤ 60 segundos |
| Cobertura de monitoramento | Reservatórios monitorados no MVP | ≥ 1 reservatório funcional |
| Disponibilidade | Uptime mensal do sistema | ≥ 99,5% |
| Tempo de ingestão | P95 do endpoint POST /ingestao/leituras | ≤ 500ms |
| Tamanho do bundle | JavaScript gzipped do frontend | ≤ 250 KB |
| Acessibilidade | WCAG 2.1 do dashboard público | Nível AA |

### 4.3 Proposta de Valor por Perfil

| Perfil | Proposta de Valor Central |
|--------|---------------------------|
| **Cidadão** | "Saiba antes que a enchente chegue: receba alertas no celular quando o piscinão perto de você encher" |
| **Gestor / Defesa Civil** | "Antecipe decisões operacionais com dados precisos de nível, taxa de variação e estimativa de transbordo em tempo real" |
| **Administrador** | "Configure e monitore o sistema de monitoramento em minutos, sem complexidade de infraestrutura" |

---

## 5. Decisão Arquitetural

### 5.1 Escolha: Monolito Modular

Após análise das alternativas (microserviços, serverless, monolito tradicional), a decisão é adotar **monolito modular com separação por domínios de negócio**.

**Alternativas Consideradas:**

| Alternativa | Prós | Contras |
|-------------|------|---------|
| Microserviços | Escalabilidade independente, isolamento de falhas | Overhead operacional desproporcional para equipe de 1-5 devs; comunicação via rede entre serviços; debugging complexo |
| Serverless (Lambda/Functions) | Sem gerenciamento de servidor, escala automática | Cold start incompatível com WebSocket; vendor lock-in; custo imprevisível |
| Monolito tradicional (sem módulos) | Máxima simplicidade inicial | Acoplamento crescente, difícil de testar e manter |
| **Monolito Modular** | Simplicidade operacional + organização por domínio | Único ponto de falha (mitigado por Docker restart) |

**Decisão: Monolito Modular** com FastAPI organizados em módulos com fronteiras de domínio claras.

**Consequências Aceitas:**
- Todo o código implantado como um único processo FastAPI
- Banco de dados único (PostgreSQL + TimescaleDB) compartilhado pelos módulos
- Escalabilidade horizontal simples (replicar o container do backend)
- Extração futura de serviços independentes é possível sem reescrita total

---

## 6. Stack Tecnológica com Justificativas

| Camada | Tecnologia | Versão | Justificativa |
|--------|------------|--------|---------------|
| **Linguagem Backend** | Python | 3.12 | Ecossistema científico/IoT consolidado, tipagem estática com Pydantic, async nativo no 3.12 |
| **Framework Backend** | FastAPI | 0.115 | Performance próxima a NodeJS/Go, OpenAPI automático, suporte nativo a async/await e WebSocket, validação Pydantic integrada |
| **ORM** | SQLAlchemy | 2.0 Async | Único ORM Python com suporte async maduro; compatível com asyncpg para PostgreSQL |
| **Driver PostgreSQL** | asyncpg | latest | Driver PostgreSQL 100% async, ~3x mais rápido que psycopg2 em workloads assíncronos |
| **Migrations** | Alembic | latest | Padrão de fato para migrations SQLAlchemy; autogenerate de schemas; suporte a rollback |
| **Banco de Dados** | PostgreSQL | 16 | Confiabilidade comprovada, ACID, JSON nativo, extensível via TimescaleDB |
| **Séries Temporais** | TimescaleDB | 2.x | Extensão PostgreSQL para hypertables, compressão nativa (até 90%), continuous aggregates, retention policies |
| **Cache / Pub-Sub** | Redis | 7 | Cache em memória, pub/sub para WebSocket, broker para ARQ worker |
| **Task Queue** | ARQ | latest | Biblioteca async-native para Python, integração direta com asyncio, Redis como broker |
| **Servidor Web** | NGINX | 1.27 | Reverse proxy, SSL termination, WebSocket upgrade, rate limiting, headers de segurança OWASP, serving de static files |
| **Framework Frontend** | React | 18 | SPA matura, ecossistema extenso, Server Components disponível para fases futuras |
| **Linguagem Frontend** | TypeScript | 5.x | Type safety em todos os componentes, melhor DX e refatoração mais segura |
| **Build Tool** | Vite | 6.x | Build 10-100x mais rápido que Webpack, HMR instantâneo, suporte nativo a PWA via plugin |
| **CSS Framework** | Tailwind CSS | 4.x | Utility-first, bundle minimal no build, consistência de design sem CSS customizado |
| **Componentes UI** | shadcn/ui | latest | Componentes headless acessíveis (Radix UI), totalmente customizáveis, sem lock-in de biblioteca |
| **Data Fetching** | TanStack Query | 5 | Cache inteligente, revalidação automática, perfeito para dados em tempo real |
| **State Management** | Zustand | 5 | Minimalista, sem boilerplate, ideal para estado global simples (auth, config) |
| **Gráficos** | Recharts | 2.x | Baseado em SVG, React-native, ótimo para séries temporais |
| **Mapas** | Leaflet / react-leaflet | latest | Open-source, leve (40 KB), tiles OpenStreetMap gratuitos |
| **PWA** | vite-plugin-pwa | latest | Service Worker automático via Workbox, manifest.json, Web Push |
| **Containerização** | Docker + Compose | latest | Ambiente reproduzível, deploy simplificado, isolamento de serviços |
| **OS** | Ubuntu Server | 24.04 LTS | LTS com suporte até 2029, Docker Community Edition suportado |

---

## 7. Estrutura de Diretórios

```
piscinao-monitor/
├── docker-compose.yml           # Orquestração: backend, frontend, postgres, redis, nginx
├── docker-compose.override.yml  # Overrides de desenvolvimento (mounts, hot reload)
├── .env.example                 # Template de variáveis de ambiente
├── .gitignore
├── README.md
│
├── backend/                     # Aplicação FastAPI (Python 3.12)
│   ├── Dockerfile
│   ├── pyproject.toml           # Dependências (uv / pip)
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/            # Migration files gerados pelo Alembic
│   │
│   ├── app/
│   │   ├── main.py              # FastAPI app factory, inclusão de routers, middleware
│   │   ├── config.py            # Settings via Pydantic BaseSettings (lê .env)
│   │   ├── database.py          # Engine async SQLAlchemy, session factory
│   │   ├── dependencies.py      # Injeções de dependência (get_db, get_current_user)
│   │   │
│   │   ├── core/                # Módulo transversal (auth, segurança, utils)
│   │   │   ├── security.py      # JWT encode/decode, bcrypt hash
│   │   │   ├── middleware.py    # CORS, rate limiting, logging middleware
│   │   │   └── exceptions.py   # Exception handlers globais
│   │   │
│   │   ├── modules/
│   │   │   ├── ingestao/        # Recebimento de leituras do gateway IoT
│   │   │   │   ├── models.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── service.py
│   │   │   │   └── router.py
│   │   │   │
│   │   │   ├── processamento/   # Cálculos: volume, taxa, estimativa de transbordo
│   │   │   │   ├── models.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── service.py
│   │   │   │   ├── policies.py  # Regras de negócio RN-01 a RN-06
│   │   │   │   └── router.py
│   │   │   │
│   │   │   ├── alertas/         # Avaliação de thresholds e dispatch multicanal
│   │   │   │   ├── models.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── service.py
│   │   │   │   ├── dispatcher.py # Orquestração de canais de notificação
│   │   │   │   ├── adapters/
│   │   │   │   │   ├── push.py  # Web Push VAPID
│   │   │   │   │   └── email.py # aiosmtplib SMTP
│   │   │   │   └── router.py
│   │   │   │
│   │   │   ├── dashboard/       # Endpoints REST + WebSocket para frontend
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   └── router.py    # /api/v1/reservatorios + /ws/dashboard + /ws/publico
│   │   │   │
│   │   │   ├── clima/           # Integração CPTEC/INPE + OpenWeatherMap
│   │   │   │   ├── models.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── service.py
│   │   │   │   └── client.py    # HTTP client com fallback automático
│   │   │   │
│   │   │   └── auth/            # Login, refresh token, RBAC
│   │   │       ├── models.py
│   │   │       ├── schemas.py
│   │   │       ├── repository.py
│   │   │       ├── service.py
│   │   │       └── router.py
│   │   │
│   │   └── worker/
│   │       └── tasks.py         # ARQ task definitions (envio push/email async)
│   │
│   └── tests/
│       ├── unit/                # Testes unitários de service.py e policies.py
│       └── integration/         # Testes de integração dos endpoints (httpx AsyncClient)
│
├── frontend/                    # React 18 + TypeScript + Vite
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts           # PWA plugin, proxy para /api e /ws em dev
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   │
│   ├── public/
│   │   ├── manifest.json        # PWA manifest
│   │   └── icons/               # Ícones da aplicação (192x192, 512x512)
│   │
│   └── src/
│       ├── main.tsx             # Entry point, ReactDOM.render
│       ├── App.tsx              # Roteamento (react-router-dom)
│       ├── sw.ts                # Service Worker (Workbox via vite-plugin-pwa)
│       │
│       ├── pages/
│       │   ├── PublicDashboard.tsx   # Dashboard público (semáforo)
│       │   ├── TechDashboard.tsx     # Dashboard técnico (mapa + gráficos)
│       │   ├── Login.tsx
│       │   └── Admin.tsx
│       │
│       ├── components/
│       │   ├── ReservoirMap.tsx      # Leaflet com marcadores coloridos
│       │   ├── LevelChart.tsx        # Recharts série temporal
│       │   ├── AlertBadge.tsx        # Semáforo de status
│       │   ├── AlertSubscribeForm.tsx
│       │   └── SensorStatusPanel.tsx
│       │
│       ├── hooks/
│       │   ├── useWebSocket.ts       # Gerenciamento de conexão WS
│       │   ├── useReservoir.ts       # TanStack Query para dados do reservatório
│       │   └── usePushSubscription.ts # VAPID push subscription
│       │
│       ├── store/
│       │   └── auth.ts               # Zustand: JWT token, user info
│       │
│       └── api/
│           └── client.ts            # Axios instance com interceptor de JWT
│
├── nginx/
│   ├── nginx.conf                   # Configuração principal
│   └── conf.d/
│       └── piscinao.conf            # Virtual host: proxy /api, /ws, static files
│
└── scripts/
    ├── setup_timescaledb.sql        # Hypertables, compression, retention, agg views
    ├── seed_dev.sql                 # Dados de desenvolvimento (1 reservatório, 2 sensores)
    └── generate_vapid_keys.py      # Gera par de chaves VAPID para push notifications
```

---

## 8. Infraestrutura Docker

```yaml
# docker-compose.yml — versão simplificada para referência
services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_DB: piscinao_db
      POSTGRES_USER: piscinao
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/setup_timescaledb.sql:/docker-entrypoint-initdb.d/01_setup.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U piscinao -d piscinao_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--pass", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build: ./backend
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    environment:
      DATABASE_URL: postgresql+asyncpg://piscinao:${DB_PASSWORD}@postgres:5432/piscinao_db
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      INGESTAO_API_KEY: ${INGESTAO_API_KEY}
      VAPID_PRIVATE_KEY: ${VAPID_PRIVATE_KEY}
      VAPID_PUBLIC_KEY: ${VAPID_PUBLIC_KEY}
      SMTP_HOST: ${SMTP_HOST}
      SMTP_USER: ${SMTP_USER}
      SMTP_PASSWORD: ${SMTP_PASSWORD}
    restart: unless-stopped

  worker:
    build: ./backend
    command: python -m arq app.worker.tasks.WorkerSettings
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    environment:
      DATABASE_URL: postgresql+asyncpg://piscinao:${DB_PASSWORD}@postgres:5432/piscinao_db
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    restart: unless-stopped

  frontend:
    build: ./frontend
    depends_on:
      - backend

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - frontend_build:/usr/share/nginx/html:ro
      - certbot_certs:/etc/letsencrypt:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  frontend_build:
  certbot_certs:
```

**Configuração NGINX (trecho principal):**

```nginx
server {
    listen 443 ssl http2;
    server_name piscinao.example.com;

    # Headers de segurança OWASP
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; ..." always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting global
    limit_req zone=general burst=20 nodelay;

    # Static files React SPA
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;

    # Proxy API REST
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        limit_req zone=api burst=50 nodelay;
    }

    # Proxy WebSocket
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s;
    }
}
```

---

## 9. ADRs — Architecture Decision Records

### ADR-001 — Python + FastAPI como Stack Backend

**Status:** Aceita

**Contexto:** Necessidade de linguagem com ecossistema IoT/científico, suporte async nativo, e framework web produtivo para APIs REST + WebSocket.

**Decisão:** Python 3.12 + FastAPI 0.115

**Justificativa:**
- FastAPI gera documentação OpenAPI automaticamente
- Pydantic v2 oferece validação e serialização com performance de Rust
- Ecossistema Python: bibliotecas para análise de dados, integração com sensores, modelos climáticos
- Performance async equivalente a NodeJS para I/O bound workloads

**Consequências:** Time de desenvolvimento deve estar familiarizado com async/await em Python; tipagem estática com TypedDicts e Pydantic schemas é obrigatória.

---

### ADR-002 — TimescaleDB para Séries Temporais

**Status:** Aceita

**Contexto:** Sistema gera até 2 leituras/minuto por reservatório × N reservatórios. Ao longo de 1 ano, milhões de registros. Queries de dashboard precisam de agregações rápidas por período.

**Decisão:** PostgreSQL 16 + TimescaleDB 2.x com hypertables para `leitura_sensor` e `leitura_climatica`

**Justificativa:**
- PostgreSQL já utilizado para demais entidades relacionais — evita segundo banco de dados
- TimescaleDB é uma extensão, não um fork: zero lock-in
- Hypertables mantêm compatibilidade total com SQL padrão
- Continuous aggregates eliminam queries pesadas de agregação no dashboard

**Consequências:** Setup inicial requer execução de SQL para criar extensão e hypertables; equipe deve entender conceitos de chunks e continuous aggregates.

---

### ADR-003 — Redis para Cache, Pub/Sub e Fila de Tarefas

**Status:** Aceita

**Contexto:** Sistema precisa de: (1) cache para evitar queries repetitivas ao banco, (2) pub/sub para distribuir eventos de novas leituras aos WebSockets ativos, (3) fila de tarefas async para envio de notificações sem bloquear o fluxo de ingestão.

**Decisão:** Redis 7 como solução unificada para cache + pub/sub + broker ARQ

**Justificativa:**
- Redis resolve os três requisitos com um único serviço
- ARQ (async task queue) utiliza Redis nativamente e integra com asyncio sem overhead
- Redis pub/sub é o mecanismo natural para sincronizar eventos entre processos (backend ↔ worker)

**Consequências:** Redis é um Single Point of Failure para notificações; em produção, considerar Redis Sentinel ou Cluster para alta disponibilidade.

---

### ADR-004 — React + TypeScript + Vite como Stack Frontend

**Status:** Aceita

**Contexto:** SPA com dois dashboards distintos (técnico e público), gráficos em tempo real, mapa interativo e funcionalidade PWA/push.

**Decisão:** React 18 + TypeScript 5.x + Vite 6.x + shadcn/ui + TanStack Query + Recharts + Leaflet

**Justificativa:**
- React: ecossistema maduro, maior disponibilidade de componentes especializados (Recharts, Leaflet react-leaflet)
- TypeScript: type safety no contrato com a API (schemas Pydantic → OpenAPI → tipos TypeScript)
- Vite: build production em < 30s, HMR < 100ms em desenvolvimento
- vite-plugin-pwa: integração automática com Workbox para Service Worker e manifest

**Consequências:** Bundle splitting deve ser configurado para carregar o código do dashboard técnico apenas quando necessário; ícones PWA devem ser gerados em múltiplos tamanhos.

---

### ADR-005 — NGINX como Reverse Proxy

**Status:** Aceita

**Contexto:** Backend FastAPI não deve ser exposto diretamente à internet. Necessidade de SSL termination, WebSocket upgrade, rate limiting e serving de arquivos estáticos com eficiência.

**Decisão:** NGINX 1.27 como única entrada de tráfego externo

**Justificativa:**
- Serving de arquivos estáticos no NGINX é ~10x mais eficiente que via Python
- WebSocket upgrade nativo sem configuração complexa
- Headers de segurança OWASP centralizados em um único lugar
- Rate limiting por zona (general / api / ingestao) sem dependência de middleware Python
- Let's Encrypt/Certbot integrado facilmente via volume Docker

**Consequências:** Toda alteração de routing passa pela configuração NGINX; equipe deve versionar nginx.conf junto ao código da aplicação.

---

### ADR-006 — Web Push VAPID + Email como Canais de Notificação no MVP

**Status:** Aceita

**Contexto:** Sistema precisa notificar cidadãos de forma proativa. Canais candidatos: SMS, WhatsApp, Email, Push Notification.

**Decisão:** MVP suportará apenas **Web Push (VAPID)** e **Email (SMTP)**. SMS e WhatsApp ficam para versão futura via padrão adapter.

**Justificativa:**
- Web Push: zero custo de envio, funciona em qualquer browser moderno, não requer app instalado
- Email: canal universal, custo próximo a zero com SMTP, sem dependência de plataforma
- SMS/WhatsApp (Twilio): custo por mensagem, requer contratos e aprovação de templates
- Pattern de adapter garante que adicionar SMS no futuro requer apenas nova implementação de `adapters/sms.py`

**Consequências:** Alcance limitado a usuários que ativaram notificações no browser; emails podem ir para spam; necessidade de processo de double opt-in para conformidade.

---

## 10. Metodologia de Desenvolvimento

### 10.1 Abordagem Scrum Adaptada

O projeto adota uma **metodologia ágil simplificada** inspirada no Scrum, adaptada para equipe reduzida (projeto de TCC):

- **Sprints:** ciclos de 2 semanas
- **Artefatos:** Product Backlog (005 - Backlog Técnico), Sprint Backlog, Definition of Done
- **Cerimônias simplificadas:** Planning (início do sprint), Review/Retrospective (fim do sprint)
- **Rastreabilidade:** cada commit referencia um EPIC/TASK do backlog técnico

### 10.2 Cronograma Macro

| Fase | Período | Entregáveis |
|------|---------|-------------|
| **Fase 0 — Bootstrap** | Semanas 1-2 | Repositório, Docker Compose base, CI skeleton |
| **Fase 1 — Infra & DB** | Semanas 3-4 | TimescaleDB configurado, migrations, seeds |
| **Fase 2 — Backend Core** | Semanas 5-8 | Ingestão, processamento, alertas, auth |
| **Fase 3 — Frontend** | Semanas 9-12 | Dashboard público, técnico, PWA, push |
| **Fase 4 — Integração** | Semanas 13-14 | Testes E2E, ajustes, integração clima |
| **Fase 5 — Entrega** | Semanas 15-16 | Documentação final, apresentação, TCC |

### 10.3 Definition of Done

Uma tarefa é considerada **concluída** quando:

- [ ] Código implementado e sem erros de lint/type
- [ ] Testes unitários escritos (≥ 80% coverage nas regras de negócio)
- [ ] Testes de integração passando para endpoints novos
- [ ] Pull Request revisado (auto-revisão com checklist)
- [ ] Documentação de API atualizada (OpenAPI / inline docstrings)
- [ ] Docker Compose sobe sem erros após a mudança
- [ ] Item de backlog marcado como concluído no 005

---

## 11. Referências Bibliográficas

1. **DAEE-SP** — Departamento de Águas e Energia Elétrica do Estado de São Paulo. *Programa de Macrodrenagem da Bacia do Alto Tietê: Piscinões*. Disponível em: https://www.daee.sp.gov.br. Acesso em: mar. 2026.

2. **CEMADEN** — Centro Nacional de Monitoramento e Alertas de Desastres Naturais. *Relatório Anual de Monitoramento Hidrometeorológico 2023*. Ministério da Ciência, Tecnologia e Inovação, 2024.

3. **CGE-SP** — Centro de Gerenciamento de Emergências da Prefeitura de São Paulo. *Dados históricos de alagamentos e enchentes na RMSP: 2018–2023*. Disponível em: https://www.cgesp.org.br. Acesso em: mar. 2026.

4. **BERNHARDSEN, T.** *Geographic Information Systems: An Introduction*. 3. ed. New York: Wiley, 2002.

5. **EVANS, E.** *Domain-Driven Design: Tackling Complexity in the Heart of Software*. Boston: Addison-Wesley, 2003.

6. **FOWLER, M.** *Patterns of Enterprise Application Architecture*. Boston: Addison-Wesley, 2002.

7. **TIMESCALE, INC.** *TimescaleDB Documentation: Hypertables, Continuous Aggregates and Compression*. Disponível em: https://docs.timescale.com. Acesso em: abr. 2026.

8. **MOZILLA DEVELOPER NETWORK.** *Progressive Web Apps (PWA): Service Workers, Web Push and VAPID*. Disponível em: https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps. Acesso em: abr. 2026.

9. **OWASP FOUNDATION.** *OWASP Top 10 — 2021: The Ten Most Critical Web Application Security Risks*. Disponível em: https://owasp.org/Top10. Acesso em: abr. 2026.

10. **RAMÍREZ, S.** *FastAPI Documentation: Async SQL Databases, WebSockets and Security*. Disponível em: https://fastapi.tiangolo.com. Acesso em: abr. 2026.

11. **HUNT, A.; THOMAS, D.** *The Pragmatic Programmer: From Journeyman to Master*. 20th Anniversary Edition. Boston: Addison-Wesley, 2019.

12. **INPE/CPTEC** — Instituto Nacional de Pesquisas Espaciais. *Previsão Numérica de Tempo: API de Dados Climáticos*. Disponível em: https://www.cptec.inpe.br. Acesso em: abr. 2026.

---

*Documento gerado como parte do Projeto Integrador PJI510 — UNIVESP 2026/S1*

