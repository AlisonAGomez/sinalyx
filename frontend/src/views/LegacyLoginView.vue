<!-- Apresentação do projeto e entrada autenticada; os efeitos visuais não representam atividade real. -->
<template>
  <main
    class="login-scene relative min-h-screen overflow-x-hidden overflow-y-auto bg-surface-950 px-3 py-4 text-slate-100 sm:px-5 sm:py-5 lg:px-6 lg:py-4"
    qa-id="page-login"
    data-testid="page-login"
    data-qa-page="login"
  >
    <div class="login-background pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <div class="absolute inset-0 cyber-grid opacity-60" />
      <div class="login-scan absolute inset-0" />
      <div class="login-particles absolute inset-0">
        <span v-for="particle in 14" :key="particle" />
      </div>
      <div class="login-code-rain absolute inset-0">
        <span v-for="row in binaryRows" :key="row">{{ row }}</span>
      </div>
      <div class="login-log-stream absolute inset-0">
        <span v-for="line in backgroundLogs" :key="line">{{ line }}</span>
      </div>
      <div class="login-bg-card login-bg-log">
        <p>FLUXO ILUSTRATIVO</p>
        <span>Entrada: registros do firewall pfSense</span>
        <span>Organização: eventos em janelas</span>
        <span>Análise: sinais complementares</span>
        <span>Classificação: combinação de sinais</span>
        <span>Resultado: interpretação para investigação</span>
      </div>
      <div class="login-bg-card login-bg-status">
        <p>ARQUITETURA DA ANÁLISE</p>
        <span>ABORDAGEM <strong>HÍBRIDA</strong></span>
        <span>ORIGEM <strong>pfSense</strong></span>
        <span>ENTRADA <strong>LOGS</strong></span>
        <span>RESULTADO <strong>INTERPRETÁVEL</strong></span>
      </div>
      <div class="login-bg-card login-bg-event">
        <p>ETAPAS DA ANÁLISE</p>
        <span>Organização dos registros</span>
        <span>Combinação de sinais</span>
        <span>Interpretação dos resultados</span>
      </div>
      <svg class="login-circuit-layer absolute inset-0" viewBox="0 0 1440 820" preserveAspectRatio="none">
        <g class="login-circuit-base">
          <path class="login-circuit-trace login-circuit-trace-a" d="M-60 92 H190 L254 48 H444 L514 96 H666 L734 58 H934 L1000 96 H1500" />
          <path class="login-circuit-trace login-circuit-trace-b" d="M-60 148 H130 L194 148 L260 106 H522 L590 148 H812 L884 108 H1500" />
          <path class="login-circuit-trace login-circuit-trace-c" d="M-60 248 H252 L316 206 H594 L666 248 H884 L958 206 H1500" />
          <path class="login-circuit-trace login-circuit-trace-d" d="M-60 560 H210 L282 516 H552 L632 560 H864 L940 520 H1500" />
          <path class="login-circuit-trace login-circuit-trace-e" d="M-60 664 H158 L228 620 H504 L584 664 H786 L854 624 H1500" />
          <path class="login-circuit-trace login-circuit-trace-f" d="M-60 742 H320 L394 700 H686 L762 742 H1012 L1090 700 H1500" />
        </g>
        <g class="login-circuit-pulses">
          <path class="login-circuit-pulse login-pulse-a" d="M-60 92 H190 L254 48 H444 L514 96 H666 L734 58 H934 L1000 96 H1500" />
          <path class="login-circuit-pulse login-pulse-b" d="M-60 248 H252 L316 206 H594 L666 248 H884 L958 206 H1500" />
          <path class="login-circuit-pulse login-pulse-c" d="M-60 560 H210 L282 516 H552 L632 560 H864 L940 520 H1500" />
          <path class="login-circuit-pulse login-pulse-d" d="M-60 742 H320 L394 700 H686 L762 742 H1012 L1090 700 H1500" />
        </g>
        <g class="login-circuit-nodes">
          <circle class="login-circuit-node" cx="190" cy="92" r="4" />
          <circle class="login-circuit-node" cx="444" cy="48" r="4" />
          <circle class="login-circuit-node" cx="590" cy="148" r="4" />
          <circle class="login-circuit-node" cx="316" cy="206" r="4" />
          <circle class="login-circuit-node" cx="666" cy="248" r="4" />
          <circle class="login-circuit-node" cx="282" cy="516" r="4" />
          <circle class="login-circuit-node" cx="632" cy="560" r="4" />
          <circle class="login-circuit-node" cx="228" cy="620" r="4" />
          <circle class="login-circuit-node" cx="584" cy="664" r="4" />
          <circle class="login-circuit-node" cx="394" cy="700" r="4" />
          <circle class="login-circuit-node" cx="762" cy="742" r="4" />
          <circle class="login-circuit-node" cx="1090" cy="700" r="4" />
        </g>
      </svg>
      <div class="login-glow login-glow-primary absolute rounded-full bg-cyan-400/10 blur-3xl" />
      <div class="login-glow login-glow-secondary absolute rounded-full bg-sky-500/10 blur-3xl" />
      <svg class="login-network-globe" viewBox="0 0 400 400" fill="none">
        <circle cx="200" cy="200" r="170" />
        <ellipse cx="200" cy="200" rx="110" ry="170" />
        <ellipse cx="200" cy="200" rx="45" ry="170" />
        <ellipse cx="200" cy="200" rx="170" ry="65" />
        <path d="M40 140 H360 M40 260 H360 M30 200 H370 M200 30 V370" />
        <g class="login-network-points">
          <circle cx="90" cy="200" r="3" /><circle cx="155" cy="140" r="3" />
          <circle cx="245" cy="260" r="3" /><circle cx="310" cy="200" r="3" />
          <circle cx="200" cy="30" r="3" /><circle cx="200" cy="370" r="3" />
        </g>
      </svg>
    </div>

    <section class="login-layout relative z-10 mx-auto grid w-full max-w-6xl items-center gap-5 lg:grid-cols-[1.08fr_0.92fr]">
      <div class="login-hero animate-rise-in">
        <div class="login-brand flex items-center gap-3" qa-id="login-brand" data-testid="login-brand">
          <img
            src="@/assets/sinalyx-logo.png"
            alt="Logo Sinalyx"
            class="login-logo h-14 w-14 rounded-md object-contain"
          />
          <div>
            <p class="text-2xl font-semibold text-white">Sinalyx</p>
            <p class="text-sm text-slate-400">Plataforma de análise interpretável de logs</p>
          </div>
        </div>

        <div class="login-copy mt-6 max-w-2xl lg:mt-7">
            <p class="muted-label">Análise híbrida de logs de firewall</p>
          <h1 class="mt-3 text-3xl font-semibold leading-tight text-white sm:text-4xl xl:text-5xl">
            Análise híbrida de <span class="login-headline-accent">logs de firewall</span>
          </h1>
          <p class="login-copy-text mt-3 text-sm leading-6 text-slate-400 sm:text-base sm:leading-7">
            Analise padrões anômalos, classifique eventos de segurança e investigue decisões interpretáveis a partir de logs reais do pfSense.
          </p>
        </div>

        <div class="login-chips mt-5 flex flex-wrap gap-2">
          <span v-for="(chip, index) in chips" :key="chip" class="login-chip">
            <component :is="chipIcons[index]" class="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            {{ chip }}
          </span>
        </div>

        <div class="login-analysis-widget mt-8">
          <div class="flex items-center justify-between">
            <p class="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200">
              Processamento de logs
            </p>
            <span class="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-cyan-100">
              TCC
            </span>
          </div>
          <div class="login-bars mt-5" aria-hidden="true">
            <span v-for="(bar, index) in analysisBars" :key="index" :style="{ '--bar-height': `${bar}%` }" />
          </div>
          <div class="login-processing-flow mt-4 flex items-center justify-between text-[11px] text-slate-300">
            <span>logs</span>
            <span class="login-flow-line" aria-hidden="true" />
            <span>análise</span>
            <span class="login-flow-line" aria-hidden="true" />
            <span>resultado</span>
          </div>
        </div>

        <div class="login-preview-grid mt-6 grid gap-4 md:grid-cols-[0.95fr_1.05fr]">
          <div class="panel border-cyan-400/20 bg-surface-900/75 p-4">
            <div class="mb-4 flex items-center justify-between">
              <div>
                <p class="text-sm font-semibold text-white">Pipeline de análise</p>
                <p class="text-xs text-slate-500">Validação em laboratório com pfSense</p>
              </div>
              <ShieldCheck class="h-5 w-5 text-cyan-200" />
            </div>
            <div class="space-y-3">
              <div v-for="step in pipeline" :key="step.label" class="flex items-center gap-3">
                <span class="h-2 w-2 rounded-full" :class="step.color" />
                <span class="text-sm text-slate-300">{{ step.label }}</span>
              </div>
            </div>
          </div>

          <div class="panel overflow-hidden border-sky-400/20 bg-surface-900/75">
            <div class="flex items-center gap-2 border-b border-slate-800 px-4 py-3 text-xs text-slate-500">
              <Terminal class="h-4 w-4 text-sky-300" />
              sinalyx-analysis.preview
            </div>
            <div class="space-y-3 p-4 font-mono text-xs">
              <div v-for="line in consoleLines" :key="line" class="console-line text-slate-300">
                {{ line }}
              </div>
            </div>
            <div class="grid grid-cols-3 gap-2 border-t border-slate-800 p-4">
              <div class="rounded-md border border-slate-800 bg-surface-850 p-3">
                <p class="text-[11px] text-slate-500">Eventos</p>
                <p class="mt-1 text-sm font-semibold text-white">pfSense</p>
              </div>
              <div class="rounded-md border border-cyan-400/20 bg-cyan-400/10 p-3">
                <p class="text-[11px] text-cyan-200/80">Decisão</p>
                <p class="mt-1 text-sm font-semibold text-cyan-100">Auditável</p>
              </div>
              <div class="rounded-md border border-emerald-400/20 bg-emerald-400/10 p-3">
                <p class="text-[11px] text-emerald-200/80">Status</p>
                <p class="mt-1 text-sm font-semibold text-emerald-100">Consulta</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <form
        class="login-card panel mx-auto w-full max-w-md animate-rise-in space-y-3 border-cyan-400/30 bg-surface-900/[0.85] p-5 shadow-[0_28px_90px_rgba(8,145,178,0.2)] backdrop-blur-xl sm:p-6 lg:max-w-none"
        qa-id="login-form"
        data-testid="login-form"
        data-qa-section="auth"
        @submit.prevent="handleLogin"
      >
        <div class="pointer-events-none absolute inset-x-5 top-0 h-px bg-gradient-to-r from-transparent via-cyan-300/80 to-transparent" />

        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-xs font-medium uppercase tracking-wide text-cyan-200">Acesso restrito</p>
            <h2 class="mt-1 text-xl font-semibold text-white">Entrar no painel</h2>
          </div>
          <span class="inline-flex items-center gap-2 rounded-md border border-emerald-400/25 bg-emerald-400/10 px-2.5 py-1 text-xs font-medium text-emerald-100">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_12px_rgba(110,231,183,0.75)]" />
            Painel
          </span>
        </div>

        <p class="text-sm leading-6 text-slate-400">
          Autentique-se para acessar o painel operacional, histórico e investigações.
        </p>

        <div class="login-signals grid grid-cols-3 gap-2">
          <div v-for="item in loginSignals" :key="item.label" class="rounded-md border border-slate-800 bg-surface-850/80 p-2">
            <p class="text-[10px] uppercase tracking-wide text-slate-500">{{ item.label }}</p>
            <p class="mt-1 text-xs font-semibold text-slate-100">{{ item.value }}</p>
          </div>
        </div>

        <label class="block text-sm">
          <span class="text-slate-300">Email</span>
          <span class="relative mt-2 block">
            <Mail class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              v-model="email"
              class="field h-10 w-full pl-10 pr-3 sm:h-11"
              type="email"
              name="email"
              qa-id="login-email"
              data-testid="login-email"
              aria-label="Email de acesso"
              autocomplete="username"
              placeholder="email@sinalyx.local"
              required
            />
          </span>
        </label>

        <label class="block text-sm">
          <span class="text-slate-300">Senha</span>
          <span class="relative mt-2 block">
            <Lock class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              v-model="password"
              class="field h-10 w-full pl-10 pr-11 sm:h-11"
              :type="showPassword ? 'text' : 'password'"
              name="password"
              qa-id="login-password"
              data-testid="login-password"
              aria-label="Senha de acesso"
              autocomplete="current-password"
              placeholder="Digite sua senha"
              required
            />
            <button
              class="focus-ring absolute right-2 top-1/2 grid h-8 w-8 -translate-y-1/2 place-items-center rounded-md text-slate-500 transition hover:bg-surface-800 hover:text-sky-200"
              type="button"
              :aria-label="showPassword ? 'Ocultar senha' : 'Mostrar senha'"
              @click="showPassword = !showPassword"
            >
              <EyeOff v-if="showPassword" class="h-4 w-4" />
              <Eye v-else class="h-4 w-4" />
            </button>
          </span>
        </label>

        <p
          v-if="error"
          class="rounded-md border border-red-400/20 bg-red-400/10 px-3 py-2 text-sm text-red-200"
          qa-id="login-error"
          data-testid="login-error"
          role="alert"
        >
          {{ error }}
        </p>

        <button
          class="btn btn-primary h-10 w-full sm:h-11"
          type="submit"
          qa-id="login-submit"
          data-testid="login-submit"
          aria-label="Entrar no painel"
          :disabled="loading"
        >
          <Activity v-if="loading" class="h-4 w-4 animate-spin" />
          {{ loading ? 'Entrando...' : 'Entrar' }}
        </button>
      </form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { Activity, Eye, EyeOff, Lock, Mail, ShieldCheck, Terminal, ChartNoAxesCombined, FileCheck } from 'lucide-vue-next'
