import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import RecentWindowsChart from '@/components/charts/RecentWindowsChart.vue'

describe('Gráfico de janelas recentes', () => {
  it('mantém barras verticais, categorias de cor, alturas e identificação recebida', () => {
    const casos = [
      { isAnomaly: false, riskLevel: 'critical', altura: '26%', cor: 'bg-emerald-400' },
      { isAnomaly: true, riskLevel: 'critical', altura: '96%', cor: 'bg-fuchsia-400' },
      { isAnomaly: true, riskLevel: 'high', altura: '78%', cor: 'bg-red-400' },
      { isAnomaly: true, riskLevel: 'medium', altura: '58%', cor: 'bg-amber-400' },
      { isAnomaly: true, riskLevel: 'low', altura: '38%', cor: 'bg-cyan-400' },
      { isAnomaly: true, riskLevel: 'unknown', altura: '48%', cor: 'bg-cyan-400' },
    ]
    const tela = mount(RecentWindowsChart, { props: {
      title: 'Janelas consultadas',
      items: casos.map((item, index) => ({ ...item, id: index, label: `J-${index}`, tooltip: `Janela de QA ${index}` })),
    } })
    expect(tela.get('h2').text()).toBe('Janelas consultadas')
    expect(tela.find('.h-40.items-end').exists()).toBe(true)
    const barras = tela.findAll('[title]')
    expect(barras).toHaveLength(casos.length)
    casos.forEach((caso, index) => {
      const barra = barras[index]
      expect((barra.element as HTMLElement).style.height).toBe(caso.altura)
      expect((barra.element as HTMLElement).style.width).toBe('')
      expect(barra.classes()).toContain(caso.cor)
      expect(barra.attributes('title')).toBe(`Janela de QA ${index}`)
      expect(tela.text()).toContain(`J-${index}`)
    })
    expect(tela.text()).toContain('Os resultados refletem as janelas mais recentes disponíveis no histórico. Recarregue a página para consultar atualizações.')
  })

  it('não apresenta barras fictícias quando a lista está vazia', () => {
    const tela = mount(RecentWindowsChart, { props: { title: 'Janelas', items: [] } })
    expect(tela.text()).toContain('Nenhum resultado recente para exibir.')
    expect(tela.findAll('[title]')).toHaveLength(0)
  })
})
