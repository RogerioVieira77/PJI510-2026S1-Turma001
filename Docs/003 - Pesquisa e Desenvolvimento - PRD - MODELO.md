# PRD — Product Requirements Document

## # NOME DO SISTEMA - Descrição breve do Objetivo do Sistema

**Projeto:** Nome do Sistema 
**Versão:** X.X
**Data:** DD-MM-AAAA  
**Status:** Em Definição  

---

## Sumário Executivo

Este PRD define a construção do sistema....

Traduz o SRS em decições de Arquitetura de Solução, descreve as decisões tomadas, o contexto e as justificativas.

O sistema prioriza:

1. ...
2. ...
3. ...
...

## 1. Contexto e Motivação

Baseado nos documentos de requisitos (SRS) e no plano:

1. ...
2. ...
3. ... 
...


---

## 2. Visão do Produto

### 2.1 Declaração de Visão

> ... .

## 3. Arquitetura Proposta

### 3.1 Decisão: MODELO ARQUITETURAL

Exemeplo: A decisão é começar com uma arquitetura de **Monolito Modular** e inicialmente não usar microserviços.

**Decisão: Adotar um monolito modular** com separação por domínios de negócio.

**Justificativa:**
- Equipe reduzida — microserviços exigem overhead operacional desproporcional
- Transações cross-domain são frequentes (ex:...)
- Deploy e debugging significativamente mais simples
- Pode ser extraído em serviços independentes futuramente se necessário

### 3.2 Stack Tecnológica

| Camada | Tecnologia | Justificativa |
|--------|------------|---------------|
| **Frontend** | ESCOLHA   | Justificativa |
| **Backend** | ESCOLHA   | Justificativa |
| **Banco de dados** | ESCOLHA   | Justificativa |
...

### 3.3 Estrutura de Diretórios Proposta

```
nome_do_sistema/
├── Pasta_Principal          # Descrição
├── 
├── .env.example                # Template de variáveis
│
├── backend/                    # 
│   ├── main.py                 # 
│   ├── config.py               # 
│   ├── database.py             # 
│   ├── dependencies.py         # 
│   │
│   ├── 
│
└── docs/                       # Documentação
```

### 3.4 Infraestrutura

---

## 4. Requisitos Funcionais

### 4.1 Módulo Administrativo (admin)

> Cadastros fundamentais que sustentam todos os demais módulos.

| ID | Requisito | Prioridade | Fase |
|----|-----------|------------|------|
| RF-01 | Cadastro de condomínios (nome, endereço, CNPJ, nº unidades) | Alta | 1 |
| RF-02 | Cadastro de unidades (número, bloco, área, tipo, proprietário) | Alta | 1 |
| RF-03 | Cadastro de moradores (nome, CPF, telefone, email, vínculo com unidade) | Alta | 1 |
| RF-04 | Cadastro de veículos vinculados a unidades | Média | 2 |
| RF-05 | Gestão de perfis e permissões (síndico, morador, porteiro, admin) | Alta | 1 |
| RF-06 | Histórico de mudanças de proprietário/inquilino por unidade | Média | 2 |
| RF-07 | Registro de multas e advertências | Média | 2 |
| RF-08 | Upload e gestão de documentos (regulamento, atas, contratos) | Média | 2 |

**Modelo de dados principal:**

```
Condominio (id, nome, endereco, cnpj, num_unidades, ativo, created_at)
    │ 1:N
Unidade (id, condominio_id, numero, bloco, area_m2, tipo, ativo)
    │ 1:N
Morador (id, unidade_id, nome, cpf, telefone, email, tipo [proprietario|inquilino|dependente], ativo)
    │ 1:N
Veiculo (id, morador_id, placa, modelo, cor, tipo)
```

### 4.2 Módulo Financeiro (financeiro)

> Coração operacional. Sem financeiro funcional, o sistema não tem propósito.

