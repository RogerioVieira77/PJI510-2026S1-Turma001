// -----------------------------------------------
// Tipos espelhando os schemas do backend FastAPI
// -----------------------------------------------

export interface ReservatorioSummary {
  id: number
  nome: string
  latitude: string | number
  longitude: string | number
  capacidade_m3: number
  nivel_pct: number | null
  status: string | null
  ultima_atualizacao: string | null
}

export interface StatusReservatorio {
  reservatorio_id: number
  nivel_cm: number
  nivel_pct: number
  volume_m3: number
  taxa_cm_min: number
  tempo_transbordo_min: number | null
  status: string
  divergencia_sensores: boolean
  timestamp: string
}

export interface PontoHistorico {
  bucket: string
  media: number
  minimo: number
  maximo: number
}

export interface AlertaRead {
  id: number
  reservatorio_id: number
  nivel: string
  nivel_pct: number | null
  mensagem: string | null
  status: string
  criado_em: string
  reconhecido_em: string | null
}

export interface StatusPublico {
  id: number
  nome: string
  status: string
  nivel_pct: number | null
  ultima_atualizacao: string | null
}