import { onMounted, onUnmounted, ref } from 'vue'
import { useLoginForm } from '@/composables/useLoginForm'

const { email, password, showPassword, loading, error, handleLogin } = useLoginForm()

const chips = ['Análise combinada', 'Logs pfSense', 'Análise interpretável', 'Validação acadêmica']
const chipIcons = [Activity, ShieldCheck, ChartNoAxesCombined, FileCheck]
const loginSignals = [
  { label: 'Modo', value: 'Validação acadêmica' },
  { label: 'Dados', value: 'pfSense' },
  { label: 'Decisão', value: 'Auditável' },
]
const binaryRows = [
  '01001011 11001010 00101101',
  '10110100 00110111 01010010',
  '00101110 11100010 10010100',
  '11010011 01000101 01101001',
  '01100110 10101010 00011101',
  '10010110 01011001 11100100',
]
const backgroundLogs = [
  'pfSense: origem dos registros',
  'firewall: contexto dos eventos',
  'janela: 13 características',
  'modelo de anomalia: sinal complementar',
  'análise estatística: sinal complementar',
  'motor de decisão: resultado interpretável',
  'sinais combinados: análise híbrida',
  'protocolo SSH: contexto do tráfego',
]
const baseAnalysisBars = [34, 52, 26, 68, 44, 31, 74, 58, 39, 62, 82, 48, 70, 86, 55, 42, 66, 78, 50, 36]
const analysisBars = ref([...baseAnalysisBars])
let analysisAnimationTimer: number | undefined
let analysisAnimationStep = 0
const pipeline = [
  { label: 'Entrada e parser de logs', color: 'bg-sky-400' },
  { label: 'Janelas agregadas e indicadores', color: 'bg-cyan-400' },
  { label: 'Sinais de modelos e heurística', color: 'bg-amber-400' },
  { label: 'Classificação interpretável', color: 'bg-emerald-400' },
]
const consoleLines = [
  'entrada: logs do pfSense',
  'janela: organização de características',
  'análise: sinais combinados',
  'resultado: classificação interpretável',
]

