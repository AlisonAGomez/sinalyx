# Sinalyx - Auditoria final, QA e preparo para entrega

> **HISTÓRICO — referência anterior à Fase 2D.** Resultados, comandos e termos
> como “atual” descrevem a etapa de origem, não uma validação presente.
> `current` segue ativo; `hybrid_v2_3` é validation-only e Candidate v1 não foi
> promovido. Consulte o [índice atual](README.md).

Data: 2026-05-23
Versao alvo: v0.1.1-tcc
Escopo: auditoria estatica, hardening de publicacao, QA basico e correcao apenas de bugs reais encontrados.

## Resumo executivo

O projeto esta organizado como sistema web local com FastAPI, PostgreSQL, Docker Compose e frontend Vue. A auditoria confirmou protecoes importantes de autenticacao, rotas admin, hash de senha, seed admin controlado por ambiente, upload restrito a `.log`, paginacao limitada e tela frontend com ampla cobertura de `qa-id`/`data-testid`.

Foram corrigidos tres pontos reais:

- fallback de versao da API atualizado de `v0.1.0-tcc` para `v0.1.1-tcc`;
- fallback do Dockerfile do frontend atualizado para `/api`, alinhado ao Nginx reverse proxy;
- `.gitignore` e `.dockerignore` endurecidos para nao publicar segredos, dumps, dados processados, modelos, caches, builds e backups;
- tela de Alertas recebeu QA IDs nos filtros.

Nao foram alterados parser, features, modelos, heuristica, ensemble, Decision Engine, schema ou persistencia.

## Estrutura auditada

- `src/api/`
- `src/auth/`
- `src/core/`
- `src/db/`
- `src/features/`
- `src/models/`
- `src/parsers/`
- `src/pipelines/`
- `src/services/`
- `frontend/src/`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `Dockerfile`
- `docker-compose.yml`
- `.gitignore`
- `.dockerignore`
- `docs/`
- `scripts/`
- `tests/`

## Backend confirmado

Rotas publicas:

- `GET /`
- `GET /health`
- `POST /auth/login`

Rotas autenticadas:

- `GET /auth/me`
- `POST /analyze/pfsense`
- `GET /analyses`
- `GET /analyses/{analysis_id}`
- `GET /analyses/{analysis_id}/results`
- `GET /live/pfsense/collector/status`
- `GET /live/pfsense/parser/status`
- `GET /live/pfsense/windows`
- `GET /dashboard/summary`
- `GET /alerts/recent`
- `GET /history/summary`
- `GET /history/windows`
- `GET /history/windows/{window_id}`
- `GET /history/alerts`
- `GET /history/executions`
- `POST /predict` como contrato legado protegido

Rotas admin:

- `GET /system/audit`
- `GET /admin/users`
- `POST /admin/users`
- `PUT /admin/users/{user_id}`
- `PATCH /admin/users/{user_id}/status`
- `DELETE /admin/users/{user_id}`
- `POST /live/pfsense/run`

## Seguranca confirmada no codigo

- Tokens JWT assinados com HS256.
- Senhas com PBKDF2-HMAC-SHA256 e salt aleatorio.
- Comparacao de senha em tempo constante.
- Segredo JWT fraco bloqueado em ambiente de producao/demo.
- Rotas sensiveis usam `get_current_user`.
- Rotas administrativas usam `require_admin`.
- Usuario inativo e bloqueado.
- Seed admin depende de `SINALYX_ADMIN_PASSWORD`.
- Administrador supremo nao pode ser removido, rebaixado ou desativado.
- Sistema impede remover o proprio usuario autenticado.
- Sistema impede remover o ultimo admin ativo.
- Upload pfSense aceita apenas `.log`.
- Nome de upload usa `Path(filename).name` e stem sanitizado.
- `analysis_id` rejeita componentes de caminho.
- Paginacao tem limite maximo.
- API local no Compose fica presa a `127.0.0.1:8000`.
- Frontend acessa API via proxy `/api` no Nginx.

## Pontos de atencao de seguranca

