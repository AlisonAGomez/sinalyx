<!-- Resumo das análises e validação histórica, apresentados com seus contextos separados. -->
<template>
  <section class="mx-auto w-full max-w-[1440px] space-y-5" data-testid="page-reports" qa-id="page-reports" data-qa-page="reports">
    <PageHeader eyebrow="Evidência e síntese" title="Relatórios do Sinalyx" description="Síntese das análises registradas e das evidências históricas usadas na avaliação acadêmica do Sinalyx.">
      <template #actions>
        <button class="btn btn-primary" :disabled="loading" data-testid="reports-export-pdf" @click="exportReportPdf">Exportar PDF</button>
        <button class="btn btn-secondary" :disabled="loading" data-testid="reports-export-json" @click="exportReportJson">Exportar JSON</button>
      </template>
    </PageHeader>
    <p v-if="feedback" role="status" class="text-sm text-slate-300">{{ feedback }}</p>
    <article class="space-y-5" data-testid="reports-preview">
      <section class="panel p-5">
        <h2 class="text-lg font-semibold text-white">Resumo das análises realizadas</h2>
        <p class="mt-2 text-sm text-slate-400">Consulta ao histórico persistido em {{ generatedAt }}. Estes totais não são métricas de detecção.</p>
        <LoadingState v-if="loading" />
        <ErrorState v-else-if="error" :message="error" />
        <dl v-else class="mt-5 grid gap-5 sm:grid-cols-2">
          <div><dt class="text-sm text-slate-400">Análises importadas · upload/replay</dt><dd class="mt-1 text-2xl text-white">{{ summary?.analyses?.total_analyses ?? 'Não disponível' }}</dd></div>
          <div><dt class="text-sm text-slate-400">Resultados por janela dessas análises</dt><dd class="mt-1 text-2xl text-white">{{ summary?.analyses?.total_results ?? 'Não disponível' }}</dd></div>
        </dl>
      </section>

      <section class="panel border-sky-400/20 p-5" data-testid="reports-historical-validation">
        <h2 class="text-xs font-semibold uppercase tracking-wide text-sky-200">RESULTADOS DA AVALIAÇÃO HISTÓRICA</h2>
        <p class="mt-2 text-sm text-slate-300">{{ evidencia.janelas }} janelas históricas · Ambiente de validação · unidade de avaliação: janela.</p>
        <p class="mt-2 text-xs leading-5 text-slate-400">Avaliação retrospectiva com dados também utilizados no desenvolvimento/configuração, sem holdout independente. Não é tempo real nem garantia de desempenho em produção.</p>
        <div class="mt-5 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          <div v-for="metrica in evidencia.metricas" :key="metrica.nome">
            <h3 class="text-sm text-slate-300">{{ metrica.nome }}</h3>
            <p class="mt-1 text-3xl font-semibold tabular-nums text-white">{{ percentual(metrica.valor) }}</p>
            <p class="mt-2 text-xs leading-5 text-slate-400">{{ metrica.descricao }}</p>
          </div>
        </div>
        <h3 class="mt-7 text-base font-semibold text-white">Matriz de confusão</h3>
        <div class="mt-3 overflow-x-auto">
          <table class="w-full text-left text-sm">
            <caption class="sr-only">Rótulo de referência nas linhas e classificação do pipeline nas colunas</caption>
            <thead><tr><th class="p-3">Referência / resultado</th><th class="p-3">Sem indícios</th><th class="p-3">Com indícios</th></tr></thead>
            <tbody class="text-slate-300">
              <tr class="border-t border-slate-800"><th class="p-3 font-normal">Negativo de referência</th><td class="p-3">TN {{ evidencia.matriz.tn }}</td><td class="p-3">FP {{ evidencia.matriz.fp }}</td></tr>
              <tr class="border-t border-slate-800"><th class="p-3 font-normal">Positivo de referência</th><td class="p-3">FN {{ evidencia.matriz.fn }}</td><td class="p-3">TP {{ evidencia.matriz.tp }}</td></tr>
            </tbody>
          </table>
        </div>
        <p class="mt-3 text-xs leading-5 text-slate-400">TN: negativos corretos · FP: falsos positivos · FN: falsos negativos · TP: positivos detectados.</p>
      </section>

      <section class="panel p-5" data-testid="reports-historical-contributions">
        <h2 class="text-lg font-semibold text-white">Contribuição dos componentes</h2>
        <p class="mt-2 text-sm text-slate-300">Participação relativa na influência das decisões analisadas.</p>
        <p class="mt-1 text-xs text-slate-400">Agregado histórico das {{ evidencia.janelas }} janelas; não substitui a contribuição de uma janela individual.</p>
        <ul class="mt-5 space-y-4">
          <li v-for="item in evidencia.contribuicoes" :key="item.nome">
            <div class="flex justify-between gap-3 text-sm text-slate-200"><span>{{ item.nome }}</span><span class="tabular-nums">{{ percentual(item.percentual / 100) }}</span></div>
            <p class="mt-1 text-xs leading-5 text-slate-400">{{ descricoesComponentes[item.nome] }}</p>
            <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-800" aria-hidden="true"><div class="h-full origin-left rounded-full bg-gradient-to-r from-sky-400 to-cyan-300" :style="{ width: `${item.percentual}%`, animation: 'bar-grow-x 520ms cubic-bezier(.2,.7,.2,1) both' }" /></div>
          </li>
        </ul>
        <p class="mt-4 text-xs leading-5 text-slate-400">Os percentuais representam influência relativa nas decisões analisadas, não precisão isolada dos componentes.</p>
        <p class="mt-4 text-xs text-slate-400">Fontes: análise por remoção/neutralização de componentes e metodologia de contribuição Shapley v1, reproduzidas em ambiente controlado de validação.</p>
      </section>

      <details v-if="!loading && !error" class="panel p-5">
        <summary class="focus-ring cursor-pointer text-sm font-semibold text-white">Histórico complementar e registros consultados</summary>
        <p class="mt-3 text-sm text-slate-400">Até 20 alertas e 20 janelas do histórico complementar são consultados nesta seção. Esse recorte não representa o conjunto histórico de 355 janelas usado na validação.</p>
        <div class="mt-4 grid gap-4 sm:grid-cols-3"><p class="text-sm text-slate-300">Janelas: {{ summary?.live?.total_windows ?? 'Não disponível' }}</p><p class="text-sm text-slate-300">Alertas: {{ summary?.live?.total_alerts ?? 'Não disponível' }}</p><p class="text-sm text-slate-300">Execuções: {{ summary?.live?.total_executions ?? 'Não disponível' }}</p></div>
        <div class="mt-5 grid gap-5 sm:grid-cols-2">
          <div><h3 class="font-semibold text-white">Distribuição por padrão</h3><p v-for="[label, total] in attackDistribution" :key="label" class="mt-2 text-sm text-slate-300">{{ label }}: {{ total }}</p></div>
          <div><h3 class="font-semibold text-white">Distribuição por risco</h3><p v-for="[label, total] in riskDistribution" :key="label" class="mt-2 text-sm text-slate-300">{{ label }}: {{ total }}</p></div>
        </div>
        <h3 class="mt-5 font-semibold text-white">Eventos para investigação</h3><ReportTable :rows="alerts" />
        <h3 class="mt-5 font-semibold text-white">Janelas consultadas</h3><ReportTable :rows="windows" />
        <p class="mt-4 text-xs text-slate-400">Consultas aos serviços: API {{ systemStatus.health.ok ? 'respondendo' : 'sem resposta' }}; parser {{ systemStatus.parser.ok ? 'respondendo' : 'sem resposta' }}; coletor {{ systemStatus.collector.ok ? 'respondendo' : 'sem resposta' }}. A disponibilidade dos serviços não significa que exista coleta contínua ativa.</p>
      </details>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { getHistoryAlerts, getHistorySummary, getHistoryWindows, getSystemStatus } from '@/services/api'
