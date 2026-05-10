# Integração de Simulações - Previsão de Chuva, Situação Defesa Civil e Alertas

**Data**: Maio de 2026  
**Versão**: 1.0  
**Status**: Implementado

---

## 📋 Visão Geral

Este documento descreve a integração de **3 novos tipos de simulações** independentes no sistema PJI510 Alerta Romano:

1. **Previsão de Chuva** — API meteorológica que informa previsões de tempo
2. **Situação Defesa Civil** — Status geral da defesa civil com múltiplos alertas ativos
3. **Alerta Defesa Civil** — Alertas específicos por região

Cada simulação publica mensagens em sua própria fila RabbitMQ, permitindo que a equipe de aplicação consuma independentemente.

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│           Simulator UI (3 Tabs Novos)                       │
│  - Previsão Chuva                                           │
│  - Situação Defesa Civil                                    │
│  - Alertas Defesa Civil                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP POST
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              API Bridge (3 Novos Endpoints)                 │
│  POST /api/v1/previsoes                                     │
│  POST /api/v1/defesa-civil                                  │
│  POST /api/v1/alertas                                       │
└──────────┬─────────────────────────┬───────────────────┬────┘
           │ Publish AMQP            │                   │
           ▼                         ▼                   ▼
┌────────────────────┐  ┌─────────────────────────┐  ┌──────────────┐
│ previsoes.exchange │  │  defesa.exchange        │  │ defesa.dlx   │
│ (topic)            │  │  (topic)                │  │ (fanout)     │
└────────┬───────────┘  └───────┬──────────┬──────┘  │              │
         │ Binding                │          │        │ (DLQ routing)│
         │ previsao.#             │          │        │              │
         ▼                        ▼          ▼        ▼              │
┌──────────────────────┐ ┌─────────────────┐ ┌────────────────┐────┤
│ previsoes.fila       │ │defesa.situacao  │ │ defesa.alertas │
│ (24h TTL, DLQ)       │ │.fila            │ │.fila (24h TTL) │
│ Max 100k msgs        │ │(24h TTL, DLQ)   │ │Max 100k msgs   │
│                      │ │Max 100k msgs    │ │                │
└──────────────────────┘ └─────────────────┘ └────────────────┘
         │                      │                     │
         │ Consumers can subscribe to each queue independently
         ▼                      ▼                     ▼
    [Consumer App]       [Consumer App]        [Consumer App]
