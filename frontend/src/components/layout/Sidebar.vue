<!-- Menu de navegação com indicação da página atual e itens administrativos condicionados ao papel. -->
<template>
  <aside
    class="fixed inset-x-0 bottom-0 z-40 border-t border-slate-800/90 bg-[#070c15]/95 backdrop-blur-xl lg:inset-y-0 lg:left-0 lg:w-[248px] lg:border-r lg:border-t-0"
    qa-id="app-sidebar"
    data-testid="app-sidebar"
    data-qa-section="sidebar"
  >
    <div class="hidden h-[76px] items-center gap-3 border-b border-slate-800/80 px-5 lg:flex" qa-id="sidebar-brand" data-testid="sidebar-brand">
      <div class="relative grid h-11 w-11 place-items-center overflow-hidden rounded-2xl border border-sky-400/20 bg-sky-400/[0.06] shadow-[0_0_28px_rgba(14,165,233,0.08)]">
        <img
          src="@/assets/sinalyx-logo.png"
          alt="Logo Sinalyx"
          class="h-9 w-9 object-contain"
        />
      </div>
      <div class="min-w-0">
        <p class="text-base font-semibold tracking-tight text-white">Sinalyx</p>
        <p class="mt-0.5 text-[11px] leading-4 text-slate-500">Análise de logs de firewall</p>
      </div>
    </div>

    <nav class="sidebar-mobile-scroll flex gap-1 overflow-x-auto p-2 lg:h-[calc(100svh-76px)] lg:flex-col lg:gap-5 lg:overflow-y-auto lg:p-4" qa-id="sidebar-nav" data-testid="sidebar-nav">
      <div v-for="group in visibleNavigationGroups" :key="group.key" class="contents lg:block lg:shrink-0">
        <p class="hidden px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600 lg:block">
          {{ group.label }}
        </p>
        <div class="flex shrink-0 gap-1 lg:block lg:space-y-1">
          <RouterLink
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="focus-ring group relative flex min-h-11 min-w-[4.5rem] shrink-0 items-center justify-center rounded-xl border border-transparent px-3 text-slate-400 transition duration-150 hover:border-slate-700/60 hover:bg-slate-800/[0.55] hover:text-slate-100 lg:min-w-0 lg:justify-start lg:gap-3"
            :class="isNavigationActive(item) ? 'border-sky-400/20 bg-sky-400/[0.08] text-sky-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]' : ''"
            :title="item.label"
            :qa-id="`nav-${item.qaId}`"
            :data-testid="`nav-${item.qaId}`"
            :aria-label="`Navegar para ${item.label}`"
            :aria-current="isNavigationActive(item) ? 'page' : undefined"
          >
            <span v-if="isNavigationActive(item)" class="absolute left-0 hidden h-7 w-1 rounded-r-full bg-sky-300 shadow-[0_0_14px_rgba(125,211,252,0.38)] lg:block" />
            <span v-if="isNavigationActive(item)" class="absolute inset-x-3 bottom-1 h-0.5 rounded-full bg-sky-300 lg:hidden" />
            <component :is="item.icon" class="h-[18px] w-[18px] shrink-0 transition duration-150 group-hover:text-sky-200" />
            <span class="hidden text-[13px] font-medium lg:inline">{{ item.label }}</span>
          </RouterLink>
        </div>
      </div>

      <p class="mt-auto hidden px-3 pb-1 pt-4 text-xs leading-5 text-slate-400 lg:block">Projeto acadêmico - Sistemas de Informação 2026</p>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import {
  Bell,
  FileText,
  History,
  Info,
  LayoutDashboard,
  Settings,
  ServerCog,
  Users,
} from 'lucide-vue-next'
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const { isAdmin } = useAuth()

const navigationGroups = [
  {
    key: 'analysis',
    label: 'Análise',
    items: [
      { label: 'Dashboard', to: '/', icon: LayoutDashboard, qaId: 'dashboard' },
      { label: 'Alertas', to: '/alerts', icon: Bell, qaId: 'alerts' },
      { label: 'Histórico', to: '/history', icon: History, qaId: 'history' },
      { label: 'Relatórios', to: '/reports', icon: FileText, qaId: 'reports' },
    ],
  },
  {
    key: 'system',
    label: 'Sistema',
    items: [
      { label: 'Configurações', to: '/settings', icon: Settings, qaId: 'settings' },
      { label: 'Status do sistema', to: '/system', icon: ServerCog, qaId: 'system', adminOnly: true },
      { label: 'Administração', to: '/admin/users', icon: Users, qaId: 'admin-users', adminOnly: true },
    ],
  },
  {
    key: 'information',
    label: 'Informações',
    items: [
      { label: 'Sobre', to: '/about', icon: Info, qaId: 'about' },
    ],
  },
] as const

const visibleNavigationGroups = computed(() =>
  navigationGroups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => !('adminOnly' in item) || !item.adminOnly || isAdmin.value),
    }))
    .filter((group) => group.items.length > 0),
)

/** Identifica a página atual para destacar o item correspondente no menu. */
function isNavigationActive(item: (typeof navigationGroups[number]['items'][number])): boolean {
  if (item.to === '/') return route.path === '/' || route.path === '/dashboard'
  if (item.to === '/history' && (route.path.startsWith('/windows/') || route.path.startsWith('/analyses/'))) return true
  if (item.to === '/admin/users') return route.path.startsWith('/admin')
  return route.path === item.to || route.path.startsWith(`${item.to}/`)
}
</script>