- O fallback local `SINALYX_AUTH_SECRET_KEY` e aceitavel apenas para desenvolvimento. Para produto real, definir segredo forte no `.env`.
- `POST /predict` permanece como endpoint legado protegido. Se o produto nao precisar dele no futuro, manter protegido ou descontinuar em versao major.
- Artefatos `joblib`/`keras` sao carregados do disco. Eles devem vir apenas do pipeline confiavel do projeto, nunca de upload de usuario.
- O CORS usa origens configuraveis. Para producao real, limitar a origem final do dominio/IP usado pelo frontend.
- `SINALYX_PFSENSE_ALLOW_UNKNOWN_HOST` deve ser revisado antes de uso real em ambiente corporativo.

## Frontend confirmado

Rotas:

- `/login`
- `/`
- `/demo`
- `/alerts`
- `/history`
- `/reports`
- `/about`
- `/analyses/:id`
- `/windows/:id`
- `/system`
- `/admin/users`
- `/settings`

Padronizacoes confirmadas:

- `formatAttackType` exibe `syn_flood` como `DDoS / SYN Flood`.
- `formatAttackType` e `formatFinalLabel` exibem `unknown_anomaly` como `Anomalia nao classificada`.
- termos tecnicos de IA passam por `formatTechnicalLabel` e `formatAiSupportReason`.
- frontend possui 189 ocorrencias de `qa-id`/`data-testid` em views/componentes.
- tela de Alertas agora tem QA IDs nos filtros.

## Docker e deploy

Confirmado em arquivo:

- `frontend` em porta 80;
- `api` em `127.0.0.1:8000`;
- `postgres` em `127.0.0.1:5432`;
- volume persistente `sinalyx_pgdata`;
- `restart: unless-stopped`;
- proxy `/api` no Nginx do frontend;
- build arg `VITE_API_BASE_URL=/api`.

## GitHub privado

Publicacao automatica nao foi executada porque:

- `git` nao foi encontrado no PATH;
- `gh` nao foi encontrado no PATH.

Foi preparado o guia `docs/github_private_publish.md` e o `.gitignore` foi endurecido para reduzir risco de envio indevido.

## QA executado

Comandos executados:

```powershell
python -m compileall src tests
```

Resultado: passou.

```powershell
python -m pytest -rs
```

Resultado: bloqueado. O Python global nao tem `pytest` instalado.

```powershell
docker-compose config --quiet
```

Resultado: passou, com aviso do Docker sobre acesso negado a `<perfil-do-usuario>\.docker` quando executado no sandbox.

```powershell
docker-compose ps
```

Resultado: passou fora do sandbox. Containers `sinalyx_frontend`, `sinalyx_api` e `sinalyx_postgres` ficaram `healthy`.

```powershell
Invoke-WebRequest http://localhost/
Invoke-WebRequest http://localhost/api/health
```

Resultado: frontend respondeu HTTP 200 e `/api/health` retornou `{"status":"ok","database":{"enabled":true,"available":true}}`.

```powershell
node node_modules\vue-tsc\bin\vue-tsc.js --noEmit
```

Resultado: passou.

```powershell
node node_modules\vite\bin\vite.js build
```

Resultado: passou fora do sandbox. O build gerou `frontend/dist`.

## Prints consolidados

Os prints de evidencia foram salvos em `docs/evidencias/prints/`:

- `01-login-desktop.png`
- `02-dashboard-desktop.png`
- `03-alertas-filtros.png`
- `04-historico-resumo.png`
- `05-detalhe-investigacao.png`
- `06-relatorios.png`
- `07-sistema-status.png`
- `08-admin-usuarios.png`
- `09-configuracoes.png`
- `10-sobre.png`
- `11-login-mobile.png`
- `12-dashboard-mobile.png`

## Bloqueios atuais

- `git` ausente no PATH bloqueia commit/push.
- `gh` ausente no PATH bloqueia criacao automatica de repositorio privado.
- `python -m pytest -rs` bloqueado por ausencia de pytest no Python global.
- `docker compose` plugin falhou neste shell; `docker-compose` funciona para `config`, `ps` e runtime.

## Conclusao

O estado atual esta coerente para a etapa de entrega local do TCC. O sistema possui separacao clara entre frontend, API, banco, pipeline e IA. A publicacao segura no GitHub privado requer apenas instalar/configurar Git e GitHub CLI ou fornecer outro metodo autenticado de envio. Antes de produto real, revisar segredo JWT, politica CORS final, host key SSH/SFTP do pfSense e processo seguro de distribuicao dos modelos.
