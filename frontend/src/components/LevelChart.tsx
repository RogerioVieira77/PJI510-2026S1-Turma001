import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import apiClient from '@/api/client'
import type { PontoHistorico } from '@/types/api'

type Periodo = '1h' | '6h' | '24h' | '7d' | '30d'

const PERIODOS: Periodo[] = ['1h', '6h', '24h', '7d', '30d']

interface Props {
  reservatorioId: number
}

function formatXAxis(value: string, periodo: Periodo): string {
  const d = new Date(value)
  if (periodo === '7d' || periodo === '30d') {
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
  }
  return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

function formatTooltip(value: number) {
  return [`${value.toFixed(1)} cm`, 'Nível']
}

export default function LevelChart({ reservatorioId }: Props) {
  const [periodo, setPeriodo] = useState<Periodo>('24h')

  const { data, isLoading, isError } = useQuery<PontoHistorico[]>({
    queryKey: ['historico', reservatorioId, periodo],
    queryFn: async () => {
      const res = await apiClient.get<PontoHistorico[]>(
        `/reservatorios/${reservatorioId}/historico?periodo=${periodo}`,
      )
      return res.data
    },
    staleTime: 30_000,
  })

  const chartData = (data ?? []).map((p) => ({
    bucket: p.bucket,
    media: Number(p.media.toFixed(2)),
    minimo: Number(p.minimo.toFixed(2)),
    maximo: Number(p.maximo.toFixed(2)),
  }))

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      {/* Seletor de período */}
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Histórico de Nível</h3>
        <div className="flex gap-1">
          {PERIODOS.map((p) => (
            <button
              key={p}
              onClick={() => setPeriodo(p)}
              className={`rounded px-2 py-1 text-xs font-medium transition ${
                periodo === p
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Loading skeleton */}
      {isLoading && (
        <div className="flex h-56 animate-pulse items-center justify-center rounded bg-slate-50">
          <span className="text-sm text-slate-400">Carregando…</span>
        </div>
      )}

      {isError && (
        <div className="flex h-56 items-center justify-center rounded bg-slate-50">
          <span className="text-sm text-red-500">Erro ao carregar dados</span>
        </div>
      )}

      {!isLoading && !isError && (
        <ResponsiveContainer width="100%" height={224}>
          <LineChart data={chartData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="bucket"
              tickFormatter={(v: string) => formatXAxis(v, periodo)}
              tick={{ fontSize: 11, fill: '#64748b' }}
              minTickGap={40}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748b' }}
              domain={[0, 100]}
              unit="%"
              width={36}
            />
            <Tooltip formatter={formatTooltip} labelFormatter={(l) => new Date(l as string).toLocaleString('pt-BR')} />
            <Legend wrapperStyle={{ fontSize: 11 }} />

            {/* Linhas de threshold */}
            <ReferenceLine y={60} stroke="#EAB308" strokeDasharray="4 4" label={{ value: 'Atenção', position: 'insideTopRight', fontSize: 10, fill: '#EAB308' }} />
            <ReferenceLine y={80} stroke="#F97316" strokeDasharray="4 4" label={{ value: 'Alerta', position: 'insideTopRight', fontSize: 10, fill: '#F97316' }} />
            <ReferenceLine y={95} stroke="#EF4444" strokeDasharray="4 4" label={{ value: 'Crítico', position: 'insideTopRight', fontSize: 10, fill: '#EF4444' }} />

            <Line
              type="monotone"
              dataKey="media"
              name="Média"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="minimo"
              name="Mínimo"
              stroke="#94a3b8"
              strokeWidth={1}
              strokeDasharray="3 3"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="maximo"
              name="Máximo"
              stroke="#94a3b8"
              strokeWidth={1}
              strokeDasharray="3 3"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
