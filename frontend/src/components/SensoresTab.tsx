import { useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'
import type { SensorStatusItem } from '@/types/api'

interface Props {
  reservatorioId: number
}

function FonteBadge({ fonte }: { fonte: 'rede' | 'bateria' | null }) {
  if (fonte === 'rede') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
        <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
        Rede Elétrica
      </span>
    )
  }
  if (fonte === 'bateria') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-700">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
        Bateria
      </span>
    )
  }
  return <span className="text-slate-400 text-xs">—</span>
}

function BmsBadge({ nivel }: { nivel: 'normal' | 'alerta' | 'critico' | null }) {
  if (nivel === 'normal') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
        <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
        Normal
      </span>
    )
  }
  if (nivel === 'alerta') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-700">
        <span className="h-1.5 w-1.5 rounded-full bg-yellow-500" />
        Alerta
      </span>
    )
  }
  if (nivel === 'critico') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-700">
        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
        Crítico
      </span>
    )
  }
  return <span className="text-slate-400 text-xs">—</span>
}

function StatusBadge({ ativo }: { ativo: boolean }) {
  return ativo ? (
    <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
      <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
      Ligado
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500">
      <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
      Desligado
    </span>
  )
}

function BatteryBar({ pct }: { pct: number | null }) {
  if (pct === null) return <span className="text-slate-400 text-xs">—</span>

  const color =
    pct >= 60 ? 'bg-green-500' :
    pct >= 30 ? 'bg-amber-400' :
                'bg-red-500'

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-20 overflow-hidden rounded-full bg-slate-200">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium text-slate-700">{pct}%</span>
    </div>
  )
}

function formatTs(ts: string | null): string {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function SensoresTab({ reservatorioId }: Props) {
  const { data: sensores = [], isLoading, isError, refetch } = useQuery<SensorStatusItem[]>({
    queryKey: ['sensores-status', reservatorioId],
    queryFn: async () => {
      const res = await apiClient.get<SensorStatusItem[]>(
        `/reservatorios/${reservatorioId}/sensores/status`
      )
      return res.data
    },
    staleTime: 60_000,
    refetchInterval: 120_000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-400 text-sm">
        Carregando status dos sensores…
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-16">
        <p className="text-slate-500 text-sm">Falha ao carregar dados dos sensores.</p>
        <button
          onClick={() => refetch()}
          className="rounded-lg border border-slate-200 px-4 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
        >
          Tentar novamente
        </button>
      </div>
    )
  }

  const hasAlerts = sensores.some(
    (s) => s.bms_nivel === 'critico' || s.bms_nivel === 'alerta' || s.fonte_alimentacao === 'bateria'
  )

  return (
    <div className="space-y-4">
      {hasAlerts && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
          <svg className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
          </svg>
          <p className="text-sm text-amber-700">
            Um ou mais sensores estão operando em modo de bateria ou com BMS em estado de alerta/crítico.
          </p>
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3.5">
          <h3 className="text-sm font-semibold text-slate-700">Status dos Sensores</h3>
          <button
            onClick={() => refetch()}
            className="rounded-md border border-slate-200 px-3 py-1 text-xs text-slate-500 hover:bg-slate-50"
          >
            Atualizar
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <th className="px-5 py-3">Nome</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Alimentação</th>
                <th className="px-4 py-3">Carga da Bateria</th>
                <th className="px-4 py-3">Estado BMS</th>
                <th className="px-4 py-3">Última Leitura</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sensores.map((sensor) => (
                <tr
                  key={sensor.codigo}
                  className={`transition-colors hover:bg-slate-50 ${
                    sensor.bms_nivel === 'critico'
                      ? 'bg-red-50/40'
                      : sensor.bms_nivel === 'alerta' || sensor.fonte_alimentacao === 'bateria'
                      ? 'bg-amber-50/30'
                      : ''
                  }`}
                >
                  <td className="px-5 py-3.5">
                    <div className="font-medium text-slate-800">{sensor.nome}</div>
                    <div className="text-xs text-slate-400">{sensor.codigo}</div>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="text-xs text-slate-500">{sensor.tipo_display}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    <StatusBadge ativo={sensor.ativo} />
                  </td>
                  <td className="px-4 py-3.5">
                    <FonteBadge fonte={sensor.fonte_alimentacao} />
                  </td>
                  <td className="px-4 py-3.5">
                    <BatteryBar pct={sensor.bateria_pct} />
                  </td>
                  <td className="px-4 py-3.5">
                    <BmsBadge nivel={sensor.bms_nivel} />
                  </td>
                  <td className="px-4 py-3.5 text-xs text-slate-500">
                    {formatTs(sensor.ultima_leitura)}
                  </td>
                </tr>
              ))}
              {sensores.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-sm text-slate-400">
                    Nenhum sensor encontrado para este reservatório.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
