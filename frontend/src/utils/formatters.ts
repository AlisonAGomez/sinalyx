/** Textos, datas e números para apresentação. Os resultados de análise vêm do servidor. */

const ATTACK_TYPE_LABELS: Record<string, string> = {
  normal: 'Sem indícios relevantes',
  anomaly: 'Atividade incomum',
  unknown_anomaly: 'Atividade incomum',
  port_scan: 'Varredura de portas',
  brute_force: 'Atividade SSH suspeita',
  ssh_bruteforce: 'Atividade SSH suspeita',
  syn_flood: 'SYN Flood',
  ddos: 'SYN Flood',
  ddo_s: 'SYN Flood',
  d_do_s: 'SYN Flood',
  ddo_s_syn_flood: 'SYN Flood',
  d_do_s_syn_flood: 'SYN Flood',
  ddos_syn_flood: 'SYN Flood',
  ssh_suspicious: 'Atividade SSH suspeita',
  suspicious: 'Suspeito',
  unknown: 'Desconhecido',
}

const RISK_LEVEL_LABELS: Record<string, string> = {
  low: 'Baixo',
  medium: 'Médio',
  high: 'Alto',
  critical: 'Crítico',
  unknown: 'Desconhecido',
}

const FINAL_LABELS: Record<string, string> = {
  normal: 'Sem indícios relevantes',
  anomaly: 'Atividade incomum',
  unknown_anomaly: 'Atividade incomum',
  available: 'Disponível',
  unavailable: 'Indisponível',
  success: 'Sucesso',
  suspicious: 'Suspeito',
  unknown: 'Desconhecido',
}

const DECISION_SOURCE_LABELS: Record<string, string> = {
  decision_engine: 'Consolidação final',
  ensemble: 'Conjunto de sinais',
  heuristic: 'Regras de segurança',
  heuristic_signature: 'Regras de segurança',
  autoencoder: 'Modelo de anomalia',
  isolation_forest: 'Análise estatística',
  safe_negative: 'Análise segura',
  ae_high_risk: 'Autoencoder com alto risco',
  contextual_support: 'Suporte contextual',
  full_agreement_negative: 'Concordância normal',
  if_filtered: 'Filtrado pelo Isolation Forest',
  system: 'Sistema',
  unknown: 'Desconhecida',
}

const TECHNICAL_LABELS: Record<string, string> = {
  final_label: 'Classificação final',
  attack_type: 'Tipo de ataque',
  risk_level: 'Nível de risco',
  decision_source: 'Fonte da decisão',
  decision_reason: 'Motivo da decisão',
  confidence: 'Confiança',
  ai_support: 'Apoio da IA',
  ai_support_conservative: 'Apoio conservador da IA',
  ai_support_reason: 'Motivo do apoio da IA',
  ai_support_signals: 'Sinais de apoio da IA',
  ai_support_type: 'Tipo de apoio da IA',
  ai_support_level: 'Nível de apoio da IA',
  autoencoder_score: 'Pontuação do Autoencoder',
  score_ae: 'Pontuação do Autoencoder',
  isolation_score: 'Pontuação do Isolation Forest',
  score_if: 'Pontuação do Isolation Forest',
  score_if_normalized: 'Pontuação normalizada do Isolation Forest',
  normalized_score: 'Pontuação normalizada',
  ensemble_score: 'Pontuação combinada da IA',
  score_ensemble: 'Pontuação combinada da IA',
  heuristic_signature: 'Regras de segurança',
  safe_negative: 'Análise segura',
  ae_high_risk: 'Autoencoder com alto risco',
  contextual_support: 'Suporte contextual',
  full_agreement_negative: 'Concordância normal',
  if_filtered: 'Filtrado pelo Isolation Forest',
  agreement_level: 'Nível de concordância',
  conflict_winner: 'Critério predominante',
  connections: 'Conexões',
  packets: 'Pacotes',
  bytes: 'Bytes',
  packet_size: 'Tamanho do pacote',
  ports: 'Portas',
  bytes_per_packet: 'Bytes por pacote',
  bytes_per_connection: 'Bytes por conexão',
  packets_per_connection: 'Pacotes por conexão',
  log1p_connections: 'Log1p de conexões',
  log1p_bytes: 'Log1p de bytes',
  log1p_packets: 'Log1p de pacotes',
  log1p_packet_size: 'Log1p do tamanho do pacote',
  log1p_ports: 'Log1p de portas',
  event_count: 'Eventos',
  source_ip: 'IP de origem',
  src_ip: 'IP de origem',
  destination_ip: 'IP de destino',
  destination_ip_sample: 'IP de destino',
  dst_ip: 'IP de destino',
  dst_port: 'Porta de destino',
  destination_port_min: 'Menor porta de destino',
  destination_port_max: 'Maior porta de destino',
  destination_port_count: 'Total de portas de destino',
  common_destination_ports: 'Portas de destino comuns',
  tcp_syn_count: 'Pacotes TCP SYN',
  tcp_pa_count: 'Pacotes TCP PA',
  tcp_flags_summary: 'Resumo de flags TCP',
  blocked_count: 'Bloqueios',
  passed_count: 'Permitidos',
  protocol: 'Protocolo',
  action: 'Ação',
  interface: 'Interface',
  window_start: 'Início da janela',
  window_end: 'Fim da janela',
  window_id: 'ID da janela',
  execution_id: 'ID da execução',
}

