# Guia de Integração — Bombas de Drenagem × Fila PJI510

**Para:** Equipe Alerta Romano  
**De:** Equipe PJI510 (responsável pela fila RabbitMQ)  
**Data:** Maio/2026  

---

## Visão Geral

O reservatório do Piscinão Romano conta com **5 bombas de drenagem** monitoradas em tempo real. Cada bomba reporta exclusivamente seu estado operacional: **Ligada** (`1.0`) ou **Desligada** (`0.0`).

As mensagens das bombas trafegam pela **mesma fila** (`sensores.leituras`) que já é consumida pelo Alerta Romano para os sensores de nível e estações meteorológicas. **Nenhuma alteração de configuração de conexão é necessária** — basta filtrar as mensagens pelo campo `tipo_sensor == "estado_bomba"`.

---

## Sensores Disponíveis

| ID | Label | Localização | Coordenadas |
|---|---|---|---|
| `BOMBA-DRE-001` | Bomba de Drenagem 1 | Piscinao Romano - Bomba 1 | `-23.477310, -46.382610` |
| `BOMBA-DRE-002` | Bomba de Drenagem 2 | Piscinao Romano - Bomba 2 | `-23.477380, -46.382680` |
| `BOMBA-DRE-003` | Bomba de Drenagem 3 | Piscinao Romano - Bomba 3 | `-23.477450, -46.382760` |
| `BOMBA-DRE-004` | Bomba de Drenagem 4 | Piscinao Romano - Bomba 4 | `-23.477520, -46.382830` |
| `BOMBA-DRE-005` | Bomba de Drenagem 5 | Piscinao Romano - Bomba 5 | `-23.477590, -46.382910` |

---

## Informações de Fila e Roteamento

| Parâmetro | Valor |
|---|---|
| Exchange | `sensores.exchange` (topic) |
| Fila | `sensores.leituras` (a mesma dos demais sensores) |
| Routing key por bomba | `sensor.estado_bomba.<sensor_id>` |
| Vhost | `/pji510` |
| Usuário | `alerta_consumer` |

**Routing keys das 5 bombas:**

```
sensor.estado_bomba.BOMBA-DRE-001
sensor.estado_bomba.BOMBA-DRE-002
sensor.estado_bomba.BOMBA-DRE-003
sensor.estado_bomba.BOMBA-DRE-004
sensor.estado_bomba.BOMBA-DRE-005
```

Para consumir **apenas** as bombas, é possível filtrar via binding com routing key `sensor.estado_bomba.#`. Porém, como o Alerta Romano já consome `sensores.leituras` com o padrão `sensor.#`, **nenhuma configuração adicional é necessária** — as mensagens das bombas já chegam na fila existente.

---

## Estrutura da Mensagem

Cada publicação de uma bomba gera **1 mensagem** na fila `sensores.leituras`.

```json
{
  "sensor_id":          "BOMBA-DRE-001",
  "tipo_sensor":        "estado_bomba",
  "valor":              1.0,
  "unidade":            "bool",
  "timestamp":          "2026-05-13T14:30:00+00:00",
  "localizacao": {
    "latitude":         -23.47731,
    "longitude":        -46.38261,
    "descricao":        "Piscinao Romano - Bomba 1"
  },
  "status":             "normal",
  "bateria_pct":        100,
  "ativo":              true,
  "fonte_alimentacao":  "rede",
  "bms_nivel":          "normal"
}
```

### Campo `valor`

| Valor | Significado |
|---|---|
| `1.0` | Bomba **Ligada** — em operação |
| `0.0` | Bomba **Desligada** — fora de operação |

> O campo `status` é sempre `"normal"`. A interpretação do estado da bomba (se está desligada em momento crítico, por exemplo) é responsabilidade da lógica do Alerta Romano.

### Campos operacionais

Os campos operacionais seguem o mesmo schema dos demais sensores. Para as bombas de drenagem, a correspondência é:

