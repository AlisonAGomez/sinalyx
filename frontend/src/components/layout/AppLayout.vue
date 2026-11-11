<!-- Organiza o layout público e autenticado e o comportamento do menu em telas menores. -->
<template>
  <div class="min-h-[100svh] overflow-x-hidden bg-surface-950 text-slate-100">
    <template v-if="isPublicRoute">
      <RouterView />
    </template>

    <div v-else class="cyber-grid relative min-h-[100svh] overflow-x-hidden lg:pl-[248px]">
      <div class="app-ambient" aria-hidden="true">
        <div class="ambient-network" />
      </div>
      <Sidebar />
      <div class="relative z-10 min-w-0">
        <Topbar />
        <main class="min-w-0 animate-soft-in px-4 pb-28 pt-6 sm:px-6 lg:px-8 lg:pb-10 xl:px-10">
          <div class="app-content">
            <RouterView />
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'

import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'

const route = useRoute()
const isPublicRoute = computed(() => route.meta.public === true)
</script>
