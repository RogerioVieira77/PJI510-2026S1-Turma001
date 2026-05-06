# Modelo Unificado - Deploy de Aplicações em Homologação

## 1. Finalidade

Este documento passa a ser o modelo oficial de deploy manual assistido no servidor de homologação.

Ele substitui a necessidade de consultar múltiplos documentos para:

- padrão de publicação das aplicações
- checklist operacional
- inventário básico de portas do host
- padrão de NGINX
- hardening mínimo com UFW
- validação pós-deploy
- rollback básico

Escopo deste documento:

- servidor de homologação com múltiplas aplicações dockerizadas
- publicação via NGINX no host
- HTTPS com certificado wildcard
- proteção do host com UFW

Não faz parte deste documento:

- pipeline GitHub Actions
- promoção entre ambientes DEV, HOM, VALIDACAO e PROD
- documentação específica de uma única aplicação

Esses pontos foram separados para documentos próprios.

---

## 2. Estado operacional observado no servidor

Dados levantados na análise inicial:

- hostname: `srv1312297`
- sistema operacional: `Ubuntu 24.04.4 LTS`
- proxy público: NGINX nas portas `80` e `443`
- firewall: UFW ativo
- aplicações implantadas sob `/opt/unicomunitaria/docker`
- padrão mais seguro já em uso: publicação local em `127.0.0.1` com reverse proxy no host

IP público observado no host analisado:

- `191.101.234.42`

Observação:

- Se o fluxo oficial usar outro IP público, isso deve ser confirmado antes de automatizar a esteira.

---

## 3. Padrão oficial de homologação

Toda nova aplicação em homologação deve seguir este padrão.

### 3.1 Regras obrigatórias

1. Toda aplicação deve ficar em `/opt/unicomunitaria/docker/<nome-do-projeto>`.
2. Toda aplicação deve ter código versionado no GitHub.
3. O acesso público deve acontecer apenas por NGINX nas portas `80` e `443`.
4. Banco de dados não deve ser publicado externamente.
5. Backend não deve ser publicado externamente, salvo exceção formalmente aprovada.
6. Frontend ou serviço principal publicado no host deve usar `127.0.0.1:<porta>`.
7. O UFW deve permitir externamente apenas `22`, `80` e `443`, além de exceções aprovadas.
8. Toda aplicação deve possuir ao menos:
   - endpoint de healthcheck
   - comando de subida
   - comando de logs
   - procedimento de rollback

### 3.2 Padrão recomendado de portas

Uso reservado do host:

- `22`: SSH
- `80`: NGINX HTTP
- `443`: NGINX HTTPS
- `8081-8099`: faixa preferencial para frontends ou upstreams publicados somente em localhost

Regras de uso:

- se a aplicação precisar de porta publicada no host, preferir `127.0.0.1:<porta>:<porta-interna>`
- evitar publicar bancos, Redis, workers e backends em `0.0.0.0`
- qualquer exceção deve ser registrada na documentação operacional da aplicação

### 3.3 Modelo de `docker compose`

Padrão seguro mínimo:

```yaml
services:
  db:
    image: postgres:16-alpine
    # sem ports

  backend:
    build: .
    # sem ports
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "127.0.0.1:8081:80"
    depends_on:
      - backend
```

Se a aplicação for somente API:

```yaml
services:
  api:
    build: .
    ports:
      - "127.0.0.1:8081:8000"
```

---

## 4. Variáveis padrão do deploy

Preencher antes da execução:

```bash
APP_NAME="<nome-app>"
APP_DOMAIN="<subdominio>.unicomunitaria.com.br"
APP_REPO_PATH="/opt/unicomunitaria/docker/<pasta-projeto>"
APP_PORT="<porta-local-app>"
APP_HEALTHCHECK_PATH="/health"
APP_MAIN_TEST_PATH="/"
```

Exemplo:

```bash
APP_NAME="sistema-de-cadastro"
APP_DOMAIN="sistema-de-cadastro.unicomunitaria.com.br"
APP_REPO_PATH="/opt/unicomunitaria/docker/sistema-de-cadastros"
APP_PORT="8081"
APP_HEALTHCHECK_PATH="/health"
APP_MAIN_TEST_PATH="/"
```

