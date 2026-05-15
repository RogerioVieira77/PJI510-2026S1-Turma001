import { useState, useCallback } from 'react'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { StatusReservatorio } from '@/types/api'

interface Props {
  reservatorioId: number
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; text: string; label: string }> = {
    EMERGENCIA: { bg: 'bg-red-100', text: 'text-red-700', label: 'Emergência' },
    ALERTA: { bg: 'bg-orange-100', text: 'text-orange-700', label: 'Alerta' },
    ATENCAO: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Atenção' },
    NORMAL: { bg: 'bg-green-100', text: 'text-green-700', label: 'Normal' },
  }
  const s = map[status] ?? map['NORMAL']
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-sm font-semibold ${s.bg} ${s.text}`}>
      {s.label}
    </span>
  )
}

function BmsBadge({ nivel }: { nivel: string }) {
  const map: Record<string, { bg: string; text: string; label: string }> = {
    normal: { bg: 'bg-green-100', text: 'text-green-700', label: 'BMS Normal' },
    alerta: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'BMS Alerta' },
    critico: { bg: 'bg-red-100', text: 'text-red-700', label: 'BMS Crítico' },
  }
  const s = map[nivel] ?? map['normal']
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-sm font-semibold ${s.bg} ${s.text}`}>
      {s.label}
    </span>
  )
}

interface CardProps {
  label: string
  value: string
  sub?: string
}

function MetricCard({ label, value, sub }: CardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="mb-1 text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-slate-800">{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
    </div>
  )
}

export default function SensorStatusPanel({ reservatorioId }: Props) {
  const [status, setStatus] = useState<StatusReservatorio | null>(null)

  const handleMessage = useCallback((data: unknown) => {
    setStatus(data as StatusReservatorio)
  }, [])

  const { connected, reconnecting } = useWebSocket(reservatorioId, handleMessage)

  const nivelPct = status?.nivel_pct != null ? `${status.nivel_pct.toFixed(1)}%` : '—'
  const volumeM3 = status?.volume_m3 != null ? `${status.volume_m3.toFixed(0)} m³` : '—'
  const taxa = status?.taxa_cm_min != null ? `${status.taxa_cm_min.toFixed(2)} cm/min` : '—'

  // RN-07: Transbordo estimado com bombas
  const nivelAbaixo50 = status?.nivel_pct != null && status.nivel_pct < 50
  const bombasLigadas = status?.bombas_ligadas ?? null
  const taxaEnchimento = status?.taxa_enchimento_m3_h ?? null
  const taxaDrenagem = status?.taxa_drenagem_m3_h ?? null

  const tempoTransbordo =
    status?.tempo_transbordo_min != null && status.tempo_transbordo_min > 0
      ? `${Math.round(status.tempo_transbordo_min)} min`
      : '—'

  const bombasSubLabel =
    bombasLigadas != null
      ? `${bombasLigadas}/5 bombas ativas`
      : undefined

  const transbordoSub = nivelAbaixo50
    ? 'Aguardando 50% para ativar'
    : tempoTransbordo === '—'
    ? bombasSubLabel
      ? `${bombasSubLabel} · drenando`
      : 'Nível estável ou caindo'
    : bombasSubLabel

  const drenagemValue =
    taxaDrenagem != null && taxaEnchimento != null
      ? `${taxaDrenagem.toFixed(1)} m³/h`
      : '—'
  const drenagemSub =
    taxaEnchimento != null
      ? `Entrada: ${taxaEnchimento.toFixed(1)} m³/h`
      : undefined

  const divergencia = status?.divergencia_sensores ? 'Divergência detectada' : 'Sensores OK'
  const ultimaAtualizacao = status?.timestamp
    ? new Date(status.timestamp).toLocaleTimeString('pt-BR')
    : '—'

  const alimentacao =
    status?.fonte_alimentacao === 'bateria' ? 'Bateria emergência' :
    status?.fonte_alimentacao === 'rede' ? 'Rede elétrica' : '—'
  const bateriaPct = status?.bateria_pct_min != null ? `${status.bateria_pct_min}%` : '—'

  return (
    <div className="space-y-4">
      {/* Banner de reconexão */}
      {(reconnecting || !connected) && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-lg border border-yellow-300 bg-yellow-50 px-4 py-2 text-sm text-yellow-800"
        >
          <span className="h-2 w-2 animate-pulse rounded-full bg-yellow-500" />
          {reconnecting ? 'Reconectando ao servidor…' : 'Aguardando conexão…'}
        </div>
      )}

      {/* Status + última atualização */}
      <div className="flex items-center justify-between">
        {status ? <StatusBadge status={status.status} /> : <span className="text-sm text-slate-400">—</span>}
        <span className="text-xs text-slate-400">Atualizado às {ultimaAtualizacao}</span>
      </div>

      {/* Energia e BMS */}
      {status?.fonte_alimentacao != null && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Alimentação:</span>
          <span className="text-sm font-semibold text-slate-700">{alimentacao}</span>
          {status.fonte_alimentacao === 'bateria' && (
            <span className="text-sm text-slate-600">({bateriaPct})</span>
          )}
          {status.bms_nivel != null && <BmsBadge nivel={status.bms_nivel} />}
        </div>
      )}

      {/* Indicadores */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <MetricCard label="Nível Atual" value={nivelPct} />
        <MetricCard label="Volume" value={volumeM3} />
        <MetricCard
          label="Taxa de Variação"
          value={taxa}
          sub={status && status.taxa_cm_min > 0 ? '↑ Subindo' : status && status.taxa_cm_min < 0 ? '↓ Caindo' : '→ Estável'}
        />
        <MetricCard
          label="Transbordo estimado"
          value={tempoTransbordo}
          sub={transbordoSub}
        />
        <MetricCard
          label="Drenagem das bombas"
          value={drenagemValue}
          sub={drenagemSub}
        />
        <MetricCard
          label="Sensores"
          value={divergencia}
          sub={status?.divergencia_sensores ? 'Verifique os sensores' : undefined}
        />
      </div>
    </div>
  )
}
