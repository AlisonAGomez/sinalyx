import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Router } from 'vue-router'

import { usuario } from '../fixtures/api'

let router: Router | undefined
beforeEach(() => vi.resetModules())
afterEach(() => router?.options.history.destroy())

async function preparar(role?: 'admin' | 'user', expirada = false) {
  if (role) {
    window.localStorage.setItem('sinalyx_access_token', 'token-sintetico-sem-validade')
    window.localStorage.setItem('sinalyx_user', JSON.stringify(usuario(role)))
  }
  const api = await import('@/services/api')
  const consultar = vi.spyOn(api, 'getCurrentUser')
  if (expirada) consultar.mockRejectedValue(new Error('Sessão expirada simulada'))
  else consultar.mockResolvedValue(usuario(role))
  router = (await import('@/router')).router
  return { router, consultar }
}

describe('Router e guards reais', () => {
  it('preserva a matriz de rotas e não registra /demo nem catch-all fictício', async () => {
    const { router } = await preparar()
    expect(router.getRoutes().map(item => item.path).sort()).toEqual([
      '/', '/login', '/dashboard', '/alerts', '/history', '/reports', '/analyses/:id',
      '/windows/:id', '/system', '/admin/users', '/settings', '/about',
    ].sort())
    // O produto não possui página 404; registra-se aqui apenas a ausência de match.
    const aviso = vi.spyOn(console, 'warn').mockImplementation(() => {})
    expect(router.resolve('/inexistente').matched).toHaveLength(0)
    expect(router.resolve('/demo').matched).toHaveLength(0)
    expect(aviso.mock.calls.flat().join(' ')).toContain('No match found')
  })

  it('abre login público sem consultar sessão ausente', async () => {
    const { router, consultar } = await preparar()
    await router.push('/login')
    expect(router.currentRoute.value.path).toBe('/login')
    expect(consultar).not.toHaveBeenCalled()
  })

  it('redireciona rota protegida e preserva o destino completo', async () => {
    const { router } = await preparar()
    await router.push('/history?search=qa')
    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.redirect).toBe('/history?search=qa')
  })

  it('valida a sessão antes de liberar rota e não repete a consulta em cada navegação', async () => {
    const { router, consultar } = await preparar('user')
    await router.push('/dashboard')
    expect(router.currentRoute.value.path).toBe('/')
    await router.push('/reports')
    expect(router.currentRoute.value.path).toBe('/reports')
    expect(consultar).toHaveBeenCalledTimes(1)
  })

  it.each(['/system', '/admin/users'])('permite admin revalidado em %s', async (destino) => {
    const { router } = await preparar('admin')
    await router.push(destino)
    expect(router.currentRoute.value.path).toBe(destino)
  })

  it.each(['/system', '/admin/users'])('nega usuário comum em %s', async (destino) => {
    const { router } = await preparar('user')
    await router.push(destino)
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('não confia em papel admin salvo localmente quando /auth/me devolve user', async () => {
    const { router, consultar } = await preparar('admin')
    consultar.mockResolvedValue(usuario('user'))
    await router.push('/admin/users')
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('limpa sessão expirada e retorna ao login', async () => {
    const { router } = await preparar('user', true)
    await router.push('/alerts')
    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.redirect).toBe('/alerts')
    expect(window.localStorage.getItem('sinalyx_access_token')).toBeNull()
    expect(window.localStorage.getItem('sinalyx_user')).toBeNull()
  })

  it('redireciona login para Dashboard quando a sessão já é válida', async () => {
    const { router } = await preparar('user')
    await router.push('/login')
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('volta a exigir login após logout', async () => {
    const { router } = await preparar('user')
    await router.push('/history')
    const { useAuth } = await import('@/composables/useAuth')
    useAuth().logout()
    await router.push('/reports')
    expect(router.currentRoute.value.path).toBe('/login')
    expect(window.localStorage.getItem('sinalyx_user')).toBeNull()
  })
})
