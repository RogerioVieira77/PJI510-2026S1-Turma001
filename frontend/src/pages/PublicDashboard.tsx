import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'
import AlertBadge from '@/components/AlertBadge'
import TrendIndicator from '@/components/TrendIndicator'
import AlertSubscribeForm from '@/components/AlertSubscribeForm'
import OfflineBanner from '@/components/OfflineBanner'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useOffline } from '@/hooks/useOffline'
import type { StatusPublico, StatusReservatorio } from '@/types/api'

// Cartão de reservatório individual com WS público
interface CardProps {
  reservatorio: StatusPublico
}

function ReservatorioCard({ reservatorio }: CardProps) {
  const [wsData, setWsData] = useState<StatusReservatorio | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const handleMessage = useCallback((data: unknown) => {
    setWsData(data as StatusReservatorio)
    setLastUpdated(new Date())
  }, [])

  const { connected } = useWebSocket(reservatorio.id, handleMessage, { publico: true })

  const status = wsData?.status ?? reservatorio.status
  const nivelPct = wsData?.nivel_pct ?? reservatorio.nivel_pct
  const taxa = wsData?.taxa_cm_min ?? null

  const pct = nivelPct ?? 0
  const barColor =
    status === 'EMERGENCIA' || status === 'CRITICO'
      ? 'bg-red-500'
      : status === 'ALERTA'
        ? 'bg-orange-400'
        : status === 'ATENCAO'
          ? 'bg-yellow-400'
          : 'bg-green-500'

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-800 p-5 shadow-lg">
      {/* Nome + indicador de conexão */}
      <div className="mb-3 flex items-start justify-between gap-2">
        <h2 className="text-base font-bold text-white">{reservatorio.nome}</h2>
        <span
          className={`mt-0.5 h-2.5 w-2.5 shrink-0 rounded-full ${connected ? 'bg-green-400' : 'bg-slate-500'}`}
          title={connected ? 'Ao vivo' : 'Desconectado'}
          aria-label={connected ? 'Conexão ativa' : 'Sem conexão ao vivo'}
        />
      </div>

      {/* Semáforo + tendência */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <AlertBadge status={status} />
        <TrendIndicator taxaVariacao={taxa} />
      </div>

      {/* Barra de nível */}
      <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
        <span>Nível</span>
        <span className="font-semibold text-white">{nivelPct != null ? `${nivelPct.toFixed(1)}%` : '—'}</span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-700" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={`Nível: ${pct.toFixed(1)}%`}>
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
        />
      </div>

      {/* Última atualização */}
      <div className="mt-3">
        <OfflineBanner offline={false} lastUpdated={lastUpdated} />
      </div>
    </div>
  )
}

export default function PublicDashboard() {
  const offline = useOffline()
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const { data: reservatorios = [], isLoading } = useQuery<StatusPublico[]>({
    queryKey: ['publico-status'],
    queryFn: async () => {
      const res = await apiClient.get<StatusPublico[]>('/publico/status')
      return res.data
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
  })

  const selected = reservatorios.find((r) => r.id === selectedId) ?? null

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900 px-6 py-4 shadow">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-blue-400">Alerta Romano</h1>
            <p className="text-xs text-slate-400">Monitoramento público — Piscinão Romano, Jardim Romano</p>
          </div>
          <a
            href="/login"
            className="rounded-lg border border-slate-600 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800"
          >
            Acesso técnico
          </a>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-8 px-6 py-8">
        {/* Banner offline global */}
        <OfflineBanner offline={offline} lastUpdated={null} />

        {/* Grid de cartões */}
        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-48 animate-pulse rounded-2xl bg-slate-800" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {reservatorios.map((r) => (
              <div
                key={r.id}
                onClick={() => setSelectedId(r.id === selectedId ? null : r.id)}
                className="cursor-pointer"
              >
                <ReservatorioCard reservatorio={r} />
              </div>
            ))}
          </div>
        )}

        {/* Formulário de inscrição para o reservatório selecionado */}
        {selected && (
          <div className="rounded-2xl border border-slate-700 bg-slate-800 p-1">
            <div className="mb-3 px-4 pt-4">
              <p className="text-sm text-slate-400">
                Receber alertas de <span className="font-semibold text-white">{selected.nome}</span>
              </p>
            </div>
            <AlertSubscribeForm reservatorioId={selected.id} />
          </div>
        )}

        {!selected && reservatorios.length > 0 && (
          <p className="text-center text-sm text-slate-500">
            Clique em um reservatório para se inscrever em alertas.
          </p>
        )}

        {/* Rodapé */}
        <footer className="border-t border-slate-700 pt-6 text-center text-xs text-slate-500">
          Dados atualizados em tempo real via WebSocket · Alerta Romano © 2026
        </footer>
      </main>
    </div>
  )
}
