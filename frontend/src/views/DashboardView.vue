<!-- Visão das análises e dos registros disponíveis; sem coleta automática pelo painel. -->
<template>
  <section class="space-y-5" qa-id="page-dashboard" data-testid="page-dashboard" data-qa-page="dashboard">
    <PageHeader
      eyebrow="Visão geral"
      title="Dashboard"
      description="Acompanhe as análises realizadas, identifique eventos que merecem atenção e acesse rapidamente os detalhes para investigação."
    />

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />

    <template v-else-if="summary">
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          qa-id="dashboard-card-analyses"
          data-testid="dashboard-card-analyses"
          label="Análises"
          hint="Arquivos processados e registrados"
          :value="historySummary?.analyses?.total_analyses ?? 'Não disponível'"
          :icon="Activity"
          icon-class="border-sky-400/30 bg-sky-400/10 text-sky-200"
        />
        <StatCard
          qa-id="dashboard-card-alerts"
          data-testid="dashboard-card-alerts"
          label="Alertas"
          hint="Eventos registrados para investigação"
          :value="historySummary?.live?.total_alerts ?? 'Não disponível'"
          :icon="Bell"
          icon-class="border-amber-400/30 bg-amber-400/10 text-amber-200"
        />
        <StatCard
          qa-id="dashboard-card-anomalies"
          data-testid="dashboard-card-anomalies"
          label="Com indícios"
          hint="Janelas classificadas com sinais relevantes"
          :value="summary.total_anomalies"
          :icon="ShieldAlert"
          icon-class="border-red-400/30 bg-red-400/10 text-red-200"
        />
        <StatCard
          label="Sem indícios"
          hint="Janelas sem sinais relevantes no resultado final"
          :value="summary.total_normal"
          :icon="ShieldCheck"
          icon-class="border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
        />
      </div>

      <div class="grid gap-4 xl:grid-cols-[1.35fr_0.85fr]">
        <RecentWindowsChart :title="recentChartTitle" :items="recentChartItems" />

        <section class="panel overflow-hidden" qa-id="dashboard-investigation-queue" data-testid="dashboard-investigation-queue">
          <div class="border-b border-slate-800/80 px-5 py-4">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="muted-label">Prioridade</p>
                <h2 class="mt-1 text-sm font-semibold text-white">Fila de investigação</h2>
              </div>
              <RouterLink class="text-xs font-medium text-sky-300 transition hover:text-sky-200" to="/alerts">Ver todos</RouterLink>
            </div>
            <div v-if="latestAlert" class="mt-3" qa-id="dashboard-latest-alert" data-testid="dashboard-latest-alert">
              <button class="btn btn-secondary" type="button" qa-id="dashboard-investigate-latest-alert" data-testid="dashboard-investigate-latest-alert" @click="openWindow(latestAlert.id)">Investigar último alerta</button>
            </div>
          </div>

          <div v-if="investigationQueue.length" class="divide-y divide-slate-800/80">
            <button
              v-for="alert in investigationQueue"
              :key="alert.id"
              type="button"
              class="group grid w-full grid-cols-[minmax(0,1fr)_auto] gap-3 px-5 py-4 text-left transition hover:bg-sky-400/[0.035]"
              @click="openWindow(alert.id)"
            >
              <span class="min-w-0">
                <span class="block truncate text-sm font-semibold text-slate-100">{{ formatAttackType(alert.attack_type || alert.final_label) }}</span>
                <span class="mt-1 block text-xs text-slate-500">{{ formatDateTime(alert.window_start) }}</span>
              </span>
              <span class="flex items-center gap-2">
                <StatusBadge :value="alert.risk_level" />
                <ArrowRight class="h-4 w-4 text-slate-600 transition group-hover:translate-x-0.5 group-hover:text-sky-300" />
              </span>
            </button>
          </div>
          <EmptyState v-else title="Nenhum alerta recente" message="Não há eventos disponíveis para investigação neste recorte." />
        </section>
      </div>

      <div class="panel overflow-hidden" qa-id="dashboard-recent-windows" data-testid="dashboard-recent-windows">
        <div class="border-b border-slate-800/80 px-5 py-4">
          <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p class="muted-label">Atividade recente</p>
              <h2 class="mt-1 text-sm font-semibold text-white">Resultados recentes</h2>
              <p class="mt-1 text-xs leading-5 text-slate-500">Abra uma ocorrência para entender a classificação, o risco e o motivo apresentado pelo sistema.</p>
            </div>
            <span class="shrink-0 rounded-lg border border-slate-800 bg-slate-950/25 px-2.5 py-1 text-xs tabular-nums text-slate-500">{{ recentWindows.length }} registros</span>
          </div>
        </div>
        <div v-if="recentWindows.length > 0" aria-hidden="true" class="hidden grid-cols-[11rem_minmax(0,1fr)_7rem_minmax(0,1.3fr)_7.5rem] gap-4 border-b border-slate-800/80 bg-slate-950/20 px-5 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-600 lg:grid">
          <span>Horário</span><span>Resultado</span><span>Risco</span><span>Motivo</span><span class="text-right">Ação</span>
        </div>
        <div v-if="recentWindows.length > 0" class="divide-y divide-slate-800/80">
          <article
            v-for="window in recentWindows"
            :key="window.id"
            :qa-id="`dashboard-recent-window-row-${window.id}`"
            :data-testid="`dashboard-recent-window-row-${window.id}`"
            class="interactive-row grid gap-3 px-5 py-4 lg:grid-cols-[11rem_minmax(0,1fr)_7rem_minmax(0,1.3fr)_7.5rem] lg:items-center lg:gap-4 lg:py-3"
          >
            <div><p class="muted-label lg:sr-only">Horário</p><p class="mt-1 text-sm tabular-nums text-slate-300 lg:mt-0">{{ formatDateTime(window.window_start) }}</p></div>
            <div class="min-w-0"><p class="muted-label lg:sr-only">Resultado</p><h3 class="mt-1 text-sm font-semibold text-white lg:mt-0">{{ formatAttackType(window.attack_type || window.final_label) }}</h3></div>
            <div><p class="muted-label mb-1 lg:sr-only">Risco</p><StatusBadge :value="window.risk_level" /></div>
            <p class="line-clamp-2 text-sm leading-5 text-slate-400">{{ formatarMotivo(window) }}</p>
            <button
              class="btn lg:w-full"
              :class="window.final_label === 'anomaly' ? 'btn-primary' : 'btn-secondary'"
              type="button"
              :qa-id="`dashboard-open-window-${window.id}`"
              :data-testid="`dashboard-open-window-${window.id}`"
              @click="openWindow(window.id)"
            >
              {{ window.final_label === 'anomaly' ? 'Investigar' : 'Ver detalhe' }}
            </button>
          </article>
        </div>
        <EmptyState v-else title="Nenhum resultado encontrado" message="Ajuste a busca global ou consulte o Histórico para visualizar análises anteriores." />
      </div>

      <details class="panel p-5">
        <summary class="focus-ring cursor-pointer rounded-lg text-sm font-semibold text-white">Ver distribuições do histórico</summary>
        <p class="mt-3 text-sm text-slate-400">Distribuições registradas no histórico complementar. Elas descrevem ocorrências e não representam precisão dos modelos.</p>
        <div class="mt-3 flex flex-wrap gap-4 text-sm text-slate-400">
          <span qa-id="dashboard-card-total-windows" data-testid="dashboard-card-total-windows">Janelas analisadas: {{ summary.total_windows }}</span>
          <span qa-id="dashboard-card-executions" data-testid="dashboard-card-executions">Lotes processados: {{ historySummary?.live?.total_executions ?? 'Não disponível' }}</span>
        </div>
        <div class="mt-4 grid gap-4 xl:grid-cols-2">
          <HorizontalBarChart qa-id="dashboard-chart-attack-distribution" data-testid="dashboard-chart-attack-distribution" title="Padrões identificados" :items="attackChartItems" rotulos-formatados />
          <HorizontalBarChart qa-id="dashboard-chart-risk-distribution" data-testid="dashboard-chart-risk-distribution" title="Níveis de risco" :items="riskChartItems" rotulos-formatados />
        </div>
      </details>
      <ErrorState v-if="chartError" :message="chartError" />
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { Activity, ArrowRight, Bell, ShieldAlert, ShieldCheck } from 'lucide-vue-next'

