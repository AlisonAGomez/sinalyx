<!-- Investigação das janelas de uma análise importada e de suas contribuições já calculadas. -->
<template>
  <section class="mx-auto w-full max-w-[1440px] space-y-5" qa-id="page-analysis-details" data-testid="page-analysis-details" data-qa-page="analysis-details">
    <PageHeader
      eyebrow="Análise importada"
      title="Detalhes da análise"
      description="Resultado consolidado de uma análise já processada, com acesso às janelas e aos motivos apresentados pelo sistema."
    >
      <template #actions>
        <RouterLink class="btn btn-secondary" to="/history" qa-id="analysis-details-back" data-testid="analysis-details-back">
          Voltar
        </RouterLink>
      </template>
    </PageHeader>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />

    <template v-else-if="details">
      <div class="grid gap-4 md:grid-cols-3">
        <StatCard
          qa-id="analysis-details-card-windows"
          data-testid="analysis-details-card-windows"
          label="Janelas"
          :value="details.total_windows"
          :icon="TableProperties"
          icon-class="border-sky-400/30 bg-sky-400/10 text-sky-200"
        />
        <StatCard
          qa-id="analysis-details-card-attack-type"
          data-testid="analysis-details-card-attack-type"
          label="Tipo predominante"
          :value="formatAttackType(details.classification?.predominant_attack_type)"
          :icon="Crosshair"
          icon-class="border-red-400/30 bg-red-400/10 text-red-200"
        />
        <StatCard
          qa-id="analysis-details-card-risk"
          data-testid="analysis-details-card-risk"
          label="Risco"
          :value="formatRiskLevel(details.classification?.predominant_risk_level)"
          :icon="ShieldAlert"
          icon-class="border-amber-400/30 bg-amber-400/10 text-amber-200"
        />
      </div>

      <div class="panel p-4">
        <div class="grid gap-3 text-sm md:grid-cols-2">
          <div>
            <p class="muted-label">Arquivo</p>
            <p class="mt-1 break-words text-slate-200">{{ details.filename }}</p>
          </div>
          <div>
            <p class="muted-label">Criado em</p>
            <p class="mt-1 text-slate-200">{{ formatDate(details.created_at) }}</p>
          </div>
        </div>
      </div>

      <section v-if="resultadoSelecionado" ref="detalheJanela" tabindex="-1" class="space-y-3 rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400" aria-label="Detalhes da janela selecionada" id="detalhe-janela-importada">
        <div class="panel flex flex-wrap items-center justify-between gap-3 p-4">
          <div class="min-w-0">
            <h2 class="text-base font-semibold text-white">{{ formatAttackType(resultadoSelecionado.attack_type) }}</h2>
            <div class="mt-2 flex flex-wrap gap-2">
              <StatusBadge :value="resultadoSelecionado.final_label" :rotulo="formatFinalLabel(resultadoSelecionado.final_label)" />
              <StatusBadge :value="resultadoSelecionado.risk_level" />
            </div>
            <p class="mt-1 break-all text-sm text-slate-300">{{ resultadoSelecionado.window_id ?? '-' }}</p>
          </div>
          <button type="button" class="btn btn-secondary" @click="fecharDetalhes">Fechar detalhes</button>
        </div>
        <ComponentContributionsPanel :contribuicoes="resultadoSelecionado.component_contributions" />
        <section class="panel p-5">
          <h2 class="text-base font-semibold text-white">Resultado da análise</h2>
          <p class="mt-3 text-sm leading-6 text-slate-300">{{ formatarMotivo(resultadoSelecionado) }}</p>
        </section>
        <section class="panel p-5">
          <h2 class="text-base font-semibold text-white">Dados relevantes</h2>
          <dl class="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <div v-for="campo in camposResultado" :key="campo.chave">
              <dt class="text-xs text-slate-400">{{ campo.rotulo }}</dt>
              <dd class="mt-1 break-words text-sm text-slate-200">{{ resultadoSelecionado[campo.chave] ?? 'Não informado' }}</dd>
            </div>
          </dl>
        </section>
      </section>

      <div class="panel overflow-hidden" qa-id="analysis-details-results" data-testid="analysis-details-results">
        <div class="border-b border-slate-800 px-4 py-3">
          <h2 class="text-sm font-semibold text-white">Resultados</h2>
        </div>
        <LoadingState v-if="carregandoResultados" label="Carregando janelas da análise" />
        <div v-else-if="erroResultados" class="space-y-3 p-4">
          <ErrorState :message="erroResultados" />
          <button type="button" class="btn btn-secondary" @click="mudarPagina(offsetResultados)">Tentar novamente</button>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-800 text-sm">
            <thead class="bg-surface-850 text-left text-xs uppercase text-slate-500">
              <tr>
                <th class="px-4 py-3 font-medium">Janela</th>
                <th class="px-4 py-3 font-medium">Classificação</th>
                <th class="px-4 py-3 font-medium">Tipo</th>
                <th class="px-4 py-3 font-medium">Risco</th>
                <th class="px-4 py-3 font-medium">Motivo da classificação</th>
                <th class="px-4 py-3 font-medium">Detalhes</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
              <tr v-for="(result, index) in results" :key="`${result.window_id ?? index}`" class="table-row">
                <td class="break-all px-4 py-3 text-slate-300">{{ result.window_id ?? '-' }}</td>
                <td class="px-4 py-3"><StatusBadge :value="String(result.final_label ?? '-')" :rotulo="formatFinalLabel(result.final_label)" /></td>
                <td class="px-4 py-3 text-slate-300">{{ formatAttackType(result.attack_type) }}</td>
                <td class="px-4 py-3"><StatusBadge :value="String(result.risk_level ?? '-')" /></td>
                <td class="px-4 py-3 text-slate-400">{{ formatarMotivo(result) }}</td>
                <td class="px-4 py-3">
                  <button type="button" class="btn btn-secondary whitespace-nowrap" :aria-label="`Ver detalhes da janela ${result.window_id ?? index + 1}`" :aria-expanded="resultadoSelecionado === result" aria-controls="detalhe-janela-importada" @click="abrirDetalhes(result, $event)">Ver detalhes</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="!carregandoResultados && !erroResultados && results.length === 0" class="px-5 py-4 text-sm text-slate-500">Nenhum resultado por janela foi retornado para esta análise.</p>
        <nav v-if="totalResultados !== null" aria-label="Paginação das janelas da análise" class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 px-4 py-3">
          <p class="text-sm text-slate-400" role="status" aria-live="polite">
            <template v-if="totalResultados > 0">Página {{ Math.floor(offsetResultados / TAMANHO_PAGINA) + 1 }} de {{ Math.ceil(totalResultados / TAMANHO_PAGINA) }} · </template>
            {{ totalResultados }} janelas
          </p>
          <div class="flex gap-2">
            <button type="button" class="btn btn-secondary" data-testid="analysis-results-prev" qa-id="analysis-results-prev" :disabled="offsetResultados === 0" @click="mudarPagina(offsetResultados - TAMANHO_PAGINA)">Anterior</button>
            <button type="button" class="btn btn-secondary" data-testid="analysis-results-next" qa-id="analysis-results-next" :disabled="offsetResultados + TAMANHO_PAGINA >= totalResultados" @click="mudarPagina(offsetResultados + TAMANHO_PAGINA)">Próxima</button>
          </div>
        </nav>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { Crosshair, ShieldAlert, TableProperties } from 'lucide-vue-next'

