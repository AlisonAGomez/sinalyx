# Contrato backend de contribuição por janela

`component_contributions` é explicabilidade derivada e aditiva, separada de
`model_outputs` e `ai_support`. Não participa da decisão de segurança.

## Cálculo e configuração

`run_inference_from_frame`, em `src/pipelines/infer_pfsense_batch.py`, calcula o
bloco após IF, AE, heurística, Ensemble e Decision Engine produzirem seus outputs
oficiais. O pipeline captura as configurações de Ensemble e Decision Engine e
as fornece tanto à inferência como à explicação. O threshold de referência AE
vem do snapshot oficial da mesma janela. Não há resolução posterior no GET.

O serviço compartilhado `src/services/component_contributions.py` chama o
`exact_shapley_v1` validado, verifica a paridade da coalizão completa com os
outputs oficiais, valida o contrato e remove as coalizões do payload público.
Somente combinação e decisão são recalculadas; não há chamadas adicionais a
AE, IF ou heurística. As chamadas preexistentes no pipeline permanecem iguais.

Batch/upload e live incremental usam o mesmo pipeline. Nenhuma mudança foi
feita no worker, coleta pfSense, parser, modelos ou mecanismos de decisão.

## Contrato

O bloco é um objeto ou `null`, com os campos:

| Campo | Tipo/valor |
|---|---|
| methodology | `exact_shapley_v1` |
| baseline_type | `zero_signal_reference` |
| baseline_value | float finito no intervalo [-1, 1] |
| full_value | float finito no intervalo [-1, 1] |
| decision_span | float finito |
| efficiency_residual | float finito |
| components | exatamente `autoencoder`, `isolation_forest`, `security_rules` |

Cada componente contém `shapley_value` assinado, `absolute_contribution` não
negativo, `relative_share_percent` entre 0 e 100 e `direction`, limitada a
`toward_anomaly`, `toward_normal` ou `neutral`. Não inclui coalizões nem dados
de rede. Os percentuais são calculados por janela, sem constantes históricas.

Os schemas `ComponentContributionItem` e `ComponentContributionsPayload` ficam
no serviço compartilhado e são reexportados por `src/api/schemas.py`. Isso
permite validar antes da serialização sem tornar o pipeline dependente da API.
Os itens de `results` continuam objetos livres no schema HTTP legado: o novo
bloco é validado pelo projetor, sem coerção/remoção dos campos antigos. As
respostas tipadas de janelas live/histórico incluem o campo opcional.

## Transporte e persistência

- POST `/analyze/pfsense`: o builder apenas projeta o bloco calculado.
- `save_analysis`: persiste o item completo em `AnalysisResult.raw_json`,
  incluindo a contribuição. GET `/analyses/{analysis_id}/results` recupera esse
  mesmo JSON sem calcular Shapley novamente.
- Live: a contribuição fica no registro original em `LivePfSenseWindow.raw_json`;
  `model_outputs_json` permanece inalterado. As projeções de janela live e
  histórico recuperam a contribuição desse registro original.
- CSV de inferência: a coluna nova usa JSON válido, não representação Python.
  O projetor aceita objeto ou JSON textual. O relatório JSON mantém o bloco
  separado dos metadados da janela.

Nenhuma migration ou alteração em models/tabelas foi necessária. Registros
batch antigos continuam sem o campo no GET; projeções live/histórico retornam
`null` quando não existe contribuição. Não há preenchimento retroativo.

## Falhas e interpretação

Falha de sinais, cálculo, paridade ou serialização deixa o bloco `null` e gera
log de erro sanitizado. Não exporta mensagem da exceção, stack trace, paths ou
dados de entrada. Não transforma erro em 0%, nem modifica decisão, scores ou
metadados auxiliares. Zero é reservado ao resultado matemático sem contribuição
relevante, conforme a metodologia offline.

