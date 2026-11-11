<!-- Título, descrição e ações de cabeçalho reutilizados nas telas. -->
<template>
  <div class="relative overflow-hidden rounded-2xl border border-slate-800/70 bg-slate-950/[0.18] px-5 py-5 sm:px-6">
    <div class="pointer-events-none absolute inset-y-0 left-0 w-px bg-gradient-to-b from-transparent via-sky-300/60 to-transparent" aria-hidden="true" />
    <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div class="min-w-0">
        <div class="flex flex-wrap items-center gap-2">
          <p v-if="eyebrow" class="muted-label text-sky-300/80">{{ eyebrow }}</p>
          <slot name="badge" />
        </div>
        <h1 class="mt-2 text-2xl font-semibold tracking-[-0.025em] text-white sm:text-[2rem] sm:leading-tight">{{ title }}</h1>
        <p v-if="description" class="mt-2 max-w-3xl text-sm leading-6 text-slate-400">{{ description }}</p>
      </div>
      <div v-if="$slots.actions" class="flex w-full flex-wrap gap-2 lg:w-auto lg:justify-end lg:pb-0.5">
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  eyebrow?: string
  title: string
  description?: string
}>()
</script>
