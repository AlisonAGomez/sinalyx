# Banco de dados

Status: **ATUAL / OFICIAL**. PostgreSQL é o banco suportado; SQLite é histórico.
Fontes: `src/db/models.py`, `src/db/repository.py` e migration
`20260505_0001_initial_schema.py`. Não houve consulta ao banco real nesta fase.

## Tabelas e relações

| Tabela | Finalidade e chave primária | Campos principais e restrições |
| --- | --- | --- |
| `users` | Autenticação e estado da conta; `id` inteiro autoincremental | Nome/email até 255, email único, hash até 512, papel até 32, estado ativo e datas; todos obrigatórios |
| `analyses` | Uma análise de arquivo; `id` texto até 128 | Arquivo, data, total de janelas, classificação predominante e JSONs de resumo/contagens/parser/artefatos obrigatórios; confiança média opcional |
| `analysis_results` | Resultado por janela; `id` inteiro autoincremental | `analysis_id` obrigatório com FK para `analyses.id`; `raw_json` obrigatório; janela, origem, protocolo, métricas, decisão, motivo e scores opcionais |
| `live_pfsense_windows` | Janelas incrementais locais; `id` inteiro autoincremental | `window_uid` único, execução, criação, status, caminho local e JSONs de features/modelos/metadados/resultado obrigatórios; offsets, janela, caminho remoto e decisão podem ser nulos |
| `alembic_version` | Revisão do schema pelo Alembic | `version_num` identifica a revisão; não é entidade de negócio nem modelo ORM do projeto |

```text
analyses.id (1) ─── (N) analysis_results.analysis_id

users                     live_pfsense_windows
(sem FK para análises)     (histórico incremental independente)
```

Não existe ownership entre `users` e `analyses`, nem FK de usuário nas janelas
live. A autorização atual é por autenticação/papel; consumidores não devem
presumir isolamento por dono de análise.

## Índices e comportamento

`analyses.created_at` tem índice para histórico; `analysis_results.analysis_id`
para recuperar janelas. `users.email` é único e indexado; `role` tem índice.
No live, são indexados `window_uid`, `execution_id`, `created_at`, `window_id` e
`window_timestamp`. A unicidade de `window_uid` apoia idempotência;
`execution_id` não é FK.

`save_analysis` cria ou atualiza o resumo e substitui seus resultados na mesma
transação. A relação ORM usa `all, delete-orphan`. Isso não significa
`ON DELETE CASCADE`: a FK da migration não declara cascata no banco.
Papéis e proteção do administrador são regras do repositório, não enum/check
de papel no schema. JSONs guardam detalhes, sem criar relações adicionais.

## Sessões e transações

O engine SQLAlchemy usa `pool_pre_ping=True`, que verifica a conexão ao
retirá-la do pool. Não garante disponibilidade durante toda a operação nem
repete automaticamente transações. `SessionLocal` usa `autocommit=False`
e `autoflush=False`.

O repositório abre sessões, chama `commit` nas gravações, `rollback` em falhas e
`close` no `finally`. Consultas também fecham sessões. O serviço da API
sanitiza falhas; exceções internas não devem ser publicadas diretamente.

## Alembic e ORM

O ORM descreve entidades Python. **Alembic é a autoridade para evolução de
schema em bancos persistentes.**
A revisão inicial `20260505_0001` usa SQL PostgreSQL com
`CREATE TABLE/INDEX IF NOT EXISTS`; seu `downgrade` não remove tabelas ou dados.
Isso não converte tabelas preexistentes divergentes para o schema esperado.

`create_tables` mantém `Base.metadata.create_all`: não executa Alembic,
não registra revisão e não migra colunas existentes. A migration define
defaults no servidor e índices/constraints SQL; o ORM usa defaults Python e
pode materializar unicidade como índice único. Não presumir catálogos físicos
idênticos entre os dois caminhos.

Na Fase 2E, o bootstrap foi mantido para compatibilidade. Atualmente, o startup
da API, `run_seed`, o início do worker live e a CLI incremental quando persiste
chamam `create_tables` uma vez; cada rodada live apenas persiste os resultados.
Em banco novo persistente, aplicar Alembic antes de iniciar esses serviços.
Em banco já existente, revisar divergências antes do upgrade: `IF NOT EXISTS`
não repara tabelas. Não houve alteração na migration inicial ou no schema.
Testes SQLite descartáveis comprovaram idempotência e que `create_all` não
adiciona colunas faltantes em tabelas existentes; não validam PostgreSQL real.

Diferenças conhecidas preservadas: defaults SQL de `total_windows`, `role`,
`is_active` e `status` versus defaults Python; unicidade de email/window_uid
como constraint mais índice na migration versus índice único no ORM.
As quatro tabelas têm as mesmas colunas declaradas. Nenhum índice foi adicionado.

Em ambiente isolado, com conexão privada configurada:

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Não foi executada migration nesta fase. Inspecione schema e backup antes de
aplicar mudanças; não use `stamp` para encobrir divergências.

## Administrador inicial e fallback

`scripts/seed_admin.py` prepara tabelas e chama o seed. Conta nova exige
`SINALYX_ADMIN_PASSWORD`; a senha é armazenada com hash. Desde a Fase 2E,
**email já existente não sofre mudança de papel, atividade, nome ou senha**.
Admin ativo é mantido; usuário comum ou conta inativa produz aviso genérico de
revisão administrativa. O seed deixou de promover/reativar silenciosamente.
Email vazio/malformado é rejeitado; senha ausente impede apenas criação nova.
Não há mecanismo de recuperação de acesso por reexecução do seed.

Se o email configurado já pertence a conta comum/inativa e não existe admin
ativo, o seed preserva a conta e o sistema continua sem admin ativo. Recuperação
deve ser deliberada pelo responsável do banco, com backup e procedimento
separado; não contornar isso mudando variáveis repetidamente. Os controles
existentes contra excluir/desativar/rebaixar o último admin permanecem testados.

Falha ao gravar análise pode preservar JSON e indicar `database_saved=false`.
Isso não fornece autenticação PostgreSQL completa, não sincroniza automaticamente
o banco depois e não torna SQLite oficial.

Veja os [scripts de backup e restauração](../scripts/README.md#backup-e-restore).
Dumps contêm dados sensíveis; restore pode substituir objetos e dados.
