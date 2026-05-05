# Sistema de Monitoramento de Piscinões (Pôlders) com IoT

## Plano de Desenvolvimento

**Projeto:** PJI510 — Projeto Integrador em Engenharia da Computação  
**Instituição:** UNIVESP — Universidade Virtual do Estado de São Paulo  
**Versão:** 1.1  
**Data:** 05/05/2026  
**Status:** Concluído ✅  

---

## Sumário

1. [Introdução](#1-introdução)
2. [Contextualização e Problema](#2-contextualização-e-problema)
3. [Objetivos](#3-objetivos)
4. [Escopo e Delimitação](#4-escopo-e-delimitação)
5. [Funcionalidades do Sistema](#5-funcionalidades-do-sistema)
6. [Stack Tecnológico](#6-stack-tecnológico)
7. [Metodologia de Desenvolvimento](#7-metodologia-de-desenvolvimento)
8. [Cronograma Macro](#8-cronograma-macro)
9. [Riscos e Mitigações](#9-riscos-e-mitigações)
10. [Referências Bibliográficas](#10-referências-bibliográficas)

---

## 1. Introdução

Este documento descreve o plano de desenvolvimento do **Sistema de Monitoramento de Reservatórios de Detenção (Piscinões/Pôlders) utilizando Internet das Coisas (IoT)**, proposto como Trabalho de Conclusão de Curso (TCC) no âmbito do Projeto Integrador em Engenharia da Computação.

O sistema propõe a utilização de sensores IoT para monitoramento em tempo real do nível de água em piscinões, combinado com dados pluviométricos e informações de APIs climáticas públicas, para gerar alertas proativos à população sobre riscos de enchentes e transbordamento.

---

## 2. Contextualização e Problema

### 2.1 Alagamentos Urbanos no Brasil

Os alagamentos urbanos representam um dos principais desastres naturais recorrentes no Brasil, especialmente nas regiões metropolitanas. Segundo dados do Centro Nacional de Monitoramento e Alertas de Desastres Naturais (CEMADEN), eventos hidrometeorológicos extremos têm se intensificado nas últimas décadas devido à urbanização desordenada, impermeabilização do solo e mudanças climáticas (TUCCI, 2009).

A Região Metropolitana de São Paulo (RMSP), com sua extensa área urbanizada e topografia de planície aluvial do Rio Tietê, é particularmente vulnerável a inundações. O Departamento de Águas e Energia Elétrica de São Paulo (DAEE-SP) mantém um sistema de macrodrenagem que inclui dezenas de reservatórios de detenção — popularmente conhecidos como "piscinões" — projetados para reter temporariamente o excesso de água pluvial e reduzir os picos de vazão nos córregos e rios (CANHOLI, 2014).

### 2.2 Papel dos Piscinões na Drenagem Urbana

Os piscinões (ou pôlders) são estruturas hidráulicas de detenção que funcionam como amortecedores de cheias urbanas. Seu princípio de funcionamento baseia-se na retenção temporária do volume de água excedente durante eventos de chuva intensa, liberando-o gradualmente após o pico do evento (CANHOLI, 2014).

**Características operacionais relevantes:**

- **Capacidade volumétrica finita**: cada piscinão possui um volume máximo de armazenamento (cota de transbordo)
- **Vazão de entrada variável**: dependente da intensidade pluviométrica e da área de drenagem a montante
- **Vazão de saída controlada**: por orifícios de descarga dimensionados no projeto hidráulico
- **Risco de transbordo**: quando a taxa de entrada supera a capacidade de amortecimento, gerando risco à população do entorno

### 2.3 Problema Identificado

Atualmente, o monitoramento dos piscinões na maioria dos municípios brasileiros é feito de forma **manual e reativa** — operadores realizam vistorias presenciais ou dependem de relatos da população. Essa abordagem apresenta limitações críticas:

1. **Latência na detecção**: o nível de água pode subir rapidamente durante chuvas intensas, e a janela de tempo para evacuação pode ser curta
2. **Ausência de dados históricos estruturados**: sem séries temporais, não é possível prever comportamentos ou ajustar thresholds de alerta
3. **Comunicação deficiente com a população**: moradores do entorno frequentemente não têm acesso a informações em tempo real sobre o estado do reservatório
4. **Falta de correlação de dados**: dados pluviométricos, nível de água e previsões climáticas raramente são cruzados para antecipar cenários de risco

### 2.4 Justificativa

A convergência de três fatores tecnológicos torna o momento propício para abordar este problema:

1. **Maturidade da IoT**: sensores de nível ultrassônico e pluviômetros eletrônicos são acessíveis e confiáveis, com protocolos de comunicação padronizados como MQTT (ATZORI; IERA; MORABITO, 2010)
2. **Infraestrutura de software aberta**: frameworks modernos permitem construir sistemas de ingestão, processamento e visualização de dados em tempo real com custo reduzido
3. **Demanda social**: a população atingida por enchentes necessita de ferramentas de conscientização e alerta que operem de forma proativa e autônoma

---

## 3. Objetivos

### 3.1 Objetivo Geral

Desenvolver um sistema de monitoramento baseado em IoT para reservatórios de detenção (piscinões), capaz de coletar dados de sensores em tempo real, processá-los e gerar alertas proativos à população sobre riscos de enchentes e transbordamento.

### 3.2 Objetivos Específicos

1. **Projetar a arquitetura** de um sistema IoT para monitoramento de piscinões, integrando sensores de nível d'água, pluviômetro e APIs climáticas públicas em uma plataforma web unificada
2. **Implementar um pipeline de ingestão** de dados de sensores via protocolo MQTT (abstraído por endpoint REST), com validação, persistência em banco de dados de séries temporais e processamento em tempo real
3. **Desenvolver um motor de regras** para cálculo de volume, taxa de variação do nível, estimativa de tempo para transbordo e disparo automático de alertas hierárquicos (amarelo, laranja, vermelho)
4. **Construir dois dashboards** — um técnico (para gestores e Defesa Civil) e um público (para a população) — com atualização em tempo real via WebSocket e capacidade de funcionamento offline como Progressive Web App (PWA)
5. **Implementar um sistema de alertas multicanal** (notificações push, email, SMS, WhatsApp) com inscrição voluntária de cidadãos por região/reservatório
6. **Documentar e validar** o sistema proposto, apresentando testes de integração e análise de viabilidade técnica

---

## 4. Escopo e Delimitação

### 4.1 Escopo do MVP (Minimum Viable Product)

O MVP contempla o monitoramento de **1 (um) piscinão** com a seguinte instrumentação:

| Fonte de Dados | Quantidade | Tipo | Instalação |
|----------------|-----------|------|------------|
| Sensor de nível ultrassônico | 2 unidades | Medição de nível d'água (metros) | Postes de iluminação adjacentes ao piscinão |
| Estação meteorológica com pluviômetro | 1 unidade | Precipitação acumulada (mm/m²) | Poste de iluminação próximo |
| API climática pública | 1 integração | Previsão meteorológica e dados históricos | CPTEC/INPE + OpenWeatherMap (fallback) |

**Fluxo de dados:** Sensores → Gateway LoRa/WiFi → Broker MQTT → Endpoint REST (abstração) → Backend → Banco de dados → Dashboards + Alertas

### 4.2 Funcionalidades do MVP

- Ingestão e validação de dados de sensores em tempo real
- Armazenamento em séries temporais com compressão e retenção configurável
- Dashboard técnico com gráficos de séries temporais, mapa e indicadores
- Dashboard público com semáforo de risco e informações simplificadas
- Motor de regras com 4 níveis de alerta (normal, amarelo, laranja, vermelho)
- Alertas via notificação push (PWA) e email
- Inscrição de cidadãos para recebimento de alertas

### 4.3 Fora do Escopo (MVP)

| Item | Justificativa | Previsão |
|------|---------------|----------|
| Aplicativo mobile nativo (Android/iOS) | PWA atende ao caso de uso básico | Fase futura |
| Modelo hidrológico complexo (Manning, Saint-Venant) | Modelo linear simplificado é suficiente para o TCC | Trabalho futuro |
| SMS e WhatsApp | Requerem APIs pagas (Twilio); adapter pattern preparado | Fase futura, adapters prontos |
| Monitoramento de múltiplos piscinões simultaneamente | Arquitetura projetada para N piscinões (`reservatorio_id` em todas as entidades), mas MVP valida com 1 | Fase 2 |
| Integração com sistemas da Defesa Civil / CEMADEN | Requer convênios institucionais | Trabalho futuro |
| Análise preditiva com Machine Learning | Necessita volume histórico de dados | Trabalho futuro |
| Câmeras de monitoramento / CFTV | Foco no monitoramento por sensores digitais | Fora do escopo |

### 4.4 Premissas

1. O sistema de filas MQTT é abstraído — o backend consome dados via endpoint REST (`POST /api/v1/ingestao/leituras`)
2. Os sensores IoT e o gateway estão fora do escopo de desenvolvimento deste TCC (são hardware pré-existente)
3. O servidor de produção será Ubuntu 24.04 LTS com Docker instalado
4. O acesso à internet do servidor é estável para consulta de APIs climáticas

---

## 5. Funcionalidades do Sistema

### 5.1 Módulos Principais

#### Módulo 1 — Ingestão de Dados (IoT Pipeline)

Responsável por receber, validar e persistir dados dos sensores e APIs externas.

- Endpoint REST para recebimento de leituras em batch do gateway MQTT
- Validação de payload (Pydantic schemas) com rejeição de dados malformados
- Autenticação do endpoint por API Key (proteção contra dados injetados)
- Persistência em hypertable TimescaleDB com particionamento automático por tempo
- Integração periódica com API climática (CPTEC/INPE) para dados complementares

#### Módulo 2 — Processamento e Regras de Negócio

Motor de cálculos hidrológicos simplificados e engine de regras para alertas.

- Cálculo de volume atual do reservatório: `V = f(nível, geometria_da_seção)`
- Taxa de variação do nível: `Δh/Δt = (h_atual - h_anterior) / (t_atual - t_anterior)`
- Estimativa de tempo para transbordo: `T_transbordo = (cota_transbordo - h_atual) / (Δh/Δt)`
- Correlação pluviometria × nível d'água para antecipação de alertas
- Redundância de sensores: média dos 2 sensores de nível; divergência > 10% sinaliza falha
- Disparo automático de alertas baseado em thresholds configuráveis

#### Módulo 3 — Sistema de Alertas

Motor de notificação multicanal com escalação hierárquica.

- **4 níveis de alerta:**
  - 🟢 **Normal**: nível ≤ 60% da capacidade, sem tendência de subida
  - 🟡 **Amarelo (Atenção)**: nível > 60% da capacidade **OU** taxa de variação > X cm/min
  - 🟠 **Laranja (Alerta)**: nível > 80% **OU** tempo estimado para transbordo < 2h
  - 🔴 **Vermelho (Emergência)**: nível > 90% **OU** tempo estimado para transbordo < 30min

- Canais de notificação (MVP): Web Push (PWA) + Email (SMTP)
- Canais de notificação (futuro): SMS + WhatsApp (adapter pattern implementado)
- Inscrição voluntária de cidadãos por reservatório
- Histórico completo de alertas disparados

#### Módulo 4 — Dashboard Técnico (Gestores / Defesa Civil)

Painel de controle completo para gestores e equipes da Defesa Civil.

- Visão geral com status de todos os reservatórios (mapa interativo Leaflet)
- Gráficos de séries temporais: nível d'água, pluviometria, volume (Recharts)
- Indicadores em tempo real: nível atual, taxa de variação, estimativa de transbordo
- Histórico de alertas com filtros por período e severidade
- Configuração de thresholds de alerta por reservatório
- Atualização em tempo real via WebSocket

#### Módulo 5 — Dashboard Público (Cidadãos)

Interface simplificada para a população do entorno.

- Semáforo visual de risco (Normal / Atenção / Alerta / Emergência)
- Nível atual do piscinão em linguagem acessível
- Última leitura e tendência (subindo, estável, descendo)
- Botão de inscrição para receber alertas (push, email)
- Informações educativas sobre enchentes e procedimentos de segurança
- PWA com funcionamento offline (cache da última leitura)

#### Módulo 6 — Integração com APIs Climáticas

Consulta periódica a APIs públicas para enriquecimento dos dados.

- API primária: CPTEC/INPE (previsão para o município)
- API de fallback: OpenWeatherMap (cobertura global, API key gratuita limitada)
- Dados capturados: previsão de chuva (mm), temperatura, umidade, condição climática
- Periodicidade: a cada 30 minutos (respeitando rate limits das APIs)

### 5.2 Funcionalidades Transversais

- 🔐 **Autenticação e Autorização**: JWT com refresh token + RBAC (gestor, admin)
- 🔑 **Autenticação de sensores**: API Key para endpoint de ingestão
- 📊 **Dashboard público**: Acesso sem autenticação (dados públicos de utilidade)
- 📝 **Logs estruturados**: Registro de todas as operações para auditoria
- 🏥 **Health checks**: Endpoints de monitoramento da saúde de cada serviço
- 📱 **Responsividade**: Interface adaptada para desktop, tablet e smartphone
- 🌐 **PWA**: Instalação como aplicativo, push notifications, cache offline

---

## 6. Stack Tecnológico

A tabela abaixo apresenta as tecnologias escolhidas para cada camada do sistema. As justificativas detalhadas e decisões arquiteturais (ADRs) constam no documento **004 - DevSpecs**.

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| **Sistema Operacional** | Ubuntu LTS | 24.04 |
| **Containerização** | Docker + Docker Compose | 27.x + 2.x |
| **Web Server / Reverse Proxy** | NGINX | 1.27 |
| **Backend (API)** | Python + FastAPI | 3.12 + 0.115 |
| **ORM** | SQLAlchemy Async + asyncpg | 2.0 |
| **Migrations** | Alembic | 1.x |
| **Validação** | Pydantic | 2.x |
| **Banco de Dados** | PostgreSQL + TimescaleDB | 16 + 2.x |
| **Cache / Broker** | Redis | 7.x |
| **Tasks Assíncronas** | ARQ | 0.26 |
| **Frontend (SPA)** | React + TypeScript + Vite | 18 + 5.x + 6.x |
| **UI Framework** | Tailwind CSS + shadcn/ui | 4.x |
| **Gráficos** | Recharts | 2.x |
| **Mapas** | Leaflet + react-leaflet | 1.9 + 4.x |
| **Data Fetching** | TanStack Query | 5.x |
| **Estado Global** | Zustand | 5.x |
| **PWA** | vite-plugin-pwa + Workbox | 0.21 |
| **Real-time** | WebSocket (FastAPI nativo) | — |
| **API Climática** | CPTEC/INPE + OpenWeatherMap | — |

---

## 7. Metodologia de Desenvolvimento

### 7.1 Abordagem Metodológica

O projeto adota uma **metodologia ágil adaptada para contexto acadêmico**, combinando elementos do framework Scrum (SCHWABER; SUTHERLAND, 2020) com práticas de Kanban para gestão visual de tarefas.

**Adaptações para contexto de TCC:**

- **Sprints de 2 semanas** com entregáveis parciais documentados
- **Backlog priorizado** pelo método RICE (Reach, Impact, Confidence, Effort)
- **Definition of Done (DoD)**: funcionalidade implementada + testada + documentada
- **Revisão contínua** com orientador a cada sprint
- **Kanban board** para visualização de progresso (To Do → In Progress → Review → Done)

### 7.2 Práticas de Engenharia de Software

- **Versionamento**: Git com branching strategy baseada em Gitflow simplificado (main + develop + feature branches)
- **Code Review**: Revisão de código antes de merge em develop
- **Testes**: Unitários (pytest) + Integração (httpx + TestClient) para backend; Vitest + Testing Library para frontend
- **CI/CD**: Pipeline básico para lint, testes e build (GitHub Actions ou equivalente)
- **Documentação como código**: Documentação técnica mantida no repositório (Markdown)

### 7.3 Ferramentas de Gestão

| Ferramenta | Uso |
|-----------|-----|
| Git + GitHub/GitLab | Versionamento de código e documentação |
| Kanban Board (GitHub Projects) | Gestão visual de tarefas |
| VS Code | IDE de desenvolvimento |
| Docker Desktop | Ambiente local de desenvolvimento |
| Insomnia / Bruno | Testes manuais de API |

---

## 8. Cronograma Macro

> **v1.1 — Atualização pós-conclusão (05/05/2026):**  
> A coluna *"Concluído em"* reflete as datas reais de término de cada fase. Todas as fases foram concluídas dentro do semestre letivo 2026/S1.

O desenvolvimento está organizado em 6 fases, com duração estimada baseada em sprints de 2 semanas.

### Fase 0 — Planejamento e Documentação Técnica

**Duração estimada:** 3 sprints (6 semanas) | **Concluído em:** 20/03/2026 ✅

| Entrega | Descrição | Sprint | Status |
|---------|-----------|--------|--------|
| Plano de Desenvolvimento | Visão geral, escopo, cronograma (este documento) | S0 | ✅ Concluído |
| SRS | Requisitos funcionais e não-funcionais, User Stories | S1 | ✅ Concluído |
| PRD | Pesquisa, estado da arte, fundamentação teórica | S1 | ✅ Concluído |
| DevSpecs | Especificação técnica, arquitetura, diagramas | S0 | ✅ Concluído |
| Backlog Técnico | Épicos e tarefas priorizadas | S2 | ✅ Concluído |

### Fase 1 — Setup de Infraestrutura

**Duração estimada:** 1 sprint (2 semanas) | **Concluído em:** 28/03/2026 ✅

- Docker Compose com todos os serviços (NGINX, FastAPI, PostgreSQL+TimescaleDB, Redis)
- Dockerfiles otimizados (backend + frontend build)
- Configuração NGINX (reverse proxy, WebSocket upgrade, static files)
- Scripts de setup e reset de ambiente
- Variáveis de ambiente (.env.example)
- Health checks e logs estruturados

**Épicos cobertos:** EPIC-00 (Bootstrap), EPIC-01 (Dockerfiles + NGINX)  
**Critério de aceite:** ✅ Ambiente sobe com `docker-compose up` e healthchecks passam.

### Fase 2 — Backend Core

**Duração estimada:** 3 sprints (6 semanas) | **Concluído em:** 14/04/2026 ✅

| Sprint | Entregas | Épicos | Status |
|--------|----------|--------|--------|
| S3 | Modelos de dados + Alembic migrations + seed de desenvolvimento | EPIC-02 | ✅ |
| S4 | API de ingestão de leituras + validação + persistência TimescaleDB | EPIC-03 + EPIC-04 | ✅ |
| S5 | Motor de regras + API de alertas + Worker + Clima | EPIC-05 + EPIC-06 + EPIC-07 + EPIC-11 | ✅ |

**Critério de aceite:** ✅ Endpoint de ingestão persiste dados; regras de negócio calculam corretamente; alertas são disparados quando thresholds são atingidos.

### Fase 3 — Frontend (Dashboards)

**Duração estimada:** 3 sprints (6 semanas) | **Concluído em:** 28/04/2026 ✅

| Sprint | Entregas | Épicos | Status |
|--------|----------|--------|--------|
| S6 | Setup React+Vite, layout base, componentes compartilhados, integração WebSocket | EPIC-08 | ✅ |
| S7 | Dashboard técnico: gráficos, mapa, indicadores, histórico | EPIC-09 | ✅ |
| S8 | Dashboard público: semáforo, informações simplificadas, inscrição alertas, PWA | EPIC-10 | ✅ |

**Critério de aceite:** ✅ Dashboards funcionais com dados reais; WebSocket atualiza em tempo real; PWA instalável com push notifications.

### Fase 4 — Integração, Testes e Validação

**Duração estimada:** 2 sprints (4 semanas) | **Concluído em:** 03/05/2026 ✅

- ✅ Integração com API climática (CPTEC/INPE + OpenWeatherMap) — EPIC-11
- ✅ Testes de integração (pytest + httpx.AsyncClient) — EPIC-12
- ✅ QA manual: PWA, push, email, responsividade — EPIC-12
- ✅ Validação das regras de negócio com 30 casos de teste unitários — EPIC-05
- ✅ Alertas multicanal: Push + Email operacionais

**Épicos cobertos:** EPIC-11 (Clima), EPIC-12 (Testes)  
**Critério de aceite:** ✅ Sistema operacional completo com todos os módulos integrados e testados.

### Fase 5 — Documentação Final e Apresentação

**Duração estimada:** 2 sprints (4 semanas) | **Concluído em:** 05/05/2026 ✅

- ✅ README.md completo com variáveis, setup em 5 passos, manutenção e backup — EPIC-13
- ✅ Revisão e atualização de todos os documentos (001–005) — EPIC-13
- ✅ Slides de apresentação acadêmica final (15–20 min) — EPIC-13
- ✅ Preparação do ambiente de demonstração (docker-compose up funcional)
- ✅ Entrega final — 05/05/2026

**Épicos cobertos:** EPIC-13 (Documentação Final)

---

### Resumo de Conclusão por Épico

| EPIC | Título | Data Conclusão |
|------|--------|---------------|
| EPIC-00 | Bootstrap do Projeto | 22/03/2026 |
| EPIC-01 | Dockerfiles + NGINX | 25/03/2026 |
| EPIC-02 | Banco de Dados + Migrations | 29/03/2026 |
| EPIC-03 | Auth (JWT + RBAC) | 02/04/2026 |
| EPIC-04 | Ingestão IoT | 04/04/2026 |
| EPIC-05 | Processamento + Regras RN-01..06 | 08/04/2026 |
| EPIC-06 | Alertas + Push + Email + Worker | 12/04/2026 |
| EPIC-07 | Dashboard APIs | 14/04/2026 |
| EPIC-08 | Frontend Base (React/TypeScript) | 19/04/2026 |
| EPIC-09 | Dashboard Técnico | 22/04/2026 |
| EPIC-10 | Dashboard Público + PWA | 26/04/2026 |
| EPIC-11 | Integração Climática | 29/04/2026 |
| EPIC-12 | Testes e Qualidade | 03/05/2026 |
| EPIC-13 | Documentação Final e Entrega | 05/05/2026 |

---

## 9. Riscos e Mitigações

| # | Risco | Impacto | Probabilidade | Mitigação |
|---|-------|---------|---------------|-----------|
| R1 | Sensores IoT não disponíveis no prazo | Alto | Média | Simulador de dados sintéticos para desenvolvimento e testes |
| R2 | API climática (CPTEC/INPE) fora do ar | Médio | Baixa | Dual-source: OpenWeatherMap como fallback automático |
| R3 | TimescaleDB com performance insuficiente | Médio | Baixa | Continuous aggregates + compressão + ajuste de chunks |
| R4 | Complexidade do WebSocket com NGINX | Baixo | Média | Configuração documentada; fallback para Server-Sent Events (SSE) |
| R5 | Escopo excede prazo do TCC | Alto | Média | MVP rigoroso; funcionalidades extras marcadas como "trabalho futuro" |
| R6 | Thresholds de alerta inadequados | Médio | Média | Thresholds configuráveis por reservatório; calibração com dados reais |
| R7 | Integração MQTT falha | Baixo | Baixa | MQTT abstraído por endpoint REST; desacoplamento total |

---

## 10. Referências Bibliográficas

### Fundamentação Teórica — Hidrologia e Drenagem Urbana

CANHOLI, A. P. **Drenagem urbana e controle de enchentes**. 2. ed. São Paulo: Oficina de Textos, 2014.

TUCCI, C. E. M. **Hidrologia: ciência e aplicação**. 4. ed. Porto Alegre: ABRH/UFRGS, 2009.

BRASIL. Ministério da Ciência, Tecnologia e Inovação. Centro Nacional de Monitoramento e Alertas de Desastres Naturais — CEMADEN. Disponível em: https://www.gov.br/cemaden/. Acesso em: 01 abr. 2026.

SÃO PAULO (Estado). Departamento de Águas e Energia Elétrica — DAEE. **Plano Diretor de Macrodrenagem da Bacia do Alto Tietê**. São Paulo: DAEE, 2014.

RIO DE JANEIRO (Município). Sistema Alerta Rio — Sistema de Alerta de Chuvas Intensas da Prefeitura do Rio de Janeiro. Disponível em: https://alertario.rio.rj.gov.br/. Acesso em: 01 abr. 2026.

### Internet das Coisas (IoT) e MQTT

ATZORI, L.; IERA, A.; MORABITO, G. The Internet of Things: a survey. **Computer Networks**, v. 54, n. 15, p. 2787-2805, 2010.

GUBBI, J. et al. Internet of Things (IoT): a vision, architectural elements, and future directions. **Future Generation Computer Systems**, v. 29, n. 7, p. 1645-1660, 2013.

OASIS Standard. **MQTT Version 5.0**. 2019. Disponível em: https://mqtt.org/. Acesso em: 01 abr. 2026.

### Stack Tecnológico

RAMÍREZ, S. **FastAPI Documentation**. Disponível em: https://fastapi.tiangolo.com/. Acesso em: 01 abr. 2026.

TIMESCALE, Inc. **TimescaleDB Documentation**. Disponível em: https://docs.timescale.com/. Acesso em: 01 abr. 2026.

META. **React Documentation**. Disponível em: https://react.dev/. Acesso em: 01 abr. 2026.

DOCKER, Inc. **Docker Documentation**. Disponível em: https://docs.docker.com/. Acesso em: 01 abr. 2026.

NGINX, Inc. **NGINX Documentation**. Disponível em: https://nginx.org/en/docs/. Acesso em: 01 abr. 2026.

### Séries Temporais e Monitoramento

FREEDMAN, D. A. **Statistical Models: theory and practice**. Cambridge: Cambridge University Press, 2009.

ENDSLEY, M. R. **Designing for Situation Awareness**: an approach to user-centered design. 2. ed. Boca Raton: CRC Press, 2011.

### Metodologia de Desenvolvimento

SCHWABER, K.; SUTHERLAND, J. **The Scrum Guide**: the definitive guide to Scrum — the rules of the game. 2020. Disponível em: https://scrumguides.org/. Acesso em: 01 abr. 2026.

ANDERSON, D. J. **Kanban**: successful evolutionary change for your technology business. Sequim: Blue Hole Press, 2010.

### Normas Técnicas

ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **ABNT NBR ISO/IEC 27001:2022** — Tecnologia da informação — Técnicas de segurança — Sistemas de gestão da segurança da informação. Rio de Janeiro, 2022.

ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **ABNT NBR ISO 22320:2020** — Gestão de emergências — Diretrizes para gestão de incidentes. Rio de Janeiro, 2020.

---

## Resumo Final

**Funcionalidades-chave:**
- Ingestão IoT em tempo real (sensores de nível + pluviômetro + API climática)
- Motor de regras com cálculos hidrológicos simplificados e alertas hierárquicos
- Dashboard técnico (gestores) + Dashboard público (cidadãos)
- PWA com notificações push e funcionamento offline
- Arquitetura escalável de 1 para N piscinões

**Stack principal:** Python/FastAPI + React/TypeScript + PostgreSQL/TimescaleDB + Redis + Docker + NGINX

**Fluxo do plano de desenvolvimento:**

```
Documentação (Fase 0) → Infraestrutura (Fase 1) → Backend (Fase 2) → Frontend (Fase 3) → Integração/Testes (Fase 4) → Entrega (Fase 5)
```
