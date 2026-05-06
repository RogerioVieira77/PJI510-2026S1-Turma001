"""HTTP clients para dados clim\u00e1ticos \u2014 TASK-110.

Hierarquia de fallback:
    CPTECClient  \u2192  OpenWeatherClient  \u2192  ClimaServiceException
"""
from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from decimal import Decimal

import httpx
import structlog

from app.config import get_settings
from app.modules.clima.schemas import PrevisaoClimatica

log = structlog.get_logger()
_settings = get_settings()

_TIMEOUT = 5.0
_MAX_RETRIES = 2
_BACKOFF = 1.0

# CPTEC: previs\u00e3o por coordenada geogr\u00e1fica
_CPTEC_URL = (
    "http://servicos.cptec.inpe.br/XML/cidade/{lat}/{lon}/previsaoLocalidade.xml"
)
# OpenWeatherMap: dados atuais
_OWM_URL = "https://api.openweathermap.org/data/2.5/weather"


class ClimaServiceException(Exception):
    """Lan\u00e7ada quando todos os clients falharam."""


async def _get_with_retry(url: str, params: dict | None = None) -> httpx.Response:
    """GET com timeout de 5 s e at\u00e9 2 retentativas com backoff exponencial."""
    last_exc: Exception | None = None
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(_BACKOFF * (2**attempt))
    raise ClimaServiceException(str(last_exc)) from last_exc  # type: ignore[arg-type]


class CPTECClient:
    """Client para o servi\u00e7o CPTEC/INPE de previs\u00e3o por localidade."""

    @staticmethod
    async def get_previsao(lat: float, lon: float) -> PrevisaoClimatica:
        url = _CPTEC_URL.format(lat=f"{lat:.2f}", lon=f"{lon:.2f}")
        try:
            resp = await _get_with_retry(url)
        except ClimaServiceException as exc:
            raise ClimaServiceException(f"CPTEC indispon\u00edvel: {exc}") from exc

        try:
            root = ET.fromstring(resp.text)

            def _dec(tag: str) -> Decimal | None:
                el = root.find(tag)
                if el is None or not el.text:
                    return None
                try:
                    return Decimal(el.text.strip().replace(",", "."))
                except Exception:
                    return None

            def _str(tag: str) -> str | None:
                el = root.find(tag)
                return el.text.strip() if el is not None and el.text else None

            vento_kmh = _dec("vento")
            vento_ms = (
                round(vento_kmh / Decimal("3.6"), 2) if vento_kmh is not None else None
            )

            return PrevisaoClimatica(
                temperatura_c=_dec("temp"),
                umidade_pct=_dec("umidade"),
                precipitacao_mm=None,  # CPTEC n\u00e3o fornece precipita\u00e7\u00e3o em tempo real
                velocidade_vento_ms=vento_ms,
                condicao=_str("condicao"),
            )
        except Exception as exc:
            raise ClimaServiceException(f"Falha ao parsear XML CPTEC: {exc}") from exc


class OpenWeatherClient:
    """Client para OpenWeatherMap \u2014 fallback quando CPTEC falha."""

    @staticmethod
    async def get_previsao(lat: float, lon: float) -> PrevisaoClimatica:
        api_key = _settings.OPENWEATHER_API_KEY
        if not api_key:
            raise ClimaServiceException("OPENWEATHER_API_KEY n\u00e3o configurada")

        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
            "lang": "pt_br",
        }
        try:
            resp = await _get_with_retry(_OWM_URL, params=params)
        except ClimaServiceException as exc:
            raise ClimaServiceException(f"OpenWeather indispon\u00edvel: {exc}") from exc

        try:
            data = resp.json()
            main = data.get("main", {})
            wind = data.get("wind", {})
            rain = data.get("rain", {})
            weather_list = data.get("weather", [{}])
            condicao = weather_list[0].get("description") if weather_list else None

            return PrevisaoClimatica(
                temperatura_c=Decimal(str(main.get("temp", 0))),
                umidade_pct=Decimal(str(main.get("humidity", 0))),
                precipitacao_mm=Decimal(str(rain.get("1h", 0))),
                velocidade_vento_ms=Decimal(str(wind.get("speed", 0))),
                condicao=condicao,
            )
        except Exception as exc:
            raise ClimaServiceException(f"Falha ao parsear JSON OWM: {exc}") from exc


async def get_previsao_with_fallback(lat: float, lon: float) -> PrevisaoClimatica:
    """Tenta CPTEC; em caso de falha usa OpenWeatherMap."""
    try:
        result = await CPTECClient.get_previsao(lat, lon)
        log.debug("clima.client.cptec_ok", lat=lat, lon=lon)
        return result
    except ClimaServiceException as exc:
        log.warning("clima.client.cptec_fallback", reason=str(exc))

    result = await OpenWeatherClient.get_previsao(lat, lon)
    log.debug("clima.client.owm_ok", lat=lat, lon=lon)
    return result
