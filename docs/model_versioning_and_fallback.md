# Registry e fallback de modelos

Status: **COMPLEMENTAR ATUAL**. O estado oficial está em
[dados e modelos](dados_modelos.md); métricas antigas permanecem históricas.

`data/models/model_registry.json` registra `active_profile`,
`candidate_profile`, `fallback_profile` e metadados em `profiles`.
O código resolve esses dados em `src/core/model_registry.py`; o loader fica
em `src/core/artifacts.py`. Git versiona código, mas não substitui rastreabilidade
e cópias privadas dos artefatos.

`current` permanece ativo. `hybrid_v2_3` é HISTÓRICO, validation-only, mesmo
quando aparece no campo antigo de candidato. Candidate v1
(`sinalyx_runtime_candidate_v1`) não foi promovido.
`current_runtime_frozen_v1` é cópia reprodutível, não equivalente ao hybrid_v2_3.

A seleção por `SINALYX_MODEL_PROFILE` pode cair no fallback configurado por
`SINALYX_MODEL_FALLBACK_PROFILE` e em `current` quando o perfil não é utilizável.
Confira o perfil resolvido e os avisos. Não interpretar fallback como sucesso
de carregamento do perfil originalmente solicitado.

Artefatos incluem scaler, Isolation Forest, Autoencoder, threshold e manifesto;
configuração do Ensemble também participa da reprodução da decisão. Validar
presença/metadados não prova equivalência entre runtimes ou qualidade medida.

```powershell
.\.venv\Scripts\python.exe scripts/validate_model_registry_and_fallback.py
```

Esse diagnóstico confere registry/caminhos/fallback, sem carregar TensorFlow ou
os modelos. O comando não foi executado na Fase 2D.
Não copiar/promover/regenerar perfis como parte de organização documental.
