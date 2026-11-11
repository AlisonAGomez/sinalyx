# Entrada pública do Sinalyx

A rota pública continua sendo `/login`, com os mesmos guards e a mesma API.
O login integrado e a apresentação anterior compartilham `useLoginForm.ts`,
que chama o `useAuth` existente. Token, armazenamento de sessão, validação no
servidor e autorização não foram modificados.

## Escolher a apresentação

`VITE_SINALYX_NEW_LOGIN_LANDING` é uma opção **pública de compilação**:

- `true`: landing com autenticação integrada.
- `false`: layout anterior preservado em `LegacyLoginView.vue`.
- Valor inválido: layout anterior, como alternativa segura.
- Ausente: usa `NOVA_LANDING_PADRAO` em `src/config/loginLanding.ts`, atualmente `true`.

No PowerShell, para compilar localmente o login anterior:

```powershell
cd frontend
$env:VITE_SINALYX_NEW_LOGIN_LANDING = 'false'
npm run build
Remove-Item Env:VITE_SINALYX_NEW_LOGIN_LANDING
```

Para a landing, use `true`. Reinicie o servidor Vite após mudar sua configuração
de ambiente. A seleção não é uma opção de autorização e não deve conter segredos.

### Build Docker existente

O Dockerfile atual não possui ARG para essa nova variável e não copia arquivos
`.env` do frontend. Portanto, passar um novo build-arg ou editar `.env.local`
**não configura essa imagem**.

Sem alterar Dockerfile/Compose, o fallback pode ser selecionado pelo valor
`NOVA_LANDING_PADRAO = false` em `src/config/loginLanding.ts`, que é copiado junto
com o código. O valor é uma configuração de apresentação, não uma mudança na
autenticação. Depois é necessário reconstruir **somente o frontend**, no lote
de implantação autorizado. Para voltar à landing, selecionar `true` e recompilar.
Nenhum build ou reinício Docker foi executado pelo lote de desenvolvimento.

## Componentes

- `LoginView.vue`: seleciona a apresentação. O layout antigo é carregado sob demanda.
- `LoginLandingView.vue`: composição pública de acesso e identidade da marca.
- `LoginForm.vue`: campos, espera, erro e alternância de senha.
- `LoginHero.vue`: mensagem breve do projeto e ilustração de infraestrutura.
- `LegacyLoginView.vue`: template e CSS anteriores, com a lógica de envio compartilhada.

A entrada mostra somente o formulário, uma apresentação curta e a assinatura
acadêmica. Não possui menu, links ou seções institucionais abaixo da composição.
A página `Sobre` interna permanece acessível após autenticação, sem nova rota pública.

## Assets e movimento

A marca vem de `src/assets/sinalyx-logo.png`, fornecida pelo autor e já presente
no projeto; seu arquivo e proporções são preservados.

Não foi encontrada fotografia local com licença e proveniência registradas.
Foi escolhido o fallback autorizado: gradientes e SVG original do projeto,
sem fotografia, marcas de terceiros ou URLs externas. O Hero não depende de
download de imagem para apresentar seus textos, linhas e equipamentos abstratos.
Não se apresenta a ilustração como atividade real ou fotografia de infraestrutura.

As animações da nova landing usam somente CSS: entrada curta, três percursos
de dados com ciclos de 12–17 segundos e iluminação lenta. Não há timer que
atualize o estado Vue para decoração na nova landing.

Com `prefers-reduced-motion: reduce`, o movimento decorativo é desativado e o
conteúdo continua visível. Sem suporte a animações, o estado padrão também é
visível. Nenhuma ação depende de `animationend`. O layout antigo conserva seus
efeitos anteriores e a própria proteção para movimento reduzido.

## Limite do QA

Testes Vitest usam respostas sintéticas e validam os dois layouts, a sessão
existente e os guards. Não substituem login integrado com API/PostgreSQL reais.
O QA visual local deve ser registrado separadamente para 1920×1080, 1366×768,
768×1024, 390×844 e 320×568. A implantação e o QA Docker pertencem ao chat 06.
