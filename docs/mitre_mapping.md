# Mapeamento MITRE ATT&CK

O MITRE ATT&CK e usado no Sinalyx apenas como enriquecimento explicativo. Ele nao substitui IA, heuristica, ensemble nem Motor de decisao.

## Classes mapeadas

| Classe Sinalyx | Taticas / tecnica | Uso |
| --- | --- | --- |
| `port_scan` | Reconhecimento / T1595 - Active Scanning | Varredura ativa de portas ou servicos. |
| `brute_force` | Acesso a credenciais / T1110 - Brute Force | Multiplas tentativas contra servico sensivel. |
| `syn_flood` | Impacto / T1498 - Network Denial of Service | Tentativa de indisponibilizar servico por alto volume de conexoes. |
| `syn_flood` | T1498.001 - Direct Network Flood | Subtecnica opcional para flood direto. |

## Classes sem tecnica MITRE atribuida

- `normal`
- `suspicious`
- `unknown_anomaly`

Essas classes nao recebem tecnica ofensiva validada. A interface deve mostrar que a tecnica MITRE e indefinida, nao inventar mapeamento.

## Modulo

```text
src/security/mitre_mapping.py
```

Funcoes:

- `get_mitre_mapping(attack_type)`
- `has_mitre_mapping(attack_type)`
- `enrich_with_mitre(payload)`

## Regras

- MITRE e explicacao, nao criterio de decisao.
- Nao citar classes nao validadas como resultado medido.
- Nao mapear Slowloris ou tecnicas nao avaliadas.
- Se for integrado a API no futuro, adicionar campo opcional `mitre` sem remover campos atuais.
