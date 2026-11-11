# Fase 4A — auditoria final pré-push do repositório público

Data: 10 de setembro de 2026. **APTO PARA PUSH**, no escopo e com os riscos
residuais descritos abaixo. Esta classificação não autoriza nem executa o push.

## 1. Remote, base e baseline

HEAD de entrada confirmado: `fa731f6`; árvore limpa; branch
`codex/fase2a-baseline`, sem upstream configurado.
Remote `origin`: `https://github.com/AlisonAGomez/sinalyx.git`.
Consulta anônima à API do GitHub confirmou `private=false` e default branch
`main`. `git ls-remote --symref` e `--heads` confirmaram apenas a branch remota
`main`, em `92501a0`, igual à referência local `origin/main`.

Cadeia auditada: **remote HEAD/main `92501a0` → 17 commits locais → `fa731f6`**.
A base é ancestral do HEAD, sem divergência. A branch local `main` está em
`431c129`, oito commits à frente do remoto; publicar somente essa branch local
não enviaria as fases de engenharia e QA. O destino recomendado é uma nova
branch remota `codex/fase2a-baseline`, para revisão antes da integração à main.

## 2. Commits pendentes de publicação

| Commit | Mensagem |
| --- | --- |
| `e5011c0` | experimento: avaliar historico recente de forca bruta |
| `74d2b59` | docs: congelar protocolo experimental de força bruta |
| `3ab425c` | feat: preparar infraestrutura de novas capturas |
| `ac2c632` | feat: preparar piloto da primeira captura development |
| `4f51589` | experiment: add Python 3.10 compatible history prototype |
| `437d1df` | experiment: preparar repetição segura da CAP_DEV_001 |
| `70cff98` | fix(parser): accept local RFC3164 filterlog lines |
| `431c129` | feat(experimental): integrate causal brute-force temporal context safely |
| `72724df` | chore: establish reproducible development baseline |
| `20cdf01` | security: harden analysis upload and error handling |
| `a31336a` | security: harden access and deployment defaults |
| `d5010fe` | docs: standardize project documentation and structure |
| `1fcd84c` | docs: align repository guidance with public hosting |
| `58bde18` | docs: sanitize public repository evidence |
| `80b55d5` | chore: improve operational reliability |
| `25fc459` | docs: record phase 3 QA environment interruption |
| `fa731f6` | test: complete integrated regression validation |

Os oito primeiros são trabalho experimental/parser anterior à Fase 2A, não
mudanças introduzidas pela auditoria. Os seguintes correspondem a 2A, 2B, 2C,
2D, 2D.1, 2D.2, 2E e 3, incluindo o registro legítimo de interrupção.
Após o commit documental desta auditoria haverá **18 commits** pendentes;
a lista acima fixa o conjunto de entrada, sem autorreferência ao hash do relatório.

## 3. Secret scan

Inspeção das árvores de todos os 17 commits, da base e do HEAD, deduplicando
conteúdo por blob: **396 blobs**, sendo **381 textuais** e **182 blobs novos
em relação à base pública**. A leitura de snapshots cobre também versões
intermediárias que não aparecem no diff final. Complemento no diff base→HEAD
e nas mensagens dos commits. A árvore rastreada estava limpa e igual ao HEAD.

Varredura heurística local via Python/Git: formatos conhecidos de tokens,
JWT, chaves privadas, certificados, URLs autenticadas, conexões com senha,
atribuições de password/secret, arquivos de ambiente e extensões sensíveis.
Gitleaks/TruffleHog não estavam disponíveis no PATH; não se afirma execução
dessas ferramentas ou verificação de credenciais contra serviços.

Resultado: **nenhum segredo operacional real confirmado**. Nenhum formato
conhecido de token/chave privada encontrado. Doze blobs com strings de conexão
usam defaults explícitos do projeto; seis blobs com atribuições correspondem a
default local ou fixtures de teste. As ocorrências de email são exemplos locais
ou fixtures. Senhas/secret operacionais no `.env.example` permanecem vazios;
valor numérico de expiração de token não é credencial.

Não há novo `.env` real, dump, PCAP, chave/certificado privado, backup ou arquivo
`.log` na cadeia inspecionada. Os nomes de arquivos restritos mencionados em
runbooks não significam que esses arquivos tenham sido versionados. Defaults
públicos não devem ser usados como credenciais reais de ambiente compartilhado.
Nenhuma senha ou token foi reproduzido neste relatório.