onMounted(() => {
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
  analysisAnimationTimer = window.setInterval(() => {
    analysisAnimationStep += 1
    analysisBars.value = baseAnalysisBars.map((bar, index) => {
      const wave = Math.sin(analysisAnimationStep * 0.85 + index * 0.72)
      const offset = index % 3 === 0 ? 5 : index % 3 === 1 ? -3 : 1
      return Math.max(18, Math.min(92, Math.round(bar + wave * 18 + offset)))
    })
  }, 620)
})

onUnmounted(() => {
  if (analysisAnimationTimer !== undefined) {
    window.clearInterval(analysisAnimationTimer)
  }
})

</script>

<style scoped>
.login-layout {
  min-height: calc(100svh - 2rem);
  max-width: min(78rem, calc(100vw - 2rem));
}

.login-scene {
  background:
    radial-gradient(circle at 20% 18%, rgba(6, 182, 212, 0.12), transparent 30%),
    radial-gradient(circle at 84% 78%, rgba(14, 165, 233, 0.12), transparent 32%),
    linear-gradient(135deg, #020817 0%, #04111f 48%, #071a2e 100%);
}

.login-background {
  opacity: 0.92;
  isolation: isolate;
}

.login-background::before {
  content: "";
  position: absolute;
  inset: -20%;
  background:
    linear-gradient(120deg, transparent 20%, rgba(56, 189, 248, 0.035), transparent 38%),
    linear-gradient(45deg, transparent 46%, rgba(14, 165, 233, 0.035) 48%, transparent 52%);
  animation: login-drift 34s linear infinite;
  z-index: 0;
}

.login-background::after {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 30% 52%, rgba(2, 8, 23, 0.34), transparent 28%),
    radial-gradient(circle at 73% 50%, rgba(2, 8, 23, 0.48), transparent 25%),
    linear-gradient(90deg, rgba(2, 8, 23, 0.5) 0%, rgba(2, 8, 23, 0.18) 42%, rgba(2, 8, 23, 0.3) 62%, rgba(2, 8, 23, 0.58) 100%);
  z-index: 2;
}

