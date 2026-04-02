# Plano: Sistema de Monitoramento de Piscinões com IoT

## TL;DR
Sistema IoT para monitoramento de reservatórios de detenção (piscinões) com sensores de nível d'água e pluviometria, dashboard técnico e público, e sistema de alertas multicanal (web, push, SMS, WhatsApp, email) para mitigação de risco de enchentes na zona leste de São Paulo. Stack: Python/FastAPI + React/TypeScript + PostgreSQL/TimescaleDB, rodando em Docker com NGINX no Ubuntu 24.04 LTS. Contexto acadêmico TCC — documentação técnica com referências bibliográficas.

---

## Decisões Alinhadas com o Usuário
- Substituir docs 001-005 existentes (São apenas Modelos - eram de outro projeto — SINDIFLOW)
- Dashboard duplo: técnico (gestores/Defesa Civil) + público (população)
- Alertas: Dashboard web, Push (PWA), SMS, WhatsApp, Email
- Backend: Python (FastAPI) — ideal para processamento IoT e cálculos científicos
- Banco: PostgreSQL + TimescaleDB (séries temporais dos sensores)
- MVP com 1 piscinão, arquitetura extensível para múltiplos

---

## Fase 1 — Documentação Arquitetural (Foco Atual)

### Step 1: Criar doc `001 - Plano de Desenvolvimento.md`
Substituir o conteúdo atual. Incluir:
- Visão geral do projeto e problema
- Objetivo (acadêmico TCC + impacto social)
- Escopo do MVP e fases futuras
- Cronograma macro de alto nível
- Referências bibliográficas

**Arquivo:** `e:\Projetos\PJI510-2026S1-Turma001\Docs\001 - Plano de desenvolvimento.md`

### Step 2: Criar doc `002 - Software Requirements Specification - SRS.md`
Substituir o conteúdo atual. Incluir:
- Requisitos Funcionais (RF01-RFnn)
- Requisitos Não-Funcionais (RNF01-RNFnn)
- Personas: Gestor/Defesa Civil, Cidadão, Administrador do Sistema
- User Stories estruturadas (formato INVEST)
- Critérios de aceite
- Regras de negócio (cálculos de volume, vazão, thresholds de alerta)
- Glossário ubíquo do domínio

**Arquivo:** `e:\Projetos\PJI510-2026S1-Turma001\Docs\002 - Software Requirements Specification - SRS.md`

### Step 3: Criar doc `003 - Pesquisa e Desenvolvimento - PRD.md`
Substituir o conteúdo atual. Incluir:
- Revisão bibliográfica e estado da arte
- Análise de soluções similares (AlertaRio, CEMADEN, etc.)
- Fundamentação teórica: IoT, MQTT, séries temporais, modelos hidrológicos simplificados
- Justificativa das escolhas tecnológicas com referências
- Metodologia de desenvolvimento

**Arquivo:** `e:\Projetos\PJI510-2026S1-Turma001\Docs\003 - Pesquisa e Desenvolvimento - PRD.md`

### Step 4: Criar doc `004 - DevSpecs.md` (Especificação Técnica + Arquitetura)
Substituir o conteúdo atual. Incluir:

#### 4.1 Arquitetura do Sistema (Diagramas C4)
- **Nível 1 — Contexto:** Sistema, Sensores IoT, API Climática, Usuários (Gestor, Cidadão)
- **Nível 2 — Containers:** NGINX, Frontend (React), Backend (FastAPI), PostgreSQL/TimescaleDB, Redis (cache), Worker de Alertas
- **Nível 3 — Componentes:** Módulos do backend (Ingestão, Processamento, Alertas, Dashboard)

#### 4.2 Stack Tecnológico com Justificativas

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| **Frontend** | React 18 + TypeScript + Tailwind CSS + Vite | Tipagem estática, componentização, responsividade, PWA |
| **Backend** | Python 3.12 + FastAPI + Pydantic v2 | Async nativo, validação de schemas IoT, libs científicas (numpy, pandas) |
| **Banco de Dados** | PostgreSQL 16 + TimescaleDB 2.x | Dados relacionais + hypertables para séries temporais, compressão automática |
| **Cache** | Redis 7 | Cache de último estado dos sensores, pub/sub para real-time |
| **Web Server** | NGINX 1.27 | Reverse proxy, SSL termination, rate limiting, serving static files |
| **Real-time** | WebSocket (FastAPI) + SSE | Dashboard atualizado em tempo real |
| **Containerização** | Docker + Docker Compose | Isolamento, reprodutibilidade, deploy simplificado |
| **SO** | Ubuntu 24.04 LTS | Estabilidade, LTS, comunidade ampla |
| **Gráficos** | Chart.js ou Recharts | Visualização de séries temporais no dashboard |
| **PWA** | Service Worker + Web Push API | Push notifications no navegador sem app nativo |
| **API Climática** | CPTEC/INPE + OpenWeatherMap | Dados meteorológicos para correlação com pluviometria local |

