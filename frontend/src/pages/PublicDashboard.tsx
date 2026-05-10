import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'
import AlertBadge from '@/components/AlertBadge'
import TrendIndicator from '@/components/TrendIndicator'
import AlertSubscribeForm from '@/components/AlertSubscribeForm'
import OfflineBanner from '@/components/OfflineBanner'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useOffline } from '@/hooks/useOffline'
import type {
  StatusPublico,
  StatusReservatorio,
  LeituraSensoresPublico,
  LeituraPublica,
  EstacaoPublica,
  AlertasExternos,
  SituacaoDefesaCivilPublica,
  AlertaDefesaCivilPublico,
  PrevisaoChuvaPublica,
} from '@/types/api'

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

// ── Card: volume médio ───────────────────────────────────────────────────────

interface VolumeMediaCardProps {
  nivelMedioM: number | null
  nivelMedioPct: number | null
  volumeMedioM3: number | null
}

function VolumeMediaCard({ nivelMedioM, nivelMedioPct, volumeMedioM3 }: VolumeMediaCardProps) {
  const pct = nivelMedioPct ?? 0
  const barColor =
    pct >= 95 ? 'from-red-500 to-red-400' :
    pct >= 80 ? 'from-orange-500 to-amber-400' :
    pct >= 60 ? 'from-yellow-500 to-yellow-300' :
    'from-emerald-500 to-teal-400'

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 p-6 shadow-xl ring-1 ring-white/5">
      <div className="pointer-events-none absolute -right-10 -bottom-10 h-48 w-48 rounded-full bg-emerald-500/10 blur-2xl" />

      <div className="mb-5 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 text-emerald-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 4.5h14.25M3 9h9.75M3 13.5h9.75m4.5-4.5v12m0 0-3.75-3.75M17.25 21 21 17.25" />
            </svg>
            <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400">Resumo do Reservatório</span>
          </div>
          <h2 className="mt-1 text-lg font-bold text-white leading-snug">Volume Médio Estimado</h2>
          <p className="mt-0.5 text-xs text-slate-500">Média entre os dois sensores de nível</p>
        </div>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Nível médio</p>
          <div className="flex items-baseline gap-1.5">
            <span className="text-4xl font-black tabular-nums text-white">
              {nivelMedioM != null ? nivelMedioM.toFixed(2) : '—'}
            </span>
            <span className="text-lg font-light text-slate-400">m</span>
          </div>
          <p className="mt-0.5 text-sm text-slate-400">
            de 8 m de profundidade
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Volume</p>
          <div className="flex items-baseline gap-1.5">
            <span className="text-4xl font-black tabular-nums text-white">
              {volumeMedioM3 != null ? volumeMedioM3.toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'}
            </span>
            <span className="text-lg font-light text-slate-400">m³</span>
          </div>
          <p className="mt-0.5 text-sm text-slate-400">
            de 120.000 m³ totais
          </p>
        </div>
      </div>

      <div className="space-y-1.5">
        <div className="flex justify-between text-xs text-slate-500">
          <span>Ocupação do reservatório</span>
          <span className="font-semibold text-white">{nivelMedioPct != null ? `${pct.toFixed(1)}%` : '—'}</span>
        </div>
        <div className="h-4 w-full overflow-hidden rounded-full bg-slate-700" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
          <div
            className={`h-full rounded-full bg-gradient-to-r ${barColor} transition-all duration-700`}
            style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-slate-600">
          <span>0%</span>
          <span className="text-yellow-600">Atenção 60%</span>
          <span className="text-orange-600">Alerta 80%</span>
          <span className="text-red-600">Crítico 95%</span>
          <span>100%</span>
        </div>
      </div>
    </div>
  )
}

// ── Banner: Defesa Civil ──────────────────────────────────────────────────────

const _STATUS_DC_LABEL: Record<string, string> = {
  verde: 'Situação Normal',
  amarelo: 'Atenção',
  laranja: 'Alerta',
  vermelho: 'Emergência',
}

const _STATUS_DC_CLASSES: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  verde:    { bg: 'bg-emerald-950/60', border: 'border-emerald-700/50', text: 'text-emerald-300', dot: 'bg-emerald-400' },
  amarelo:  { bg: 'bg-yellow-950/60',  border: 'border-yellow-700/50',  text: 'text-yellow-300',  dot: 'bg-yellow-400' },
  laranja:  { bg: 'bg-orange-950/60',  border: 'border-orange-700/50',  text: 'text-orange-300',  dot: 'bg-orange-400' },
  vermelho: { bg: 'bg-red-950/60',     border: 'border-red-700/50',     text: 'text-red-300',     dot: 'bg-red-500 animate-pulse' },
}

function BannerDefesaCivil({ situacao }: { situacao: SituacaoDefesaCivilPublica }) {
  const cls = _STATUS_DC_CLASSES[situacao.status] ?? _STATUS_DC_CLASSES.verde
  const label = _STATUS_DC_LABEL[situacao.status] ?? situacao.status
  const nAlertas = situacao.alertas_ativos.length

  return (
    <div className={`flex items-center gap-3 rounded-2xl border ${cls.border} ${cls.bg} px-5 py-3`}>
      <span className={`h-3 w-3 flex-shrink-0 rounded-full ${cls.dot}`} />
      <div className="flex-1 min-w-0">
        <span className={`text-sm font-bold ${cls.text}`}>Defesa Civil — {label}</span>
        {nAlertas > 0 && (
          <span className="ml-2 text-xs text-slate-400">
            {nAlertas} alerta{nAlertas > 1 ? 's' : ''} ativo{nAlertas > 1 ? 's' : ''}
          </span>
        )}
      </div>
      <span className="text-xs text-slate-500">{horaFormatada(situacao.timestamp)}</span>
    </div>
  )
}

