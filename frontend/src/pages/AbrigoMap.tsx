import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import { ABRIGOS, type Abrigo } from '@/data/abrigos'

// ── Corrige ícones padrão do Leaflet no Vite ─────────────────────────────────
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const ICON_USER = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

const ICON_ABRIGO = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

const ICON_NEAREST = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Distância euclidiana simples (suficiente para área pequena) */
function distancia(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const dlat = lat1 - lat2
  const dlng = lng1 - lng2
  return Math.sqrt(dlat * dlat + dlng * dlng)
}

/** Busca o abrigo mais próximo de um ponto */
function abrigoMaisProximo(lat: number, lng: number): Abrigo {
  return ABRIGOS.reduce((closest, a) =>
    distancia(lat, lng, a.lat, a.lng) < distancia(lat, lng, closest.lat, closest.lng) ? a : closest,
  )
}

/** Geocodifica um CEP via backend proxy (sem CSP/CORS issues) */
async function geocodificarCep(cep: string): Promise<{ lat: number; lng: number; logradouro: string }> {
  const cepLimpo = cep.replace(/\D/g, '')
  if (cepLimpo.length !== 8) throw new Error('CEP deve ter 8 dígitos.')

  const resp = await fetch(`/api/v1/geo/cep/${cepLimpo}`)
  if (resp.status === 404) throw new Error('CEP não encontrado.')
  if (resp.status === 422) throw new Error('Não foi possível localizar as coordenadas do CEP.')
  if (!resp.ok) throw new Error('Erro ao consultar o CEP. Tente novamente.')

  return resp.json()
}

// ── Componente auxiliar: recentra o mapa quando os bounds mudam ────────────────
function FitBounds({ bounds }: { bounds: L.LatLngBoundsExpression }) {
  const map = useMap()
  useEffect(() => {
    map.fitBounds(bounds, { padding: [48, 48] })
  }, [map, bounds])
  return null
}