import ComponentContributionsPanel from '@/components/ui/ComponentContributionsPanel.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { getAnalysisDetails, getAnalysisResults } from '@/services/api'
import type { AnalysisDetails, AnalysisResultItem } from '@/types/api'
import {
  formatDateTime,
  formatRiskLevel,
} from '@/utils/formatters'
import { formatarClassificacao as formatAttackType, formatarClassificacao as formatFinalLabel, formatarMotivo } from '@/utils/apresentacaoSeguranca'

type AnalysisResultRow = {
  window_id?: string
  final_label?: string
  attack_type?: string
  risk_level?: string
  decision_source?: string
} & AnalysisResultItem

const props = defineProps<{
  id: string
}>()

const camposResultado = [
  { chave: 'window_start', rotulo: 'Início da janela' },
  { chave: 'window_end', rotulo: 'Fim da janela' },
  { chave: 'connections', rotulo: 'Conexões' },
  { chave: 'packets', rotulo: 'Pacotes' },
  { chave: 'bytes', rotulo: 'Bytes' },
  { chave: 'ports', rotulo: 'Portas' },
]

const details = ref<AnalysisDetails | null>(null)
const results = ref<AnalysisResultRow[]>([])
const resultadoSelecionado = ref<AnalysisResultRow | null>(null)
const detalheJanela = ref<HTMLElement | null>(null)
let botaoOrigem: HTMLElement | null = null

