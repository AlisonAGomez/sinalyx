<template>
  <form class="entrada-form" :aria-busy="loading" @submit.prevent="handleLogin">
    <div>
      <label for="entrada-email">E-mail</label>
      <div class="entrada-input-wrap">
        <Mail aria-hidden="true" class="entrada-input-icon" />
        <input id="entrada-email" v-model="email" class="field entrada-input" type="email" name="email"
          qa-id="login-email" data-testid="login-email" aria-label="Email de acesso" autocomplete="username"
          placeholder="seu@email.com" :aria-describedby="error ? 'entrada-erro' : undefined" required />
      </div>
    </div>
    <div>
      <label for="entrada-senha">Senha</label>
      <div class="entrada-input-wrap">
        <Lock aria-hidden="true" class="entrada-input-icon" />
        <input id="entrada-senha" v-model="password" class="field entrada-input entrada-password"
          :type="showPassword ? 'text' : 'password'" name="password" qa-id="login-password" data-testid="login-password"
          aria-label="Senha de acesso" autocomplete="current-password" placeholder="Digite sua senha"
          :aria-describedby="error ? 'entrada-erro' : undefined" required />
        <button class="entrada-password-toggle" type="button" :aria-label="showPassword ? 'Ocultar senha' : 'Mostrar senha'"
          :aria-pressed="showPassword" @click="showPassword = !showPassword">
          <EyeOff v-if="showPassword" aria-hidden="true" /><Eye v-else aria-hidden="true" />
        </button>
      </div>
    </div>
    <p v-if="error" id="entrada-erro" class="entrada-error" role="alert" qa-id="login-error" data-testid="login-error">{{ error }}</p>
    <button class="entrada-submit" type="submit" qa-id="login-submit" data-testid="login-submit" aria-label="Entrar no painel" :disabled="loading">
      <LoaderCircle v-if="loading" class="entrada-spinner" aria-hidden="true" />
      {{ loading ? 'Entrando...' : 'Entrar' }}
      <ArrowRight v-if="!loading" aria-hidden="true" />
    </button>
    <p class="entrada-auth-note"><Lock aria-hidden="true" /> Acesso autenticado</p>
  </form>
</template>

<script setup lang="ts">
import { ArrowRight, Eye, EyeOff, LoaderCircle, Lock, Mail } from 'lucide-vue-next'
import { useLoginForm } from '@/composables/useLoginForm'

const { email, password, showPassword, loading, error, handleLogin } = useLoginForm()
</script>

<style scoped>
.entrada-form { display: grid; gap: 1.25rem; }
label { display: block; margin-bottom: .5rem; color: #dbe7f4; font-size: .875rem; font-weight: 500; }
.entrada-input-wrap { position: relative; }
.entrada-input { width: 100%; min-height: 3.25rem; padding: .75rem 1rem .75rem 2.8rem; background: #0b1626; border: 1px solid #35465b; border-radius: .75rem; color: #f1f5f9; transition: border-color 160ms, box-shadow 160ms; font-size: 1rem; }
.entrada-input::placeholder { color: #8a9bb0; }
.entrada-input:focus { outline: 2px solid #38bdf8; outline-offset: 2px; border-color: #38bdf8; box-shadow: none; }
.entrada-input-icon { position: absolute; left: 1rem; top: 1.05rem; width: 1.05rem; height: 1.05rem; color: #829ab4; pointer-events: none; }
.entrada-password { padding-right: 3.25rem; }
.entrada-password-toggle { position: absolute; right: .3rem; top: .25rem; display: grid; place-items: center; width: 2.75rem; height: 2.75rem; border-radius: .5rem; color: #9eafc3; transition: background-color 160ms, color 160ms; }
.entrada-password-toggle:hover { background: #17273d; color: #e2f7ff; }
.entrada-password-toggle:focus-visible, .entrada-submit:focus-visible { outline: 2px solid #67e8f9; outline-offset: 4px; }
.entrada-password-toggle svg { width: 1.1rem; height: 1.1rem; }
.entrada-submit { min-height: 3.25rem; display: flex; align-items: center; justify-content: center; gap: .75rem; padding: .8rem 1rem; border: 1px solid #2785ff; border-radius: .75rem; background: linear-gradient(105deg,#1064f6,#167be8); color: white; font-weight: 600; transition: background 160ms, border-color 160ms, box-shadow 160ms; }
.entrada-submit:hover:not(:disabled) { background: linear-gradient(105deg,#2375ff,#238cf0); border-color: #73baff; box-shadow: 0 5px 20px #1064f626; }
.entrada-submit:disabled { cursor: wait; opacity: .75; }
.entrada-submit svg { width: 1.1rem; height: 1.1rem; }
.entrada-error { padding: .8rem 1rem; border: 1px solid #b9506070; border-radius: .65rem; background: #551f2c40; color: #fecdd3; font-size: .875rem; line-height: 1.5; }
.entrada-auth-note { display: flex; align-items: center; justify-content: center; gap: .4rem; color: #9aadc2; font-size: .75rem; }
.entrada-auth-note svg { width: .8rem; height: .8rem; }
.entrada-spinner { animation: entrada-spin 800ms linear infinite; }
@keyframes entrada-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
</style>
