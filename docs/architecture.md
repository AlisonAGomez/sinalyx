# Arquitetura do Sinalyx

Status: **ATUAL / OFICIAL**, referência de código da Fase 2D.

## Fluxo de análise

A FastAPI recebe o upload autenticado em `POST /analyze/pfsense`. O serviço
valida a entrada e aguarda o processamento no thread pool. Não é uma fila de
jobs nem uma resposta assíncrona com consulta posterior de tarefa.

```text
Logs pfSense → entrada/coleta → parser → agregação → 13 features
                                                   ↓
                         Autoencoder + Isolation Forest + heurística
                                                   ↓
                                Ensemble → Decision Engine
                                                   ↓
                      resposta FastAPI → PostgreSQL → frontend/dashboard
```

As setas descrevem dependências de dados; Autoencoder e Isolation Forest não
consomem a saída um do outro. Modelos fornecem sinais, heurística acrescenta
contexto e o Ensemble combina apoio. O Decision Engine produz decisão final,
tipo provável, risco, confiança e explicação. O resultado não prova um ataque.

## Responsabilidades e fontes

| Camada | Responsabilidade | Fonte |
| --- | --- | --- |
| Entrada | Upload ou coleta SSH/SFTP opcional | `src/api/services.py`, `src/collectors/pfsense_collector.py` |
| Parser | Transformar linhas em eventos estruturados | `src/parsers/pfsense_parser.py` |
| Janelas | Agrupar eventos e calcular features | `src/pipelines/parse_pfsense_logs.py`, `src/pipelines/window_aggregator.py` |
| Artefatos | Resolver perfil e carregar scaler/modelos/thresholds | `src/core/model_registry.py`, `src/core/artifacts.py` |
| Sinais | Reconstrução, anomalia estatística e padrões heurísticos | `src/models/autoencoder.py`, `isolation_forest.py`, `heuristics.py` |
| Combinação e decisão | Combinar sinais e aplicar regras do perfil | `src/models/ensemble.py`, `decision_engine.py` |
| Armazenamento | Gravar análise e janelas ou indicar fallback | `src/db/repository.py`, `src/api/services.py` |
| Apresentação | Consultas autenticadas, filtros e explicações | `frontend/src/` |

`make_decision` usa estratégia assimétrica: Autoencoder delimita zonas de
risco, Isolation Forest modula conflito/estabilidade e heurística fornece
contexto. O Ensemble não é a decisão final. A função permanece sem decomposição
nesta fase; cada regra deve ser lida junto ao código e perfil, sem substituir
suas condições por uma narrativa de votação simples.

## Features e tempo

As 13 colunas oficiais, na ordem de `src/features/constants.py`, são:
`connections`, `bytes`, `packets`, `packet_size`, `ports`, `bytes_per_packet`,
`bytes_per_connection`, `packets_per_connection`, `log1p_connections`,
`log1p_bytes`, `log1p_packets`, `log1p_packet_size`, `log1p_ports`.
Metadados de janela e colunas `ctx_*` não ampliam essa entrada oficial dos modelos.

O batch e o live local usam **5 segundos por origem** por padrão. O live mantém
offsets e pode deixar a última janela aberta. Cada chamada executa uma passagem;
agendamento externo não é coleta autônoma implementada pela CLI.
`--finite-file` fecha a janela final de replay; `--flush-pending` é compatibilidade.

## API, banco e implantação

Upload temporário e saídas incompletas da requisição são limpos ao terminar;
resultados concluídos permanecem. `artifacts.uploaded_file` registra proveniência,
mas não promete que o temporário ainda exista. Falha de gravação pode retornar
análise concluída com `database_saved=false` e fallback JSON.

PostgreSQL armazena usuários, análises e janelas locais. A API consulta a conta
no banco ao validar acesso; JSON não substitui autenticação.
No Compose, Nginx entrega o frontend e encaminha `/api/` para `api:8000`, retirando
o prefixo. Os serviços são `frontend`, `api`, `postgres`.

O startup valida o segredo JWT antes de preparar banco/modelos. Falhas de
carregamento são tratadas; processo iniciado ou health HTTP isolado não prova
que todos os modelos estejam prontos.

## Pesquisa e compatibilidade

**EXPERIMENTAL:** contexto temporal entre Ensemble e Decision Engine, memória,
ajustes laterais e Candidate v1 não promovido. Esses caminhos não devem aparecer
no desenho oficial como etapas ativadas. **HISTÓRICO:** `hybrid_v2_3` é
validation-only. **LEGADO:** `/predict`, SQLite antigo e nomes LogSense.
Veja [dados e modelos](dados_modelos.md).

Não há bloqueio automático. Logs de firewall permitem descrever um padrão
compatível com força bruta, não confirmar tentativas de senha malsucedidas.
