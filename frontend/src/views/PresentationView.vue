<!-- Roteiro acadêmico do projeto, com metodologia, resultados históricos e limitações. -->
<template>
  <section
    class="mx-auto w-full max-w-[1440px] space-y-5"
    qa-id="page-demo"
    data-testid="page-demo"
    data-qa-page="demo"
  >
    <PageHeader
      eyebrow="Apresentação do TCC"
      title="Sinalyx"
      description="O Sinalyx auxilia a análise de eventos de rede combinando múltiplos sinais para apoiar a identificação de padrões anômalos."
    />

    <section class="panel overflow-hidden border-sky-400/25 bg-sky-400/[0.04] p-5 sm:p-6" data-testid="presentation-intro">
      <div class="grid gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(18rem,0.7fr)] lg:items-center">
        <div>
          <p class="muted-label text-sky-200">Análise combinada</p>
          <h2 class="mt-2 max-w-3xl text-2xl font-semibold leading-tight text-white sm:text-3xl">
            Análise de logs de firewall combinando modelos, regras de segurança e decisão interpretável.
          </h2>
          <p class="mt-4 max-w-3xl text-sm leading-6 text-slate-300">
            O sistema transforma registros do pfSense em janelas analisáveis, combina modelos de IA, análise estatística e regras de segurança, e apresenta uma decisão interpretável para apoiar a investigação humana.
          </p>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="rounded-xl border border-slate-800 bg-surface-850/80 p-4">
            <p class="text-xs font-medium uppercase tracking-wide text-slate-500">Entrada oficial</p>
            <p class="mt-2 text-lg font-semibold text-white">Logs pfSense</p>
            <p class="mt-1 text-xs leading-5 text-slate-400">Eventos agrupados em janelas</p>
          </div>
          <div class="rounded-xl border border-slate-800 bg-surface-850/80 p-4">
            <p class="text-xs font-medium uppercase tracking-wide text-slate-500">Representação</p>
            <p class="mt-2 text-lg font-semibold text-white">13 características</p>
            <p class="mt-1 text-xs leading-5 text-slate-400">Representação utilizada na análise</p>
          </div>
        </div>
      </div>
    </section>

    <section class="space-y-3" data-testid="presentation-problem-objective">
      <div>
        <p class="muted-label">Contexto do projeto</p>
        <h2 class="mt-1 text-lg font-semibold text-white">Problema e objetivo</h2>
      </div>
      <div class="grid gap-3 md:grid-cols-2">
        <article class="panel panel-hover p-5">
          <p class="text-xs font-medium uppercase tracking-wide text-amber-200">Problema</p>
          <p class="mt-3 text-sm leading-6 text-slate-300">
            Grandes volumes de logs de firewall dificultam a análise manual e a identificação de padrões fora do comportamento esperado.
          </p>
        </article>
        <article class="panel panel-hover p-5">
          <p class="text-xs font-medium uppercase tracking-wide text-sky-200">Objetivo</p>
          <p class="mt-3 text-sm leading-6 text-slate-300">
            Desenvolver uma solução híbrida capaz de analisar logs, combinar sinais e apresentar explicações sobre as decisões.
          </p>
        </article>
      </div>
    </section>

    <section class="panel p-5 sm:p-6" data-testid="presentation-architecture">
      <div>
        <p class="muted-label">Visão do sistema</p>
        <h2 class="mt-1 text-lg font-semibold text-white">Arquitetura híbrida</h2>
        <p class="mt-2 max-w-4xl text-sm leading-6 text-slate-400">
          Os modelos geram sinais complementares. A decisão final é consolidada pelo Ensemble e pelo Decision Engine, que organizam a classificação, o risco e a explicação.
        </p>
      </div>
      <ol class="mt-5 flex flex-wrap items-center gap-2" aria-label="Fluxo oficial de análise">
        <li v-for="(step, index) in architectureSteps" :key="step.label" class="flex min-w-0 items-center gap-2">
          <div class="min-w-[8.5rem] rounded-xl border border-slate-800 bg-surface-850 px-3 py-3 text-center">
            <span class="block text-[11px] font-semibold uppercase tracking-wide text-sky-300">Etapa {{ index + 1 }}</span>
            <span class="mt-1 block text-sm font-medium text-slate-200">{{ step.label }}</span>
            <span v-if="step.branches" class="mt-2 grid gap-1 text-xs text-slate-400">
              <span v-for="branch in step.branches" :key="branch">{{ branch }}</span>
            </span>
          </div>
          <span v-if="index < architectureSteps.length - 1" class="hidden text-lg text-slate-600 sm:inline" aria-hidden="true">→</span>
        </li>
      </ol>
    </section>

    <section class="space-y-3" data-testid="presentation-components">
      <div>
        <p class="muted-label">Como a análise é composta</p>
        <h2 class="mt-1 text-lg font-semibold text-white">Componentes da análise</h2>
      </div>
      <div class="grid gap-3 md:grid-cols-2 2xl:grid-cols-5">
        <article v-for="component in components" :key="component.title" class="panel panel-hover p-4">
          <div class="flex items-center gap-2">
            <span class="h-2 w-2 rounded-full" :class="component.dotClass" aria-hidden="true" />
            <h3 class="text-sm font-semibold text-white">{{ component.title }}</h3>
          </div>
          <p class="mt-3 text-sm leading-6 text-slate-400">{{ component.description }}</p>
        </article>
      </div>
    </section>

    <section class="panel p-5 sm:p-6" data-testid="presentation-validation">
      <div class="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="muted-label text-sky-200">Evidência histórica</p>
          <h2 class="mt-1 text-lg font-semibold text-white">Validação histórica reproduzida</h2>
        </div>
        <p class="text-sm text-slate-400">Ambiente de validação histórica · unidade: janela</p>
      </div>

      <div class="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <div v-for="metric in validationMetrics" :key="metric.label" class="rounded-xl border border-slate-800 bg-surface-850 p-4">
          <p class="text-xs font-medium uppercase tracking-wide text-slate-500">{{ metric.label }}</p>
          <p class="mt-2 text-2xl font-semibold tabular-nums text-white">{{ metric.value }}</p>
          <p class="mt-1 text-xs leading-5 text-slate-400">{{ metric.hint }}</p>
        </div>
      </div>

      <div class="mt-6 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(20rem,0.8fr)]">
        <div>
          <h3 class="text-sm font-semibold text-white">Matriz de confusão</h3>
          <div class="mt-3 overflow-x-auto rounded-xl border border-slate-800">
            <table class="w-full min-w-[28rem] text-left text-sm">
              <caption class="sr-only">Rótulo de referência nas linhas e classificação do pipeline nas colunas</caption>
              <thead class="bg-surface-850 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th class="px-4 py-3 font-medium">Referência / resultado</th>
                  <th class="px-4 py-3 font-medium">Sem indícios</th>
                  <th class="px-4 py-3 font-medium">Com indícios</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800 text-slate-300">
                <tr>
                  <th class="px-4 py-3 font-normal">Negativo de referência</th>
                  <td class="px-4 py-3 tabular-nums">TN 144</td>
                  <td class="px-4 py-3 tabular-nums">FP 1</td>
                </tr>
                <tr>
                  <th class="px-4 py-3 font-normal">Positivo de referência</th>
                  <td class="px-4 py-3 tabular-nums">FN 18</td>
                  <td class="px-4 py-3 tabular-nums">TP 192</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="rounded-xl border border-amber-400/20 bg-amber-400/[0.04] p-4">
          <p class="text-sm font-semibold text-amber-100">Como interpretar</p>
          <p class="mt-2 text-sm leading-6 text-slate-300">
            Resultados históricos reproduzidos em ambiente controlado de validação. Eles não representam operação em tempo real ou garantia de desempenho futuro.
          </p>
        </div>
      </div>
    </section>

    <section class="panel p-5 sm:p-6" data-testid="presentation-contributions">
      <div>
        <p class="muted-label">Explicabilidade</p>
        <h2 class="mt-1 text-lg font-semibold text-white">Contribuição dos componentes</h2>
        <p class="mt-2 text-sm leading-6 text-slate-400">Influência relativa nas decisões analisadas.</p>
      </div>
      <ul class="mt-5 grid gap-4 md:grid-cols-3">
        <li v-for="item in contributions" :key="item.label">
          <div class="flex items-center justify-between gap-3 text-sm font-medium text-slate-200">
            <span>{{ item.label }}</span>
            <span class="tabular-nums text-cyan-200">{{ item.value }}</span>
          </div>
          <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-800" aria-hidden="true">
            <div class="h-full origin-left rounded-full bg-gradient-to-r from-sky-400 to-cyan-300" :style="{ width: item.width, animation: 'bar-grow-x 620ms cubic-bezier(.2,.7,.2,1) both' }" />
          </div>
        </li>
      </ul>
      <p class="mt-5 text-xs leading-5 text-slate-400">
        Os percentuais representam influência relativa nas decisões analisadas e não precisão individual dos componentes.
      </p>
    </section>

    <section class="grid gap-3 lg:grid-cols-[minmax(0,1.15fr)_minmax(18rem,0.85fr)]">
      <article class="panel border-amber-400/20 bg-amber-400/[0.03] p-5" data-testid="presentation-limitations">
        <p class="muted-label text-amber-200">Escopo e interpretação</p>
        <h2 class="mt-1 text-lg font-semibold text-white">Limitações</h2>
        <ul class="mt-4 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-300">
          <li v-for="limitation in limitations" :key="limitation">{{ limitation }}</li>
        </ul>
      </article>

      <article class="panel p-5" data-testid="presentation-technologies">
        <p class="muted-label">Stack do projeto</p>
        <h2 class="mt-1 text-lg font-semibold text-white">Tecnologias</h2>
        <div class="mt-4 space-y-4">
          <div v-for="group in technologyGroups" :key="group.title">
            <p class="text-xs font-medium uppercase tracking-wide text-slate-500">{{ group.title }}</p>
            <p class="mt-1 text-sm leading-6 text-slate-300">{{ group.items.join(' · ') }}</p>
          </div>
        </div>
      </article>
    </section>

    <section class="panel p-5 sm:p-6" data-testid="presentation-demo-links">
      <div>
        <p class="muted-label">Demonstração prática</p>
        <h2 class="mt-1 text-lg font-semibold text-white">Explore o sistema</h2>
        <p class="mt-2 text-sm leading-6 text-slate-400">A apresentação explica o projeto; estas telas mostram a aplicação em uso.</p>
      </div>
      <div class="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <RouterLink
          v-for="link in demoLinks"
          :key="link.to"
          :to="link.to"
          class="group rounded-xl border border-slate-800 bg-surface-850 p-4 transition hover:border-sky-400/40 hover:bg-surface-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-300/60"
        >
          <span class="text-sm font-semibold text-white group-hover:text-sky-200">{{ link.label }}</span>
          <span class="mt-1 block text-xs leading-5 text-slate-400">{{ link.description }}</span>
        </RouterLink>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

