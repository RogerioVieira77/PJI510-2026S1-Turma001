import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/store/auth'
import { useNavigate } from 'react-router-dom'
import apiClient from '@/api/client'
import ReservoirMap from '@/components/ReservoirMap'
import LevelChart from '@/components/LevelChart'
import SensorStatusPanel from '@/components/SensorStatusPanel'
import AlertsTable from '@/components/AlertsTable'
import type { ReservatorioSummary } from '@/types/api'

export default function TechDashboard() {
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const { data: reservatorios = [], isLoading } = useQuery<ReservatorioSummary[]>({
    queryKey: ['reservatorios'],
    queryFn: async () => {
      const res = await apiClient.get<ReservatorioSummary[]>('/reservatorios')
      return res.data
    },
    staleTime: 60_000,
    onSuccess: (data) => {
      if (data.length > 0 && selectedId === null) {
        setSelectedId(data[0].id)
      }
    },
  })

  function handleLogout() {
    clearAuth()
    navigate('/login')
  }

  const selected = reservatorios.find((r) => r.id === selectedId) ?? null

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Topbar */}
      <header className="border-b border-slate-200 bg-white px-6 py-3 shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold text-blue-700">PiscinãoMonitor</span>
            <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700 uppercase">
              Técnico
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-600">
              {user?.nome ?? user?.email}
              {user?.role && (
                <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">
                  {user.role}
                </span>
              )}
            </span>
            <button
              onClick={handleLogout}
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
            >
              Sair
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 p-6">
        {/* Seletor de reservatório */}
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm font-medium text-slate-600">Reservatório:</span>
          {isLoading ? (
            <span className="text-sm text-slate-400">Carregando…</span>
          ) : (
            reservatorios.map((r) => (
              <button
                key={r.id}
                onClick={() => setSelectedId(r.id)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
                  selectedId === r.id
                    ? 'bg-blue-600 text-white shadow'
                    : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
                }`}
              >
                {r.nome}
              </button>
            ))
          )}
        </div>

        {/* Grid principal */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Mapa */}
          <div className="lg:col-span-2">
            <ReservoirMap reservatorios={reservatorios} />
          </div>

          {/* Painel de sensores em tempo real */}
          {selectedId !== null && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="mb-4 text-sm font-semibold text-slate-700">
                {selected?.nome ?? `Reservatório #${selectedId}`} — Tempo Real
              </h2>
              <SensorStatusPanel reservatorioId={selectedId} />
            </div>
          )}

          {/* Gráfico histórico */}
          {selectedId !== null && (
            <LevelChart reservatorioId={selectedId} />
          )}
        </div>

        {/* Tabela de alertas — largura total */}
        <AlertsTable />
      </main>
    </div>
  )
}
