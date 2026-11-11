<!-- Consulta de disponibilidade e estados operacionais informados pelo servidor. -->
<template>
  <section class="space-y-5" qa-id="page-system" data-testid="page-system" data-qa-page="system">
    <PageHeader
      eyebrow="Ambiente"
      title="Status do sistema"
      description="Visão administrativa da disponibilidade dos principais serviços do Sinalyx. Informações internas sensíveis não são exibidas nesta tela."
    />

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />

    <template v-else-if="status">
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard qa-id="system-card-api" data-testid="system-card-api" label="API" :value="healthLabel" :icon="ServerCog" icon-class="border-sky-400/30 bg-sky-400/10 text-sky-200" />
        <StatCard qa-id="system-card-database" data-testid="system-card-database" label="Banco de dados" :value="databaseLabel" :icon="Database" icon-class="border-emerald-400/30 bg-emerald-400/10 text-emerald-200" />
        <StatCard qa-id="system-card-parser" data-testid="system-card-parser" label="Processamento de logs" :value="parserLabel" :icon="FileSearch" icon-class="border-cyan-400/30 bg-cyan-400/10 text-cyan-200" />
        <StatCard qa-id="system-card-collector" data-testid="system-card-collector" label="Integração contínua" value="Não habilitada" :icon="RadioReceiver" icon-class="border-amber-400/30 bg-amber-400/10 text-amber-200" />
      </div>

      <div class="grid gap-4 xl:grid-cols-2">
        <section class="panel p-5" qa-id="system-parser-runtime" data-testid="system-parser-runtime">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="muted-label">Processamento</p>
              <h2 class="mt-1 text-base font-semibold text-white">Leitura de logs pfSense</h2>
              <p class="mt-2 text-sm leading-6 text-slate-500">Resumo seguro da última execução registrada pelo sistema.</p>
            </div>
            <StatusBadge :value="parserLabel" />
          </div>

          <div v-if="!status.parser.ok" class="mt-5 rounded-xl border border-slate-700/80 bg-slate-950/25 p-4">
            <p class="text-sm font-medium text-slate-200">Status não disponível</p>
            <p class="mt-1 text-sm leading-6 text-slate-500">Não foi possível obter uma atualização recente do processamento.</p>
          </div>
          <dl v-else class="mt-5 grid gap-3 sm:grid-cols-2">
            <InfoItem label="Última verificação" :value="safeDate(parserState.last_run_at)" />
            <InfoItem label="Linhas novas" :value="parserState.last_lines_new ?? undefined" />
            <InfoItem label="Janelas geradas" :value="parserState.last_windows_generated ?? undefined" />
            <InfoItem label="Eventos pendentes" :value="parserState.pending_events_count ?? undefined" />
            <InfoItem label="Arquivo disponível" :value="fileExistsLabel" />
            <InfoItem label="Volume processado" :value="formatBytes(parserState.current_file_size)" />
          </dl>
        </section>

        <section class="panel p-5" qa-id="system-collector-runtime" data-testid="system-collector-runtime">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="muted-label">Integração direta</p>
              <h2 class="mt-1 text-base font-semibold text-white">Coleta contínua do pfSense</h2>
            </div>
            <StatusBadge value="warning" rotulo="Não habilitada" />
          </div>
          <div class="mt-5 rounded-xl border border-amber-400/[0.15] bg-amber-400/[0.035] p-4">
            <p class="text-sm font-medium text-amber-100">Recurso fora do escopo operacional desta versão</p>
            <p class="mt-2 text-sm leading-6 text-slate-400">O fluxo oficial do TCC utiliza logs processados por upload/replay. A integração contínua direta permanece como evolução futura e não deve ser interpretada como coleta ativa.</p>
          </div>
          <div class="mt-4 grid gap-3 sm:grid-cols-2">
            <InfoItem label="Última consulta registrada" :value="safeDate(collectorState.last_fetch_at)" />
            <InfoItem label="Estado informado" :value="collectorStatusLabel" />
          </div>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { Database, FileSearch, RadioReceiver, ServerCog } from 'lucide-vue-next'

import ErrorState from '@/components/ui/ErrorState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { getSystemStatus } from '@/services/api'
import type { LiveRuntimeState, SystemStatus } from '@/types/api'
import { formatDateTime } from '@/utils/formatters'

const status = ref<SystemStatus | null>(null)
const loading = ref(true)
const error = ref('')
const parserState = computed<LiveRuntimeState>(() => status.value?.parser.data?.state ?? {})
const collectorState = computed<LiveRuntimeState>(() => status.value?.collector.data?.state ?? {})

const healthLabel = computed(() => status.value?.health.ok && status.value.health.data?.status === 'ok' ? 'Operacional' : 'Não disponível')
const databaseLabel = computed(() => status.value?.health.ok && status.value.health.data?.database.available ? 'Disponível' : 'Não disponível')
const parserLabel = computed(() => status.value?.parser.ok && parserState.value.last_run_status === 'success' ? 'Operacional' : status.value?.parser.ok ? 'Sem execução recente' : 'Não disponível')
const collectorStatusLabel = computed(() => {
  const value = String(collectorState.value.last_fetch_status ?? '').toLowerCase()
  if (value === 'success') return 'Execução registrada anteriormente'
  if (value === 'not_configured' || value === 'disabled') return 'Não configurada'
  return 'Sem execução recente'
})
const fileExistsLabel = computed(() => parserState.value.local_file_exists == null ? 'Não informado' : parserState.value.local_file_exists ? 'Sim' : 'Não')

/** Apresenta a data recebida ou indica que ela não foi informada. */
function safeDate(value?: string | null): string { return value ? formatDateTime(value) : 'Não informada' }
/** Apresenta o tamanho recebido em uma unidade legível. */
function formatBytes(value: unknown): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return 'Não informado'
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 / 1024).toFixed(2)} MB`
}

const InfoItem = defineComponent({
  props: { label: { type: String, required: true }, value: { type: [String, Number, Boolean], default: 'Não informado' } },
  setup(props) {
    return () => h('div', { class: 'rounded-xl border border-slate-800/80 bg-slate-950/[0.22] p-3.5' }, [
      h('dt', { class: 'text-xs font-medium text-slate-500' }, props.label),
      h('dd', { class: 'mt-1.5 text-wrap-safe text-sm text-slate-200' }, props.value == null || props.value === '' ? 'Não informado' : String(props.value)),
    ])
  },
})

onMounted(async () => {
  try { status.value = await getSystemStatus() }
  catch { error.value = 'Não foi possível carregar o status do sistema.' }
  finally { loading.value = false }
})
</script>
