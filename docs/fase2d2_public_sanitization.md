# Fase 2D.2 — sanitização de evidências públicas

Data: 9 de setembro de 2026. Branch: `codex/fase2a-baseline`.
Base confirmada com árvore limpa:
`1fcd84c0d8012a718a29174846ecbefedf7e1640`.

## Resultado e escopo

Sanitizadas localmente as screenshots 05/07 e cinco caminhos locais em quatro
documentos históricos. Não houve alteração funcional, de resultado técnico,
modelo, threshold, registry, schema, migration, endpoint ou autenticação.
A Fase 2E não foi iniciada. Nenhum push ou reescrita de histórico foi realizado.

## Arquivos alterados

| Arquivo | Alteração |
| --- | --- |
| `docs/evidencias/prints/05-detalhe-investigacao.png` | Cinco tarjas: origem/destino, origem repetida, ID de janela que contém endereço e identificador de execução |
| `docs/evidencias/prints/07-sistema-status.png` | Três tarjas: identificador de execução e caminhos remoto/local |
| `docs/context_scored_operational_dataset_report.md` | Dois caminhos de executável substituídos por referência neutra; argumentos preservados |
| `docs/final_audit_qa_report.md` | Caminho de perfil/configuração substituído por placeholder |
| `docs/hybrid_v2_retrain_report.md` | Caminho de instalação substituído por referência neutra |
| `docs/versioning_fallback_presentation_and_memory_update_report.md` | Caminho de perfil/configuração substituído por placeholder |
| `docs/README.md` | Índice e estado atual das capturas |
| `docs/fase2d1_github_public_audit.md` | Nota de atualização, sem apagar os achados históricos |
| Este relatório | Método, validação e risco residual |

Não foram alterados os nomes/caminhos dos arquivos nem links para as imagens.

## Método e revisão visual

A tentativa inicial de edição por IA foi rejeitada: ocultou os campos, mas
alterou resolução/tipografia/disposição. Essa saída não substituiu nenhum
arquivo do projeto. Após autorização explícita do usuário, foram aplicadas
tarjas opacas diretamente nos pixels originais, com Pillow do runtime auxiliar
do Codex. Não foram instaladas dependências no projeto.

A venv oficial não possui Pillow; somente a execução auxiliar de edição utilizou
o runtime disponibilizado pelo aplicativo. Nenhuma análise de IA do Sinalyx
foi executada.

Ambas as imagens continuam em **1265 × 720**. Comparação com os originais do
commit-base confirmou **zero pixels diferentes fora das oito áreas de máscara**.
As tarjas são preenchimento opaco, não blur reversível ou camada sobreposta.
O PNG foi salvo novamente, sem copiar metadados opcionais da imagem original.

A revisão visual completa confirmou ausência dos endereços, caminhos e IDs
mascarados. Permanecem os rótulos, datas, scores, contagens, risco, classificação,
estado dos componentes e nome administrativo genérico já existente. Não foram
identificados token, credencial, hostname interno real ou usuário pessoal no
conteúdo visível remanescente. Não foi inventado resultado ou reconstruída tela.

A comparação detalhada de dimensões, retângulos e hashes das imagens ficou
em `fase2d2_comparacao_imagens.json`, fora do Git, nas evidências locais da tarefa.
As duas mudanças de hash são **esperadas e autorizadas**, não corrupção.

## Textos históricos

Foram mantidos os comandos e argumentos técnicos, substituindo somente a parte
do caminho específica da máquina. Referências neutras identificam executável
Python e perfil local. Os comandos continuam evidência histórica, não promessa
de que o caminho de exemplo exista na máquina do leitor.

Verificação automatizada confirmou a preservação de hashes e números/métricas
fora dos trechos de caminho substituídos. Não houve recálculo de resultados,
tradução de identificadores nem reescrita de conclusões históricas.

## Nova auditoria da árvore

