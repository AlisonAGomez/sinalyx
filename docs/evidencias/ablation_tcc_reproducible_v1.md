# Sinalyx — Evidência de ablação do TCC

- Status: **VALIDAÇÃO / EXPERIMENTAL**
- Runtime avaliado: `current`
- Janelas: **355**
- Paridade do Ensemble: **355/355**
- Paridade do Decision Engine: **355/355**
- Diferença máxima do `ensemble_score`: **0.000000000000**

## Resultado principal

| Variante | Precision | Recall | F1 | FPR | FN rate |
|---|---:|---:|---:|---:|---:|
| Pipeline híbrido oficial | 99.48% | 91.43% | 95.29% | 0.69% | 8.57% |
| Sem sinal do Isolation Forest | 99.48% | 91.43% | 95.29% | 0.69% | 8.57% |
| Sem sinal do Autoencoder | 100.00% | 90.00% | 94.74% | 0.00% | 10.00% |
| Heurística isolada | 100.00% | 90.00% | 94.74% | 0.00% | 10.00% |

## Conclusões suportadas pelos dados

- O Autoencoder apresentou contribuição causal direta: sua neutralização removeu **3** detecções ofensivas que estavam presentes no pipeline oficial.
- O Isolation Forest não alterou a decisão binária final neste conjunto, mas modificou o score do Ensemble em **351/355** janelas (98.87%) e alterou **3** predições intermediárias do Ensemble.
- A heurística isolada atingiu recall de **90.00%**, enquanto o pipeline híbrido atingiu **91.43%**.

## Interpretação metodológica

Esta ablação mede o efeito de neutralizar sinais dentro do runtime congelado atual. Ela não representa retreino nem recalibração de um sistema alternativo sem o componente.
O cenário `brute_force` permanece no diagnóstico completo para transparência e comparabilidade histórica. Para o TCC, sua interpretação semântica deve permanecer qualificada pela limitação observacional dos logs de firewall.

O script não altera modelos, thresholds, parser, Decision Engine ou perfil ativo.
