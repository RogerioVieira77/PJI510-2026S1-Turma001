# Guia de Integração — Alerta Romano × Fila PJI510

**Para:** Equipe Alerta Romano  
**De:** Equipe PJI510 (responsável pela fila RabbitMQ)  
**Data:** Maio/2026  

---

## Informações de Conexão

| Parâmetro       | Valor                    | Observação                            |
|-----------------|--------------------------|---------------------------------------|
| Protocolo       | AMQP 0-9-1               | Sem TLS (conexão interna ao servidor) |
| Host            | `rabbitmq`               | Se o app rodar em Docker (ver abaixo) |
| Host alternativo| `127.0.0.1`              | Se o app rodar direto no servidor     |
| Porta           | `5672`                   | Porta padrão AMQP, sem TLS            |
| Virtual Host    | `/pji510`                | Obrigatório informar no client        |
| Fila            | `sensores.leituras`      | Fila principal de leituras            |
| Exchange        | `sensores.exchange`      | Tipo: topic                           |
| Routing key     | `sensor.#`               | Recebe todos os tipos de sensor       |
| Usuário         | `alerta_consumer`        | A senha será enviada pela equipe PJI510 por canal seguro |
| Dead Letter Q   | `sensores.leituras.dlq`  | Mensagens rejeitadas 3x vão aqui      |

> A porta AMQP **não está exposta à internet**. O acesso é exclusivamente interno ao servidor `srv1312297`.

---

## Como o app Alerta Romano deve se conectar

### Opção A — App em Docker (recomendado)

Se o Alerta Romano rodar como container Docker, adicione a rede `pji510` ao seu `docker-compose.yml` como rede **externa**. Assim os containers se comunicam diretamente, sem expor nenhuma porta no host.

**No `docker-compose.yml` do Alerta Romano:**

```yaml
services:
  alerta_romano:            # nome do seu serviço
    # ... configurações existentes do serviço ...
    networks:
      - sua_rede_interna    # rede interna que você já usa
      - pji510              # adicione esta linha

networks:
  sua_rede_interna:         # declaração da sua rede existente
    # ... mantém como está ...
  pji510:
    external: true          # referencia a rede criada pela equipe PJI510
```

Com isso, dentro do container o broker fica acessível em:
- **Host:** `rabbitmq`
- **Porta:** `5672`

### Opção B — App rodando diretamente no servidor (sem Docker)

Se o Alerta Romano rodar como processo Python diretamente no servidor (sem Docker):
- **Host:** `127.0.0.1`
- **Porta:** `5672`

---

## Exemplo de conexão com Python (aio-pika)

Dependência: `pip install aio-pika`

```python
import asyncio
import json
import os
import aio_pika

async def processar_leitura(dados: dict) -> None:
    """Implemente aqui a lógica do Alerta Romano."""
    print(f"[{dados['sensor_id']}] {dados['tipo_sensor']} = {dados['valor']} {dados['unidade']}")
    # Avalie regras de alerta, salve no banco, dispare notificações, etc.

async def main():
    connection = await aio_pika.connect_robust(
        host=os.getenv("RABBITMQ_HOST", "rabbitmq"),   # "127.0.0.1" se não usar Docker
        port=5672,
        virtualhost="/pji510",
        login="alerta_consumer",
        password=os.getenv("ALERTA_CONSUMER_PASS"),    # senha via variável de ambiente
    )

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.get_queue("sensores.leituras")

        async with queue.iterator() as messages:
            async for message in messages:
                async with message.process(requeue=False):
                    try:
                        dados = json.loads(message.body.decode())
                        await processar_leitura(dados)
                    except json.JSONDecodeError:
                        pass  # mensagem inválida → vai para DLQ automaticamente

asyncio.run(main())
```

---

## Estrutura da mensagem recebida

Cada mensagem na fila `sensores.leituras` tem o seguinte formato JSON:

```json
{
  "sensor_id":   "SENSOR-RES-001",
  "tipo_sensor": "nivel_agua",
  "valor":       3.72,
  "unidade":     "metros",
  "timestamp":   "2026-04-15T14:30:00+00:00",
  "localizacao": {
    "latitude":  -23.5505,
    "longitude": -46.6333,
    "descricao": "Reservatório Norte - Ponto A"
  },
  "status":      "normal",
  "bateria_pct": 87
}
```

**Valores possíveis de `tipo_sensor`:**

