import { useState } from 'react'

interface Props {
  reservatorioId: number
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function AlertSubscribeForm({ reservatorioId: _reservatorioId }: Props) {
  // Push (mock)
  const [pushStatus, setPushStatus] = useState<'idle' | 'sent'>('idle')

  // Email (mock)
  const [email, setEmail] = useState('')
  const [emailStatus, setEmailStatus] = useState<'idle' | 'sent'>('idle')
  const [emailError, setEmailError] = useState<string | null>(null)

  // SMS (mock)
  const [sms, setSms] = useState('')
  const [smsStatus, setSmsStatus] = useState<'idle' | 'sent'>('idle')
  const [smsError, setSmsError] = useState<string | null>(null)

  // WhatsApp (mock)
  const [whatsapp, setWhatsapp] = useState('')
  const [whatsappStatus, setWhatsappStatus] = useState<'idle' | 'sent'>('idle')
  const [whatsappError, setWhatsappError] = useState<string | null>(null)

  function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault()
    setEmailError(null)
    if (!EMAIL_RE.test(email)) {
      setEmailError('Informe um endereço de e-mail válido.')
      return
    }
    setEmailStatus('sent')
  }

  function handleSmsSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSmsError(null)
    if (!sms.trim()) {
      setSmsError('Informe um número de telefone.')
      return
    }
    setSmsStatus('sent')
  }

  function handleWhatsappSubmit(e: React.FormEvent) {
    e.preventDefault()
    setWhatsappError(null)
    if (!whatsapp.trim()) {
      setWhatsappError('Informe um número de telefone.')
      return
    }
    setWhatsappStatus('sent')
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-slate-700">Receber Alertas</h3>

      <div className="space-y-5">
        {/* Push (mock) */}
        <div>
          <p className="mb-2 text-xs font-medium text-slate-600 uppercase tracking-wide">
            Notificação no navegador
          </p>

          {pushStatus === 'sent' ? (
            <p role="status" className="text-sm text-green-700">
              Alerta de Push Cadastrado com Sucesso
            </p>
          ) : (
            <button
              onClick={() => setPushStatus('sent')}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Receber Push no navegador
            </button>
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
              Alerta de E-mail Cadastrado com Sucesso
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
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Inscrever
              </button>
            </form>
          )}

          {emailError && (
            <p id="email-error" role="alert" className="mt-1 text-xs text-red-600">
              {emailError}
            </p>
          )}
        </div>

        <hr className="border-slate-100" />

        {/* SMS (mock) */}
        <div>
          <p className="mb-2 text-xs font-medium text-slate-600 uppercase tracking-wide">
            Receber SMS
          </p>

          {smsStatus === 'sent' ? (
            <p role="status" className="text-sm text-green-700">
              Alerta de SMS Cadastrado com Sucesso
            </p>
          ) : (
            <form onSubmit={handleSmsSubmit} noValidate className="flex flex-col gap-2 sm:flex-row">
              <label htmlFor="subscribe-sms" className="sr-only">
                Número de telefone para SMS
              </label>
              <input
                id="subscribe-sms"
                type="tel"
                value={sms}
                onChange={(e) => setSms(e.target.value)}
                placeholder="(11) 99999-9999"
                autoComplete="tel"
                className="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-400"
                aria-describedby={smsError ? 'sms-error' : undefined}
                aria-invalid={smsError ? 'true' : 'false'}
              />
              <button
                type="submit"
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Inscrever
              </button>
            </form>
          )}

          {smsError && (
            <p id="sms-error" role="alert" className="mt-1 text-xs text-red-600">
              {smsError}
            </p>
          )}
        </div>

        <hr className="border-slate-100" />

        {/* WhatsApp (mock) */}
        <div>
          <p className="mb-2 text-xs font-medium text-slate-600 uppercase tracking-wide">
            Receber Alerta no WhatsApp
          </p>

          {whatsappStatus === 'sent' ? (
            <p role="status" className="text-sm text-green-700">
              Alerta de WhatsApp Cadastrado com Sucesso
            </p>
          ) : (
            <form onSubmit={handleWhatsappSubmit} noValidate className="flex flex-col gap-2 sm:flex-row">
              <label htmlFor="subscribe-whatsapp" className="sr-only">
                Número de telefone para WhatsApp
              </label>
              <input
                id="subscribe-whatsapp"
                type="tel"
                value={whatsapp}
                onChange={(e) => setWhatsapp(e.target.value)}
                placeholder="(11) 99999-9999"
                autoComplete="tel"
                className="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-400"
                aria-describedby={whatsappError ? 'whatsapp-error' : undefined}
                aria-invalid={whatsappError ? 'true' : 'false'}
              />
              <button
                type="submit"
                className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
              >
                Inscrever
              </button>
            </form>
          )}

          {whatsappError && (
            <p id="whatsapp-error" role="alert" className="mt-1 text-xs text-red-600">
              {whatsappError}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
