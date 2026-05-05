import { useState } from 'react'
import { usePushSubscription } from '@/hooks/usePushSubscription'
import apiClient from '@/api/client'

interface Props {
  reservatorioId: number
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function AlertSubscribeForm({ reservatorioId }: Props) {
  // Push
  const { isSubscribed, isLoading: pushLoading, error: pushError, subscribe, unsubscribe } = usePushSubscription()
  const pushSupported = typeof window !== 'undefined' && 'PushManager' in window && 'serviceWorker' in navigator

  // Email
  const [email, setEmail] = useState('')
  const [emailStatus, setEmailStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const [emailError, setEmailError] = useState<string | null>(null)

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault()
    setEmailError(null)

    if (!EMAIL_RE.test(email)) {
      setEmailError('Informe um endereço de e-mail válido.')
      return
    }

    setEmailStatus('sending')
    try {
      await apiClient.post(`/alertas/subscribe/email`, {
        email,
        reservatorio_id: reservatorioId,
      })
      setEmailStatus('sent')
    } catch {
      setEmailStatus('error')
      setEmailError('Não foi possível realizar a inscrição. Tente novamente.')
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-slate-700">Receber Alertas</h3>

      <div className="space-y-5">
        {/* Push */}
        <div>
          <p className="mb-2 text-xs font-medium text-slate-600 uppercase tracking-wide">
            Notificação no navegador
          </p>

          {!pushSupported ? (
            <p className="text-xs text-slate-400" role="note">
              Seu navegador não suporta notificações push.
            </p>
          ) : (
            <>
              <button
                onClick={isSubscribed ? unsubscribe : subscribe}
                disabled={pushLoading}
                aria-pressed={isSubscribed}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition disabled:opacity-50 ${
                  isSubscribed
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {pushLoading
                  ? 'Aguarde…'
                  : isSubscribed
                    ? '✓ Notificações ativas'
                    : 'Receber Push no navegador'}
              </button>

              {isSubscribed && (
                <p role="status" className="mt-2 text-xs text-green-700">
                  Notificações ativas! Você será avisado sobre alertas.
                </p>
              )}

              {pushError && (
                <p role="alert" className="mt-2 text-xs text-red-600">
                  {pushError}
                </p>
              )}
            </>
          )}
        </div>

        <hr className="border-slate-100" />

        {/* Email */}
        <div>
          <p className="mb-2 text-xs font-medium text-slate-600 uppercase tracking-wide">
            Notificação por e-mail
          </p>

          {emailStatus === 'sent' ? (
            <p role="status" className="text-sm text-green-700">
              Inscrição realizada! Verifique seu e-mail para confirmar.
            </p>
          ) : (
            <form onSubmit={handleEmailSubmit} noValidate className="flex flex-col gap-2 sm:flex-row">
              <label htmlFor="subscribe-email" className="sr-only">
                Endereço de e-mail
              </label>
              <input
                id="subscribe-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                required
                autoComplete="email"
                className="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-400"
                aria-describedby={emailError ? 'email-error' : undefined}
                aria-invalid={emailError ? 'true' : 'false'}
              />
              <button
                type="submit"
                disabled={emailStatus === 'sending'}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {emailStatus === 'sending' ? 'Enviando…' : 'Inscrever'}
              </button>
            </form>
          )}

          {emailError && (
            <p id="email-error" role="alert" className="mt-1 text-xs text-red-600">
              {emailError}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
