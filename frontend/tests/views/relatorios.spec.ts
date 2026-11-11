import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as api from '@/services/api'
import * as exportadores from '@/utils/exporters'
import { validacaoHistorica } from '@/utils/validacaoHistorica'
import ReportsView from '@/views/ReportsView.vue'
import { promessaControlada, resumoHistorico } from '../fixtures/api'
import type { HistorySummary } from '@/types/api'

beforeEach(() => {
  vi.spyOn(api, 'getHistorySummary').mockResolvedValue(resumoHistorico())
  vi.spyOn(api, 'getHistoryWindows').mockResolvedValue({ windows: [], meta: { total: 0, limit: 20, offset: 0, returned: 0 } })
  vi.spyOn(api, 'getHistoryAlerts').mockResolvedValue({ alerts: [], meta: { total: 0, limit: 20, offset: 0, returned: 0 } })
  vi.spyOn(api, 'getSystemStatus').mockResolvedValue({ health: { ok: true }, parser: { ok: false }, collector: { ok: false } })
})

describe('Relatórios: evidência histórica separada do operacional', () => {
  it('mostra os nomes e percentuais documentados sem recalcular a ciência', async () => {
    const tela = mount(ReportsView)
    await flushPromises()
    const contribuicoes = tela.get('[data-testid="reports-historical-contributions"]')
    expect(contribuicoes.findAll('li').map(item => item.findAll('span').map(span => span.text()))).toEqual([
      ['Regras de segurança', '55,22%'], ['Autoencoder', '30,40%'], ['Isolation Forest', '14,38%'],
    ])
    expect(contribuicoes.text()).toContain('não precisão isolada dos componentes')
    const evidencia = tela.get('[data-testid="reports-historical-validation"]')
    for (const texto of ['355 janelas históricas', '99,48%', '91,43%', '95,29%', '0,69%', 'TN 144', 'FP 1', 'FN 18', 'TP 192']) {
      expect(evidencia.text()).toContain(texto)
    }
    expect(evidencia.get('h2').text()).toBe('RESULTADOS DA AVALIAÇÃO HISTÓRICA')
    expect(evidencia.text()).not.toContain('Validação histórica reproduzida')
    expect(evidencia.text()).toContain('sem holdout independente')
    expect(evidencia.text()).toContain('Não é tempo real')
    expect(api.getHistoryWindows).toHaveBeenCalledExactlyOnceWith(20, 0)
    expect(api.getHistoryAlerts).toHaveBeenCalledExactlyOnceWith(20, 0)
    expect(tela.text()).toContain('não representa o conjunto histórico de 355 janelas')
  })

  it('desabilita exportação durante carregamento', async () => {
    const resposta = promessaControlada<HistorySummary>()
    vi.mocked(api.getHistorySummary).mockReturnValue(resposta.promessa)
    const tela = mount(ReportsView)
    expect(tela.find('[role="status"]').exists()).toBe(true)
    expect(tela.get('[data-testid="reports-export-json"]').attributes('disabled')).toBeDefined()
    resposta.resolver(resumoHistorico())
    await flushPromises()
    expect(tela.get('[data-testid="reports-export-json"]').attributes('disabled')).toBeUndefined()
  })

  it('mantém evidência histórica identificada quando consulta operacional falha', async () => {
    vi.mocked(api.getHistorySummary).mockRejectedValue(new Error('indisponível'))
    const tela = mount(ReportsView)
    await flushPromises()
    expect(tela.get('[role="alert"]').text()).toContain('Dados operacionais indisponíveis')
    expect(tela.get('[data-testid="reports-historical-validation"]').text()).toContain('355 janelas históricas')
    expect(tela.get('[data-testid="reports-historical-contributions"]').text()).toContain('Autoencoder')
    expect(tela.find('details').exists()).toBe(false)
  })

  it('preserva o conteúdo histórico e as exportações existentes', async () => {
    const json = vi.spyOn(exportadores, 'exportJson').mockReturnValue(true)
    const pdf = vi.spyOn(exportadores, 'exportPdfDocument').mockReturnValue(true)
    const tela = mount(ReportsView)
    await flushPromises()
    await tela.get('[data-testid="reports-export-json"]').trigger('click')
    expect(json.mock.calls[0][1]).toMatchObject({ evidencia_historica: validacaoHistorica, operacional: { analises_importadas: 2, resultados_importados: 33 } })
    await tela.get('[data-testid="reports-export-pdf"]').trigger('click')
    const html = pdf.mock.calls[0][1]
    for (const texto of ['355 janelas históricas', '99,48%', '91,43%', '95,29%', '0,69%', '144', '192', 'Limitações']) expect(html).toContain(texto)
  })
})
