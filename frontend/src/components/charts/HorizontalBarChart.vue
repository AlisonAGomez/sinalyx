<!-- Gráfico de distribuição: comprimento das barras representa os valores recebidos. -->
<template>
  <section class="panel panel-hover p-5">
    <div class="flex items-center justify-between gap-3">
      <div>
        <p class="muted-label">Distribuição</p>
        <h2 class="mt-1 text-sm font-semibold text-white">{{ title }}</h2>
      </div>
      <p class="rounded-lg border border-slate-800 bg-slate-950/25 px-2.5 py-1 text-xs tabular-nums text-slate-500">{{ total }} registros</p>
    </div>

    <p v-if="items.length === 0" class="mt-5 text-sm text-slate-400">Nenhum dado disponível para este gráfico.</p>

    <div v-else class="mt-5 space-y-4">
      <div v-for="item in items" :key="item.label" class="group space-y-1.5">
        <div class="flex items-center justify-between gap-3 text-sm">
          <span class="text-slate-300">{{ displayLabel(item.label) }}</span>
          <span class="font-semibold tabular-nums text-white">{{ item.value }}</span>
        </div>
        <div class="h-2.5 overflow-hidden rounded-full border border-slate-800/70 bg-slate-950/[0.45]">
          <div
            class="h-full origin-left rounded-full transition duration-200 group-hover:brightness-125"
            :class="item.color"
            :style="{ width: `${barWidth(item.value)}%`, animation: 'bar-grow-x 520ms cubic-bezier(.2,.7,.2,1) both' }"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatDisplayText } from '@/utils/formatters'

export type ChartItem = { label: string; value: number; color: string }
const props = defineProps<{ title: string; items: ChartItem[]; rotulosFormatados?: boolean }>()
const total = computed(() => props.items.reduce((sum, item) => sum + Number(item.value || 0), 0))
const maxValue = computed(() => Math.max(1, ...props.items.map((item) => Number(item.value || 0))))
/** Calcula a largura visual da barra a partir do maior valor apresentado. */
function barWidth(value: number): number { return Math.max(4, Math.round((Number(value || 0) / maxValue.value) * 100)) }
/** Escolhe o rótulo apresentado para cada categoria do gráfico. */
function displayLabel(value: string): string { return props.rotulosFormatados ? value : formatDisplayText(value) || value }
</script>
