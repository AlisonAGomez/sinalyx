import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import Sidebar from '@/components/layout/Sidebar.vue'
import { useAuth } from '@/composables/useAuth'
import * as api from '@/services/api'
import { sessao } from '../fixtures/api'

beforeEach(() => useAuth().logout())

async function abrirMenu(role: 'admin' | 'user') {
  vi.spyOn(api, 'loginUser').mockResolvedValue(sessao(role))
  await useAuth().login('pessoa@example.test', 'senha-sintetica')
  const caminhos = ['/', '/alerts', '/history', '/reports', '/settings', '/system', '/admin/users', '/about']
  const detalhes = ['/windows/1', '/analyses/1', '/admin/users/1']
  const router = createRouter({ history: createMemoryHistory(), routes: [...caminhos, ...detalhes].map(path => ({
    path, component: { template: '<div />' },
  })) })
  await router.push('/')
  const tela = mount(Sidebar, { global: { plugins: [router] } })
  return { tela, router, caminhos }
}

describe('Navegação operacional', () => {
  it('oferece todos os destinos administrativos, navega e sinaliza página ativa', async () => {
    const { tela, router, caminhos } = await abrirMenu('admin')
    expect(tela.findAll('a').map(link => link.attributes('href'))).toEqual(caminhos)
    for (const link of tela.findAll('a')) {
      expect(link.attributes('qa-id')).toBe(link.attributes('data-testid'))
      await link.trigger('click')
      await flushPromises()
      expect(router.currentRoute.value.path).toBe(link.attributes('href'))
      expect(link.attributes('aria-current')).toBe('page')
    }
    expect(tela.text()).not.toContain('Apresentação')
    expect(tela.find('[data-testid="nav-demo"]').exists()).toBe(false)
    expect(tela.find('a[href="/demo"]').exists()).toBe(false)
    expect(tela.text()).not.toContain('Escopo desta versão')
    expect(tela.text()).toContain('Projeto acadêmico - Sistemas de Informação 2026')
  })

  it('mantém destinos comuns e oculta controles administrativos de usuário comum', async () => {
    const { tela } = await abrirMenu('user')
    expect(tela.findAll('a').map(link => link.attributes('href'))).toEqual([
      '/', '/alerts', '/history', '/reports', '/settings', '/about',
    ])
    expect(tela.find('[data-testid="nav-system"]').exists()).toBe(false)
    expect(tela.find('[data-testid="nav-admin-users"]').exists()).toBe(false)
    useAuth().logout()
    await flushPromises()
    expect(tela.find('[data-testid="nav-admin-users"]').exists()).toBe(false)
  })

  it('mantém o contexto ativo na investigação de janelas, análises e usuários', async () => {
    const { tela, router } = await abrirMenu('admin')
    for (const [caminho, seletor] of [
      ['/windows/1', 'nav-history'],
      ['/analyses/1', 'nav-history'],
      ['/admin/users/1', 'nav-admin-users'],
    ] as const) {
      await router.push(caminho)
      await flushPromises()
      const ativos = tela.findAll('a[aria-current="page"]')
      expect(ativos).toHaveLength(1)
      expect(ativos[0]!.attributes('data-testid')).toBe(seletor)
    }
    for (const link of tela.findAll('a')) {
      expect(link.attributes('aria-label')).toMatch(/^Navegar para /)
      expect(link.attributes('tabindex')).not.toBe('-1')
    }
  })
})
