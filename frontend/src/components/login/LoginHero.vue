<template>
  <section class="entrada-hero" aria-labelledby="entrada-proposta" data-testid="login-hero">
    <div class="entrada-ambiente" aria-hidden="true" />
    <!-- Ilustração original em SVG: representa infraestrutura, não dados ou atividade reais. -->
    <svg class="entrada-rede" viewBox="0 0 800 700" fill="none" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="entrada-metal" x1="300" y1="130" x2="750" y2="640" gradientUnits="userSpaceOnUse">
          <stop stop-color="#254462" /><stop offset="1" stop-color="#081627" />
        </linearGradient>
        <linearGradient id="entrada-borda" x1="350" y1="160" x2="690" y2="550" gradientUnits="userSpaceOnUse">
          <stop stop-color="#5ba7d9" stop-opacity=".65" /><stop offset="1" stop-color="#1f4770" stop-opacity=".12" />
        </linearGradient>
      </defs>
      <g class="entrada-equipamentos" transform="translate(40 0)">
        <path d="M400 145 664 231 664 568 400 483Z" fill="url(#entrada-metal)" stroke="url(#entrada-borda)" />
        <path d="M400 145 483 97 747 183 664 231Z" fill="#1a324c" stroke="#396081" stroke-opacity=".4" />
        <path d="M664 231 747 183 747 520 664 568Z" fill="#0a1829" stroke="#29445c" stroke-opacity=".6" />
        <g v-for="linha in 5" :key="linha" :transform="`translate(0 ${(linha - 1) * 59})`">
          <path d="M416 179 647 254 647 292 416 217Z" fill="#0a182a" stroke="#345572" stroke-opacity=".7" />
          <path d="M430 198 468 210M430 205 468 217" stroke="#43637e" stroke-width="2" />
          <path v-for="porta in 6" :key="porta" :d="`M${482 + porta * 21} ${215 + porta * 6.8}v9l12 4v-9Z`" fill="#1b3b57" stroke="#5e90ad" stroke-opacity=".45" />
          <circle cx="633" cy="269" r="2" fill="#47c5d9" opacity=".8" />
        </g>
        <path d="M511 349C429 343 445 457 342 483S234 562 128 548" stroke="#167deb" stroke-opacity=".55" stroke-width="4" />
        <path d="M552 423C463 420 506 509 406 541S326 615 204 611" stroke="#24b4cf" stroke-opacity=".45" stroke-width="3" />
      </g>
      <g class="entrada-trilhas" stroke="#3499d4" stroke-opacity=".22">
        <path d="M40 570C170 570 180 430 330 430S540 296 780 296" />
        <path d="M95 668C220 668 250 535 410 535S617 404 800 404" />
        <path d="M270 650C350 650 350 225 520 225S660 128 800 128" />
      </g>
      <g class="entrada-fluxo" stroke="#72d8f3" stroke-width="2" stroke-linecap="round">
        <path d="M40 570C170 570 180 430 330 430S540 296 780 296" />
        <path d="M95 668C220 668 250 535 410 535S617 404 800 404" />
        <path d="M270 650C350 650 350 225 520 225S660 128 800 128" />
      </g>
    </svg>
    <div class="entrada-hero-copy">
      <h2 id="entrada-proposta">Dos logs à <span>investigação.</span></h2>
      <p class="entrada-hero-description">O Sinalyx analisa registros de firewall e apresenta indícios de comportamentos suspeitos para apoiar a investigação de segurança.</p>
    </div>
    <p class="entrada-hero-caption">Projeto acadêmico — Sistemas de Informação 2026</p>
  </section>
</template>

<style scoped>
.entrada-hero { position: relative; isolation: isolate; display: flex; flex-direction: column; justify-content: center; min-width: 0; min-height: 42rem; padding: clamp(2rem,4vw,4.5rem); overflow: hidden; background: linear-gradient(135deg,#0b1b2e,#081421 60%,#0a1c30); }
.entrada-ambiente { position: absolute; z-index: -2; inset: 0; background: radial-gradient(ellipse at 80% 38%,#1261a333,transparent 60%),radial-gradient(ellipse at 95% 90%,#06b6d41c,transparent 50%); animation: entrada-luz 14s ease-in-out infinite alternate; }
.entrada-rede { position: absolute; z-index: -1; right: -9%; top: 3%; width: 100%; height: 100%; opacity: .64; pointer-events: none; animation: entrada-ilustracao 650ms ease-out both; }
.entrada-hero::after { content: ''; position: absolute; z-index: -1; inset: 0; background: linear-gradient(90deg,#08182bf5 0%,#08182be8 26%,#08182b9c 57%,#08182b05 100%); pointer-events: none; }
.entrada-hero-copy { max-width: 31rem; animation: entrada-copy 600ms ease-out both; }
h2 { max-width: 11em; color: #f1f7ff; font-size: clamp(2rem,3.25vw,3.5rem); line-height: 1.15; font-weight: 600; letter-spacing: -.045em; text-wrap: balance; }
h2 span { color: #55d4e8; }
.entrada-hero-description { max-width: 28rem; margin-top: 1.35rem; color: #b0c1d3; font-size: .95rem; line-height: 1.8; }
.entrada-hero-caption { position: absolute; bottom: 2rem; left: clamp(2rem,4vw,4.5rem); right: 1rem; display: flex; align-items: center; gap: .55rem; color: #93afc5; font-size: .6875rem; }
.entrada-fluxo path { stroke-dasharray: 3 1000; animation: entrada-dados 14s linear infinite; }
.entrada-fluxo path:nth-child(2) { animation-duration: 17s; animation-delay: -7s; }
.entrada-fluxo path:nth-child(3) { animation-duration: 12s; animation-delay: -4s; }
@keyframes entrada-dados { from { stroke-dashoffset: 1000; } to { stroke-dashoffset: 0; } }
@keyframes entrada-luz { from { opacity: .55; transform: translate3d(-1%,0,0); } to { opacity: 1; transform: translate3d(1%,1%,0); } }
@keyframes entrada-copy { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes entrada-ilustracao { from { opacity: .2; transform: translateX(12px); } to { opacity: .64; transform: translateX(0); } }
@media (max-width: 1023px) { .entrada-hero { min-height: 28rem; padding: 3rem 2rem 5rem; border-top: 1px solid #293d53; } h2 { font-size: clamp(2rem,5vw,2.75rem); } .entrada-rede { right: -18%; width: 80%; } .entrada-hero-copy { max-width: 32rem; } }
@media (max-width: 479px) { .entrada-hero { min-height: auto; padding: 2.5rem 1.25rem 5rem; } .entrada-rede { top: 5%; right: -26%; width: 110%; opacity: .35; } .entrada-hero::after { background: linear-gradient(90deg,#08182bf5,#08182bb5 65%,#08182b66); } .entrada-hero-caption { left: 1.25rem; bottom: 1.75rem; font-size: .625rem; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
</style>