.login-background .cyber-grid {
  opacity: 0.32 !important;
  z-index: 1;
}

.login-scan {
  background:
    linear-gradient(115deg, transparent 18%, rgba(56, 189, 248, 0.07) 24%, transparent 31%),
    radial-gradient(circle at 30% 24%, rgba(34, 211, 238, 0.14), transparent 28%),
    radial-gradient(circle at 78% 70%, rgba(16, 185, 129, 0.08), transparent 30%);
  filter: blur(0.3px);
  opacity: 0.5;
  animation: login-scan-drift 42s ease-in-out infinite alternate;
  z-index: 1;
}

.login-particles {
  overflow: hidden;
  z-index: 1;
}

.login-particles span {
  position: absolute;
  width: 2.5px;
  height: 2.5px;
  border-radius: 999px;
  background: rgba(125, 211, 252, 0.46);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.36);
  animation: login-particle 22s ease-in-out infinite;
}

.login-particles span:nth-child(1) { left: 6%; top: 18%; animation-delay: -1s; }
.login-particles span:nth-child(2) { left: 14%; top: 74%; animation-delay: -4s; }
.login-particles span:nth-child(3) { left: 24%; top: 42%; animation-delay: -8s; }
.login-particles span:nth-child(4) { left: 38%; top: 13%; animation-delay: -2s; }
.login-particles span:nth-child(5) { left: 46%; top: 68%; animation-delay: -7s; }
.login-particles span:nth-child(6) { left: 55%; top: 29%; animation-delay: -5s; }
.login-particles span:nth-child(7) { left: 64%; top: 82%; animation-delay: -9s; }
.login-particles span:nth-child(8) { left: 72%; top: 20%; animation-delay: -3s; }
.login-particles span:nth-child(9) { left: 80%; top: 54%; animation-delay: -6s; }
.login-particles span:nth-child(10) { left: 90%; top: 32%; animation-delay: -10s; }
.login-particles span:nth-child(11) { left: 18%; top: 24%; animation-delay: -11s; }
.login-particles span:nth-child(12) { left: 33%; top: 84%; animation-delay: -12s; }
.login-particles span:nth-child(13) { left: 68%; top: 10%; animation-delay: -13s; }
.login-particles span:nth-child(14) { left: 95%; top: 76%; animation-delay: -14s; }

