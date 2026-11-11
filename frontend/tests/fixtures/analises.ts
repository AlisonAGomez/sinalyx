import type { AnalysisDetails, AnalysisResultItem, AnalysisResultsResponse } from '@/types/api'

export function analise(id: string, total = 1): AnalysisDetails {
  return {
    status: 'success', analysis_id: id, filename: `analise-${id}.log`,
    created_at: '2026-01-01T12:00:00Z', total_windows: total,
  }
}

export function paginaAnalise(id: string, total = 1, offset = 0): AnalysisResultsResponse {
  const results: AnalysisResultItem[] = Array.from({ length: Math.min(50, Math.max(0, total - offset)) }, (_, index) => ({
    window_id: `${id}-janela-${offset + index + 1}`, final_label: 'normal',
    attack_type: 'normal', risk_level: 'low', explanation: `Motivo sintético ${offset + index + 1}`,
  }))
  return {
    ...analise(id, total), results, data: { results },
    meta: { total, limit: 50, offset, returned: results.length },
  }
}
