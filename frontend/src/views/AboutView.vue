<!-- Objetivo, arquitetura e limites de observação do Sinalyx. -->
<template>
  <section class="space-y-5" qa-id="page-about" data-testid="page-about" data-qa-page="about">
    <PageHeader
      eyebrow="Projeto"
      title="Sobre o Sinalyx"
      description="Uma plataforma acadêmica para transformar logs do firewall pfSense em informações mais claras para análise e investigação de segurança."
    />

    <section class="panel overflow-hidden p-5 sm:p-6">
      <div class="grid gap-6 xl:grid-cols-[1.15fr_0.85fr] xl:items-center">
        <div>
          <p class="muted-label text-sky-300/80">Em termos simples</p>
          <h2 class="mt-2 text-xl font-semibold tracking-tight text-white">O sistema procura comportamentos que merecem atenção e explica o resultado.</h2>
          <p class="mt-3 max-w-3xl text-sm leading-7 text-slate-400">O Sinalyx organiza registros reais do pfSense em pequenas janelas de análise, extrai características do tráfego e combina diferentes sinais antes de apresentar a classificação final, o risco e o motivo da decisão.</p>
        </div>
        <div class="rounded-2xl border border-sky-400/[0.15] bg-sky-400/[0.035] p-5">
          <p class="text-sm font-semibold text-sky-100">O que ele não faz</p>
          <ul class="mt-3 space-y-2 text-sm leading-6 text-slate-400">
            <li>Não bloqueia ataques automaticamente.</li>
            <li>Não substitui um analista ou uma solução SIEM.</li>
            <li>Não consegue observar senhas ou confirmar falhas de autenticação apenas pelos logs do firewall.</li>
            <li>A coleta contínua direta do pfSense não está habilitada como recurso oficial desta versão.</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <InfoCard title="Modelo de anomalia" text="Procura comportamentos que se afastam do padrão aprendido. No TCC, esse papel é exercido pelo Autoencoder." />
      <InfoCard title="Análise estatística" text="Fornece um sinal complementar para comportamentos incomuns. No projeto, é realizada pelo Isolation Forest." />
      <InfoCard title="Regras de segurança" text="Acrescentam contexto interpretável para padrões como varredura de portas, SYN Flood e atividade SSH suspeita." />
      <InfoCard title="Decisão final" text="O Ensemble e a Decision Engine consolidam os sinais e produzem o resultado apresentado ao usuário." />
    </section>

    <section class="panel p-5 sm:p-6">
      <p class="muted-label">Como os dados percorrem o sistema</p>
      <h2 class="mt-1 text-base font-semibold text-white">Fluxo de análise</h2>
      <div class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        <Step v-for="(step, index) in steps" :key="step" :label="step" :index="index + 1" />
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { defineComponent, h } from 'vue'
import PageHeader from '@/components/ui/PageHeader.vue'

const steps = [
  'Logs do pfSense', 'Parser e janelas', '13 características', 'Sinais e regras', 'Resultado no painel',
]

const InfoCard = defineComponent({
  props: { title: { type: String, required: true }, text: { type: String, required: true } },
  setup(props) {
    return () => h('article', { class: 'panel panel-hover p-5' }, [
      h('h2', { class: 'text-sm font-semibold text-white' }, props.title),
      h('p', { class: 'mt-2 text-sm leading-6 text-slate-400' }, props.text),
    ])
  },
})

const Step = defineComponent({
  props: { label: { type: String, required: true }, index: { type: Number, required: true } },
  setup(props) {
    return () => h('div', { class: 'relative rounded-xl border border-slate-800/80 bg-slate-950/[0.22] p-4' }, [
      h('p', { class: 'text-[10px] font-semibold uppercase tracking-[0.16em] text-sky-300/80' }, `Etapa ${props.index}`),
      h('p', { class: 'mt-2 text-sm font-medium text-slate-200' }, props.label),
    ])
  },
})
</script>
