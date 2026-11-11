# Versao estavel

> **HISTÓRICO — referência anterior à Fase 2D.** Resultados, comandos e termos
> como “atual” descrevem a etapa de origem, não uma validação presente.
> `current` segue ativo; `hybrid_v2_3` é validation-only e Candidate v1 não foi
> promovido. Consulte o [índice atual](README.md).

Data da revisao: 2026-05-19

## Estado validado

- Nome do projeto: Sinalyx.
- Parser real de pfSense preservado.
- Pipeline oficial com 13 features preservado.
- Autoencoder mantido como detector individual principal.
- Isolation Forest mantido como apoio estatistico.
- Heuristica, Ensemble e Decision Engine preservados.
- Cenarios oficiais validados: `normal_firewall`, `port_scan`, `brute_force`, `syn_flood`.

## Artefatos principais

- Modelos atuais: `data/models/`.
- Modelos versionados: `data/models/versions/retrain_20260518_235642/`.
- Dados processados: `data/processed/pfsense/retrain_20260518_235642/`.
- Validacao final: `docs/validation/final_validation_20260518_235642.md`.
- Auditoria: `docs/audit/system_audit_20260518_235642.md`.

## Resultado resumido

Todos os quatro cenarios oficiais passaram na validacao final com o perfil `balanced`.