/** Seleciona o resultado recebido e leva o foco para sua área de investigação. */
async function abrirDetalhes(resultado: AnalysisResultRow, evento: MouseEvent): Promise<void> {
  botaoOrigem = evento.currentTarget as HTMLElement
  resultadoSelecionado.value = resultado
  await nextTick()
  detalheJanela.value?.focus()
  detalheJanela.value?.scrollIntoView({ block: 'nearest' })
}

/** Limpa a seleção de janela e fecha sua área de investigação. */
function fecharDetalhes(): void {
  resultadoSelecionado.value = null
  botaoOrigem?.focus()
}

const loading = ref(true)
const error = ref('')
const TAMANHO_PAGINA = 50
const carregandoResultados = ref(true)
const erroResultados = ref('')
const offsetResultados = ref(0)
const totalResultados = ref<number | null>(null)
let geracaoAnalise = 0
let requisicaoResultados = 0

/** Reutiliza o formato de data da aplicação para o resumo da análise. */
function formatDate(value: string): string {
  return formatDateTime(value)
}

/** Carrega a análise atual e ignora respostas de uma navegação anterior. */
async function loadAnalysis(id: string): Promise<void> {
  const geracao = ++geracaoAnalise
  /** Confere se a resposta ainda pertence à solicitação e ao contexto atuais da tela. */
  const atual = () => geracao === geracaoAnalise && props.id === id
  loading.value = true
  error.value = ''
  details.value = null
  totalResultados.value = null
  void carregarResultados(id, 0, geracao)
  try {
    const detailsResponse = await getAnalysisDetails(id)
    if (!atual()) return
    details.value = detailsResponse
  } catch {
    if (atual()) error.value = 'Não foi possível carregar os detalhes desta análise.'
  } finally {
    if (atual()) loading.value = false
  }
}

/** Carrega a página solicitada sem aceitar resultados obsoletos de outra análise ou página. */
async function carregarResultados(id: string, offset: number, geracao: number): Promise<void> {
  const requisicao = ++requisicaoResultados
  /** Confere se a resposta ainda pertence à solicitação e ao contexto atuais da tela. */
  const atual = () => geracao === geracaoAnalise && props.id === id && requisicao === requisicaoResultados
  offsetResultados.value = offset
  carregandoResultados.value = true
  erroResultados.value = ''
  results.value = []
  resultadoSelecionado.value = null
  botaoOrigem = null
  try {
    const resposta = await getAnalysisResults(id, TAMANHO_PAGINA, offset)
    if (!atual()) return
    totalResultados.value = resposta.meta?.total ?? resposta.total_windows
    const pagina = (resposta.data?.results ?? resposta.results ?? []) as AnalysisResultRow[]
    // Se o total diminuiu, não mantém uma página que deixou de existir.
    if (pagina.length === 0 && offset > 0 && offset >= totalResultados.value) {
      const ultimoOffset = Math.max(0, Math.floor((totalResultados.value - 1) / TAMANHO_PAGINA) * TAMANHO_PAGINA)
      if (totalResultados.value === 0) offsetResultados.value = 0
      else await carregarResultados(id, ultimoOffset, geracao)
      return
    }
    results.value = pagina
  } catch {
    if (atual()) erroResultados.value = 'Não foi possível carregar as janelas desta análise.'
  } finally {
    if (atual()) carregandoResultados.value = false
  }
}

/** Solicita a página de resultados mantendo o vínculo com a análise atual. */
function mudarPagina(offset: number): void {
  if (offset < 0 || (totalResultados.value !== null && offset > 0 && offset >= totalResultados.value)) return
  void carregarResultados(props.id, offset, geracaoAnalise)
}

watch(() => props.id, (id) => { void loadAnalysis(id) }, { immediate: true })
onBeforeUnmount(() => {
  // Invalida também catch/finally de chamadas ainda pendentes.
  geracaoAnalise += 1
  requisicaoResultados += 1
})
</script>
