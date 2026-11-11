<!-- Aviso acessível de consulta em andamento. -->
<template>
  <div class="panel p-5" role="status" aria-live="polite" aria-busy="true">
    <div class="flex items-center gap-3 text-slate-300">
      <LoaderCircle class="h-5 w-5 animate-spin text-sky-300" />
      <span class="text-sm font-medium">{{ label }}</span>
    </div>
    <div class="mt-5 grid gap-3 sm:grid-cols-3" aria-hidden="true">
      <div class="skeleton h-20" />
      <div class="skeleton h-20" />
      <div class="skeleton h-20" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircle } from 'lucide-vue-next'
withDefaults(defineProps<{ label?: string }>(), { label: 'Carregando informações' })
</script>