| ID | Requisito | Prioridade | Fase |
|----|-----------|------------|------|
| RF-10 | Geração automática de taxas condominiais mensais | Alta | 1 |
| RF-11 | Emissão de boletos (integração bancária CNAB/API) | Alta | 1 |
| RF-12 | Registro e baixa de pagamentos (manual e automática) | Alta | 1 |
| RF-13 | Cálculo automático de multa, juros e desconto por antecipação | Alta | 1 |
| RF-14 | Controle de inadimplência com relatório e alertas | Alta | 1 |
| RF-15 | Cadastro e gestão de contas a pagar (fornecedores, concessionárias) | Alta | 2 |
| RF-16 | Fluxo de caixa (entradas e saídas com categorização) | Alta | 2 |
| RF-17 | Demonstrativo financeiro mensal (prestação de contas) | Alta | 2 |
| RF-18 | Rateio de despesas por unidade (fração ideal ou igualitário) | Média | 2 |
| RF-19 | Emissão de recibos e segunda via de boletos | Média | 2 |
| RF-20 | Cobrança extra (obras, fundo de reserva) | Média | 2 |
| RF-21 | Integração com gateway de pagamento (Pix, cartão) | Média | 3 |
| RF-22 | Conciliação bancária automática | Baixa | 3 |

**Modelo de dados principal:**

```
ContaCondominio (id, condominio_id, banco, agencia, conta, saldo)

TaxaCondominial (id, condominio_id, mes_ref, valor_base, data_vencimento, status)
    │ 1:N
Cobranca (id, taxa_id, unidade_id, valor, multa, juros, desconto, data_venc, status [pendente|pago|vencido|cancelado])
    │ 1:N
Pagamento (id, cobranca_id, valor_pago, data_pagamento, forma [boleto|pix|transferencia], comprovante_url)

ContaPagar (id, condominio_id, fornecedor_id, descricao, valor, data_venc, categoria, status, nota_fiscal_url)

LancamentoFinanceiro (id, condominio_id, tipo [receita|despesa], categoria, valor, data, descricao, cobranca_id?, conta_pagar_id?)
```

### 4.3 Módulo Manutenção (manutencao)

> Gestão de solicitações de moradores e ordens de serviço.

| ID | Requisito | Prioridade | Fase |
|----|-----------|------------|------|
| RF-30 | Abertura de solicitações por moradores (descrição, categoria, fotos) | Alta | 1 |
| RF-31 | Categorização de serviços (elétrico, hidráulico, pintura, limpeza, outros) | Alta | 1 |
| RF-32 | Definição de prioridade (baixa, normal, urgente, emergência) | Alta | 1 |
| RF-33 | Geração de ordem de serviço (OS) a partir de solicitação | Alta | 1 |
| RF-34 | Atribuição de técnico responsável (interno ou fornecedor) | Alta | 2 |
| RF-35 | Acompanhamento de status (aberto, em andamento, concluído, cancelado) | Alta | 1 |
| RF-36 | SLA configurável por categoria (tempo máximo de resposta/resolução) | Média | 2 |
| RF-37 | Histórico de manutenções por unidade e por equipamento | Média | 2 |
| RF-38 | Agenda de manutenção preventiva com alertas | Média | 3 |
| RF-39 | Checklist de inspeção e conclusão de serviço | Baixa | 3 |
| RF-40 | Relatórios: tempo médio, custo por categoria, chamados por período | Média | 2 |
| RF-41 | Vínculo entre OS concluída e lançamento financeiro (custo) | Média | 2 |

**Modelo de dados principal:**

```
Solicitacao (id, unidade_id, morador_id, descricao, categoria, prioridade, status, fotos[], created_at)
    │ 1:1
OrdemServico (id, solicitacao_id, tecnico, fornecedor_id?, prazo, custo_estimado, custo_real, status, observacoes, concluida_em)

AgendaPreventiva (id, condominio_id, equipamento_id?, descricao, periodicidade, proxima_execucao, checklist[])
```

### 4.4 Módulo Facilities (facilities)

> Gestão de espaços comuns e equipamentos do condomínio.

