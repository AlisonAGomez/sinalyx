# Linguagem e termos do projeto

Status: **ATUAL**, orientação documental. Não altera rótulos da interface.

Use português brasileiro natural: “fluxo de análise”, “armazenamento dos
resultados”, “janela”, “tipo provável” e “explicação da decisão”.
Preserve API, endpoint, parser, frontend, backend, JWT, Docker, FastAPI,
PostgreSQL, SQLAlchemy, Alembic, migration, commit, rollback, build, healthcheck,
dataset, runtime, threshold, Autoencoder, Isolation Forest e Ensemble.
Não traduzir identificadores, arquivos ou contratos somente por estética.

| Termo | Explicação precisa |
| --- | --- |
| score | Pontuação; não é necessariamente probabilidade ou confiança calibrada |
| threshold | Limiar aplicado a um sinal/regra |
| precision | TP / (TP + FP): proporção de alertas positivos corretos |
| recall | TP / (TP + FN): proporção dos positivos reais detectados |
| FPR | FP / (FP + TN): proporção dos negativos reais alertados |
| F1 | Média harmônica de precision e recall |
| accuracy | Acerto geral; isoladamente pode ocultar desbalanceamento |
| Decision Engine | Camada que produz a decisão final |
| Tipo provável | Interpretação do padrão, não confirmação de ataque |

Diferencie detecção (normal/anômalo), tipagem e episódio. Para força bruta a
partir de firewall, use “padrão compatível” ou “suspeita”, sem afirmar falha de
senha confirmada. Mapeamento MITRE é explicativo.

Use OFICIAL, EXPERIMENTAL, HISTÓRICO e LEGADO conforme
[dados/modelos](dados_modelos.md). “Candidato para rede real”, quando encontrado
em rótulo antigo de `hybrid_v2_3`, não significa promoção: o perfil é HISTÓRICO,
validation-only. Os mapeamentos em `src/core/display_labels.py` e frontend
foram preservados; divergências visuais não são corrigidas nesta fase.