.login-code-rain {
  overflow: hidden;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  z-index: 1;
}

.login-code-rain span {
  position: absolute;
  top: -18%;
  color: rgba(125, 211, 252, 0.12);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-shadow: 0 0 10px rgba(56, 189, 248, 0.16);
  writing-mode: vertical-rl;
  animation: binary-fall 42s linear infinite;
}

.login-code-rain span:nth-child(1) { left: 8%; animation-delay: -2s; }
.login-code-rain span:nth-child(2) { left: 22%; animation-delay: -12s; animation-duration: 48s; }
.login-code-rain span:nth-child(3) { left: 43%; animation-delay: -6s; animation-duration: 44s; }
.login-code-rain span:nth-child(4) { left: 62%; animation-delay: -16s; animation-duration: 52s; }
.login-code-rain span:nth-child(5) { left: 78%; animation-delay: -9s; animation-duration: 46s; }
.login-code-rain span:nth-child(6) { left: 92%; animation-delay: -20s; animation-duration: 54s; }

.login-log-stream {
  overflow: hidden;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  mask-image: linear-gradient(to right, transparent 0%, black 10%, black 90%, transparent 100%);
  opacity: 0.36;
  z-index: 1;
}

.login-log-stream span {
  position: absolute;
  top: var(--log-top);
  left: 0;
  width: max-content;
  padding: 0.2rem 0.55rem;
  border: 1px solid rgba(34, 211, 238, 0.11);
  border-radius: 999px;
  background: rgba(3, 7, 17, 0.32);
  color: rgba(125, 211, 252, 0.44);
  font-size: 0.68rem;
  line-height: 1.35;
  text-shadow: 0 0 12px rgba(56, 189, 248, 0.16);
  transform: translate3d(var(--log-start), 0, 0);
  animation: log-stream-x var(--log-speed) linear infinite;
  animation-delay: var(--log-delay);
  will-change: transform, opacity;
}

.login-log-stream span:nth-child(1) { --log-top: 15%; --log-start: 108vw; --log-speed: 44s; --log-delay: -2s; }
.login-log-stream span:nth-child(2) { --log-top: 30%; --log-start: -80vw; --log-speed: 48s; --log-delay: -9s; animation-name: log-stream-x-reverse; }
.login-log-stream span:nth-child(3) { --log-top: 46%; --log-start: 112vw; --log-speed: 42s; --log-delay: -6s; }
.login-log-stream span:nth-child(4) { --log-top: 62%; --log-start: -76vw; --log-speed: 52s; --log-delay: -15s; animation-name: log-stream-x-reverse; }
.login-log-stream span:nth-child(5) { --log-top: 77%; --log-start: 114vw; --log-speed: 46s; --log-delay: -12s; }
.login-log-stream span:nth-child(6) { --log-top: 88%; --log-start: -82vw; --log-speed: 54s; --log-delay: -18s; animation-name: log-stream-x-reverse; }
.login-log-stream span:nth-child(7) { --log-top: 9%; --log-start: 116vw; --log-speed: 50s; --log-delay: -20s; }
.login-log-stream span:nth-child(8) { --log-top: 94%; --log-start: -78vw; --log-speed: 45s; --log-delay: -4s; animation-name: log-stream-x-reverse; }

