---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: 'Segoe UI', sans-serif;
    font-size: 1.1rem;
  }
  h1 { color: #1e40af; }
  h2 { color: #1d4ed8; border-bottom: 2px solid #93c5fd; padding-bottom: 0.2em; }
  h3 { color: #2563eb; }
  .highlight { background: #eff6ff; padding: 0.5em; border-left: 4px solid #3b82f6; }
  table { font-size: 0.9rem; }
---

<!-- SLIDE 1 — CAPA -->
# Sistema de Monitoramento de Piscinões com IoT

**PiscinãoMonitor**

---

**Projeto Integrador em Engenharia da Computação — PJI510**  
UNIVESP — Universidade Virtual do Estado de São Paulo  
2026/S1 — Turma 001

> *Monitoramento em tempo real de reservatórios de detenção para prevenção de enchentes urbanas na RMSP*

---

<!-- SLIDE 2 — O PROBLEMA (contexto) -->
## 1. O Problema: Enchentes na RMSP

### Impacto Social e Econômico

- A RMSP registra **mais de 350 pontos de alagamento** recorrentes
- Enchentes custam em média **R$ 2,5 bilhões/ano** em danos diretos à região
- Moradores da zona leste são desproporcionalmente afetados
- Alertas existentes dependem de monitoramento **manual e reativo**

### Piscinões: Solução de Infraestrutura Subutilizada

- O DAEE-SP opera **~40 piscinões** com capacidade de **>60 milhões m³**
- Cada piscinão possui **capacidade finita** — o transbordo é previsível
- Janela de ação antes do transbordo: **30–90 minutos** (raramente aproveitada)
- Ausência de sistema integrado de monitoramento e alerta à população

---

<!-- SLIDE 3 — O PROBLEMA (visual) -->
## 1. O Problema: Monitoramento Manual vs. Proativo

| Situação atual | Com PiscinãoMonitor |
|---------------|---------------------|
| Operador realiza vistorias físicas | Sensores coletam dados a cada minuto |
| Alerta por telefone / rádio | Push notification + e-mail automático |
| Sem histórico estruturado | Série temporal comprimida por 1 ano |
| Sem correlação com chuva prevista | Dados climáticos CPTEC + OpenWeather |
| Público sem acesso às informações | Dashboard público aberto, sem login |

> **Pergunta norteadora:** *Como a IoT pode aumentar o tempo de resposta antes de uma enchente, reduzindo danos à população?*

---

<!-- SLIDE 4 — SOLUÇÃO PROPOSTA -->
## 2. Solução Proposta

### PiscinãoMonitor — Plataforma de Monitoramento em Tempo Real

Três pilares:

1. **Ingestão IoT** — Sensores de nível d'água e pluviômetros enviam leituras via REST; integração com API climática CPTEC/INPE (+ fallback OpenWeatherMap)

2. **Motor de Regras** — 6 regras de negócio (RN-01 a RN-06) calculam volume, taxa de variação, estimativa de transbordo e disparam alertas hierárquicos (atenção / alerta / emergência)

3. **Comunicação** — Dashboard público (cidadão), Dashboard técnico (gestor DAEE), Push Notifications (PWA), e-mail — tudo em tempo real via WebSocket

---

<!-- SLIDE 5 — ARQUITETURA (diagrama textual) -->
## 3. Arquitetura do Sistema

```
Sensores IoT ──► REST/HTTPS ──► NGINX 1.27 (reverse proxy)
                                      │
                        ┌─────────────┼─────────────────┐
                        │             │                  │
                  FastAPI 0.115  WebSocket          Static SPA
                  (Python 3.12)   /ws/*           (React 18 + Vite)
                        │
          ┌─────────────┼─────────────┐
          │             │             │
       Alembic     ARQ Worker     Redis 7
       Migrations  (cron 30min)  (cache + queue)
          │
  PostgreSQL 16 + TimescaleDB 2.x
  ├── leitura_sensor (hypertable)
  ├── leitura_climatica (hypertable)
  └── continuous aggregates + compressão
```

**Implantação:** Docker Compose — 6 containers com healthchecks

---

<!-- SLIDE 6 — STACK TECNOLÓGICO -->
## 3. Stack Tecnológico

| Camada | Tecnologia | Versão | Decisão Chave |
|--------|-----------|--------|---------------|
| Backend | FastAPI + Python | 0.115 + 3.12 | Performance async, tipagem, OpenAPI grátis |
| ORM | SQLAlchemy Async + asyncpg | 2.0 | Zero bloqueio I/O com TimescaleDB |
| Séries Temporais | PostgreSQL + TimescaleDB | 16 + 2.x | Hypertables, aggregates, compressão automática |
| Cache/Filas | Redis + ARQ | 7 + 0.26 | Pub/Sub para alertas + cron jobs |
| Frontend | React + TypeScript + Vite | 18 + 5.x + 6.x | SPA tipada, build otimizado |
| UI | Tailwind CSS v4 + shadcn/ui | 4.x | Design system acessível |
| Real-time | WebSocket nativo FastAPI | — | Sem dependência extra |
| PWA | vite-plugin-pwa + Workbox | — | Instalável + offline + push |
| Infra | Docker + NGINX | Compose V2 + 1.27 | Reproduzível, OWASP headers |

---

<!-- SLIDE 7 — FUNCIONALIDADES PRINCIPAIS -->
## 4. Funcionalidades Implementadas

### Backend (14 módulos completos)

- **Auth:** JWT access (30min) + refresh (7d) + RBAC (admin/gestor/operador)
- **Ingestão:** `POST /api/v1/ingestao/leituras` — batch 1–100, API Key, validação Pydantic v2
- **Processamento:** RN-01 (volume %) → RN-06 (alerta emergência), subscriber Redis pub/sub
- **Alertas:** CRUD com filtros, reconhecimento por gestor, deduplicação
- **Clima:** CPTEC/INPE primário + OpenWeatherMap fallback, retry com backoff exponencial, cron 30min
- **Dashboard:** endpoints de tendência, histórico, mapa, status sensores

### Frontend (20+ componentes TypeScript)

- Dashboard público (semáforo de risco, mapa Leaflet, gráfico Recharts)
- Dashboard técnico (SensorStatusPanel, AlertsTable, LevelChart)
- PWA: Service Worker + cache offline + push subscription

---

<!-- SLIDE 8 — MOTOR DE REGRAS -->
## 4. Motor de Regras — RN-01 a RN-06

| Regra | Descrição | Saída |
|-------|-----------|-------|
| **RN-01** | Calcular volume ocupado (%) | `volume_pct ∈ [0, 100]` |
| **RN-02** | Calcular taxa de variação do nível | `delta cm/h` |
| **RN-03** | Estimar tempo até transbordo | `eta_transbordo_min` |
| **RN-04** | Disparo de alerta — Atenção | volume ≥ 70% OU taxa > 5 cm/h |
| **RN-05** | Disparo de alerta — Alerta | volume ≥ 85% OU ETA < 60 min |
| **RN-06** | Disparo de alerta — Emergência | volume ≥ 95% OU ETA < 20 min |

> Testado com **30 casos unitários** (pytest). Deduplicação evita alertas duplicados para o mesmo estado.

---

<!-- SLIDE 9 — BANCO DE DADOS -->
## 4. Banco de Dados — TimescaleDB

### Por que TimescaleDB?

- Extensão PostgreSQL — SQL padrão, sem curva de aprendizado nova
- **Hypertables** particionam automaticamente por tempo (chunks de 7 dias)
- **Continuous aggregates** pré-computam médias/máx/mín por hora
- **Compressão** automática de dados > 7 dias (~90% de redução de espaço)
- **Retenção** configurável — 1 ano, descarta automaticamente

```sql
-- Leitura com aggregate (exemplo de query eficiente)
SELECT time_bucket('1 hour', timestamp) AS hora,
       avg(valor) AS nivel_medio,
       max(valor) AS nivel_maximo
FROM leitura_sensor_1h_agg   -- continuous aggregate
WHERE sensor_id = $1
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY hora DESC;
```

---

<!-- SLIDE 10 — PWA e NOTIFICAÇÕES -->
## 4. PWA — Progressive Web App

### Experiência do Usuário

- **Instalável** como app nativo (Android, iOS, Desktop) via `manifest.json`
- **Offline:** Service Worker (Workbox) faz cache dos assets e dados recentes
- **Push Notifications:** VAPID/Web Push API — alerta chega mesmo com app fechado
- **Offline Banner:** aviso visual quando conexão é perdida

### Fluxo de notificação push

```
Motor de Regras → alerta_criado → Redis Pub/Sub
       → ARQ Worker (enviar_push_notifications)
       → pywebpush (VAPID) → Browser Push Service
       → Dispositivo do cidadão
```

> Testado em Chrome 124 (Android), Firefox 125 (Desktop), Safari 17 (iOS 17.4+)

---

<!-- SLIDE 11 — TESTES -->
## 5. Qualidade e Testes

### Cobertura de Testes

| Tipo | Arquivo | Casos | Framework |
|------|---------|-------|-----------|
| Unitários | `test_processamento_policies.py` | 30 | pytest |
| Integração | `test_ingestao.py` | 8 | pytest + httpx.AsyncClient |
| Integração | `test_alertas.py` | 8 | pytest + httpx.AsyncClient |
| Manual/QA | `QA_CHECKLIST.md` | 35 | Checklist manual |

**Total: 81 casos de teste**

### Estratégias

- SAVEPOINT rollback por teste (sem contaminação entre casos)
- Banco de teste isolado (PostgreSQL em Docker)
- Fixtures de seed: reservatório, sensor, gestor, operador
- API Key lida de `Settings.INGESTAO_API_KEY` (sem hardcode)

---

<!-- SLIDE 12 — SEGURANÇA -->
## 5. Segurança — OWASP Top 10

| Risco OWASP | Mitigação implementada |
|-------------|----------------------|
| Broken Access Control | RBAC com 3 níveis (admin/gestor/operador); `require_role()` decorator |
| Cryptographic Failures | bcrypt rounds=12; JWT HS256; HTTPS via NGINX |
| Injection | Pydantic v2 valida todos os inputs; SQLAlchemy ORM (sem SQL cru) |
| Insecure Design | API Key obrigatória para ingestão IoT; sem chave → 401 |
| Security Misconfiguration | NGINX: `X-Content-Type-Options`, `X-Frame-Options`, `HSTS`, `CSP` |
| Rate Limiting | NGINX `limit_req_zone` — 10 req/s por IP na API |
| Sensitive Data Exposure | `SECRET_KEY`, senhas, VAPID nunca no código — apenas `.env` |

---

<!-- SLIDE 13 — DEMONSTRAÇÃO -->
## 6. Demonstração ao Vivo

### Roteiro (10 minutos)

1. `docker compose up -d` → mostrar containers `healthy`
2. **Dashboard Público** (`http://localhost`) — semáforo de risco, mapa, temperatura
3. **Dashboard Técnico** (`/dashboard`) — login como gestor, LevelChart, AlertsTable
4. **Simulação de alerta** — POST leitura com nível 95% via `curl`
5. **Alerta gerado** — badge na tabela, status "ativo", notificação push
6. **Reconhecer alerta** — PATCH `/alertas/{id}/reconhecer`, status → "resolvido"
7. **Modo Offline** — desabilitar rede, verificar OfflineBanner e cache PWA

### Dados de acesso para demonstração

```
Admin:   admin@piscinao.local   / Admin@2026!
Gestor:  gestor@piscinao.local  / Gestor@2026!
API Key: (variável INGESTAO_API_KEY do .env)
```

---

<!-- SLIDE 14 — RESULTADOS E MÉTRICAS -->
## 7. Resultados e Métricas

### Artefatos Entregues

| Fase | Épicos | Artefatos | Linhas de código |
|------|--------|-----------|-----------------|
| Infraestrutura | EPIC-00 + 01 | 12 arquivos Docker/NGINX | ~800 |
| Backend | EPIC-02 a 07, 11 | 40+ módulos Python | ~4.500 |
| Frontend | EPIC-08 a 10 | 25+ componentes React/TS | ~3.200 |
| Testes | EPIC-12 | 4 arquivos, 81 casos | ~600 |
| Documentação | EPIC-13 | README + Docs + Slides | ~1.200 |

### Objetivos Alcançados

- ✅ OE1: Arquitetura IoT multi-sensor projetada e implementada
- ✅ OE2: Pipeline de ingestão validado (batch, API Key, séries temporais)
- ✅ OE3: Motor de regras com 6 RNs e 30 testes unitários
- ✅ OE4: Dois dashboards funcionais + WebSocket em tempo real + PWA
- ✅ OE5: Alertas multicanal: Push + Email + WebSocket
- ✅ OE6: Testes de integração + QA manual + documentação completa

---

<!-- SLIDE 15 — DIFICULDADES E APRENDIZADOS -->
## 8. Dificuldades e Aprendizados

### Desafios Técnicos

| Desafio | Solução adotada |
|---------|----------------|
| TimescaleDB: hypertables exigem cuidado em Alembic | Migrations separadas (0001 tabelas → 0002 hypertables) |
| SQLAlchemy Async + pytest: isolamento de transações | SAVEPOINT (`begin_nested`) por teste — sem rollback incompleto |
| NGINX + WebSocket upstream | Configuração explícita de `Upgrade` e `Connection` headers |
| VAPID/Web Push em ambiente local | `localhost` requer flag `--ignore-certificate-errors` |
| CPTEC/INPE XML instável | Fallback automático para OpenWeatherMap com retry + backoff |

### Aprendizados

- **TimescaleDB** é altamente eficiente para séries temporais, mas requer ordem específica nas migrations
- **ARQ** (Python Redis Queue) é simples e suficiente para workloads moderados — sem overhead do Celery
- **Pydantic v2** com `model_config` quebra código Pydantic v1 — migração exige atenção
- **pytest-asyncio** com `asyncio_mode="auto"` elimina boilerplate em projetos async

---

<!-- SLIDE 16 — TRABALHOS FUTUROS -->
## 8. Trabalhos Futuros e Limitações

### Limitações do MVP

- Sensores IoT físicos não foram instalados — dados de teste gerados sinteticamente
- Modelo hidrológico simplificado (linear) — não implementa Manning/Saint-Venant
- Sem redundância geográfica (multi-região)
- SMTP não testado em produção real

### Evolução Proposta

| Prioridade | Melhoria |
|-----------|----------|
| Alta | Integração MQTT real (HiveMQ/Mosquitto) com gateway LoRaWAN |
| Alta | Modelo hidrológico com equações de Manning para canais |
| Média | Notificações WhatsApp (Twilio) e SMS |
| Média | App mobile React Native (reutilizando componentes) |
| Baixa | Escalabilidade multi-piscinão com Kubernetes |
| Baixa | Machine Learning para previsão de transbordo |

---

<!-- SLIDE 17 — REFERÊNCIAS -->
## Referências Principais

CANHOLI, A. P. **Drenagem urbana e controle de enchentes**. 2. ed. São Paulo: Oficina de Textos, 2014.

TUCCI, C. E. M. **Hidrologia: ciência e aplicação**. 4. ed. Porto Alegre: ABRH/UFRGS, 2009.

RAMÍREZ, S. **FastAPI Documentation**. Disponível em: https://fastapi.tiangolo.com/. Acesso em: 01 mai. 2026.

TIMESCALE, Inc. **TimescaleDB Documentation**. Disponível em: https://docs.timescale.com/. Acesso em: 01 mai. 2026.

OASIS Standard. **MQTT Version 5.0**. 2019. Disponível em: https://mqtt.org/. Acesso em: 01 mai. 2026.

SCHWABER, K.; SUTHERLAND, J. **The Scrum Guide**. 2020. Disponível em: https://scrumguides.org/. Acesso em: 01 mai. 2026.

---

<!-- SLIDE 18 — ENCERRAMENTO -->
## Obrigado!

### PiscinãoMonitor

> *Monitoramento inteligente de piscinões para prevenção de enchentes urbanas*

---

**Repositório:** `github.com/<org>/PJI510-2026S1-Turma001`  
**Demo:** `docker compose up -d` → `http://localhost`  
**Documentação:** `Docs/README.md` + Swagger UI em `/api/v1/docs`

---

PJI510 — Projeto Integrador em Engenharia da Computação  
UNIVESP 2026/S1 — Turma 001  

*Perguntas?*
