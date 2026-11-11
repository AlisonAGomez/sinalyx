<!-- Rótulo e cor dos estados recebidos, sem mudar sua classificação. -->
<template>
  <span
    class="inline-flex min-h-6 items-center whitespace-nowrap rounded-lg px-2.5 py-1 text-xs font-semibold leading-none ring-1 ring-inset"
    :class="classes"
  >
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import {
  formatFinalLabel,
  formatRiskLevel,
} from '@/utils/formatters'

const props = defineProps<{
  value?: string | boolean | null
  rotulo?: string
}>()

const normalized = computed(() =>
  String(props.value ?? 'unknown')
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase(),
)

const label = computed(() => {
  if (props.rotulo) return props.rotulo
  if (typeof props.value === 'boolean') {
    return props.value ? 'Sim' : 'Não'
  }
  const value = String(props.value ?? 'unknown')
  if (['low', 'medium', 'high', 'critical'].includes(normalized.value)) {
    return formatRiskLevel(value)
  }
  return formatFinalLabel(value)
})

const classes = computed(() => {
  if (typeof props.value === 'boolean') {
    return props.value
      ? 'bg-emerald-400/10 text-emerald-200 ring-emerald-400/25'
      : 'bg-slate-700/40 text-slate-300 ring-slate-600/50'
  }

  if ([
    'normal',
    'low',
    'success',
    'sucesso',
    'available',
    'disponivel',
    'operational',
    'operacional',
    'ok',
    'ativo',
    'active',
  ].includes(normalized.value)) {
    return 'bg-emerald-400/10 text-emerald-200 ring-emerald-400/20'
  }

  if (['critical', 'critico'].includes(normalized.value)) {
    return 'bg-fuchsia-400/10 text-fuchsia-100 ring-fuchsia-400/25'
  }

  if ([
    'anomaly',
    'high',
    'error',
    'erro',
    'unavailable',
    'indisponivel',
  ].includes(normalized.value)) {
    return 'bg-red-400/10 text-red-200 ring-red-400/20'
  }

  if (['medium', 'medio', 'warning', 'nao configurado'].includes(normalized.value)) {
    return 'bg-amber-400/10 text-amber-200 ring-amber-400/20'
  }

  return 'bg-slate-700/40 text-slate-300 ring-slate-600/50'
})
</script>
