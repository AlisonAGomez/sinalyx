/** Comunicação HTTP com o servidor. Envia a sessão e preserva os formatos atuais e legados. */

import axios from 'axios'

import type {
  AlertItem,
  AnalysisDetails,
  AnalysisItem,
  AnalysisResultsResponse,
  ApiEnvelope,
  AuthLoginData,
  AuthUser,
  DashboardSummary,
  HealthStatus,
  HistoryExecution,
  HistorySummary,
  LiveStatusResponse,
  PaginationMeta,
  SystemBlock,
  SystemAudit,
  SystemStatus,
  UserPayload,
  WindowFilters,
  WindowItem,
} from '@/types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    Accept: 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem('sinalyx_access_token')
  const requestUrl = String(config.url ?? '')
  const isLoginRequest = requestUrl.includes('/auth/login')
  // Nunca anexa um token antigo à requisição de login.
  if (token && !isLoginRequest) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const requestUrl = String(error?.config?.url ?? '')
    const isLoginRequest = requestUrl.includes('/auth/login')

    if (status === 401 && !isLoginRequest) {
      window.localStorage.removeItem('sinalyx_access_token')
      window.localStorage.removeItem('sinalyx_user')

      if (window.location.pathname !== '/login') {
        const currentPath = `${window.location.pathname}${window.location.search}`
        const redirect = currentPath && currentPath !== '/'
          ? `?redirect=${encodeURIComponent(currentPath)}`
          : ''
        window.location.assign(`/login${redirect}`)
      }
    }

    return Promise.reject(error)
  },
)

/** Aceita a lista no formato atual da API e no formato antigo ainda suportado. */
function unwrapArray<TItem>(
  payload: unknown,
  primaryKey: string,
  legacyKey: string,
): TItem[] {
  const record = payload as Record<string, unknown>
  const data = record.data as Record<string, unknown> | undefined
  const primary = data?.[primaryKey]
  const legacy = record[legacyKey]

  if (Array.isArray(primary)) {
    return primary as TItem[]
  }
  if (Array.isArray(legacy)) {
    return legacy as TItem[]
  }
  return []
}

/** Consulta os contadores e as janelas que a API disponibiliza para o painel. */
export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await api.get<ApiEnvelope<DashboardSummary>>('/dashboard/summary')
  return response.data.data
}

/** Consulta uma página dos alertas recentes e seus dados de paginação. */
export async function getRecentAlerts(limit = 20, offset = 0): Promise<{
  alerts: AlertItem[]
  meta: PaginationMeta
}> {
  const response = await api.get<ApiEnvelope<{ alerts: AlertItem[] }, PaginationMeta>>(
    '/alerts/recent',
    { params: { limit, offset } },
  )

  return {
    alerts: response.data.data.alerts,
    meta: response.data.meta ?? {
      total: response.data.data.alerts.length,
      limit,
      offset,
      returned: response.data.data.alerts.length,
    },
  }
}

/** Converte os filtros preenchidos em parâmetros da requisição. */
function filterParams(
  limit: number,
  offset: number,
  filters: WindowFilters = {},
): Record<string, string | number | boolean> {
  const params: Record<string, string | number | boolean> = { limit, offset }

  if (filters.final_label) {
    params.final_label = filters.final_label
  }
  if (filters.attack_type) {
    params.attack_type = filters.attack_type
  }
  if (filters.risk_level) {
    params.risk_level = filters.risk_level
  }
  if (typeof filters.ai_support === 'boolean') {
    params.ai_support = filters.ai_support
  }
  if (filters.date_from) {
    params.date_from = filters.date_from
  }
  if (filters.date_to) {
    params.date_to = filters.date_to
  }

  return params
}

/** Consulta o resumo do histórico com os filtros informados. */
export async function getHistorySummary(): Promise<HistorySummary> {
  const response = await api.get<ApiEnvelope<HistorySummary>>('/history/summary')
  return response.data.data
}