Limite: padrões e revisão contextual não garantem ausência absoluta de todo
segredo possível, nem atestam configurações administrativas de push protection.
Os arquivos privados ignorados de QA não fazem parte dos objetos enviados.

## 4. Privacidade e referências locais

Sanitizações de Markdown da Fase 2D.2 permanecem no HEAD. Os documentos públicos
principais usam caminhos neutros e distinguem evidência histórica de estado atual.

Revisão explícita das referências residuais já apontadas na Fase 2D.2:

| Local | Evidência e classificação |
| --- | --- |
| `data/experiments/bruteforce_validation_v2/development/CAP_DEV_001_RUNBOOK.txt`, linhas 51, 62, 143, 154 | Quatro caminhos absolutos de uma instalação local com perfil genérico; novos em relação à main pública |
| `data/experiments/bruteforce_validation_v2/development/reports/first_capture_preparation.txt`, linha 73 | Um caminho do mesmo tipo, também ainda não publicado |
| `scripts/build_context_scored_operational_dataset.py`, linhas 642–643 | Strings antigas capazes de reintroduzir caminhos no relatório gerado; já presentes na base pública |

Os cinco caminhos dos documentos experimentais usam nome de perfil genérico,
não identificam uma pessoa e não contêm credencial. Classificação: **resíduo
contextual de baixa severidade, não bloqueador**. Não se declara que toda
referência local foi removida. A revisão pendente foi feita nesta fase;
neutralizar esses exemplos permanece melhoria documental, sem alterar dados
protegidos ou geradores nesta inspeção. Versões intermediárias do runbook
existem em `ac2c632` e `437d1df`; um patch somente no HEAD não as apagaria.

IPs privados encontrados em versões de exemplo/configuração foram avaliados
como parâmetros de laboratório, não automaticamente como incidente. Não foram
encontrados emails pessoais no conteúdo textual examinado. Metadados de autoria
Git não são apresentados como credenciais nem eliminados pela auditoria.

## 5. Screenshots e histórico público

Revisão visual atual das imagens 05 e 07 confirmou tarjas opacas, com conteúdo
técnico preservado e sem valores sensíveis visíveis nas áreas mascaradas.
Seus blobs coincidem exatamente com `58bde18`; não houve regressão da sanitização.
São as únicas imagens alteradas desde a base pública. As demais mantêm a revisão
e os bytes previamente conferidos; não há nova captura de QA na cadeia.

As versões originais das imagens e textos continuam no ancestral público
`92501a0`. O push comum publicará a árvore sanitizada na branch de destino,
mas não elimina conteúdo já público do histórico, clones ou caches. Esse risco
contextual de laboratório já foi documentado em 2D.1/2D.2, sem comprovação de
credencial exposta. Não se considerou proporcional reescrever automaticamente
o histórico. Não houve edição de imagem, force push ou remoção de objetos.

## 6. Dados e modelos

O diff total contém **25 caminhos em `data/experiments/`**, introduzidos antes
da Fase 2A: protocolos, manifests, relatórios, marcadores e resultados derivados.
Não são modelos de runtime nem novas capturas brutas. O relatório de CAP_DEV_001
mantém explicitamente a tentativa invalidada por captura não preservada;
não foi fabricado arquivo para preencher a lacuna experimental.

Entre `431c129` e o HEAD não há mudança em `data/`, `src/models/`, registry
ou utilitário de artefatos. No intervalo completo remoto→HEAD há alterações
legítimas anteriores em código temporal/parser/pipeline, especialmente `431c129`
e `70cff98`; não seria correto afirmar que essas áreas nunca mudaram na cadeia.
Não há diff em `data/models/` ou `models/`, nem promoção ou alteração de pesos,
thresholds/registry de runtime pelas fases de engenharia/QA.

## 7. Arquivos grandes e artefatos

Maior blob novo: `prototype_results.csv`, **3.975.303 bytes**. Nenhum blob novo
atinge sequer 5 MB. Não foi detectado impedimento de tamanho neste conjunto.
Nenhum modelo foi removido por tamanho e não há duplicata nova de modelo.

| Material | Classificação | Justificativa |
| --- | --- | --- |
| CSV do protótipo | Necessário como evidência experimental derivada | 12.402 linhas, 86 colunas; identificador anônimo e medidas/contexto; sem colunas de IP, hostname, usuário, email, senha ou timestamp; nenhuma sequência IPv4 encontrada |
| Relatórios/manifests experimentais | Necessário; referências locais revisadas acima | Rastreabilidade e resultados negativos preservados, sem captura bruta |
| Imagens 05/07 | Necessárias | Versões sanitizadas, 320.463 e 300.218 bytes |
| Lockfile frontend | Necessário | 98.806 bytes, dependências reproduzíveis |
| Dumps, `.env`, logs brutos e saídas privadas da Fase 3 | Não publicar | Fora da cadeia Git; mantidos no ambiente privado |

