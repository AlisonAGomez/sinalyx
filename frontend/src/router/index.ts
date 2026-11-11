/** Define as páginas e verifica a sessão antes de permitir a navegação protegida. */

import { createRouter, createWebHistory } from 'vue-router'

import { useAuth } from '@/composables/useAuth'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
    },
    {
      path: '/dashboard',
      redirect: '/',
    },
    {
      path: '/alerts',
      name: 'alerts',
      component: () => import('@/views/AlertsView.vue'),
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('@/views/HistoryView.vue'),
    },
    {
      path: '/reports',
      name: 'reports',
      component: () => import('@/views/ReportsView.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('@/views/AboutView.vue'),
    },
    {
      path: '/analyses/:id',
      name: 'analysis-details',
      component: () => import('@/views/AnalysisDetailsView.vue'),
      props: true,
    },
    {
      path: '/windows/:id',
      name: 'window-details',
      component: () => import('@/views/WindowDetailsView.vue'),
      props: true,
    },
    {
      path: '/system',
      name: 'system',
      component: () => import('@/views/SystemStatusView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('@/views/AdminUsersView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuth()

  if (to.meta.public === true) {
    if (to.name === 'login' && auth.token.value) {
      if (!auth.sessionValidated.value) {
        await auth.loadMe()
      }
      if (auth.isAuthenticated.value) return { path: '/' }
    }
    return true
  }

  if (!auth.token.value) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    }
  }

  if (!auth.sessionValidated.value) {
    await auth.loadMe()
  }

  if (!auth.isAuthenticated.value) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.requiresAdmin === true && !auth.isAdmin.value) {
    return { path: '/' }
  }

  return true
})
