import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { useAuth } from '@/composables/useAuth'
import * as api from '@/services/api'
import type { AuthLoginData } from '@/types/api'
import LoginView from '@/views/LoginView.vue'
import { promessaControlada, sessao } from '../fixtures/api'

beforeEach(() => useAuth().logout())

async function abrirLogin(redirect = '/') {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/login', component: LoginView },
    { path: '/', component: { template: '<div>Dashboard</div>' } },
    { path: '/history', component: { template: '<div>Histórico</div>' } },
  ] })
  await router.push({ path: '/login', query: { redirect } })
  await router.isReady()
  const tela = mount(LoginView, { attachTo: document.body, global: { plugins: [router] } })
  return { tela, router }
}

describe('Login com autenticação frontend real e respostas simuladas', () => {
  it('apresenta formulário acessível, vazio e com senha inicialmente oculta', async () => {
    const { tela } = await abrirLogin()
    expect(tela.get('[data-testid="page-login"]').attributes('qa-id')).toBe('page-login')
    expect(tela.get('[data-testid="login-email"]').attributes('autocomplete')).toBe('username')
    expect(tela.get('[data-testid="login-password"]').attributes('type')).toBe('password')
    expect(tela.find('[role="alert"]').exists()).toBe(false)
    await tela.get('[aria-label="Mostrar senha"]').trigger('click')
    expect(tela.get('[data-testid="login-password"]').attributes('type')).toBe('text')
    await tela.get('[aria-label="Ocultar senha"]').trigger('click')
    expect(tela.get('[data-testid="login-password"]').attributes('type')).toBe('password')
  })

  it.each(['', 'email-invalido'])('não envia formulário com email inválido: %s', async (email) => {
    const enviar = vi.spyOn(api, 'loginUser')
    const { tela } = await abrirLogin()
    await tela.get('input[name="email"]').setValue(email)
    await tela.get('input[name="password"]').setValue('senha-sintetica')
    expect((tela.get('form').element as HTMLFormElement).checkValidity()).toBe(false)
    ;(tela.get('[data-testid="login-submit"]').element as HTMLButtonElement).click()
    await flushPromises()
    expect(enviar).not.toHaveBeenCalled()
  })

  it('exige senha antes de enviar o formulário', async () => {
    const enviar = vi.spyOn(api, 'loginUser')
    const { tela } = await abrirLogin()
    await tela.get('input[name="email"]').setValue('pessoa@example.test')
    expect((tela.get('input[name="password"]').element as HTMLInputElement).validity.valueMissing).toBe(true)
    ;(tela.get('[data-testid="login-submit"]').element as HTMLButtonElement).click()
    await flushPromises()
    expect(enviar).not.toHaveBeenCalled()
  })

  it('mantém carregamento durante a resposta e autentica sem revelar a senha', async () => {
    const resposta = promessaControlada<AuthLoginData>()
    const enviar = vi.spyOn(api, 'loginUser').mockReturnValue(resposta.promessa)
    const { tela, router } = await abrirLogin('/history')
    await tela.get('input[name="email"]').setValue(' pessoa@example.test ')
    await tela.get('input[name="password"]').setValue('senha-sintetica')
    await tela.get('form').trigger('submit')
    expect(enviar).toHaveBeenCalledExactlyOnceWith('pessoa@example.test', 'senha-sintetica')
    expect(tela.get('[data-testid="login-submit"]').attributes('disabled')).toBeDefined()
    expect(tela.text()).toContain('Entrando...')
    resposta.resolver(sessao())
    await flushPromises()
    expect(router.currentRoute.value.fullPath).toBe('/history')
    expect(useAuth().isAuthenticated.value).toBe(true)
    expect(window.localStorage.getItem('sinalyx_access_token')).toBe(sessao().access_token)
    expect(window.localStorage.getItem('sinalyx_user')).not.toContain('senha-sintetica')
    expect(tela.get('[data-testid="login-submit"]').attributes('disabled')).toBeUndefined()
  })

  it('apresenta erro seguro e libera nova tentativa após rejeição', async () => {
    vi.spyOn(api, 'loginUser').mockRejectedValue(new Error('detalhe interno sintético'))
    const { tela, router } = await abrirLogin()
    await tela.get('input[name="email"]').setValue('pessoa@example.test')
    await tela.get('input[name="password"]').setValue('senha-sintetica')
    await tela.get('form').trigger('submit')
    await flushPromises()
    expect(tela.get('[role="alert"]').text()).toBe('Não foi possível entrar. Verifique seus dados e tente novamente.')
    expect(tela.text()).not.toContain('detalhe interno')
    expect(router.currentRoute.value.path).toBe('/login')
    expect(useAuth().isAuthenticated.value).toBe(false)
    expect(tela.get('[data-testid="login-submit"]').attributes('disabled')).toBeUndefined()
  })

  it.each(['https://example.invalid/', '//example.invalid/'])('não redireciona login para destino externo: %s', async (destino) => {
    vi.spyOn(api, 'loginUser').mockResolvedValue(sessao())
    const { tela, router } = await abrirLogin(destino)
    await tela.get('input[name="email"]').setValue('pessoa@example.test')
    await tela.get('input[name="password"]').setValue('senha-sintetica')
    await tela.get('form').trigger('submit')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/')
  })
})
