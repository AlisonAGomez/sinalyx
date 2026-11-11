import { mount } from '@vue/test-utils'
import { SearchX, Shield } from 'lucide-vue-next'
import { describe, expect, it } from 'vitest'

import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'

describe('Estados compartilhados', () => {
  it('renderiza o ícone padrão real no estado vazio', () => {
    const tela = mount(EmptyState)
    expect(tela.text()).toBe('Nenhum resultado encontrado')
    expect(tela.findComponent(SearchX).exists()).toBe(true)
    expect(tela.find('svg').exists()).toBe(true)
  })

  it('respeita mensagem, título e ícone personalizados', () => {
    const tela = mount(EmptyState, { props: { title: 'Sem análises', message: 'Importe um arquivo.', icon: Shield } })
    expect(tela.text()).toContain('Sem análises')
    expect(tela.text()).toContain('Importe um arquivo.')
    expect(tela.findComponent(Shield).exists()).toBe(true)
  })

  it('anuncia o carregamento sem apresentar resultados fictícios', () => {
    const tela = mount(LoadingState, { props: { label: 'Consultando histórico' } })
    expect(tela.get('[role="status"]').attributes('aria-busy')).toBe('true')
    expect(tela.text()).toBe('Consultando histórico')
  })

  it('anuncia o erro recebido e mantém o estado vazio separado', () => {
    const tela = mount(ErrorState, { props: { message: 'Histórico indisponível' } })
    expect(tela.get('[role="alert"]').text()).toContain('Histórico indisponível')
    expect(tela.findComponent(EmptyState).exists()).toBe(false)
  })
})
