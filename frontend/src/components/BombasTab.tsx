import { useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'
import type { BombaStatusItem } from '@/types/api'

interface Props {
  reservatorioId: number
}

function EstadoBadge({ ligada }: { ligada: boolean | null }) {
  if (ligada === true) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
        <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
        Ligada
      </span>
    )
  }
  if (ligada === false) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
        <span className="h-2 w-2 rounded-full bg-slate-400" />
        Desligada
      </span>
    )
  }
  return <span className="text-slate-400 text-xs">Sem dados</span>
}

function FonteBadge({ fonte }: { fonte: 'rede' | 'bateria' | null }) {
  if (fonte === 'rede') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
        <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
        Rede
      </span>
    )
  }
  if (fonte === 'bateria') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-700">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
        Gerador de Emergência
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

function BatteryBar({ pct }: { pct: number | null }) {
  if (pct === null) return <span className="text-slate-400 text-xs">—</span>
  const color =
    pct >= 60 ? 'bg-green-500' :
    pct >= 30 ? 'bg-amber-400' :
                'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-16 overflow-hidden rounded-full bg-slate-200">
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

export default function BombasTab({ reservatorioId }: Props) {
  const { data: bombas = [], isLoading, isError, refetch } = useQuery<BombaStatusItem[]>({
    queryKey: ['bombas-status', reservatorioId],
    queryFn: async () => {
      const res = await apiClient.get<BombaStatusItem[]>(
        `/reservatorios/${reservatorioId}/bombas/status`
      )
      return res.data
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-400 text-sm">
        Carregando status das bombas…
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-sm text-red-600">
        <span>Erro ao carregar status das bombas.</span>
        <button
          onClick={() => refetch()}
          className="rounded-lg border border-red-200 bg-red-50 px-4 py-1.5 text-xs font-medium text-red-700 hover:bg-red-100"
        >
          Tentar novamente
        </button>
      </div>
    )
  }

  if (bombas.length === 0) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-400 text-sm">
        Nenhuma bomba cadastrada para este reservatório.
      </div>
    )
  }

  const ligadas = bombas.filter((b) => b.ligada === true).length
  const desligadas = bombas.filter((b) => b.ligada === false).length
  const semDados = bombas.filter((b) => b.ligada === null).length

  return (
    <div className="space-y-5">
      {/* Resumo */}
      <div className="flex flex-wrap gap-4">
        <div className="flex items-center gap-2 rounded-xl border border-green-200 bg-green-50 px-4 py-3">
          <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-green-500" />
          <span className="text-sm font-semibold text-green-700">{ligadas}</span>
          <span className="text-sm text-green-600">Ligada{ligadas !== 1 ? 's' : ''}</span>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
          <span className="h-2.5 w-2.5 rounded-full bg-slate-400" />
          <span className="text-sm font-semibold text-slate-700">{desligadas}</span>
          <span className="text-sm text-slate-600">Desligada{desligadas !== 1 ? 's' : ''}</span>
        </div>
        {semDados > 0 && (
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3">
            <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
            <span className="text-sm font-semibold text-slate-500">{semDados}</span>
            <span className="text-sm text-slate-400">Sem dados</span>
          </div>
        )}
      </div>

      {/* Tabela */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <th className="px-5 py-3">Bomba</th>
              <th className="px-5 py-3">Estado</th>
              <th className="px-5 py-3">Última Leitura</th>
              <th className="px-5 py-3">Alimentação</th>
              <th className="px-5 py-3">Gerador de Emergência</th>
              <th className="px-5 py-3">Rotação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {bombas.map((bomba) => (
              <tr
                key={bomba.sensor_id}
                className="transition-colors hover:bg-slate-50"
              >
                <td className="px-5 py-3.5">
                  <div className="font-medium text-slate-800">{bomba.nome}</div>
                  <div className="text-xs text-slate-400">{bomba.codigo}</div>
                </td>
                <td className="px-5 py-3.5">
                  <EstadoBadge ligada={bomba.ligada} />
                </td>
                <td className="px-5 py-3.5 text-slate-600">
                  {formatTs(bomba.ultima_leitura)}
                </td>
                <td className="px-5 py-3.5">
                  <FonteBadge fonte={bomba.fonte_alimentacao} />
                </td>
                <td className="px-5 py-3.5">
                  <BatteryBar pct={bomba.bateria_pct} />
                </td>
                <td className="px-5 py-3.5">
                  <BmsBadge nivel={bomba.bms_nivel} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