.login-circuit-layer {
  width: 100%;
  height: 100%;
  opacity: 0.54;
  filter: drop-shadow(0 0 10px rgba(34, 211, 238, 0.18));
  z-index: 1;
}

.login-circuit-trace,
.login-circuit-pulse {
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  vector-effect: non-scaling-stroke;
}

.login-circuit-trace {
  stroke: rgba(103, 232, 249, 0.28);
  stroke-width: 0.9;
  stroke-dasharray: 12 20;
  animation: login-circuit-flow 38s linear infinite;
}

.login-circuit-pulse {
  stroke: rgba(34, 211, 238, 0.58);
  stroke-width: 1.45;
  stroke-dasharray: 1 320;
  opacity: 0.42;
  animation: login-circuit-pulse 24s linear infinite;
}

.login-circuit-trace-b,
.login-circuit-trace-e {
  animation-duration: 44s;
  opacity: 0.62;
}

.login-circuit-trace-c,
.login-circuit-trace-f {
  animation-duration: 34s;
  opacity: 0.48;
}

.login-pulse-b { animation-delay: -8s; animation-duration: 28s; }
.login-pulse-c { animation-delay: -15s; animation-duration: 26s; }
.login-pulse-d { animation-delay: -11s; animation-duration: 30s; }

.login-circuit-node {
  fill: rgba(34, 211, 238, 0.62);
  filter: drop-shadow(0 0 7px rgba(34, 211, 238, 0.5));
  transform-box: fill-box;
  transform-origin: center;
  animation: login-node-pulse 7s ease-in-out infinite;
}

.login-circuit-node:nth-child(3n) {
  animation-delay: -1s;
}

.login-circuit-node:nth-child(3n + 1) {
  animation-delay: -1.8s;
}

.login-glow-primary {
  left: 50%;
  top: -2rem;
  width: 26rem;
  height: 26rem;
  background: rgba(6, 182, 212, 0.12);
  transform: translateX(-50%);
  animation: glow-primary-drift 30s ease-in-out infinite alternate;
}

.login-glow-secondary {
  right: -8rem;
  bottom: -12rem;
  width: 30rem;
  height: 30rem;
  background: rgba(14, 165, 233, 0.1);
  animation: glow-secondary-drift 34s ease-in-out infinite alternate;
}

.login-logo {
  filter: drop-shadow(0 0 18px rgba(56, 189, 248, 0.2));
  animation: logo-pulse 3.5s ease-in-out infinite;
}

.login-chip {
  @apply rounded-md border border-cyan-400/25 bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-100 transition hover:border-cyan-300/50 hover:bg-cyan-400/[0.15];
}

.login-bg-card {
  position: absolute;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  max-width: min(22rem, 32vw);
  border: 1px solid rgba(34, 211, 238, 0.12);
  border-radius: 0.5rem;
  background: rgba(2, 8, 23, 0.28);
  padding: 1rem 1.15rem;
  color: rgba(125, 211, 252, 0.46);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-size: 0.72rem;
  line-height: 1.35;
  opacity: 0.52;
  backdrop-filter: blur(2px);
  box-shadow: 0 0 38px rgba(6, 182, 212, 0.06);
}

