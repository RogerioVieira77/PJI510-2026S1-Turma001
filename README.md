# PJI510-2026S1-Turma001 — Sistema de Monitoramento de Piscinões utilizando IoT

## Disciplina

PJI510 — Projeto Integrador em Engenharia da Computação (2026/S1 — Turma 001)

## Tema

Criação de um sistema de monitoramento de **reservatórios de detenção** (piscinões/pôlders), que utilize uma solução de Internet das Coisas (IoT) para monitoramento em tempo real, modelo matemático para prever transbordos e possua um sistema de alertas multicanal para avisar a população e a Defesa Civil sobre possíveis enchentes.

## Título Provisório

**Sistema de Monitoramento de Piscinões (Pôlders) utilizando IoT**

## Problema

Como a Internet das Coisas pode ajudar na atenuação dos impactos das enchentes, auxiliando na tomada de decisões e enviando alertas à comunidade, nas áreas de várzea da zona leste de São Paulo?

## Objetivo

Entender os danos causados pelos alagamentos, suas frequências de ocorrência, identificar na comunidade o grau de conhecimento sobre situações de risco e disponibilizar uma ferramenta de monitoramento e alerta proativos que ajude a população a ser avisada de um possível alagamento em tempo real.

## Stack Tecnológico

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12 + FastAPI + Pydantic v2 |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Banco de Dados | PostgreSQL 16 + TimescaleDB 2.x |
| Cache / Broker | Redis 7 + ARQ |
| Web Server | NGINX 1.27 |
| Infra | Docker + Docker Compose / Ubuntu 24.04 LTS |
| Mapas | Leaflet + OpenStreetMap |
| Gráficos | Recharts |
| Real-time | WebSocket (FastAPI) |
| PWA | vite-plugin-pwa + Workbox |

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [001 - Plano de Desenvolvimento](Docs/001%20-%20Plano%20de%20desenvolvimento.md) | Plano macro do projeto: objetivos, escopo, cronograma, riscos |
| [004 - DevSpecs](Docs/004%20-%20DevSpecs.md) | Especificação técnica: arquitetura (C4), ADRs, ER, endpoints, Docker |

## Como Executar

```bash
# 1. Clonar o repositório
git clone <repo-url>
cd piscinao-monitor

# 2. Copiar variáveis de ambiente
cp .env.example .env

# 3. Subir todos os serviços
docker compose up -d

# 4. Acessar
# Frontend: http://localhost
# API Docs: http://localhost/api/v1/docs
# Health:   http://localhost/api/v1/health
```