const FRIENDLY_AI_SUPPORT_REASON =
  'Foram encontrados indicadores complementares para apoiar esta análise. Eles não alteram a classificação final, o padrão identificado nem o nível de risco.'

const FRIENDLY_NO_AI_SUPPORT_REASON =
  'Não foram encontrados indicadores complementares suficientes nesta janela. A classificação final permanece inalterada.'

const TEXT_REPLACEMENTS: Record<string, string> = {
  ensemble_score: 'Pontuação combinada da IA',
  score_ensemble: 'Pontuação combinada da IA',
  autoencoder_score: 'Pontuação do Autoencoder',
  score_ae: 'Pontuação do Autoencoder',
  score_if_normalized: 'Pontuação normalizada do Isolation Forest',
  final_label: 'Classificação final',
  attack_type: 'Tipo de ataque',
  risk_level: 'Nível de risco',
  ai_support: 'Apoio da IA',
  heuristic_signature: 'Regras de segurança',
  safe_negative: 'Análise segura',
  ae_high_risk: 'Autoencoder com alto risco',
  contextual_support: 'Suporte contextual',
  full_agreement_negative: 'Concordância normal',
  if_filtered: 'Filtrado pelo Isolation Forest',
  unknown_anomaly: 'Atividade incomum',
  syn_flood: 'SYN Flood',
}

const DISPLAY_VALUE_LABELS: Record<string, string> = {
  ...ATTACK_TYPE_LABELS,
  ...RISK_LEVEL_LABELS,
  ...FINAL_LABELS,
  ...DECISION_SOURCE_LABELS,
  true: 'Sim',
  false: 'Não',
  none: 'Nenhum',
}

/** Padroniza o texto para consultar os rótulos conhecidos. */
function normalize(value?: string | number | boolean | null): string {
  return normalizeTechnicalKey(value ?? 'unknown') || 'unknown'
}

/** Padroniza uma chave técnica para procurar seu nome de apresentação. */
function normalizeTechnicalKey(value: unknown): string {
  return String(value ?? 'unknown')
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toLowerCase()
}

