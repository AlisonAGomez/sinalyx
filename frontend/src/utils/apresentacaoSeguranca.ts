/** Apresenta classificações e justificativas em linguagem de investigação. */

// Formatação operacional: não altera os valores nem reconstrói a decisão.
function chave(valor: unknown): string {
  return String(valor ?? '').trim().normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '')
}

const classificacoes: Record<string, string> = {
  normal: 'Sem indícios relevantes', benign: 'Sem indícios relevantes', benigno: 'Sem indícios relevantes',
  anomaly: 'Atividade incomum', anomalia: 'Atividade incomum', unknown_anomaly: 'Atividade incomum',
  unclassified_anomaly: 'Atividade incomum', anomalia_nao_classificada: 'Atividade incomum',
  brute_force: 'Atividade SSH suspeita', ssh_bruteforce: 'Atividade SSH suspeita', ssh_brute_force: 'Atividade SSH suspeita',
  forca_bruta_ssh: 'Atividade SSH suspeita', ssh_suspicious: 'Atividade SSH suspeita',
  syn_flood: 'SYN Flood', ddos: 'SYN Flood', ddo_s: 'SYN Flood', d_do_s: 'SYN Flood', ddo_s_syn_flood: 'SYN Flood', ddos_syn_flood: 'SYN Flood', d_do_s_syn_flood: 'SYN Flood',
  port_scan: 'Varredura de portas', varredura_de_portas: 'Varredura de portas',
}

/** Apresenta a classificação recebida em linguagem de investigação. */
export function formatarClassificacao(valor: unknown): string {
  return classificacoes[chave(valor)] ?? 'Classificação não informada'
}

const motivos: Record<string, string> = {
  heuristic: 'Padrão identificado pelas regras de segurança',
  heuristic_signature: 'Padrão identificado pelas regras de segurança',
  heuristic_guided_attack: 'Padrão identificado pelas regras de segurança',
  contextual_attack: 'O contexto observado sustentou a classificação suspeita',
  contextual_support: 'O contexto observado contribuiu para a classificação',
  ensemble: 'O conjunto de sinais sustentou a classificação',
  ensemble_support: 'O conjunto de sinais sustentou a classificação suspeita',
  if_ae: 'Os sinais analisados concordaram na indicação de atividade suspeita',
  safe_negative: 'Não foram encontrados indícios suficientes de atividade suspeita',
  full_agreement_negative: 'Os sinais concordaram na ausência de indícios relevantes',
  suppressed_by_context: 'O contexto observado não sustentou o alerta',
  if_filtered: 'O sinal estatístico não foi suficiente para sustentar o alerta',
  autoencoder: 'O comportamento observado se afastou do padrão esperado',
  ae_high_risk: 'O comportamento observado se afastou do padrão esperado',
  ae_medium_risk: 'O comportamento observado se afastou do padrão esperado',
  ae_contextual_band: 'O desvio do padrão esperado foi acompanhado por sinais de contexto',
}

/** Converte o nome técnico da origem da decisão em um rótulo legível. */
export function formatarFonte(valor: unknown): string {
  return motivos[chave(valor)] ?? 'Motivo detalhado não informado'
}

/** Apresenta o motivo registrado sem inventar justificativas ou recalcular a decisão. */
export function formatarMotivo(resultado: { decision_source?: unknown; decision_reason?: unknown; explanation?: unknown }): string {
  for (const valor of [resultado.decision_reason, resultado.explanation]) {
    if (typeof valor !== 'string' || !valor.trim()) continue
    const mensagem = mensagensOperacionais[chave(valor)] ?? motivos[chave(valor)]
    if (mensagem) return mensagem
  }
  return motivos[chave(resultado.decision_source)] ?? 'Resultado definido pelos sinais observados nesta janela.'
}

// Correspondência exata evita confundir contexto negativo com confirmação de indícios.
// O texto original permanece no registro; aqui só muda a apresentação operacional.
const mensagensOperacionais: Record<string, string> = Object.fromEntries([
  [
    'O Autoencoder permaneceu na zona baixa de anomalia e nao houve sinal suficiente para elevar o caso.',
    'Não foram encontrados sinais suficientes para indicar atividade suspeita.',
  ],
  [
    'O Autoencoder entrou em zona alta e houve corroboracao suficiente no ensemble, no IF ou no contexto heuristico para preservar o alerta.',
    'Foram encontrados sinais consistentes de comportamento fora do padrão.',
  ],
  [
    'O Autoencoder entrou em zona alta, mas o contexto heuristico pertence a uma familia com alto falso positivo e bloqueou o alerta neste perfil conservador.',
    'O contexto observado não sustentou o alerta.',
  ],
].map(([mensagem, rotulo]) => [chave(mensagem), rotulo]))
