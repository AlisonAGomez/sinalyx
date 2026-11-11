# component_contribution_methodology_v1

Status: baseline metodológico definido; implementação e avaliação offline concluídas.

## Objetivo e delimitação

Medir a contribuição marginal contrafactual de Autoencoder, Isolation Forest e Regras de Segurança por atribuição por intervenção nos sinais. O método é offline, isolado do runtime, API, banco e frontend. Não houve alteração dos modelos, thresholds, pesos, calibração, Ensemble, Decision Engine ou Docker; não houve retreino nem reinferência.

Participantes exatos: autoencoder, isolation_forest e security_rules. **security_rules representa exclusivamente o módulo heurístico/regras comportamentais fornecido ao Decision Engine, não todas as regras do Sinalyx.** Supressão de ruído operacional, thresholds, condições e políticas internas permanecem no mecanismo fixo em todas as coalizões. O contexto operacional permitido também permanece fixo.

Ensemble e Decision Engine não são participantes. Seus pesos não equivalem a percentuais de contribuição: bandas, limiares, penalidades, interações e decisões condicionais tornam a influência dependente dos sinais e do contexto. Uma assinatura heurística confirmada pode impedir a supressão operacional; o Shapley atribui a influência dessa intervenção sem tratar a política de supressão como quarto participante.

## Baseline adotado

**Alternativa adotada: baseline por intervenção de zeramento, preservando integralmente Ensemble e Decision Engine.**

A coalizão vazia é o **estado de referência sem evidência de ataque**, não neutralidade e não evidência observada de normalidade. O Shapley mede quanto cada componente desloca a decisão a partir desse estado até a decisão da coalizão completa, considerando suas contribuições marginais nas diferentes coalizões.

Detectores ausentes: pred=0, raw_score=0, normalized_score=0 e confidence=0. Regras ausentes: heuristic_detected_attack=false, heuristic_confidence=0, attack_type="normal" e heuristic_reason="". Não se atribui confiança alta manualmente ao componente removido. A referência de threshold AE permanece fixa no combinador.

A causa principal de v(empty)=-1 no diagnóstico e nas 355 janelas foi:

attack_support=0 → compute_negative_support: 1-attack_support → negative_support=1 → decisão normal → confidence=1.

É **suporte de normalidade derivado pela política do Decision Engine**. ae_risk_band=low e if_stability_score=1 são estados internos registrados, não a causa principal da confiança 1. Abstenção explícita fica apenas como possibilidade metodológica futura, não adotada.

## Valor, coalizões e recálculo

v(S)=+confidence_final para decisão anômala e -confidence_final para normal. Confidence é **força relativa da decisão**, não probabilidade. Eixo: -1 significa decisão normal forte; 0 é a região central; +1 significa decisão anômala forte.

Exatamente oito coalizões por janela: ∅, AE, IF, Regras, AE+IF, AE+Regras, IF+Regras e AE+IF+Regras. As chaves usam nomes completos unidos por +, em ordem estável; a vazia usa empty.

O módulo recebe outputs já calculados, copia sinais presentes, zera ausentes, chama a função real _build_support_snapshot e fornece o novo snapshot à função real decide_attack. Não reutiliza o ensemble_score original como resultado do recálculo, não duplica fórmulas e não executa AE/IF por coalizão. O cálculo não faz I/O.

Somente campos necessários dos sinais e uma lista explícita de contexto operacional consumido pela supressão chegam ao motor. Label, target, scenario, diagnostic_category, error_type, nomes de arquivo e IPs não são encaminhados. O tipo heurístico é saída predita pelo componente, não cenário real. Agrupamento e referências sequenciais são anexados após Shapley e paridade. A evidência não exporta features, metadata, conteúdo de logs, IPs, razões textuais dos detectores ou caminhos absolutos.

## Shapley, participação e eficiência

Para cada participante i e conjunto N dos três participantes:

phi_i = Σ[S ⊆ N sem i] |S|! (3-|S|-1)! / 3! × [v(S ∪ {i}) - v(S)].

A definição combinatória exata também foi validada por um oráculo independente de seis permutações. Campos por participante: shapley_value, absolute_contribution, relative_share_percent e direction.

Participação relativa = 100 × |phi_i| / Σ|phi_j|.

