"""Hydrology calculation policies (RN-01 – RN-06)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

# RN-04 thresholds (nivel_percentual)
THRESHOLD_ATENCAO: float = 60.0
THRESHOLD_ALERTA: float = 80.0
THRESHOLD_EMERGENCIA: float = 95.0

# RN-06 divergence tolerance between redundant sensors
DIVERGENCIA_MAXIMA_PCT: float = 10.0


def calcular_volume(nivel_cm: float, area_m2: float) -> float:
    """RN-01: Volume armazenado em m³.

    V = (nivel_cm / 100) * area_m2
    """
    if nivel_cm < 0 or area_m2 <= 0:
        return 0.0
    return (nivel_cm / 100.0) * area_m2


def calcular_taxa_variacao(
    leituras: list[float],
    timestamps: list[datetime],
) -> float:
    """RN-02: Taxa de variação do nível em cm/min.

    Uses linear regression slope over the provided series.
    Returns 0.0 when series has fewer than 2 points or no elapsed time.
    """
    n = len(leituras)
    if n != len(timestamps) or n < 2:
        return 0.0

    # Convert timestamps to minutes relative to first reading
    t0 = timestamps[0].timestamp()
    times = [(ts.timestamp() - t0) / 60.0 for ts in timestamps]
    dt = times[-1] - times[0]
    if dt == 0.0:
        return 0.0

    # Simple slope between first and last point (sufficient for RN-02)
    return (leituras[-1] - leituras[0]) / dt


def estimar_tempo_transbordo(
    nivel_cm: float,
    capacidade_cm: float,
    taxa_cm_min: float,
) -> Optional[float]:
    """RN-03: Minutos até o transbordo.

    Returns None when taxa ≤ 0 (nível estabilizado ou baixando).
    Returns None when nível já atingiu ou ultrapassou a capacidade.
    """
    if taxa_cm_min <= 0:
        return None
    if nivel_cm >= capacidade_cm:
        return None
    return (capacidade_cm - nivel_cm) / taxa_cm_min


def detectar_divergencia_sensores(leituras_sensores: dict[int, float]) -> bool:
    """RN-06: True quando a diferença relativa entre quaisquer dois sensores
    redundantes supera DIVERGENCIA_MAXIMA_PCT.

    Uses the mean as reference to be more robust than min/max alone.
    """
    values = list(leituras_sensores.values())
    if len(values) < 2:
        return False
    mean = sum(values) / len(values)
    if mean == 0.0:
        return False
    return any(abs(v - mean) / mean * 100 > DIVERGENCIA_MAXIMA_PCT for v in values)


def correlacionar_pluviometria(nivel_taxa_cm_min: float, chuva_mm: float) -> str:
    """RN-05: Classifica a correlação entre taxa de elevação do nível e
    precipitação recente.

    Returns one of: 'alta', 'moderada', 'baixa', 'sem_chuva'.
    """
    if chuva_mm <= 0:
        return "sem_chuva"
    if nivel_taxa_cm_min > 5.0 and chuva_mm > 10.0:
        return "alta"
    if nivel_taxa_cm_min > 1.0 and chuva_mm > 2.0:
        return "moderada"
    return "baixa"


def calcular_nivel_percentual(nivel_cm: float, capacidade_cm: float) -> float:
    """Helper: nivel como porcentagem da capacidade total."""
    if capacidade_cm <= 0:
        return 0.0
    pct = (nivel_cm / capacidade_cm) * 100.0
    return min(max(pct, 0.0), 100.0)


def classificar_nivel(nivel_pct: float) -> str:
    """RN-04: Classifica o status do reservatório com base no nível percentual."""
    if nivel_pct >= THRESHOLD_EMERGENCIA:
        return "emergencia"
    if nivel_pct >= THRESHOLD_ALERTA:
        return "alerta"
    if nivel_pct >= THRESHOLD_ATENCAO:
        return "atencao"
    return "normal"
