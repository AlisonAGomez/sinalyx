# Scripts do Sinalyx

Os pipelines antigos preservados para reprodução do TCC estão em
[`historical/pipelines/`](historical/pipelines/README.md); não integram o fluxo
operacional atual.

Status: catálogo **ATUAL**; cada grupo tem seu próprio estado.
Nenhum script de treino, calibração, coleta, geração de relatórios ou restore foi
executado na Fase 2D. “Validação” no nome não significa somente leitura: muitos
scripts escrevem CSV/JSON e substituem relatórios em `docs/`.

Caminhos da tabela são relativos a `scripts/`. Consulte argumentos e constantes
de saída no código antes de executar; alguns scripts não têm CLI e usam destinos
fixos. Não usar `--allow-overwrite` nem destinos de artefatos congelados por rotina.

| Grupo e scripts | Quando usar / entrada | Saída / risco | Estado |
| --- | --- | --- | --- |
| Operação: `windows/start_sinalyx.ps1`, `stop_sinalyx.ps1`, `status_sinalyx.ps1` | Operar Compose já configurado | Início/parada/status; muda disponibilidade dos serviços, requer Docker | OFICIAL, integração pendente |
| Autostart: `windows/install_autostart_sinalyx.ps1`, `uninstall_autostart_sinalyx.ps1` | Configurar início no login Windows | Tarefa agendada e logs; altera configuração do usuário, não agenda coleta pfSense | OFICIAL, integração pendente |
| Administração: `seed_admin.py` | Inicializar conta via ambiente e PostgreSQL | Cria admin novo; conta existente é preservada, sem promoção/reativação | OFICIAL |
| Manutenção: `backup_postgres.ps1`, `restore_postgres.ps1` | Salvar banco ou restaurar dump privado | SQL/alterações de banco; restore pode substituir objetos e dados | OFICIAL; backup PostgreSQL real e restore em banco descartável validados na Fase 3 |
| Recuperação: `create_recovery_point.py` | Copiar fontes e metadados locais | `recovery_points/`; não é backup integral, revisar conteúdo privado | COMPLEMENTAR |
| Cenários: `validate_pfsense_scenarios.py` | Comparar quatro logs disponíveis com parser/inferência | `data/processed/pfsense/validation_runs/`; gera resultados, usa modelos, janela padrão 5 s | OFICIAL como ferramenta; resultados datados |
| Retreino antigo: `retrain_pfsense_official.py` | Reprocessar e treinar a partir dos quatro logs | Pode gravar modelos ativos e manifesto; alto risco para baseline, não é setup | HISTÓRICO; fora da operação atual |
| Treino candidato: `retrain_hybrid_v2.py`, `train_calibrated_runtime_candidate_v1.py` | Pesquisa autorizada com normais para fit e ataques para avaliação/calibração | Pacotes hybrid_v2/Candidate v1; custo de treino e risco de sobrescrever artefatos | EXPERIMENTAL; NÃO PROMOVIDO |
| Calibração: `calibrate_hybrid_v2_1.py`, `calibrate_hybrid_v2_2.py`, `calibrate_runtime_candidate_v1_recall.py` | Testar thresholds/pesos de artefatos/scores existentes | Configurações, relatórios e pacote candidato; risco de confundir seleção com promoção | EXPERIMENTAL; resultados anteriores HISTÓRICOS |
| Empacotamento: `package_runtime_candidate.py` | Auditar completude e congelar pacote de artefatos | Cópia reprodutível/relatórios; não prova equivalência ao hybrid_v2_3 | EXPERIMENTAL |
| Registry: `validate_model_registry_and_fallback.py` | Diagnosticar metadados e resolução de perfis | JSON no terminal; não carrega TF/modelos, pode revelar caminhos | OFICIAL como diagnóstico |
| Auditoria: `audit_context_scored_coverage.py`, `audit_portscan_false_negatives_trace.py`, `audit_runtime_candidate_v1_errors.py`, `audit_runtime_profile_alignment.py`, `audit_window_metadata.py` | Examinar bases, erros e perfis; alguns executam inferência | Relatórios/CSV/JSON; não promover nem interpretar métricas como atuais | HISTÓRICO/diagnóstico |
| Consolidação: `build_consolidated_validation_report.py`, `evaluate_attack_window_evaluability.py` | Reunir métricas e leitura complementar de janelas avaliáveis | Relatórios derivados; não substituir métricas brutas nem rotular só janelas favoráveis | HISTÓRICO/diagnóstico |
| Contexto: `export_security_context_windows.py`, `build_context_enriched_evaluation.py`, `build_context_scored_operational_dataset.py`, `build_context_scored_full_replay.py`, `validate_security_window_context.py` | Gerar/avaliar ctx_* de logs ou metadados e scores | Bases/relatórios em data/models e docs; replay pode ser custoso e regravar saídas | EXPERIMENTAL |
| Regras: `validate_hybrid_v2_2_operational_adjustment.py`, `validate_hybrid_v2_3_error_recovery.py`, `validate_hybrid_v2_4_temporal_error_recovery.py`, `validate_targeted_decision_tuning.py`, `validate_operational_targeted_tuning.py` | Avaliar ajustes laterais sobre scores/baselines | Métricas, regressões e candidatos de regra; não é alteração oficial do Decision Engine | EXPERIMENTAL; baselines HISTÓRICAS |
| Memória: `validate_memory_analysis_experiment.py`, `validate_memory_analysis_v2.py` | Replay causal sobre janelas históricas | Relatórios, estado e predições; não integra runtime | EXPERIMENTAL |
| Isolation Forest: `if_normal_only_experiment.py` | Auditoria de sinais e fit experimental em normais | Relatórios em docs/validation e artefatos/backup; não executar para preparar ambiente | EXPERIMENTAL |
| Capturas: `experiments/bruteforce_capture_preflight.py`, `bruteforce_capture_postcheck.py`, `validate_bruteforce_capture_manifest.py` (todos em experiments) | Conferir plano, captura manual e splits/manifests | Diagnóstico local; não gera tráfego; cuidado com caminhos e dados privados | EXPERIMENTAL |
| Apoio de capturas: `experiments/bruteforce_capture_common.py`, `experiments/__init__.py` | Helpers compartilhados/importação | Suporte interno, não comando operacional independente | EXPERIMENTAL |
| Temporal: `experiments/bruteforce_recent_history_prototype.py`, `bruteforce_recent_history_prototype_py310_compat.py`, `evaluate_temporal_bruteforce_integration_v1.py` (todos em experiments) | Reproduzir DEVELOPMENT congelado e diagnóstico causal | Métricas agregadas; protótipo original incompatível com Python 3.10, cópia compatível usada pelos testes | EXPERIMENTAL / NÃO RUNTIME / NÃO CANDIDATE |