O frontend **não deve recalcular** as contribuições. Percentual não é
probabilidade, e maior percentual não significa melhor modelo. A direção deve
acompanhar o percentual para distinguir influência para anomalia ou normalidade.
`security_rules` representa a heurística comportamental, não todas as políticas
internas do Decision Engine. Ensemble e Decision Engine não são participantes
Shapley. O baseline é o estado de referência sem evidência de ataque; seu suporte
de normalidade é derivado pela política do motor.

## Validação desta fase

Testes cobrem contrato, JSON, falhas sanitizadas, percentuais zero, negativos,
compatibilidade, configuração compartilhada, paridade, preservação dos campos
oficiais e round-trip HTTP POST/GET com SQLite e opção PostgreSQL descartável.
O replay das 355 janelas históricas no pipeline integrado teve zero divergências
nos campos oficiais: pred_decision_engine, is_anomaly, final_label, attack_type,
risk_level, confidence, decision_source, base_attack_support e
base_negative_support. Não executou detectores reais nem retreino.

### Validação PostgreSQL real

O teste opt-in foi executado contra PostgreSQL 16 real da stack Docker do
Sinalyx, usando banco QA descartável:

```text
tests/test_component_contributions_backend.py::test_post_get_persistencia_live_e_legado[postgresql] PASSED
1 passed, 2 warnings
```

Os dois avisos são de depreciação FastAPI preexistentes. O teste confirmou POST
HTTP 200, persistência de `component_contributions` em `raw_json`, recuperação
via GET e igualdade do bloco após o round-trip. Nenhuma migration foi necessária.

### Benchmark de overhead

Foram usadas 355 janelas históricas do runtime `current`, com os mesmos outputs
já calculados e sem reinferência AE/IF. Somente `component_contributions` foi
habilitado/desabilitado em memória, no mesmo caminho do pipeline. Foram feitos
3 warm-ups por modo, 20 pares de medições em ordem alternada e instrumentação
direta adicional com 1.775 amostras. Imports, leitura, carregamento de artefatos
e verificações de paridade ficaram fora do cronômetro.

| Medida | Resultado |
|---|---:|
| Janelas | 355 |
| Tempo médio sem contribuições | 1,322 s |
| Tempo médio com contribuições | 9,470 s |
| Overhead absoluto médio | 8,148 s |
| Overhead relativo ao pipeline com sinais reutilizados | 616,27% |
| Overhead médio por janela | 22,952 ms |
| Desvio-padrão do overhead por lote | 0,893 s |
| Custo direto médio | 20,963 ms/janela |
| Mediana do custo direto por janela | 20,168 ms |
| p95 do custo direto por janela | 29,665 ms |

O percentual de **616,27% não representa aumento da latência completa incluindo
execução real de AE/IF e carregamento de modelos**. O custo absoluto observado é
de aproximadamente **21–23 ms por janela neste ambiente**. A explicabilidade
possui custo computacional mensurável, que pode acumular em análises batch muito
grandes. Otimizações ou cálculo sob demanda podem ser avaliados futuramente.

Nenhuma decisão oficial foi alterada, não houve reinferência e os hashes dos
arquivos permaneceram inalterados durante o benchmark.

Detalhes científicos permanecem em
`docs/evidencias/component_contribution_methodology_v1.md`, sem duplicação nem
alteração das evidências históricas.

Resultados das suítes, anteriores à execução opt-in PostgreSQL:

- Testes específicos, metodologia offline e `tests/test_model_outputs.py`:
  35 aprovados, 2 ignorados (PostgreSQL opt-in).
- Suíte completa: 294 aprovados, 11 ignorados, 2 subtestes aprovados;
  2 avisos preexistentes de depreciação FastAPI. Duração: 38,46 s.
- Comando da suíte: `.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider`,
  com dotenv e banco operacional desabilitados.
- `git diff --check` aprovado, incluindo verificação dos arquivos novos.

Sem commit ou push nesta fase.
