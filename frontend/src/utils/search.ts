/** Busca textual local sobre os campos disponíveis dos registros. */

import type { AnalysisItem, HistoryExecution, WindowItem } from '@/types/api'
import {
  formatAttackType,
  formatDecisionSource,
  formatDisplayText,
  formatFinalLabel,
  formatRiskLevel,
} from '@/utils/formatters'

/** Padroniza espaços, letras e acentos para a busca textual. */
export function normalizeSearchText(value: unknown): string {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

/** Reúne valores do objeto em texto para pesquisa. */
function textFromObject(value: unknown): string {
  if (value === null || typeof value === 'undefined') {
    return ''
  }
  if (typeof value !== 'object') {
    return String(value)
  }
  if (Array.isArray(value)) {
    return value.map(textFromObject).join(' ')
  }
  return Object.entries(value as Record<string, unknown>)
    .map(([key, entryValue]) => [key, formatDisplayText(key), textFromObject(entryValue)].join(' '))
    .join(' ')
}

/** Verifica se o texto atende aos termos de busca informados. */
export function matchesSearch(text: string, query: string): boolean {
  const cleanQuery = normalizeSearchText(query)
  if (!cleanQuery) {
    return true
  }
  return normalizeSearchText(text).includes(cleanQuery)
}

/** Filtra a lista local pelo texto de busca sem alterar seus registros. */
export function filterBySearch<TItem>(
  items: TItem[],
  query: string,
  getText: (item: TItem) => string,
): TItem[] {
  if (!query.trim()) {
    return items
  }
  return items.filter((item) => matchesSearch(getText(item), query))
}

/** Reúne os campos pesquisáveis da janela. */
export function windowSearchText(window: WindowItem): string {
  return [
    window.id,
    window.window_id,
    window.execution_id,
    window.final_label,
    formatFinalLabel(window.final_label),
    window.attack_type,
    formatAttackType(window.attack_type),
    window.risk_level,
    formatRiskLevel(window.risk_level),
    window.decision_source,
    formatDecisionSource(window.decision_source),
    window.src_ip,
    window.dst_ip,
    window.dst_port,
    window.protocol,
    window.action,
    textFromObject(window.features),
    textFromObject(window.metadata),
  ]
    .filter(Boolean)
    .join(' ')
}

/** Reúne os campos pesquisáveis da execução complementar. */
export function executionSearchText(execution: HistoryExecution): string {
  return [
    execution.execution_id,
    execution.total_windows,
    execution.total_anomalies,
    textFromObject(execution.final_label_distribution),
    textFromObject(execution.attack_type_distribution),
    textFromObject(execution.risk_level_distribution),
    execution.local_log_path,
    execution.remote_path,
  ]
    .filter(Boolean)
    .join(' ')
}

/** Reúne os campos pesquisáveis da análise importada. */
export function analysisSearchText(analysis: AnalysisItem): string {
  return [
    analysis.analysis_id,
    analysis.filename,
    analysis.final_status,
    analysis.predominant_attack_type,
    formatAttackType(analysis.predominant_attack_type),
    analysis.predominant_risk_level,
    formatRiskLevel(analysis.predominant_risk_level),
    analysis.total_windows,
  ]
    .filter(Boolean)
    .join(' ')
}
