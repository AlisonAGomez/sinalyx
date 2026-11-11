# Mapa do código e estrutura

Status: **COMPLEMENTAR ATUAL**, roteiro de leitura para manutenção e banca.
Leia primeiro [arquitetura](architecture.md), [banco](database.md) e
[segurança](security.md). Caminhos abaixo são relativos à raiz do projeto.

| Caminho | Responsabilidade e ponto de atenção |
| --- | --- |
| `src/api/main.py` | Rotas, inicialização e respostas; análise principal em /analyze/pfsense, /predict legado |
| `src/api/services.py` | Recebimento do arquivo, fluxo de análise, resposta e tratamento de falhas |
| `src/api/upload_limits.py`, `auth_request_limits.py`, `error_sanitization.py` | Limites de tamanho e login; mensagens que não expõem dados internos |
| `src/api/health_checks.py` | Prontidão do banco e modelos já carregados; `/live` permanece independente dessas verificações |
| `src/api/auth.py`, `src/auth/security.py` | Token, consulta da conta e autorização por papel; senha protegida por hash |
| `src/db/` | Conexão, sessões, tabelas, consultas e criação inicial de contas; sem separação de análises por proprietário |
| `src/parsers/pfsense_parser.py` | Leitor oficial dos campos dos logs pfSense |
| `src/pfsense_parser.py`, `src/parsers/pipilines/` | Caminhos antigos/compatibilidade; não escolher pela semelhança do nome |
| `src/features/` | Preparação das características numéricas; security_window_context é auxiliar experimental |
| `src/pipelines/` | Processamento em lote, agrupamento por janela, análise e leitura incremental; prepare/train/validate são históricos |
| `src/collectors/`, `src/services/pfsense_incremental_service.py` | Coleta SSH e leitura a partir da posição salva; o agendamento é responsabilidade do processo separado |
| `src/models/autoencoder.py`, `isolation_forest.py`, `heuristics.py`, `ensemble.py`, `decision_engine.py` | Sinais e decisão híbrida oficial |
| `src/models/memory_context*.py`, `*targeted_tuning.py` | Pesquisa lateral/experimental, não promovida |
| `src/core/` | Ambiente, caminhos, cadastro de perfis, arquivos de modelos e nomes de apresentação |
| `src/security/mitre_mapping.py` | Enriquecimento explicativo, não detector independente |
| `frontend/src/router/`, `services/`, `views/`, `components/` | Navegação, HTTP, telas e componentes; proteção visual não substitui autorização no servidor |
| `tests/`, `frontend/tests/` | Testes de comportamento e integração; experimentos separados |
| `scripts/` | [Catálogo por finalidade](../scripts/README.md) |
| `data/` | [Dados privados e modelos](dados_modelos.md) |
| `docs/` | [Índice classificado](README.md) |
| `migrations/` | Histórico de alterações da estrutura do banco, aplicado pelo Alembic |

## Configurações da raiz

`.python-version` registra Python 3.10.11. `requirements.txt` fixa dependências
declaradas; `requirements-windows-py310.lock` reproduz a resolução Windows com
hashes. `.env.example` documenta variáveis, sem substituir o ambiente privado.
`alembic.ini` configura migrations; Dockerfile/Compose definem imagens e serviços.
`.gitignore` e os arquivos `.dockerignore` têm responsabilidades diferentes:
seleção Git e envio de contexto de build. Nenhum deles limpa histórico já publicado.
`frontend/package.json` define scripts; lockfile fixa dependências frontend.

## Decisões que merecem leitura no código

O processamento de upload é aguardado no thread pool, com limpeza de temporários
da requisição. A gravação de análise e substituição de resultados compartilham
transação. O seed cria o admin quando necessário e permitido, sem promover
usuário comum nem reativar conta existente silenciosamente. Contas existentes
exigem tratamento administrativo deliberado quando aplicável. O live preserva
offsets e última janela até outra passagem, salvo finite-file.

As regras de decisão estão descritas em [architecture.md](architecture.md).
Os comentários e as descrições de funções usam português direto, explicando
entradas, saídas e cuidados que não ficam evidentes apenas pelo nome. Nomes
de funções, campos, arquivos e mensagens públicas são preservados para manter
a compatibilidade. Não é necessário comentar cada atribuição ou linha trivial.

A interface usa `qa-id` e `data-testid`; nenhum seletor ou comportamento visual
foi alterado. Capturas antigas são evidência histórica, não execução de QA atual.

## Ordem de leitura do processamento oficial

