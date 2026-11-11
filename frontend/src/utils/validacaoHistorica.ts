/** Valores e metodologia da validação histórica. Não representam medição da sessão atual. */

// Evidência fixa e documentada; não representa a execução operacional atual.
// Fontes: docs/evidencias/ablation_tcc_reproducible_v1.md e
// docs/evidencias/component_contribution_methodology_v1.md.
export const validacaoHistorica = {
  titulo: 'Validação histórica reproduzida',
  janelas: 355,
  metricas: [
    { nome: 'Precision', valor: 0.9948, descricao: 'Precisão dos alertas por janela' },
    { nome: 'Recall', valor: 0.9143, descricao: 'Detecção dos casos positivos por janela' },
    { nome: 'F1-score', valor: 0.9529, descricao: 'Equilíbrio entre precision e recall' },
    { nome: 'FPR', valor: 0.0069, descricao: 'Taxa de falsos positivos por janela' },
  ],
  matriz: { tn: 144, fp: 1, fn: 18, tp: 192 },
  contribuicoes: [
    { nome: 'Regras de segurança', percentual: 55.22 },
    { nome: 'Autoencoder', percentual: 30.40 },
    { nome: 'Isolation Forest', percentual: 14.38 },
  ],
  limitacoes: [
    'O recall histórico de 91,43% ficou abaixo da meta de 95%.',
    'Logs de firewall do pfSense permitem observar conexões, portas, protocolo, volume e repetição, mas não tentativas de senha ou falhas de autenticação.',
    'SYN Flood indica um padrão compatível com o cenário controlado de negação de serviço; não comprova origens distribuídas.',
    'O Sinalyx usa uma arquitetura híbrida e não bloqueia ataques automaticamente. A coleta contínua direta permanece experimental/congelada.',
  ],
} as const