// ── Página principal ──────────────────────────────────────────────────────────
export default function AbrigoMap() {
  const [cep, setCep] = useState('')
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [resultado, setResultado] = useState<{
    lat: number
    lng: number
    logradouro: string
    nearest: Abrigo
  } | null>(null)

  const inputRef = useRef<HTMLInputElement>(null)

  async function handleBuscar(e: React.FormEvent) {
    e.preventDefault()
    setErro(null)
    setResultado(null)
    setLoading(true)

    try {
      const { lat, lng, logradouro } = await geocodificarCep(cep)
      const nearest = abrigoMaisProximo(lat, lng)
      setResultado({ lat, lng, logradouro, nearest })
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro desconhecido.')
    } finally {
      setLoading(false)
    }
  }

  // Centro padrão: região do Jardim Romano
  const defaultCenter: [number, number] = [-23.4805, -46.3830]

  // Bounds para fitBounds quando há resultado
  const bounds: L.LatLngBoundsExpression | null = resultado
    ? [
        [resultado.lat, resultado.lng],
        [resultado.nearest.lat, resultado.nearest.lng],
      ]
    : null

  // Polilinha usuário → abrigo mais próximo
  const polyline: [number, number][] | null = resultado
    ? [
        [resultado.lat, resultado.lng],
        [resultado.nearest.lat, resultado.nearest.lng],
      ]
    : null

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* ── Header ── */}
      <header className="border-b border-slate-800 bg-slate-900 px-4 py-4">
        <div className="mx-auto flex max-w-4xl items-center gap-4">
          <Link to="/" className="text-xs text-slate-400 hover:text-slate-200 transition">
            ← Voltar
          </Link>
          <h1 className="text-base font-bold tracking-tight text-white">
            Busca por Abrigo — Jardim Romano
          </h1>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-6 px-4 py-6">
        {/* ── Formulário de CEP ── */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-1 text-sm font-semibold text-white">Encontre o abrigo mais próximo</h2>
          <p className="mb-2 text-xs text-slate-400">
            Informe o CEP da sua residência para localizar o abrigo de emergência mais próximo.
          </p>
          <p className="mb-4 inline-flex items-center gap-1.5 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-1.5 text-xs font-semibold text-amber-400">
            <span>⚠️</span>
            <span>Válido somente para CEPs da região do <span className="uppercase tracking-wide">Jardim Romano</span></span>
          </p>
          <form onSubmit={handleBuscar} className="flex flex-col gap-3 sm:flex-row">
            <label htmlFor="cep-input" className="sr-only">CEP</label>
            <input
              id="cep-input"
              ref={inputRef}
              type="text"
              inputMode="numeric"
              value={cep}
              onChange={(e) => setCep(e.target.value)}
              placeholder="00000-000"
              maxLength={9}
              required
              className="flex-1 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {loading ? 'Buscando…' : 'Buscar abrigo'}
            </button>
          </form>

          {erro && (
            <p role="alert" className="mt-3 text-xs text-red-400">{erro}</p>
          )}
        </section>

        {/* ── Card do abrigo mais próximo ── */}
        {resultado && (
          <section className="rounded-2xl border border-green-800 bg-green-950 p-5">
            <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-green-400">
              Abrigo mais próximo
            </p>
            <p className="text-base font-bold text-white">{resultado.nearest.nome}</p>
            <p className="mt-1 text-sm text-green-200">{resultado.nearest.endereco}</p>
            <p className="mt-3 text-xs text-slate-400">
              Sua localização: <span className="text-slate-200">{resultado.logradouro}</span>
            </p>
          </section>
        )}

        {/* ── Mapa ── */}
        <section className="overflow-hidden rounded-2xl border border-slate-800">
          <MapContainer
            center={defaultCenter}
            zoom={15}
            className="h-[480px] w-full"
            scrollWheelZoom
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* Abrigos */}
            {ABRIGOS.map((a) => (
              <Marker
                key={a.id}
                position={[a.lat, a.lng]}
                icon={resultado?.nearest.id === a.id ? ICON_NEAREST : ICON_ABRIGO}
              >
                <Popup>
                  <div className="min-w-[180px]">
                    <p className="font-bold text-slate-900">{a.nome}</p>
                    <p className="mt-1 text-xs text-slate-600">{a.endereco}</p>
                    {resultado?.nearest.id === a.id && (
                      <p className="mt-2 text-xs font-semibold text-red-600">⭐ Mais próximo de você</p>
                    )}
                  </div>
                </Popup>
              </Marker>
            ))}

            {/* Localização do usuário */}
            {resultado && (
              <Marker position={[resultado.lat, resultado.lng]} icon={ICON_USER}>
                <Popup>
                  <div className="min-w-[160px]">
                    <p className="font-bold text-slate-900">Sua localização</p>
                    <p className="mt-1 text-xs text-slate-600">{resultado.logradouro}</p>
                  </div>
                </Popup>
              </Marker>
            )}

            {/* Rota (linha reta) */}
            {polyline && (
              <Polyline positions={polyline} pathOptions={{ color: '#EF4444', weight: 3, dashArray: '8 6' }} />
            )}

            {/* Recentra o mapa */}
            {bounds && <FitBounds bounds={bounds} />}
          </MapContainer>
        </section>

        {/* ── Lista de todos os abrigos ── */}
        <section>
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
            Todos os abrigos cadastrados
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {ABRIGOS.map((a) => (
              <div
                key={a.id}
                className={`rounded-xl border p-4 transition ${
                  resultado?.nearest.id === a.id
                    ? 'border-green-700 bg-green-950'
                    : 'border-slate-800 bg-slate-900'
                }`}
              >
                <p className="text-sm font-semibold text-white">{a.nome}</p>
                <p className="mt-0.5 text-xs text-slate-400">{a.endereco}</p>
                {resultado?.nearest.id === a.id && (
                  <span className="mt-2 inline-block rounded-full bg-green-800 px-2 py-0.5 text-xs font-medium text-green-200">
                    Mais próximo
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
