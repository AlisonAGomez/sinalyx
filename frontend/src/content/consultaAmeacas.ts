/** Conteúdo explicativo para consulta de padrões; não cria detecções nem altera resultados. */

// Conteúdo consultivo. Proveniência e limites em docs/consulta_ameacas.md.
export const featuresConsulta = [
  { chave: 'connections', nome: 'Registros de tráfego', unidade: 'registros/janela', definicao: 'Quantidade de eventos elegíveis agregados para uma origem na janela.', uso: 'Ajuda a examinar repetição e intensidade de registros.', limite: 'Não mede sessões estabelecidas nem conexões simultâneas.' },
  { chave: 'bytes', nome: 'Volume registrado', unidade: 'bytes/janela', definicao: 'Soma dos comprimentos informados nos registros de tráfego.', uso: 'Contextualiza o volume observado.', limite: 'Não representa todo o tráfego da rede nem apenas conteúdo útil.' },
  { chave: 'packets', nome: 'Pacotes registrados', unidade: 'pacotes/janela', definicao: 'Soma do campo de pacotes; o parser canônico atribui um pacote por evento.', uso: 'Contextualiza a quantidade de pacotes observados nos logs.', limite: 'No filterlog canônico coincide com a contagem de registros; não é uma captura completa.' },
  { chave: 'packet_size', nome: 'Tamanho médio registrado', unidade: 'bytes/pacote', definicao: 'Volume registrado dividido pelos pacotes registrados; zero se não há pacotes.', uso: 'Ajuda a comparar perfis de tamanho dos pacotes.', limite: 'Uma média não mostra a distribuição dos tamanhos ou o conteúdo.' },
  { chave: 'ports', nome: 'Portas de destino distintas', unidade: 'portas/janela', definicao: 'Quantidade de portas de destino válidas diferentes na janela da origem.', uso: 'Ajuda a examinar diversidade de serviços consultados.', limite: 'Não é o número da porta nem comprova portas abertas ou varredura.' },
  { chave: 'bytes_per_packet', nome: 'Bytes por pacote registrado', unidade: 'bytes/pacote', definicao: 'Razão bytes / packets; denominador zero produz zero no pipeline.', uso: 'Relaciona volume e quantidade de pacotes.', limite: 'Nesse agregador coincide com o tamanho médio; não é evidência independente.' },
  { chave: 'bytes_per_connection', nome: 'Bytes por registro', unidade: 'bytes/registro', definicao: 'Razão bytes / connections; denominador zero produz zero no pipeline.', uso: 'Relaciona volume e registros de tráfego.', limite: 'O denominador representa eventos, não sessões autenticadas.' },
  { chave: 'packets_per_connection', nome: 'Pacotes por registro', unidade: 'pacotes/registro', definicao: 'Razão packets / connections; denominador zero produz zero no pipeline.', uso: 'Relaciona pacotes e registros agregados.', limite: 'No filterlog canônico tende a 1 por construção; não mede sucesso de conexão.' },
  { chave: 'log1p_connections', nome: 'Registros em escala logarítmica', unidade: 'escala logarítmica', definicao: 'ln(1 + max(connections, 0)), calculado pelo pipeline.', uso: 'Representa a mesma contagem em escala comprimida.', limite: 'Não acrescenta um sinal independente, score ou probabilidade.' },
  { chave: 'log1p_bytes', nome: 'Volume em escala logarítmica', unidade: 'escala logarítmica', definicao: 'ln(1 + max(bytes, 0)), calculado pelo pipeline.', uso: 'Representa o volume em escala comprimida.', limite: 'Não corresponde a bytes diretos nem a percentual de ameaça.' },
  { chave: 'log1p_packets', nome: 'Pacotes em escala logarítmica', unidade: 'escala logarítmica', definicao: 'ln(1 + max(packets, 0)), calculado pelo pipeline.', uso: 'Representa a contagem de pacotes em escala comprimida.', limite: 'Não indica, por si, tráfego malicioso.' },
  { chave: 'log1p_packet_size', nome: 'Tamanho em escala logarítmica', unidade: 'escala logarítmica', definicao: 'ln(1 + max(packet_size, 0)), calculado pelo pipeline.', uso: 'Representa o tamanho médio em escala comprimida.', limite: 'Não permite recuperar a distribuição dos tamanhos.' },
  { chave: 'log1p_ports', nome: 'Diversidade de portas em escala logarítmica', unidade: 'escala logarítmica', definicao: 'ln(1 + max(ports, 0)), calculado pelo pipeline.', uso: 'Representa a diversidade de portas em escala comprimida.', limite: 'Não contém a lista de portas nem identifica o serviço.' },
] as const

type FeatureConsulta = typeof featuresConsulta[number]['chave']
type ComportamentoConsulta = {
  id: string; nome: string; descricao: string; limite: string
  indicadores: readonly FeatureConsulta[]
}

export const comportamentosConsulta: readonly ComportamentoConsulta[] = [
  { id: 'dos', nome: 'DoS / possível DDoS', descricao: 'Volume e repetição de registros podem contextualizar tráfego intenso compatível com negação de serviço. A interpretação exige comparação com a atividade legítima do ambiente.', limite: 'Uma janela agrupada por origem não comprova DDoS. Distribuição entre múltiplas origens e impacto no serviço precisam de evidência adicional; as 13 features não incluem flags SYN.', indicadores: ['connections', 'bytes', 'packets', 'packet_size'] },
  { id: 'brute-force', nome: 'Brute force — indícios de rede', descricao: 'Registros repetidos de conexão podem motivar investigação de acesso a serviços. O Sinalyx possui categorias de força bruta e atividade SSH suspeita, apoiadas também por metadados do pipeline.', limite: 'Logs de firewall não confirmam falhas de senha. As 13 features não contêm autenticações, porta específica ou sequência temporal entre janelas. São necessários logs do serviço para confirmar força bruta.', indicadores: ['connections', 'ports', 'bytes_per_connection', 'packets_per_connection'] },
  { id: 'port-scan', nome: 'Port scan', descricao: 'Diversidade de portas de destino e repetição de registros podem estar associadas à sondagem de serviços. Ferramentas administrativas legítimas também podem produzir esse padrão.', limite: 'A contagem de portas não comprova intenção, portas abertas ou sequência da sondagem. Um scan lento pode ultrapassar a janela observada.', indicadores: ['ports', 'connections', 'packet_size'] },
  { id: 'anomalo', nome: 'Tráfego anômalo', descricao: 'Volumes, tamanhos e relações entre registros podem ajudar a contextualizar desvios do comportamento aprendido ou observações estatisticamente incomuns.', limite: 'Atividade legítima também pode ser incomum. Estes valores não mostram qual feature causou a decisão ou a contribuição individual de um modelo.', indicadores: ['bytes_per_packet', 'bytes_per_connection', 'packets_per_connection', 'log1p_connections', 'log1p_bytes', 'log1p_packets', 'log1p_packet_size', 'log1p_ports'] },
]

export const referenciasConsulta = [
  { nome: 'MITRE ATT&CK — T1498: Network Denial of Service', url: 'https://attack.mitre.org/techniques/T1498/' },
  { nome: 'MITRE ATT&CK — T1046: Network Service Discovery', url: 'https://attack.mitre.org/techniques/T1046/' },
  { nome: 'MITRE ATT&CK — T1110: Brute Force', url: 'https://attack.mitre.org/techniques/T1110/' },
  { nome: 'NIST SP 800-94 — seção 2.3.2: Anomaly-Based Detection', url: 'https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-94.pdf' },
] as const