import PageHeader from '@/components/ui/PageHeader.vue'

const architectureSteps = [
  { label: 'pfSense/logs' },
  { label: 'Parser' },
  { label: 'Agregação em janelas' },
  { label: '13 características' },
  { label: 'Sinais complementares', branches: ['Autoencoder', 'Isolation Forest', 'Heurística'] },
  { label: 'Ensemble' },
  { label: 'Decision Engine' },
  { label: 'FastAPI' },
  { label: 'PostgreSQL' },
  { label: 'Frontend' },
]

const components = [
  {
    title: 'Autoencoder',
    description: 'Identifica padrões anômalos comparando o comportamento observado com padrões aprendidos.',
    dotClass: 'bg-cyan-400',
  },
  {
    title: 'Isolation Forest',
    description: 'Método estatístico auxiliar para encontrar comportamentos fora do padrão.',
    dotClass: 'bg-sky-400',
  },
  {
    title: 'Heurística',
    description: 'Utiliza regras baseadas em características observáveis do tráfego.',
    dotClass: 'bg-amber-400',
  },
  {
    title: 'Ensemble',
    description: 'Combina os diferentes sinais produzidos pelos componentes da análise.',
    dotClass: 'bg-violet-400',
  },
  {
    title: 'Decision Engine',
    description: 'Consolida decisão, risco, classificação e explicação para cada janela.',
    dotClass: 'bg-emerald-400',
  },
]