.login-bg-card p {
  margin-bottom: 0.25rem;
  color: rgba(34, 211, 238, 0.72);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.login-bg-card strong {
  color: rgba(34, 211, 238, 0.58);
  font-weight: 700;
}

.login-bg-status span {
  display: flex;
  justify-content: space-between;
  gap: 2rem;
}

.login-bg-log {
  left: 2.4rem;
  top: 2.4rem;
}

.login-bg-status {
  right: 2.6rem;
  top: 2.7rem;
}

.login-bg-event {
  right: 3rem;
  bottom: 2.4rem;
}

.login-card {
  position: relative;
  border-radius: 0.375rem;
  border-color: rgba(34, 211, 238, 0.22) !important;
  background: rgba(2, 8, 23, 0.9) !important;
  animation-delay: 80ms;
  box-shadow:
    0 28px 90px rgba(2, 8, 23, 0.62),
    0 0 0 1px rgba(34, 211, 238, 0.08),
    0 0 42px rgba(8, 145, 178, 0.14) !important;
}

.login-analysis-widget {
  width: min(19rem, 100%);
  border: 1px solid rgba(34, 211, 238, 0.18);
  border-radius: 0.5rem;
  background:
    linear-gradient(180deg, rgba(2, 8, 23, 0.54), rgba(2, 8, 23, 0.74)),
    radial-gradient(circle at 50% 100%, rgba(6, 182, 212, 0.16), transparent 58%);
  padding: 1.1rem 1.25rem;
  box-shadow:
    0 16px 60px rgba(2, 8, 23, 0.34),
    inset 0 0 0 1px rgba(125, 211, 252, 0.04);
  backdrop-filter: blur(10px);
}

.login-bars {
  display: flex;
  height: 4.7rem;
  align-items: end;
  gap: 0.24rem;
  border-bottom: 1px solid rgba(34, 211, 238, 0.18);
  background:
    repeating-linear-gradient(to top, rgba(34, 211, 238, 0.06) 0 1px, transparent 1px 0.85rem);
}

.login-bars span {
  flex: 1 1 0;
  min-width: 0.32rem;
  height: var(--bar-height);
  border-radius: 0.16rem 0.16rem 0 0;
  background: linear-gradient(180deg, rgba(34, 211, 238, 0.95), rgba(14, 165, 233, 0.28));
  box-shadow: 0 0 12px rgba(34, 211, 238, 0.18);
  opacity: 0.9;
  transform-origin: bottom;
  transition: height 520ms ease-in-out, opacity 260ms ease, transform 520ms ease-in-out;
  animation: login-bar-breathe 1.6s ease-in-out infinite alternate;
}

.login-bars span:nth-child(3n) {
  animation-delay: -1.2s;
}

.login-bars span:nth-child(4n) {
  animation-delay: -2.1s;
}

.login-preview-grid {
  display: none !important;
}

@media (min-width: 1024px) and (max-height: 760px) {
  .login-layout {
    min-height: calc(100svh - 2rem);
    gap: clamp(2rem, 5vw, 4rem);
  }

  .login-logo {
    width: 3rem;
    height: 3rem;
  }

  .login-copy {
    margin-top: 1.25rem;
  }

  .login-copy h1 {
    max-width: 38rem;
    font-size: clamp(2.1rem, 3.2vw, 2.8rem);
    line-height: 1.08;
  }

  .login-copy-text {
    max-width: 39rem;
    line-height: 1.55;
  }

  .login-chips,
  .login-analysis-widget {
    margin-top: 1rem;
  }

  .login-analysis-widget {
    width: min(18rem, 100%);
    padding: 0.9rem 1rem;
  }

  .login-bars {
    height: 3.3rem;
  }

  .login-card {
    padding: 1.25rem;
  }
}

@media (min-width: 1024px) and (max-height: 660px) {
  .login-copy h1 {
    font-size: clamp(1.9rem, 2.8vw, 2.35rem);
  }

  .login-signals {
    display: none;
  }

  .login-analysis-widget {
    margin-top: 0.9rem;
  }
}

@media (max-width: 767px) {
  .login-layout {
    min-height: auto;
  }

  .login-bg-card {
    display: none;
  }

  .login-analysis-widget {
    width: 100%;
  }
}

@media (min-width: 1024px) {
  .login-layout {
    grid-template-columns: minmax(0, 1.08fr) minmax(24rem, 0.92fr);
    gap: clamp(3rem, 7vw, 7rem);
  }
}

@media (max-width: 1120px) {
  .login-bg-card {
    opacity: 0.38;
  }
}

@media (max-height: 820px) and (min-width: 900px) {
  .login-bg-log {
    display: none;
  }
}

.console-line {
  opacity: 0;
  animation: console-line 420ms ease-out both;
}

.console-line:nth-child(2) {
  animation-delay: 120ms;
}

.console-line:nth-child(3) {
  animation-delay: 240ms;
}

.console-line:nth-child(4) {
  animation-delay: 360ms;
}

@keyframes login-drift {
  from {
    transform: translate3d(-2%, -1%, 0);
  }
  to {
    transform: translate3d(2%, 1%, 0);
  }
}

@keyframes login-scan-drift {
  from {
    transform: translate3d(-2%, -1%, 0) scale(1);
  }
  to {
    transform: translate3d(2%, 1%, 0) scale(1.03);
  }
}

@keyframes login-particle {
  0%,
  100% {
    opacity: 0.14;
    transform: translate3d(0, 0, 0) scale(0.8);
  }
  50% {
    opacity: 0.38;
    transform: translate3d(12px, -16px, 0) scale(1.08);
  }
}

@keyframes binary-fall {
  0% {
    opacity: 0;
    transform: translate3d(0, -10%, 0);
  }
  12% {
    opacity: 0.22;
  }
  84% {
    opacity: 0.14;
  }
  100% {
    opacity: 0;
    transform: translate3d(0, 128vh, 0);
  }
}

@keyframes log-stream-x {
  0% {
    opacity: 0;
    transform: translate3d(112vw, 0, 0);
  }
  9% {
    opacity: 0.28;
  }
  72% {
    opacity: 0.16;
  }
  100% {
    opacity: 0;
    transform: translate3d(-132vw, 0, 0);
  }
}

@keyframes log-stream-x-reverse {
  0% {
    opacity: 0;
    transform: translate3d(-92vw, 0, 0);
  }
  10% {
    opacity: 0.24;
  }
  70% {
    opacity: 0.16;
  }
  100% {
    opacity: 0;
    transform: translate3d(128vw, 0, 0);
  }
}

@keyframes login-circuit-flow {
  0% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: -300;
  }
}