import HorizontalBarChart from '@/components/charts/HorizontalBarChart.vue'
import RecentWindowsChart, { type RecentWindowChartItem } from '@/components/charts/RecentWindowsChart.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { useGlobalSearch } from '@/composables/useGlobalSearch'
import { getDashboardSummary, getHistorySummary, getHistoryWindows } from '@/services/api'
import type { DashboardSummary, HistorySummary, WindowItem } from '@/types/api'
import { filterBySearch, windowSearchText } from '@/utils/search'
import { formatDateTime, formatRiskLevel } from '@/utils/formatters'
import { formatarClassificacao as formatAttackType, formatarMotivo } from '@/utils/apresentacaoSeguranca'

const summary = ref<DashboardSummary | null>(null)
const historySummary = ref<HistorySummary | null>(null)
const historyWindows = ref<WindowItem[]>([])
const loading = ref(true)
const error = ref('')
const chartError = ref('')
const router = useRouter()
const { trimmedSearch } = useGlobalSearch()

type ChartItem = { label: string; value: number; color: string }
const chartColors = ['bg-emerald-400', 'bg-sky-400', 'bg-cyan-400', 'bg-violet-400', 'bg-amber-400']
const attackChartColorByKey: Record<string, string> = {
  normal: 'bg-emerald-400', brute_force: 'bg-amber-400', ssh_bruteforce: 'bg-amber-400',
  syn_flood: 'bg-red-500', ddos: 'bg-red-500', ddo_s: 'bg-red-500', d_do_s: 'bg-red-500',
  ddos_syn_flood: 'bg-red-500', port_scan: 'bg-cyan-400', ssh_suspicious: 'bg-amber-400',
  unknown_anomaly: 'bg-slate-500', unknown_anomalies: 'bg-slate-500', anomalia_nao_classificada: 'bg-slate-500',
}
const riskChartColorByKey: Record<string, string> = {
  low: 'bg-emerald-400', baixo: 'bg-emerald-400', medium: 'bg-amber-400', medio: 'bg-amber-400',
  high: 'bg-red-500', alto: 'bg-red-500', critical: 'bg-fuchsia-500', critico: 'bg-fuchsia-500', unknown: 'bg-slate-500',
}

