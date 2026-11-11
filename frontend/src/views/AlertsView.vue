<!-- Consulta e triagem de alertas registrados, com navegação para a investigação. -->
<template>
  <section class="space-y-5" qa-id="page-alerts" data-testid="page-alerts" data-qa-page="alerts">
    <PageHeader
      eyebrow="Investigação"
      title="Alertas"
      description="Eventos com indícios relevantes organizados por risco para facilitar a triagem e a investigação."
    >
      <template #actions>
        <span v-if="meta" class="rounded-xl border border-slate-800 bg-slate-950/25 px-3 py-2 text-sm text-slate-500">
          {{ filteredAlerts.length }} de {{ meta.total }} exibidos
        </span>
      </template>
    </PageHeader>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />

    <template v-else>
      <section class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Resumo dos alertas carregados">
        <article v-for="item in riskSummary" :key="item.label" class="panel panel-hover p-4">
          <p class="muted-label">{{ item.label }}</p>
          <div class="mt-2 flex items-end justify-between gap-3">
            <p class="text-2xl font-semibold tabular-nums text-white">{{ item.value }}</p>
            <span class="h-2.5 w-2.5 rounded-full" :class="item.dot" aria-hidden="true" />
          </div>
          <p class="mt-2 text-xs text-slate-500">{{ item.hint }}</p>
        </article>
      </section>

      <section class="panel p-5" qa-id="alerts-filter-panel" data-testid="alerts-filter-panel">
        <div class="flex flex-col gap-4 xl:flex-row xl:items-end">
          <div class="grid flex-1 gap-3 md:grid-cols-3">
            <label class="text-sm">
              <span class="muted-label">Evento</span>
              <select v-model="filters.attack_type" class="field mt-2 h-10 w-full" qa-id="alerts-filter-attack-type" data-testid="alerts-filter-attack-type" aria-label="Filtrar por evento">
                <option value="">Todos</option>
                <option v-for="attackType in attackTypeOptions" :key="attackType" :value="attackType">{{ formatAttackType(attackType) }}</option>
              </select>
            </label>
            <label class="text-sm">
              <span class="muted-label">Risco</span>
              <select v-model="filters.risk_level" class="field mt-2 h-10 w-full" qa-id="alerts-filter-risk-level" data-testid="alerts-filter-risk-level" aria-label="Filtrar por risco">
                <option value="">Todos</option><option value="low">Baixo</option><option value="medium">Médio</option><option value="high">Alto</option><option value="critical">Crítico</option>
              </select>
            </label>
            <label class="text-sm">
              <span class="muted-label">Base da análise</span>
              <select v-model="filters.decision_source" class="field mt-2 h-10 w-full" qa-id="alerts-filter-decision-source" data-testid="alerts-filter-decision-source" aria-label="Filtrar pela base da análise">
                <option value="">Todas</option>
                <option v-for="source in decisionSourceOptions" :key="source" :value="source">{{ formatDecisionSource(source) }}</option>
              </select>
            </label>
          </div>
          <p class="max-w-sm text-xs leading-5 text-slate-500">Os filtros atuam sobre os alertas já carregados. Use “Carregar mais” para ampliar a fila.</p>
        </div>
      </section>

      <section class="panel overflow-hidden" qa-id="alerts-table" data-testid="alerts-table">
        <div class="border-b border-slate-800/80 px-5 py-4">
          <p class="muted-label">Fila de investigação</p>
          <h2 class="mt-1 text-sm font-semibold text-white">Eventos que merecem atenção</h2>
        </div>
        <div v-if="filteredAlerts.length" aria-hidden="true" class="hidden grid-cols-[11rem_minmax(0,1fr)_7rem_minmax(0,1.5fr)_7.5rem] gap-4 border-b border-slate-800/80 bg-slate-950/20 px-5 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-600 lg:grid">
          <span>Horário</span><span>Evento</span><span>Risco</span><span>Motivo</span><span class="text-right">Ação</span>
        </div>
        <div v-if="filteredAlerts.length" class="divide-y divide-slate-800/80">
          <article
            v-for="alert in filteredAlerts"
            :key="alert.id"
            class="interactive-row relative grid gap-3 border-l-2 px-5 py-4 lg:grid-cols-[11rem_minmax(0,1fr)_7rem_minmax(0,1.5fr)_7.5rem] lg:items-center lg:gap-4 lg:py-3"
            :class="severityBorder(alert.risk_level)"
            :data-testid="`alert-row-${alert.id}`"
          >
            <div><p class="muted-label lg:sr-only">Horário</p><p class="mt-1 text-sm tabular-nums text-slate-300 lg:mt-0">{{ formatDateTime(alert.window_start) }}</p></div>
            <div class="min-w-0"><p class="muted-label lg:sr-only">Evento</p><h3 class="mt-1 text-sm font-semibold text-white lg:mt-0">{{ formatAttackType(alert.attack_type) }}</h3></div>
            <div><p class="muted-label mb-1 lg:sr-only">Risco</p><StatusBadge :value="alert.risk_level" /></div>
            <div class="min-w-0"><p class="muted-label lg:sr-only">Motivo</p><p class="mt-1 line-clamp-2 text-sm leading-5 text-slate-400 lg:mt-0" :title="formatarMotivo(alert)">{{ formatarMotivo(alert) }}</p></div>
            <button class="btn btn-primary lg:w-full" type="button" :data-testid="`alert-open-${alert.id}`" @click="openAlert(alert.id)">Investigar</button>
          </article>
        </div>
        <div v-else class="p-4"><EmptyState title="Nenhum evento com indícios encontrado" message="Ajuste os filtros ou a busca global para ampliar a triagem." /></div>
      </section>

      <div class="flex flex-wrap items-center gap-3">
        <button v-if="meta && alerts.length < meta.total" class="btn btn-secondary" :disabled="carregandoMais" @click="carregarMais">{{ carregandoMais ? 'Carregando…' : 'Carregar mais alertas' }}</button>
        <p v-if="erroMais" role="alert" class="text-sm text-rose-200">{{ erroMais }}</p>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { useGlobalSearch } from '@/composables/useGlobalSearch'
