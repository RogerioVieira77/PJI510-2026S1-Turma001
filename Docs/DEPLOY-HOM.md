# Alerta Romano — Runbook de Deploy em Homologação

## Identificação do Deploy

| Campo | Valor |
|-------|-------|
| Aplicação | `alerta-romano` |
| Domínio | `alertaromano.unicomunitaria.com.br` |
| Caminho no servidor | `/opt/unicomunitaria/docker/alerta-romano` |
| Porta local (host) | `8083` |
| Repositório | `git@github.com:RogerioVieira77/PJI510-2026S1-Turma001.git` |
| Healthcheck | `/api/v1/health` |
| Servidor | `srv1312297` — Ubuntu 24.04.4 LTS — `191.101.234.42` |

---

## Pré-checklist (execute antes de qualquer passo)

- [ ] DNS de `alertaromano.unicomunitaria.com.br` aponta para `191.101.234.42`
  ```bash
  dig +short alertaromano.unicomunitaria.com.br
  # Resultado esperado: 191.101.234.42
  ```
- [ ] Certificado wildcard está presente no servidor
  ```bash
  sudo ls /etc/letsencrypt/live/unicomunitaria.com.br/
  # Esperado: fullchain.pem  privkey.pem  ...
  ```
- [ ] Porta `8083` está livre no host
  ```bash
  ss -tulnp | grep 8083
  # Sem saída = porta livre
  ```
- [ ] Acesso SSH ao servidor confirmado

---

## Variáveis de Deploy

```bash
export APP_NAME="alerta-romano"
export APP_DOMAIN="alertaromano.unicomunitaria.com.br"
export APP_REPO_PATH="/opt/unicomunitaria/docker/alerta-romano"
export APP_PORT="8083"
export APP_HEALTHCHECK_PATH="/api/v1/health"
```

---

## Passo 1 — Clone do repositório

```bash
sudo mkdir -p /opt/unicomunitaria/docker
sudo git clone git@github.com:RogerioVieira77/PJI510-2026S1-Turma001.git \
  /opt/unicomunitaria/docker/alerta-romano

# Definir permissão de dono (ajuste o usuário se necessário)
sudo chown -R $USER:$USER /opt/unicomunitaria/docker/alerta-romano

cd /opt/unicomunitaria/docker/alerta-romano
git log --oneline -n 3
```

---

## Passo 2 — Configurar variáveis de ambiente

```bash
cd "$APP_REPO_PATH"
cp .env.example .env
nano .env   # ou: vim .env
```

Preencher **obrigatoriamente** os campos abaixo no `.env`:

| Variável | Instrução |
|---------|-----------|
| `POSTGRES_PASSWORD` | Senha forte (mínimo 24 chars) |
| `REDIS_PASSWORD` | Senha forte |
| `SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_hex(64))"` |
| `INGESTAO_API_KEY` | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `VAPID_PUBLIC_KEY` | Gerado em Passo 2.1 |
| `VAPID_PRIVATE_KEY` | Gerado em Passo 2.1 |
| `APP_ENV` | `homolog` |
| `CORS_ORIGINS` | `https://alertaromano.unicomunitaria.com.br` |
| `DATABASE_URL` | `postgresql+asyncpg://<USER>:<SENHA>@postgres:5432/<DB>` |
| `REDIS_URL` | `redis://:<REDIS_PASSWORD>@redis:6379/0` |

### Passo 2.1 — Gerar chaves VAPID (opcional para push notifications)

```bash
pip3 install py_vapid --quiet
python3 scripts/generate_vapid_keys.py
# Copie VAPID_PUBLIC_KEY e VAPID_PRIVATE_KEY para o .env
```

> Pule se não for testar Push Notifications em HOM.

---

## Passo 3 — Build e subida dos containers

```bash
cd "$APP_REPO_PATH"

# Build de todas as imagens e subida em background
docker compose up -d --build

# Acompanhar logs de startup (aguardar ~60s)
docker compose logs -f --tail=100
# Ctrl+C quando os logs estabilizarem
```

O backend executa `alembic upgrade head` automaticamente antes do uvicorn.  
Acompanhe as migrations nos logs:

```bash
docker compose logs backend | grep -E "alembic|migration|Running"
```

Verificar status de todos os containers:

```bash
docker compose ps
```

Resultado esperado:

```
NAME                      STATUS
alerta_romano_postgres    Up (healthy)
alerta_romano_redis       Up (healthy)
alerta_romano_backend     Up
alerta_romano_worker      Up
alerta_romano_frontend    Up
alerta_romano_nginx       Up
```

---

## Passo 4 — Validação local (antes do NGINX do host)