| ID | Requisito | Prioridade | Fase |
|----|-----------|------------|------|
| RF-50 | Cadastro de áreas comuns (salão, churrasqueira, quadra, piscina, academia) | Alta | 1 |
| RF-51 | Reserva de espaços por moradores com visualização de disponibilidade | Alta | 1 |
| RF-52 | Regras de reserva configuráveis (antecedência, duração, taxa de uso) | Média | 2 |
| RF-53 | Aprovação de reservas (automática ou por síndico) | Média | 2 |
| RF-54 | Cadastro de equipamentos (elevadores, bombas, geradores, portões) | Média | 2 |
| RF-55 | Registro de manutenções por equipamento (logs de falhas, substituições) | Média | 2 |
| RF-56 | Upload de manuais e documentação técnica de equipamentos | Baixa | 3 |
| RF-57 | Calendário integrado de reservas e manutenções | Média | 2 |

**Modelo de dados principal:**

```
AreaComum (id, condominio_id, nome, descricao, capacidade, regras, taxa_uso, ativa, fotos[])

Reserva (id, area_id, unidade_id, morador_id, data_inicio, data_fim, status [pendente|aprovada|rejeitada|cancelada], valor, observacoes)

Equipamento (id, condominio_id, nome, localizacao, fabricante, modelo, data_instalacao, proxima_manutencao, manual_url, status)
```

### 4.5 Módulo Social (social)

> Comunicação interna e engajamento entre moradores e administração.

| ID | Requisito | Prioridade | Fase |
|----|-----------|------------|------|
| RF-60 | Publicação de comunicados (texto, imagens, urgência) | Alta | 1 |
| RF-61 | Notificações multi-canal (email, push, SMS) | Alta | 2 |
| RF-62 | Comunicados emergenciais (interrupção de água, energia, gás) | Alta | 2 |
| RF-63 | Mural digital (avisos, informações úteis, telefones de emergência) | Média | 2 |
| RF-64 | Criação de eventos do condomínio com inscrição | Média | 3 |
| RF-65 | Enquetes e votações rápidas (não deliberativas) | Média | 3 |
| RF-66 | Canal de sugestões e reclamações | Baixa | 3 |

**Modelo de dados principal:**

```
Comunicado (id, condominio_id, autor_id, titulo, conteudo, tipo [aviso|emergencia|informativo], destinatarios [todos|bloco|unidade], fixado, publicado_em, expira_em)

Evento (id, condominio_id, titulo, descricao, data, local, max_participantes, inscricoes[])

Enquete (id, condominio_id, pergunta, opcoes[], data_limite, votos[])
```

### 4.6 Módulo Assembleias (assembleia)

> Gestão de assembleias condominiais conforme legislação brasileira.

| ID | Requisito | Prioridade | Fase |
|----|-----------|------------|------|
| RF-70 | Criação de assembleia com pauta e convocação | Média | 2 |
| RF-71 | Registro de presença (quórum) | Média | 2 |
| RF-72 | Votação digital por pauta (presencial ou remota) | Média | 3 |
| RF-73 | Geração automática de ata com resultados | Média | 3 |
| RF-74 | Histórico de assembleias e atas por condomínio | Média | 2 |
| RF-75 | Procuração digital (delegação de voto) | Baixa | 3 |

### 4.7 Módulo Ocorrências (ocorrencias)

> Registro de eventos e incidentes no condomínio.

| ID | Requisito | Prioridade | Fase |
|----|-----------|------------|------|
| RF-80 | Registro de ocorrências (barulho, vazamento, dano, segurança) | Alta | 1 |
| RF-81 | Categorização e priorização | Alta | 1 |
| RF-82 | Acompanhamento de tratativa e resolução | Média | 2 |
| RF-83 | Anexos (fotos, vídeos) | Média | 2 |
| RF-84 | Relatório de ocorrências por período, tipo e unidade | Média | 2 |

### 4.8 Módulo Portaria (portaria)

> Controle básico de acesso sem dependência de hardware especializado.

| ID | Requisito | Prioridade | Fase |
|----|-----------|------------|------|
| RF-90 | Registro de visitantes (nome, documento, unidade destino, horário) | Média | 2 |
| RF-91 | Pré-autorização de visitantes pelo morador | Média | 2 |
| RF-92 | Controle de encomendas (recebimento, notificação, retirada) | Média | 2 |
| RF-93 | Registro de prestadores de serviço | Média | 2 |
| RF-94 | Livro de ocorrências da portaria (digital) | Média | 3 |

