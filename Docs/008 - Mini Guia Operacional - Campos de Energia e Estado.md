# Mini Guia Operacional - Campos de Energia e Estado

## Objetivo

Este guia descreve como usar os novos campos operacionais no simulador de sensores do projeto Alerta Romano.

Escopo:
- estado do sensor (ligado/desligado)
- fonte de alimentacao (rede/bateria)
- nivel de bateria e BMS

---

## Campos Novos

| Campo | Tipo | Valores | Uso operacional |
|---|---|---|---|
| `ativo` | boolean | `true` / `false` | Indica se o sensor esta ligado e apto para enviar leituras |
| `fonte_alimentacao` | string | `rede` / `bateria` | Fonte eletrica atual do dispositivo |
| `bateria_pct` | inteiro | `0` a `100` | Carga estimada da bateria |
| `bms_nivel` | string | `normal` / `alerta` / `critico` | Estado de saude/risco informado pelo BMS |

Regra importante:
- Se `ativo=false`, o envio de leitura e bloqueado pelo simulador.

---

## Onde configurar na tela

Em cada card de sensor, a equipe pode ajustar:
1. Estado: Ligado/Desligado
2. Alimentacao: Rede eletrica/Bateria emergencia
3. Bateria: valor percentual (0-100)
4. BMS: nivel textual (normal/alerta/critico)

Ao clicar em Enviar, esses campos seguem no payload para a fila RabbitMQ.

---

## Comportamento esperado

### 1) Sensor desligado

Condicao:
- `ativo=false`

Resultado esperado:
- Botao de envio desabilitado na interface
- Tentativa de envio retorna bloqueio no backend

### 2) Sensor ligado na rede

Condicao:
- `ativo=true`
- `fonte_alimentacao=rede`

Resultado esperado:
- envio normal de leituras
- `bms_nivel` tende a permanecer `normal`

### 3) Sensor ligado na bateria

Condicao:
- `ativo=true`
- `fonte_alimentacao=bateria`

Resultado esperado:
- envio normal de leituras
- `bateria_pct` e `bms_nivel` devem ser monitorados

Sugestao de leitura de risco:
- `bms_nivel=normal`: operacao estavel
- `bms_nivel=alerta`: planejar manutencao/intervencao
- `bms_nivel=critico`: tratar como prioridade operacional

---

## Exemplos de uso em teste

### Cenario A - Falha de energia local com bateria ativa

Configurar:
- `ativo=true`
- `fonte_alimentacao=bateria`
- `bateria_pct=22`
- `bms_nivel=alerta`

Validar:
- mensagem chega na fila com os 4 campos novos

### Cenario B - Sensor fora de operacao

Configurar:
- `ativo=false`

Validar:
- simulador bloqueia envio desse sensor

### Cenario C - Risco critico de bateria

Configurar:
- `ativo=true`
- `fonte_alimentacao=bateria`
- `bateria_pct=10`
- `bms_nivel=critico`

Validar:
- mensagem publicada com risco explicito para o consumidor

---

## Checklist rapido para operacao diaria

1. Confirmar se sensor esta `ativo=true` antes de iniciar testes.
2. Definir `fonte_alimentacao` conforme cenario que sera simulado.
3. Ajustar `bateria_pct` e `bms_nivel` para representar condicao realista.
4. Enviar leitura e confirmar consumo na fila `sensores.leituras`.
5. Verificar no payload recebido se os campos novos estao presentes.

---

## Payload de referencia

```json
{
  "sensor_id": "SENSOR-RES-001",
  "tipo_sensor": "nivel_agua",
  "valor": 3.72,
  "unidade": "m",
  "timestamp": "2026-05-07T22:00:00+00:00",
  "localizacao": {
    "latitude": -23.477448639552904,
    "longitude": -46.38281519942896,
    "descricao": "Piscinao Romano - Norte"
  },
  "status": "normal",
  "bateria_pct": 22,
  "ativo": true,
  "fonte_alimentacao": "bateria",
  "bms_nivel": "alerta"
}
```

---

## Referencias

- Simulador (UI + regras): `sensor_simulator/`
- Contrato da API bridge: `api_bridge/main.py`
- Guia de integracao consumidor: `docs/006 - Guia de Integracao - Alerta Romano.md`