#### 4.3 Modelagem de Dados

**Entidades Principais:**
- `reservatorio` — cadastro de piscinões (id, nome, localização, capacidade_m3, cota_transbordo_m, cota_alerta_m)
- `sensor` — cadastro de sensores (id, reservatorio_id, tipo [nivel|pluviometro|meteorologico], posicao, status)
- `leitura_sensor` — hypertable TimescaleDB (timestamp, sensor_id, valor, unidade) — particionada por tempo
- `leitura_climatica` — dados da API pública (timestamp, reservatorio_id, temperatura, umidade, previsao_chuva_mm)
- `alerta` — registros de alertas disparados (id, reservatorio_id, tipo [amarelo|laranja|vermelho], mensagem, timestamp, canais_notificados)
- `configuracao_alerta` — thresholds configuráveis por reservatório
- `usuario` — gestores e administradores do sistema
- `inscricao_alerta` — cidadãos inscritos para receber alertas (canal, contato, reservatorio_id)

#### 4.4 Regras de Negócio Críticas

- **RN-01:** Cálculo de volume baseado na geometria do piscinão e nível d'água medido
- **RN-02:** Taxa de variação do nível (delta nível / delta tempo) — indica velocidade de enchimento
- **RN-03:** Estimativa de tempo para transbordo: (cota_transbordo - nivel_atual) / taxa_variacao
- **RN-04:** Níveis de alerta:
  - 🟡 Amarelo: nível > 60% da capacidade OU taxa de variação > X cm/min
  - 🟠 Laranja: nível > 80% OU tempo estimado para transbordo < 2h
  - 🔴 Vermelho: nível > 90% OU tempo estimado para transbordo < 30min
- **RN-05:** Correlação pluviometria × nível — se chuva > threshold E nível subindo, antecipar alerta
- **RN-06:** Redundância de sensores: 2 sensores de nível, usar média; se divergência > 10%, sinalizar falha

#### 4.5 Endpoints da API (Visão Macro)

**Ingestão (interno):**
- `POST /api/v1/ingestao/leituras` — recebe batch de leituras do gateway MQTT (endpoint que abstrai a fila)

**Dashboard Técnico:**
- `GET /api/v1/reservatorios/{id}/status` — status atual (nível, volume, alertas ativos)
- `GET /api/v1/reservatorios/{id}/historico` — série temporal de leituras
- `GET /api/v1/reservatorios/{id}/alertas` — histórico de alertas
- `GET /api/v1/dashboard/overview` — visão geral de todos os reservatórios

**Dashboard Público:**
- `GET /api/v1/publico/status` — status simplificado (semáforo: normal/atenção/alerta/emergência)

**Alertas:**
- `POST /api/v1/alertas/inscricao` — cidadão se inscreve para receber alertas
- `DELETE /api/v1/alertas/inscricao/{id}` — cancelar inscrição

**WebSocket:**
- `WS /ws/dashboard/{reservatorio_id}` — atualizações em tempo real

#### 4.6 Diagrama de Fluxo de Dados

```
Sensores (nível × 2 + pluvio) → Gateway LoRa/WiFi → Broker MQTT
                                                           ↓
                                                    [Abstração: Endpoint]
                                                           ↓
                                              POST /api/v1/ingestao/leituras
                                                           ↓
                                               ┌─── FastAPI Backend ───┐
                                               │  Validação Pydantic   │
                                               │  Persistência TimescaleDB │
                                               │  Motor de Regras      │
                                               │  Cálculo de Volume    │
                                               │  Estimativa Transbordo│
                                               └───────┬───────────────┘
                                                       ↓
                                          ┌──── Se threshold atingido ────┐
                                          │  Disparar Alertas             │
                                          │  Push / SMS / WhatsApp / Email│
                                          └───────────────────────────────┘
                                                       ↓
                                               Dashboard (WebSocket)
                                          ┌──── Técnico (gestores) ────┐
                                          │  Gráficos tempo real       │
                                          │  Histórico completo        │
                                          │  Configuração de alertas   │
                                          └────────────────────────────┘
                                          ┌──── Público (cidadão) ─────┐
                                          │  Semáforo de risco         │
                                          │  Último nível              │
                                          │  Botão inscrever alertas   │
                                          └────────────────────────────┘
```

#### 4.7 Infraestrutura Docker

```yaml
# docker-compose.yml (visão macro)
services:
  nginx:       # Reverse proxy, SSL, static files
  frontend:    # React app (build estático servido pelo NGINX)
  backend:     # FastAPI (uvicorn, 2+ workers)
  postgres:    # PostgreSQL 16 + TimescaleDB
  redis:       # Cache + pub/sub
  worker:      # Celery ou ARQ — processamento assíncrono de alertas
```