## Batch, coleta e replay local

Os comandos oficiais de processamento estão em `src/pipelines/`, não foram
movidos para scripts. Execute na raiz com a venv preparada.

```powershell
.\.venv\Scripts\python.exe -m src.pipelines.parse_pfsense_logs --input CAMINHO_LOG_REVISADO --events-output SAIDA_EVENTOS_NOVA.csv --features-output SAIDA_FEATURES_NOVA.csv
.\.venv\Scripts\python.exe -m src.pipelines.infer_pfsense_batch --input SAIDA_FEATURES_NOVA.csv --output-csv SAIDA_RESULTADOS_NOVA.csv --output-json SAIDA_RESULTADOS_NOVA.json
```

Substitua os placeholders por caminhos privados revisados e saídas novas.
O primeiro comando lê log e grava eventos/features; o segundo carrega modelos e
grava resultados. Os defaults de saída podem substituir arquivos anteriores.
Para o fluxo principal autenticado, prefira `POST /analyze/pfsense`.

```powershell
.\.venv\Scripts\python.exe -m src.pipelines.process_pfsense_incremental --skip-collect --finite-file --no-persist
```

Esse replay usa arquivo local configurado e fecha a janela pendente. Mesmo com
`--no-persist`, pode atualizar estado/offsets locais: prepare caminhos isolados.
O live padrão usa janelas de 5 s, assim como o batch. Sem `--skip-collect`,
há acesso SSH/SFTP real; sem `--no-persist`, há tentativa de gravação PostgreSQL.
A CLI termina após uma passagem, não implementa laço contínuo.
O nome antigo `src.pipelines.process_live_pfsense` permanece como wrapper
LEGADO da CLI; novos comandos devem usar `src.pipelines.process_pfsense_incremental`.
`--flush-pending` é LEGADO/compatibilidade; novas validações usam finite-file.
A API também oferece `POST /live/pfsense/run?collect=false&finite_file=true`
para administrador; esse endpoint pode persistir resultados.

## Backup e restore

Backup recebe ContainerName, Database, User e OutputPath; chama `pg_dump`
com `--clean --if-exists`. O arquivo SQL deve ficar fora do Git.
Restore exige BackupPath e envia SQL ao `psql` do container: pode remover e
recriar objetos. Teste em banco isolado, confirme destino e preserve backup
atual antes de restaurar. Mensagem impressa pelo script não substitui validação
da restauração e dos dados. A [Fase 3](../docs/fase3_qa_integrado.md) validou
backup real, restore em banco descartável e rollback de falha controlada.

Veja [testes](../docs/testing.md), [banco](../docs/database.md) e
[dados/modelos](../docs/dados_modelos.md) antes de qualquer reprodução.