Repetida a busca defensiva nos **267 arquivos textuais rastreados** da base de
entrada, lendo a árvore de trabalho após sanitização dos quatro documentos.
Padrões: tokens conhecidos, chave privada, JWT, hash de credencial, conexões com
senha, atribuições de secret, IPv4 privados, hostnames locais e caminhos pessoais.
As imagens foram revisadas visualmente, complementando a varredura textual.

Foram encontrados **27 candidatos heurísticos**: cinco conexões, onze
atribuições de ambiente e onze literais. São os mesmos tipos de
defaults/exemplos, constantes e fixtures examinados na Fase 2D.1; nenhum
segredo operacional real novo foi confirmado. Não houve teste de credenciais
contra serviço real nem leitura de `.env` privado.

Loopback, endereços de bind, hostnames genéricos do projeto, exemplos da tela de
login e fixtures não foram tratados como vazamento de infraestrutura real.
A varredura dos documentos sanitizados não encontrou caminho pessoal restante.
Os novos textos do relatório/índice não reproduzem valores removidos.

## Referências residuais na árvore atual

Não afirmar que todos os caminhos locais existem somente no histórico:

- `scripts/build_context_scored_operational_dataset.py`, linhas 642–643 na base,
  ainda contém caminhos em strings de geração de relatório. O arquivo Python
  foi preservado pela restrição de não alterar arquivos funcionais. Executar
  esse gerador pode reintroduzir o texto; a correção exige escopo próprio.
- `data/experiments/bruteforce_validation_v2/development/CAP_DEV_001_RUNBOOK.txt`
  e `development/reports/first_capture_preparation.txt` mantêm cinco ocorrências
  em documentação experimental. Não foram alterados para preservar os dados/
  artefatos solicitados. Não estavam na main pública consultada na Fase 2D.1.
  Revisar explicitamente antes de enviar essa parte do histórico local.
- Defaults de desenvolvimento permanecem em código/configuração por escopo.
  Seu uso operacional real não foi confirmado; não reutilizá-los em ambiente
  compartilhado. Isso não foi tratado como simples remoção textual de segredo.

## Histórico e proporcionalidade

As versões originais das imagens e caminhos continuam acessíveis nos commits
anteriores. A Fase 2D.1 confirmou o commit público `92501a0` e as imagens
originais no GitHub. **Sem push nesta fase, o conteúdo público não foi substituído**;
os dados não estão apenas no histórico remoto, mas também na árvore pública
consultada anteriormente. Não houve nova consulta remota nesta etapa.

Classificação mantida: IPs associados à investigação de laboratório são exposição
contextual de severidade média; caminhos/IDs operacionais têm severidade baixa.
Não foi comprovada exposição de credencial ou comprometimento de serviço.

Para esses dados, reescrever todo o histórico não se mostrou proporcional como
ação automática: muda hashes, afeta clones e não elimina cópias já obtidas.
Recomendação: revisar o conjunto que será enviado, autorizar publicação das
versões sanitizadas em etapa própria e avaliar histórico apenas se surgir risco
adicional concreto, requisito de privacidade ou decisão do responsável.
Nenhum filter-repo, BFG, reset destrutivo ou force push foi executado.

Se for confirmado segredo operacional real, interromper a sanitização comum,
revogar/rotacionar primeiro e obter plano específico de remediação do histórico.

## Validação final

Validação documental concluída: **175 links locais verificados, nenhum quebrado**;
`git diff --check` sem erros. Diff revisado e restrito aos nove arquivos listados.
Os **67 arquivos protegidos por SHA-256** e os **563 registros de tamanho/data de
modificação** permanecem iguais à referência anterior à Fase 2A. As outras dez
capturas permanecem byte a byte iguais ao commit-base. Somente as duas imagens
autorizadas tiveram seus hashes alterados; os demais arquivos funcionais,
dados, modelos e artefatos não foram modificados.
Não é necessário pytest completo nesta alteração de documentação/imagens.
Nenhum teste funcional, treino, calibração, migração ou serviço Docker foi iniciado.