---

## 5. Requisitos Não Funcionais

| ID | Requisito | Especificação |
|----|-----------|---------------|
| RNF-01 | **Segurança** | Autenticação JWT, senhas com bcrypt, HTTPS obrigatório, CORS restritivo, rate limiting, headers OWASP |
| RNF-02 | **Desempenho** | Resposta de API < 500ms (p95), suporte a 1000 usuários simultâneos |
| RNF-03 | **Disponibilidade** | 99.5% uptime (aceita janela de manutenção programada) |
| RNF-04 | **Responsividade** | Interface funcional em desktop (1024px+), tablet (768px+) e mobile (375px+) |
| RNF-05 | **LGPD** | Dados pessoais criptografados, consentimento, direito ao esquecimento |
| RNF-06 | **Multi-tenancy** | Isolamento de dados por condomínio, sem vazamento cross-tenant |
| RNF-07 | **Acessibilidade** | WCAG 2.1 nível AA (contraste, navegação por teclado, screen readers) |
| RNF-08 | **Internacionalização** | pt-BR como idioma principal, moeda BRL, timezone America/Sao_Paulo |
| RNF-09 | **Auditoria** | Log de ações administrativas e financeiras com timestamp e autor |
| RNF-10 | **Backup** | Backup diário do banco de dados, retenção de 30 dias |

---

## 6. Dashboard e Relatórios

### 6.1 Dashboard do Síndico

Visão executiva com indicadores principais:

- **Financeiro**: Receita do mês vs. previsto, inadimplência (%), saldo em caixa
- **Manutenção**: Chamados abertos, SLA cumprido (%), OSs pendentes
- **Ocupação**: Unidades ocupadas vs. vagas, moradores ativos
- **Comunicação**: Últimos comunicados, eventos próximos
- **Ocorrências**: Abertas este mês, por categoria

### 6.2 Portal do Morador

Visão pessoal:

- **Financeiro**: Boletos pendentes, histórico de pagamentos, 2ª via
- **Solicitações**: Minhas solicitações e status
- **Reservas**: Minhas reservas, calendário de disponibilidade
- **Comunicados**: Feed de avisos e eventos
- **Documentos**: Regulamento, atas, informativos

### 6.3 Relatórios

| Relatório | Frequência | Destinatário |
|-----------|------------|--------------|
| Demonstrativo financeiro mensal | Mensal | Síndico, Conselho |
| Balancete | Mensal | Síndico, Conselho |
| Inadimplência | Mensal | Síndico |
| Chamados por categoria | Mensal | Síndico, Zelador |
| Consumo de áreas comuns | Mensal | Síndico |
| Prestação de contas anual | Anual | Assembleia |

---

## 7. Plano de Fases

### Fase 1 — MVP Funcional (8-10 semanas)

**Objetivo:** Sistema usável com funcionalidades essenciais de gestão.

**Critério de sucesso:** Um síndico consegue cadastrar o condomínio, gerenciar moradores, gerar cobranças, receber solicitações de manutenção e publicar comunicados.

#### Backend

- [ ] Reestruturar backend em módulos de domínio (`modules/`)
- [ ] Módulo Admin: CRUD de condomínios, unidades e moradores (RF-01 a RF-03, RF-05)
- [ ] Módulo Financeiro: Geração de taxas, cobranças, pagamentos, inadimplência (RF-10 a RF-14)
- [ ] Módulo Manutenção: Solicitações e OSs básicas (RF-30 a RF-33, RF-35)
- [ ] Módulo Facilities: Reservas de espaços comuns (RF-50, RF-51)
- [ ] Módulo Social: Comunicados básicos (RF-60)
- [ ] Módulo Ocorrências: Registro básico (RF-80, RF-81)
- [ ] Auth: Login, registro, JWT, roles (reaproveitar existente)
- [ ] Dashboard API: Indicadores financeiros e operacionais
- [ ] Gerar migrations iniciais com Alembic (não usar create_all)
- [ ] Seed de dados de demonstração
- [ ] Testes unitários para módulos core