---

## 5. Pré-check obrigatório

### 5.1 Conferir repositório e arquivos

```bash
cd "$APP_REPO_PATH"
git status
ls -la
```

Validar se existem:

- `Dockerfile` ou build equivalente
- `docker-compose.yml`, `docker-compose.staging.yml` ou `compose.yml`
- `.env` ou `.env.example`
- endpoint de healthcheck

### 5.2 Conferir portas e containers ativos

```bash
docker ps
ss -tulnp
```

### 5.3 Conferir NGINX e UFW

```bash
nginx -t
ufw status numbered
```

### 5.4 Conferir DNS

Confirmar se o domínio da aplicação aponta para o servidor de homologação antes da publicação pública.

---

## 6. Ajustes mínimos antes de publicar

### 6.1 Corrigir exposição indevida de portas

Aplicar a seguinte política:

- banco: sem `ports`
- Redis: sem `ports`
- backend interno: sem `ports` quando o frontend ou proxy interno consome pela rede Docker
- serviço publicado no host: apenas em `127.0.0.1`

Exemplo correto:

```yaml
ports:
  - "127.0.0.1:${APP_PORT}:80"
```

Exemplo a evitar:

```yaml
ports:
  - "8081:80"
  - "5432:5432"
```

### 6.2 Corrigir frontend para same-origin

Se o frontend chamar API por IP ou porta fixa, trocar para caminho relativo:

```js
const API_URL = '/api'
```

### 6.3 Variáveis de ambiente

Padronizar o uso de env vars para:

- banco
- credenciais
- endpoint externo
- modo de execução

Exemplos comuns:

- `DB_HOST=db`
- `DB_PORT=5432`
- `API_BASE_URL=/api`
- `APP_ENV=homolog`

---

## 7. Subida da aplicação

Se o projeto usar compose padrão:

```bash
cd "$APP_REPO_PATH"
docker compose up -d --build
docker compose ps
```

Se usar arquivo específico de homologação:

```bash
cd "$APP_REPO_PATH"
docker compose -f docker-compose.staging.yml up -d --build
docker compose -f docker-compose.staging.yml ps
```

Logs iniciais:

```bash
docker compose logs --tail=100
```

Ou:

```bash
docker compose -f docker-compose.staging.yml logs --tail=100
```

---

## 8. Validação local antes do NGINX

Testar o upstream localmente antes de publicar o domínio:

```bash
curl -I "http://127.0.0.1:${APP_PORT}${APP_MAIN_TEST_PATH}"
curl -sS "http://127.0.0.1:${APP_PORT}${APP_HEALTHCHECK_PATH}"
```

Se a aplicação for API-only, testar também um endpoint funcional principal.