| Valor          | Unidade | Descrição                          |
|----------------|---------|------------------------------------|
| `nivel_agua`   | metros  | Nível da água no reservatório      |
| `vazao`        | m³/s    | Vazão de entrada/saída             |
| `pluviometro`  | mm/h    | Índice pluviométrico na região     |
| `pressao`      | kPa     | Pressão na tubulação               |
| `temperatura`  | °C      | Temperatura da água                |

**Valores possíveis de `status`:** `normal` · `alerta` · `critico` · `erro`

**Routing key da mensagem:** `sensor.<tipo_sensor>.<sensor_id>`  
Exemplo: `sensor.nivel_agua.SENSOR-RES-001`

---

## Procedimento de teste — Validar se estão "enxergando" a fila

Execute os passos abaixo no servidor `srv1312297` para confirmar que a conexão e o consumo funcionam.

### Pré-requisito

```bash
pip install aio-pika    # ou: pip3 install aio-pika
```

### Passo 1 — Testar conectividade de rede

Verifique se a porta AMQP está alcançável (substitua `<HOST>` por `rabbitmq` ou `127.0.0.1`):

```bash
python3 -c "
import socket
s = socket.create_connection(('<HOST>', 5672), timeout=5)
s.close()
print('OK: porta 5672 alcançável')
"
```

Se receber `OK`, a rede está correta. Se der `Connection refused` ou timeout, entre em contato com a equipe PJI510.

### Passo 2 — Testar autenticação e acesso à fila

Crie o arquivo `teste_conexao.py` e execute:

```python
# teste_conexao.py
import asyncio
import aio_pika

RABBITMQ_HOST = "rabbitmq"   # ou "127.0.0.1"
RABBITMQ_PASS = "SENHA_FORNECIDA_PELO_TIME_PJI510"

async def main():
    try:
        conn = await aio_pika.connect(
            host=RABBITMQ_HOST,
            port=5672,
            virtualhost="/pji510",
            login="alerta_consumer",
            password=RABBITMQ_PASS,
            timeout=10,
        )
        channel = await conn.channel()
        queue = await channel.get_queue("sensores.leituras")
        info = await queue.declare(passive=True)
        print(f"OK: conectado! Mensagens na fila: {info.message_count}")
        await conn.close()
    except Exception as e:
        print(f"ERRO: {e}")

asyncio.run(main())
```

```bash
python3 teste_conexao.py
```

**Resultado esperado:**
```
OK: conectado! Mensagens na fila: <N>
```

### Passo 3 — Consumir uma mensagem de teste

A equipe PJI510 pode publicar uma mensagem de teste pelo Management UI ou pelo script `make test-producer`. Depois execute:

```python
# teste_consumo.py
import asyncio, json
import aio_pika

RABBITMQ_HOST = "rabbitmq"   # ou "127.0.0.1"
RABBITMQ_PASS = "SENHA_FORNECIDA_PELO_TIME_PJI510"

async def main():
    conn = await aio_pika.connect(
        host=RABBITMQ_HOST, port=5672,
        virtualhost="/pji510",
        login="alerta_consumer", password=RABBITMQ_PASS,
    )
    async with conn:
        channel = await conn.channel()
        queue = await channel.get_queue("sensores.leituras")
        message = await queue.get(timeout=10, fail=False)
        if message:
            async with message.process():
                dados = json.loads(message.body)
                print("Mensagem recebida:")
                print(json.dumps(dados, indent=2, ensure_ascii=False))
        else:
            print("Fila vazia — peça à equipe PJI510 para publicar uma mensagem de teste.")

asyncio.run(main())
```

```bash
python3 teste_consumo.py
```

---

## Política de ack/nack

A equipe Alerta Romano é responsável por confirmar (ack) cada mensagem após processá-la com sucesso.

| Situação                            | Ação esperada               | Resultado                         |
|-------------------------------------|-----------------------------|-----------------------------------|
| Processamento bem-sucedido          | `ack`                       | Mensagem removida da fila         |
| Erro transitório (ex: banco fora)   | `nack` com `requeue=True`   | Mensagem volta para o início da fila |
| Erro permanente (ex: JSON inválido) | `nack` com `requeue=False`  | Mensagem vai para `sensores.leituras.dlq` |

> Após **3 nacks consecutivos** sem requeue, a mensagem vai automaticamente para a Dead Letter Queue (`sensores.leituras.dlq`) onde fica retida por **7 dias** para análise.

---

## Contato — Equipe PJI510

Dúvidas sobre a fila, credenciais, ou testes de conectividade: abrir chamado / mensagem direta para a equipe PJI510.

Acesso ao Management UI (monitoramento de filas): `https://rabbitmq-pji510.unicomunitaria.com.br`  
*(credenciais de acesso à UI fornecidas separadamente)*