import type { AlertItem, HistorySummary, SystemStatus, WindowItem } from '@/types/api'
import { buildDefinitionTable, buildHtmlTable, dateStamp, escapeHtml, exportJson, exportPdfDocument, type ExportColumn } from '@/utils/exporters'
import { formatDateTime, formatRiskLevel } from '@/utils/formatters'
import { formatarClassificacao, formatarMotivo } from '@/utils/apresentacaoSeguranca'
import { validacaoHistorica as evidencia } from '@/utils/validacaoHistorica'

const descricoesComponentes = {
  Autoencoder: 'Detecta desvios em relação ao comportamento aprendido.',
  'Isolation Forest': 'Identifica estatisticamente observações incomuns.',
  'Regras de segurança': 'Adicionam contexto interpretável às decisões.',
} as const

const loading = ref(true)
const error = ref('')
const feedback = ref('')
const generatedAt = formatDateTime(new Date().toISOString())
const summary = ref<HistorySummary | null>(null)
const windows = ref<WindowItem[]>([])
const alerts = ref<AlertItem[]>([])
const systemStatus = ref<SystemStatus>({ health: { ok: false }, parser: { ok: false }, collector: { ok: false } })
/** Formata a proporção para apresentação; não calcula métricas de classificação. */
const percentual = (value: number) => new Intl.NumberFormat('pt-BR', { style: 'percent', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value)
const attackDistribution = computed(() => Object.entries(summary.value?.live?.attack_type_distribution ?? {}).map(([label, value]) => [formatarClassificacao(label), value] as const))
const riskDistribution = computed(() => Object.entries(summary.value?.live?.risk_level_distribution ?? {}).map(([label, value]) => [formatRiskLevel(label), value] as const))
const reportWindowColumns: ExportColumn<WindowItem>[] = [
  { header: 'Horário', value: row => formatDateTime(row.window_start) },
  { header: 'Evento', value: row => formatarClassificacao(row.attack_type) },
  { header: 'Risco', value: row => formatRiskLevel(row.risk_level) },
  { header: 'Motivo da classificação', value: row => formatarMotivo(row) },
]
// Exporta a mesma apresentação, sem paths, credenciais ou conteúdos de rede.
const registrosExportaveis = (rows: WindowItem[]) => rows.map(row => Object.fromEntries(reportWindowColumns.map(col => [col.header, col.value(row)])))
/** Reúne os dados recebidos e seus rótulos para o relatório. */
function reportPayload() {
  return {
    gerado_em: generatedAt,
    operacional: error.value ? { indisponivel: true } : {
      analises_importadas: summary.value?.analyses?.total_analyses ?? null,
      resultados_importados: summary.value?.analyses?.total_results ?? null,
    },
    evidencia_historica: evidencia,
    complementar: { limite_por_lista: 20, alertas: registrosExportaveis(alerts.value), janelas: registrosExportaveis(windows.value), distribuicao_padrao: attackDistribution.value, distribuicao_risco: riskDistribution.value },
  }
}
/** Monta o documento de relatório para impressão sem recalcular resultados científicos. */
function reportPdfHtml(): string {
  return `<section><h2>Resumo das análises realizadas</h2>${buildDefinitionTable([
    { label: 'Consulta', value: generatedAt }, { label: 'Situação', value: error.value || 'Dados consultados' },
    { label: 'Análises importadas', value: summary.value?.analyses?.total_analyses }, { label: 'Resultados por janela', value: summary.value?.analyses?.total_results },
  ])}</section><section><h2>${evidencia.titulo}</h2><p>${evidencia.janelas} janelas históricas · Ambiente de validação. Não é tempo real.</p>
  ${buildDefinitionTable(evidencia.metricas.map(item => ({ label: item.nome, value: percentual(item.valor) })))}
  <h3>Matriz de confusão</h3>${buildDefinitionTable(Object.entries(evidencia.matriz).map(([label, value]) => ({ label: label.toUpperCase(), value })))}
  <h3>Contribuição dos componentes · agregado histórico</h3>${buildDefinitionTable(evidencia.contribuicoes.map(item => ({ label: item.nome, value: percentual(item.percentual / 100) })))}
  <p>Influência relativa, não precisão isolada dos componentes.</p></section>
  <section><h2>Limitações</h2>${evidencia.limitacoes.map(nota => `<p>${escapeHtml(nota)}</p>`).join('')}</section>
  <section><h2>Histórico complementar</h2><p>Até 20 registros por lista; amostra distinta da validação histórica.</p><h3>Alertas consultados</h3>${buildHtmlTable(alerts.value, reportWindowColumns)}<h3>Janelas consultadas</h3>${buildHtmlTable(windows.value, reportWindowColumns)}</section>`
}
/** Abre o relatório para impressão ou gravação em PDF. */
function exportReportPdf(): void {
  feedback.value = exportPdfDocument(`Relatório do Sinalyx - ${dateStamp()}`, reportPdfHtml()) ? 'Relatório aberto para impressão ou salvamento em PDF.' : 'Não foi possível abrir a impressão. Verifique o bloqueio de pop-ups.'
}
/** Disponibiliza os dados do relatório em JSON. */
function exportReportJson(): void {
  feedback.value = exportJson(`sinalyx_relatorio_${dateStamp()}.json`, reportPayload()) ? 'Arquivo JSON exportado com sucesso.' : 'Não foi possível exportar.'
}
const ReportTable = defineComponent({
  props: { rows: { type: Array as () => WindowItem[], required: true } },
  setup(props) { return () => h('div', { class: 'mt-3 overflow-x-auto' }, [h('table', { class: 'w-full text-left text-sm' }, [
    h('thead', [h('tr', reportWindowColumns.map(col => h('th', { class: 'p-3 text-slate-400' }, col.header)))]),
    h('tbody', props.rows.map(row => h('tr', { key: row.id }, reportWindowColumns.map(col => h('td', { class: 'p-3 text-slate-300' }, String(col.value(row) ?? '-')))))),
  ])]) },
})
onMounted(async () => {
  try {
    const [s, w, a, status] = await Promise.all([getHistorySummary(), getHistoryWindows(20, 0), getHistoryAlerts(20, 0), getSystemStatus()])
    summary.value = s; windows.value = w.windows; alerts.value = a.alerts; systemStatus.value = status
  } catch { error.value = 'Dados operacionais indisponíveis. A evidência histórica abaixo permanece identificada separadamente.' }
  finally { loading.value = false }
})
</script>