Exemplo:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' "http://127.0.0.1:${APP_PORT}/api/usuarios"
```

---

## 9. Padrão de NGINX no host

Arquivo esperado:

- `/etc/nginx/sites-available/${APP_NAME}.hml.conf`

Modelo padrão:

```nginx
server {
    listen 80;
    server_name ${APP_DOMAIN};

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name ${APP_DOMAIN};

    ssl_certificate /etc/letsencrypt/live/unicomunitaria.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/unicomunitaria.com.br/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Habilitar:

```bash
ln -sfn \
  "/etc/nginx/sites-available/${APP_NAME}.hml.conf" \
  "/etc/nginx/sites-enabled/${APP_NAME}.hml.conf"

nginx -t
systemctl reload nginx
```

Padronização obrigatória de HTTPS:

```nginx
listen 443 ssl http2;
```

Auditoria rápida:

```bash
grep -RIn --include='*.conf' 'listen .*443' /etc/nginx
nginx -t
```

---

## 10. Firewall e hardening

### 10.1 Política base

Permitir externamente:

- `OpenSSH`
- `Nginx Full`

Negar portas internas publicadas por exceção:

- porta da aplicação
- porta de backend
- porta de banco
- porta de Redis

### 10.2 Comandos úteis

Bloquear a porta publicada da app:

```bash
ufw deny ${APP_PORT}/tcp
```

Conferir regras:

```bash
ufw status numbered
```

Se houver regras duplicadas de `80` e `443` além de `Nginx Full`, limpar:

```bash
ufw delete allow 80
ufw delete allow 443
ufw delete allow 80/tcp
ufw delete allow 443/tcp
```

---

## 11. Validação pública fim a fim

Depois do NGINX ativo:

```bash
curl -I "http://${APP_DOMAIN}" | head -n 5
curl -I "https://${APP_DOMAIN}" | head -n 10
curl -sS "https://${APP_DOMAIN}${APP_HEALTHCHECK_PATH}"
```

Se existir endpoint funcional principal, testar também.

Resultado esperado:

- HTTP retorna `301`
- HTTPS retorna `200`
- healthcheck retorna sucesso
- endpoint funcional retorna código esperado

---

## 12. Rollback básico

Rollback operacional simples:

```bash
cd "$APP_REPO_PATH"
git log --oneline -n 5
git checkout <commit_estavel>
docker compose up -d --build
```

Se o projeto usar compose específico:

```bash
docker compose -f docker-compose.staging.yml up -d --build
```

Depois do rollback:

- validar `docker compose ps`
- validar `curl` local
- validar domínio público

---

## 13. Registro pós-deploy

Toda publicação deve registrar no mínimo:

- aplicação
- domínio
- caminho do projeto
- porta local usada
- branch ou tag implantada
- data e hora
- resultado da validação local
- resultado da validação pública
- regras de firewall aplicadas
- responsável pela execução

Modelo:

```md
Deploy realizado em: <data/hora>
Aplicação: <APP_NAME>
Domínio: <APP_DOMAIN>
Porta local: <APP_PORT>
Caminho: <APP_REPO_PATH>
Versão implantada: <branch/tag/commit>
Status NGINX: OK
Status UFW: OK
Validação local: OK
Validação pública: OK
Responsável: <nome>
```

---

## 14. Checklist operacional único

- [ ] Repositório conferido e limpo para deploy
- [ ] DNS do domínio validado
- [ ] Compose ajustado sem exposição indevida
- [ ] Banco e Redis sem portas públicas
- [ ] Serviço publicado no host usando `127.0.0.1`
- [ ] Frontend ajustado para same-origin quando necessário
- [ ] Variáveis de ambiente revisadas
- [ ] Containers iniciados com sucesso
- [ ] Logs iniciais sem erro crítico
- [ ] Healthcheck local validado
- [ ] Vhost NGINX criado e habilitado
- [ ] `nginx -t` executado com sucesso
- [ ] UFW revisado
- [ ] Validação HTTP/HTTPS executada
- [ ] Registro pós-deploy atualizado
- [ ] Procedimento de rollback validado ou conhecido

---

## 15. Inventário resumido do host analisado

Portas observadas durante a análise:

| Porta | Situação observada | Observação |
|---|---|---|
| 22 | Host | SSH |
| 80 | Host | NGINX HTTP |
| 443 | Host | NGINX HTTPS |
| 3000 | Container publicado | uso atual fora do padrão ideal |
| 8000 | Container publicado | uso atual fora do padrão ideal |
| 8081 | Localhost | aderente ao padrão ideal |
| 8091 | Container publicado | depende de UFW |
| 8092 | Container publicado | depende de UFW |
| 5434 | Container publicado | fora do padrão ideal |
| 6380 | Container publicado | fora do padrão ideal |
| 15432 | Container publicado | fora do padrão ideal |

Leitura operacional:

- o objetivo é convergir todas as aplicações para o padrão `127.0.0.1 + NGINX`, exceto quando houver justificativa técnica explícita.

---

## 16. Referências deste conjunto documental

- análise do estado atual: `Analise Inicial - Deploy Server.md`
- arquitetura alvo da esteira: `Arquitetura Alvo - Esteira de Deploy.md`
- plano técnico de implementação: `Plano Tecnico - Implementacao da Esteira.md`
- checklist reutilizável por aplicação: `Template - Checklist por Aplicacao.md`

Os arquivos legados em `docs_old/` passam a ser apenas referência histórica.