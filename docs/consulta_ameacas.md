# Consulta interpretativa de ameaças — frontend

Status: conteúdo de consulta, sem participação na inferência. Não cria regras,
thresholds, probabilidades ou rótulos; não modifica respostas da API. Funciona
offline após o build; referências externas só são abertas por ação do usuário.

## Decisões de UI e limite científico

- Relatórios usa **RESULTADOS DA AVALIAÇÃO HISTÓRICA**. O rótulo solicitado
  “MELHOR RESULTADO OBTIDO” não foi adotado: não há critério de ranking geral
  registrado que sustente essa afirmação. Na tabela da
  [ablação](evidencias/ablation_tcc_reproducible_v1.md), há empate de F1 com a
  neutralização do IF e troca entre precision/recall ao neutralizar o AE.
- O título visual “Validação histórica reproduzida” foi retirado. A evidência e
  as exportações existentes foram preservadas. Os números são retrospectivos,
  em 355 janelas com dados também usados no desenvolvimento/configuração;
  não são holdout independente nem garantia de generalização em produção.
- O avatar não tinha ação; nome, papel e logout foram preservados.
- A assinatura acadêmica substitui o card da sidebar. O footer continua oculto
  na navegação móvel compacta; no desktop ocupa o final do menu, sem sobreposição.
- O JSON expansível de WindowDetails foi removido somente da UI. Não possuía
  qa-id/data-testid próprios. Os testes de concorrência que liam seu `<pre>`
  passaram a verificar a janela entregue ao componente consultivo real; não
  perderam as verificações de identidade, erros, loading ou exportação.
- Exportação JSON/PDF e `buildSafeWindowRecord` continuam independentes da seção
  removida. A estrutura dos dados exportados não mudou. O rótulo amigável de
  `connections` na tabela/PDF passa a “Registros de tráfego”, conforme a semântica
  real; seus derivados usam “por registro” e “registros em escala logarítmica”.
  Pacotes e portas recebem os qualificadores “registrados” e “de destino
  distintas”. São nomes amigáveis, sem alteração das features.

## Proveniência das 13 entradas

Conferir estes pontos ao atualizar o conteúdo:

1. `src/features/constants.py`: nomes e ordem oficiais.
2. `data/models/manifest.json`: `feature_columns` e `n_features` do store oficial.
3. `src/parsers/pfsense_parser.py::_parse_filterlog_message`: `bytes = length`
   (ou zero se ausente), `packets = 1` para o evento canônico; validação posterior
   define elegibilidade.
4. `src/pipelines/window_aggregator.py::normalize_event_record`,
   `WindowAggregateState.add_record/to_output_record`: eventos elegíveis por origem e
   bucket temporal; contagem, somas, portas distintas e média. O default é 5 s,
   mas registros históricos podem ter outra duração. Não reinterpretar uma
   janela histórica de 60 s como janela de 5 s.
5. `src/features/engineering.py::safe_ratio/add_engineered_features`: razões
   protegidas, zero para denominador zero e `ln(1 + max(x, 0))` das cinco bases.
   Sanitização numérica trata valores ausentes/não finitos no pipeline; o
   frontend não refaz essas transformações.

| Feature | Nome amigável | Definição comprovada | Unidade | Uso interpretativo | Limitação |
| --- | --- | --- | --- | --- | --- |
| connections | Registros de tráfego | event_count: um por evento elegível | registros/janela | Repetição/intensidade | Não conta sessões estabelecidas ou simultaneidade |
| bytes | Volume registrado | Soma dos comprimentos registrados, não negativos | bytes/janela | Volume observado | Logs podem representar somente parte do tráfego; não é payload útil |
| packets | Pacotes registrados | Soma do campo packets; parser atribui 1 por evento | pacotes/janela | Quantidade observada | No filterlog canônico coincide com connections; não é captura completa |
| packet_size | Tamanho médio registrado | bytes / packets; zero sem pacotes | bytes/pacote | Perfil médio de tamanho | Não preserva distribuição/conteúdo |
| ports | Portas de destino distintas | Cardinalidade das portas de destino válidas na janela/origem | portas/janela | Diversidade de serviços | Não identifica porta aberta, intenção ou sequência |
| bytes_per_packet | Bytes por pacote registrado | safe_ratio(bytes, packets) | bytes/pacote | Relação volume/pacotes | Coincide com packet_size neste agregador |
| bytes_per_connection | Bytes por registro | safe_ratio(bytes, connections) | bytes/registro | Relação volume/eventos | Não corresponde a bytes por sessão autenticada |
| packets_per_connection | Pacotes por registro | safe_ratio(packets, connections) | pacotes/registro | Relação pacotes/eventos | No parser canônico tende a 1 por construção |
| log1p_connections | Registros em escala logarítmica | ln(1 + max(connections, 0)) | escala logarítmica | Compressão de escala | Não é sinal independente ou probabilidade |
| log1p_bytes | Volume em escala logarítmica | ln(1 + max(bytes, 0)) | escala logarítmica | Compressão de escala | Não são bytes diretos ou percentual |
| log1p_packets | Pacotes em escala logarítmica | ln(1 + max(packets, 0)) | escala logarítmica | Compressão de escala | Não determina malícia |
| log1p_packet_size | Tamanho em escala logarítmica | ln(1 + max(packet_size, 0)) | escala logarítmica | Compressão de escala | Não reconstrói a distribuição |
| log1p_ports | Diversidade de portas em escala logarítmica | ln(1 + max(ports, 0)) | escala logarítmica | Compressão de escala | Não contém lista de portas/serviços |

