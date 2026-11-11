# Auditoria de alinhamento do perfil ativo

> **HISTÓRICO — referência anterior à Fase 2D.** Resultados, comandos e termos
> como “atual” descrevem a etapa de origem, não uma validação presente.
> `current` segue ativo; `hybrid_v2_3` é validation-only e Candidate v1 não foi
> promovido. Consulte o [índice atual](README.md).

## Respostas objetivas

1. Perfil ativo carregado hoje: `current`.
2. Runtime ativo alinhado ao `hybrid_v2_3`: `misaligned`.
3. Artefatos que divergem: `['autoencoder_model', 'ensemble', 'isolation', 'manifest', 'scaler', 'threshold']`.
4. Model registry aponta para perfil correto? Ativo=`current`, candidato=`hybrid_v2_3`; o ativo nao aponta para `hybrid_v2_3`.
5. Existe fallback carregando artefatos errados? `Sim`; `hybrid_v2_3` nao tem artefatos runtime completos e o fallback configurado e `current`.
6. Thresholds batem? `Nao comprovavel`; `hybrid_v2_3` nao possui `threshold.pkl`/`ensemble.json` no diretorio.
7. Pesos do ensemble batem? `Nao comprovavel`; o runtime ativo usa `data/models/ensemble.json`, mas `hybrid_v2_3` nao tem ensemble config runtime.
8. Normalizacao de score bate? `Nao comprovavel`; faltam scaler e artefatos runtime do `hybrid_v2_3`.
9. Decision Engine chamado no replay e o atual do codigo, nao um pacote congelado do baseline.
10. Inversao de classe suspeita? `True`.
11. `active_runtime_recalc` reproduz baseline? `False`.
12. `hybrid_v2_3_forced_recalc` reproduz baseline? `unavailable_missing_runtime_artifacts`.
13. Por que o full replay deu FPR alto? Porque recalculou as 12402 janelas com runtime `current`, enquanto o baseline `hybrid_v2_3` e um CSV/relatorio candidato sem artefatos runtime carregaveis.
14. Problema principal: configuracao/artefato reprodutivel ausente; o replay tambem nao deve ser usado como equivalencia de baseline.
15. Correcao: congelar pacote runtime do candidato e impedir fallback silencioso antes de promover.
16. Promocao/correcao automatica agora? `Nao`.

## Metricas de paridade

| Modo | Precision | Recall | F1 | FPR | Accuracy |
|---|---:|---:|---:|---:|---:|
| reported_baseline | 0.6143 | 0.7996 | 0.6948 | 0.0204 | 0.9726 |
| active_runtime_recalc | 0.0652 | 0.5124 | 0.1157 | 0.2982 | 0.6944 |

## Divergencia linha a linha

- Mesma decisao: `8478`.
- Decisao alterada: `3924`.
- Normal para ataque: `3548`.
- Ataque para normal: `376`.
- Concentra em normal_block_heavy: `True`.

## Artefatos gerados

- `data/models/runtime_profile_alignment_audit/runtime_profile_alignment_summary.json`
- `data/models/runtime_profile_alignment_audit/artifact_alignment_matrix.csv`
- `data/models/runtime_profile_alignment_audit/runtime_loaded_artifacts.json`
- `data/models/runtime_profile_alignment_audit/hybrid_v2_3_artifacts.json`
- `data/models/runtime_profile_alignment_audit/scoring_parity_metrics.json`
- `data/models/runtime_profile_alignment_audit/prediction_divergence_summary.json`
- `data/models/runtime_profile_alignment_audit/prediction_divergence_sample.csv`
- `data/models/runtime_profile_alignment_audit/runtime_alignment_recommendations.md`
- `docs/runtime_profile_alignment_audit_report.md`

## Comandos executados

- `python scripts/audit_runtime_profile_alignment.py`
- `python -m compileall src scripts`
- validacao JSON dos artefatos gerados
- varredura de IP bruto nos artefatos gerados
- validacao de `FEATURE_COLUMNS` sem `ctx_*`

## Comandos nao executados

- Docker nao executado por escopo.
- Frontend nao executado por escopo.
- Pytest nao executado por escopo.

## Conclusao

O problema e desalinhamento de runtime/artefatos: `hybrid_v2_3` nao e carregavel como perfil de inferencia completo, o registry mantem `current` como ativo e fallback, e a recalculacao usa o runtime atual. Nao aplicar promocao automatica; primeiro congelar pacote runtime reprodutivel do candidato e bloquear fallback silencioso.