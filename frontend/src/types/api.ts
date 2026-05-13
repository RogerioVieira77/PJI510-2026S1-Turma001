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
  nivel_medio_m: number | null
  nivel_medio_pct: number | null
  volume_medio_m3: number | null
}

export interface SensorStatusItem {
  sensor_id: number
  nome: string
  codigo: string
  ativo: boolean
  tipo_display: string
  fonte_alimentacao: 'rede' | 'bateria' | null
  bateria_pct: number | null
  bms_nivel: 'normal' | 'alerta' | 'critico' | null
  ultima_leitura: string | null
}

export interface BombaStatusItem {
  sensor_id: number
  nome: string
  codigo: string
  ligada: boolean | null
  ultima_leitura: string | null
  fonte_alimentacao: 'rede' | 'bateria' | null
  bateria_pct: number | null
  bms_nivel: 'normal' | 'alerta' | 'critico' | null
}

// ── Alertas externos (Defesa Civil + Previsão de Chuva) ──────────────────────

export interface PrevisaoChuvaPublica {
  id: number
  regiao: string
  nivel: number        // 1-5
  descricao: string
  precipitacao_mm: number
  timestamp: string
}

export interface AlertaAtivoPublico {
  regiao: string
  descricao: string
  severidade: string   // normal | atencao | critico
}

export interface SituacaoDefesaCivilPublica {
  id: number
  status: 'verde' | 'amarelo' | 'laranja' | 'vermelho'
  alertas_ativos: AlertaAtivoPublico[]
  timestamp: string
}

export interface AlertaDefesaCivilPublico {
  id: number
  titulo: string
  descricao: string
  regiao: string
  valido_ate: string
  timestamp: string
}

export interface AlertasExternos {
  previsao_chuva: PrevisaoChuvaPublica | null
  situacao_defesa_civil: SituacaoDefesaCivilPublica | null
  alertas_defesa_civil: AlertaDefesaCivilPublico[]
}