| Campo na mensagem | Rótulo no simulador | Descrição |
|---|---|---|
| `bateria_pct` | Gerador de Emergência | Nível de carga do gerador (%) |
| `bms_nivel` | Rotação | Leitura do sensor de rotação do motor (`normal` / `alerta` / `critico`) |
| `fonte_alimentacao` | Alimentação | Fonte ativa: `rede` ou `bateria` (gerador) |

---

## Exemplo de Consumer Python

Este exemplo consome a fila existente e filtra as mensagens das bombas de drenagem:

```python
import asyncio
import json
import os
import aio_pika

async def processar_estado_bomba(dados: dict) -> None:
    sensor_id = dados["sensor_id"]
    ligada = dados["valor"] == 1.0
    estado = "LIGADA" if ligada else "DESLIGADA"
    print(f"[{sensor_id}] Bomba {estado}")
    # Implemente aqui: salvar no banco, disparar alerta, etc.

async def processar_mensagem(dados: dict) -> None:
    if dados.get("tipo_sensor") == "estado_bomba":
        await processar_estado_bomba(dados)
    # outros tipo_sensor são ignorados aqui

async def main():
    connection = await aio_pika.connect_robust(
        host=os.getenv("RABBITMQ_HOST", "rabbitmq"),   # "127.0.0.1" se não usar Docker
        port=5672,
        virtualhost="/pji510",
        login="alerta_consumer",
        password=os.getenv("ALERTA_CONSUMER_PASS"),
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
                        await processar_mensagem(dados)
                    except json.JSONDecodeError:
                        pass  # mensagem inválida → vai para DLQ automaticamente

asyncio.run(main())
```

---

## Como Usar o Simulador

O simulador web (porta `8084`) exibe os 5 cards de bomba na aba **Sensores**.

Cada card de bomba contém:

| Controle | Descrição |
|---|---|
| **Estado da Bomba** | Select com opções `Ligada` / `Desligada`. Alterar o select atualiza o estado imediatamente. |
| **Estado** | Select `Ligado` / `Desligado` — controla se o sensor está **ativo para envio**. Quando desligado, o botão Enviar é bloqueado. |
| **Alimentação** | Select `Rede elétrica` / `Gerador de Emergência` — fonte de energia ativa da bomba. |
| **Gerador de Emergência** | Percentual de carga do gerador (0–100%). |
| **Rotação** | Sensor de rotação do motor: `normal`, `alerta` ou `critico`. |
| **Randomizar** | Alterna o estado da bomba aleatoriamente (útil para testes automatizados). |
| **Enviar** | Publica o estado atual da bomba na fila `sensores.leituras`. |

**Fluxo típico de uso:**

1. Na aba **Sensores**, localize os cards `BOMBA-DRE-001` até `BOMBA-DRE-005`.
2. No select **Estado da Bomba**, escolha `Ligada` ou `Desligada`.
3. Clique em **Enviar** para publicar o estado na fila.
4. Verifique o resultado no painel **Último envio** (JSON de confirmação).

O **Modo Automático** também inclui as bombas: ao ativar o envio automático, o simulador randomiza e publica o estado de todas as bombas no intervalo configurado.

---

## Verificação no RabbitMQ Management

Acesse a interface web do RabbitMQ (porta `8093`) e vá em:

**Queues → sensores.leituras → Get Messages**

Filtre visualmente as mensagens com `"tipo_sensor": "estado_bomba"` para confirmar que os eventos das bombas estão chegando corretamente.

Para verificar o routing key, observe o campo **Routing key** na visualização da mensagem — deve aparecer no formato `sensor.estado_bomba.BOMBA-DRE-00X`.

---

## Referências

- [006 - Guia de Integração - Alerta Romano.md](006%20-%20Guia%20de%20Integração%20-%20Alerta%20Romano.md) — Conexão AMQP, credenciais e exemplos gerais
- [009 - Integração de Simulações.md](009%20-%20Integração%20de%20Simulações.md) — Previsão de chuva, Situação e Alertas da Defesa Civil
- [lista-sensores.md](../lista-sensores.md) — Catálogo completo de sensores e routing keys
