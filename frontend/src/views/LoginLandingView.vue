<template>
  <main class="entrada-page" qa-id="page-login" data-testid="page-login" data-qa-page="login">
    <div class="entrada-shell" data-testid="login-landing">
      <section class="entrada-access" aria-labelledby="entrada-titulo">
        <div class="entrada-access-content">
          <div class="entrada-brand" qa-id="login-brand" data-testid="login-brand">
            <img src="@/assets/sinalyx-logo.png" alt="Logo Sinalyx" width="80" height="80" />
            <div><p class="entrada-brand-name">Sinalyx</p><p class="entrada-brand-description">Análise de logs de firewall</p></div>
          </div>
          <h1 id="entrada-titulo">Bem vindo!</h1>
          <p class="entrada-intro">Entre com sua conta para acessar o sistema.</p>
          <LoginForm />
        </div>
      </section>
      <div class="entrada-showcase">
        <LoginHero />
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import LoginForm from '@/components/login/LoginForm.vue'
import LoginHero from '@/components/login/LoginHero.vue'
</script>

<style scoped>
/* Só a nova página pública dispensa o mínimo global, que recorta a margem quando há barra de rolagem em 320 px. */
:global(body:has(.entrada-page)) { min-width: 0; }
.entrada-page { --entrada-border: #293c52; color: #dbe7f4; background: #070e19; min-height: 100svh; }
.entrada-shell { display: grid; grid-template-columns: minmax(22rem, .42fr) minmax(0,.58fr); max-width: 120rem; min-height: 100svh; margin-inline: auto; }
.entrada-access { position: relative; display: flex; flex-direction: column; min-width: 0; padding: 2.25rem clamp(2rem,4vw,5rem); border-right: 1px solid var(--entrada-border); background: linear-gradient(155deg,#0b1728,#08111e 70%); }
.entrada-brand { display: flex; align-items: center; gap: .8rem; margin-bottom: 2.25rem; animation: entrada-in 450ms ease-out both; }
.entrada-brand img { flex-shrink: 0; width: 80px; height: 80px; object-fit: contain; }
.entrada-brand-name { color: #f3f7fc; font-size: 2rem; font-weight: 650; letter-spacing: -.035em; }
.entrada-brand-description { margin-top: .15rem; color: #9bb0c7; font-size: .875rem; }
.entrada-access-content { max-width: 25rem; width: 100%; margin: auto; padding-block: 2.5rem; animation: entrada-in 550ms ease-out both; }
h1 { color: #f4f7fc; font-size: clamp(1.875rem,2.5vw,2.65rem); font-weight: 600; letter-spacing: -.04em; line-height: 1.2; }
.entrada-intro { margin-block: 1rem 2rem; color: #a8b9cc; font-size: .875rem; line-height: 1.85; }
.entrada-showcase { display: flex; flex-direction: column; min-width: 0; background: #0b1b2e; }
.entrada-showcase :deep(.entrada-hero) { flex: 1; }
@keyframes entrada-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@media (min-width: 1024px) and (max-height: 820px) { .entrada-access { padding-block: 1.75rem; } }
@media (max-width: 1023px) { .entrada-shell { display: flex; flex-direction: column; min-height: auto; } .entrada-access { padding: 2.5rem max(1.5rem,calc((100vw - 28rem)/2)); border-right: 0; } .entrada-access-content { max-width: 28rem; margin: 0 auto; padding-block: 0; } }
@media (max-width: 479px) { .entrada-access { padding: 1.5rem 1.25rem 2rem; } .entrada-brand { margin-bottom: 1.75rem; } .entrada-brand img { width: 64px; height: 64px; } .entrada-brand-name { font-size: 1.75rem; } .entrada-brand-description { font-size: .75rem; } h1 { font-size: 1.875rem; } .entrada-intro { margin-block: .75rem 1.5rem; font-size: .8125rem; line-height: 1.75; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
</style>
