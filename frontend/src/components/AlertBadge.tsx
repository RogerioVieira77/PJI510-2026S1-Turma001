/**
 * Semáforo de status WCAG AA
 * - Usa ícone + cor + texto (não depende apenas de cor — WCAG 1.4.1)
 * - role="status" + aria-label descritivo
 * - Contraste >= 4.5:1 (texto escuro sobre fundo claro)
 * - Estado CRITICO/EMERGENCIA: ícone pulsante
 */

export type StatusNivel = 'NORMAL' | 'ATENCAO' | 'ALERTA' | 'EMERGENCIA' | 'CRITICO'

interface Config {
  label: string
  ariaLabel: string
  textColor: string
  bgColor: string
  borderColor: string
  /** SVG path do ícone */
  icon: string
  pulse: boolean
}

const CONFIG: Record<string, Config> = {
  NORMAL: {
    label: 'Normal',
    ariaLabel: 'Status normal — reservatório dentro dos limites',
    textColor: 'text-green-800',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-300',
    // checkmark circle
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    pulse: false,
  },
  ATENCAO: {
    label: 'Atenção',
    ariaLabel: 'Atenção — nível elevado, monitoramento recomendado',
    textColor: 'text-yellow-900',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-400',
    // exclamation triangle
    icon: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
    pulse: false,
  },
  ALERTA: {
    label: 'Alerta',
    ariaLabel: 'Alerta — nível crítico, ação necessária',
    textColor: 'text-orange-900',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-400',
    // bell alert
    icon: 'M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0M3.124 7.5A8.969 8.969 0 015.292 3m13.416 0a8.969 8.969 0 012.168 4.5',
    pulse: false,
  },
  EMERGENCIA: {
    label: 'Situação Crítica',
    ariaLabel: 'Situação crítica — emergência, risco de transbordamento iminente',
    textColor: 'text-red-900',
    bgColor: 'bg-red-100',
    borderColor: 'border-red-500',
    // fire
    icon: 'M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z',
    pulse: true,
  },
  CRITICO: {
    label: 'Situação Crítica',
    ariaLabel: 'Situação crítica — emergência, risco de transbordamento iminente',
    textColor: 'text-red-900',
    bgColor: 'bg-red-100',
    borderColor: 'border-red-500',
    icon: 'M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z',
    pulse: true,
  },
}

interface Props {
  status: string | null | undefined
  /** 'sm' | 'md' (padrão: 'md') */
  size?: 'sm' | 'md'
}

export default function AlertBadge({ status, size = 'md' }: Props) {
  const key = (status ?? 'NORMAL').toUpperCase()
  const cfg = CONFIG[key] ?? CONFIG['NORMAL']

  const iconSize = size === 'sm' ? 'h-4 w-4' : 'h-5 w-5'
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm'
  const padding = size === 'sm' ? 'px-2 py-0.5 gap-1' : 'px-3 py-1 gap-1.5'

  return (
    <span
      role="status"
      aria-label={cfg.ariaLabel}
      className={`inline-flex items-center rounded-full border font-semibold ${padding} ${textSize} ${cfg.bgColor} ${cfg.textColor} ${cfg.borderColor}`}
    >
      {/* Ícone — pulsante se emergência */}
      <span className={cfg.pulse ? 'animate-pulse' : undefined}>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
          className={iconSize}
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d={cfg.icon} />
        </svg>
      </span>
      {cfg.label}
    </span>
  )
}
