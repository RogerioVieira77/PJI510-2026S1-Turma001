/**
 * Indicador de tendência baseado em taxa_variacao (cm/min)
 * - ↑ Nível subindo  (taxa > +0.05)
 * - ↓ Nível caindo   (taxa < -0.05)
 * - → Nível estável  (entre -0.05 e +0.05)
 * - Ícone + texto para acessibilidade (WCAG 1.4.1)
 * - Transição suave ao mudar de estado (transition-all)
 */

interface Props {
  taxaVariacao: number | null | undefined
}

type Trend = 'subindo' | 'caindo' | 'estavel'

function getTrend(taxa: number | null | undefined): Trend {
  if (taxa == null) return 'estavel'
  if (taxa > 0.05) return 'subindo'
  if (taxa < -0.05) return 'caindo'
  return 'estavel'
}

const TREND_CONFIG: Record<
  Trend,
  { label: string; ariaLabel: string; color: string; bg: string; border: string; rotate: string }
> = {
  subindo: {
    label: 'Nível subindo',
    ariaLabel: 'Tendência: nível subindo',
    color: 'text-red-700',
    bg: 'bg-red-50',
    border: 'border-red-200',
    rotate: '-rotate-45',
  },
  estavel: {
    label: 'Nível estável',
    ariaLabel: 'Tendência: nível estável',
    color: 'text-slate-600',
    bg: 'bg-slate-50',
    border: 'border-slate-200',
    rotate: 'rotate-0',
  },
  caindo: {
    label: 'Nível caindo',
    ariaLabel: 'Tendência: nível caindo',
    color: 'text-blue-700',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    rotate: 'rotate-45',
  },
}

// Seta genérica — rotaciona para indicar direção
function ArrowIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={2.5}
      stroke="currentColor"
      className={className}
      aria-hidden="true"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
    </svg>
  )
}

export default function TrendIndicator({ taxaVariacao }: Props) {
  const trend = getTrend(taxaVariacao)
  const cfg = TREND_CONFIG[trend]

  return (
    <span
      aria-label={cfg.ariaLabel}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-semibold transition-all duration-300 ${cfg.bg} ${cfg.border} ${cfg.color}`}
    >
      <ArrowIcon className={`h-4 w-4 transition-transform duration-300 ${cfg.rotate}`} />
      {cfg.label}
    </span>
  )
}
