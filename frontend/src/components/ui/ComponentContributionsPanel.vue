<!-- Mostra influência relativa já calculada; participação não é precisão nem probabilidade de ataque. -->
<template>
  <section
    v-if="contribuicoes.length"
    class="panel overflow-hidden p-5 sm:p-6"
    :aria-labelledby="tituloId"
    qa-id="component-contributions"
    data-testid="component-contributions"
  >
    <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <p class="muted-label text-cyan-300/80">Base da análise</p>
        <h2 :id="tituloId" class="mt-1 text-base font-semibold text-white">Contribuição para esta decisão</h2>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-400">Mostra o peso relativo das fontes que sustentaram esta classificação.</p>
      </div>
      <span class="rounded-lg border border-slate-700/70 bg-slate-950/25 px-2.5 py-1 text-xs text-slate-500">Explicação da decisão</span>
    </div>

    <ul class="mt-5 grid gap-4 md:grid-cols-3">
      <li v-for="contribuicao in contribuicoes" :key="contribuicao.fonte" class="rounded-xl border border-slate-800/80 bg-slate-950/[0.22] p-4">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-sm font-semibold text-slate-100">{{ contribuicao.nome }}</p>
            <p class="mt-1 text-xs leading-5 text-slate-500">{{ direcoesContribuicao[contribuicao.direcao] }}</p>
          </div>
          <span class="shrink-0 text-sm font-semibold tabular-nums text-cyan-100">{{ formatarParticipacao(contribuicao.percentual) }}</span>
        </div>
        <div class="mt-4 h-2 overflow-hidden rounded-full bg-slate-800" aria-hidden="true">
          <div
            class="h-full origin-left rounded-full bg-gradient-to-r from-sky-400 to-cyan-300 shadow-[0_0_14px_rgba(34,211,238,0.18)]"
            :style="{ width: `${contribuicao.percentual}%`, animation: 'bar-grow-x 520ms cubic-bezier(.2,.7,.2,1) both' }"
          />
        </div>
      </li>
    </ul>
    <p class="mt-4 text-xs leading-5 text-slate-500">Os percentuais representam influência relativa nesta decisão, não precisão individual dos componentes.</p>
  </section>
</template>

<script setup lang="ts">
import { computed, useId } from 'vue'
import type { ComponentContributionDirection, ComponentContributionsPayload } from '@/types/api'

const props = defineProps<{ contribuicoes?: ComponentContributionsPayload | null }>()
const tituloId = useId()

const fontesContribuicao = [
  { fonte: 'autoencoder', nome: 'Autoencoder' },
  { fonte: 'isolation_forest', nome: 'Isolation Forest' },
  { fonte: 'security_rules', nome: 'Regras de segurança' },
] as const

const direcoesContribuicao: Record<ComponentContributionDirection, string> = {
  toward_anomaly: 'Reforçou a suspeita',
  toward_normal: 'Reduziu a suspeita',
  neutral: 'Sem influência relevante',
}

const formatoParticipacao = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 })
/** Formata a participação recebida do servidor sem calcular novas contribuições. */
function formatarParticipacao(percentual: number): string {
  return `${formatoParticipacao.format(percentual)}%`
}

const contribuicoes = computed(() => {
  const bloco = props.contribuicoes
  if (!bloco?.components) return []
  return fontesContribuicao.flatMap(({ fonte, nome }) => {
    const item = bloco.components[fonte]
    if (!item || !Number.isFinite(item.relative_share_percent)) return []
    return [{ fonte, nome, percentual: item.relative_share_percent, direcao: item.direction }]
  }).sort((a, b) => b.percentual - a.percentual)
})
</script>
