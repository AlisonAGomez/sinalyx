<!-- A configuração altera somente a apresentação pública, sem mudar rotas ou permissões. -->
<template>
  <LoginLandingView v-if="novaLanding" />
  <LegacyLoginView v-else />
</template>

<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import { NOVA_LANDING_PADRAO } from '@/config/loginLanding'
import LoginLandingView from '@/views/LoginLandingView.vue'

const LegacyLoginView = defineAsyncComponent(() => import('@/views/LegacyLoginView.vue'))
const configurado = import.meta.env.VITE_SINALYX_NEW_LOGIN_LANDING
const novaLanding = configurado === undefined
  ? NOVA_LANDING_PADRAO
  : configurado.trim().toLowerCase() === 'true'
</script>