@keyframes login-circuit-pulse {
  0% {
    opacity: 0;
    stroke-dashoffset: 280;
  }
  8% {
    opacity: 0.32;
  }
  58% {
    opacity: 0.22;
  }
  100% {
    opacity: 0;
    stroke-dashoffset: -460;
  }
}

@keyframes login-node-pulse {
  0%, 100% {
    opacity: 0.28;
    transform: scale(0.82);
  }
  48% {
    opacity: 0.68;
    transform: scale(1.18);
  }
}

@keyframes glow-primary-drift {
  from {
    opacity: 0.48;
    transform: translate3d(-54%, -2%, 0) scale(0.96);
  }
  to {
    opacity: 0.72;
    transform: translate3d(-46%, 7%, 0) scale(1.08);
  }
}

@keyframes glow-secondary-drift {
  from {
    opacity: 0.42;
    transform: translate3d(0, 0, 0) scale(0.96);
  }
  to {
    opacity: 0.68;
    transform: translate3d(-9%, -7%, 0) scale(1.08);
  }
}

@keyframes logo-pulse {
  0%,
  100% {
    filter: drop-shadow(0 0 14px rgba(56, 189, 248, 0.16));
  }
  50% {
    filter: drop-shadow(0 0 24px rgba(56, 189, 248, 0.3));
  }
}

@keyframes login-bar-breathe {
  from {
    opacity: 0.72;
    transform: scaleY(0.62) translateY(2px);
  }
  55% {
    opacity: 1;
    transform: scaleY(1.08) translateY(0);
  }
  to {
    opacity: 0.86;
    transform: scaleY(0.82) translateY(1px);
  }
}

@keyframes console-line {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-headline-accent {
  color: #7dd3fc;
  background: linear-gradient(110deg, #a5f3fc, #7dd3fc 65%, #93c5fd);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.login-copy h1 { letter-spacing: -0.025em; }

.login-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.1), rgba(15, 23, 42, 0.75));
  box-shadow: inset 0 1px 0 rgba(165, 243, 252, 0.06);
}

.login-network-globe {
  position: absolute;
  right: -9rem;
  top: 24%;
  width: min(40rem, 52vw);
  height: auto;
  stroke: #7dd3fc;
  stroke-width: 0.8;
  opacity: 0.12;
  transform: rotate(-18deg);
  z-index: 1;
}
.login-network-points { fill: #a5f3fc; }
.login-circuit-layer { opacity: 0.62; }

.login-analysis-widget {
  border-color: rgba(125, 211, 252, 0.25);
  box-shadow: 0 12px 32px rgba(2, 8, 23, 0.3), inset 0 1px 0 rgba(165, 243, 252, 0.08);
}
.login-processing-flow { gap: 0.5rem; }
.login-flow-line {
  position: relative;
  flex: 1;
  height: 1px;
  overflow: hidden;
  background: rgba(125, 211, 252, 0.2);
}
.login-flow-line::after {
  content: '';
  position: absolute;
  width: 30%;
  height: 100%;
  background: #a5f3fc;
  animation: login-signal-travel 4s linear infinite;
}
@keyframes login-signal-travel {
  from { transform: translateX(-100%); }
  to { transform: translateX(440%); }
}

.login-card {
  border-color: rgba(125, 211, 252, 0.3) !important;
  background: linear-gradient(150deg, rgba(10, 25, 42, 0.96), rgba(2, 8, 23, 0.92)) !important;
}
.login-card .field {
  border-color: rgba(100, 116, 139, 0.5);
  background: rgba(2, 8, 23, 0.65);
}
.login-card .field:focus {
  border-color: #7dd3fc;
  box-shadow: 0 0 0 2px rgba(125, 211, 252, 0.16);
  outline: none;
}
.login-card .btn-primary {
  background: linear-gradient(110deg, #38bdf8, #67e8f9);
  color: #082f49;
  border: 1px solid rgba(165, 243, 252, 0.45);
}
.login-card .btn-primary:hover:not(:disabled) {
  background: linear-gradient(110deg, #7dd3fc, #a5f3fc);
}

@media (prefers-reduced-motion: reduce) {
  .login-scene *,
  .login-scene *::before,
  .login-scene *::after {
    animation: none !important;
    transition: none !important;
  }

  .console-line {
    opacity: 1;
  }
}
</style>
