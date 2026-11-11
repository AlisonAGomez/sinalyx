# Fase 3 — QA integrado e regressão final

Data: 10 de setembro de 2026. **APROVADO COM RESSALVAS**.

Base: `80b55d5005b66294d4c522b032050e14ebfc022d`, branch
`codex/fase2a-baseline`, árvore limpa confirmada no início. O commit documental
`25fc45972bbc1695d49a821f512ac7c952093bd1` registrou a interrupção inicial.
Esta retomada conclui somente a Fase 3, sem push nem início de outra fase.

## 1. Ambiente e isolamento

| Componente | Versão observada |
| --- | --- |
| Windows 11 Enterprise | NT 10.0.26200 |
| Python do host | 3.10.11, ambiente `.venv` |
| Python da imagem | 3.10.21, imagem `python:3.10-slim` |
| Node / npm | 24.19.0 / 11.17.0 |
| Docker cliente e daemon | 29.7.2 |
| Docker Compose | 5.3.1 |
| PostgreSQL | 16.15, Debian 16.15-1.pgdg13+2 |
| Navegador de QA | Microsoft Edge headless, Playwright |

Exportação dos arquivos Git da base em diretório privado externo ao repositório.
`.env` novo baseado em `.env.example`, com credenciais aleatórias exclusivas
para QA. Nenhum banco, volume, container ou `.env` do PC anterior foi copiado.
Projeto Compose `sinalyxqafase3`; volumes de PostgreSQL e saída criados nesta
execução. A retomada preservou esses volumes, sem reiniciar a fase.

Modelos current são uma dependência externa não versionada, montada somente
leitura. Portanto, a execução comprova integração limpa com os artefatos
fornecidos, não reconstrução dos modelos a partir de Git sozinho.
OMP e threads intra/inter-op do TensorFlow limitados a 1 no ambiente de QA.
Não houve alteração global de energia, WSL, drivers ou recursos do Docker.

## 2. Docker e Compose

`docker compose config --quiet`, build de API/frontend e `up -d`: concluídos.
Serviços esperados: frontend, api e postgres; os três saudáveis no fechamento.
Portas 80, 8000 e 5432 publicadas somente em `127.0.0.1`.
A API foi reconstruída e recriada após o patch; os dados de QA foram mantidos.

Build inicial baixou dependências Linux, inclusive TensorFlow. Retomadas
aproveitaram somente camadas produzidas nesta própria execução. Avisos de pip
como root na construção e debconf sem terminal não impediram o build; o
Dockerfile executa a aplicação com usuário `sinalyx`.

Três containers adicionais isolados testaram dependências ausentes nas portas
loopback 18001–18003, sem parar o PostgreSQL principal. Foram removidos após
os testes. Nenhum container de outro projeto foi alterado.

## 3. Frontend

QA conectado à API e ao PostgreSQL sintéticos: login, dashboard, demo, alertas,
histórico, relatórios, detalhes de análise, detalhes de janela, sistema/auditoria,
administração de usuários, settings e logout. Páginas localizadas pelos
`data-testid` existentes; sem erro JavaScript observado ou erro visível de carga.

Desktop 1366 × 900 e verificação básica mobile 390 × 844: sem transbordamento
horizontal nos cenários medidos. Login inválido apresentou erro; logout voltou
a login. Usuário comum tentando abrir administração foi redirecionado.
Dados integrados e estados vazios de alertas foram observados. Capturas privadas
foram mantidas fora do Git; isso não representa teste de todos os dispositivos
nem cobertura visual de todos os estados de erro possíveis.

## 4. API e sondas

| Cenário HTTP real | `/health` | `/live` | `/ready` |
| --- | --- | --- | --- |
| Stack completa, direta e proxy | 200, banco disponível | 200 | 200 |
| Container sem modelos | 200, banco disponível | 200 | 503 |
| Container com conexão de banco recusada | 200, banco indisponível | 200 | 503 |
| Container com Autoencoder oculto, demais arquivos presentes | não necessário | 200 | 503 |