const attackChartItems = computed<ChartItem[]>(() => buildChartItems(
  historySummary.value?.live?.attack_type_distribution ?? summary.value?.attack_type_distribution ?? {},
  formatAttackType,
  attackChartColor,
))
const riskChartItems = computed<ChartItem[]>(() => buildChartItems(
  historySummary.value?.live?.risk_level_distribution ?? summary.value?.risk_level_distribution ?? {},
  formatRiskLevel,
  riskChartColor,
))
const recentWindows = computed(() => filterBySearch(
  historyWindows.value.length > 0 ? historyWindows.value : summary.value?.recent_windows ?? [],
  trimmedSearch.value,
  windowSearchText,
))
const latestAlert = computed(() => historySummary.value?.live?.latest_alert
  ?? recentWindows.value.find((item) => item.final_label === 'anomaly')
  ?? summary.value?.recent_windows?.find((item) => item.final_label === 'anomaly')
  ?? null)
const investigationQueue = computed(() => recentWindows.value
  .filter((item) => item.final_label === 'anomaly')
  .slice(0, 4))
const recentChartItems = computed<RecentWindowChartItem[]>(() => recentWindows.value.slice(0, 12).map((item, index) => ({
  id: item.id,
  label: String(index + 1).padStart(2, '0'),
  riskLevel: item.risk_level,
  isAnomaly: item.final_label === 'anomaly',
  tooltip: `${formatAttackType(item.attack_type || item.final_label)} · ${formatRiskLevel(item.risk_level)}`,
})))
const recentChartTitle = computed(() => {
  const total = recentChartItems.value.length
  if (total === 0) return 'Últimas janelas processadas'
  if (total === 1) return 'Última janela processada'
  return `Últimas ${total} janelas processadas`
})

/** Prepara os itens de apresentação do gráfico com as contagens recebidas. */
function buildChartItems(distribution: Record<string, number>, formatter: (value?: string | null) => string, colorFor: (label: string, index: number) => string): ChartItem[] {
  return Object.entries(distribution).map(([label, value], index) => ({ label: formatter(label), value: Number(value || 0), color: colorFor(label, index) }))
}
/** Seleciona a cor visual padrão de uma categoria. */
function defaultChartColor(_label: string, index: number): string { return chartColors[index % chartColors.length] }
/** Seleciona a cor visual da categoria de evento recebida. */
function attackChartColor(label: string, index: number): string { return attackChartColorByKey[normalizeChartKey(label)] ?? defaultChartColor(label, index) }
/** Seleciona a cor visual da categoria de risco recebida. */
function riskChartColor(label: string, index: number): string { return riskChartColorByKey[normalizeChartKey(label)] ?? defaultChartColor(label, index) }
/** Padroniza a chave usada para consultar as cores do gráfico. */
function normalizeChartKey(value: string): string { return value.trim().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-zA-Z0-9]+/g, '_').replace(/^_+|_+$/g, '').toLowerCase() }
/** Abre o detalhe da janela selecionada pela rota existente. */
function openWindow(id: number): void { router.push(`/windows/${id}`) }

onMounted(async () => {
  try {
    summary.value = await getDashboardSummary()
  } catch {
    error.value = 'Não foi possível carregar o resumo do Dashboard.'
  } finally {
    loading.value = false
  }

  const [historySummaryResult, historyWindowsResult] = await Promise.allSettled([
    getHistorySummary(),
    getHistoryWindows(12, 0),
  ])
  if (historySummaryResult.status === 'fulfilled') historySummary.value = historySummaryResult.value
  if (historyWindowsResult.status === 'fulfilled') historyWindows.value = historyWindowsResult.value.windows
  if (historySummaryResult.status === 'rejected' || historyWindowsResult.status === 'rejected') {
    chartError.value = 'Parte do histórico não pôde ser consultada. Os dados disponíveis continuam exibidos.'
  }
})
</script>