Denominador menor ou igual a 1e-12 implica participações zero e relevant_contribution=false, nunca 33/33/33. Direções: toward_anomaly para positiva, toward_normal para negativa e neutral quando o módulo é menor ou igual à tolerância. Os valores assinados não são arredondados para testar eficiência.

Contribuição negativa significa deslocamento marginal para normalidade, não pior detector. Valores individuais podem superar 1 porque diferenças no eixo [-1,1] podem alcançar 2. A participação global usa soma dos módulos em todas as janelas, não média dos percentuais de cada janela.

Eficiência: Σphi_i ≈ v(full)-v(empty). São retornados baseline_value, full_value, decision_span, efficiency_residual e tolerance. O cálculo falha se o residual exceder a tolerância absoluta de 1e-12.

## Configuração efetiva de current

O diagnóstico inicial usou defaults apenas para evidenciar a semântica. A avaliação histórica resolveu a configuração pelos caminhos oficiais:

1. resolve_model_profile(requested_profile="current", fallback_profile="current") resolve o perfil de artefatos pelo registry e exige resolução solicitada, sem fallback.
2. profile_runtime_artifacts identifica o ensemble.json persistido; seu conteúdo instancia EnsembleConfig e passa por resolve_ensemble_config com o perfil operacional registrado na janela.
3. Todas as janelas registram balanced, nome do perfil operacional, distinto do perfil de artefatos current. Ensemble resolvido: IF=0,18 e AE=0,90; o snapshot oficial normaliza para aproximadamente 0,166667 e 0,833333. Threshold efetivo: 0,32.
4. _resolve_ae_reference_threshold aplica a precedência oficial: referência persistida ou, se ausente, threshold AE já registrado pelo bundle. Referência efetiva: 9,158707301456236. Nenhum modelo ou pickle é carregado.
5. resolve_config(profile="balanced") segue o caminho de decide_attack_batch no pipeline, que não fornece config customizada do Decision Engine. Não se converte indevidamente a config do Ensemble em config do motor.

As configurações completas persistidas e resolvidas estão no JSON resumo. As funções reais foram reutilizadas sem alteração.

## Paridade e eficiência observadas

Cada coalizão completa foi comparada com a linha oficial para is_anomaly, final_label, attack_type, decision_source, base_attack_support, base_negative_support, confidence e agreement_level. Também foram comparados predição, score, threshold e pesos do Ensemble. Leitura do CSV com float_precision="round_trip".

**Paridade aprovada em 355/355 janelas.** Erro máximo observado em suporte de ataque, suporte negativo, confiança e score do Ensemble: **0**. Nenhuma divergência categórica. Maior residual absoluto de eficiência: **2,220446049250313e-16**, com tolerância **1e-12**. Todos os baselines foram -1.

O avaliador interrompe antes de agregar se houver divergência ou quantidade diferente de 355. Em falha, grava somente diagnóstico, sem resultados agregados. Um teste injeta divergência de confiança e comprova essa interrupção.

## Resultados globais

| Componente | Soma de módulos | Participação | Média assinada | Média absoluta | Mediana assinada | Anomalia / normal / neutra |
|---|---:|---:|---:|---:|---:|---|
| Autoencoder | 109,121537194 | 30,402952% | 0,307384612 | 0,307384612 | 0,234685398 | 206 / 0 / 149 |
| Isolation Forest | 51,605680823 | 14,378143% | 0,145209957 | 0,145368115 | 0,004790051 | 199 / 3 / 153 |
| Regras comportamentais | 198,190350623 | 55,218905% | 0,558282678 | 0,558282678 | 0,306266667 | 189 / 0 / 166 |

Maior percentual mede influência interna sob este baseline e composição de dados; **não implica melhor modelo**.

## Resultados por cenário

| Cenário | Janelas | AE | IF | Regras |
|---|---:|---:|---:|---:|
| normal | 145 | 96,344472% | 3,655528% | 0% |
| port_scan | 33 | 70,731999% | 14,638001% | 14,630001% |
| syn_flood | 24 | 8,889776% | 0,841485% | 90,268739% |
| brute_force | 153 | 24,332322% | 16,532676% | 59,135002% |

Percentuais calculados pela soma de módulos dentro do cenário. O relatório de dados e o JSON resumo incluem todas as médias, medianas, somas e contagens de direção por cenário.

