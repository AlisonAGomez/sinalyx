<!-- Integrações planejadas e limites atuais; os cartões não executam configurações. -->
<template>
  <section class="space-y-5" qa-id="page-settings" data-testid="page-settings" data-qa-page="settings">
    <PageHeader
      eyebrow="Planejamento do sistema"
      title="Configurações"
      description="Visão das capacidades disponíveis e das evoluções planejadas. Recursos ainda não implementados aparecem apenas como informação, sem controles fictícios."
    />

    <section class="panel border-sky-400/[0.15] bg-sky-400/[0.025] p-5" data-testid="settings-overview">
      <p class="muted-label text-sky-300/80">Versão atual</p>
      <p class="mt-2 max-w-4xl text-sm leading-6 text-slate-300">Credenciais, tokens, chaves e outras informações sensíveis não são exibidos nem configurados por esta tela. O fluxo oficial do TCC trabalha com logs pfSense processados por upload/replay.</p>
    </section>

    <section class="space-y-3" aria-labelledby="settings-title">
      <div>
        <p class="muted-label">Capacidades</p>
        <h2 id="settings-title" class="mt-1 text-lg font-semibold text-white">O que está disponível e o que fica para depois</h2>
      </div>

      <div class="grid items-start gap-4 md:grid-cols-2 xl:grid-cols-3">
        <article v-for="item in settingsItems" :key="item.key" class="panel panel-hover flex flex-col p-5" :data-testid="`settings-${item.key}`">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <h3 class="text-sm font-semibold leading-5 text-white">{{ item.title }}</h3>
            <StatusBadge :value="item.status" :rotulo="item.label" />
          </div>
          <p class="mt-4 text-sm leading-6 text-slate-400">{{ item.description }}</p>
        </article>

        <article class="panel panel-hover flex flex-col p-5" data-testid="settings-security">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <h3 class="text-sm font-semibold leading-5 text-white">Proteção de informações sensíveis</h3>
            <span class="rounded-lg border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-xs font-semibold text-emerald-200">Ativo</span>
          </div>
          <p class="mt-4 text-sm leading-6 text-slate-400">A interface não deve revelar senhas, tokens, hashes, chaves, strings de conexão ou credenciais do pfSense.</p>
        </article>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'

const settingsItems = [
  { key: 'analysis-engine', title: 'Análise híbrida', status: 'active', label: 'Disponível', description: 'Combina modelos, análise estatística, regras de segurança e uma camada final de decisão interpretável.' },
  { key: 'database', title: 'Histórico e persistência', status: 'active', label: 'Disponível', description: 'Armazena análises, usuários e informações operacionais no PostgreSQL.' },
  { key: 'pfsense', title: 'Integração direta com pfSense', status: 'experimental', label: 'Em avaliação', description: 'A coleta automatizada e contínua diretamente do firewall não está habilitada como recurso oficial desta versão.' },
  { key: 'future-integrations', title: 'Eventos de autenticação', status: 'not_implemented', label: 'Planejado', description: 'Uma fonte futura de autenticação poderia complementar cenários que o firewall sozinho não observa, como tentativas de senha.' },
  { key: 'manual-review', title: 'Classificação manual', status: 'not_implemented', label: 'Planejado', description: 'Recurso futuro para registrar revisão humana e apoiar processos de investigação.' },
  { key: 'custom-rules', title: 'Regras personalizadas', status: 'not_implemented', label: 'Planejado', description: 'Configuração de regras próprias fica fora do escopo desta versão acadêmica.' },
] as const
</script>
