import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import RecentWindowsChart from '@/components/charts/RecentWindowsChart.vue'
import { useGlobalSearch } from '@/composables/useGlobalSearch'
import * as api from '@/services/api'
import type { DashboardSummary } from '@/types/api'
import DashboardView from '@/views/DashboardView.vue'
import { janela, promessaControlada, resumoDashboard, resumoHistorico } from '../fixtures/api'

beforeEach(() => {
  useGlobalSearch().globalSearch.value = ''
  vi.spyOn(api, 'getDashboardSummary').mockResolvedValue(resumoDashboard())
  vi.spyOn(api, 'getHistorySummary').mockResolvedValue(resumoHistorico())
  vi.spyOn(api, 'getHistoryWindows').mockResolvedValue({
    windows: Array.from({ length: 14 }, (_, index) => janela(index + 1)),
    meta: { total: 14, limit: 12, offset: 0, returned: 14 },
  })
})

async function abrirDashboard() {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/', component: DashboardView },
    { path: '/alerts', component: { template: '<div />' } },
    { path: '/windows/:id', component: { template: '<div />' } },
  ] })
  await router.push('/')
  return { tela: mount(DashboardView, { global: { plugins: [router] } }), router }
}

describe('Dashboard com histórico simulado', () => {
  it('apresenta loading até o resumo ser recebido', async () => {
    const resposta = promessaControlada<DashboardSummary>()
    vi.mocked(api.getDashboardSummary).mockReturnValue(resposta.promessa)
    const { tela } = await abrirDashboard()
    expect(tela.get('[role="status"]').attributes('aria-busy')).toBe('true')
    resposta.resolver(resumoDashboard())
    await flushPromises()
    expect(tela.find('[role="status"]').exists()).toBe(false)
    expect(tela.get('[data-testid="dashboard-card-analyses"]').text()).toContain('2')
  })

  it('usa até 12 janelas do histórico, sem vincular barras à análise importada', async () => {
    const { tela } = await abrirDashboard()
    await flushPromises()
    const grafico = tela.getComponent(RecentWindowsChart)
    expect(api.getHistoryWindows).toHaveBeenCalledExactlyOnceWith(12, 0)
    expect(grafico.props('items').map(item => item.id)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    expect(grafico.props('items').map(item => item.label)).toEqual(['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'])
    expect(grafico.props('title')).toBe('Últimas 12 janelas processadas')
    expect(grafico.text()).toContain('Recarregue a página para consultar atualizações.')
    expect(grafico.text().toLowerCase()).not.toContain('última análise')
    expect(tela.find('[data-testid="dashboard-recent-window-row-999"]').exists()).toBe(false)
  })

  it('aplica a busca existente às janelas e abre o detalhe complementar', async () => {
    vi.mocked(api.getHistoryWindows).mockResolvedValue({
      windows: [janela(1), janela(2, { attack_type: 'port_scan', final_label: 'anomaly', risk_level: 'high' })],
      meta: { total: 2, limit: 12, offset: 0, returned: 2 },
    })
    const { tela, router } = await abrirDashboard()
    await flushPromises()
    useGlobalSearch().globalSearch.value = 'port_scan'
    await flushPromises()
    expect(tela.getComponent(RecentWindowsChart).props('items').map(item => item.id)).toEqual([2])
    await tela.get('[data-testid="dashboard-open-window-2"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/windows/2')
    expect(api.getHistoryWindows).toHaveBeenCalledTimes(1)
  })

  it('mostra listas vazias sem criar janelas e alertas', async () => {
    vi.mocked(api.getDashboardSummary).mockResolvedValue({ ...resumoDashboard(), recent_windows: [] })
    vi.mocked(api.getHistoryWindows).mockResolvedValue({ windows: [], meta: { total: 0, limit: 12, offset: 0, returned: 0 } })
    const { tela } = await abrirDashboard()
    await flushPromises()
    expect(tela.getComponent(RecentWindowsChart).props('items')).toEqual([])
    expect(tela.text()).toContain('Nenhum alerta recente')
    expect(tela.text()).toContain('Nenhum resultado encontrado')
  })

  it('informa erro no resumo principal sem mascarar como estado vazio', async () => {
    vi.mocked(api.getDashboardSummary).mockRejectedValue(new Error('indisponível'))
    const { tela } = await abrirDashboard()
    await flushPromises()
    expect(tela.get('[role="alert"]').text()).toContain('Não foi possível carregar o resumo do Dashboard.')
    expect(tela.findComponent(RecentWindowsChart).exists()).toBe(false)
  })

  it('preserva dados disponíveis e informa falha parcial no histórico', async () => {
    vi.mocked(api.getHistoryWindows).mockRejectedValue(new Error('indisponível'))
    const { tela } = await abrirDashboard()
    await flushPromises()
    expect(tela.getComponent(RecentWindowsChart).props('items').map(item => item.id)).toEqual([999])
    expect(tela.get('[role="alert"]').text()).toContain('Parte do histórico não pôde ser consultada.')
  })
})