**Brute force possui limitação de observabilidade no pfSense.** Estes resultados não demonstram observação de tentativas de senha, falhas de autenticação ou autenticação bem-sucedida. As 153 janelas desse cenário influenciam substancialmente a composição global.

Três contribuições negativas foram observadas, todas do IF:

| Referência sequencial | Shapley IF | v(full) |
|---|---:|---:|
| brute_force-0081 | -0,011377213101455341 | -0,8475798002175541 |
| brute_force-0087 | -0,008980157093380903 | -0,8426669536723863 |
| brute_force-0088 | -0,007715648897996696 | -0,8425869770975227 |

Mesmo com baseline -1, um componente pode ter contribuição negativa média nas coalizões, compensada pela contribuição dos demais. Não houve contribuição negativa de AE ou regras acima da tolerância nesta amostra.

## Evidências e reprodução

Entradas: data/processed/pfsense/validation_runs/20260911_current_tcc. Nenhum artefato histórico foi sobrescrito. A leitura seleciona somente colunas necessárias. Hashes de origem identificam essa projeção, não o CSV integral com identificadores de rede.

Novos arquivos em data/processed/pfsense/component_contribution_v1/:

- contribuicoes_por_janela.csv: contribuições, direções, baseline e residual;
- resultados_detalhados.json: oito coalizões, decisões e snapshots reduzidos por janela;
- resumo.json: estatísticas completas, paridade, tolerância, configurações e hashes;
- relatorio.md: tabelas completas globais e por cenário.

Esse diretório segue o ignore existente de dados: disponível localmente, sem aparecer no git status. O avaliador recusa saída existente. Para repetir, fornecer um novo --output-root.

Comando executado: .\.venv\Scripts\python.exe -B scripts/evaluate_component_contribution_tcc.py

Antes da execução, foram definidos PYTHON_DOTENV_DISABLED=1, OMP_NUM_THREADS=1, TF_NUM_INTRAOP_THREADS=1 e TF_NUM_INTEROP_THREADS=1. O script também desabilita dotenv antes dos imports do projeto. Não acessa credenciais, inicia serviços ou usa contexto temporal experimental. Imports transitivos do Ensemble incluem TensorFlow, mas não executam modelos.

## Comparação e limitações

Desempenho individual compara predições com ground truth. Remoção histórica usa a neutralização de scripts/validate_ablation_tcc.py, incluindo confiança 1 para detectores removidos. Este Shapley usa confiança 0 e todas as coalizões com pesos combinatórios. **São metodologias diferentes, sem equivalência direta.** A análise histórica não foi recalculada nem modificada.

A atribuição mede influência interna de intervenções artificiais, não contribuição causal estatística forte. Pode avaliar combinações de sinais que não ocorrem naturalmente. Baseline e função de valor condicionam a interpretação; confidence não é probabilidade calibrada. Contexto operacional e políticas internas ficam condicionados à janela e não recebem atribuição separada. Resultados restritos às 355 janelas e à configuração current preservada; não demonstram generalização ou ranking de qualidade.

## Validação

- Testes iniciais do módulo: 17 aprovados.
- Testes ampliados do módulo e contratos de outputs: 24 aprovados, 1 ignorado (PostgreSQL opt-in), 2 avisos preexistentes de depreciação FastAPI.
- Cobertura: oito coalizões, determinismo, não mutação, oráculo por permutações, eficiência, percentuais/zero, sinais positivos/negativos/direções, zeramento, baseline, paridade, contexto fixo, filtragem de ground truth, bloqueio de inferência/treino/carregamento, config persistida, interrupção por divergência e recusa de sobrescrita.
- Avaliação real: 355 janelas, 2.840 coalizões, paridade e eficiência aprovadas.
- Suíte completa: 283 aprovados, 10 ignorados, 2 subtestes aprovados e 2 avisos preexistentes de depreciação FastAPI; duração de 32,92 s. Comando: .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider. Dotenv e banco operacional desabilitados; testes PostgreSQL opt-in não habilitados.
- git diff --check aprovado. Os quatro arquivos novos também foram verificados individualmente com git diff --no-index --check, pois ainda não estão no índice.

Sem dependências novas, migrations, commit ou push. Nenhuma integração com API, banco ou frontend.
