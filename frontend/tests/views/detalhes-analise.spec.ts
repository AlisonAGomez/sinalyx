import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import * as api from '@/services/api'
import type { AnalysisDetails, AnalysisResultsResponse } from '@/types/api'
import AnalysisDetailsView from '@/views/AnalysisDetailsView.vue'
import { analise, paginaAnalise } from '../fixtures/analises'
import { promessaControlada } from '../fixtures/api'

beforeEach(() => {
  vi.spyOn(api, 'getAnalysisDetails').mockImplementation(async id => analise(id))
  vi.spyOn(api, 'getAnalysisResults').mockImplementation(async (id, _limit, offset = 0) => paginaAnalise(id, 1, offset))
})

async function abrirAnalise(id = 'A') {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/analyses/:id', component: AnalysisDetailsView, props: true },
    { path: '/history', component: { template: '<div />' } },
  ] })
  await router.push(`/analyses/${id}`)
  const tela = mount(AnalysisDetailsView, { props: { id }, global: { plugins: [router] } })
  return { tela, router }
}

describe('AUD-06: seleção atual da análise', () => {
  it('carrega resumo e resultados normalmente, sem prefetch', async () => {
    const { tela } = await abrirAnalise()
    await flushPromises()
    expect(tela.text()).toContain('analise-A.log')
    expect(tela.text()).toContain('A-janela-1')
    expect(api.getAnalysisDetails).toHaveBeenCalledExactlyOnceWith('A')
    expect(api.getAnalysisResults).toHaveBeenCalledExactlyOnceWith('A', 50, 0)
  })

  it('não permite que A substitua B quando A responde depois', async () => {
    const detalhesA = promessaControlada<AnalysisDetails>()
    const resultadosA = promessaControlada<AnalysisResultsResponse>()
    vi.mocked(api.getAnalysisDetails).mockImplementation(id => id === 'A' ? detalhesA.promessa : Promise.resolve(analise(id)))
    vi.mocked(api.getAnalysisResults).mockImplementation(id => id === 'A' ? resultadosA.promessa : Promise.resolve(paginaAnalise(id)))
    const { tela } = await abrirAnalise()
    await tela.setProps({ id: 'B' })
    await flushPromises()
    expect(tela.text()).toContain('analise-B.log')
    detalhesA.resolver(analise('A'))
    resultadosA.resolver(paginaAnalise('A'))
    await flushPromises()
    expect(tela.text()).toContain('analise-B.log')
    expect(tela.text()).not.toContain('A-janela-1')
    expect(tela.text()).toContain('B-janela-1')
  })

  it('mantém C em uma troca rápida A → B → C com respostas fora de ordem', async () => {
    const detalhes = ['A', 'B', 'C'].map(() => promessaControlada<AnalysisDetails>())
    const resultados = ['A', 'B', 'C'].map(() => promessaControlada<AnalysisResultsResponse>())
    vi.mocked(api.getAnalysisDetails).mockImplementation(id => detalhes[['A', 'B', 'C'].indexOf(id)].promessa)
    vi.mocked(api.getAnalysisResults).mockImplementation(id => resultados[['A', 'B', 'C'].indexOf(id)].promessa)
    const { tela } = await abrirAnalise()
    await tela.setProps({ id: 'B' })
    await tela.setProps({ id: 'C' })
    for (const index of [2, 0, 1]) {
      detalhes[index].resolver(analise(['A', 'B', 'C'][index]))
      resultados[index].resolver(paginaAnalise(['A', 'B', 'C'][index]))
      await flushPromises()
      expect(tela.text()).toContain('analise-C.log')
      expect(tela.text()).toContain('C-janela-1')
      expect(tela.find('[role="alert"]').exists()).toBe(false)
    }
  })

  it('ignora erros tardios de resumo e resultados de A após sucesso de B', async () => {
    const detalhesA = promessaControlada<AnalysisDetails>()
    const resultadosA = promessaControlada<AnalysisResultsResponse>()
    vi.mocked(api.getAnalysisDetails).mockImplementation(id => id === 'A' ? detalhesA.promessa : Promise.resolve(analise(id)))
    vi.mocked(api.getAnalysisResults).mockImplementation(id => id === 'A' ? resultadosA.promessa : Promise.resolve(paginaAnalise(id)))
    const { tela } = await abrirAnalise()
    await tela.setProps({ id: 'B' })
    await flushPromises()
    detalhesA.rejeitar(new Error('Erro antigo'))
    resultadosA.rejeitar(new Error('Erro antigo'))
    await flushPromises()
    expect(tela.text()).toContain('analise-B.log')
    expect(tela.text()).toContain('B-janela-1')
    expect(tela.find('[role="alert"]').exists()).toBe(false)
  })

  it('finally antigo não encerra loading nem apaga erro da seleção atual', async () => {
    const detalhesA = promessaControlada<AnalysisDetails>()
    const detalhesB = promessaControlada<AnalysisDetails>()
    const resultadosA = promessaControlada<AnalysisResultsResponse>()
    const resultadosB = promessaControlada<AnalysisResultsResponse>()
    vi.mocked(api.getAnalysisDetails).mockImplementation(id => id === 'A' ? detalhesA.promessa : detalhesB.promessa)
    vi.mocked(api.getAnalysisResults).mockImplementation(id => id === 'A' ? resultadosA.promessa : resultadosB.promessa)
    const { tela } = await abrirAnalise()
    await tela.setProps({ id: 'B' })
    detalhesA.resolver(analise('A'))
    resultadosA.resolver(paginaAnalise('A'))
    await flushPromises()
    expect(tela.get('[aria-busy="true"]').text()).toContain('Carregando')
    expect(tela.text()).not.toContain('analise-A.log')
    detalhesB.resolver(analise('B'))
    await flushPromises()
    expect(tela.get('[aria-busy="true"]').text()).toContain('Carregando janelas')
    resultadosB.rejeitar(new Error('Erro atual'))
    await flushPromises()
    expect(tela.get('[role="alert"]').text()).toContain('Não foi possível carregar as janelas')
    expect(tela.find('[aria-busy="true"]').exists()).toBe(false)
  })

  it('mantém erro atual de B quando o resumo antigo A termina com sucesso', async () => {
    const detalhesA = promessaControlada<AnalysisDetails>()
    vi.mocked(api.getAnalysisDetails).mockImplementation(id => id === 'A' ? detalhesA.promessa : Promise.reject(new Error('Erro atual')))
    const { tela } = await abrirAnalise()
    await tela.setProps({ id: 'B' })
    await flushPromises()
    detalhesA.resolver(analise('A'))
    await flushPromises()
    expect(tela.get('[role="alert"]').text()).toContain('Não foi possível carregar os detalhes')
    expect(tela.text()).not.toContain('analise-A.log')
  })

  it('acompanha mudança real de rota durante carregamento', async () => {
    const detalhesA = promessaControlada<AnalysisDetails>()
    vi.mocked(api.getAnalysisDetails).mockImplementation(id => id === 'A' ? detalhesA.promessa : Promise.resolve(analise(id)))
    const router = createRouter({ history: createMemoryHistory(), routes: [
      { path: '/analyses/:id', component: AnalysisDetailsView, props: true },
      { path: '/history', component: { template: '<div />' } },
    ] })
    await router.push('/analyses/A')
    const tela = mount(RouterView, { global: { plugins: [router] } })
    await router.push('/analyses/B')
    await flushPromises()
    detalhesA.resolver(analise('A'))
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/analyses/B')
    expect(tela.text()).toContain('analise-B.log')
    expect(tela.text()).toContain('B-janela-1')
  })

  it('desmonta com chamadas pendentes sem erros tardios ou nova navegação', async () => {
    const detalhes = promessaControlada<AnalysisDetails>()
    const resultados = promessaControlada<AnalysisResultsResponse>()
    vi.mocked(api.getAnalysisDetails).mockReturnValue(detalhes.promessa)
    vi.mocked(api.getAnalysisResults).mockReturnValue(resultados.promessa)
    const { tela, router } = await abrirAnalise()
    const erro = vi.spyOn(console, 'error')
    const navegar = vi.spyOn(router, 'push')
    tela.unmount()
    detalhes.rejeitar(new Error('Erro após desmontagem'))
    resultados.resolver(paginaAnalise('A'))
    await flushPromises()
    expect(erro).not.toHaveBeenCalled()
    expect(navegar).not.toHaveBeenCalled()
    expect(api.getAnalysisResults).toHaveBeenCalledTimes(1)
  })
})