As somas referem-se aos registros incluídos, não necessariamente ao tráfego total
real. Entradas preparadas podem informar packets diferentes de 1; a equivalência
de contadores descrita acima é específica do parser canônico filterlog.

## Categorias e literatura cruzada com o produto

- **DoS / possível DDoS:** `syn_flood` e padrões de volume existem na heurística.
  Os números agregados contextualizam intensidade; a heurística também usa
  metadados de protocolo/flags/ações, que não são as 13 features. Não afirmar
  DDoS a partir de uma origem isolada. [MITRE T1498](https://attack.mitre.org/techniques/T1498/)
  distingue tráfego de uma ou múltiplas origens e impacto de disponibilidade.
- **Brute force — indícios de rede:** categorias `brute_force` e `ssh_suspicious`
  existem no projeto, com contexto de serviços e repetição. Os 13 agregados não
  observam autenticações ou falhas de senha. [MITRE T1110](https://attack.mitre.org/techniques/T1110/)
  descreve ataques a credenciais; essa literatura não torna o firewall capaz
  de confirmar o evento de autenticação. A limitação do Sinalyx é explícita.
- **Port scan:** a heurística contempla `port_scan` com diversidade de portas e
  outros metadados. Contagens ajudam a contextualizar sondagens, sem provar sua
  intenção. [MITRE T1046](https://attack.mitre.org/techniques/T1046/) aborda descoberta
  de serviços; não equivale a cobertura completa dessas técnicas pelo produto.
- **Tráfego anômalo:** modelos e classificação de anomalia já existem. O
  [NIST SP 800-94, seção 2.3.2](https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-94.pdf)
  descreve comparação com perfis e a possibilidade de desvios benignos/falsos
  positivos. Os valores do guia não atribuem causalidade a AE/IF/Ensemble.

Referências verificadas em 2026-11-02. São bases conceituais; nenhum link é
consultado automaticamente em execução. Não foram adicionadas outras categorias.

## Três níveis separados

1. **Valores observados:** somente números finitos existentes em `features`.
   Zero continua zero; ausente/inválido mostra “Não informado”. Não há cálculo
   de razões, logs, comparação com limiares ou inferência de alto/baixo na UI.
2. **Padrões associados:** consulta estática selecionada pelo usuário. Não deriva
   categoria do valor de uma feature e não muda a classificação.
3. **Decisão do Sinalyx:** campos existentes de resultado, evento, risco e
   confiança bruta. O motivo segue o formatter operacional já adotado, sem
   expor texto arbitrário de metadados. Confiança não é probabilidade calibrada.

`ctx_*`, ground truth e rótulos de cenários não entram no catálogo de features.
O painel de contribuição Shapley já existente permanece separado; o guia não
inventa atribuição por feature nem percentuais de influência.

## Manutenção e testes

Conteúdo: `frontend/src/content/consultaAmeacas.ts`. Renderização:
`frontend/src/components/ui/ConsultaAmeacas.vue`. Atualizações devem conferir
código/manifest e literatura, preservar a distinção entre observação e hipótese
e executar os testes de catálogo, componente, detalhes, header e Relatórios.

Os testes de exportação usam adapters de UI simulados para inspecionar conteúdo;
não provam download/impressão em navegador. Aprovação de build não equivale a QA
visual. Integração Docker, banco, runtime científico e Windows ficam fora do lote.

Para o chat 00: consolidar a troca do JSON visual por consulta interpretativa,
o rótulo histórico neutro e a preservação das exportações como decisões de UX;
isso não promove detecção, cobertura ou generalização científica.

## QA visual local deste lote

Executado em navegador real contra uma prévia temporária do build, com respostas
HTTP e sessão sintéticas no processo do navegador, isoladas do backend/Docker.
Nenhuma credencial real, conexão PostgreSQL ou inferência foi utilizada.

| Viewport | Observação |
| --- | --- |
| 1366×768 | Consulta, seletor de 44 px, quatro categorias, expansões das 13 definições e referências verificados; sem overflow horizontal da página |
| 1920×1080 | Relatórios, métricas/matriz, header sem avatar e assinatura da sidebar verificados; conteúdo centralizado, sem overflow horizontal da página |
| 390×844 | Consulta e textos legíveis, seletor de 44 px, largura dentro do viewport; QA móvel parcial pelo problema de navegação abaixo |

O logout foi acionado no navegador e retornou ao login. Não houve erros/warnings
de console na consulta sintética observada. Screenshots foram guardados somente
em pasta temporária externa ao checkout; não são evidência de integração real.

**Limitação móvel preexistente:** os grupos de links da sidebar podem encolher
e sobrepor seus itens. Em 390 px, Configurações ocupou x=189–261 enquanto
Histórico ocupou x=160–232. O padrão base dos grupos não foi alterado neste lote;
somente o footer e sua distribuição desktop mudaram. Como o restante do menu
foi explicitamente preservado, a correção fica para autorização própria. Não
declarar toda a navegação móvel aprovada.
