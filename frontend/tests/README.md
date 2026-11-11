# Testes automatizados frontend — AUD-12

Status: contratos unitários, de componentes e router. Não substituem QA no
navegador, E2E com backend, autorização no servidor ou validação científica.

## Ambiente e execução

Node 20, 22 ou 24 compatível com Vitest/Vite; execução deste lote em Node 24.19.0.
O Docker frontend existente usa Node 20 e foi considerado na escolha das versões.
Dependências DEV fixadas: Vitest 4.1.12, Vue Test Utils 2.4.11,
jsdom 26.1.0 e tipos Node 20.19.43. As versões anteriores de produção/build
permanecem no lockfile. Não é necessário instalar ferramentas globalmente.

Em `frontend/`:

```powershell
npm ci
npm run test:run
npm run test:run -- --sequence.shuffle --sequence.seed=1206
npm run test:typecheck
npm run typecheck
npm run build
```

`npm test` abre o modo watch para desenvolvimento. `test:run` termina com exit
code adequado a automação; não inicia API ou frontend de desenvolvimento.
`test:typecheck` inclui fixtures, testes e configuração; o typecheck original
do produto permanece preservado. O build pode atualizar somente o `dist`
gerado/ignorado e não reconstrói imagens Docker.

Nenhum backend, PostgreSQL, Docker, log pfSense, modelo treinado ou credencial é
pré-requisito da suíte. Instalação exige npm/registry, mas executar os testes não
exige rede externa. A configuração de testes não carrega arquivos `.env` e usa
`/api` como base sintética. Fetch e envio XMLHttpRequest sem mock falham.

## Organização e isolamento

- `setup.ts`: desmontagem automática, limpeza de DOM/localStorage, restauração
  de mocks/timers, movimento reduzido e bloqueio de transportes não simulados.
- `fixtures/api.ts`: dados tipados/sintéticos e promessa controlada sem sleeps.
- `components/`: estados compartilhados, navegação e gráfico de janelas.
- `router/`: router/guards reais; só a resposta da consulta de sessão é simulada.
- `views/`: Login, Dashboard e Relatórios reais, com serviços HTTP simulados.
- `services/`: Axios/interceptors e envelopes reais com adapter em memória.

Os testes de formulário inválido usam a validação HTML do jsdom. Isso não prova
o comportamento em todos os navegadores. O movimento reduzido evita depender de
relógio/animações sem retirar as renderizações reais dos componentes.
Não há snapshots extensos, chamadas ao cofre Windows nem tokens válidos.

## Matriz das rotas atuais

| Caminho | Tela/destino | Acesso no frontend |
| --- | --- | --- |
| `/login` | Login | Público; sessão válida retorna a `/` |
| `/` | Dashboard | Sessão revalidada |
| `/dashboard` | Redireciona a `/` | Sessão revalidada |
| `/alerts` | Alertas | Sessão revalidada |
| `/history` | Histórico | Sessão revalidada |
| `/reports` | Relatórios | Sessão revalidada |
| `/analyses/:id` | Detalhes de análise | Sessão revalidada |
| `/windows/:id` | Detalhes de janela complementar | Sessão revalidada |
| `/system` | Status do sistema | Admin revalidado |
| `/admin/users` | Administração | Admin revalidado |
| `/settings` | Configurações | Sessão revalidada |
| `/about` | Sobre | Sessão revalidada |

`/demo` está ausente. `PresentationView.vue` permanece no repositório, sem item
no menu. Não existe catch-all/página 404 registrada: o teste de rota inexistente
comprova apenas ausência de match, sem afirmar tratamento 404 completo.

## Rastreabilidade da cobertura inicial

| Requisito | Teste efetivamente implementado | Limite |
| --- | --- | --- |
| Login | Acesso, validação nativa, senha visível/oculta, sucesso, loading, erro e redirect interno | Resposta de login simulada |
| Sessão | Ausente, expirada, logout e revalidação antes de acesso | Não valida JWT no servidor |
| Permissões | Admin permitido, user negado; papel local não prevalece sobre `/auth/me` | Somente guard/UI |
| Navegação | Destinos comuns/admin, clique, página ativa e QA IDs; sem Apresentação | Destinos de menu isolados; guards testados separadamente |
| Estados | Loading acessível, erro, vazio e ícone padrão real de EmptyState | DOM simulado |
| Dashboard | Até 12 janelas, busca, identificação, navegação, cores/alturas verticais, vazio e falha parcial | Sem polling/streaming ou vínculo com análise importada |
| Relatórios | Nomes, percentuais documentados, matriz/355 janelas e distinção operacional/histórico | Verifica apresentação; não recalcula métricas/Shapley |
| HTTP auth | Payload/envelope, Bearer, login sem token antigo e limpeza após 401 | Adapter Axios em memória |

