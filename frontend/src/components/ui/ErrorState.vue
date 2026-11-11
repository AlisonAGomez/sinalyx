<!-- Mensagem de falha da consulta, mantendo a apresentação consistente entre telas. -->
<template>
  <div class="panel border-red-400/20 bg-red-950/[0.15] p-5 text-red-100" role="alert" aria-live="assertive">
    <div class="flex items-start gap-3">
      <div class="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-red-400/20 bg-red-400/10">
        <AlertTriangle class="h-[18px] w-[18px] text-red-300" />
      </div>
      <div>
        <p class="font-semibold">{{ title }}</p>
        <p class="mt-1 text-sm leading-6 text-red-100/70">{{ message }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AlertTriangle } from 'lucide-vue-next'
withDefaults(defineProps<{ title?: string; message?: string }>(), {
  title: 'Não foi possível carregar esta informação',
  message: 'Tente novamente em instantes. Se o problema continuar, verifique o estado do sistema.',
})
</script>