/** Consulta uma página das janelas complementares do histórico. */
export async function getHistoryWindows(
  limit = 20,
  offset = 0,
  filters: WindowFilters = {},
): Promise<{
  windows: WindowItem[]
  meta: PaginationMeta
}> {
  const response = await api.get<ApiEnvelope<{ windows: WindowItem[] }, PaginationMeta>>(
    '/history/windows',
    { params: filterParams(limit, offset, filters) },
  )
  const windows = response.data.data.windows ?? []

  return {
    windows,
    meta: response.data.meta ?? {
      total: windows.length,
      limit,
      offset,
      returned: windows.length,
    },
  }
}

/** Consulta uma página dos alertas do histórico. */
export async function getHistoryAlerts(
  limit = 20,
  offset = 0,
  filters: WindowFilters = {},
): Promise<{
  alerts: AlertItem[]
  meta: PaginationMeta
}> {
  const response = await api.get<ApiEnvelope<{ alerts: AlertItem[] }, PaginationMeta>>(
    '/history/alerts',
    { params: filterParams(limit, offset, filters) },
  )
  const alerts = response.data.data.alerts ?? []

  return {
    alerts,
    meta: response.data.meta ?? {
      total: alerts.length,
      limit,
      offset,
      returned: alerts.length,
    },
  }
}

/** Consulta as execuções complementares registradas no histórico. */
export async function getHistoryExecutions(
  limit = 20,
  offset = 0,
): Promise<{
  executions: HistoryExecution[]
  meta: PaginationMeta
}> {
  const response = await api.get<ApiEnvelope<{ executions: HistoryExecution[] }, PaginationMeta>>(
    '/history/executions',
    { params: { limit, offset } },
  )
  const executions = response.data.data.executions ?? []

  return {
    executions,
    meta: response.data.meta ?? {
      total: executions.length,
      limit,
      offset,
      returned: executions.length,
    },
  }
}

/** Busca uma janela do histórico pelo identificador informado. */
export async function getHistoryWindowById(id: string | number): Promise<WindowItem> {
  const response = await api.get<ApiEnvelope<{ window: WindowItem }>>(
    `/history/windows/${id}`,
  )
  return response.data.data.window
}

/** Envia e-mail e senha ao login; os dados de sessão vêm da resposta da API. */
export async function loginUser(email: string, password: string): Promise<AuthLoginData> {
  const response = await api.post<ApiEnvelope<AuthLoginData>>('/auth/login', {
    email,
    password,
  })
  return response.data.data
}

/** Consulta a conta associada ao token atual. */
export async function getCurrentUser(): Promise<AuthUser> {
  const response = await api.get<ApiEnvelope<{ user: AuthUser }>>('/auth/me')
  return response.data.data.user
}

/** Consulta as contas; a API exige permissão de administrador. */
export async function getAdminUsers(limit = 50, offset = 0): Promise<{
  users: AuthUser[]
  meta: PaginationMeta
}> {
  const response = await api.get<ApiEnvelope<{ users: AuthUser[] }, PaginationMeta>>(
    '/admin/users',
    { params: { limit, offset } },
  )
  const users = response.data.data.users ?? []
  return {
    users,
    meta: response.data.meta ?? {
      total: users.length,
      limit,
      offset,
      returned: users.length,
    },
  }
}

/** Solicita a criação de uma conta, sujeita à autorização da API. */
export async function createAdminUser(payload: UserPayload): Promise<AuthUser> {
  const response = await api.post<ApiEnvelope<{ user: AuthUser }>>(
    '/admin/users',
    payload,
  )
  return response.data.data.user
}

/** Solicita a atualização de uma conta, sujeita à autorização da API. */
export async function updateAdminUser(
  id: number,
  payload: Partial<UserPayload>,
): Promise<AuthUser> {
  const response = await api.put<ApiEnvelope<{ user: AuthUser }>>(
    `/admin/users/${id}`,
    payload,
  )
  return response.data.data.user
}

/** Solicita a ativação ou desativação de uma conta na API. */
export async function updateAdminUserStatus(
  id: number,
  isActive: boolean,
): Promise<AuthUser> {
  const response = await api.patch<ApiEnvelope<{ user: AuthUser }>>(
    `/admin/users/${id}/status`,
    { is_active: isActive },
  )
  return response.data.data.user
}

