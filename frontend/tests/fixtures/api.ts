import type { AuthLoginData, AuthUser, DashboardSummary, HistorySummary, WindowItem } from '@/types/api'

export function usuario(role: AuthUser['role'] = 'user'): AuthUser {
  return {
    id: 1, name: 'Pessoa de QA', email: 'pessoa@example.test', role, is_active: true,
    created_at: '2026-01-01T12:00:00Z', updated_at: '2026-01-01T12:00:00Z',
  }
}

export function sessao(role: AuthUser['role'] = 'user'): AuthLoginData {
  return { access_token: 'token-sintetico-sem-validade', token_type: 'bearer', expires_in: 3600, user: usuario(role) }
}

export function janela(id: number, campos: Partial<WindowItem> = {}): WindowItem {
  return {
    id, window_id: `janela-qa-${id}`, window_start: '2026-01-01T12:00:00Z',
    final_label: 'normal', attack_type: 'normal', risk_level: 'low',
    explanation: 'Registro sintético para teste de apresentação.', ...campos,
  }
}

export function resumoDashboard(): DashboardSummary {
  return {
    total_windows: 14, total_normal: 10, total_anomalies: 4,
    attack_type_distribution: {}, risk_level_distribution: {},
    ai_support_count: 0, ai_support_conservative_count: 0,
    recent_windows: [janela(999)],
  }
}

export function resumoHistorico(): HistorySummary {
  return {
    analyses: { total_analyses: 2, total_results: 33 },
    live: { total_windows: 14, total_alerts: 4, total_executions: 3 },
  }
}

// Controla a ordem de respostas sem sleeps; reutilizável no futuro AUD-06.
export function promessaControlada<T>() {
  let resolver!: (valor: T) => void
  let rejeitar!: (motivo: unknown) => void
  const promessa = new Promise<T>((resolve, reject) => { resolver = resolve; rejeitar = reject })
  return { promessa, resolver, rejeitar }
}
