# QA Checklist — PWA PiscinãoMonitor — TASK-122

**Objetivo:** Validar funcionalidades PWA em Chrome/Android (real ou DevTools emulado).  
**Pré-requisito:** Sistema rodando via `docker compose up -d` com dados semente aplicados.

---

## 1. Instalação PWA

| # | Passo | Critério de Aceite | Status |
|---|-------|--------------------|--------|
| 1.1 | Abrir `https://localhost` em Chrome Android ou DevTools → emular Pixel 6 | URL carrega sem erro de certificado (aceitar self-signed) | ☐ PASS / ☐ FAIL |
| 1.2 | Banner "Adicionar à tela inicial" aparece automaticamente | Banner exibido dentro de 30 s | ☐ PASS / ☐ FAIL |
| 1.3 | Tocar "Adicionar" e verificar ícone na home screen | Ícone aparece com nome "PiscinãoMonitor" | ☐ PASS / ☐ FAIL |
| 1.4 | Abrir app via ícone da home screen | Abre em modo standalone (sem barra de endereço) | ☐ PASS / ☐ FAIL |
| 1.5 | Inspecionar Lighthouse PWA score | Score ≥ 90 no Lighthouse PWA audit | ☐ PASS / ☐ FAIL |

---

## 2. Modo Offline

| # | Passo | Critério de Aceite | Status |
|---|-------|--------------------|--------|
| 2.1 | Acessar `/` com conexão normal — aguardar carregamento completo | Página exibe reservatórios com status | ☐ PASS / ☐ FAIL |
| 2.2 | DevTools → Network → "Offline" (ou desativar Wi-Fi) | Nenhuma requisição de rede pendente | ☐ PASS / ☐ FAIL |
| 2.3 | Recarregar a página (`F5`) offline | App carrega do Service Worker (sem tela de dinossauro) | ☐ PASS / ☐ FAIL |
| 2.4 | Verificar banner amarelo no topo | Banner "Sem conexão — dados podem estar desatualizados" visível | ☐ PASS / ☐ FAIL |
| 2.5 | Verificar timestamp de última atualização | Exibe horário da última mensagem WS recebida | ☐ PASS / ☐ FAIL |
| 2.6 | Reativar conexão | Banner desaparece; dados são atualizados automaticamente | ☐ PASS / ☐ FAIL |
| 2.7 | Acessar `/login` offline | Página de login carrega (assets em cache) | ☐ PASS / ☐ FAIL |

---

## 3. Push Notifications

| # | Passo | Critério de Aceite | Status |
|---|-------|--------------------|--------|
| 3.1 | Abrir `/` (Dashboard Público) — clicar em um reservatório | Formulário de inscrição aparece na parte inferior | ☐ PASS / ☐ FAIL |
| 3.2 | Clicar botão "Receber alertas via Push" | Browser solicita permissão de notificação | ☐ PASS / ☐ FAIL |
| 3.3 | Conceder permissão | Botão muda para "Inscrito ✓"; nenhum erro exibido | ☐ PASS / ☐ FAIL |
| 3.4 | Fechar a aba do browser | Aba fechada (ou app em background) | ☐ PASS / ☐ FAIL |
| 3.5 | Injetar leitura acima de 60% via `POST /api/v1/ingestao/leituras` | Notificação push recebida no dispositivo em ≤ 10 s | ☐ PASS / ☐ FAIL |
| 3.6 | Tocar na notificação | App abre na página do reservatório correto | ☐ PASS / ☐ FAIL |
| 3.7 | Clicar "Cancelar inscrição Push" | Botão volta ao estado original; endpoint `/subscribe/push` DELETE retorna 204 | ☐ PASS / ☐ FAIL |

---

## 4. Inscrição via E-mail

| # | Passo | Critério de Aceite | Status |
|---|-------|--------------------|--------|
| 4.1 | Preencher e-mail válido no formulário de inscrição | Campo aceita formato válido | ☐ PASS / ☐ FAIL |
| 4.2 | Clicar "Inscrever-se" | Mensagem "Verifique seu e-mail para confirmar" aparece | ☐ PASS / ☐ FAIL |
| 4.3 | Abrir e-mail de confirmação | E-mail recebido com link de confirmação | ☐ PASS / ☐ FAIL |
| 4.4 | Clicar no link de confirmação | Browser abre URL de confirmação; inscrição ativada | ☐ PASS / ☐ FAIL |
| 4.5 | Inserir e-mail inválido (ex.: `abc`) | Mensagem de erro inline sem submeter o formulário | ☐ PASS / ☐ FAIL |
| 4.6 | Clicar link "Cancelar inscrição" no rodapé do e-mail | Inscrição desativada; página de confirmação exibida | ☐ PASS / ☐ FAIL |

---

## 5. Responsividade e Acessibilidade

| # | Passo | Critério de Aceite | Status |
|---|-------|--------------------|--------|
| 5.1 | Abrir DevTools → emular tela 375 × 667 (iPhone SE) | Layout sem overflow horizontal | ☐ PASS / ☐ FAIL |
| 5.2 | Abrir DevTools → emular tela 1440 × 900 (desktop) | Grid de reservatórios ocupa largura corretamente | ☐ PASS / ☐ FAIL |
| 5.3 | Executar axe DevTools ou Lighthouse accessibility | Sem erros críticos de acessibilidade (contrast, ARIA) | ☐ PASS / ☐ FAIL |
| 5.4 | Navegar com Tab pela página pública | Foco visível em todos os elementos interativos | ☐ PASS / ☐ FAIL |
| 5.5 | Verificar `AlertBadge` com leitor de tela (VoiceOver/TalkBack) | Status anunciado como texto ("Normal", "Atenção", etc.) | ☐ PASS / ☐ FAIL |

---

## 6. Dashboard Técnico (autenticado)

| # | Passo | Critério de Aceite | Status |
|---|-------|--------------------|--------|
| 6.1 | Fazer login com conta `gestor` | Redirecionado para `/dashboard` | ☐ PASS / ☐ FAIL |
| 6.2 | Selecionar reservatório no seletor | Mapa, gráfico e tabela atualizam para o reservatório selecionado | ☐ PASS / ☐ FAIL |
| 6.3 | Aguardar 5 s com WebSocket conectado | Painel SensorStatus atualiza em tempo real | ☐ PASS / ☐ FAIL |
| 6.4 | Tentar acessar `/dashboard` sem login | Redirecionado para `/login` | ☐ PASS / ☐ FAIL |
| 6.5 | Tentar acessar `/admin` com conta `gestor` | Exibe mensagem 403 — Acesso negado | ☐ PASS / ☐ FAIL |

---

## Resultado Final

| Seção | Total | PASS | FAIL | Obs. |
|-------|-------|------|------|------|
| 1. Instalação PWA | 5 | | | |
| 2. Modo Offline | 7 | | | |
| 3. Push Notifications | 7 | | | |
| 4. E-mail | 6 | | | |
| 5. Responsividade/A11y | 5 | | | |
| 6. Dashboard Técnico | 5 | | | |
| **TOTAL** | **35** | | | |

**Data de execução:** _______________  
**Executor:** _______________  
**Ambiente:** Chrome ___ · Android ___ (ou DevTools emulando ___)  
**Resultado global:** ☐ APROVADO (0 FAIL) / ☐ REPROVADO (___ FAILs)
