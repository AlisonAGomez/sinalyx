<!-- Consulta de análises importadas e histórico complementar, com filtros e exportação. -->
<template>
  <section class="mx-auto w-full max-w-[1440px] space-y-4" qa-id="page-history" data-testid="page-history" data-qa-page="history">
    <PageHeader
      eyebrow="Consulta e investigação"
      title="Histórico de análises"
      description="Consulta análises realizadas e registros complementares persistidos."
    />

    <div class="panel flex flex-nowrap gap-2 overflow-x-auto p-2" role="tablist" aria-label="Seções do histórico">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        role="tab"
        :aria-selected="activeTab === tab.key"
        :qa-id="`history-tab-${tab.key}`"
        :data-testid="`history-tab-${tab.key}`"
        class="focus-ring shrink-0 rounded-md px-3 py-2 text-sm font-medium transition"
        :class="
          activeTab === tab.key
            ? 'bg-sky-400/10 text-sky-200 ring-1 ring-sky-400/20'
            : 'text-slate-400 hover:bg-surface-800 hover:text-white'
        "
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <div v-if="usesWindowFilters" class="panel p-4">
      <div class="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <label class="text-sm">
          <span class="muted-label">Período inicial</span>
          <input
            v-model="filters.date_from"
            type="datetime-local"
            name="history-date-from"
            qa-id="history-filter-date-from"
            data-testid="history-filter-date-from"
            aria-label="Período inicial"
            class="mt-2 w-full rounded-md border border-slate-800 bg-surface-850 px-3 py-2 text-slate-200"
          />
        </label>
        <label class="text-sm">
          <span class="muted-label">Período final</span>
          <input
            v-model="filters.date_to"
            type="datetime-local"
            name="history-date-to"
            qa-id="history-filter-date-to"
            data-testid="history-filter-date-to"
            aria-label="Período final"
            class="mt-2 w-full rounded-md border border-slate-800 bg-surface-850 px-3 py-2 text-slate-200"
          />
        </label>
        <label class="text-sm">
          <span class="muted-label">Classificação</span>
          <select v-model="filters.final_label" name="history-final-label" qa-id="history-filter-final-label" data-testid="history-filter-final-label" aria-label="Classificação" class="mt-2 w-full rounded-md border border-slate-800 bg-surface-850 px-3 py-2 text-slate-200">
            <option value="">Todas</option>
            <option value="normal">{{ formatFinalLabel('normal') }}</option>
            <option value="anomaly">{{ formatFinalLabel('anomaly') }}</option>
          </select>
        </label>
        <label class="text-sm">
          <span class="muted-label">Padrão identificado</span>
          <select v-model="filters.attack_type" name="history-attack-type" qa-id="history-filter-attack-type" data-testid="history-filter-attack-type" aria-label="Padrão identificado" class="mt-2 w-full rounded-md border border-slate-800 bg-surface-850 px-3 py-2 text-slate-200">
            <option value="">Todos</option>
            <option
              v-for="attackType in attackTypeFilterOptions"
              :key="attackType"
              :value="attackType"
            >
              {{ formatAttackType(attackType) }}
            </option>
          </select>
        </label>
        <label class="text-sm">
          <span class="muted-label">Risco</span>
          <select v-model="filters.risk_level" name="history-risk-level" qa-id="history-filter-risk-level" data-testid="history-filter-risk-level" aria-label="Risco" class="mt-2 w-full rounded-md border border-slate-800 bg-surface-850 px-3 py-2 text-slate-200">
            <option value="">Todos</option>
            <option value="low">Baixo</option>
            <option value="medium">Médio</option>
            <option value="high">Alto</option>
            <option value="critical">Crítico</option>
          </select>
        </label>

        <label class="text-sm">
          <span class="muted-label">IP de origem</span>
          <input v-model="filters.src_ip" name="history-src-ip" qa-id="history-filter-src-ip" data-testid="history-filter-src-ip" aria-label="IP de origem" class="mt-2 w-full rounded-md border border-slate-800 bg-surface-850 px-3 py-2 text-slate-200" />
        </label>
        <label class="text-sm">
          <span class="muted-label">IP de destino</span>
          <input v-model="filters.dst_ip" name="history-dst-ip" qa-id="history-filter-dst-ip" data-testid="history-filter-dst-ip" aria-label="IP de destino" class="mt-2 w-full rounded-md border border-slate-800 bg-surface-850 px-3 py-2 text-slate-200" />
        </label>
        <label class="text-sm">
          <span class="muted-label">Porta</span>
          <input v-model="filters.dst_port" name="history-dst-port" qa-id="history-filter-dst-port" data-testid="history-filter-dst-port" aria-label="Porta" class="mt-2 w-full rounded-md border border-slate-800 bg-surface-850 px-3 py-2 text-slate-200" />
        </label>
        <label class="text-sm">
          <span class="muted-label">Protocolo</span>
          <input v-model="filters.protocol" name="history-protocol" qa-id="history-filter-protocol" data-testid="history-filter-protocol" aria-label="Protocolo" class="mt-2 w-full rounded-md border border-slate-800 bg-surface-850 px-3 py-2 text-slate-200" />
        </label>
        <label class="text-sm">
          <span class="muted-label">Ação</span>
          <input v-model="filters.action" name="history-action" qa-id="history-filter-action" data-testid="history-filter-action" aria-label="Ação" class="mt-2 w-full rounded-md border border-slate-800 bg-surface-850 px-3 py-2 text-slate-200" />
        </label>
        <label class="flex items-end gap-2 text-sm text-slate-300">
          <input
            v-model="filters.only_anomalies"
            type="checkbox"
            name="history-only-anomalies"
            qa-id="history-filter-only-anomalies"
            data-testid="history-filter-only-anomalies"
            aria-label="Somente com indícios"
            class="h-4 w-4 rounded border-slate-700 bg-surface-850 text-sky-400"
          />
          Somente com indícios
        </label>
      </div>
      <div class="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          class="btn btn-primary"
          qa-id="history-apply-filters"
          data-testid="history-apply-filters"
          @click="reloadFiltered"
        >
          Aplicar filtros
        </button>
        <button
          type="button"
          class="btn btn-secondary"
          qa-id="history-clear-filters"
          data-testid="history-clear-filters"
          @click="clearFilters"
        >
          Limpar
        </button>
      </div>
    </div>

    <section v-if="activeTab !== 'analyses'" class="panel border-slate-700/80 p-4" data-testid="history-complementary-context">
      <p class="muted-label">Histórico complementar</p>
      <p class="mt-1 text-sm leading-6 text-slate-300">Registros complementares persistidos para consulta. A integração contínua direta com o pfSense não está habilitada nesta versão.</p>
    </section>
    <p class="text-xs leading-5 text-slate-400">Logs de firewall do pfSense permitem observar conexões, portas, protocolo, volume e repetição, mas não tentativas de senha ou falhas de autenticação.</p>
    <button v-if="activeTab === 'analyses'" class="btn btn-secondary self-start" :disabled="loading.analyses || !filteredAnalyses.length" @click="exportarAnalises">Exportar análises exibidas em PDF</button>
    <details v-else class="panel p-4">
      <summary class="focus-ring cursor-pointer text-sm font-semibold text-white">Exportações do histórico complementar</summary>
      <div class="mt-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="muted-label">Exportações</p>
          <p class="mt-1 text-sm text-slate-400">Exportações limitadas a até 500 registros por consulta; não representam necessariamente todo o banco.</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button class="btn btn-primary" type="button" qa-id="history-export-filtered-pdf" data-testid="history-export-filtered-pdf" @click="executarExportacao(exportFilteredHistoryPdf)">
            Exportar filtrados em PDF
          </button>
          <button class="btn btn-secondary" type="button" qa-id="history-export-all-pdf" data-testid="history-export-all-pdf" @click="executarExportacao(exportAllHistoryPdf)">
            Exportar janelas carregadas em PDF
          </button>
          <button class="btn btn-secondary" type="button" qa-id="history-export-alerts-pdf" data-testid="history-export-alerts-pdf" @click="executarExportacao(exportAlertsPdf)">
            Exportar alertas em PDF
          </button>
          <button class="btn btn-secondary" type="button" qa-id="history-export-executions-pdf" data-testid="history-export-executions-pdf" @click="executarExportacao(exportExecutionsPdf)">
            Exportar lotes processados em PDF
          </button>
          <button class="btn btn-secondary" type="button" qa-id="history-export-summary-json" data-testid="history-export-summary-json" @click="executarExportacao(exportSummaryJson)">
            Exportar resumo JSON
          </button>
        </div>
      </div>
    </details>
    <p v-if="exportFeedback" role="status" class="text-sm text-slate-300">{{ exportFeedback }}</p>

    <template v-if="activeTab === 'summary'">
      <LoadingState v-if="loading.summary" />
      <ErrorState v-else-if="errors.summary" :message="errors.summary" />
      <template v-else-if="summary">
        <div class="grid gap-4 md:grid-cols-3">
          <SummaryBox label="Janelas" :value="summary.live?.total_windows" />
          <SummaryBox label="Alertas" :value="summary.live?.total_alerts" />
          <SummaryBox label="Lotes processados" :value="summary.live?.total_executions" />
        </div>

        <div class="grid gap-4 xl:grid-cols-2">
          <DistributionBox
            title="Distribuição"
            :items="summary.live?.attack_type_distribution"
            kind="attack"
          />
          <DistributionBox
            title="Risco"
            :items="summary.live?.risk_level_distribution"
            kind="risk"
          />
        </div>
      </template>
    </template>

    <template v-else-if="activeTab === 'windows'">
      <LoadingState v-if="activeWindowLoading" />
      <ErrorState v-else-if="activeWindowError" :message="activeWindowError" />
      <div v-else class="panel overflow-hidden" qa-id="history-windows-table" data-testid="history-windows-table">
        <div class="border-b border-slate-800 px-4 py-3">
          <div class="flex items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-semibold text-white">Janelas</h2>
              <p class="mt-1 text-sm text-slate-500">
                Janelas carregadas nesta consulta, incluindo resultados sem indícios e com indícios.
              </p>
            </div>
            <p v-if="activeWindowMeta" class="text-sm text-slate-500">
              {{ activeWindowRows.length }} exibidos de {{ activeWindowMeta.total }}
            </p>
          </div>
        </div>
        <p v-if="activeWindowRows.length === 0" class="p-4 text-sm text-slate-400">
          Não existem registros complementares disponíveis.
        </p>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-800 text-sm">
            <thead class="bg-surface-850 text-left text-xs uppercase text-slate-500">
              <tr>
                <th class="px-4 py-3 font-medium">Início da janela</th>
                <th class="px-4 py-3 font-medium">Classificação</th>
                <th class="px-4 py-3 font-medium">Padrão identificado</th>
                <th class="px-4 py-3 font-medium">Risco</th>
                <th class="px-4 py-3 font-medium">Base da análise</th>
                <th class="px-4 py-3 font-medium">Detalhe</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
              <tr
                v-for="row in activeWindowRows"
                :key="row.id"
                :qa-id="`history-window-row-${row.id}`"
                :data-testid="`history-window-row-${row.id}`"
                class="table-row cursor-pointer"
                tabindex="0"
                @click="openWindow(row.id)"
                @keydown.enter="openWindow(row.id)"
                @keydown.space.prevent="openWindow(row.id)"
              >
                <td class="px-4 py-3 font-medium text-sky-300">{{ formatDateTime(row.window_start) }}</td>
                <td class="px-4 py-3"><StatusBadge :value="row.final_label" :rotulo="formatFinalLabel(row.final_label)" /></td>
                <td class="px-4 py-3 text-slate-300">{{ formatAttackType(row.attack_type) }}</td>
                <td class="px-4 py-3"><StatusBadge :value="row.risk_level" /></td>
                <td class="px-4 py-3 text-slate-400">{{ formatarMotivo(row) }}</td>
                <td class="px-4 py-3">
                  <button
                    class="btn"
                    :class="row.final_label === 'anomaly' ? 'btn-primary' : 'btn-secondary'"
                    type="button"
                    :qa-id="`history-window-open-${row.id}`"
                    :data-testid="`history-window-open-${row.id}`"
                    @click.stop="openWindow(row.id)"
                  >
                    {{ row.final_label === 'anomaly' ? 'Investigar' : 'Ver detalhe' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <template v-else-if="activeTab === 'alerts'">
      <LoadingState v-if="activeWindowLoading" />
      <ErrorState v-else-if="activeWindowError" :message="activeWindowError" />
      <div v-else class="space-y-4">
        <div class="panel p-4">
          <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 class="text-sm font-semibold text-white">Alertas para investigação</h2>
              <p class="mt-1 text-sm text-slate-500">
                Triagem focada apenas nas janelas anômalas que precisam de atenção.
              </p>
            </div>
            <p v-if="activeWindowMeta" class="text-sm text-slate-500">
              {{ activeWindowRows.length }} exibidos de {{ activeWindowMeta.total }}
            </p>
          </div>
        </div>

        <p v-if="activeWindowRows.length === 0" class="panel p-4 text-sm text-slate-400">
          Não existem registros complementares disponíveis.
        </p>

        <div v-else class="grid gap-3 xl:grid-cols-2">
          <article
            v-for="row in activeWindowRows"
            :key="row.id"
            :qa-id="`history-alert-card-${row.id}`"
            :data-testid="`history-alert-card-${row.id}`"
            class="panel border-l-4 border-l-rose-400 p-4"
          >
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p class="text-sm font-semibold text-white">{{ formatAttackType(row.attack_type) }}</p>
                <p class="mt-1 text-sm text-slate-500">{{ formatDateTime(row.window_start) }}</p>
              </div>
              <StatusBadge :value="row.risk_level" />
            </div>

            <div class="mt-4 grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <p class="muted-label">Classificação</p>
                <p class="mt-1 text-slate-200">{{ formatFinalLabel(row.final_label) }}</p>
              </div>
              <div>
                <p class="muted-label">Base da análise</p>
                <p class="mt-1 text-slate-200">{{ formatarMotivo(row) }}</p>
              </div>


            </div>

            <div class="mt-4 flex justify-end">
              <button
                class="btn btn-primary"
                type="button"
                :qa-id="`history-alert-open-${row.id}`"
                :data-testid="`history-alert-open-${row.id}`"
                @click="openWindow(row.id)"
              >
                Investigar
              </button>
            </div>
          </article>
        </div>
      </div>
    </template>

    <template v-else-if="activeTab === 'executions'">
      <LoadingState v-if="loading.executions" />
      <ErrorState v-else-if="errors.executions" :message="errors.executions" />
      <div v-else class="panel overflow-hidden">
        <div class="border-b border-slate-800 px-4 py-3">
          <div class="flex items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-semibold text-white">Lotes processados</h2>
              <p class="mt-1 text-sm text-slate-500">
                Cada lote representa um conjunto de logs processado pelo pipeline do Sinalyx.
              </p>
            </div>
            <p v-if="executionsMeta" class="text-sm text-slate-500">
              {{ filteredExecutions.length }} exibidas de {{ executionsMeta.total }}
            </p>
          </div>
        </div>
        <p v-if="filteredExecutions.length === 0" class="p-4 text-sm text-slate-400">
          Não existem registros complementares disponíveis.
        </p>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-800 text-sm">
            <thead class="bg-surface-850 text-left text-xs uppercase text-slate-500">
              <tr>
                <th class="px-4 py-3 font-medium">Execução</th>
                <th class="px-4 py-3 font-medium">Primeiro registro</th>
                <th class="px-4 py-3 font-medium">Janelas</th>
                <th class="px-4 py-3 font-medium">Janelas com indícios</th>
                <th class="px-4 py-3 font-medium">Padrão identificado</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
              <tr v-for="(execution, index) in filteredExecutions" :key="execution.execution_id" class="table-row">
                <td class="max-w-[260px] truncate px-4 py-3 font-mono text-xs text-sky-300" >
                  Lote {{ index + 1 }}
                </td>
                <td class="px-4 py-3 text-slate-400">{{ formatDateTime(execution.first_seen_at) }}</td>
                <td class="px-4 py-3 text-slate-300">{{ execution.total_windows ?? 0 }}</td>
                <td class="px-4 py-3 text-slate-300">{{ execution.total_anomalies ?? 0 }}</td>
                <td class="px-4 py-3 text-slate-300">
                  {{ firstDistributionLabel(execution.attack_type_distribution) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <template v-else>
      <LoadingState v-if="loading.analyses" />
      <ErrorState v-else-if="errors.analyses" :message="errors.analyses" />
      <div v-else class="panel overflow-hidden">
        <div class="border-b border-slate-800 px-4 py-3">
          <div class="flex items-center justify-between gap-3">
            <div>
              <h2 class="text-base font-semibold text-white">Análises realizadas</h2>
              <p class="mt-1 text-sm text-slate-500">
                Resultados persistidos do upload/replay de logs pfSense. Selecione uma análise para consultar suas janelas.
              </p>
            </div>
            <p v-if="analysesMeta" class="text-sm text-slate-500">
              {{ filteredAnalyses.length }} exibidas de {{ analysesMeta.total }}
            </p>
          </div>
        </div>
        <p v-if="filteredAnalyses.length === 0" class="p-4 text-sm text-slate-400">
          Não existem análises disponíveis.
        </p>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-800 text-sm">
            <thead class="bg-surface-850 text-left text-xs uppercase text-slate-500">
              <tr>
                <th class="px-4 py-3 font-medium">Data e hora</th>
                <th class="px-4 py-3 font-medium">Origem</th>
                <th class="px-4 py-3 font-medium">Janelas</th>
                <th class="px-4 py-3 font-medium">Resultado</th>
                <th class="px-4 py-3 text-right font-medium">Ação</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
              <tr v-for="analysis in filteredAnalyses" :key="analysis.analysis_id">
                <td class="px-4 py-3 text-slate-400">{{ formatDateTime(analysis.created_at) }}</td>
                <td class="px-4 py-3 text-slate-300">Upload/replay pfSense</td>
                <td class="px-4 py-3 text-slate-300">{{ analysis.total_windows }}</td>
                <td class="px-4 py-3"><StatusBadge :value="analysis.final_status" :rotulo="formatarResultadoAnalise(analysis.final_status)" /></td>
                <td class="px-4 py-3 text-right">
                  <RouterLink class="btn btn-primary" :to="`/analyses/${analysis.analysis_id}`">Ver análise</RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import ErrorState from '@/components/ui/ErrorState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { useGlobalSearch } from '@/composables/useGlobalSearch'
import {
  getAnalyses,
  getHistoryAlerts,
  getHistoryExecutions,
  getHistorySummary,
  getHistoryWindows,
} from '@/services/api'
import type {
  AnalysisItem,
  HistoryExecution,
  HistorySummary,
  PaginationMeta,
  WindowFilters,
  WindowItem,
} from '@/types/api'
import {
  buildHtmlTable,
  dateStamp,
  escapeHtml,
  exportPdfDocument,
  exportJson,
  type ExportColumn,
} from '@/utils/exporters'
import {
  analysisSearchText,
  executionSearchText,
  filterBySearch,
  normalizeSearchText,
  windowSearchText,
} from '@/utils/search'
import {
  formatDateTime,
  formatRiskLevel,
} from '@/utils/formatters'
import { formatarClassificacao as formatAttackType, formatarClassificacao as formatFinalLabel, formatarMotivo } from '@/utils/apresentacaoSeguranca'

type TabKey = 'summary' | 'windows' | 'alerts' | 'executions' | 'analyses'
type DistributionKind = 'attack' | 'risk' | 'plain'

const tabs: { key: TabKey; label: string }[] = [
  { key: 'analyses', label: 'Análises realizadas' },
  { key: 'executions', label: 'Lotes processados' },
  { key: 'windows', label: 'Janelas' },
  { key: 'alerts', label: 'Alertas' },
  { key: 'summary', label: 'Resumo' },
]

const attackTypeFilterOptions = [
  'normal',
  'port_scan',
  'brute_force',
  'syn_flood',
  'ssh_suspicious',
  'unknown_anomaly',
]

const activeTab = ref<TabKey>('analyses')
const router = useRouter()
const { trimmedSearch } = useGlobalSearch()

const summary = ref<HistorySummary | null>(null)
const windows = ref<WindowItem[]>([])
const alerts = ref<WindowItem[]>([])
const executions = ref<HistoryExecution[]>([])
const analyses = ref<AnalysisItem[]>([])
const exportFeedback = ref('')

const windowsMeta = ref<PaginationMeta | null>(null)
const alertsMeta = ref<PaginationMeta | null>(null)
const executionsMeta = ref<PaginationMeta | null>(null)
const analysesMeta = ref<PaginationMeta | null>(null)

const loading = reactive({
  summary: true,
  windows: true,
  alerts: true,
  executions: true,
  analyses: true,
})

const errors = reactive({
  summary: '',
  windows: '',
  alerts: '',
  executions: '',
  analyses: '',
})

const filters = reactive({
  final_label: '',
  attack_type: '',
  risk_level: '',
  ai_support: '',
  date_from: '',
  date_to: '',
  src_ip: '',
  dst_ip: '',
  dst_port: '',
  protocol: '',
  action: '',
  only_anomalies: false,
})

const usesWindowFilters = computed(
  () => activeTab.value === 'windows' || activeTab.value === 'alerts',
)

const activeWindowRows = computed<WindowItem[]>(() => {
  const rows = activeTab.value === 'alerts' ? alerts.value : windows.value
  return filterBySearch(
    rows.filter(matchesLocalWindowFilters),
    trimmedSearch.value,
    windowSearchText,
  )
})
const activeWindowMeta = computed(() =>
  activeTab.value === 'alerts' ? alertsMeta.value : windowsMeta.value,
)
const activeWindowLoading = computed(() =>
  activeTab.value === 'alerts' ? loading.alerts : loading.windows,
)
const activeWindowError = computed(() =>
  activeTab.value === 'alerts' ? errors.alerts : errors.windows,
)
const filteredExecutions = computed(() =>
  filterBySearch(executions.value, trimmedSearch.value, executionSearchText),
)
const filteredAnalyses = computed(() =>
  filterBySearch(analyses.value, trimmedSearch.value, analysisSearchText),
)

/** Reúne os filtros atuais nos parâmetros aceitos pelo serviço de histórico. */
function currentFilters(): WindowFilters {
  const finalLabel =
    filters.only_anomalies && !filters.final_label
      ? 'anomaly'
      : filters.final_label || undefined

  return {
    final_label: finalLabel,
    attack_type: filters.attack_type || undefined,
    risk_level: filters.risk_level || undefined,
    ai_support:
      filters.ai_support === ''
        ? null
        : filters.ai_support === 'true',
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
    src_ip: filters.src_ip || undefined,
    dst_ip: filters.dst_ip || undefined,
    dst_port: filters.dst_port || undefined,
    protocol: filters.protocol || undefined,
    action: filters.action || undefined,
    only_anomalies: filters.only_anomalies,
  }
}

/** Aplica os filtros locais à janela sem alterar seu resultado. */
function matchesLocalWindowFilters(row: WindowItem): boolean {
  if (filters.only_anomalies && row.final_label !== 'anomaly') {
    return false
  }

  return (
    textIncludes(row.src_ip, filters.src_ip)
    && textIncludes(row.dst_ip, filters.dst_ip)
    && textIncludes(row.dst_port, filters.dst_port)
    && textIncludes(row.protocol, filters.protocol)
    && textIncludes(row.action, filters.action)
    && dateInRange(row.window_start)
  )
}

/** Compara textos de forma padronizada para os filtros da tela. */
function textIncludes(value: unknown, query: string): boolean {
  if (!query.trim()) {
    return true
  }
  return normalizeSearchText(value).includes(normalizeSearchText(query))
}

/** Verifica se a data do registro está dentro do período escolhido. */
function dateInRange(value?: string | null): boolean {
  if (!filters.date_from && !filters.date_to) {
    return true
  }
  const timestamp = value ? new Date(value).getTime() : Number.NaN
  if (Number.isNaN(timestamp)) {
    return false
  }
  if (filters.date_from && timestamp < new Date(filters.date_from).getTime()) {
    return false
  }
  if (filters.date_to && timestamp > new Date(filters.date_to).getTime()) {
    return false
  }
  return true
}

const windowExportColumns: ExportColumn<WindowItem>[] = [
  { header: 'Início da janela', value: (item) => item.window_start },
  { header: 'Fim da janela', value: (item) => item.window_end },
  { header: 'Classificação', value: (item) => formatFinalLabel(item.final_label) },
  { header: 'Padrão identificado', value: (item) => formatAttackType(item.attack_type) },
  { header: 'Risco', value: (item) => formatRiskLevel(item.risk_level) },
  { header: 'Base da análise', value: (item) => formatarMotivo(item) },
  { header: 'IP de origem', value: (item) => item.src_ip },
  { header: 'IP de destino', value: (item) => item.dst_ip },
  { header: 'Porta', value: (item) => item.dst_port },
  { header: 'Protocolo', value: (item) => item.protocol },
  { header: 'Ação', value: (item) => item.action },
]

const executionExportColumns: ExportColumn<HistoryExecution>[] = [
  { header: 'Primeiro registro', value: (item) => item.first_seen_at },
  { header: 'Último registro', value: (item) => item.last_seen_at },
  { header: 'Janelas', value: (item) => item.total_windows },
  { header: 'Anomalias', value: (item) => item.total_anomalies },
]


/** Monta o rótulo de uma distribuição recebida do servidor. */
function distributionLabel(label: string, kind: DistributionKind): string {
  if (kind === 'attack') {
    return formatAttackType(label)
  }
  if (kind === 'risk') {
    return formatRiskLevel(label)
  }
  return label
}

/** Obtém o rótulo disponível para o resumo da distribuição. */
function firstDistributionLabel(distribution?: Record<string, number>): string {
  const [first] = Object.entries(distribution ?? {})
  return first ? `${formatAttackType(first[0])} (${first[1]})` : '-'
}

/** Traduz o resultado geral da análise para o texto da listagem. */
function formatarResultadoAnalise(value?: string | null): string {
  const normalized = String(value ?? '').trim().toLowerCase()
  if (normalized === 'normal' || normalized === 'benign' || normalized === 'benigno') {
    return 'Sem indícios relevantes'
  }
  if (normalized === 'anomaly' || normalized === 'anomalia') {
    return 'Com indícios relevantes'
  }
  if (normalized === 'unknown_anomaly') {
    return 'Atividade incomum'
  }
  return formatFinalLabel(value)
}


/** Abre o detalhe da janela selecionada pela rota existente. */
function openWindow(id: number): void {
  router.push(`/windows/${id}`)
}

/** Consulta o resumo do histórico e atualiza os estados de espera e erro. */
async function loadSummary(): Promise<void> {
  loading.summary = true
  errors.summary = ''
  try {
    summary.value = await getHistorySummary()
  } catch {
    errors.summary = 'Não foi possível carregar o histórico.'
  } finally {
    loading.summary = false
  }
}

/** Consulta as janelas complementares conforme os filtros e a paginação. */
async function loadWindows(): Promise<void> {
  loading.windows = true
  errors.windows = ''
  try {
    const response = await getHistoryWindows(500, 0, currentFilters())
    windows.value = response.windows
    windowsMeta.value = response.meta
  } catch {
    errors.windows = 'Não foi possível carregar o histórico.'
  } finally {
    loading.windows = false
  }
}

/** Consulta os alertas complementares conforme os filtros e a paginação. */
async function loadAlerts(): Promise<void> {
  loading.alerts = true
  errors.alerts = ''
  try {
    const response = await getHistoryAlerts(500, 0, currentFilters())
    alerts.value = response.alerts
    alertsMeta.value = response.meta
  } catch {
    errors.alerts = 'Não foi possível carregar o histórico.'
  } finally {
    loading.alerts = false
  }
}

/** Consulta as execuções complementares conforme os filtros e a paginação. */
async function loadExecutions(): Promise<void> {
  loading.executions = true
  errors.executions = ''
  try {
    const response = await getHistoryExecutions(500, 0)
    executions.value = response.executions
    executionsMeta.value = response.meta
  } catch {
    errors.executions = 'Não foi possível carregar o histórico.'
  } finally {
    loading.executions = false
  }
}

/** Consulta as análises importadas já processadas. */
async function loadAnalyses(): Promise<void> {
  loading.analyses = true
  errors.analyses = ''
  try {
    const response = await getAnalyses(500, 0)
    analyses.value = response.analyses
    analysesMeta.value = response.meta
  } catch {
    errors.analyses = 'Não foi possível carregar o histórico.'
  } finally {
    loading.analyses = false
  }
}

/** Recarrega as consultas do histórico com os filtros atuais. */
async function reloadFiltered(): Promise<void> {
  await Promise.all([loadSummary(), loadWindows(), loadAlerts(), loadExecutions()])
}

/** Limpa os filtros e recarrega os dados correspondentes. */
async function clearFilters(): Promise<void> {
  filters.final_label = ''
  filters.attack_type = ''
  filters.risk_level = ''
  filters.ai_support = ''
  filters.date_from = ''
  filters.date_to = ''
  filters.src_ip = ''
  filters.dst_ip = ''
  filters.dst_port = ''
  filters.protocol = ''
  filters.action = ''
  filters.only_anomalies = false
  await reloadFiltered()
}

/** Executa a exportação e apresenta sucesso ou erro sem alterar o histórico. */
async function executarExportacao(acao: () => Promise<void>): Promise<void> {
  try { await acao() } catch { exportFeedback.value = 'Não foi possível carregar os dados para exportação.' }
}

/** Exporta os dados disponíveis das análises realizadas. */
function exportarAnalises(): void {
  showExportFeedback(exportPdfDocument('Análises importadas do Sinalyx', buildHistoryPdfHtml(
    'Análises importadas', 'Registros exibidos do upload/replay de logs pfSense.', filteredAnalyses.value,
    [
      { header: 'Data/hora', value: (item: AnalysisItem) => formatDateTime(item.created_at) },
      { header: 'Origem', value: () => 'Upload/replay pfSense' },
      { header: 'Janelas', value: (item: AnalysisItem) => item.total_windows },
      { header: 'Padrão identificado', value: (item: AnalysisItem) => formatAttackType(item.predominant_attack_type) },
      { header: 'Risco', value: (item: AnalysisItem) => formatRiskLevel(item.predominant_risk_level) },
    ],
  )))
}

/** Apresenta o retorno da exportação ao usuário. */
function showExportFeedback(success: boolean, type: 'pdf' | 'json' = 'pdf'): void {
  exportFeedback.value = success
    ? type === 'pdf'
      ? 'Relatório aberto para impressão ou salvamento em PDF.'
      : 'Arquivo JSON exportado com sucesso.'
    : 'Não há dados para exportar.'
}

/** Monta o documento de histórico usando somente os dados já disponíveis. */
function buildHistoryPdfHtml<TItem>(
  title: string,
  description: string,
  rows: TItem[],
  columns: ExportColumn<TItem>[],
): string {
  if (rows.length === 0) {
    return ''
  }

  return `
    <section class="section">
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(description)}</p>
      ${buildHtmlTable(rows, columns)}
    </section>
  `
}

/** Abre a exportação do histórico filtrado para impressão ou PDF. */
async function exportFilteredHistoryPdf(): Promise<void> {
  const response = await getHistoryWindows(500, 0, currentFilters())
  const rows = filterBySearch(
    response.windows.filter(matchesLocalWindowFilters),
    trimmedSearch.value,
    windowSearchText,
  )
  showExportFeedback(
    exportPdfDocument(
      `Histórico filtrado do Sinalyx - ${dateStamp()}`,
      buildHistoryPdfHtml(
        'Janelas filtradas',
        'Dados filtrados pela busca e pelos filtros aplicados no Histórico.',
        rows,
        windowExportColumns,
      ),
    ),
  )
}

/** Abre a exportação dos registros carregados para impressão ou PDF. */
async function exportAllHistoryPdf(): Promise<void> {
  const response = await getHistoryWindows(500, 0)
  showExportFeedback(
    exportPdfDocument(
      `Histórico completo do Sinalyx - ${dateStamp()}`,
      buildHistoryPdfHtml(
        'Janelas do histórico',
        'Até 500 janelas carregadas do histórico complementar do Sinalyx.',
        response.windows,
        windowExportColumns,
      ),
    ),
  )
}

/** Abre a exportação dos alertas disponíveis para impressão ou PDF. */
async function exportAlertsPdf(): Promise<void> {
  const response = await getHistoryAlerts(500, 0, currentFilters())
  const rows = filterBySearch(
    response.alerts.filter(matchesLocalWindowFilters),
    trimmedSearch.value,
    windowSearchText,
  )
  showExportFeedback(
    exportPdfDocument(
      `Alertas do Sinalyx - ${dateStamp()}`,
      buildHistoryPdfHtml(
        'Alertas',
        'Somente janelas classificadas como anomalia.',
        rows,
        windowExportColumns,
      ),
    ),
  )
}

/** Abre a exportação das execuções disponíveis para impressão ou PDF. */
async function exportExecutionsPdf(): Promise<void> {
  const response = await getHistoryExecutions(500, 0)
  const rows = filterBySearch(
    response.executions,
    trimmedSearch.value,
    executionSearchText,
  )
  showExportFeedback(
    exportPdfDocument(
      `Lotes processados do Sinalyx - ${dateStamp()}`,
      buildHistoryPdfHtml(
        'Lotes processados',
        'Resumo dos lotes registrados no histórico.',
        rows,
        executionExportColumns,
      ),
    ),
  )
}

/** Exporta o resumo recebido em JSON. */
async function exportSummaryJson(): Promise<void> {
  const payload = summary.value ?? (await getHistorySummary())
  showExportFeedback(
    exportJson(`sinalyx_relatorio_resumo_${dateStamp()}.json`, {
      escopo: 'Totais persistidos; histórico live complementar experimental/congelado',
      analises: { total: payload.analyses?.total_analyses, janelas: payload.analyses?.total_results },
      complementar: {
        janelas: payload.live?.total_windows, alertas: payload.live?.total_alerts, execucoes: payload.live?.total_executions,
        classificacoes: payload.live?.final_label_distribution, padroes: payload.live?.attack_type_distribution, riscos: payload.live?.risk_level_distribution,
      },
    }),
    'json',
  )
}

const SummaryBox = defineComponent({
  props: {
    label: {
      type: String,
      required: true,
    },
    value: {
      type: Number,
      default: 0,
    },
  },
  setup(props) {
    return () =>
      h('div', { class: 'panel p-4' }, [
        h('p', { class: 'text-xs font-medium text-slate-500' }, props.label),
        h('p', { class: 'mt-2 text-2xl font-semibold text-white' }, String(props.value ?? 0)),
      ])
  },
})

const DistributionBox = defineComponent({
  props: {
    title: {
      type: String,
      required: true,
    },
    items: {
      type: Object,
      default: () => ({}),
    },
    kind: {
      type: String,
      default: 'plain',
    },
  },
  setup(props) {
    return () =>
      h('div', { class: 'panel p-4' }, [
        h('h2', { class: 'text-sm font-semibold text-white' }, props.title),
        h(
          'div',
          { class: 'mt-4 space-y-2' },
          Object.entries(props.items as Record<string, number>).map(([label, value]) =>
            h('div', { class: 'flex items-center justify-between gap-3 text-sm' }, [
              h('span', { class: 'text-slate-300' }, distributionLabel(label, props.kind as DistributionKind)),
              h('span', { class: 'font-medium text-white' }, String(value)),
            ]),
          ),
        ),
      ])
  },
})

onMounted(async () => {
  await Promise.all([
    loadSummary(),
    loadWindows(),
    loadAlerts(),
    loadExecutions(),
    loadAnalyses(),
  ])
})
</script>
