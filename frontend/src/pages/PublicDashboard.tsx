import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'
import AlertBadge from '@/components/AlertBadge'
import TrendIndicator from '@/components/TrendIndicator'
import AlertSubscribeForm from '@/components/AlertSubscribeForm'
import OfflineBanner from '@/components/OfflineBanner'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useOffline } from '@/hooks/useOffline'
import type { StatusPublico, StatusReservatorio, LeituraSensoresPublico, LeituraPublica, EstacaoPublica } from '@/types/api'

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmt(val: number | null | undefined, digits = 1): string {
  return val != null ? val.toFixed(digits) : '—'
}

function direcaoVento(graus: number | null | undefined): string {
  if (graus == null) return '—'
  const dirs = ['N', 'NE', 'L', 'SE', 'S', 'SO', 'O', 'NO']
  return dirs[Math.round(graus / 45) % 8]
}

function horaFormatada(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

// ── Card: sensor de nível ────────────────────────────────────────────────────

interface NivelCardProps {
  sensor: LeituraPublica
  reservatorioId: number
  status: string | null
}

function NivelCard({ sensor, reservatorioId, status }: NivelCardProps) {
  const [wsData, setWsData] = useState<StatusReservatorio | null>(null)
  const handleMessage = useCallback((data: unknown) => {
    setWsData(data as StatusReservatorio)
  }, [])
  const { connected } = useWebSocket(reservatorioId, handleMessage, { publico: true })

  const nivelPct = wsData?.nivel_pct ?? null
  const taxa = wsData?.taxa_cm_min ?? null
  const wsStatus = wsData?.status ?? status

  const pct = nivelPct ?? 0
  const barGradient =
    wsStatus === 'EMERGENCIA' || wsStatus === 'CRITICO'
      ? 'from-red-500 to-red-400'
      : wsStatus === 'ALERTA'
        ? 'from-orange-500 to-amber-400'
        : wsStatus === 'ATENCAO'
          ? 'from-yellow-500 to-yellow-300'
          : 'from-cyan-600 to-blue-400'

  const glowColor =
    wsStatus === 'EMERGENCIA' || wsStatus === 'CRITICO'
      ? 'shadow-red-500/30'
      : wsStatus === 'ALERTA'
        ? 'shadow-orange-500/30'
        : wsStatus === 'ATENCAO'
          ? 'shadow-yellow-400/30'
          : 'shadow-cyan-500/20'

  return (
    <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 p-6 shadow-xl ring-1 ring-white/5 ${glowColor} shadow-lg`}>
      <div className="pointer-events-none absolute -right-8 -top-8 h-40 w-40 rounded-full bg-blue-500/10 blur-2xl" />
      <div className="mb-4 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 text-blue-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9 9 0 01-9-9c0-4.97 9-13 9-13s9 8.03 9 13a9 9 0 01-9 9z" />
            </svg>
            <span className="text-xs font-semibold uppercase tracking-widest text-blue-400">Sensor de Nível</span>
          </div>
          <h2 className="mt-1 text-lg font-bold text-white leading-snug">{sensor.descricao}</h2>
          <p className="mt-0.5 text-xs text-slate-500">{sensor.codigo}</p>
        </div>
        <div className="flex items-center gap-1.5 rounded-full bg-slate-700/60 px-2.5 py-1">
          <span className={`h-2 w-2 rounded-full ${connected ? 'animate-pulse bg-green-400' : 'bg-slate-500'}`} />
          <span className="text-[10px] font-medium text-slate-300">{connected ? 'Ao vivo' : 'Offline'}</span>
        </div>
      </div>
      <div className="mb-5 flex items-end gap-3">
        <span className="text-5xl font-black tabular-nums text-white">
          {sensor.valor != null ? Math.round(sensor.valor) : '—'}
        </span>
        <span className="mb-1.5 text-xl font-light text-slate-400">{sensor.unidade ?? 'cm'}</span>
        <div className="mb-1.5 ml-auto">
          <TrendIndicator taxaVariacao={taxa} />
        </div>
      </div>
      <div className="mb-2 space-y-1">
        <div className="flex justify-between text-xs text-slate-500">
          <span>Capacidade</span>
          <span className="font-semibold text-white">{nivelPct != null ? `${pct.toFixed(1)}%` : '—'}</span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-700" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
          <div
            className={`h-full rounded-full bg-gradient-to-r ${barGradient} transition-all duration-700`}
            style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
          />
        </div>
      </div>
      <div className="mt-4 flex items-center justify-between">
        <AlertBadge status={wsStatus?.toUpperCase() ?? null} />
        <span className="text-xs text-slate-500">Atualizado: {horaFormatada(sensor.timestamp)}</span>
      </div>
    </div>
  )
}

// ── Card: estação meteorológica ──────────────────────────────────────────────

function MetricRow({ icon, label, value, unit }: { icon: React.ReactNode; label: string; value: string; unit?: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0">
      <div className="flex items-center gap-2">
        <span className="text-slate-400">{icon}</span>
        <span className="text-sm text-slate-300">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-sm font-bold text-white tabular-nums">{value}</span>
        {unit && <span className="text-xs text-slate-500">{unit}</span>}
      </div>
    </div>
  )
}

function EstacaoCard({ estacao }: { estacao: EstacaoPublica }) {
  const nomeEstacao = estacao.descricao || estacao.codigo_estacao

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 p-6 shadow-xl ring-1 ring-white/5">
      <div className="pointer-events-none absolute -left-6 -bottom-6 h-32 w-32 rounded-full bg-indigo-500/10 blur-2xl" />
      <div className="mb-4 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 text-indigo-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 15a4 4 0 004 4h9a5 5 0 10-4.9-6H7a4 4 0 00-4 4z" />
            </svg>
            <span className="text-xs font-semibold uppercase tracking-widest text-indigo-400">Estação Meteorológica</span>
          </div>
          <h2 className="mt-1 text-lg font-bold text-white">{nomeEstacao}</h2>
          <p className="mt-0.5 text-xs text-slate-500">{estacao.descricao}</p>
        </div>
        <span className="text-xs text-slate-500">{horaFormatada(estacao.timestamp)}</span>
      </div>
      <div>
        <MetricRow
          icon={<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l3-3 3 3v13" /></svg>}
          label="Temperatura"
          value={fmt(estacao.temperatura)}
          unit="°C"
        />
        <MetricRow
          icon={<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1M4.22 4.22l.707.707M18.364 18.364l.707.707M1 12h1M21 12h1M4.22 19.778l.707-.707M18.364 5.636l.707-.707" /></svg>}
          label="Umidade"
          value={fmt(estacao.umidade)}
          unit="%"
        />
        <MetricRow
          icon={<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M3 15a4 4 0 004 4h9a5 5 0 10-4.9-6H7a4 4 0 00-4 4z" /></svg>}
          label="Pressão"
          value={fmt(estacao.pressao, 1)}
          unit="hPa"
        />
        <MetricRow
          icon={<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" /></svg>}
          label="Chuva acumulada"
          value={fmt(estacao.pluviometro)}
          unit="mm"
        />
        <MetricRow
          icon={<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>}
          label="Vento"
          value={`${fmt(estacao.vento_velocidade)} km/h ${direcaoVento(estacao.vento_direcao)}`}
        />
      </div>
    </div>
  )
}

// ── Card skeleton ────────────────────────────────────────────────────────────

function CardSkeleton() {
  return <div className="h-64 animate-pulse rounded-2xl bg-slate-800" />
}

// ── Página principal ─────────────────────────────────────────────────────────

export default function PublicDashboard() {
  const offline = useOffline()
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const { data: reservatorios = [], isLoading: loadingRes } = useQuery<StatusPublico[]>({
    queryKey: ['publico-status'],
    queryFn: async () => {
      const res = await apiClient.get<StatusPublico[]>('/publico/status')
      return res.data
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
  })

  const reservatorioId = reservatorios[0]?.id ?? null

  const { data: leituras, isLoading: loadingLeituras } = useQuery<LeituraSensoresPublico>({
    queryKey: ['publico-leituras', reservatorioId],
    queryFn: async () => {
      const res = await apiClient.get<LeituraSensoresPublico>(`/publico/leituras/${reservatorioId}`)
      return res.data
    },
    enabled: reservatorioId != null,
    staleTime: 15_000,
    refetchInterval: 15_000,
  })

  const selected = reservatorios.find((r) => r.id === selectedId) ?? null
  const loading = loadingRes || loadingLeituras

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* ── Header ── */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 shadow-lg shadow-blue-500/30">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9 9 0 01-9-9c0-4.97 9-13 9-13s9 8.03 9 13a9 9 0 01-9 9z" />
              </svg>
            </div>
            <div>
              <p className="text-base font-bold leading-none text-white">Alerta Romano</p>
              <p className="text-xs text-slate-500">Piscinão Romano · Jardim Romano, SP</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <OfflineBanner offline={offline} lastUpdated={null} />
            <a href="/login" className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-400 hover:bg-slate-800 transition">
              Acesso técnico
            </a>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-10 px-6 py-10">
        {/* ── Hero ── */}
        <section className="text-center">
          <h1 className="text-3xl font-black tracking-tight text-white sm:text-4xl">
            Monitoramento em{' '}
            <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              Tempo Real
            </span>
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-slate-400">
            Acompanhe o nível do reservatório e as condições meteorológicas do entorno.
            Dados atualizados automaticamente a cada 10 segundos.
          </p>
        </section>

        {/* ── Sensores de Nível ── */}
        <section>
          <div className="mb-4 flex items-center gap-3">
            <div className="h-px flex-1 bg-slate-800" />
            <span className="text-xs font-semibold uppercase tracking-widest text-slate-500">Sensores de Nível</span>
            <div className="h-px flex-1 bg-slate-800" />
          </div>
          {loading ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <CardSkeleton /><CardSkeleton />
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {leituras?.sensores_nivel.map((sensor) => (
                <NivelCard
                  key={sensor.sensor_id}
                  sensor={sensor}
                  reservatorioId={reservatorioId!}
                  status={reservatorios[0]?.status ?? null}
                />
              ))}
            </div>
          )}
        </section>

        {/* ── Estações Meteorológicas ── */}
        <section>
          <div className="mb-4 flex items-center gap-3">
            <div className="h-px flex-1 bg-slate-800" />
            <span className="text-xs font-semibold uppercase tracking-widest text-slate-500">Estações Meteorológicas</span>
            <div className="h-px flex-1 bg-slate-800" />
          </div>
          {loading ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <CardSkeleton /><CardSkeleton />
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {leituras?.estacoes.map((estacao) => (
                <EstacaoCard key={estacao.codigo_estacao} estacao={estacao} />
              ))}
            </div>
          )}
        </section>

        {/* ── Inscrição de alertas ── */}
        {reservatorios.length > 0 && (
          <section>
            <div className="mb-4 flex items-center gap-3">
              <div className="h-px flex-1 bg-slate-800" />
              <span className="text-xs font-semibold uppercase tracking-widest text-slate-500">Receber Alertas</span>
              <div className="h-px flex-1 bg-slate-800" />
            </div>
            <div className="mx-auto max-w-md">
              {!selected ? (
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-center">
                  <p className="mb-4 text-sm text-slate-400">
                    Selecione um reservatório para se inscrever e receber notificações de alerta:
                  </p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {reservatorios.map((r) => (
                      <button
                        key={r.id}
                        onClick={() => setSelectedId(r.id)}
                        className="rounded-full border border-slate-700 bg-slate-800 px-4 py-1.5 text-sm text-slate-300 hover:bg-slate-700 transition"
                      >
                        {r.nome}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                  <div className="mb-4 flex items-center justify-between">
                    <p className="text-sm text-slate-300">
                      Alertas de <span className="font-semibold text-white">{selected.nome}</span>
                    </p>
                    <button onClick={() => setSelectedId(null)} className="text-xs text-slate-500 hover:text-slate-300">
                      Cancelar
                    </button>
                  </div>
                  <AlertSubscribeForm reservatorioId={selected.id} />
                </div>
              )}
            </div>
          </section>
        )}

        {/* ── Footer ── */}
        <footer className="border-t border-slate-800 pt-8 text-center">
          <p className="text-xs text-slate-600">
            Dados em tempo real via WebSocket · Sistema Alerta Romano © 2026 ·{' '}
            <span className="text-slate-500">Uniço Munitária</span>
          </p>
        </footer>
      </main>
    </div>
  )
}
