# Empacotamento do candidato de inferencia

> **HISTÓRICO — referência anterior à Fase 2D.** Resultados, comandos e termos
> como “atual” descrevem a etapa de origem, não uma validação presente.
> `current` segue ativo; `hybrid_v2_3` é validation-only e Candidate v1 não foi
> promovido. Consulte o [índice atual](README.md).

## Respostas objetivas

1. O `hybrid_v2_3` e carregavel como runtime? `False`.
2. Artefatos faltantes no `hybrid_v2_3`: `scaler, isolation, autoencoder_model, threshold, manifest, ensemble`.
3. Existe pacote completo equivalente ao `hybrid_v2_3`? `False`.
4. O runtime ativo atual e empacotavel? `True`.
5. Pacote criado: `current_runtime_frozen_v1` em `data/models/runtime_candidates/current_runtime_frozen_v1`.
6. O pacote criado e equivalente ao `hybrid_v2_3`? `False`.
7. O teste de paridade passou? `parity_not_possible_missing_artifacts`.
8. O registry foi alterado? `False`.
9. `active_profile` mantido? `True`.
10. `fallback_profile` mantido? `True`.
11. O pacote pode ser promovido? `False`.
12. Motivo: Pacote congelado do runtime atual; ele nao e equivalente ao baseline validado hybrid_v2_3..
13. Proximo passo real: Executar novo retreino/calibracao controlada que gere artefatos runtime completos e depois validar paridade antes de qualquer promocao..

## Conclusao obrigatoria

`current_runtime_frozen_only`

## Metricas de paridade

- Baseline salvo no CSV: `{'scope': 'saved_csv_prediction', 'prediction_column': 'baseline_prediction', 'rows': 12402, 'precision': 0.6142857142857143, 'recall': 0.7995867768595041, 'f1_score': 0.6947935368043088, 'false_positive_rate': 0.020389327068300052, 'accuracy': 0.9725850669246896, 'confusion_matrix': {'tn': 11675, 'fp': 243, 'fn': 97, 'tp': 387}, 'false_positives': 243, 'false_negatives': 97, 'scenario_recall': {'brute_force': {'support': 311, 'true_positive': 256, 'false_negative': 55, 'recall': 0.8231511254019293}, 'port_scan': {'support': 126, 'true_positive': 91, 'false_negative': 35, 'recall': 0.7222222222222222}, 'syn_flood': {'support': 47, 'true_positive': 40, 'false_negative': 7, 'recall': 0.851063829787234}}}`
- Recalculo com runtime ativo: `{'scope': 'active_runtime_recalc', 'prediction_column': 'active_runtime_prediction', 'rows': 12402, 'precision': 0.06522882693319305, 'recall': 0.512396694214876, 'f1_score': 0.11572561829211385, 'false_positive_rate': 0.2982043967108575, 'accuracy': 0.6944041283663925, 'confusion_matrix': {'tn': 8364, 'fp': 3554, 'fn': 236, 'tp': 248}, 'false_positives': 3554, 'false_negatives': 236, 'scenario_recall': {'brute_force': {'support': 311, 'true_positive': 97, 'false_negative': 214, 'recall': 0.31189710610932475}, 'port_scan': {'support': 126, 'true_positive': 105, 'false_negative': 21, 'recall': 0.8333333333333334}, 'syn_flood': {'support': 47, 'true_positive': 46, 'false_negative': 1, 'recall': 0.9787234042553191}}}`
- Recalculo com pacote candidato: `{'scope': 'candidate_package_recalc', 'prediction_column': 'candidate_package_prediction', 'rows': 12402, 'precision': 0.06522882693319305, 'recall': 0.512396694214876, 'f1_score': 0.11572561829211385, 'false_positive_rate': 0.2982043967108575, 'accuracy': 0.6944041283663925, 'confusion_matrix': {'tn': 8364, 'fp': 3554, 'fn': 236, 'tp': 248}, 'false_positives': 3554, 'false_negatives': 236, 'scenario_recall': {'brute_force': {'support': 311, 'true_positive': 97, 'false_negative': 214, 'recall': 0.31189710610932475}, 'port_scan': {'support': 126, 'true_positive': 105, 'false_negative': 21, 'recall': 0.8333333333333334}, 'syn_flood': {'support': 47, 'true_positive': 46, 'false_negative': 1, 'recall': 0.9787234042553191}}}`

## Artefatos gerados

- `data/models/runtime_candidate_packaging/runtime_candidate_packaging_summary.json`
- `data/models/runtime_candidate_packaging/model_artifact_inventory.csv`
- `data/models/runtime_candidate_packaging/profile_runtime_readiness.csv`
- `data/models/runtime_candidate_packaging/missing_artifacts_by_profile.csv`
- `data/models/runtime_candidate_packaging/candidate_package_manifest.json`
- `data/models/runtime_candidate_packaging/parity_test_results.json`
- `data/models/runtime_candidate_packaging/parity_divergence_sample.csv`
- `data/models/runtime_candidate_packaging/registry_update_report.md`
- `data/models/runtime_candidate_packaging/runtime_candidate_next_steps.md`
- `docs/runtime_candidate_packaging_report.md`

## Garantias da etapa

- Nenhum modelo foi retreinado.
- Nenhum perfil foi promovido.
- `active_profile` e `fallback_profile` foram preservados.
- Parser, 13 features, API, frontend, banco e Decision Engine oficial nao foram alterados.
