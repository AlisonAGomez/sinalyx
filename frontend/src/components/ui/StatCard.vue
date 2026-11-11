<!-- Indicador recebido da tela; a animação modifica somente sua apresentação. -->
<template>
  <article class="metric-card animate-rise-in">
    <div class="flex items-start justify-between gap-4">
      <div class="min-w-0">
        <p class="metric-label">{{ label }}</p>
        <p class="metric-value text-wrap-safe">{{ displayValue }}</p>
      </div>
      <div class="grid h-11 w-11 shrink-0 place-items-center rounded-2xl border shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]" :class="iconClass">
        <component :is="icon" class="h-5 w-5" />
      </div>
    </div>
    <p v-if="hint" class="mt-4 text-xs leading-5 text-slate-500">{{ hint }}</p>
  </article>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  label: string
  value: string | number
  hint?: string
  icon: Component
  iconClass?: string
}>()

const animatedValue = ref(0)
let animationFrame: number | null = null
const displayValue = computed(() => typeof props.value === 'number'
  ? Math.round(animatedValue.value).toLocaleString('pt-BR')
  : props.value)

/** Respeita a preferência do usuário por menos movimento na interface. */
function shouldReduceMotion(): boolean {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
}

/** Interrompe a animação anterior antes de iniciar outra ou remover o componente. */
function cancelAnimation(): void {
  if (animationFrame !== null) {
    window.cancelAnimationFrame(animationFrame)
    animationFrame = null
  }
}

/** Anima somente a apresentação do número; o indicador recebido não é recalculado. */
function animateNumber(target: number): void {
  cancelAnimation()
  if (shouldReduceMotion()) {
    animatedValue.value = target
    return
  }
  const start = animatedValue.value
  const startedAt = performance.now()
  const duration = 420
  /** Atualiza um quadro da animação até alcançar o valor recebido. */
  const tick = (now: number) => {
    const progress = Math.min(1, (now - startedAt) / duration)
    const eased = 1 - Math.pow(1 - progress, 3)
    animatedValue.value = start + (target - start) * eased
    if (progress < 1) animationFrame = window.requestAnimationFrame(tick)
    else animationFrame = null
  }
  animationFrame = window.requestAnimationFrame(tick)
}

watch(() => props.value, (value) => {
  if (typeof value === 'number') animateNumber(value)
})

onMounted(() => {
  if (typeof props.value === 'number') animateNumber(props.value)
})

onBeforeUnmount(cancelAnimation)
</script>
