# Validação consolidada e ajuste direcionado

> **HISTÓRICO — referência anterior à Fase 2D.** Resultados, comandos e termos
> como “atual” descrevem a etapa de origem, não uma validação presente.
> `current` segue ativo; `hybrid_v2_3` é validation-only e Candidate v1 não foi
> promovido. Consulte o [índice atual](README.md).

## Métricas consolidadas

- Bruta: precision `0.6143`, recall `0.7996`, F1 `0.6948`, FPR `0.0204`, ataques que passaram `0.2004`.
- Avaliável: precision `0.6124`, recall `0.8477`, F1 `0.7111`, FPR `0.0204`, ataques que passaram `0.1523`.

## Recall por cenário

- `brute_force`: bruto `0.8232`; avaliável `0.8232`.
- `port_scan`: bruto `0.7222`; avaliável `0.9263`.
- `syn_flood`: bruto `0.8511`; avaliável `0.8511`.

## Status das metas

| Meta | Bruto | Avaliável | Status |
|---|---:|---:|---|
| FPR <= 0.04 | 0.0204 | 0.0204 | bruto=met; avaliável=met |
| recall >= 0.95 | 0.7996 | 0.8477 | bruto=not_met; avaliável=not_met |
| ataques que passaram <= 0.05 | 0.2004 | 0.1523 | bruto=not_met; avaliável=not_met |

## Port scan

- FNs brutos: `35`.
- FNs avaliáveis: `7`.
- FNs não avaliáveis: `28`.
- Erros reais de decisão: `3`.

A métrica bruta foi preservada. A métrica avaliável é complementar e não substitui automaticamente a métrica oficial.

## Recomendação

Fazer ajuste direcionado apenas como experimento. Não baixar threshold global e não promover janelas fracas de `port_scan`.