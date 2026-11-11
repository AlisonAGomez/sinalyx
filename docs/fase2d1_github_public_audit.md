# Fase 2D.1 — GitHub público e auditoria de exposição

> **Atualização posterior:** as imagens 05/07 e os caminhos de quatro documentos
> foram sanitizados localmente na [Fase 2D.2](fase2d2_public_sanitization.md).
> Os achados abaixo registram a auditoria anterior; as versões públicas antigas
> e o histórico não foram removidos. Há referências residuais fora desses documentos.

Data: 9 de setembro de 2026. Branch: `codex/fase2a-baseline`.
Base confirmada com árvore limpa:
`d5010fee79f8a8915c2a9a97e4a0b0002be296d7`.

## Resultado e alcance

O repositório **já é público**, confirmado na
[página do Sinalyx](https://github.com/AlisonAGomez/sinalyx) e pela API pública
do GitHub, sem autenticação. O remote `origin` corresponde ao projeto; nenhuma
credencial de URL foi exibida. A consulta da branch pública `main` retornou
`92501a0172017df5b27229b031c2c15646079092`, já disponível localmente.
Essa árvore pública tem 214 arquivos; o HEAD local auditado tem 279.
As alterações locais posteriores não foram enviadas nesta fase.

Não foi confirmado segredo operacional real, chave privada, token GitHub,
JWT completo ou hash de senha exposto no material examinado. Foram encontrados
**dados de laboratório em captura pública** e **caminhos locais em documentos**,
com recomendações de sanitização. Isso não equivale a comprometimento comprovado
nem a aprovação irrestrita para publicar todos os dados.

A imagem 05 contém endereços de origem/destino associados a uma investigação
de laboratório. A imagem 07 mostra caminhos operacionais e identificador de
execução. São achados de exposição contextual, não credenciais. Nenhuma imagem
foi editada. Não foi identificado dado crítico que exigisse suspender o commit
documental segundo o critério solicitado; os achados abaixo permanecem abertos.

## Método e cobertura

| Verificação | Cobertura |
| --- | --- |
| Clone | Não raso |
| Commits | 13, união das refs locais e reflogs |
| Commits sem refs adicionais | Nenhum encontrado por fsck |
| Caminhos históricos | 279 |
| Blobs únicos referenciados | 360; cada versão de conteúdo examinada uma vez |
| Texto | 347 blobs UTF-8, incluindo CSV/JSON, fontes e configurações |
| Binários | 13 PNG: 12 screenshots e um logo; sem modelos serializados |
| Volume examinado | 9.240.899 bytes de blobs referenciados |
| Capturas | 12/12 revisadas visualmente; hashes Git idênticos aos publicados |
| Candidatos heurísticos | 55 ocorrências em versões distintas, triadas sem reproduzir valores |

Foram usados Git, Python padrão e leitura visual local. Gitleaks, TruffleHog e
GitHub CLI não estavam disponíveis no PATH; nenhuma ferramenta foi instalada.
O script de auditoria e inventários mascarados ficaram fora do repositório, no
diretório local de evidências da tarefa.

Comandos/famílias usados:

- `git status --short`, `git rev-parse HEAD`, `git branch --show-current`;
- leitura de remote com ocultação de credencial antes de exibir;
- `git rev-parse --is-shallow-repository`;
- `git rev-list --all --reflog` e `git fsck --full --no-reflogs --unreachable`;
- `git ls-tree -r -z COMMIT` para todos os commits e `git cat-file blob OID`;
- `git rev-list --objects --all --reflog` na revisão complementar de caminhos;
- padrões de chave privada, tokens conhecidos, JWT, conexão com senha, hashes
  de credencial, atribuições de senha/secret e configuração de ambiente;
- busca contextual de IPv4, hostnames locais, emails e caminhos pessoais;
- consulta HTTPS pública de visibilidade, branch e árvore GitHub;
- revisão de links relativos e diff após alterações apenas Markdown.

O fsck encontrou objetos soltos de árvore/blob, mas nenhum commit adicional.
Objetos sem vínculo com commit não foram considerados prova de publicação.
Mensagens/metadados dos 13 commits também foram pesquisados por marcadores de
chave privada, token GitHub e JWT; nenhum desses marcadores foi encontrado.
Identidade de autoria Git não foi reproduzida no relatório.

Essa cobertura inclui todos os commits acessíveis localmente identificados,
não todos os possíveis forks, caches, PRs, releases ou artefatos do GitHub.
Não houve fetch, autenticação administrativa, teste de credencial, consulta a
serviços de produção ou leitura de `.env` real. A árvore remota consultada não
foi truncada. A visibilidade foi confirmada; configuração/alertas de secret
scanning e push protection não foram consultados.

## Triagem de possíveis secrets

Os 55 candidatos foram: 12 conexões com credencial, 31 atribuições reconhecidas
como configuração e 12 literais associados a senha/secret. As contagens incluem
versões históricas e falsos positivos; não representam 55 segredos reais.

| Arquivo/grupo | Tipo e avaliação | Severidade/ação |
| --- | --- | --- |
| `.env.example`, `alembic.ini`, `docker-compose.yml`, `src/core/config.py`, `src/db/database.py`, README histórico | Valores de desenvolvimento/exemplo em conexão; [MASCARADO] | Médio se reutilizados em ambiente real; confirmar uso privadamente e trocar defaults antes de exposição |
| `src/auth/security.py` e Compose histórico | Segredo padrão de desenvolvimento; [MASCARADO]; não confirmado como segredo operacional | Médio condicional; nunca reutilizar o padrão em ambiente compartilhado |
| `src/auth/security.py` | Iterações, algoritmo, tipo de token, duração e conjunto de defaults inseguros confundidos com credenciais | Falso positivo de constante/configuração |
| `tests/test_acesso_seguranca.py`, `test_api_upload_seguranca.py`, `test_ssh_host_keys.py`, `test_api_smoke.py` | Fixtures, entradas inválidas e leitura de variáveis; [MASCARADO] | Exemplos de teste; não credenciais reais confirmadas |
| `frontend/src/views/LoginView.vue` | Atributo/placeholder de senha detectado como literal | Falso positivo de interface |
| Hashes SHA-256, integridades do lockfile e IDs de execução | Integridade/rastreabilidade, sem credencial demonstrada | Não confundir com hash de senha ou token de autenticação |

Os defaults já aparecem no commit público `92501a0`; versões posteriores
também foram examinadas, incluindo o hardening local `a31336a`.
A ausência de confirmação de uso real não permite afirmar que nenhum operador
reutilizou esses defaults. Não foram testados contra banco, API ou pfSense.

A busca por nomes de arquivos encontrou somente `.env.example` e
`frontend/.env.example`. Não encontrou `.env` real, dump SQL, PCAP, log bruto,
chave SSH privada, certificado privado ou backup rastreado nos commits examinados.
Referências textuais a esses arquivos não significam que os arquivos existam
na árvore publicada.

## Achados de exposição e plano

| ID | Evidência e commit de presença pública | Avaliação | Ação recomendada |
| --- | --- | --- | --- |
| E01 | `docs/evidencias/prints/05-detalhe-investigacao.png`, `92501a0` | Médio: endereços do laboratório e identificadores de janela/execução visíveis; valores omitidos | Preparar captura sanitizada ou remover a evidência após decisão; avaliar necessidade de tratar cópias históricas |
| E02 | `docs/evidencias/prints/07-sistema-status.png`, `92501a0` | Baixo: caminhos operacionais, datas e identificador de execução; sem segredo visível | Minimizar dados operacionais na próxima captura; não alterar nesta fase |
| E03 | `docs/context_scored_operational_dataset_report.md`, `docs/final_audit_qa_report.md`, `docs/hybrid_v2_retrain_report.md`, `docs/versioning_fallback_presentation_and_memory_update_report.md`, guia GitHub histórico e `scripts/build_context_scored_operational_dataset.py`; presentes em `92501a0` | Baixo: caminhos absolutos de execução/usuário/ambiente, sem credencial demonstrada | Substituir por caminhos relativos/placeholders em etapa própria; gerador pode reintroduzir o texto |
| E04 | `data/experiments/bruteforce_validation_v2/development/CAP_DEV_001_RUNBOOK.txt` e `reports/first_capture_preparation.txt`, histórico local a partir de `ac2c632` | Baixo: caminhos locais; ausentes da main pública consultada | Revisar antes de qualquer envio dessas versões, preservando evidências congeladas |
| E05 | Defaults de banco/JWT em código/configuração pública desde `92501a0` | Médio condicional, sem uso operacional confirmado | Confirmar privadamente que não foram reutilizados; se foram, tratar como credencial comprometida e rotacionar |

Não tratar todo IPv4 privado como vulnerabilidade: loopback e endereço de bind
não revelam topologia; fixtures e textos simulados da tela de login são exemplos.
O achado E01 se baseia no contexto visual da investigação, não apenas na faixa
do endereço. Hostnames locais genéricos e email administrativo de exemplo não
foram classificados como email pessoal. Não foram reproduzidos valores reais.

## Inventário de arquivos e dados

| Grupo | Classificação | Observação |
| --- | --- | --- |
| Código e guias em geral | Seguro para público dentro desta revisão, com exceções E03/E05 | Não é certificação de segurança funcional |
| `.env.example` e exemplos de configuração | Exemplo de desenvolvimento; requer revisão de uso | Não devem fornecer credenciais para ambiente compartilhado |
| `data/raw/.../README.md` | Histórico aceitável | Único arquivo sob data na main pública; não contém os logs mencionados |
| 26 arquivos locais sob `data/` | Revisão por subgrupo abaixo | Presença no Git local não implica presença na main pública consultada |
| `data/experiments/bruteforce_recent_history_v1/` | Histórico derivado; requer decisão individual | CSV com IDs anônimos e indicadores, relatórios e hashes de integridade; sem IP literal encontrado; anonimização não prova irreidentificabilidade |
| Manifests planejados/templates/.gitkeep/HOLDOUT_LOCKED | Exemplo sanitizado/metodologia | Campos de execução pendentes, papéis genéricos; não contém captura bruta de holdout |
| Relatórios/runbooks experimentais | Histórico aceitável com revisão de caminhos | E04; não reenviar automaticamente |
| `docs/experiments/*metrics.json` | Métricas experimentais agregadas | Sem credencial ou endereço literal encontrado |
| `docs/evidencias/` | Requer revisão | E01 não deveria permanecer público sem sanitização/justificativa; E02 é minimização |
| Logo PNG frontend | Inventariado como asset | Não é captura operacional; sem revisão visual específica nesta fase |
| Modelos serializados/registry em data/models ou models | Nenhum rastreado encontrado | Modelos locais preservados e não carregados |
| Logs reais, PCAPs, dumps, backups, .env real, chaves privadas | Não deveriam estar públicos; não encontrados como arquivos rastreados | Excluir de futuros commits; não confundir menções com conteúdo |

## Revisão individual das screenshots

Todos os arquivos abaixo estão em `docs/evidencias/prints/` e seus blobs
coincidem com a árvore pública. Nenhum foi editado.

| Imagem | Resultado visual |
| --- | --- |
| 01-login-desktop.png | Exemplo de email/fluxo; senha vazia, nenhum segredo visível |
| 02-dashboard-desktop.png | Dados de demo, horários e papel genérico; endereços sem valor visível |
| 03-alertas-filtros.png | Classes, scores e horários de laboratório; sem credencial/endereço visível |
| 04-historico-resumo.png | Contagens agregadas; sem dado pessoal evidente |
| 05-detalhe-investigacao.png | E01: endereços internos e identificadores; requer sanitização |
| 06-relatorios.png | Agregados e data de relatório; sem credencial visível |
| 07-sistema-status.png | E02: caminhos operacionais e identificadores; minimizar |
| 08-admin-usuarios.png | Nome/papel/email genéricos da conta inicial; senha vazia, sem email pessoal identificado |
| 09-configuracoes.png | Nomes de variáveis e explicações; credenciais não exibidas |
| 10-sobre.png | Texto de arquitetura; sem dado sensível evidente |
| 11-login-mobile.png | Texto de apresentação; sem credenciais visíveis no recorte |
| 12-dashboard-mobile.png | Contagens e estado de demo; sem endereço/credencial visível no recorte |

Revisão dos pixels visíveis não certifica metadados PNG nem dados fora dos
recortes. Não houve OCR ou análise esteganográfica.

## Documentação corrigida e referências

Alterados somente Markdown: README principal, `docs/README.md`,
`docs/dados_modelos.md`, `docs/security.md`,
`docs/github_private_publish.md`, nota de correção em
`docs/fase2d_documentacao_padronizacao.md` e este relatório.

As referências ao guia antigo foram mapeadas no README principal,
índice de docs, segurança, relatório da Fase 2D e auditoria histórica final.
O nome do arquivo foi mantido por compatibilidade; título e conteúdo agora
tratam do repositório público. Não há rename nem redirecionamento quebrado.
Menções a “privado” que descrevem dados/ambiente local continuam corretas.
Relatos históricos de intenção de publicação privada não foram reescritos como
se a etapa tivesse conhecido o contexto atual; a correção está explícita.

## Decisões pendentes e resposta a incidente

Prioridade: decidir sanitização da imagem 05; minimizar a 07; planejar remoção
de caminhos locais sem modificar artefatos protegidos ou geradores nesta fase.
Verificar uso dos defaults em ambientes reais e os controles de secret scanning/
push protection com acesso administrativo autorizado.

Se surgir confirmação de segredo real, o procedimento obrigatório é:
revogar/rotacionar, preparar remoção da árvore, avaliar reescrita e impactos em
clones/forks/caches, obter decisão explícita e só então executar push corretivo.
Remover apenas no HEAD não resolve segredo histórico.
[Referência oficial do GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

Nenhuma credencial foi rotacionada/testada, nenhum arquivo sensível removido,
nenhuma imagem sanitizada e nenhum histórico reescrito nesta fase.
Não foram executados filter-repo, BFG ou force push. **Nenhum push realizado.**

## Validação documental

Foram validados 173 links relativos, todos existentes. O diff integral foi
revisado e `git diff --check` passou. Foram conferidos 67 hashes e 563 metadados
protegidos, sem divergências. Apenas sete arquivos Markdown mudaram; nenhuma suíte Python/frontend foi executada
por rotina. Parser, 13 features, modelos, runtime, thresholds, registry,
Candidate v1, schema, migrations, endpoints, autenticação e frontend funcional
permanecem intactos. A Fase 2E não foi iniciada.

A revisão automática interrompeu uma leitura por limite de uso da conta; após
pedido de continuação, a mesma leitura mascarada foi executada com sucesso.
Não houve contorno de restrição nem bloqueio remanescente dessa leitura.
