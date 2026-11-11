# Fase 2E — confiabilidade operacional

Período: 9–10 de setembro de 2026. Escopo OFICIAL limitado a operação da API e banco.
Base: `58bde183cc103ef2eed3c997a0bbfee84c2cc8ea`, árvore limpa confirmada antes
das alterações; branch `codex/fase2a-baseline`. Não houve push nem Fase 3.

## Resultado por achado

| Achado | Classificação | Decisão |
| --- | --- | --- |
| A16 | Melhorado | `/live` e `/ready` adicionados; `/health` preservado |
| A17 | Corrigido nos testes de comportamento | Exit codes, temporários, publicação atômica e interrupção SQL |
| A14 | Documentado e validado com mocks/SQLite | Alembic é autoridade; bootstrap compatível mantido |
| A15 | Corrigido | Seed não promove nem reativa conta existente silenciosamente |
| A13 | Não alterado por falta de evidência operacional suficiente | Custo sintético medido; filtro posterior exige cuidado semântico |
| Docker/PostgreSQL | Pendente de validação integrada | Nenhum resultado de integração foi simulado |

## Arquivos alterados

| Arquivos | Finalidade |
| --- | --- |
| `src/api/main.py`, `src/api/prontidao.py` | Sondas e marcador de preload completo |
| `scripts/backup_postgres.ps1`, `scripts/restore_postgres.ps1` | Tratamento de falha e transferência de SQL sem recodificação |
| `src/db/repository.py` | Apenas comportamento do seed; consultas preservadas |
| `src/db/init_db.py` | Docstring de autoridade/limites do bootstrap, sem mudança de execução |
| `tests/test_confiabilidade_operacional.py` | API/sondas, seed, proteção de admin, bootstrap e migration |
| `tests/test_backup_restore.py` | PowerShell real com comando Docker simulado |
| `tests/test_historico_caracterizacao.py` | Paginação atual, filtros e medição sintética |
| `docs/database.md`, `docs/database_vscode.md` | Autoridade, seed e manutenção do banco |
| `docs/deploy_local_sinalyx.md` | Contratos e limites das sondas |
| `scripts/README.md`, `docs/README.md` | Catálogo e índice atualizados |
| Este relatório | Evidências e pendências da fase |

Não foram adicionadas dependências, migrations, tabelas ou índices. Nenhum
contrato principal da API, comportamento visual ou identificador de UI mudou.

## A16 — antes/depois

Antes: `/health` retornava HTTP 200 mesmo quando banco/modelos indisponíveis.
Depois: o endpoint mantém o payload anterior por compatibilidade; `/live`
responde 200 com `status=ok` sem acessar banco ou modelos. `/ready` responde
200 com `status=ready` ou 503 com `status=not_ready`, sem detalhes internos.

A readiness verifica conexão PostgreSQL e IDs das quatro tabelas centrais
por consulta `LIMIT 0`, sem ler dados. Usa engine separado com `NullPool`,
`connect_timeout=2` e `statement_timeout=2000`, evitando espera pelo pool da API.
Esses limites não são deadline global de DNS/conexões multi-host.

No runtime, exige preload completo e acesso aos bundles já carregados do
Autoencoder e Isolation Forest, incluindo as validações existentes de
modelo/scaler/threshold. Não resolve outro perfil, não altera paths, não lê
holdout, não carrega artefatos nem executa inferência por healthcheck.
Falha parcial de preload conserva readiness negativa; corrigir e reiniciar.
O fallback JSON não torna a aplicação pronta para autenticação PostgreSQL.

Os testes cobrem disponibilidade/indisponibilidade dos componentes, falha de
conexão/consulta, banco desabilitado, ausência de bundles, preload incompleto,
contrato anterior de health e liveness independente. A sonda não substitui
validação de schema completo, qualidade dos modelos ou análise ponta a ponta.

Compose não mudou: fazer o frontend depender de `/ready` sem testar a stack
poderia bloquear seu início em instalações sem artefatos/banco prontos.

## A17 — antes/depois

Antes: pipeline textual de `pg_dump` para `Out-File`; destino podia ser truncado
e sucesso anunciado mesmo com falha nativa. Restore não usava `ON_ERROR_STOP`.

Depois: `pg_dump --file` escreve temporário único no container. `docker cp`
transfere para temporário no mesmo diretório do destino; exit codes e arquivo
não vazio são conferidos antes de `File.Replace`/`File.Move`. O destino anterior
permanece intacto em falha de geração/cópia. Caminhos relativos seguem a
localização atual do PowerShell. A transferência preserva bytes, sem pipeline
de conversão de texto, e evita carregar todo o dump em memória do PowerShell.