import { getRecentAlerts } from '@/services/api'
import type { AlertItem, PaginationMeta } from '@/types/api'
import { filterBySearch, windowSearchText } from '@/utils/search'
import { formatDateTime } from '@/utils/formatters'
import { formatarClassificacao as formatAttackType, formatarFonte as formatDecisionSource, formatarMotivo } from '@/utils/apresentacaoSeguranca'

const alerts = ref<AlertItem[]>([])
const carregandoMais = ref(false)
const erroMais = ref('')
const meta = ref<PaginationMeta | null>(null)
const loading = ref(true)
const error = ref('')
const router = useRouter()
const { trimmedSearch } = useGlobalSearch()
const filters = reactive({ attack_type: '', risk_level: '', decision_source: '' })

const attackTypeOptions = computed(() => unique(alerts.value.map((alert) => alert.attack_type).filter(Boolean) as string[]))
const decisionSourceOptions = computed(() => unique(alerts.value.map((alert) => alert.decision_source).filter(Boolean) as string[]))
const filteredAlerts = computed(() => filterBySearch(alerts.value, trimmedSearch.value, windowSearchText).filter(matchesFilters))
const riskSummary = computed(() => [
  { label: 'Alertas exibidos', value: alerts.value.length, dot: 'bg-sky-400', hint: 'Neste recorte da fila' },
  { label: 'Risco alto', value: alerts.value.filter((item) => item.risk_level === 'high' || item.risk_level === 'critical').length, dot: 'bg-red-400', hint: 'Inclui risco crítico' },
  { label: 'Risco médio', value: alerts.value.filter((item) => item.risk_level === 'medium').length, dot: 'bg-amber-400', hint: 'Requer avaliação contextual' },
  { label: 'Risco baixo', value: alerts.value.filter((item) => item.risk_level === 'low').length, dot: 'bg-emerald-400', hint: 'Menor prioridade relativa' },
])

/** Busca a próxima página de alertas e mantém os registros já carregados. */
async function carregarMais(): Promise<void> {
  carregandoMais.value = true
  erroMais.value = ''
  try {
    const pagina = await getRecentAlerts(20, alerts.value.length)
    const ids = new Set(alerts.value.map(item => item.id))
    alerts.value.push(...pagina.alerts.filter(item => !ids.has(item.id)))
    meta.value = pagina.meta
  } catch {
    erroMais.value = 'Não foi possível carregar mais alertas.'
  } finally {
    carregandoMais.value = false
  }
}
/** Remove valores repetidos usados nas opções dos filtros. */
function unique(values: string[]): string[] { return Array.from(new Set(values)).sort() }
/** Confere os filtros locais de apresentação dos alertas. */
function matchesFilters(alert: AlertItem): boolean {
  if (filters.attack_type && alert.attack_type !== filters.attack_type) return false
  if (filters.risk_level && alert.risk_level !== filters.risk_level) return false
  if (filters.decision_source && alert.decision_source !== filters.decision_source) return false
  return true
}
/** Escolhe a borda do alerta a partir do risco recebido. */
function severityBorder(value?: string | null): string {
  if (value === 'critical') return 'border-l-fuchsia-400'
  if (value === 'high') return 'border-l-red-400'
  if (value === 'medium') return 'border-l-amber-400'
  return 'border-l-emerald-400'
}
/** Abre a investigação do alerta pela rota já existente. */
function openAlert(id: number): void { router.push(`/windows/${id}`) }

onMounted(async () => {
  try {
    const response = await getRecentAlerts(20, 0)
    alerts.value = response.alerts
    meta.value = response.meta
  } catch {
    error.value = 'Não foi possível carregar a fila de alertas.'
  } finally {
    loading.value = false
  }
})
</script>
