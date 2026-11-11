import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import * as api from '@/services/api'
import ConsultaAmeacas from '@/components/ui/ConsultaAmeacas.vue'
import * as exportadores from '@/utils/exporters'
import type { WindowItem } from '@/types/api'
import WindowDetailsView from '@/views/WindowDetailsView.vue'
import { janela, promessaControlada } from '../fixtures/api'

beforeEach(() => {
  vi.spyOn(api, 'getWindowById').mockImplementation(async id => janela(Number(id)))
})

function criarRouter() {
  return createRouter({ history: createMemoryHistory(), routes: [
    { path: '/windows/:id', component: WindowDetailsView, props: true },
    { path: '/alerts', component: { template: '<div>Fila de alertas de QA</div>' } },
  ] })
}

async function abrirJanela(id = '1') {
  const router = criarRouter()
  await router.push(`/windows/${id}`)
  const tela = mount(WindowDetailsView, { props: { id }, global: { plugins: [router] } })
  return { tela, router }
}

describe('AUD-06: identidade atual nos detalhes da janela', () => {
  it('separa decisão, valores observados e guia, preservando confiança e exportações', async () => {
    const registro = Object.freeze(janela(1, {
      final_label: 'anomaly', attack_type: 'brute_force', risk_level: 'high',
      confidence: 0.8000000000000001, decision_reason: 'heuristic_signature',
      features: Object.freeze({ connections: 12, ports: 3 }),
    }))
    vi.mocked(api.getWindowById).mockResolvedValue(registro)
    const json = vi.spyOn(exportadores, 'exportJson').mockReturnValue(true)
    const pdf = vi.spyOn(exportadores, 'exportPdfDocument').mockReturnValue(true)
    const antes = JSON.stringify(registro)
    const { tela } = await abrirJanela()
    await flushPromises()
    const decisao = tela.get('[aria-label="Decisão do Sinalyx"]')
    expect(decisao.text()).toContain('Atividade SSH suspeita')
    expect(decisao.text()).toContain('Alto')
    expect(tela.get('[data-testid="window-confidence"]').text()).toBe('0,80')
    expect(tela.text()).toContain('Não representa necessariamente a probabilidade de um ataque')
    expect(tela.text()).toContain('Padrão identificado pelas regras de segurança')
    expect(tela.get('[data-testid="observed-connections"]').text()).toBe('12')
    expect(tela.get('[data-testid="threat-category"]').element).toHaveProperty('value', '')
    await tela.get('[data-testid="threat-category"]').setValue('dos')
    expect(decisao.text()).toContain('Atividade SSH suspeita')
    expect(decisao.text()).not.toContain('DoS')
    await tela.get('[data-testid="window-details-export-json"]').trigger('click')
    expect(json.mock.calls[0][1]).toMatchObject({ confidence: registro.confidence, features: registro.features })
    await tela.get('[data-testid="window-details-export-pdf"]').trigger('click')
    expect(pdf.mock.calls[0][1]).toContain(String(registro.confidence))
    expect(JSON.stringify(registro)).toBe(antes)
    expect(api.getWindowById).toHaveBeenCalledTimes(1)
  })

  it.each([
    ['O Autoencoder permaneceu na zona baixa de anomalia e nao houve sinal suficiente para elevar o caso.', 'Não foram encontrados sinais suficientes para indicar atividade suspeita.'],
    [null, 'Padrão identificado pelas regras de segurança'],
    ['detalhe não reconhecido para apresentação', 'Padrão identificado pelas regras de segurança'],
  ])('usa somente motivos conhecidos e seguros: %s', async (motivo, esperado) => {
    vi.mocked(api.getWindowById).mockResolvedValue(janela(1, { decision_source: 'heuristic', decision_reason: motivo }))
    const { tela } = await abrirJanela()
    await flushPromises()
    expect(tela.text()).toContain(esperado)
    expect(tela.text()).not.toMatch(/senha incorreta|autenticação malsucedida|ataque confirmado|bloqueio realizado/i)
    expect(tela.text()).not.toContain('detalhe não reconhecido para apresentação')
  })

  it('diferencia zero observado, confiança ausente e características não informadas', async () => {
    vi.mocked(api.getWindowById).mockResolvedValue(janela(1, { confidence: null, features: { connections: 0, bytes: null } }))
    const { tela } = await abrirJanela()
    await flushPromises()
    expect(tela.get('[data-testid="window-confidence"]').text()).toBe('Não informado')
    expect(tela.get('[data-testid="observed-connections"]').text()).toBe('0')
    expect(tela.get('[data-testid="observed-bytes"]').text()).toBe('Não informado')
    expect(tela.text()).not.toContain('NaN')
    expect(tela.text()).not.toContain('undefined')
  })

  it('carrega uma janela normalmente e mantém os seletores existentes', async () => {
    const resposta = promessaControlada<WindowItem | null>()
    vi.mocked(api.getWindowById).mockReturnValue(resposta.promessa)
    const { tela } = await abrirJanela()
    expect(tela.get('[aria-busy="true"]').text()).toContain('Carregando')
    expect(tela.get('[data-testid="window-details-export-json"]').attributes('disabled')).toBeDefined()
    resposta.resolver(janela(1))
    await flushPromises()
    expect(api.getWindowById).toHaveBeenCalledExactlyOnceWith('1')
    expect(tela.getComponent(ConsultaAmeacas).props('janela')).toMatchObject({ id: 1, window_id: 'janela-qa-1' })
    expect(tela.find('pre').exists()).toBe(false)
    expect(tela.text()).toContain('As características oficiais não estão disponíveis neste registro.')
    expect(tela.text()).not.toContain('Ver registro técnico seguro')
    for (const id of ['page-window-details', 'window-details-export-pdf', 'window-details-export-json', 'window-details-back', 'window-details-executive-summary']) {
      expect(tela.get(`[data-testid="${id}"]`).attributes('qa-id')).toBe(id)
    }
    expect(tela.find('[aria-busy="true"]').exists()).toBe(false)
    expect(tela.find('[role="alert"]').exists()).toBe(false)
  })

  it('mantém B quando a resposta antiga de A chega depois', async () => {
    const respostaA = promessaControlada<WindowItem | null>()
    vi.mocked(api.getWindowById).mockImplementation(id => id === '1' ? respostaA.promessa : Promise.resolve(janela(Number(id))))
    const { tela } = await abrirJanela()
    await tela.setProps({ id: '2' })
    await flushPromises()
    expect(tela.getComponent(ConsultaAmeacas).props('janela').id).toBe(2)
    respostaA.resolver(janela(1))
    await flushPromises()
    expect(tela.getComponent(ConsultaAmeacas).props('janela').id).toBe(2)
    expect(tela.getComponent(ConsultaAmeacas).props('janela').window_id).toBe('janela-qa-2')
  })

  it('preserva C em mudanças rápidas A → B → C com retornos fora de ordem', async () => {
    const respostas = [1, 2, 3].map(() => promessaControlada<WindowItem | null>())
    vi.mocked(api.getWindowById).mockImplementation(id => respostas[Number(id) - 1].promessa)
    const { tela } = await abrirJanela()
    await tela.setProps({ id: '2' })
    await tela.setProps({ id: '3' })
    for (const id of [3, 1, 2]) {
      respostas[id - 1].resolver(janela(id))
      await flushPromises()
      expect(tela.getComponent(ConsultaAmeacas).props('janela')).toMatchObject({ id: 3, window_id: 'janela-qa-3' })
      expect(tela.find('[role="alert"]').exists()).toBe(false)
    }
  })

  it.each(['erro', 'ausente'])('ignora retorno tardio de A após sucesso de B: %s', async tipo => {
    const respostaA = promessaControlada<WindowItem | null>()
    vi.mocked(api.getWindowById).mockImplementation(id => id === '1' ? respostaA.promessa : Promise.resolve(janela(Number(id))))
    const { tela } = await abrirJanela()
    await tela.setProps({ id: '2' })
    await flushPromises()
    if (tipo === 'erro') respostaA.rejeitar(new Error('Erro antigo'))
    else respostaA.resolver(null)
    await flushPromises()
    expect(tela.getComponent(ConsultaAmeacas).props('janela').id).toBe(2)
    expect(tela.find('[role="alert"]').exists()).toBe(false)
  })

  it.each(['sucesso', 'erro'])('finally antigo não encerra loading de B: %s de A', async tipo => {
    const respostaA = promessaControlada<WindowItem | null>()
    const respostaB = promessaControlada<WindowItem | null>()
    vi.mocked(api.getWindowById).mockImplementation(id => id === '1' ? respostaA.promessa : respostaB.promessa)
    const { tela } = await abrirJanela()
    await tela.setProps({ id: '2' })
    if (tipo === 'sucesso') respostaA.resolver(janela(1))
    else respostaA.rejeitar(new Error('Erro antigo'))
    await flushPromises()
    expect(tela.get('[aria-busy="true"]').text()).toContain('Carregando')
    expect(tela.findComponent(ConsultaAmeacas).exists()).toBe(false)
    expect(tela.find('[role="alert"]').exists()).toBe(false)
    expect(tela.get('[data-testid="window-details-export-json"]').attributes('disabled')).toBeDefined()
    respostaB.resolver(janela(2))
    await flushPromises()
    expect(tela.getComponent(ConsultaAmeacas).props('janela').id).toBe(2)
    expect(tela.find('[aria-busy="true"]').exists()).toBe(false)
  })

  it('sucesso antigo não substitui erro da janela atual', async () => {
    const respostaA = promessaControlada<WindowItem | null>()
    vi.mocked(api.getWindowById).mockImplementation(id => id === '1' ? respostaA.promessa : Promise.reject(new Error('Erro atual')))
    const { tela } = await abrirJanela()
    await tela.setProps({ id: '2' })
    await flushPromises()
    respostaA.resolver(janela(1))
    await flushPromises()
    expect(tela.get('[role="alert"]').text()).toContain('Não foi possível carregar os detalhes desta janela.')
    expect(tela.findComponent(ConsultaAmeacas).exists()).toBe(false)
    expect(tela.get('[data-testid="window-details-export-pdf"]').attributes('disabled')).toBeDefined()
  })

  it('mantém o estado de janela não encontrada para a seleção atual', async () => {
    vi.mocked(api.getWindowById).mockResolvedValue(null)
    const { tela } = await abrirJanela()
    await flushPromises()
    expect(tela.get('[role="alert"]').text()).toContain('A janela solicitada não foi encontrada.')
    expect(tela.findComponent(ConsultaAmeacas).exists()).toBe(false)
    expect(tela.find('[aria-busy="true"]').exists()).toBe(false)
  })

  it('acompanha o ID da rota sem reaplicar uma resposta antiga', async () => {
    const respostaA = promessaControlada<WindowItem | null>()
    vi.mocked(api.getWindowById).mockImplementation(id => id === '1' ? respostaA.promessa : Promise.resolve(janela(Number(id))))
    const router = criarRouter()
    await router.push('/windows/1')
    const tela = mount(RouterView, { global: { plugins: [router] } })
    await router.push('/windows/2')
    await flushPromises()
    respostaA.resolver(janela(1))
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/windows/2')
    expect(tela.getComponent(ConsultaAmeacas).props('janela').id).toBe(2)
  })

  it('Voltar navega para Alertas e a resposta pendente não provoca retorno', async () => {
    const resposta = promessaControlada<WindowItem | null>()
    vi.mocked(api.getWindowById).mockReturnValue(resposta.promessa)
    const router = criarRouter()
    await router.push('/windows/1')
    const tela = mount(RouterView, { global: { plugins: [router] } })
    const navegar = vi.spyOn(router, 'push')
    await tela.get('[data-testid="window-details-back"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/alerts')
    resposta.resolver(janela(1))
    await flushPromises()
    expect(tela.text()).toBe('Fila de alertas de QA')
    expect(router.currentRoute.value.path).toBe('/alerts')
    expect(navegar).toHaveBeenCalledTimes(1)
    expect(tela.find('[data-testid="page-window-details"]').exists()).toBe(false)
  })

  it('encerra com uma requisição pendente sem erro ou navegação tardia', async () => {
    const resposta = promessaControlada<WindowItem | null>()
    vi.mocked(api.getWindowById).mockReturnValue(resposta.promessa)
    const { tela, router } = await abrirJanela()
    const erro = vi.spyOn(console, 'error')
    const navegar = vi.spyOn(router, 'push')
    tela.unmount()
    resposta.rejeitar(new Error('Erro após desmontagem'))
    await flushPromises()
    expect(erro).not.toHaveBeenCalled()
    expect(navegar).not.toHaveBeenCalled()
    expect(api.getWindowById).toHaveBeenCalledTimes(1)
  })

  it('exporta somente a identidade atual depois de uma resposta antiga', async () => {
    const respostaA = promessaControlada<WindowItem | null>()
    vi.mocked(api.getWindowById).mockImplementation(id => id === '1' ? respostaA.promessa : Promise.resolve(janela(Number(id))))
    const json = vi.spyOn(exportadores, 'exportJson').mockReturnValue(true)
    const pdf = vi.spyOn(exportadores, 'exportPdfDocument').mockReturnValue(true)
    const { tela } = await abrirJanela()
    await tela.setProps({ id: '2' })
    await flushPromises()
    respostaA.resolver(janela(1))
    await flushPromises()
    await tela.get('[data-testid="window-details-export-json"]').trigger('click')
    expect(json).toHaveBeenCalledTimes(1)
    expect(json.mock.calls[0][0]).toMatch(/^sinalyx_ocorrencia_janela_2_/)
    expect(json.mock.calls[0][1]).toMatchObject({ id: 2, window_id: 'janela-qa-2' })
    await tela.get('[data-testid="window-details-export-pdf"]').trigger('click')
    expect(pdf).toHaveBeenCalledTimes(1)
    expect(pdf.mock.calls[0][0]).toContain('Janela 2')
    expect(pdf.mock.calls[0][1]).toContain('janela-qa-2')
    expect(pdf.mock.calls[0][1]).not.toContain('janela-qa-1')
  })
})
