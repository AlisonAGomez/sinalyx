<!-- Consulta explicativa sobre padrões e contexto da janela, sem nova análise de tráfego. -->
<template>
  <section class="panel space-y-5 p-5 sm:p-6" data-testid="threat-consultation" aria-labelledby="consulta-ameacas-titulo">
    <div>
      <h2 id="consulta-ameacas-titulo" class="text-lg font-semibold text-white">Saiba mais sobre possíveis ameaças</h2>
      <p id="consulta-ameacas-aviso" class="mt-2 text-sm leading-6 text-slate-400">Esta consulta apresenta exemplos gerais de comportamentos suspeitos. Ela não determina a classificação da janela.</p>
    </div>

    <section class="space-y-3" aria-label="Padrões associados">
      <label class="block max-w-xl text-sm text-slate-300">
        Consultar comportamento
        <select v-model="selecionado" class="field mt-2 min-h-11 w-full px-3 py-2" data-testid="threat-category" aria-describedby="consulta-ameacas-aviso">
          <option value="">Selecione um comportamento para consultar</option>
          <option v-for="item in comportamentosConsulta" :key="item.id" :value="item.id">{{ item.nome }}</option>
        </select>
      </label>
      <template v-if="comportamento">
        <h3 class="text-sm font-semibold text-sky-200">{{ comportamento.nome }}</h3>
        <p class="text-sm leading-6 text-slate-300">{{ comportamento.descricao }}</p>
        <p class="text-sm leading-6 text-slate-400">{{ comportamento.limite }}</p>
        <ul class="space-y-2 text-sm text-slate-400">
          <li v-for="feature in indicadores" :key="feature.chave"><strong class="font-medium text-slate-200">{{ feature.nome }}:</strong> {{ feature.uso }}</li>
        </ul>
      </template>
      <p v-else class="text-sm leading-6 text-slate-300">Escolha um tipo de comportamento para conhecer os sinais de tráfego que podem estar associados a ele.</p>
    </section>

    <details class="border-t border-slate-800 pt-4">
      <summary class="focus-ring cursor-pointer rounded text-sm font-semibold text-white">Entenda as 13 features</summary>
      <p class="mt-3 text-sm leading-6 text-slate-400">No fluxo canônico, a agregação é por origem e intervalo; o padrão oficial é 5 segundos. Registros históricos podem usar outra duração. As fórmulas abaixo documentam o pipeline e não são executadas aqui.</p>
      <dl class="mt-4 grid gap-5 lg:grid-cols-2" data-testid="feature-reference">
        <div v-for="feature in featuresConsulta" :key="feature.chave" class="min-w-0">
          <dt class="text-sm font-medium text-slate-200">{{ feature.nome }}</dt>
          <dd class="mt-1 space-y-1 text-sm leading-6 text-slate-400">
            <p>{{ feature.definicao }}</p><p>{{ feature.unidade }} · {{ feature.limite }}</p>
            <p class="break-all text-xs text-slate-500">Campo: {{ feature.chave }}</p>
          </dd>
        </div>
      </dl>
    </details>

    <p class="text-sm leading-6 text-slate-400">Os indicadores apresentados auxiliam na interpretação do tráfego. Eles não confirmam isoladamente um ataque nem substituem a avaliação do analista. Um valor elevado não demonstra, por si só, a causa da decisão.</p>
    <details class="border-t border-slate-800 pt-4">
      <summary class="focus-ring cursor-pointer rounded text-sm font-semibold text-white">Referências</summary>
      <p class="mt-3 text-xs leading-5 text-slate-400">Estas fontes descrevem comportamentos gerais; não comprovam cobertura de todas as técnicas pelo Sinalyx.</p>
      <ul class="mt-3 space-y-2 text-sm">
        <li v-for="fonte in referenciasConsulta" :key="fonte.url"><a class="focus-ring break-words text-sky-300 underline underline-offset-4" :href="fonte.url" target="_blank" rel="noopener noreferrer">{{ fonte.nome }}</a></li>
      </ul>
    </details>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { WindowItem } from '@/types/api'
import { comportamentosConsulta, featuresConsulta, referenciasConsulta } from '@/content/consultaAmeacas'

const props = defineProps<{ janela: WindowItem }>()
const selecionado = ref('')
const comportamento = computed(() => comportamentosConsulta.find(item => item.id === selecionado.value))
const indicadores = computed(() => featuresConsulta.filter(feature => comportamento.value?.indicadores.includes(feature.chave)))

watch(() => props.janela, () => { selecionado.value = '' })
</script>