/** Produz um rótulo legível quando não há tradução cadastrada para o campo. */
function fallbackLabel(value?: string | number | boolean | null): string {
  const text = String(value ?? 'unknown')
  return normalizeTechnicalKey(text)
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

/** Padroniza um texto para comparar termos independentemente da apresentação. */
function normalizeForMatch(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

/** Troca termos internos conhecidos por descrições voltadas ao usuário. */
function replaceTechnicalTerms(value: string): string {
  const synFloodPlaceholder = '__SINALYX_DDOS_SYN_FLOOD__'
  let text = value
    .replace(/\bDDoS\s*\/\s*SYN Flood\b/gi, synFloodPlaceholder)
    .replace(/\bUnknown Anomaly\b/gi, 'Anomalia não classificada')
    .replace(/\bsyn flood\b/gi, 'SYN Flood')

  Object.entries(TEXT_REPLACEMENTS).forEach(([technical, label]) => {
    text = text.replace(new RegExp(`\\b${technical}\\b`, 'gi'), label)
  })

  return text.replace(new RegExp(synFloodPlaceholder, 'g'), 'SYN Flood')
}

/** Reconhece uma justificativa de apoio auxiliar dos modelos já registrada. */
function isAiSupportReason(value: string): boolean {
  const text = normalizeForMatch(value)
  return (
    text.includes('metadado auxiliar sem alterar')
    && (
      text.includes('suporte da ia')
      || text.includes('ensemble_score')
      || text.includes('autoencoder_score')
      || text.includes('score_if_normalized')
    )
  )
}

/** Reconhece uma justificativa registrada de ausência de apoio auxiliar dos modelos. */
function isNoAiSupportReason(value: string): boolean {
  const text = normalizeForMatch(value)
  return (
    text.includes('nenhum criterio calibrado de suporte da ia')
    || text.includes('nenhum critério calibrado de suporte da ia')
  )
}

/** Apresenta o tipo de evento recebido sem confirmar a ocorrência de um ataque. */
export function formatAttackType(value?: string | null): string {
  const key = normalize(value)
  return ATTACK_TYPE_LABELS[key] ?? fallbackLabel(value)
}

/** Traduz a categoria de risco já calculada pelo servidor. */
export function formatRiskLevel(value?: string | null): string {
  const key = normalize(value)
  return RISK_LEVEL_LABELS[key] ?? fallbackLabel(value)
}

/** Traduz a classificação final já calculada pelo servidor. */
export function formatFinalLabel(value?: string | null): string {
  const key = normalize(value)
  return FINAL_LABELS[key] ?? fallbackLabel(value)
}

/** Traduz o nome da origem da decisão para apresentação. */
export function formatDecisionSource(value?: string | null): string {
  const key = normalize(value)
  return DECISION_SOURCE_LABELS[key] ?? fallbackLabel(value)
}

const formatoDataHoraLocal = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit', month: '2-digit', year: 'numeric',
  hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
})

const formatoConfianca = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

/** Formata o indicador de confiança informado; não o transforma em probabilidade de ataque. */
export function formatarConfianca(valor: unknown): string {
  return typeof valor === 'number' && Number.isFinite(valor)
    ? formatoConfianca.format(valor)
    : 'Não informado'
}

/** Apresenta a data e hora no formato local definido para a interface. */
export function formatDateTime(value?: string | null): string {
  if (!value) return '-'
  const texto = value.trim()
  // Só converte instantes com fuso explícito; logs antigos podem não informá-lo.
  if (/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})$/i.test(texto)) {
    const instante = new Date(texto.replace(' ', 'T'))
    if (!Number.isNaN(instante.getTime())) {
      return formatoDataHoraLocal.format(instante).replace(',', '')
    }
  }
  // Reordena a apresentação sem atribuir fuso ao horário registrado.
  const semFuso = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}:\d{2}(?::\d{2})?)(?:\.\d+)?)?$/.exec(texto)
  if (semFuso) {
    return `${semFuso[3]}/${semFuso[2]}/${semFuso[1]}${semFuso[4] ? ` ${semFuso[4]}` : ''}`
  }
  return texto
}

/** Apresenta o nome legível de um campo técnico conhecido. */
export function formatTechnicalLabel(value: string): string {
  const key = normalizeTechnicalKey(value)
  return TECHNICAL_LABELS[key] ?? fallbackLabel(value)
}

/** Traduz a justificativa auxiliar dos modelos sem alterar a decisão. */
export function formatAiSupportReason(value?: unknown): string {
  const text = String(value ?? '').trim()
  if (!text) {
    return 'Sem indicadores adicionais nesta janela.'
  }
  if (isAiSupportReason(text)) {
    return FRIENDLY_AI_SUPPORT_REASON
  }
  if (isNoAiSupportReason(text)) {
    return FRIENDLY_NO_AI_SUPPORT_REASON
  }
  return replaceTechnicalTerms(text)
}

/** Prepara o texto recebido para apresentação com os rótulos conhecidos. */
export function formatDisplayText(value?: unknown): string {
  const text = String(value ?? '').trim()
  if (!text) {
    return ''
  }
  const exactLabel = DISPLAY_VALUE_LABELS[normalize(text)]
  return exactLabel ?? formatAiSupportReason(text)
}
