<!-- Cabeçalho com busca, identificação da conta e encerramento de sessão. -->
<template>
  <header
    class="sticky top-0 z-30 border-b border-slate-800/80 bg-[#070c15]/[0.88] backdrop-blur-xl"
    qa-id="app-topbar"
    data-testid="app-topbar"
    data-qa-section="topbar"
  >
    <div class="flex h-[76px] items-center gap-4 px-4 sm:px-6 lg:px-8 xl:px-10">
      <div class="min-w-0 flex-1">
        <label class="relative block max-w-2xl">
          <Search class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            v-model="globalSearch"
            class="field h-10 w-full bg-slate-950/30 pl-10 pr-3"
            type="search"
            name="global-search"
            qa-id="global-search"
            data-testid="global-search"
            aria-label="Buscar análises, alertas ou janelas"
            placeholder="Buscar análises, alertas ou janelas"
          />
        </label>
      </div>

      <div class="flex shrink-0 items-center gap-3" qa-id="topbar-user-menu" data-testid="topbar-user-menu">
        <div class="hidden text-right md:block">
          <p class="text-sm font-medium text-white" qa-id="topbar-user-name" data-testid="topbar-user-name">{{ currentUser?.name ?? 'Usuário' }}</p>
          <p class="mt-0.5 text-xs text-slate-500">{{ roleLabel }}</p>
        </div>
        <button
          class="focus-ring min-h-11 rounded-xl border border-slate-700/80 bg-slate-950/20 px-3 py-2 text-sm font-medium text-slate-300 transition duration-150 hover:border-slate-600 hover:bg-surface-800 hover:text-white"
          type="button"
          qa-id="logout-button"
          data-testid="logout-button"
          aria-label="Sair do sistema"
          @click="handleLogout"
        >
          Sair
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { Search } from 'lucide-vue-next'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useAuth } from '@/composables/useAuth'
import { useGlobalSearch } from '@/composables/useGlobalSearch'

const { globalSearch } = useGlobalSearch()
const { currentUser, logout } = useAuth()
const router = useRouter()

const roleLabel = computed(() => currentUser.value?.role === 'admin' ? 'Administrador' : 'Usuário')

/** Encerra a sessão local e encaminha para o login. */
function handleLogout(): void {
  logout()
  router.push('/login')
}
</script>
