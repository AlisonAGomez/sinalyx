import { AxiosError } from 'axios'
import type { AxiosAdapter } from 'axios'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { api, getCurrentUser, loginUser } from '@/services/api'
import { sessao, usuario } from '../fixtures/api'

const adaptadorOriginal = api.defaults.adapter
afterEach(() => { api.defaults.adapter = adaptadorOriginal })

describe('Contrato HTTP de autenticação com transporte em memória', () => {
  it('envia o contrato de login e não anexa um token antigo', async () => {
    window.localStorage.setItem('sinalyx_access_token', 'token-antigo-sintetico')
    const transporte = vi.fn<AxiosAdapter>(async config => ({
      data: { status: 'success', data: sessao() }, status: 200, statusText: 'OK', headers: {}, config,
    }))
    api.defaults.adapter = transporte
    expect(await loginUser('pessoa@example.test', 'senha-sintetica')).toEqual(sessao())
    const config = transporte.mock.calls[0][0]
    expect(config.url).toBe('/auth/login')
    expect(config.method).toBe('post')
    expect(JSON.parse(config.data)).toEqual({ email: 'pessoa@example.test', password: 'senha-sintetica' })
    expect(config.headers.get('Authorization')).toBeUndefined()
  })

  it('consulta a sessão com Bearer e lê o envelope real de /auth/me', async () => {
    window.localStorage.setItem('sinalyx_access_token', sessao().access_token)
    const transporte = vi.fn<AxiosAdapter>(async config => ({
      data: { status: 'success', data: { user: usuario() } }, status: 200, statusText: 'OK', headers: {}, config,
    }))
    api.defaults.adapter = transporte
    expect(await getCurrentUser()).toEqual(usuario())
    const config = transporte.mock.calls[0][0]
    expect(config.url).toBe('/auth/me')
    expect(config.headers.get('Authorization')).toBe(`Bearer ${sessao().access_token}`)
  })

  it('remove dados persistidos ao receber 401 em consulta protegida', async () => {
    window.history.replaceState({}, '', '/login')
    window.localStorage.setItem('sinalyx_access_token', sessao().access_token)
    window.localStorage.setItem('sinalyx_user', JSON.stringify(usuario()))
    api.defaults.adapter = async config => {
      throw new AxiosError('Sessão expirada simulada', 'ERR_BAD_REQUEST', config, undefined, {
        data: {}, status: 401, statusText: 'Unauthorized', headers: {}, config,
      })
    }
    await expect(getCurrentUser()).rejects.toMatchObject({ response: { status: 401 } })
    expect(window.localStorage.getItem('sinalyx_access_token')).toBeNull()
    expect(window.localStorage.getItem('sinalyx_user')).toBeNull()
  })
})