const validationMetrics = [
  { label: 'Janelas avaliadas', value: '355', hint: 'conjunto histórico reproduzido' },
  { label: 'Precision', value: '99,48%', hint: 'precisão por janela' },
  { label: 'Recall', value: '91,43%', hint: 'sensibilidade por janela' },
  { label: 'F1-score', value: '95,29%', hint: 'equilíbrio entre precision e recall' },
  { label: 'FPR', value: '0,69%', hint: 'falsos positivos' },
]

const contributions = [
  { label: 'Regras de segurança', value: '55,22%', width: '55.22%' },
  { label: 'Modelo de anomalia', value: '30,40%', width: '30.40%' },
  { label: 'Análise estatística', value: '14,38%', width: '14.38%' },
]

const limitations = [
  'Logs de firewall não observam autenticação diretamente.',
  'Brute force possui limitação de observabilidade usando apenas logs do pfSense.',
  'A coleta contínua direta do pfSense não está finalizada e permanece experimental.',
  'O Sinalyx não bloqueia ataques automaticamente.',
]

const technologyGroups = [
  { title: 'Frontend', items: ['Vue 3', 'TypeScript', 'Tailwind'] },
  { title: 'Backend', items: ['FastAPI', 'Python', 'PostgreSQL'] },
  { title: 'IA', items: ['TensorFlow/Keras', 'scikit-learn'] },
  { title: 'Infraestrutura', items: ['Docker Compose'] },
]

const demoLinks = [
  { to: '/', label: 'Dashboard', description: 'Resumo operacional das janelas consultadas.' },
  { to: '/alerts', label: 'Alertas', description: 'Fila de eventos para investigação.' },
  { to: '/history', label: 'Histórico', description: 'Análises realizadas e registros persistidos.' },
  { to: '/reports', label: 'Relatórios', description: 'Validação histórica e síntese dos resultados.' },
]
</script>
