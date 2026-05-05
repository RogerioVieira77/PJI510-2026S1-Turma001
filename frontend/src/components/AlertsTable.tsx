import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'
import type { AlertaRead } from '@/types/api'

const PAGE_SIZE = 20

const NIVEL_OPCOES = ['', 'atencao', 'alerta', 'emergencia']
const NIVEL_LABELS: Record<string, string> = {
  '': 'Todos',
  atencao: 'Atenção',
  alerta: 'Alerta',
  emergencia: 'Emergência',
}

interface Filtros {
  nivel: string
  periodo: string
}

function exportCSV(rows: AlertaRead[]) {
  const BOM = '\uFEFF'
  const header = ['Data/Hora', 'Reservatório', 'Nível (%)', 'Mensagem', 'Status']
  const lines = rows.map((a) => [
    new Date(a.criado_em).toLocaleString('pt-BR'),
    String(a.reservatorio_id),
    a.nivel_pct != null ? a.nivel_pct.toFixed(1) : '—',
    `"${(a.mensagem ?? '').replace(/"/g, '""')}"`,
    a.status,
  ])

  const csv = BOM + [header, ...lines].map((r) => r.join(';')).join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `alertas_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

export default function AlertsTable() {
  const [page, setPage] = useState(1)
  const [filtros, setFiltros] = useState<Filtros>({ nivel: '', periodo: '' })

  const { data: alertas = [], isLoading } = useQuery<AlertaRead[]>({
    queryKey: ['alertas', filtros],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (filtros.nivel) params.set('nivel', filtros.nivel)
      const res = await apiClient.get<AlertaRead[]>(`/alertas?${params.toString()}`)
      return res.data
    },
    staleTime: 30_000,
  })

  // Filtro local por período
  const filtered = alertas.filter((a) => {
    if (!filtros.periodo) return true
    const hours = parseInt(filtros.periodo, 10)
    const from = new Date(Date.now() - hours * 3_600_000)
    return new Date(a.criado_em) >= from
  })

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const pageData = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  function handleFiltro(key: keyof Filtros, value: string) {
    setFiltros((prev) => ({ ...prev, [key]: value }))
    setPage(1)
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      {/* Cabeçalho + filtros */}
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-100 p-4">
        <h3 className="flex-1 text-sm font-semibold text-slate-700">Histórico de Alertas</h3>

        {/* Filtro nível */}
        <select
          value={filtros.nivel}
          onChange={(e) => handleFiltro('nivel', e.target.value)}
          className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
          aria-label="Filtrar por nível"
        >
          {NIVEL_OPCOES.map((n) => (
            <option key={n} value={n}>{NIVEL_LABELS[n]}</option>
          ))}
        </select>

        {/* Filtro período */}
        <select
          value={filtros.periodo}
          onChange={(e) => handleFiltro('periodo', e.target.value)}
          className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
          aria-label="Filtrar por período"
        >
          <option value="">Qualquer período</option>
          <option value="1">Última hora</option>
          <option value="6">Últimas 6h</option>
          <option value="24">Últimas 24h</option>
          <option value="168">Última semana</option>
        </select>

        {/* Exportar */}
        <button
          onClick={() => exportCSV(filtered)}
          className="rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          disabled={filtered.length === 0}
        >
          Exportar CSV
        </button>
      </div>

      {/* Tabela */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3 text-left">Data/Hora</th>
              <th className="px-4 py-3 text-left">Reservatório</th>
              <th className="px-4 py-3 text-left">Nível</th>
              <th className="px-4 py-3 text-left">Mensagem</th>
              <th className="px-4 py-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-400">
                  Carregando…
                </td>
              </tr>
            )}
            {!isLoading && pageData.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-400">
                  Nenhum alerta encontrado
                </td>
              </tr>
            )}
            {pageData.map((a) => (
              <tr key={a.id} className="hover:bg-slate-50">
                <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                  {new Date(a.criado_em).toLocaleString('pt-BR')}
                </td>
                <td className="px-4 py-3 text-slate-700">{a.reservatorio_id}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${
                      a.nivel === 'emergencia'
                        ? 'bg-red-100 text-red-700'
                        : a.nivel === 'alerta'
                          ? 'bg-orange-100 text-orange-700'
                          : 'bg-yellow-100 text-yellow-700'
                    }`}
                  >
                    {NIVEL_LABELS[a.nivel] ?? a.nivel}
                  </span>
                </td>
                <td className="max-w-xs truncate px-4 py-3 text-slate-600">{a.mensagem}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${
                      a.status === 'ativo'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {a.status === 'ativo' ? 'Ativo' : 'Resolvido'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginação */}
      <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3">
        <span className="text-xs text-slate-500">
          {filtered.length} alerta{filtered.length !== 1 ? 's' : ''}
        </span>
        <div className="flex gap-1">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded px-2 py-1 text-xs text-slate-600 hover:bg-slate-100 disabled:opacity-40"
          >
            ← Anterior
          </button>
          <span className="px-2 py-1 text-xs text-slate-500">
            {page}/{totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="rounded px-2 py-1 text-xs text-slate-600 hover:bg-slate-100 disabled:opacity-40"
          >
            Próximo →
          </button>
        </div>
      </div>
    </div>
  )
}