/** Solicita a exclusão de uma conta; a API valida a permissão e as restrições. */
export async function deleteAdminUser(id: number): Promise<AuthUser> {
  const response = await api.delete<ApiEnvelope<{ user: AuthUser }>>(
    `/admin/users/${id}`,
  )
  return response.data.data.user
}

/** Obtém o detalhe da janela pelo serviço de consulta do histórico. */
export async function getWindowById(id: string | number): Promise<WindowItem | null> {
  const target = Number(id)
  if (!Number.isFinite(target)) {
    return null
  }

  try {
    return await getHistoryWindowById(target)
  } catch {
    // Fallback temporario para compatibilidade com backends sem o endpoint por ID.
  }

  const limit = 100
  let offset = 0
  let total = limit

  while (offset < total && offset < 1000) {
    const response = await getHistoryWindows(limit, offset)
    const found = response.windows.find((window) => window.id === target)
    if (found) {
      return found
    }
    total = response.meta.total
    offset += limit
  }

  return null
}

/** Consulta a listagem de análises já processadas. */
export async function getAnalyses(limit = 20, offset = 0): Promise<{
  analyses: AnalysisItem[]
  meta: PaginationMeta
}> {
  const response = await api.get('/analyses', { params: { limit, offset } })
  const analyses = unwrapArray<AnalysisItem>(response.data, 'analyses', 'analyses')

  return {
    analyses,
    meta: response.data.meta ?? {
      total: Number(response.data.total_analyses ?? analyses.length),
      limit,
      offset,
      returned: analyses.length,
    },
  }
}

/** Consulta o resumo de uma análise pelo identificador. */
export async function getAnalysisDetails(analysisId: string): Promise<AnalysisDetails> {
  const response = await api.get<AnalysisDetails>(`/analyses/${analysisId}`)
  return response.data
}

/** Consulta uma página dos resultados da análise, preservando o formato recebido. */
export async function getAnalysisResults(
  analysisId: string,
  limit = 50,
  offset = 0,
): Promise<AnalysisResultsResponse> {
  const response = await api.get<AnalysisResultsResponse>(
    `/analyses/${analysisId}/results`,
    { params: { limit, offset } },
  )
  return response.data
}

/** Consulta o estado de saúde publicado pela API. */
export async function getHealth(): Promise<HealthStatus> {
  const response = await api.get<HealthStatus>('/health')
  return response.data
}

/** Consulta o último estado registrado do leitor incremental experimental. */
export async function getParserStatus(): Promise<LiveStatusResponse> {
  const response = await api.get<LiveStatusResponse>('/live/pfsense/parser/status')
  return response.data
}

/** Consulta o último estado registrado da coleta experimental. */
export async function getCollectorStatus(): Promise<LiveStatusResponse> {
  const response = await api.get<LiveStatusResponse>('/live/pfsense/collector/status')
  return response.data
}

/** Converte sucesso ou falha de uma consulta em um bloco de estado para a tela. */
function blockFromSettled<TData>(
  result: PromiseSettledResult<TData>,
  fallbackMessage: string,
): SystemBlock<TData> {
  if (result.status === 'fulfilled') {
    return {
      ok: true,
      data: result.value,
    }
  }

  return {
    ok: false,
    // Não repassa mensagens internas do cliente/servidor para a camada visual.
    error: fallbackMessage,
  }
}

/** Reúne as consultas de estado sem impedir a apresentação quando uma delas falha. */
export async function getSystemStatus(): Promise<SystemStatus> {
  const [health, parser, collector] = await Promise.allSettled([
    getHealth(),
    getParserStatus(),
    getCollectorStatus(),
  ])

  return {
    health: blockFromSettled(health, 'Falha ao consultar /health.'),
    parser: blockFromSettled(parser, 'Falha ao consultar /live/pfsense/parser/status.'),
    collector: blockFromSettled(
      collector,
      'Falha ao consultar /live/pfsense/collector/status.',
    ),
  }
}

/** Consulta o diagnóstico operacional seguro disponibilizado pelo servidor. */
export async function getSystemAudit(): Promise<SystemAudit> {
  const response = await api.get<ApiEnvelope<SystemAudit>>('/system/audit')
  return response.data.data
}

/** Retorna o endereço configurado para as requisições da interface. */
export function apiBaseUrl(): string {
  return API_BASE_URL
}