Falhas foram produzidas em containers próprios. No preload parcial, montagem
temporária vazia ocultou o Autoencoder apenas naquele container; os arquivos
originais permaneceram somente leitura. Readiness devolveu somente
`not_ready`, sem publicar causa interna. O contrato compatível de health foi
preservado, inclusive 200 quando o banco está indisponível.

## 5. Proxy e Swagger

Frontend em `http://localhost/`; API direta em `http://127.0.0.1:8000` e pelo
prefixo `http://localhost/api`. Health, live e ready retornaram 200 por ambos.

**QA-04 reproduzido antes da correção:** `/api/docs` apontava para
`/openapi.json`, que no frontend devolvia HTML 200. O schema correto estava em
`/api/openapi.json`. O navegador apresentava falha ao renderizar o schema.

Patch pequeno em `src/api/main.py`: documentação Swagger com URL relativa
`./openapi.json` e servidor OpenAPI relativo `.`. Não altera as rotas de negócio.
Dois testes de regressão falharam antes e passaram depois do patch. Após rebuild,
Swagger carregou no Edge por ambos os acessos. **Try it out de `/live` retornou
200 usando respectivamente `/live` e `/api/live`**, sem depender de ajuste manual.

## 6. PostgreSQL

`pg_isready` aceitou conexões. Bootstrap criou `users`, `analyses`,
`analysis_results` e `live_pfsense_windows`. PK `id` nas quatro tabelas;
FK de `analysis_results.analysis_id` para `analyses.id`. Índices conferidos
para email/role, created_at, analysis_id e campos live de execução, janela,
timestamp e window_uid. Não houve divergência operacional com o ORM.

Primeiro conjunto: 3 usuários, 2 análises, 27 resultados e 3 janelas live.
A repetição da análise após o patch acrescentou 2 análises e 27 resultados;
as 3 janelas live permaneceram as mesmas. Nenhum dado pessoal foi utilizado.

## 7. Migrations

Banco PostgreSQL novo e descartável: `alembic upgrade head` retornou 0;
`alembic_version = 20260505_0001`. Quatro tabelas da aplicação mais a tabela
Alembic. Colunas compatíveis com o ORM. Nenhum `stamp`, alteração de migration
antiga ou ajuste estético de schema.

## 8. Seed

Teste real no PostgreSQL migrado vazio: primeira execução criou admin;
repetição não criou outro. Para contas existentes admin/comum, ativas/inativas,
foram preservados role, atividade, hash de senha e updated_at. Sem senha de seed,
conta ausente não foi criada. Não houve promoção ou reativação silenciosa.

## 9. Autenticação e permissões

| Cenário | Resultado |
| --- | --- |
| Login admin / comum | 200 / 200 |
| Credenciais inválidas / usuário inativo | 401 / 401 |
| Token malformado / expirado | 401 / 401 |
| Anônimo em administração | 401 |
| Comum em administração e auditoria | 403 |
| Admin em administração e auditoria | 200 |
| Comum em `/auth/me` e consultas autenticadas | 200 |
| Logout na interface | retorno ao login |

Rate limit real em API isolada: após esgotar tentativas, HTTP 429;
`Retry-After` positivo dentro da janela de 60 s. Após aguardar sua expiração,
login inválido voltou a 401, comprovando reset da janela. O primeiro leitor de
headers do script privado precisou normalizar caixa; não era defeito da API.
O limitador permanece local ao processo, conforme implementação existente.

## 10. Runtime current

Registry com perfil ativo current; scaler, Isolation Forest, Autoencoder,
threshold e manifest presentes no container. Preload completo e readiness 200.
Manifest contém a definição das features; resultados reais de inferência
contêm as 13 features oficiais, saídas de IF/AE, heurística, Ensemble e decisão.

Nenhum treino, calibração, alteração de threshold, promoção de Candidate ou uso
de holdout. Esta fase comprova compatibilidade operacional, não qualidade
estatística ou generalização do detector.

