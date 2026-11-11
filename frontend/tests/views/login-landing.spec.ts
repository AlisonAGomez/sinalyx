import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { useAuth } from '@/composables/useAuth'
import * as api from '@/services/api'
import LoginView from '@/views/LoginView.vue'
import { promessaControlada, sessao } from '../fixtures/api'
import type { AuthLoginData } from '@/types/api'

beforeEach(() => useAuth().logout())
afterEach(() => vi.unstubAllEnvs())

async function abrir(flag?: string, redirect = '/history') {
  if (flag !== undefined) vi.stubEnv('VITE_SINALYX_NEW_LOGIN_LANDING', flag)
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/login', component: LoginView },
    { path: '/history', component: { template: '<div>Histórico</div>' } },
    { path: '/', component: { template: '<div>Painel</div>' } },
  ] })
  await router.push({ path: '/login', query: { redirect } })
  await router.isReady()
  const tela = mount(LoginView, { attachTo: document.body, global: { plugins: [router] } })
  await vi.dynamicImportSettled()
  await flushPromises()
  return { tela, router }
}

describe('Entrada pública com opção de login anterior', () => {
  it('apresenta a landing por padrão, com marca oficial e conteúdo público', async () => {
    const consultar = vi.spyOn(api, 'getCurrentUser')
    const analises = vi.spyOn(api, 'getAnalyses')
    const { tela } = await abrir()
    expect(tela.find('[data-testid="login-landing"]').exists()).toBe(true)
    expect(tela.get('h1').text()).toBe('Bem vindo!')
    expect(tela.get('[data-testid="login-brand"] img').attributes('src')).toContain('sinalyx-logo.png')
    for (const texto of ['Dos logs à investigação.', 'O Sinalyx analisa registros de firewall e apresenta indícios de comportamentos suspeitos para apoiar a investigação de segurança.', 'Projeto acadêmico — Sistemas de Informação 2026']) {
      expect(tela.text()).toContain(texto)
    }
    expect(tela.text()).not.toMatch(/355|99,48|SOC ativo|tempo real|proteção ativa/)
    expect(tela.findAll('a').some(a => a.attributes('href') === '/demo')).toBe(false)
    expect(consultar).not.toHaveBeenCalled()
    expect(analises).not.toHaveBeenCalled()
  })

  it('mantém somente os controles de acesso, sem navegação ou seções institucionais duplicadas', async () => {
    const { tela } = await abrir('true')
    expect(tela.findAll('a, nav')).toHaveLength(0)
    expect(tela.findAll('form')).toHaveLength(1)
    expect(tela.findAll('input')).toHaveLength(2)
    expect(tela.findAll('button')).toHaveLength(2)
    expect(tela.findAll('button[type="submit"]')).toHaveLength(1)
    expect(tela.find('[aria-label="Mostrar senha"]').exists()).toBe(true)
    expect(tela.findAll('#sobre, #como-funciona, #recursos, .entrada-destaques, .entrada-conteudo')).toHaveLength(0)
    for (const texto of ['Conheça o projeto', 'Conheça o Sinalyx', 'Da análise dos logs à investigação', 'Recursos para apoiar sua análise', 'Análise de logs', 'Detecção de anomalias', 'Apoio à investigação']) {
      expect(tela.find('[data-testid="login-hero"]').text()).not.toContain(texto)
    }
  })

  it.each(['false', 'valor-invalido'])('usa a apresentação anterior quando a configuração é %s', async (flag) => {
    const { tela } = await abrir(flag)
    expect(tela.find('[data-testid="login-landing"]').exists()).toBe(false)
    expect(tela.find('.login-scene').exists()).toBe(true)
    expect(tela.find('[data-testid="login-email"]').exists()).toBe(true)
    expect(tela.find('[data-testid="login-submit"]').exists()).toBe(true)
  })

  it.each(['true', 'false'])('usa a mesma autenticação e redirecionamento com flag %s', async (flag) => {
    const enviar = vi.spyOn(api, 'loginUser').mockResolvedValue(sessao())
    const { tela, router } = await abrir(flag)
    await tela.get('input[name="email"]').setValue(' pessoa@example.test ')
    await tela.get('input[name="password"]').setValue('senha-sintetica')
    await tela.get('form').trigger('submit')
    await flushPromises()
    expect(enviar).toHaveBeenCalledExactlyOnceWith('pessoa@example.test', 'senha-sintetica')
    expect(router.currentRoute.value.path).toBe('/history')
    expect(useAuth().isAuthenticated.value).toBe(true)
    expect(localStorage.getItem('sinalyx_user')).not.toContain('senha-sintetica')
  })

  it.each(['true', 'false'])('preserva espera, erro e visibilidade de senha com flag %s', async (flag) => {
    const pendente = promessaControlada<AuthLoginData>()
    vi.spyOn(api, 'loginUser').mockReturnValue(pendente.promessa)
    const { tela } = await abrir(flag)
    await tela.get('input[name="email"]').setValue('pessoa@example.test')
    await tela.get('input[name="password"]').setValue('senha-sintetica')
    await tela.get('[aria-label="Mostrar senha"]').trigger('click')
    expect(tela.get('input[name="password"]').attributes('type')).toBe('text')
    await tela.get('form').trigger('submit')
    expect(tela.get('[data-testid="login-submit"]').attributes('disabled')).toBeDefined()
    pendente.rejeitar(new Error('detalhe interno sintético'))
    await flushPromises()
    expect(tela.get('[role="alert"]').text()).toBe('Não foi possível entrar. Verifique seus dados e tente novamente.')
    expect(tela.get('[data-testid="login-submit"]').attributes('disabled')).toBeUndefined()
    expect(tela.text()).not.toContain('detalhe interno')
  })

  it('permanece utilizável sem fotografia e com movimento reduzido', async () => {
    const timer = vi.spyOn(window, 'setInterval')
    const { tela } = await abrir('true')
    expect(window.matchMedia('(prefers-reduced-motion: reduce)').matches).toBe(true)
    expect(tela.get('[data-testid="login-hero"] svg').attributes('aria-hidden')).toBe('true')
    expect(tela.find('[data-testid="login-hero"] img').exists()).toBe(false)
    expect(tela.get('[data-testid="login-submit"]').attributes('disabled')).toBeUndefined()
    expect(timer).not.toHaveBeenCalled()
    expect(tela.findAll('img')).toHaveLength(1)
  })
})
