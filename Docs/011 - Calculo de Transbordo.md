# Transbordo estimado

Mostra uma estrutura prática em Python, de como fazer a implementação do calculo do transbordo.


## A lógica

1 - Ler a altura atual do sensor
2 - Comparar com a altura anterior
3 - Calcular:
-  variação de altura dh
-  intervalo de tempo dt
- taxa de preenchimento
4 - Converter para:
- m³/h
- litros/h

## Fórmula usada

dt/dV = 1600*dt/dh

Onde:
- Área = 50×50=2500m2
- dh/dt = velocidade de subida da água

## Exemplo em Python

```python
import time

# Área da base do reservatório (m²)
AREA = 1600

# Altura inicial lida pelo sensor (metros)
altura_anterior = 2.50

# Tempo inicial
tempo_anterior = time.time()

while True:

    # =========================
    # SIMULAÇÃO DO SENSOR
    # =========================
    # Aqui você substituirá pela leitura real do sensor
    altura_atual = float(input("Altura atual da água (m): "))

    # Tempo atual
    tempo_atual = time.time()

    # Diferença de altura
    dh = altura_atual - altura_anterior

    # Diferença de tempo em horas
    dt = (tempo_atual - tempo_anterior) / 3600

    # Evita divisão por zero
    if dt > 0:

        # Taxa de variação da altura
        dh_dt = dh / dt

        # Vazão em m³/h
        vazao_m3_h = AREA * dh_dt

        # Vazão em litros/h
        vazao_l_h = vazao_m3_h * 1000

        print("\n===== RESULTADOS =====")
        print(f"Variação da altura: {dh:.4f} m")
        print(f"Taxa de subida: {dh_dt:.4f} m/h")
        print(f"Vazão: {vazao_m3_h:.2f} m³/h")
        print(f"Vazão: {vazao_l_h:.2f} L/h")

    # Atualiza valores
    altura_anterior = altura_atual
    tempo_anterior = tempo_atual

    print("----------------------\n")
```
Substituir no código pelos valores de leitura do sensores.

Você substituiria:

- altura_atual = float(input(...))

por algo como:

- altura_atual = sensor.read()
 
## Calculos

Calculos que devemos fazer: 

- taxa de enchimento
- taxa de drenagem
- previsão de transbordamento
- tempo até esvaziar
- eficiência das bombas


## Exemplo real

Se:

altura sobe 1 cm em 1 minuto

Então:

dh=0,01m
dt= 1/60h

dh/dt = 0,6m/h

Logo:

2500×0,6=1500m3/h
1500.000L/h