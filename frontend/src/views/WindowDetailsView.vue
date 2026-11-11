<!-- Investigação de uma janela complementar; respostas antigas não podem trocar a janela atual. -->
<template>
  <section class="space-y-5" qa-id="page-window-details" data-testid="page-window-details" data-qa-page="window-details">
    <PageHeader eyebrow="Investigação" :title="investigationTitle" :description="investigationDescription">
      <template #actions>
        <button class="btn btn-primary" type="button" qa-id="window-details-export-pdf" data-testid="window-details-export-pdf" :disabled="!windowItem" @click="exportWindowPdf">Exportar PDF</button>
        <button class="btn btn-secondary" type="button" qa-id="window-details-export-json" data-testid="window-details-export-json" :disabled="!windowItem" @click="exportWindowJson">Exportar JSON</button>
        <RouterLink class="btn btn-secondary" to="/alerts" qa-id="window-details-back" data-testid="window-details-back">Voltar</RouterLink>
      </template>
    </PageHeader>
    <p v-if="exportFeedback" role="status" class="text-sm text-slate-300">{{ exportFeedback }}</p>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />

    <template v-else-if="windowItem">
      <section class="panel overflow-hidden border-cyan-400/[0.15] p-5 sm:p-6" aria-label="Decisão do Sinalyx" qa-id="window-details-executive-summary" data-testid="window-details-executive-summary">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 class="muted-label text-cyan-300/80">O que o Sinalyx identificou</h2>
            <p class="mt-2 text-xl font-semibold tracking-tight text-white">{{ formatAttackType(windowItem.attack_type) }}</p>
            <p class="mt-3 max-w-4xl text-sm leading-7 text-slate-300">{{ executiveInterpretation }}</p>
          </div>
          <div class="flex flex-wrap gap-2">
            <StatusBadge :value="windowItem.final_label" :rotulo="formatFinalLabel(windowItem.final_label)" />
            <StatusBadge :value="windowItem.risk_level" />
          </div>
        </div>
        <dl class="mt-4">
          <dt class="text-sm text-slate-400">Confiança informada</dt>
          <dd class="mt-1 text-sm tabular-nums text-slate-200" data-testid="window-confidence">{{ formatarConfianca(windowItem.confidence) }}</dd>
        </dl>
        <p class="mt-2 max-w-3xl text-xs leading-5 text-slate-400">Indicador de confiança informado pelo Sinalyx. Não representa necessariamente a probabilidade de um ataque.</p>
      </section>

      <section class="panel p-5 sm:p-6">
        <p class="muted-label">Motivo da classificação</p>
        <h2 class="mt-1 text-base font-semibold text-white">Por que o sistema apresentou este resultado?</h2>
        <p class="mt-3 max-w-4xl text-sm leading-7 text-slate-300">{{ decisionText }}</p>
        <p class="mt-2 max-w-4xl text-xs leading-5 text-slate-400">Justificativa apresentada a partir do resultado registrado. Os valores de tráfego, isoladamente, não explicam a decisão.</p>
      </section>

      <ComponentContributionsPanel :contribuicoes="windowItem.component_contributions" />

      <section class="panel p-5 sm:p-6">
        <p class="muted-label">Contexto da janela</p>
        <h2 class="mt-1 text-base font-semibold text-white">Dados principais</h2>
        <div class="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <InfoItem label="Origem" :value="headerSource" />
          <InfoItem label="Destino" :value="safeNetworkValue(windowItem.dst_ip)" />
          <InfoItem label="Início da janela" :value="formatDateTime(windowItem.window_start)" />
          <InfoItem label="Duração" :value="durationLabel" />
          <InfoItem label="Protocolo" :value="windowItem.protocol ?? undefined" />
          <InfoItem label="Ação registrada no firewall" :value="windowItem.action ?? undefined" />
        </div>
      </section>

      <section class="panel overflow-hidden" aria-label="Valores observados">
        <div class="border-b border-slate-800/80 px-5 py-4">
          <p class="muted-label">Características analisadas</p>
          <h2 class="mt-1 text-sm font-semibold text-white">O que foi observado no tráfego</h2>
          <p class="mt-1 text-xs leading-5 text-slate-400">Valores recebidos entre as 13 características oficiais. Esta tela não avalia se são altos ou baixos e não recalcula esses indicadores.</p>
        </div>
        <div class="responsive-table">
          <table class="min-w-full divide-y divide-slate-800/80 text-sm">
            <thead class="bg-slate-950/20 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-600">
              <tr><th class="px-5 py-3">Característica</th><th class="px-5 py-3 text-right">Valor</th></tr>
            </thead>
            <tbody class="divide-y divide-slate-800/80">
              <tr v-for="[key, value] in featureEntries" :key="key" class="table-row">
                <td class="px-5 py-3.5 text-slate-400">{{ friendlyFeatureLabel(key) }}</td>
                <td class="px-5 py-3.5 text-right font-mono text-slate-200" :data-testid="`observed-${key}`">{{ value == null ? 'Não informado' : displayValue(value) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="featureEntries.length === 0" class="px-5 py-4 text-sm text-slate-500">As características oficiais não estão disponíveis neste registro.</p>
      </section>

      <ConsultaAmeacas :janela="windowItem" />
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onBeforeUnmount, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import ComponentContributionsPanel from '@/components/ui/ComponentContributionsPanel.vue'
import ConsultaAmeacas from '@/components/ui/ConsultaAmeacas.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { getWindowById } from '@/services/api'
import type { WindowItem } from '@/types/api'
import { buildDefinitionTable, buildHtmlTable, dateStamp, escapeHtml, exportJson, exportPdfDocument, type ExportColumn, type DefinitionField } from '@/utils/exporters'
import { formatarConfianca, formatDateTime, formatRiskLevel, formatTechnicalLabel } from '@/utils/formatters'
import { formatarClassificacao as formatAttackType, formatarClassificacao as formatFinalLabel, formatarMotivo } from '@/utils/apresentacaoSeguranca'

const props = defineProps<{ id: string }>()
const windowItem = ref<WindowItem | null>(null)
const loading = ref(true)
const error = ref('')
const exportFeedback = ref('')
let geracaoJanela = 0

const OFFICIAL_FEATURES = [
  'connections', 'bytes', 'packets', 'packet_size', 'ports',
  'bytes_per_packet', 'bytes_per_connection', 'packets_per_connection',
  'log1p_connections', 'log1p_bytes', 'log1p_packets', 'log1p_packet_size', 'log1p_ports',
] as const
const FRIENDLY_FEATURES: Record<string, string> = {
  connections: 'Registros de tráfego', bytes: 'Volume de dados (bytes)', packets: 'Pacotes registrados', packet_size: 'Tamanho médio do pacote', ports: 'Portas de destino distintas',
  bytes_per_packet: 'Dados por pacote', bytes_per_connection: 'Dados por registro', packets_per_connection: 'Pacotes por registro',
  log1p_connections: 'Registros em escala logarítmica', log1p_bytes: 'Volume de dados em escala logarítmica', log1p_packets: 'Pacotes em escala logarítmica',
  log1p_packet_size: 'Tamanho do pacote em escala logarítmica', log1p_ports: 'Portas em escala logarítmica',
}

const investigationTitle = computed(() => windowItem.value?.final_label === 'anomaly' ? 'Detalhes do alerta' : 'Detalhes da janela')
const investigationDescription = computed(() => windowItem.value
  ? `${formatAttackType(windowItem.value.attack_type)} • Risco ${formatRiskLevel(windowItem.value.risk_level).toLowerCase()} • ${formatDateTime(windowItem.value.window_start)}`
  : 'Resumo interpretável da janela analisada pelo Sinalyx.')
const headerSource = computed(() => safeNetworkValue(windowItem.value?.src_ip ?? (windowItem.value?.metadata?.src_ip as string | undefined)))
const durationLabel = computed(() => {
  const start = parseDate(windowItem.value?.window_start)
  const end = parseDate(windowItem.value?.window_end)
  if (!start || !end) return 'Não informada'
  return `${Math.max(1, Math.round((end.getTime() - start.getTime()) / 1000))}s`
})
const decisionText = computed(() => formatarMotivo(windowItem.value ?? {}))
const executiveInterpretation = computed(() => {
  if (!windowItem.value) return 'A janela está disponível para auditoria técnica.'
  if (windowItem.value.final_label === 'anomaly') return `O Sinalyx encontrou indícios compatíveis com ${formatAttackType(windowItem.value.attack_type)}. Consulte o motivo e as características abaixo para apoiar a investigação.`
  return `O resultado registrado foi ${formatFinalLabel(windowItem.value.final_label).toLowerCase()}. O registro permanece disponível para consulta e auditoria.`
})
const featureEntries = computed(() => OFFICIAL_FEATURES.flatMap((key) => {
  const features = windowItem.value?.features ?? {}
  return Object.prototype.hasOwnProperty.call(features, key) ? [[key, features[key]] as [string, unknown]] : []
}))
const pdfFeatureColumns: ExportColumn<[string, unknown]>[] = [
  { header: 'Característica', value: ([key]) => friendlyFeatureLabel(key) },
  { header: 'Valor', value: ([, value]) => displayValue(value) },
]

/** Interpreta a data recebida apenas para apresentação do detalhe. */
function parseDate(value?: string | null): Date | null { if (!value) return null; const date = new Date(value); return Number.isNaN(date.getTime()) ? null : date }
/** Prepara o campo de rede recebido para apresentação sem criar um valor substituto. */
function safeNetworkValue(value?: string | null): string { return value?.trim() || 'Não informado' }
/** Consulta o nome legível da característica numérica. */
function friendlyFeatureLabel(key: string): string { return FRIENDLY_FEATURES[key] ?? formatTechnicalLabel(key) }
/** Formata o valor recebido para leitura, preservando seu significado. */
function displayValue(value: unknown): string {
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(4)
  if (typeof value === 'boolean') return value ? 'Sim' : 'Não'
  if (value == null) return '-'
  return typeof value === 'object' ? JSON.stringify(value) : String(value)
}
/** Seleciona os campos da janela que serão apresentados na exportação. */
function buildSafeWindowRecord(item: WindowItem | null): Record<string, unknown> {
  if (!item) return {}
  return {
    id: item.id,
    window_id: item.window_id ?? null,
    created_at: item.created_at ?? null,
    window_start: item.window_start ?? null,
    window_end: item.window_end ?? null,
    final_label: item.final_label ?? null,
    attack_type: item.attack_type ?? null,
    risk_level: item.risk_level ?? null,
    confidence: item.confidence ?? null,
    decision_reason: formatarMotivo(item),
    src_ip: item.src_ip ?? null,
    dst_ip: item.dst_ip ?? null,
    dst_port: item.dst_port ?? null,
    protocol: item.protocol ?? null,
    action: item.action ?? null,
    features: Object.fromEntries(featureEntries.value),
    component_contributions: item.component_contributions ?? null,
  }
}
/** Monta o documento de investigação com os dados registrados da janela. */
function buildWindowPdfHtml(item: WindowItem): string {
  const summaryFields: DefinitionField[] = [
    { label: 'Janela', value: item.window_id ?? item.id }, { label: 'Origem', value: headerSource.value }, { label: 'Destino', value: item.dst_ip },
    { label: 'Porta', value: item.dst_port }, { label: 'Protocolo', value: item.protocol }, { label: 'Ação do firewall', value: item.action },
    { label: 'Início', value: formatDateTime(item.window_start) }, { label: 'Fim', value: formatDateTime(item.window_end) }, { label: 'Duração', value: durationLabel.value },
  ]
  const decisionFields: DefinitionField[] = [
    { label: 'Resultado', value: formatFinalLabel(item.final_label) }, { label: 'Padrão identificado', value: formatAttackType(item.attack_type) },
    { label: 'Risco', value: formatRiskLevel(item.risk_level) }, { label: 'Motivo da classificação', value: formatarMotivo(item) },
  ]
  return `<section class="section"><h2>Resumo da ocorrência</h2>${buildDefinitionTable(summaryFields)}</section>
    <section class="section"><h2>Resultado da análise</h2>${buildDefinitionTable(decisionFields)}</section>
    <section class="section"><h2>Características analisadas</h2>${buildHtmlTable(featureEntries.value, pdfFeatureColumns)}</section>
    <section class="section"><h2>Registro técnico seguro</h2><pre>${escapeHtml(JSON.stringify(buildSafeWindowRecord(item), null, 2))}</pre></section>`
}
/** Abre a investigação para impressão ou gravação em PDF. */
function exportWindowPdf(): void {
  if (!windowItem.value) { exportFeedback.value = 'Não há dados para exportar.'; return }
  const success = exportPdfDocument(`Ocorrência Sinalyx - Janela ${windowItem.value.id} - ${dateStamp()}`, buildWindowPdfHtml(windowItem.value))
  exportFeedback.value = success ? 'Ocorrência aberta para impressão ou salvamento em PDF.' : 'Não foi possível abrir a exportação em PDF.'
}
/** Disponibiliza os dados permitidos da janela em JSON. */
function exportWindowJson(): void {
  if (!windowItem.value) { exportFeedback.value = 'Não há dados para exportar.'; return }
  const success = exportJson(`sinalyx_ocorrencia_janela_${windowItem.value.id}_${dateStamp()}.json`, buildSafeWindowRecord(windowItem.value))
  exportFeedback.value = success ? 'Arquivo JSON exportado com sucesso.' : 'Não há dados para exportar.'
}

const InfoItem = defineComponent({
  props: { label: { type: String, required: true }, value: { type: [String, Number, Boolean], default: 'Não informado' } },
  setup(itemProps) { return () => h('div', { class: 'rounded-xl border border-slate-800/80 bg-slate-950/[0.22] p-3.5' }, [
    h('p', { class: 'text-xs font-medium text-slate-500' }, itemProps.label),
    h('p', { class: 'mt-1.5 text-wrap-safe text-sm text-slate-200' }, displayValue(itemProps.value)),
  ]) },
})

/** Carrega a janela atual e ignora resposta, erro ou fim de espera de solicitações antigas. */
async function loadWindow(id: string): Promise<void> {
  const geracao = ++geracaoJanela
  /** Confere se a resposta ainda pertence à solicitação e ao contexto atuais da tela. */
  const atual = () => geracao === geracaoJanela && props.id === id
  loading.value = true
  error.value = ''
  windowItem.value = null
  try {
    const response = await getWindowById(id)
    if (!atual()) return
    if (!response) { error.value = 'A janela solicitada não foi encontrada.'; return }
    windowItem.value = response
  } catch {
    if (atual()) error.value = 'Não foi possível carregar os detalhes desta janela.'
  } finally {
    if (atual()) loading.value = false
  }
}

watch(() => props.id, (id) => { void loadWindow(id) }, { immediate: true })
onBeforeUnmount(() => {
  // Invalida também catch/finally de chamadas ainda pendentes.
  geracaoJanela += 1
})
</script>