#### Frontend

- [ ] Setup do projeto Next.js 16 com App Router, Tailwind, shadcn/ui
- [ ] Layout principal: sidebar, header, navegação
- [ ] Página de login
- [ ] Dashboard do síndico
- [ ] CRUD de unidades e moradores
- [ ] Tela de cobranças e pagamentos
- [ ] Tela de solicitações de manutenção (abertura + listagem)
- [ ] Tela de reserva de espaços
- [ ] Tela de comunicados
- [ ] Tela de ocorrências

#### Infraestrutura

- [ ] `docker-compose.staging.yml` com 4 containers (Postgres, Redis, Backend, Frontend)
- [ ] `.env` configurado para testes
- [ ] Nginx removido do staging (acesso direto às portas)
- [ ] Script de setup inicial (`scripts/setup.sh`)
- [ ] Corrigir path do `.env` no `config.py`

### Fase 2 — Expansão Operacional (8-10 semanas)

**Objetivo:** Funcionalidades avançadas que diferenciam o sistema.

- [ ] Financeiro: Contas a pagar, fluxo de caixa, demonstrativo mensal, rateio (RF-15 a RF-20)
- [ ] Manutenção: Atribuição de técnicos, SLA, relatórios, custo de OS (RF-34, RF-36, RF-37, RF-40, RF-41)
- [ ] Facilities: Regras de reserva, aprovação, cadastro de equipamentos (RF-52 a RF-55, RF-57)
- [ ] Social: Notificações multi-canal, comunicados emergenciais, mural (RF-61 a RF-63)
- [ ] Assembleias: Criação, presença, histórico (RF-70, RF-71, RF-74)
- [ ] Ocorrências: Tratativa, anexos, relatórios (RF-82 a RF-84)
- [ ] Portaria: Visitantes, encomendas, prestadores (RF-90 a RF-93)
- [ ] Portal do Morador: Interface dedicada com boletos, chamados, reservas
- [ ] Admin: Veículos, histórico de mudanças, multas, documentos (RF-04, RF-06 a RF-08)
- [ ] Geração de PDFs (boletos, demonstrativos, atas)
- [ ] Integração bancária básica (CNAB ou API de boletos)

### Fase 3 — Social e Engajamento (6-8 semanas)

**Objetivo:** Funcionalidades sociais e de engajamento dos moradores.

- [ ] Eventos com inscrição (RF-64)
- [ ] Enquetes e votações rápidas (RF-65)
- [ ] Canal de sugestões (RF-66)
- [ ] Votação digital em assembleias (RF-72)
- [ ] Ata automática (RF-73)
- [ ] Procuração digital (RF-75)
- [ ] Portaria: Livro de ocorrências digital (RF-94)
- [ ] Integração com gateway de pagamento — Pix, cartão (RF-21)
- [ ] Conciliação bancária (RF-22)
- [ ] App mobile (React Native / Expo) — leitura e ações básicas
- [ ] Notificações push

### Fase 4 — Escala, Qualidade e Integrações (8-12 semanas)

**Objetivo:** Robustez, monitoramento e integrações externas.

- [ ] Monitoramento (Prometheus, Grafana)
- [ ] Tracing distribuído (OpenTelemetry + Jaeger)
- [ ] Nginx como proxy reverso com SSL/TLS
- [ ] Réplica PostgreSQL para leitura
- [ ] Load testing e otimização
- [ ] Backup automatizado (S3 ou equivalente)
- [ ] Documentação completa da API (OpenAPI)
- [ ] Integrações opcionais de hardware (catracas, câmeras)
- [ ] IA assistiva (análise de inadimplência, previsão de custos)
- [ ] White-label para administradoras
- [ ] CI/CD pipeline completo

---

## 8. Métricas de Sucesso

### MVP (Fase 1)