// ── Card: Previsão de Chuva ───────────────────────────────────────────────────

const _NIVEL_CHUVA_LABEL: Record<number, string> = {
  1: 'Sem Chuva',
  2: 'Garoa',
  3: 'Chuva Fraca',
  4: 'Chuva Forte',
  5: 'Tempestade',
}

function PrevisaoChuvaCard({ previsao }: { previsao: PrevisaoChuvaPublica }) {
  const label = _NIVEL_CHUVA_LABEL[previsao.nivel] ?? `Nível ${previsao.nivel}`
  const nivelColor =
    previsao.nivel >= 5 ? 'text-red-400' :
    previsao.nivel >= 4 ? 'text-orange-400' :
    previsao.nivel >= 3 ? 'text-yellow-400' :
    previsao.nivel >= 2 ? 'text-cyan-400' :
    'text-emerald-400'

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 p-6 shadow-xl ring-1 ring-white/5">
      <div className="pointer-events-none absolute -left-8 -top-8 h-40 w-40 rounded-full bg-cyan-500/10 blur-2xl" />
      <div className="mb-4 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            {/* Rain icon */}
            <svg className="h-5 w-5 text-cyan-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 15a4 4 0 004 4h9a5 5 0 10-4.9-6H7a4 4 0 00-4 4z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 19v2M12 19v2M16 19v2" />
            </svg>
            <span className="text-xs font-semibold uppercase tracking-widest text-cyan-400">Previsão de Chuva</span>
          </div>
          <h2 className="mt-1 text-lg font-bold text-white leading-snug">{previsao.regiao}</h2>
        </div>
        <span className="text-xs text-slate-500">{horaFormatada(previsao.timestamp)}</span>
      </div>

      <div className="mb-3 flex items-center gap-3">
        <span className={`text-3xl font-black tabular-nums ${nivelColor}`}>{label}</span>
        <span className="rounded-full bg-slate-700/60 px-2.5 py-0.5 text-xs font-semibold text-slate-300">
          Nível {previsao.nivel}/5
        </span>
      </div>

      <p className="mb-3 text-sm text-slate-400">{previsao.descricao}</p>

      <div className="flex items-center gap-2">
        <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" />
        </svg>
        <span className="text-sm text-slate-300">
          <span className="font-bold text-white">{previsao.precipitacao_mm.toFixed(1)}</span>
          <span className="ml-1 text-slate-500">mm esperado</span>
        </span>
      </div>
    </div>
  )
}

// ── Lista de Alertas Defesa Civil ─────────────────────────────────────────────

function dataFormatada(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

function AlertasDefesaCivilList({ alertas }: { alertas: AlertaDefesaCivilPublico[] }) {
  if (alertas.length === 0) return null

  return (
    <div className="space-y-3">
      {alertas.map((alerta) => (
        <div
          key={alerta.id}
          className="rounded-xl border border-orange-800/40 bg-orange-950/30 p-4"
        >
          <div className="mb-1 flex items-start justify-between gap-2">
            <span className="text-sm font-bold text-orange-300">{alerta.titulo}</span>
            <span className="flex-shrink-0 rounded-full bg-orange-900/50 px-2 py-0.5 text-[10px] font-semibold text-orange-400 uppercase tracking-wide">
              {alerta.regiao}
            </span>
          </div>
          <p className="text-xs text-slate-400">{alerta.descricao}</p>
          <div className="mt-2 flex items-center gap-1 text-[11px] text-slate-500">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z" />
            </svg>
            <span>Válido até {dataFormatada(alerta.valido_ate)}</span>
          </div>
        </div>
      ))}
    </div>
  )
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

  const { data: alertasExternos } = useQuery<AlertasExternos>({
    queryKey: ['publico-alertas-externos'],
    queryFn: async () => {
      const res = await apiClient.get<AlertasExternos>('/publico/alertas-externos')
      return res.data
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
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

        {/* ── Banner Defesa Civil ── */}
        {alertasExternos?.situacao_defesa_civil && (
          <BannerDefesaCivil situacao={alertasExternos.situacao_defesa_civil} />
        )}

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
          {/* Card de volume médio */}
          {!loading && leituras && (
            <div className="mt-4">
              <VolumeMediaCard
                nivelMedioM={leituras.nivel_medio_m ?? null}
                nivelMedioPct={leituras.nivel_medio_pct ?? null}
                volumeMedioM3={leituras.volume_medio_m3 ?? null}
              />
            </div>
          )}
        </section>

        {/* ── Previsão de Chuva / Alertas Defesa Civil ── */}
        {alertasExternos && (alertasExternos.previsao_chuva || alertasExternos.alertas_defesa_civil.length > 0) && (
          <section>
            <div className="mb-4 flex items-center gap-3">
              <div className="h-px flex-1 bg-slate-800" />
              <span className="text-xs font-semibold uppercase tracking-widest text-slate-500">Defesa Civil</span>
              <div className="h-px flex-1 bg-slate-800" />
            </div>
            <div className="space-y-4">
              {alertasExternos.previsao_chuva && (
                <PrevisaoChuvaCard previsao={alertasExternos.previsao_chuva} />
              )}
              <AlertasDefesaCivilList alertas={alertasExternos.alertas_defesa_civil} />
            </div>
          </section>
        )}

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
