import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import Topbar from '@/components/layout/Topbar.vue'
import { useAuth } from '@/composables/useAuth'
import { useGlobalSearch } from '@/composables/useGlobalSearch'
import * as api from '@/services/api'
import { sessao } from '../fixtures/api'

beforeEach(() => { useAuth().logout(); useGlobalSearch().globalSearch.value = '' })

it('remove o avatar, preserva nome/papel, busca e logout', async () => {
  vi.spyOn(api, 'loginUser').mockResolvedValue({ ...sessao('admin'), user: { ...sessao('admin').user, name: 'Administrador Sinalyx' } })
  await useAuth().login('pessoa@example.test', 'senha-sintetica')
  const router = createRouter({ history: createMemoryHistory(), routes: ['/', '/login'].map(path => ({ path, component: { template: '<div />' } })) })
  await router.push('/')
  const tela = mount(Topbar, { global: { plugins: [router] } })
  expect(tela.get('[data-testid="topbar-user-name"]').text()).toBe('Administrador Sinalyx')
  const menu = tela.get('[data-testid="topbar-user-menu"]')
  expect(menu.text()).toContain('Administrador')
  expect(menu.findAll('*').some(item => item.text() === 'AS')).toBe(false)
  expect(tela.get('[data-testid="global-search"]').classes()).toContain('w-full')
  await tela.get('[data-testid="global-search"]').setValue('janela de QA')
  expect(useGlobalSearch().trimmedSearch.value).toBe('janela de QA')
  await tela.get('[data-testid="logout-button"]').trigger('click')
  await flushPromises()
  expect(router.currentRoute.value.path).toBe('/login')
  expect(useAuth().isAuthenticated.value).toBe(false)
  expect(localStorage.getItem('sinalyx_access_token')).toBeNull()
})