Restore rejeita arquivo ausente/vazio, copia antes de executar e chama
`psql -X --set ON_ERROR_STOP=1 --single-transaction --file`. Falha de cópia
impede SQL; falha SQL/nativa interrompe sem anunciar sucesso. **Restore é
destrutivo**, para dumps confiáveis e compatíveis com transação; não foi
executado no banco real. Os scripts não imprimem senha, connection string,
stdout SQL ou stderr bruto. Tentam limpar somente seus temporários.

Testes executam PowerShell 5.1.26100.9444 e 7.6.5 com Docker substituído por
função controlada que registra argumentos e simula exit codes. Cobrem sucesso,
backup novo/anterior, caminho com espaços/relativo, falha de dump, cópia parcial,
arquivo vazio, restore ausente, falha SQL e interrupção antes de SQL.
Não comprovam um dump restaurável, rollback PostgreSQL ou comportamento do
Docker real. A política de execução foi ajustada apenas nos processos de
teste, sem alteração persistente da configuração do Windows.

Durante o desenvolvimento, os testes detectaram coerção de `$null` para string
vazia em `File.Replace` nos dois PowerShells. A correção usa `NullString.Value`;
os cenários de substituição passaram após a correção. Também foram observadas
falhas esperadas nos scripts anteriores por ausência de verificação de exit code.

## A14 — análise e decisão

Startup da API, `run_seed` e preparação live usam `create_tables`, que executa
`Base.metadata.create_all`. Alembic não é chamado automaticamente. Retirar esse
bootstrap agora mudaria instalações existentes; o comportamento foi mantido.
**Alembic é referência para evolução controlada em bancos persistentes**;
aplicar migrations explicitamente, após revisar schema/backup.

Testes com SQLite em memória demonstram idempotência/preservação de registros,
falha sem engine e ausência de migração de colunas em tabela preexistente.
Teste da migration com `op.execute` simulado confirma que as quatro tabelas
declaram as mesmas colunas do ORM e que downgrade não executa remoções.

Diferenças preservadas: defaults SQL de `analyses.total_windows`, `users.role`,
`users.is_active`, `live_pfsense_windows.status` versus defaults Python; email
e window_uid únicos por constraint mais índice SQL versus índice único ORM.
Os índices de data, role, analysis_id e campos live seguem declarados; não
houve alteração estética ou índice novo. `IF NOT EXISTS` não corrige divergência
preexistente nem `create_all` registra revisão Alembic. Não usar `stamp` para
ocultar diferenças. PostgreSQL/Alembic online continuam pendentes.

## A15 — análise e decisão

O código anterior restaurava papel/atividade deliberadamente: o retorno dizia
que o administrador estava protegido. Esse comportamento podia promover um
usuário comum ou reativar conta mesmo sem senha de seed. A intenção operacional
estava no código, mas era incompatível com bootstrap previsível sem mutações
silenciosas em contas existentes.

Agora email inexistente com senha cria admin ativo; conta existente é mantida
com papel, atividade e senha originais. Conta comum/inativa retorna motivo
genérico de revisão administrativa; admin ativo segue idempotente. Email vazio,
malformado ou acima de 255 caracteres é rejeitado. Ausência de senha não cria
conta. Nenhum hash/senha é incluído na serialização pública.

Compatibilidade: reexecutar seed deixou de ser mecanismo de promoção/reativação.
Se nenhuma conta admin estiver ativa e o email estiver ocupado por conta comum
ou inativa, o seed não resolve acesso automaticamente. Recuperação exige ação
deliberada do responsável; não foi criada ferramenta/tabela de recuperação.
As proteções existentes contra excluir, desativar ou rebaixar o último admin
ativo foram testadas e mantidas. Concorrência administrativa não foi redesenhada.

## A13 — evidência e decisão

`list_history_windows` usa `_load_live_history_rows`, que aplica filtros SQL,
ordena por `coalesce(window_timestamp, created_at) DESC, id DESC`, materializa
`.all()`, aplica filtro Python `ai_support`, calcula total e faz slice.
Alertas também materializam antes do slice; execuções/resumos agregam janelas
em memória. Esses caminhos não foram alterados.

