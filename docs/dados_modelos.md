# Dados, modelos e estado dos perfis

Status: **ATUAL**. Este guia não altera artefatos nem autoriza treino/promoção.

| Diretório | Finalidade e cuidado |
| --- | --- |
| `data/raw/pfsense/` | Logs originais; privados, preservar conteúdo e proveniência |
| `data/processed/` | Eventos/features e saídas de processamento/validação |
| `data/runtime/pfsense/live/` | Arquivo local incremental, offsets e estado de processamento |
| `data/runtime/` | Temporários e resultados da API; não é dataset de treino por padrão |
| `data/models/` | Artefatos e perfis registrados; disponibilidade local não significa versionamento Git |
| `data/experiments/` | Evidências e manifests experimentais, incluindo recortes congelados |

## Perfis

| Identificador | Classificação e interpretação |
| --- | --- |
| `current` | OFICIAL; runtime ativo |
| `current_runtime_frozen_v1` | Cópia reprodutível de current; não equivale ao hybrid_v2_3 |
| `hybrid_v2_3` | HISTÓRICO / validation-only; CSVs e relatórios não formam runtime equivalente carregável |
| `sinalyx_runtime_candidate_v1` | EXPERIMENTAL / NÃO PROMOVIDO |
| Protótipos temporais/memória | EXPERIMENTAL / fora do runtime oficial |

O campo histórico `candidate_profile` do registry pode apontar para
`hybrid_v2_3`. Esse nome não comprova artefatos completos, promoção ou equivalência
de métricas com `current`. Nenhum campo do registry foi corrigido nesta fase.
Não existe autorização para Candidate v2.

`src/core/model_registry.py` resolve perfis e fallback;
`src/core/artifacts.py` carrega artefatos. Registre o perfil efetivamente
resolvido, não somente o solicitado. Validar metadados não prova que todos os
modelos carregam nem que sua qualidade é suficiente.

## Rastreabilidade

Preserve origem, hashes, manifesto, janela, unidade de avaliação e separação
DEVELOPMENT/CALIBRATION/HOLDOUT. Não ajustar pelo holdout. Não misturar detecção
binária, tipagem por janela e avaliação por episódio. Métricas de 5 s e 60 s
não são diretamente equivalentes.

Logs do alvo e PCAP podem apoiar ground truth offline; não são entradas do
runtime oficial do TCC. Colunas auxiliares `ctx_*` não mudam as 13 features.

Não copie modelos de fonte desconhecida: formatos serializados exigem confiança.
Não mover, regenerar ou sobrescrever manifests/modelos para organizar o Git.
Cada arquivo exige decisão individual de publicação;
dados operacionais e modelos locais não devem entrar automaticamente no Git.
Veja a [auditoria de exposição](fase2d1_github_public_audit.md), que distingue
arquivos rastreados localmente da árvore pública consultada.