O caso de limite do Dashboard inclui deliberadamente registros extras na resposta
sintética para verificar o recorte visual de 12; isso não muda o contrato da API.
Os valores históricos esperados são evidência fixa de apresentação, não uma
nova medição de precisão, generalização ou contribuição.

## AUD-06/AUD-07: detalhes de análise e paginação

Implementados em `views/detalhes-analise.spec.ts`, com fixtures tipadas em
`fixtures/analises.ts` e promises controladas sem sleeps. A regressão A → B foi
executada antes da correção e falhou quando a resposta de A substituiu B; o
mesmo teste passou após a correção.

- **Concorrência:** gerações locais invalidam resumo/resultados ao trocar a
  análise ou desmontar; um contador separado protege as requisições de páginas.
  Respostas, catch e finally obsoletos não atualizam o estado. A → B → C, erros
  tardios, loading, mudança real de rota e desmontagem são exercitados.
- **Paginação:** 50 registros por página, sem prefetch nem concatenação. O total
  vem de `meta.total`, com compatibilidade para `total_windows` no envelope
  anterior. A API aceita limit 1–500 e offset não negativo; PostgreSQL ordena
  por `AnalysisResult.id ASC`. O fallback local preserva a ordem persistida.
  O frontend não reordena nem recalcula resultados.
- **Limites:** testes com 0/1/50/51/125 janelas, última página incompleta, avanço,
  retorno, erro/retry, páginas concorrentes, troca de análise e detalhe da janela
  51. Exatamente 50 registros com total 50 não habilitam próxima página. Se uma
  página vazia informar redução do total, volta à última página válida; total
  zero reinicia offset sem inventar janelas.
- **Estados:** resumo e resultados têm loading/erro próprios. Navegar páginas
  não consulta novamente o resumo. Durante consulta, as linhas anteriores são
  ocultadas; o detalhe selecionado é fechado. Anterior/Próxima continuam
  acessíveis dentro dos limites conhecidos e respostas tardias são ignoradas.

Para execução focada:

```powershell
npm run test:run -- tests/views/detalhes-analise.spec.ts
```

O único ajuste de ambiente específico desses testes é a simulação local de
`scrollIntoView`, ausente no jsdom, com restauração ao terminar. Não é alteração
do produto. A proteção invalida respostas; não cancela o transporte HTTP.

## Complemento AUD-06: detalhes da janela

`views/detalhes-janela.spec.ts` reproduziu a falha A → B antes da correção:
o ID 2 era substituído pelo ID 1 quando A respondia por último. O mesmo teste
passou com a proteção local em `WindowDetailsView.vue::loadWindow`.

Um contador de geração e o ID atual protegem resposta, erro e finally; a
desmontagem invalida chamadas pendentes, seguindo o padrão da análise. O template,
layout, seletores e serviços HTTP permanecem intactos. Isso invalida a aplicação
de respostas obsoletas, sem cancelar o transporte.

Os testes cobrem sucesso, A → B → C, erro/null tardios, loading, erro da seleção
atual, janela não encontrada, rota dinâmica, Voltar para Alertas, desmontagem e
identidade dos dados enviados à exportação JSON/PDF. Os exportadores são
simulados para inspecionar seus argumentos; não há download ou impressão real.

```powershell
npm run test:run -- tests/views/detalhes-janela.spec.ts
```

Classificação local após testes: `AUD-06_WINDOW_DETAILS_CORRIGIDO_VALIDADO_LOCALMENTE`.
Não equivale a E2E com a API real ou validação visual em navegador.

## Segurança e limites restantes

Sem atualizações gerais de dependências nem `audit fix`. A comparação do audit
com o lockfile anterior foi feita separadamente: os avisos já existentes não
são resolvidos por esta suíte. A cadeia DEV de formatação do Vue Test Utils
também exige acompanhamento de advisories; aprovação funcional não é aprovação
de segurança de todas as dependências. Não usar entradas externas não confiáveis
nesses helpers de teste nem expor runners de teste como serviço público.

Faltam E2E reais, validação visual de resoluções, downloads/exportação em navegador,
autorização backend e cobertura completa das demais views. O AUD-11 e seus gates
de distribuição permanecem independentes. Este lote não aprova Setup Windows,
PostgreSQL gerenciado, nova classificação do runtime ou promoção de candidato.