Medição com **1.000 registros sintéticos**, SQLite descartável, JSON de teste
com 256 caracteres e `limit=50`: **1.000 objetos ORM carregados**, 50 devolvidos,
uma consulta sem LIMIT, pico de **4.240.982 bytes** monitorado por `tracemalloc`.
O pico mede alocações Python durante a consulta/serialização, não RSS total nem
memória de PostgreSQL. Não foi usado dado real ou benchmark de produção.

O custo é linear, mas não se demonstrou gargalo operacional no volume atual.
Aplicar LIMIT antes de `ai_support` muda total/composição das páginas; traduzir
o filtro exige preservar coerção de valores JSON e compatibilidade de dados.
Um caminho SQL especial sem esse filtro adicionaria uma segunda estratégia.
Nesta fase, o benefício medido não justifica essa ampliação: melhoria futura,
sem alegar otimização entregue. Se o volume crescer, medir PostgreSQL e fixar
semântica JSON antes de migrar paginação/agregações. Nenhum índice foi criado.

Seis testes caracterizam primeira página, intermediária, vazia, ordenação,
total e combinação de filtro relacional/IA antes do slice, além da medição.

## Validações e preservação

Baseline em Python **3.10.11**: **134 passed, 7 skipped, 2 subtests passed**.
Antes das correções, os testes novos reproduziram promoção/reativação do seed,
configuração inválida aceita e ausência das sondas. Depois, 54 testes de seed,
sondas, bootstrap e scripts passaram, seguidos da ampliação de cobertura.

Validação final em Python 3.10.11:

| Verificação | Resultado |
| --- | --- |
| Compileall oficial com exclusão documentada | Código 0 |
| Pytest completo após todos os casos novos | **199 passed, 7 skipped, 2 subtests passed**, 153,03 s |
| `tests/testparser.py` explícito | **2 passed**, 0,20 s |
| Casos novos na suíte | **65**: 37 operacionais, 22 de scripts e 6 de histórico |
| Links Markdown locais | **177 verificados, zero quebrados** |
| Diff e escopo | `git diff --check` sem erros; 15 arquivos revisados |

Os sete skips são smoke tests HTTP por ausência de API em execução; não foram
contabilizados como integração aprovada. Permanecem dois avisos preexistentes
de depreciação `on_event`. A execução inicial da venv no sandbox não conseguiu
iniciar o interpretador; a execução autorizada fora dessa restrição confirmou
Python 3.10.11 e executou as validações. Nenhum ambiente foi reinstalado.

Comandos oficiais, com `.env` desabilitado nos testes e banco real não usado:

```powershell
.\.venv\Scripts\python.exe -m compileall -q -x 'bruteforce_recent_history_prototype\.py$' src scripts tests migrations
.\.venv\Scripts\python.exe -m pytest -q -ra --tb=short
.\.venv\Scripts\python.exe -m pytest -q tests/testparser.py --tb=short
```

A exclusão do protótipo experimental congelado é a mesma da Fase 2A; não houve
correção nem alegação de sucesso do compileall irrestrito. Frontend não mudou,
portanto typecheck/build não foram repetidos. Não houve treino/inferência real.

Preservação conferida: **67 arquivos com SHA-256 e 563 metadados sem divergência**
em relação às referências anteriores à Fase 2A. Parser, 13 features, modelos,
heurística, Ensemble, Decision Engine, thresholds, registry, runtime current,
Candidate v1 e dados não foram modificados. Não houve Candidate v2 ou promoção.

## Docker, pendências e riscos residuais

Docker não foi encontrado no PATH nem no caminho padrão de instalação Windows.
`docker info` não pôde executar. Assim, Compose config/build/up, healthchecks de
container, frontend/proxy, PostgreSQL real, migrations online e restore real
**não foram executados**. Validar futuramente em stack isolada, sem volumes reais.

Riscos: readiness é condição mínima; falha no preload exige reinício, e timeouts
não são deadline absoluto. Bootstrap antigo não repara schema. Recuperação de
admin não é automatizada. Paginação/agregações continuam carregando todas as
janelas filtradas. Backup precisa de espaço, ACL adequada e teste de restore;
queda abrupta pode deixar temporários. Não há checksum remoto, e perda de
conexão ao confirmar restore pode deixar resultado incerto. SQL arbitrário não
tem garantia de rollback. Reescrita do histórico Git permanece fora do escopo.

Entrega somente por commit local único, com arquivos selecionados explicitamente.
Nenhum push, mudança de frontend/detecção ou início automático da Fase 3.