## 11. Análise pfSense

Fixture sintética com endereços reservados para documentação. Uma linha válida
produziu 1 janela; arquivo de 130 linhas produziu 26 janelas no fluxo de upload.
Ambos HTTP 200, `database_saved=true`, detalhes e resultados consultáveis.
Repetição após patch preservou esse comportamento.

Vazio: 400; extensão inválida: 415; log inválido: 422. Sem traceback público.
Excesso de tamanho coberto pela suíte automatizada existente, inclusive sem
Content-Length, limite exato e cleanup; não foi criado arquivo enorme.
Diretório de uploads temporários vazio após os cenários executados.

## 12. Histórico

Consultas retornaram 200. Com três janelas live, `limit=1&offset=0` retornou ID 3,
offset 1 retornou ID 2 e offset 99 retornou lista vazia. Filtro `final_label=normal`
retornou IDs 3, 2, 1; data futura retornou lista vazia. Ordenação e separação das
páginas verificadas; detalhe da janela existente acessível pela API e interface.
Sem mudança de paginação ou promessa de desempenho com grandes bases.

## 13. Alertas

Consultas de alertas recentes e histórico: 200. A fixture produziu resultados
normais; estado vazio exibido corretamente. Não se atribui a esse conjunto
cobertura visual de alertas positivos nem avaliação de detecção de ataques.

## 14. Relatórios e detalhes

Relatórios, resumos, execuções, análises e detalhes carregaram com os dados de
QA. Detalhes de análise mostraram resultados persistidos; detalhe de janela
mostrou a inferência live. Não houve redesign ou feature de relatório nova.

## 15. Backup e restore

Scripts versionados executados contra bancos exclusivamente descartáveis.
Dump SQL de **102.613 bytes**, não vazio. Restore via `psql` em transação única
concluiu com sucesso em banco novo; contagens **3 / 2 / 27 / 3** iguais às da
origem no instante do backup. Isso também validou o dump com PostgreSQL real.

Cópia privada do dump recebeu instrução SQL deliberadamente inválida. Restore
retornou **exit 1** e o destino ficou com **zero tabelas públicas**, confirmando
rollback. Dump original preservado. **Backup aprovado; restore aprovado**.
Dumps, senhas e arquivos privados de QA não foram adicionados ao Git.

## 16. Live local

`python -m src.pipelines.process_live_pfsense --skip-collect --finite-file`:
130 linhas lidas, 130 parseadas, 3 janelas de um minuto persistidas. Offset
0 → 18.720 bytes; repetição terminou com zero linhas/janelas novas e offset
inalterado. Banco continuou com 3 registros e nenhum window_uid duplicado.

Não foi executado SSH real nem afirmada coleta contínua diretamente de pfSense.
Credenciais/known_hosts reais continuam pendentes fora deste QA local.

## 17. Segurança e logs

Verificação dos logs da API contra senhas sintéticas, secret JWT, senha do banco
e tokens gerados: nenhuma ocorrência. Sem linha completa `filterlog:` nos logs
observados. Respostas de erro sanitizadas; login retorna token somente como
parte prevista do contrato. Não se confunde essa amostragem com prova universal
de ausência de vazamento em todos os caminhos possíveis.

Configuração, dump, capturas e saídas brutas ficaram fora do repositório.
Revisão do diff e dos arquivos selecionados para commit, sem `.env` ou dados
sensíveis. Nenhum push autorizado ou executado.

## 18. Testes automatizados

| Execução | Resultado |
| --- | --- |
| Baseline host antes da stack | 199 passed, 7 skipped, 2 subtests passed |
| Regressão após patch, stack ativa sem credenciais no pytest | 204 passed, 4 skipped, 17 subtests passed; 141,98 s |
| Smoke HTTP com credenciais de QA + parser explícito | 8 passed, 1 skipped, 15 subtests passed; 53,69 s |
| Dois testes novos de Swagger | falharam antes; passaram depois; incluídos na regressão |
| Compileall oficial após patch | exit 0 |
| npm ci / npm audit | exit 0; zero vulnerabilidades reportadas |
| npm run typecheck / npm run build | exit 0; build com 1.693 módulos |
| Docker config / build / up / sondas | aprovados |

