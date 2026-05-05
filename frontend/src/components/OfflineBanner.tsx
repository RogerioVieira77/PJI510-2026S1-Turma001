/**
 * Banner de status offline + última atualização (TASK-103)
 *
 * Props:
 *   offline      — resultado de useOffline()
 *   lastUpdated  — Date da última mensagem WebSocket (ou null)
 */

interface Props {
  offline: boolean
  lastUpdated: Date | null
}

function formatRelative(date: Date): string {
  const diffMs = Date.now() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)

  if (diffSec < 60) return `há ${diffSec}s`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `há ${diffMin} minuto${diffMin !== 1 ? 's' : ''}`
  const diffH = Math.floor(diffMin / 60)
  return `há ${diffH} hora${diffH !== 1 ? 's' : ''}`
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function OfflineBanner({ offline, lastUpdated }: Props) {
  const stale = lastUpdated != null && Date.now() - lastUpdated.getTime() > 120_000

  return (
    <div className="space-y-1">
      {/* Banner offline */}
      {offline && (
        <div
          role="alert"
          aria-live="assertive"
          className="flex items-center gap-2 rounded-lg border border-yellow-400 bg-yellow-50 px-4 py-2 text-sm font-medium text-yellow-900"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 5.636a9 9 0 010 12.728M15.536 8.464a5 5 0 010 7.072M6.343 6.343a9 9 0 000 12.728M9.172 9.172a5 5 0 000 7.07M12 12h.01" />
          </svg>
          Sem conexão — dados podem estar desatualizados
        </div>
      )}

      {/* Última atualização */}
      {lastUpdated && (
        <p className={`text-xs ${stale ? 'text-yellow-700' : 'text-slate-400'}`}>
          Última atualização: {formatTime(lastUpdated)}
          {stale && ` (${formatRelative(lastUpdated)} — dados podem estar desatualizados)`}
        </p>
      )}
    </div>
  )
}