```

---

## 📡 Endpoints API

### 1. Previsão de Chuva

**POST** `/api/v1/previsoes`

**Request:**
```json
{
  "regiao": "Jardim Romano",
  "nivel": 3,
  "descricao": "Chuva fraca à tarde",
  "precipitacao_mm": 18.5
}
```

**Parameters:**
- `regiao` (string, 1-100 chars): Região da previsão (ex: "Jardim Romano")
- `nivel` (integer, 1-5): Nível de intensidade
  - 1: Sem Previsão de Chuva
  - 2: Garoa/Cuvisco
  - 3: Chuva Fraca
  - 4: Chuva Forte
  - 5: Tempestade
- `descricao` (string, 1-200 chars): Descrição textual
- `precipitacao_mm` (float, 0-300): Precipitação prevista em milímetros
- `timestamp` (string, ISO 8601, *optional*): Auto-preenchido se não fornecido

**Response:** (201 Created)
```json
{
  "ok": true,
  "message": "Previsão publicada",
  "routing_key": "previsao.jardim_romano"
}
```

**Queue:** `previsoes.fila`  
**Routing Key Pattern:** `previsao.{region}`

---

### 2. Situação Defesa Civil

**POST** `/api/v1/defesa-civil`

**Request:**
```json
{
  "status": "amarelo",
  "alertas_ativos": [
    {
      "regiao": "Zona Norte",
      "descricao": "Risco de alagamento em vias baixas",
      "severidade": "alerta"
    },
    {
      "regiao": "Zona Leste",
      "descricao": "Risco de deslizamento",
      "severidade": "critico"
    }
  ]
}
```

**Parameters:**
- `status` (string): Status geral da defesa civil
  - `verde`: Normal - Sem risco iminente
  - `amarelo`: Atenção - Risco potencial
  - `laranja`: Alerta - Risco moderado
  - `vermelho`: Crítico - Risco iminente
- `alertas_ativos` (array, max 5 items): Lista de alertas ativos
  - `regiao` (string, 1-100 chars): Região do alerta
  - `descricao` (string, 1-200 chars): Descrição do risco
  - `severidade` (string): `normal` | `atencao` | `critico`
- `timestamp` (string, ISO 8601, *optional*): Auto-preenchido se não fornecido

**Response:** (201 Created)
```json
{
  "ok": true,
  "message": "Situação Defesa Civil publicada",
  "routing_key": "situacao.geral"
}
```

**Queue:** `defesa.situacao.fila`  
**Routing Key:** `situacao.geral` (fixo)

---

### 3. Alerta Defesa Civil

**POST** `/api/v1/alertas`

**Request:**
```json
{
  "titulo": "Atenção: chuvas intensas",
  "descricao": "Previsão de chuvas intensas com possibilidade de alagamentos. Válido até 21h de hoje.",
  "regiao": "Jardim Romano",
  "valido_ate": "2026-05-10T21:00:00Z"
}
```

**Parameters:**
- `titulo` (string, 1-100 chars): Título do alerta
- `descricao` (string, 1-500 chars): Descrição detalhada
- `regiao` (string, 1-100 chars): Região do alerta (ex: "Jardim Romano")
- `valido_ate` (string, ISO 8601): Quando o alerta expira
- `timestamp` (string, ISO 8601, *optional*): Auto-preenchido se não fornecido

**Response:** (201 Created)
```json
{
  "ok": true,
  "message": "Alerta Defesa Civil publicado",
  "routing_key": "alerta.jardim_romano"
}
```

**Queue:** `defesa.alertas.fila`  
**Routing Key Pattern:** `alerta.{region}`

---

## 🧪 Exemplos com cURL

### Exemplo 1: Publicar Previsão de Chuva

```bash
curl -X POST https://sensores-pji510.unicomunitaria.com.br/api/v1/previsoes \
  -H "Content-Type: application/json" \
  -d '{
    "regiao": "Jardim Romano",
    "nivel": 4,
    "descricao": "Chuva forte com raios",
    "precipitacao_mm": 45.0
  }'
```

### Exemplo 2: Publicar Situação Defesa Civil

```bash
curl -X POST https://sensores-pji510.unicomunitaria.com.br/api/v1/defesa-civil \
  -H "Content-Type: application/json" \
  -d '{
    "status": "laranja",
    "alertas_ativos": [
      {
        "regiao": "Zona Norte",
        "descricao": "Alagamento em vias coletoras",
        "severidade": "alerta"
      }
    ]
  }'
```

### Exemplo 3: Publicar Alerta Específico

```bash
curl -X POST https://sensores-pji510.unicomunitaria.com.br/api/v1/alertas \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Atenção: chuvas intensas",
    "descricao": "Válido até 21h00 de hoje. Intensidade 4/5.",
    "regiao": "Jardim Romano",
    "valido_ate": "2026-05-10T21:00:00Z"
  }'
```

---

## 📊 Estrutura RabbitMQ

### Exchanges

| Nome | Tipo | Propósito |
|------|------|----------|
| `previsoes.exchange` | topic | Receber previsões de chuva |
| `defesa.exchange` | topic | Receber dados de defesa civil |
| `previsoes.dlx` | fanout | Dead-letter (previsões) |
| `defesa.dlx` | fanout | Dead-letter (defesa civil) |

### Queues

| Nome | TTL | Max | DLX | Binding Key |
|------|-----|-----|-----|-------------|
| `previsoes.fila` | 24h | 100k | `previsoes.dlx` | `previsao.#` |
| `previsoes.fila.dlq` | 7d | 50k | — | — |
| `defesa.situacao.fila` | 24h | 100k | `defesa.dlx` | `situacao.#` |
| `defesa.alertas.fila` | 24h | 100k | `defesa.dlx` | `alerta.#` |
| `defesa.dlq` | 7d | 50k | — | — |

### Usuários & Permissões

| Usuário | Vhost | Escrever | Ler | Propósito |
|---------|-------|----------|-----|----------|
| `sensor_producer` | `/pji510` | `sensores.*` | — | Enviar sensores |
| `simulador_app` | `/pji510` | `previsoes.*`\|`defesa.*` | — | Enviar simulações |
| `alerta_consumer` | `/pji510` | — | `sensores.*` | Consumir sensores |
| `admin` | `/pji510` | `.*` | `.*` | Administrador |

---

## 🔌 Implementar Consumer (Exemplo)

