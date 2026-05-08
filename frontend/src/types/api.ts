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
  // Campos de energia e estado (PJI510)
  bms_nivel?: 'normal' | 'alerta' | 'critico' | null
  fonte_alimentacao?: 'rede' | 'bateria' | null
  bateria_pct_min?: number | null
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

export interface LeituraPublica {
  sensor_id: number
  codigo: string
  descricao: string
  valor: number | null
  unidade: string | null
  timestamp: string | null
}

export interface EstacaoPublica {
  codigo_estacao: string
  descricao: string
  temperatura: number | null
  umidade: number | null
  pressao: number | null
  pluviometro: number | null
  vento_velocidade: number | null
  vento_direcao: number | null
  timestamp: string | null
}

export interface LeituraSensoresPublico {
  sensores_nivel: LeituraPublica[]
  estacoes: EstacaoPublica[]
  atualizado_em: string
}