1. **Receber o arquivo:** `src/api/main.py` recebe o envio autenticado em
   `/analyze/pfsense`. `src/api/services.py` organiza os arquivos temporários,
   chama o processamento e prepara a resposta.
2. **Ler as linhas:** `src/parsers/pfsense_parser.py` separa os campos do
   `filterlog` em eventos estruturados. Uma linha de firewall descreve tráfego;
   não comprova que uma senha foi aceita ou recusada.
3. **Agrupar por tempo e origem:** `src/pipelines/window_aggregator.py` reúne
   eventos da mesma origem em intervalos fixos. A duração é fornecida ao fluxo;
   o padrão incremental é de cinco segundos. Lotes históricos preservam a
   duração usada em cada avaliação.
4. **Preparar os números:** `src/features/constants.py` define as treze colunas
   oficiais e sua ordem. `src/features/engineering.py` prepara razões e
   transformações numéricas de forma consistente.
5. **Obter os sinais:** `src/pipelines/infer_pfsense_batch.py` coordena os dois
   modelos e as regras. O Autoencoder mede a diferença de reconstrução; o
   Isolation Forest avalia o isolamento dos registros. A heurística identifica
   padrões pelos campos disponíveis. Nenhum deles bloqueia tráfego.
6. **Combinar e decidir:** `src/models/ensemble.py` combina os sinais dos modelos.
   `src/models/decision_engine.py` aplica as regras de decisão final e produz
   classificação, risco e justificativa. A explicação das contribuições reutiliza
   os sinais; não executa novamente Autoencoder ou Isolation Forest.
7. **Salvar e consultar:** `src/db/repository.py` grava as análises e seus
   resultados no PostgreSQL. O conteúdo completo por janela fica em `raw_json`;
   as consultas recuperam os blocos detalhados já calculados.
8. **Apresentar:** `frontend/src/services/api.ts` consulta a API. As telas usam
   formatadores para apresentar os valores, sem recalcular modelos ou decisões.
   As telas de detalhe descartam respostas antigas quando a navegação muda.

## Leitura incremental experimental

`src/collectors/pfsense_collector.py` copia o log quando a coleta é solicitada.
`src/collectors/file_generation.py` compara uma amostra inicial para reconhecer
substituição do arquivo, sem salvar seu conteúdo na assinatura.
`src/services/pfsense_incremental_service.py` lê a partir da posição já
processada, fecha as janelas elegíveis e salva resultados antes de confirmar o
novo estado. Falha de análise ou gravação não deve confirmar avanço da leitura.

`src/services/live_execution_lock.py` evita rodadas persistentes concorrentes.
`src/services/live_run_retention.py` limita somente os arquivos reconhecidos de
execuções concluídas. `src/workers/pfsense_live_worker.py` repete rodadas quando
autorizado; sua existência não significa que a coleta direta está concluída ou
ativa na instalação do usuário.

## Termos que aparecem em identificadores existentes

| Termo no código | Significado para leitura |
| --- | --- |
| parser | Leitor que separa os campos de cada linha de log |
| feature | Característica numérica de uma janela, como quantidade de conexões |
| runtime / profile | Configuração e conjunto de modelos usados na execução |
| current | Nome do perfil oficial atual; não significa promoção de candidato |
| registry / manifest | Cadastro dos perfis e descrição dos arquivos necessários |
| scaler | Ajuste de escala aplicado aos números antes da análise pelos modelos |
| score / threshold | Pontuação produzida e limite usado na classificação |
| confidence | Indicador informado pelo componente; não é garantia de acerto |
| payload / raw_json | Conteúdo transportado ou salvo integralmente como JSON |
| offset | Posição em bytes até onde o arquivo já foi processado |
| Shapley | Método que compara combinações de componentes para explicar sua influência |
| JWT / RBAC | Token de sessão e verificação de permissões pelo papel da conta |

Nomes técnicos exigidos por bibliotecas, arquivos e contratos continuam literais.
Comentários não devem atribuir autonomia à IA, confirmar ataques sem evidência
ou apresentar experimentos como funcionamento oficial.

## Nomes visíveis no Docker

| Container | Responsabilidade | Serviço interno preservado |
| --- | --- | --- |
| `sinalyx-painel` | Interface web | `frontend` |
| `sinalyx-servidor` | API e processamento | `api` |
| `sinalyx-banco` | PostgreSQL | `postgres` |
| `sinalyx-coleta-experimental` | Processo opcional de coleta experimental | `live-worker` |

Os três primeiros compõem o ambiente principal. O quarto nome fica definido na
configuração; isso não inicia o processo. Os nomes de imagens, redes, volumes e
serviços não precisam ser traduzidos para tornar o Docker Desktop legível.