O CSV não foi tratado como dado bruto de firewall: a estrutura e todo o texto
foram inspecionados. Anonimização de identificadores não torna qualquer dataset
universalmente anônimo; nenhuma identidade direta foi encontrada neste artefato.

## 8. Coerência da documentação

README, dados/modelos, arquitetura, versionamento e relatórios atuais mantêm:

- Sinalyx como nome oficial; PostgreSQL como banco oficial.
- `POST /analyze/pfsense` oficial; `/predict` LEGADO/compatibilidade.
- current ativo; current_runtime_frozen_v1 como cópia reprodutível.
- hybrid_v2_3 HISTÓRICO/validation-only; Candidate v1 NÃO PROMOVIDO.
- Contexto temporal EXPERIMENTAL e fora do fluxo oficial.
- Sem promessa de bloqueio automático, Candidate v2, IA isolada ou coleta real
  contínua concluída; métricas históricas identificadas como históricas.

Relatos históricos foram preservados com avisos de contexto, não convertidos
em alegações atuais. O relatório da Fase 3 continua APROVADO COM RESSALVAS.

## 9. Ressalvas da Fase 3 e janela 11

Resultados reutilizados, sem repetir QA integrada: **204 passed, 4 skipped**;
smoke autenticado + parser: **8 passed, 1 skipped**. Totais não somados.

A causa da janela 11 é conclusiva para aquele ambiente: o smoke fixa
`/history/windows/11` e marca skip em HTTP 404. O banco foi criado vazio e o
processamento sintético gerou somente três janelas, IDs 1, 2, 3, conforme as
consultas e o relatório da Fase 3. A janela 1 foi validada pela API e interface.
Classificação: **dado ausente no banco de QA; comportamento esperado para esse
conjunto**, com acoplamento do teste a um ID fixo como limitação do teste.
Não há evidência de defeito da rota, migração ou persistência. Não foi inserido
dado artificial, alterado teste nem executado novo cenário para apagar o skip.

SSH real ainda não testado; cobertura visual limitada aos cenários registrados,
sem alertas positivos na fixture normal. Essas ressalvas limitam o QA, mas não
constituem vazamento nem impedem publicar honestamente o estado documentado.

## 10. Git diff e validações leves

Diff de entrada remoto→HEAD: **144 arquivos**, 26.615 inserções e 1.709 remoções.
Revisão de nomes, blobs históricos, conteúdo textual, duas imagens alteradas,
artefatos grandes e documentação. `git diff --check origin/main HEAD` passou.
**178 links Markdown relativos para arquivos existentes**, zero quebrados,
antes de adicionar este relatório; destinos remotos e âncoras não certificados
por esse verificador local.

Nenhum arquivo funcional mudou nesta fase. Não foi necessário iniciar Docker,
refazer pytest, npm, inferência ou backup/restore. Este relatório é a única
alteração destinada ao commit documental; scripts e saídas auxiliares ficaram
fora do repositório. Índice selecionado explicitamente, sem `git add .`.

## 11. Preservação

Rechecagem das referências anteriores à Fase 2A: **67 hashes SHA-256 e 563
registros de metadados, zero divergências**. Não foram alterados modelos,
dados protegidos, thresholds ou registry para passar a auditoria.

## 12. Riscos residuais e condição de publicação

Referências genéricas de instalação nos experimentos e gerador antigo permanecem
como baixa severidade; versões não sanitizadas já públicas continuam no histórico.
Secret scan é heurístico, sem validação online de credenciais. Resultado vale
para o conjunto inspecionado: novos commits ou alteração do remoto exigem
reconferência antes de publicar. Não foi encontrada razão concreta para bloquear
esta cadeia; tampouco se declara risco zero ou remoção retroativa de conteúdo.

## 13. Status final e comando futuro

**APTO PARA PUSH** do conjunto auditado e do commit documental desta fase.
Não houve push, reescrita de histórico, reset, alteração de modelos ou nova feature.

Após autorização explícita, o comando recomendado é:

```powershell
git push -u origin codex/fase2a-baseline
```

Destino: nova branch remota `codex/fase2a-baseline`. Integração à `main` fica
para revisão posterior. O comando acima não foi executado; não utiliza force.
