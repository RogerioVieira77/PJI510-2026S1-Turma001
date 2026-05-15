from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

router = APIRouter()

_NOMINATIM_HEADERS = {
    "User-Agent": "alerta-romano/1.0 (unicomunitaria.com.br)",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

# Bounding box restrito ao Jardim Romano e entorno imediato (raio ~3 km).
# Evita que o Nominatim retorne bairros homônimos em municípios vizinhos (ex.: Ferraz de Vasconcelos).
_JARDIM_ROMANO_BBOX = {
    "viewbox": "-46.4127,-23.4532,-46.3538,-23.5073",
    "bounded": "1",
}

# Centroide de fallback: Comunidade N. Sra. Aparecida — Praça da Igreja, 90, Jardim Romano.
# Usado quando a geocodificação não encontra a rua exata no OSM.
_JARDIM_ROMANO_LAT = -23.480534055166668
_JARDIM_ROMANO_LNG = -46.38459352308587


class GeoResult(BaseModel):
    lat: float
    lng: float
    logradouro: str


def _valida_jardim_romano(lat: float, lng: float) -> bool:
    """Verifica se as coordenadas estão no entorno do Jardim Romano (raio ~3 km)."""
    return -23.5073 <= lat <= -23.4532 and -46.4127 <= lng <= -46.3538


async def _nominatim(params: dict[str, str]) -> list[dict]:
    """Consulta Nominatim e retorna resultados na Zona Leste de SP."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={**params, "format": "json", "limit": "3"},
                headers=_NOMINATIM_HEADERS,
            )
        if resp.status_code == 200:
            return [
                r for r in resp.json()
                if _valida_jardim_romano(float(r["lat"]), float(r["lon"]))
            ]
    except Exception:
        pass
    return []


@router.get("/cep/{cep}", response_model=GeoResult, summary="Geocodifica um CEP brasileiro")
async def geocodificar_cep(
    cep: str = Path(..., pattern=r"^\d{8}$", description="CEP sem traço (8 dígitos)"),
) -> GeoResult:
    # 1) ViaCEP
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.get(f"https://viacep.com.br/ws/{cep}/json/")
        r.raise_for_status()
        dados = r.json()
    except Exception:
        raise HTTPException(502, "Erro ao consultar o ViaCEP. Tente novamente.")

    if dados.get("erro"):
        raise HTTPException(404, "CEP não encontrado.")

    logradouro = ", ".join(filter(None, [dados.get("logradouro"), dados.get("bairro")]))
    logradouro_fmt = f"{logradouro} — {dados.get('localidade')}/{dados.get('uf')}"

    # 2) Nominatim — estratégias em cascata (todas filtradas para Zona Leste de SP)
    resultados: list[dict] = []

    # 2a) CEP direto
    resultados = await _nominatim({"postalcode": cep, "countrycodes": "br"})

    # 2b) Logradouro + bairro + cidade dentro do bbox do Jardim Romano
    if not resultados and dados.get("logradouro"):
        q = f"{dados['logradouro']}, {dados.get('bairro', '')}, {dados['localidade']}, {dados['uf']}, Brasil"
        resultados = await _nominatim({"q": q, **_JARDIM_ROMANO_BBOX})

    # 2c) Bairro + cidade dentro do bbox do Jardim Romano
    if not resultados and dados.get("bairro"):
        q = f"{dados['bairro']}, {dados['localidade']}, {dados['uf']}, Brasil"
        resultados = await _nominatim({"q": q, **_JARDIM_ROMANO_BBOX})

    # 2d) Bairro + cidade sem bbox restrito (ainda valida Zona Leste no retorno)
    if not resultados and dados.get("bairro"):
        q = f"{dados['bairro']}, {dados['localidade']}, {dados['uf']}, Brasil"
        resultados = await _nominatim({"q": q, "countrycodes": "br"})

    # 2e) Fallback final: centroide do Jardim Romano.
    # Garante que o pin apareça no bairro correto quando a rua não está no OSM,
    # em vez do centroide genérico da cidade de SP (15 km de distância).
    if not resultados:
        return GeoResult(
            lat=_JARDIM_ROMANO_LAT,
            lng=_JARDIM_ROMANO_LNG,
            logradouro=logradouro_fmt,
        )

    return GeoResult(
        lat=float(resultados[0]["lat"]),
        lng=float(resultados[0]["lon"]),
        logradouro=logradouro_fmt,
    )