```bash
# Health da API
curl -sS "http://127.0.0.1:${APP_PORT}${APP_HEALTHCHECK_PATH}"
# Esperado: {"status":"ok",...}

# Status HTTP do frontend
curl -o /dev/null -w '%{http_code}\n' "http://127.0.0.1:${APP_PORT}/"
# Esperado: 200

# Testar um endpoint da API
curl -o /dev/null -w '%{http_code}\n' "http://127.0.0.1:${APP_PORT}/api/v1/auth/me"
# Esperado: 401 (sem token — mas confirma que a API responde)
```

---

## Passo 5 — Configurar NGINX do host

```bash
# Copiar vhost
sudo cp "$APP_REPO_PATH/nginx/alerta-romano.hml.conf" \
        "/etc/nginx/sites-available/${APP_NAME}.hml.conf"

# Habilitar (symlink)
sudo ln -sfn \
  "/etc/nginx/sites-available/${APP_NAME}.hml.conf" \
  "/etc/nginx/sites-enabled/${APP_NAME}.hml.conf"

# Validar configuração
sudo nginx -t
# Esperado: syntax is ok / test is successful

# Recarregar
sudo systemctl reload nginx
```

---

## Passo 6 — Hardening UFW

```bash
# Bloquear porta da app — acesso apenas via NGINX (porta 80/443)
sudo ufw deny ${APP_PORT}/tcp

# Confirmar regras
sudo ufw status numbered
```

Regras esperadas ativas:

| # | Porta | Ação |
|---|-------|------|
| 1 | OpenSSH | ALLOW |
| 2 | Nginx Full | ALLOW |
| N | 8083/tcp | DENY |

---

## Passo 7 — Validação pública fim a fim

```bash
# HTTP deve redirecionar para HTTPS
curl -I "http://${APP_DOMAIN}" | head -n 5
# Esperado: HTTP/1.1 301 Moved Permanently

# HTTPS deve responder 200
curl -I "https://${APP_DOMAIN}" | head -n 10
# Esperado: HTTP/2 200

# Healthcheck via HTTPS
curl -sS "https://${APP_DOMAIN}${APP_HEALTHCHECK_PATH}"
# Esperado: {"status":"ok",...}

# Dashboard público
curl -o /dev/null -w '%{http_code}\n' "https://${APP_DOMAIN}/"
# Esperado: 200
```

---

## Seed de dados de desenvolvimento (opcional)

Para popular com reservatórios e usuários de exemplo:

```bash
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} \
  -f /docker-entrypoint-initdb.d/seed_dev.sql
```

Criar usuário admin inicial:

```bash
# Substitua a senha e a API Key correta
curl -s -X POST "https://${APP_DOMAIN}/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Admin HOM","email":"admin@piscinao.local","password":"Admin@HOM2026!","role":"admin"}'
```

---

## Rollback

Em caso de falha após o deploy:

```bash
cd "$APP_REPO_PATH"

# Ver histórico de commits
git log --oneline -n 10

# Voltar para commit estável
git checkout <commit_estavel>

# Rebuild e resubida
docker compose up -d --build

# Validar
docker compose ps
curl -sS "http://127.0.0.1:${APP_PORT}${APP_HEALTHCHECK_PATH}"
```

---

## Comandos de manutenção recorrente

```bash
cd "$APP_REPO_PATH"

# Atualizar código e redeployar
git pull origin main
docker compose up -d --build

# Logs em tempo real
docker compose logs -f backend
docker compose logs -f worker

# Reiniciar serviço específico sem parar os demais
docker compose restart backend

# Verificar uso de recursos
docker stats --no-stream
```

---

## Registro pós-deploy

Preencher após conclusão bem-sucedida:

```
Deploy realizado em: ___/___/____  __:__
Aplicação:          alerta-romano
Domínio:            alertaromano.unicomunitaria.com.br
Porta local:        8083
Caminho:            /opt/unicomunitaria/docker/alerta-romano
Versão implantada:  (branch/commit: _______________)
Status NGINX host:  OK / FALHOU
Status UFW:         OK / FALHOU
Validação local:    OK / FALHOU
Validação pública:  OK / FALHOU
Responsável:        _______________
Observações:        _______________
```

---

## Checklist operacional final

- [ ] DNS confirmado e propagado
- [ ] `.env` preenchido com senhas fortes (nunca comitar)
- [ ] Todos os containers em `Up` ou `Up (healthy)`
- [ ] Migrations aplicadas (`alembic upgrade head` nos logs)
- [ ] Healthcheck local retorna `{"status":"ok"}`
- [ ] Vhost NGINX copiado e habilitado
- [ ] `nginx -t` sem erros
- [ ] `systemctl reload nginx` executado
- [ ] UFW bloqueando porta `8083` externamente
- [ ] `curl -I http://vigia-romano.unicomunitaria.com.br` retorna `301`
- [ ] `curl -I https://vigia-romano.unicomunitaria.com.br` retorna `200`
- [ ] Registro pós-deploy preenchido
- [ ] Rollback testado ou procedimento conhecido