| Métrica | Meta |
|---------|------|
| Condomínios cadastrados | ≥ 3 em piloto |
| Cobranças geradas | 100% das unidades do piloto |
| Solicitações abertas por moradores | ≥ 10 no primeiro mês |
| Tempo médio de resposta API | < 500ms |
| Uptime | ≥ 99% |

### Adoção (Fase 2+)

| Métrica | Meta |
|---------|------|
| Taxa de inadimplência visível | Antes: desconhecida → Depois: rastreada |
| Tempo médio de resolução de chamados | Medido e em redução |
| Uso de reservas pelo app | ≥ 30% dos moradores |
| Participação em assembleias digitais | ≥ 40% dos proprietários |

---

## 9. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Escopo excessivo no MVP | Alta | Alto | Fase 1 rigidamente limitada aos RFs listados |
| Integração bancária complexa | Média | Alto | Começar com boleto PDF manual, evoluir para API |
| Baixa adoção por moradores | Média | Médio | Interface mobile-first, UX simplificada |
| Performance com dados reais | Baixa | Médio | Índices PostgreSQL, cache Redis, paginação |
| Conformidade legal (condomínios) | Média | Alto | Consultar legislação brasileira (Código Civil art. 1.331+) |
| Servidor com recursos limitados (8GB RAM, 2 cores) | Alta | Alto | Compose staging minimalista, sem monitoramento no MVP |

---

## Referências

- 001 - Plano de desenvolvimento.md 
- 002 - Software Requirements Specification - SRS.md 
- Código Civil Brasileiro — Art. 1.331 a 1.358 (Condomínio Edilício)
- LGPD — Lei 13.709/2018

---

## 10. Decisões Formais de Arquitetura (Adendos)

As ADRs completas e vinculantes estão no documento **004 - DevSpecs.md, seção 19**. Abaixo, os adendos aprovados após a revisão técnica inicial.

### ADR-006: Onboarding do morador por auto-registro

**Status:** Aprovada

**Contexto**

O sistema precisa de um fluxo claro para que moradores acessem a plataforma pela primeira vez. As opções variam entre convite individual pelo síndico e auto-registro pelo morador.

**Opções consideradas**

1. convite individual enviado pelo síndico
2. auto-registro pelo morador com validação posterior
3. ambos os fluxos simultaneamente

**Decisão**

O MVP adotará auto-registro pelo morador. O morador se cadastra informando CPF e unidade. O vínculo com a unidade fica pendente até confirmação pelo síndico (ou automática se CPF já estiver pré-cadastrado no módulo admin).

**Consequências**

1. reduz carga operacional do síndico no onboarding
2. aumenta velocidade de adoção pelos moradores
3. exige fluxo de aprovação/confirmação de vínculo
4. CPF pré-cadastrado pelo síndico permite match automático

**Diretriz de implementação**

O auto-registro cria o `Usuario` com status `pendente`. Quando o síndico confirma (ou se há match por CPF), o vínculo `Usuario <-> Morador <-> Unidade` é ativado e o papel `morador` é concedido.

### ADR-007: Upload de arquivos com filesystem local no MVP

**Status:** Aprovada

**Contexto**

Vários módulos requerem upload de arquivos (fotos de manutenção, anexos de ocorrências, documentos, comprovantes). É necessário definir a estratégia de armazenamento desde o início.

**Opções consideradas**

1. filesystem local com abstração por interface
2. S3/MinIO desde o MVP
3. armazenamento em banco (BYTEA/BLOB)

**Decisão**

O MVP usará filesystem local com abstração por interface (`StorageProvider`). O provider real (S3, MinIO, Azure Blob) será conectado em fase posterior sem mudança no código de domínio.

**Consequências**

1. zero dependência de serviço externo no MVP
2. o módulo `core/storage/` nasce com contrato claro
3. exige atenção ao backup do volume no Docker
4. limite de tamanho de arquivo deve ser configurável

**Diretriz de implementação**

Criar interface `StorageProvider` com operações `upload`, `download`, `delete` e `get_url`. Implementação `LocalStorageProvider` salva em volume mapeado. Arquivos referenciados por path relativo nos modelos de domínio.
