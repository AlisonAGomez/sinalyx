<!-- Apresenta até doze janelas recebidas. Altura e cor representam a categoria de risco registrada. -->
<template>
  <section class="panel panel-hover p-5">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <p class="muted-label">Comportamento recente</p>
        <h2 class="mt-1 text-sm font-semibold text-white">{{ title }}</h2>
        <p class="mt-2 text-xs leading-5 text-slate-400">Resultados das janelas mais recentes disponíveis no histórico.</p>
      </div>
      <p class="text-xs leading-5 text-slate-500">Altura indica a categoria de risco; janelas sem indícios usam a altura mínima.</p>
    </div>

    <p v-if="items.length === 0" class="mt-5 text-sm text-slate-400">Nenhum resultado recente para exibir.</p>

    <div v-else class="mt-6">
      <div class="flex h-40 items-end gap-2 border-b border-slate-800/80 pb-2">
        <div v-for="item in items" :key="item.id" class="group flex min-w-0 flex-1 flex-col items-center gap-2">
          <div class="flex h-28 w-full items-end justify-center rounded-t-lg border-x border-t border-slate-800/60 bg-slate-950/[0.22] px-1 transition group-hover:border-sky-400/20 group-hover:bg-sky-400/[0.03]">
            <div
              class="w-full max-w-8 origin-bottom rounded-t-md shadow-[0_0_14px_rgba(56,189,248,0.08)] transition duration-200 group-hover:brightness-125"
              :class="barClass(item)"
              :style="{ height: `${barHeight(item)}%`, animation: 'bar-grow-y 540ms cubic-bezier(.2,.7,.2,1) both' }"
              :title="item.tooltip"
            />
          </div>
          <span class="max-w-full truncate text-[10px] text-slate-600">{{ item.label }}</span>
        </div>
      </div>
      <p class="mt-2 text-center text-[10px] text-slate-500">Janelas processadas</p>
      <div class="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-500">
        <span class="inline-flex items-center gap-2"><span class="h-2 w-2 rounded-full bg-emerald-400" /> Sem indícios relevantes</span>
        <span class="inline-flex items-center gap-2"><span class="h-2 w-2 rounded-full bg-amber-400" /> Atenção</span>
        <span class="inline-flex items-center gap-2"><span class="h-2 w-2 rounded-full bg-red-400" /> Risco elevado</span>
      </div>
    </div>
    <p class="mt-4 text-xs leading-5 text-slate-500">Os resultados refletem as janelas mais recentes disponíveis no histórico. Recarregue a página para consultar atualizações.</p>
  </section>
</template>

<script setup lang="ts">
export type RecentWindowChartItem = {
  id: string | number
  label: string
  riskLevel?: string | null
  isAnomaly: boolean
  tooltip: string
}

defineProps<{ title: string; items: RecentWindowChartItem[] }>()

/** Padroniza a categoria de risco recebida, sem recalcular o risco. */
function normalizedRisk(value?: string | null): string { return String(value ?? '').trim().toLowerCase() }
/** Traduz a categoria de risco em altura visual, mantendo altura mínima para a janela. */
function barHeight(item: RecentWindowChartItem): number {
  if (!item.isAnomaly) return 26
  const risk = normalizedRisk(item.riskLevel)
  if (risk === 'critical') return 96
  if (risk === 'high') return 78
  if (risk === 'medium') return 58
  if (risk === 'low') return 38
  return 48
}
/** Escolhe a cor da barra conforme a categoria de risco já informada. */
function barClass(item: RecentWindowChartItem): string {
  if (!item.isAnomaly) return 'bg-emerald-400'
  const risk = normalizedRisk(item.riskLevel)
  if (risk === 'critical') return 'bg-fuchsia-400'
  if (risk === 'high') return 'bg-red-400'
  if (risk === 'medium') return 'bg-amber-400'
  return 'bg-cyan-400'
}
</script>
