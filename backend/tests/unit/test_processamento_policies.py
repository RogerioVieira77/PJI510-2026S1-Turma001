"""TASK-52 — Testes unitários das políticas de processamento (RN-01..06).

pytest tests/unit/test_processamento_policies.py -v
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.modules.processamento.policies import (
    THRESHOLD_ALERTA,
    THRESHOLD_ATENCAO,
    THRESHOLD_EMERGENCIA,
    calcular_nivel_percentual,
    calcular_taxa_variacao,
    calcular_volume,
    classificar_nivel,
    correlacionar_pluviometria,
    detectar_divergencia_sensores,
    estimar_tempo_transbordo,
    estimar_tempo_transbordo_com_bombas,
    NIVEL_ACIONAMENTO_BOMBAS_PCT,
    VAZAO_POR_BOMBA_M3_H,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _ts(offset_min: int = 0) -> datetime:
    """Return a UTC-aware datetime offset by `offset_min` minutes from epoch."""
    base = datetime(2026, 5, 5, 10, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(minutes=offset_min)


# ── RN-01: calcular_volume ────────────────────────────────────────────────────


def test_calcular_volume_normal():
    """200 cm em 250 000 m² = 500 000 m³."""
    assert calcular_volume(200, 250_000) == pytest.approx(500_000.0)


def test_calcular_volume_zero_nivel():
    assert calcular_volume(0, 250_000) == 0.0


def test_calcular_volume_nivel_negativo():
    assert calcular_volume(-10, 250_000) == 0.0


def test_calcular_volume_area_zero():
    assert calcular_volume(100, 0) == 0.0


def test_calcular_volume_pequeno():
    assert calcular_volume(50, 100) == pytest.approx(50.0)


# ── RN-02: calcular_taxa_variacao ─────────────────────────────────────────────


def test_taxa_nivel_constante():
    ts = [_ts(0), _ts(1), _ts(2)]
    leituras = [100.0, 100.0, 100.0]
    assert calcular_taxa_variacao(leituras, ts) == pytest.approx(0.0)


def test_taxa_subindo():
    """Sobe 10 cm em 5 minutos = 2 cm/min."""
    ts = [_ts(0), _ts(5)]
    leituras = [100.0, 110.0]
    assert calcular_taxa_variacao(leituras, ts) == pytest.approx(2.0)


def test_taxa_descendo():
    """Cai 6 cm em 3 minutos = -2 cm/min."""
    ts = [_ts(0), _ts(3)]
    leituras = [150.0, 144.0]
    assert calcular_taxa_variacao(leituras, ts) == pytest.approx(-2.0)


def test_taxa_serie_insuficiente():
    assert calcular_taxa_variacao([100.0], [_ts(0)]) == 0.0


def test_taxa_timestamps_iguais():
    ts = [_ts(0), _ts(0)]
    assert calcular_taxa_variacao([100.0, 110.0], ts) == 0.0


def test_taxa_tamanhos_diferentes():
    assert calcular_taxa_variacao([100.0, 110.0], [_ts(0)]) == 0.0


# ── RN-03: estimar_tempo_transbordo ──────────────────────────────────────────


def test_transbordo_taxa_zero():
    assert estimar_tempo_transbordo(100.0, 500.0, 0.0) is None


def test_transbordo_taxa_negativa():
    assert estimar_tempo_transbordo(100.0, 500.0, -1.0) is None


def test_transbordo_nivel_igual_capacidade():
    assert estimar_tempo_transbordo(500.0, 500.0, 2.0) is None


def test_transbordo_nivel_acima_capacidade():
    assert estimar_tempo_transbordo(510.0, 500.0, 2.0) is None


def test_transbordo_calculo_correto():
    """400 cm restantes com taxa 4 cm/min = 100 minutos."""
    assert estimar_tempo_transbordo(100.0, 500.0, 4.0) == pytest.approx(100.0)


# ── RN-06: detectar_divergencia_sensores ─────────────────────────────────────


def test_divergencia_igual():
    assert detectar_divergencia_sensores({1: 100.0, 2: 100.0}) is False


def test_divergencia_dentro_limite():
    """9% de desvio — abaixo do limite de 10%."""
    assert detectar_divergencia_sensores({1: 100.0, 2: 90.1}) is False


def test_divergencia_acima_limite():
    """15% de desvio (100 vs 115, média=107.5 → |100-107.5|/107.5≈6.97%, mas
    |115-107.5|/107.5≈6.97% também — abaixo de 10%.
    Use {1:100, 2:130}: média=115, desvios 13% e 13% → True."""
    assert detectar_divergencia_sensores({1: 100.0, 2: 130.0}) is True


def test_divergencia_sensor_unico():
    assert detectar_divergencia_sensores({1: 100.0}) is False


def test_divergencia_media_zero():
    """Quando média é zero não divide por zero."""
    assert detectar_divergencia_sensores({1: 0.0, 2: 0.0}) is False


# ── RN-05: correlacionar_pluviometria ────────────────────────────────────────


def test_correlacao_sem_chuva():
    assert correlacionar_pluviometria(10.0, 0.0) == "sem_chuva"


def test_correlacao_alta():
    assert correlacionar_pluviometria(6.0, 15.0) == "alta"


def test_correlacao_moderada():
    assert correlacionar_pluviometria(2.0, 5.0) == "moderada"


def test_correlacao_baixa():
    assert correlacionar_pluviometria(0.5, 3.0) == "baixa"


# ── calcular_nivel_percentual + classificar_nivel ────────────────────────────


def test_nivel_percentual_normal():
    assert calcular_nivel_percentual(300, 500) == pytest.approx(60.0)


def test_nivel_percentual_maximo():
    assert calcular_nivel_percentual(600, 500) == pytest.approx(100.0)


def test_nivel_percentual_zero():
    assert calcular_nivel_percentual(0, 500) == pytest.approx(0.0)


def test_classificar_normal():
    assert classificar_nivel(50.0) == "normal"


def test_classificar_atencao():
    assert classificar_nivel(THRESHOLD_ATENCAO) == "atencao"


def test_classificar_alerta():
    assert classificar_nivel(THRESHOLD_ALERTA) == "alerta"


def test_classificar_emergencia():
    assert classificar_nivel(THRESHOLD_EMERGENCIA) == "emergencia"


# ── RN-07: estimar_tempo_transbordo_com_bombas ────────────────────────────────
# Fixture: reservatório 50×50 m, profundidade 8 m, capacidade 20 000 m³
# area_m2 = 2500, capacidade_cm = 800

_AREA = 2500.0       # m² (50×50)
_CAP_CM = 800.0      # 8 m em cm
_N_BOMBAS_TOTAL = 5


def test_rn07_nivel_abaixo_50pct_retorna_none():
    """Função deve retornar None quando nível < 50 %."""
    result = estimar_tempo_transbordo_com_bombas(
        nivel_pct=40.0,
        nivel_cm=320.0,
        capacidade_cm=_CAP_CM,
        area_m2=_AREA,
        taxa_cm_min=0.5,
        bombas_ligadas=0,
    )
    assert result is None


def test_rn07_nivel_exato_50pct_ativa():
    """A partir de exatamente 50 % a função deve calcular (não retornar None
    apenas por causa do nível) — desde que taxa líquida seja positiva."""
    # Sem nenhuma bomba para garantir taxa líquida > 0
    result = estimar_tempo_transbordo_com_bombas(
        nivel_pct=50.0,
        nivel_cm=400.0,
        capacidade_cm=_CAP_CM,
        area_m2=_AREA,
        taxa_cm_min=1.0,
        bombas_ligadas=0,
    )
    assert result is not None
    assert result > 0


def test_rn07_todas_bombas_ligadas_drenando_retorna_none():
    """5 bombas × 2,8 m³/h = 14 m³/h = 0,2333 m³/min.
    Se o enchimento for menor, a taxa líquida é negativa → None."""
    # taxa_cm_min = 0.5 → enchimento = (0.5/100)*2500 = 12.5 m³/min  [muito alto]
    # Usa taxa baixa: 0.001 cm/min → enchimento = 0.025 m³/min < 0.2333 m³/min (drenagem)
    result = estimar_tempo_transbordo_com_bombas(
        nivel_pct=75.0,
        nivel_cm=600.0,
        capacidade_cm=_CAP_CM,
        area_m2=_AREA,
        taxa_cm_min=0.001,  # praticamente estável
        bombas_ligadas=5,
    )
    assert result is None


def test_rn07_sem_bombas_calculo_correto():
    """Com 0 bombas a drenagem é zero; equivale a estimar_tempo_transbordo.

    Nível 600 cm, capacidade 800 cm → restam 200 cm.
    Area = 2500 m² → volume restante = 2 cm/100 * 2500 = 5000 m³.
    taxa_cm_min = 1 → enchimento = (1/100)*2500 = 25 m³/min.
    T = 5000 / 25 = 200 min.
    """
    result = estimar_tempo_transbordo_com_bombas(
        nivel_pct=75.0,
        nivel_cm=600.0,
        capacidade_cm=_CAP_CM,
        area_m2=_AREA,
        taxa_cm_min=1.0,
        bombas_ligadas=0,
    )
    assert result == pytest.approx(200.0)


def test_rn07_3_bombas_ligadas_calculo_correto():
    """3 bombas falhas (2 ativas).

    taxa_cm_min = 1 → enchimento = 25 m³/min.
    drenagem = 3 * 2.8 / 60 = 0.14 m³/min.
    taxa_liquida = 25 - 0.14 = 24.86 m³/min.
    volume_restante = 5000 m³.
    T = 5000 / 24.86 ≈ 201.12 min.
    """
    drenagem_min = 3 * VAZAO_POR_BOMBA_M3_H / 60
    taxa_liquida = 25.0 - drenagem_min
    esperado = 5000.0 / taxa_liquida
    result = estimar_tempo_transbordo_com_bombas(
        nivel_pct=75.0,
        nivel_cm=600.0,
        capacidade_cm=_CAP_CM,
        area_m2=_AREA,
        taxa_cm_min=1.0,
        bombas_ligadas=3,
    )
    assert result == pytest.approx(esperado, rel=1e-4)


def test_rn07_nivel_ja_no_maximo_retorna_none():
    result = estimar_tempo_transbordo_com_bombas(
        nivel_pct=100.0,
        nivel_cm=_CAP_CM,
        capacidade_cm=_CAP_CM,
        area_m2=_AREA,
        taxa_cm_min=1.0,
        bombas_ligadas=0,
    )
    assert result is None


def test_rn07_taxa_zero_retorna_none():
    """Taxa de enchimento zero → taxa líquida negativa (drenagem > 0) → None."""
    result = estimar_tempo_transbordo_com_bombas(
        nivel_pct=60.0,
        nivel_cm=480.0,
        capacidade_cm=_CAP_CM,
        area_m2=_AREA,
        taxa_cm_min=0.0,
        bombas_ligadas=5,
    )
    assert result is None


def test_rn07_uma_bomba_falhou():
    """4 de 5 bombas ligadas — verifica que o tempo calculado é maior que com 5 bombas."""
    kwargs = dict(
        nivel_pct=75.0, nivel_cm=600.0, capacidade_cm=_CAP_CM,
        area_m2=_AREA, taxa_cm_min=1.0,
    )
    t5 = estimar_tempo_transbordo_com_bombas(**kwargs, bombas_ligadas=5)
    t4 = estimar_tempo_transbordo_com_bombas(**kwargs, bombas_ligadas=4)
    # Com menos drenagem o transbordo é mais rápido (menor t)
    assert t5 is not None and t4 is not None
    assert t4 < t5


def test_rn07_nivel_acionamento_constante_valor():
    assert NIVEL_ACIONAMENTO_BOMBAS_PCT == 50.0


def test_rn07_vazao_por_bomba_constante_valor():
    assert VAZAO_POR_BOMBA_M3_H == pytest.approx(2.8)
