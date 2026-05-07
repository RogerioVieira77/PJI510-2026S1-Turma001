# Lista de Sensores — PJI510 2026/S1

## Sensores de Nível de Água

| ID | Label | Localização | Métrica | Faixa |
|---|---|---|---|---|
| `SENSOR-RES-001` | Sensor de Nivel 1 | Piscinão Norte | `nivel_agua` | 0 – 8 m |
| `SENSOR-RES-002` | Sensor de Nivel 2 | Piscinão Sul | `nivel_agua` | 0 – 8 m |

**Coordenadas:**

- `SENSOR-RES-001`: latitude `-23.5505`, longitude `-46.6333`
- `SENSOR-RES-002`: latitude `-23.5510`, longitude `-46.6338`

---

## Estações Meteorológicas

| ID | Label | Localização |
|---|---|---|
| `ESTACAO-MET-001` | Estacao Meteorologica 1 | Estação Oeste |
| `ESTACAO-MET-002` | Estacao Meteorologica 2 | Estação Leste |

**Coordenadas:**

- `ESTACAO-MET-001`: latitude `-23.5499`, longitude `-46.6325`
- `ESTACAO-MET-002`: latitude `-23.5520`, longitude `-46.6350`

### Métricas das Estações Meteorológicas

| Tipo (`tipo_sensor`) | Unidade | Faixa |
|---|---|---|
| `vento_direcao` | graus | 0 – 359 |
| `vento_velocidade` | km/h | 0 – 180 |
| `pluviometro` | mm | 0 – 300 |
| `temperatura` | °C | −40 – 60 |
| `umidade` | % | 10 – 99 |
| `pressao` | hPa | 800 – 1100 |

> Cada envio de uma estação meteorológica gera **6 mensagens separadas** no RabbitMQ, uma por tipo de métrica.

---

## Routing Keys (RabbitMQ)

Formato: `sensores.<tipo_sensor>.<sensor_id>`

Exemplos:

- `sensores.nivel_agua.SENSOR-RES-001`
- `sensores.nivel_agua.SENSOR-RES-002`
- `sensores.temperatura.ESTACAO-MET-001`
- `sensores.pluviometro.ESTACAO-MET-002`

Exchange: `sensores.exchange` (topic)  
Vhost: `/pji510`