Os totais das execuções se sobrepõem e não devem ser somados. Os quatro skips
na regressão eram os casos autenticados. Na execução autenticada, resta somente
o teste que fixa `/history/windows/11`: a janela 11 não existe no banco novo.
O detalhe da janela real 1 foi validado separadamente, inclusive na interface.
Skip não foi contado como aprovação. Parser explícito: 2 testes aprovados.

Compileall mantém exclusão do protótipo experimental congelado
`bruteforce_recent_history_prototype.py`. Dois avisos existentes de `on_event`
depreciado; aviso de depreciação de lucide-vue-next e aviso npm 11 relativo ao
install script do esbuild. Instalação, auditoria e build passaram sem migrar
bibliotecas ou mudar política global.

## 19. Achados registrados

| ID | Classe / severidade | Reprodução, esperado e impacto | Tratamento |
| --- | --- | --- | --- |
| QA-01 | AMBIENTE / bloqueador inicial | CLI instalado, pipe do daemon ausente; esperado Docker ativo | Desktop iniciado, resolvido sem patch |
| QA-02 | MELHORIA FUTURA / baixa | npm avisa depreciação de lucide-vue-next; build funciona | Registrado, sem migração fora de escopo |
| QA-03 | AMBIENTE / alta para continuidade | Sessões interrompidas e Docker encerrado; esperado execução contínua | Usuário informou bateria descarregada; retomada autorizada, sem atribuição ao código |
| QA-04 | BUG DE INTEGRAÇÃO / média | Swagger no proxy busca schema fora de `/api`, recebe HTML e falha | Corrigido em `src/api/main.py`, testes e navegador aprovados |

A hipótese QA-04 foi registrada e reproduzida antes do patch. Uma tentativa de
rebuild também foi interrompida por limite de uso da revisão automática de
aprovação; retomada posterior concluiu normalmente. Não houve contorno dessa
restrição nem mudança de código para mascarar problema ambiental.

## 20. Correções

Única mudança funcional: URLs relativas de Swagger/OpenAPI. Teste novo em
`tests/test_documentacao_proxy.py`; atualização da referência de deploy e deste
relatório. Sem refatoração de arquitetura, parser, features, persistência ou
motor de decisão. Correção validada na mesma stack de QA após rebuild.

## 21. Pendências e ressalvas

- SSH/coleta real do pfSense não validado; QA live foi exclusivamente local.
- Smoke existente fixa janela 11 e ficou skipped; janela existente validada à parte.
- Alertas positivos e todos os estados visuais de erro não foram exercitados com
  a fixture normal; não se fabricou resultado de modelo para satisfazer QA.
- Modelos precisam ser fornecidos fora do Git; imagem Python e dependências Linux
  resolvidas pelo build não equivalem a lock integral do ambiente host 3.10.11.
- Warnings de depreciação permanecem, sem impacto observado nesta execução.

## 22. Preservação

Rechecagem após inferências e regressão: **67 hashes protegidos e 563 registros
de metadados, zero divergências**. Modelos, dados protegidos, registry e thresholds
inalterados. Nenhuma mudança de runtime ou resultado deliberadamente ajustado.

## 23. Resultado final

**APROVADO COM RESSALVAS** para integração operacional local: Compose → frontend
→ proxy → FastAPI → PostgreSQL → current → persistência → interface, incluindo
falhas controladas e restauração real. Ressalvas acima delimitam a cobertura;
não impedem o fluxo local validado e não são apresentadas como testes aprovados.
A Fase 3 termina aqui. Commit somente local, sem publicação e sem nova fase.
