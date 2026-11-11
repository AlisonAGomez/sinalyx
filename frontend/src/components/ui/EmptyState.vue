<!-- Mensagem e ação disponíveis quando não há registros para apresentar. -->
<template>
  <div class="panel p-6 text-center">
    <div class="mx-auto grid h-11 w-11 place-items-center rounded-2xl border border-slate-700/80 bg-surface-850/80 text-slate-400">
      <component :is="icon" class="h-5 w-5" />
    </div>
    <p class="mt-3 text-sm font-semibold text-white">{{ title }}</p>
    <p v-if="message" class="mx-auto mt-1 max-w-lg text-sm leading-6 text-slate-500">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
import { SearchX } from 'lucide-vue-next'
import type { Component } from 'vue'
withDefaults(defineProps<{ title?: string; message?: string; icon?: Component }>(), {
  title: 'Nenhum resultado encontrado',
  message: '',
  icon: () => SearchX,
})
</script>
