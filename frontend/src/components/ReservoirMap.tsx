import 'leaflet/dist/leaflet.css'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import type { ReservatorioSummary } from '@/types/api'

/** Cor do marcador por status */
function statusColor(status: string | null | undefined): string {
  switch (status) {
    case 'EMERGENCIA':
      return '#EF4444'
    case 'ALERTA':
      return '#F97316'
    case 'ATENCAO':
      return '#EAB308'
    default:
      return '#22C55E'
  }
}

interface Props {
  reservatorios: ReservatorioSummary[]
}

export default function ReservoirMap({ reservatorios }: Props) {
  const first = reservatorios[0]
  const center: [number, number] =
    first ? [Number(first.latitude), Number(first.longitude)] : [-23.4778200, -46.3829000]

  return (
    <MapContainer
      center={center}
      zoom={16}
      className="h-[420px] w-full rounded-xl"
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {reservatorios.map((r) => {
        const lat = Number(r.latitude)
        const lng = Number(r.longitude)
        if (isNaN(lat) || isNaN(lng)) return null
        const color = statusColor(r.status)

        return (
          <CircleMarker
            key={r.id}
            center={[lat, lng]}
            radius={14}
            pathOptions={{ color, fillColor: color, fillOpacity: 0.8, weight: 2 }}
          >
            <Popup>
              <div className="min-w-[160px]">
                <p className="font-bold text-slate-900">{r.nome}</p>
                <p className="text-sm text-slate-600">
                  Nível:{' '}
                  <span className="font-semibold">
                    {r.nivel_pct != null ? `${r.nivel_pct.toFixed(1)}%` : '—'}
                  </span>
                </p>
                <p className="text-sm text-slate-600">
                  Status:{' '}
                  <span className="font-semibold" style={{ color }}>
                    {r.status ?? 'NORMAL'}
                  </span>
                </p>
                {r.ultima_atualizacao && (
                  <p className="mt-1 text-xs text-slate-400">
                    Atualizado:{' '}
                    {new Date(r.ultima_atualizacao).toLocaleTimeString('pt-BR')}
                  </p>
                )}
              </div>
            </Popup>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}