Baseado em [scripts/alerta_consumer_template.py](../scripts/alerta_consumer_template.py):

### Consumer para Previsões

```python
import asyncio
import json
import aio_pika
from aio_pika import connect_robust

async def consume_previsoes():
    connection = await connect_robust("amqp://alerta_consumer:SENHA@rabbitmq:5672//pji510")
    
    async with connection:
        channel = await connection.channel()
        
        # Declare queue (será criada se não existir)
        queue = await channel.declare_queue(
            "previsoes.fila",
            durable=True,
            auto_delete=False,
        )
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    payload = json.loads(message.body.decode())
                    
                    print(f"Previsão recebida: {payload}")
                    print(f"  Região: {payload['regiao']}")
                    print(f"  Nível: {payload['nivel']}")
                    print(f"  Descrição: {payload['descricao']}")
                    print(f"  Precipitação: {payload['precipitacao_mm']}mm")
                    
                    # Integrar sua lógica aqui
                    # Ex: armazenar em BD, enviar notificação, atualizar dashboard
                    
                    await message.ack()

if __name__ == "__main__":
    asyncio.run(consume_previsoes())
```

### Consumer para Situação Defesa Civil

```python
async def consume_defesa_civil():
    connection = await connect_robust("amqp://alerta_consumer:SENHA@rabbitmq:5672//pji510")
    
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(
            "defesa.situacao.fila",
            durable=True,
        )
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    payload = json.loads(message.body.decode())
                    
                    print(f"Situação Defesa Civil: {payload['status']}")
                    print(f"  Alertas ativos: {len(payload['alertas_ativos'])}")
                    for alerta in payload['alertas_ativos']:
                        print(f"    - {alerta['regiao']}: {alerta['descricao']} ({alerta['severidade']})")
                    
                    await message.ack()

asyncio.run(consume_defesa_civil())
```

### Consumer para Alertas Defesa Civil

```python
async def consume_alertas():
    connection = await connect_robust("amqp://alerta_consumer:SENHA@rabbitmq:5672//pji510")
    
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(
            "defesa.alertas.fila",
            durable=True,
        )
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    payload = json.loads(message.body.decode())
                    
                    print(f"🚨 Alerta: {payload['titulo']}")
                    print(f"   Região: {payload['regiao']}")
                    print(f"   Descrição: {payload['descricao']}")
                    print(f"   Válido até: {payload['valido_ate']}")
                    
                    await message.ack()

asyncio.run(consume_alertas())
```

---

## ✅ Checklist de Verificação

- [ ] RabbitMQ restart e exchanges/queues verificados
- [ ] API Bridge iniciado e 3 novos endpoints acessíveis
- [ ] Simulator UI mostra 4 abas (Sensores, Previsão, Situação, Alertas)
- [ ] Formulários preenchem corretamente
- [ ] Botões "Enviar" publicam mensagens
- [ ] RabbitMQ UI mostra mensagens nas filas respectivas
- [ ] Consumer consegue ler mensagens de cada fila
- [ ] Mensagens expiram após 24 horas (TTL)
- [ ] Dead-letter queues recebem mensagens com erro

---

## 🔧 Troubleshooting

### "Broker indisponível"
- Verificar se RabbitMQ está rodando: `docker-compose ps`
- Verificar logs: `docker-compose logs rabbitmq`
- Verificar conectividade: `telnet localhost 5672`

### "Sem permissão para escrever"
- Verificar usuário/senha no `docker-compose.yml`
- Verificar permissões em `config/definitions.json`
- Recriar usuários: `docker-compose down && docker-compose up -d`

### Mensagens não aparecem na fila
- Verificar se exchange/queue existem no RabbitMQ UI
- Verificar routing keys (devem corresponder binding key padrão)
- Verificar se consumer está ativo (precisa fazer ack)

### UI não renderiza abas
- Limpar cache: Ctrl+Shift+Delete (Browser)
- Verificar console para erros JavaScript
- Verificar arquivo `app.js` foi atualizado

---

## 📚 Referências

- [RabbitMQ Concepts](https://www.rabbitmq.com/tutorials/amqp-concepts.html)
- [aio-pika Documentation](https://aio-pika.readthedocs.io/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Estrutura Existente: Sensores](../docs/007%20-%20Modelo%20de%20Deploy%20-%20HOM.md)

---

**Última atualização**: Maio 10, 2026