### Step 5: Criar doc `005 - Backlog Tecnico.md`
Substituir o conteúdo atual. Incluir:
- Épicos organizados por fase
- Tasks com prioridade RICE
- Dependências entre tarefas

**Épicos principais:**
- EPIC-01: Setup de infraestrutura (Docker, NGINX, PostgreSQL, Redis)
- EPIC-02: Modelagem e migrations do banco de dados
- EPIC-03: API de ingestão de dados de sensores
- EPIC-04: Motor de processamento e regras de negócio
- EPIC-05: Dashboard técnico (frontend)
- EPIC-06: Dashboard público
- EPIC-07: Sistema de alertas multicanal
- EPIC-08: Integração com API climática
- EPIC-09: PWA e push notifications
- EPIC-10: Testes e validação

---

## Fase 2 — Implementação (Futuro, fora do escopo atual)
Será executada após aprovação da documentação.

---

## Referências Bibliográficas Sugeridas

### Fundamentação Teórica
1. **CEMADEN** — Centro Nacional de Monitoramento e Alertas de Desastres Naturais. Disponível em: https://www.gov.br/cemaden/
2. **DAEE-SP** — Departamento de Águas e Energia Elétrica. Plano Diretor de Macrodrenagem da Bacia do Alto Tietê.
3. **TUCCI, C. E. M.** Hidrologia: Ciência e Aplicação. 4ª ed. ABRH/UFRGS, 2009.
4. **CANHOLI, A. P.** Drenagem Urbana e Controle de Enchentes. 2ª ed. Oficina de Textos, 2014.
5. **AlertaRio** — Sistema de Alerta de Chuvas Intensas da Prefeitura do Rio de Janeiro.

### IoT e MQTT
6. **ATZORI, L.; IERA, A.; MORABITO, G.** The Internet of Things: A survey. Computer Networks, v. 54, n. 15, p. 2787-2805, 2010.
7. **OASIS Standard.** MQTT Version 5.0. 2019. Disponível em: https://mqtt.org/
8. **GUBBI, J. et al.** Internet of Things (IoT): A vision, architectural elements, and future directions. Future Generation Computer Systems, v. 29, n. 7, 2013.

### Stack Tecnológico
9. **FASTAPI.** FastAPI Documentation. Disponível em: https://fastapi.tiangolo.com/
10. **TIMESCALEDB.** Time-series data simplified. Disponível em: https://www.timescale.com/
11. **REACT.** React Documentation. Disponível em: https://react.dev/
12. **DOCKER.** Docker Documentation. Disponível em: https://docs.docker.com/

### Séries Temporais e Monitoramento
13. **FREEDMAN, D. A.** Statistical Models: Theory and Practice. Cambridge University Press, 2009.
14. **ENDSLEY, M. R.** Designing for Situation Awareness. CRC Press, 2011.

### Normas
15. **ABNT NBR ISO/IEC 27001:2022** — Segurança da informação
16. **ABNT NBR ISO 22320:2020** — Gestão de emergências

---

## Arquivos a Serem Modificados

| Arquivo | Ação |
|---------|------|
| `Docs/001 - Plano de desenvolvimento.md` | Reescrever completo |
| `Docs/002 - Software Requirements Specification - SRS.md` | Reescrever completo |
| `Docs/003 - Pesquisa e Desenvolvimento - PRD.md` | Reescrever completo |
| `Docs/004 - DevSpecs.md` | Reescrever completo |
| `Docs/005 - Backlog Tecnico.md` | Reescrever completo |
| `README.md` | Atualizar com resumo da nova documentação |

---

## Verificação
1. Cada documento deve ser internamente consistente (mesmos termos, mesmas tecnologias)
2. Diagramas C4 devem cobrir os 3 níveis (Contexto, Container, Componente)
3. Todos os endpoints listados em DevSpecs devem ter User Story correspondente na SRS
4. Regras de negócio (RN) devem estar catalogadas e referenciadas nos requisitos funcionais
5. Referências bibliográficas devem ser verificáveis
6. Stack tecnológico deve ser consistente em todos os documentos
7. Glossário ubíquo deve cobrir todos os termos do domínio

---

## Considerações Adicionais
1. **Modelo hidrológico simplificado:** Para o TCC, o cálculo de estimativa de transbordo pode usar modelo linear simplificado (nível × área da seção → volume; delta_volume/delta_t → vazão de entrada). Modelos mais complexos (Manning, Saint-Venant) podem ser mencionados como trabalho futuro.
2. **Segurança do endpoint de ingestão:** Mesmo abstraindo o MQTT, o endpoint `POST /ingestao/leituras` precisa de autenticação (API key) para evitar dados injetados maliciosamente.
3. **Escalabilidade futura:** Arquitetura projetada para 1 piscinão no MVP, mas com `reservatorio_id` em todas as entidades, facilitando expansão para múltiplos sites.