function configurarPaginas(total: number) {
  vi.mocked(api.getAnalysisDetails).mockImplementation(async id => analise(id, total))
  vi.mocked(api.getAnalysisResults).mockImplementation(async (id, _limit, offset = 0) => paginaAnalise(id, total, offset))
}

describe('AUD-07: páginas de 50 janelas', () => {
  it.each([0, 1, 50, 51])('renderiza a primeira página e limites com %i janelas', async total => {
    configurarPaginas(total)
    const { tela } = await abrirAnalise()
    await flushPromises()
    expect(tela.findAll('tbody tr')).toHaveLength(Math.min(total, 50))
    expect(tela.get('[data-testid="analysis-results-prev"]').attributes('disabled')).toBeDefined()
    expect(tela.get('[data-testid="analysis-results-next"]').attributes('disabled') !== undefined).toBe(total <= 50)
    expect(tela.get('nav').text()).toContain(`${total} janelas`)
    if (total === 0) {
      expect(tela.text()).toContain('Nenhum resultado por janela foi retornado')
      expect(tela.get('nav').text()).not.toContain('Página 1')
    }
    expect(api.getAnalysisResults).toHaveBeenCalledTimes(1)
  })

  it('avança e retorna entre três páginas sem duplicação, ordenação local ou prefetch', async () => {
    configurarPaginas(125)
    const { tela } = await abrirAnalise()
    await flushPromises()
    for (const offset of [50, 100]) {
      await tela.get('[data-testid="analysis-results-next"]').trigger('click')
      await flushPromises()
      const ids = tela.findAll('tbody tr').map(row => row.find('td').text())
      const quantidade = offset === 100 ? 25 : 50
      expect(ids).toEqual(Array.from({ length: quantidade }, (_, index) => `A-janela-${offset + index + 1}`))
      expect(new Set(ids).size).toBe(quantidade)
    }
    expect(tela.get('[data-testid="analysis-results-next"]').attributes('disabled')).toBeDefined()
    expect(tela.get('nav').text()).toContain('Página 3 de 3')
    await tela.get('[data-testid="analysis-results-prev"]').trigger('click')
    await flushPromises()
    expect(tela.findAll('tbody tr')[0].text()).toContain('A-janela-51')
    expect(api.getAnalysisResults).toHaveBeenNthCalledWith(4, 'A', 50, 50)
    expect(api.getAnalysisResults).toHaveBeenCalledTimes(4)
    expect(api.getAnalysisDetails).toHaveBeenCalledTimes(1)
  })

  it('alcança a janela 51 e mantém o detalhe individual ao navegar pelas páginas', async () => {
    configurarPaginas(51)
    const original = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'scrollIntoView')
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', { configurable: true, value: vi.fn() })
    try {
      const { tela } = await abrirAnalise()
      await flushPromises()
      await tela.get('[aria-label="Ver detalhes da janela A-janela-1"]').trigger('click')
      expect(tela.get('#detalhe-janela-importada').text()).toContain('A-janela-1')
      await tela.get('[data-testid="analysis-results-next"]').trigger('click')
      await flushPromises()
      expect(tela.find('#detalhe-janela-importada').exists()).toBe(false)
      expect(tela.findAll('tbody tr')).toHaveLength(1)
      await tela.get('[aria-label="Ver detalhes da janela A-janela-51"]').trigger('click')
      expect(tela.get('#detalhe-janela-importada').text()).toContain('A-janela-51')
      await tela.get('#detalhe-janela-importada button').trigger('click')
      expect(tela.find('#detalhe-janela-importada').exists()).toBe(false)
      expect(tela.get('[aria-label="Ver detalhes da janela A-janela-51"]').attributes('aria-expanded')).toBe('false')
    } finally {
      if (original) Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', original)
      else Reflect.deleteProperty(HTMLElement.prototype, 'scrollIntoView')
    }
  })

  it('informa falha de página e permite retry sem misturar janelas', async () => {
    configurarPaginas(75)
    vi.mocked(api.getAnalysisResults).mockResolvedValueOnce(paginaAnalise('A', 75))
      .mockRejectedValueOnce(new Error('Erro de página'))
      .mockResolvedValueOnce(paginaAnalise('A', 75, 50))
    const { tela } = await abrirAnalise()
    await flushPromises()
    await tela.get('[data-testid="analysis-results-next"]').trigger('click')
    await flushPromises()
    expect(tela.text()).toContain('analise-A.log')
    expect(tela.get('[role="alert"]').text()).toContain('Não foi possível carregar as janelas')
    expect(tela.findAll('tbody tr')).toHaveLength(0)
    await tela.get('button').trigger('click')
    await flushPromises()
    expect(tela.findAll('tbody tr')).toHaveLength(25)
    expect(tela.get('nav').text()).toContain('Página 2 de 2')
    expect(api.getAnalysisResults).toHaveBeenLastCalledWith('A', 50, 50)
  })

  it('respostas e erros de páginas antigas não alteram a página atual nem seu loading', async () => {
    configurarPaginas(125)
    const segunda = promessaControlada<AnalysisResultsResponse>()
    const primeira = promessaControlada<AnalysisResultsResponse>()
    vi.mocked(api.getAnalysisResults).mockResolvedValueOnce(paginaAnalise('A', 125))
      .mockReturnValueOnce(segunda.promessa).mockReturnValueOnce(primeira.promessa)
    const { tela } = await abrirAnalise()
    await flushPromises()
    await tela.get('[data-testid="analysis-results-next"]').trigger('click')
    await tela.get('[data-testid="analysis-results-prev"]').trigger('click')
    segunda.rejeitar(new Error('Erro antigo da página 2'))
    await flushPromises()
    expect(tela.get('[aria-busy="true"]').text()).toContain('Carregando janelas')
    expect(tela.find('[role="alert"]').exists()).toBe(false)
    primeira.resolver(paginaAnalise('A', 125))
    await flushPromises()
    expect(tela.get('nav').text()).toContain('Página 1 de 3')
    expect(tela.findAll('tbody tr')[0].text()).toContain('A-janela-1')
  })

  it('não aplica sucesso de página antiga depois da página atual', async () => {
    configurarPaginas(125)
    const segunda = promessaControlada<AnalysisResultsResponse>()
    vi.mocked(api.getAnalysisResults).mockResolvedValueOnce(paginaAnalise('A', 125))
      .mockReturnValueOnce(segunda.promessa).mockResolvedValueOnce(paginaAnalise('A', 125))
    const { tela } = await abrirAnalise()
    await flushPromises()
    await tela.get('[data-testid="analysis-results-next"]').trigger('click')
    await tela.get('[data-testid="analysis-results-prev"]').trigger('click')
    await flushPromises()
    segunda.resolver(paginaAnalise('A', 125, 50))
    await flushPromises()
    expect(tela.get('nav').text()).toContain('Página 1 de 3')
    expect(tela.findAll('tbody tr')[0].text()).toContain('A-janela-1')
    expect(tela.text()).not.toContain('A-janela-51')
  })

  it('permite avanço rápido até página 3 sem aplicar a página 2 atrasada', async () => {
    configurarPaginas(125)
    const segunda = promessaControlada<AnalysisResultsResponse>()
    const terceira = promessaControlada<AnalysisResultsResponse>()
    vi.mocked(api.getAnalysisResults).mockResolvedValueOnce(paginaAnalise('A', 125))
      .mockReturnValueOnce(segunda.promessa).mockReturnValueOnce(terceira.promessa)
    const { tela } = await abrirAnalise()
    await flushPromises()
    await tela.get('[data-testid="analysis-results-next"]').trigger('click')
    await tela.get('[data-testid="analysis-results-next"]').trigger('click')
    terceira.resolver(paginaAnalise('A', 125, 100))
    await flushPromises()
    segunda.resolver(paginaAnalise('A', 125, 50))
    await flushPromises()
    expect(tela.get('nav').text()).toContain('Página 3 de 3')
    expect(tela.findAll('tbody tr')).toHaveLength(25)
    expect(tela.findAll('tbody tr')[0].text()).toContain('A-janela-101')
    expect(api.getAnalysisResults).toHaveBeenLastCalledWith('A', 50, 100)
    expect(tela.find('[aria-busy="true"]').exists()).toBe(false)
  })

  it('trocar a análise reinicia a página e invalida página pendente da análise anterior', async () => {
    configurarPaginas(75)
    const segundaA = promessaControlada<AnalysisResultsResponse>()
    vi.mocked(api.getAnalysisResults).mockResolvedValueOnce(paginaAnalise('A', 75))
      .mockReturnValueOnce(segundaA.promessa).mockResolvedValueOnce(paginaAnalise('B', 1))
    const { tela } = await abrirAnalise()
    await flushPromises()
    await tela.get('[data-testid="analysis-results-next"]').trigger('click')
    await tela.setProps({ id: 'B' })
    await flushPromises()
    segundaA.resolver(paginaAnalise('A', 75, 50))
    await flushPromises()
    expect(tela.text()).toContain('B-janela-1')
    expect(tela.text()).not.toContain('A-janela-51')
    expect(tela.get('nav').text()).toContain('Página 1 de 1')
    expect(api.getAnalysisResults).toHaveBeenLastCalledWith('B', 50, 0)
  })

  it('usa o total real da página e suporta envelope legado sem meta/data', async () => {
    configurarPaginas(100)
    const legado = paginaAnalise('A', 50)
    delete legado.meta
    delete legado.data
    vi.mocked(api.getAnalysisResults).mockResolvedValue(legado)
    const { tela } = await abrirAnalise()
    await flushPromises()
    expect(tela.get('nav').text()).toContain('Página 1 de 1')
    expect(tela.get('nav').text()).toContain('50 janelas')
    expect(tela.get('[data-testid="analysis-results-next"]').attributes('disabled')).toBeDefined()
  })

  it.each([0, 50])('ajusta página que deixou de existir quando o total real diminui para %i', async total => {
    configurarPaginas(75)
    vi.mocked(api.getAnalysisResults).mockResolvedValueOnce(paginaAnalise('A', 75))
      .mockResolvedValueOnce(paginaAnalise('A', total, 50)).mockResolvedValueOnce(paginaAnalise('A', total))
    const { tela } = await abrirAnalise()
    await flushPromises()
    await tela.get('[data-testid="analysis-results-next"]').trigger('click')
    await flushPromises()
    expect(tela.get('nav').text()).toContain(`${total} janelas`)
    expect(tela.findAll('tbody tr')).toHaveLength(total)
    if (total > 0) {
      expect(tela.get('nav').text()).toContain('Página 1 de 1')
      expect(api.getAnalysisResults).toHaveBeenLastCalledWith('A', 50, 0)
    } else {
      expect(tela.get('nav').text()).not.toContain('Página')
      expect(api.getAnalysisResults).toHaveBeenCalledTimes(2)
    }
  })
})
