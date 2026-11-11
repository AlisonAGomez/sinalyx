/** Exportações JSON e documentos de impressão com escape dos valores inseridos. */

export interface ExportColumn<TItem> {
  header: string
  value: (item: TItem) => unknown
}

export interface DefinitionField {
  label: string
  value: unknown
}

/** Escapa caracteres especiais antes de inserir valores nos documentos exportados. */
export function escapeHtml(value: unknown): string {
  if (value === null || typeof value === 'undefined' || value === '') {
    return '-'
  }

  const text = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/** Disponibiliza o conteúdo como arquivo e libera o endereço temporário após o uso. */
function downloadFile(filename: string, content: string, type: string): void {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/** Monta o arquivo JSON para download no navegador. */
export function exportJson(filename: string, payload: unknown): boolean {
  if (
    payload === null ||
    typeof payload === 'undefined' ||
    (Array.isArray(payload) && payload.length === 0)
  ) {
    return false
  }

  downloadFile(
    filename,
    JSON.stringify(payload, null, 2),
    'application/json;charset=utf-8',
  )
  return true
}

/** Monta uma tabela de exportação escapando os títulos e os valores. */
export function buildHtmlTable<TItem>(
  rows: TItem[],
  columns: ExportColumn<TItem>[],
): string {
  if (rows.length === 0) {
    return '<p class="empty">Nenhum dado disponível.</p>'
  }

  const headers = columns
    .map((column) => `<th>${escapeHtml(column.header)}</th>`)
    .join('')
  const body = rows
    .map((row) => {
      const cells = columns
        .map((column) => `<td>${escapeHtml(column.value(row))}</td>`)
        .join('')
      return `<tr>${cells}</tr>`
    })
    .join('')

  return `<table><thead><tr>${headers}</tr></thead><tbody>${body}</tbody></table>`
}

/** Monta os pares de rótulo e valor usados nos documentos exportados. */
export function buildDefinitionTable(fields: DefinitionField[]): string {
  const rows = fields
    .map(
      (field) =>
        `<tr><th>${escapeHtml(field.label)}</th><td>${escapeHtml(field.value)}</td></tr>`,
    )
    .join('')

  return `<table class="definition"><tbody>${rows}</tbody></table>`
}

/** Abre o documento para impressão ou gravação em PDF pelo navegador. */
export function exportPdfDocument(title: string, bodyHtml: string): boolean {
  if (!bodyHtml.trim()) {
    return false
  }

  const printWindow = window.open('', '_blank', 'width=1100,height=800')
  if (!printWindow) {
    return false
  }
  // A janela é local e recebe somente conteúdo montado pelos helpers de exportação.
  // Remove a referência ao opener para reduzir risco de tabnabbing/reuso indevido.
  try { printWindow.opener = null } catch { /* proteção best-effort */ }

  const generatedAt = new Date().toLocaleString('pt-BR')
  printWindow.document.write(`<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(title)}</title>
  <style>
    @page { margin: 16mm; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #ffffff;
      color: #172033;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 12px;
      line-height: 1.45;
    }
    header {
      border-bottom: 2px solid #0ea5e9;
      margin-bottom: 20px;
      padding-bottom: 12px;
    }
    h1 {
      color: #0f172a;
      font-size: 24px;
      margin: 0 0 4px;
    }
    h2 {
      color: #0f172a;
      font-size: 16px;
      margin: 22px 0 10px;
    }
    h3 {
      color: #1e293b;
      font-size: 13px;
      margin: 14px 0 6px;
    }
    p { margin: 0 0 8px; }
    .subtitle { color: #475569; }
    .section { break-inside: avoid; margin-bottom: 16px; }
    table {
      border-collapse: collapse;
      margin: 8px 0 14px;
      table-layout: fixed;
      width: 100%;
    }
    th, td {
      border: 1px solid #cbd5e1;
      padding: 7px 8px;
      text-align: left;
      vertical-align: top;
      word-break: break-word;
    }
    thead th {
      background: #e0f2fe;
      color: #0f172a;
      font-weight: 700;
    }
    .definition th {
      background: #f1f5f9;
      width: 32%;
    }
    pre {
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      overflow-wrap: anywhere;
      padding: 10px;
      white-space: pre-wrap;
    }
    .empty { color: #64748b; font-style: italic; }
    .no-print {
      margin-top: 18px;
    }
    .no-print button {
      background: #0284c7;
      border: 0;
      border-radius: 6px;
      color: #ffffff;
      cursor: pointer;
      font-weight: 700;
      padding: 10px 14px;
    }
    @media print {
      .no-print { display: none; }
    }
  </style>
</head>
<body>
  <header>
    <h1>${escapeHtml(title)}</h1>
    <p class="subtitle">Sinalyx · Análise de logs de firewall</p>
    <p class="subtitle">Gerado em ${escapeHtml(generatedAt)}</p>
  </header>
  ${bodyHtml}
  <div class="no-print">
    <button type="button" id="print-report">Imprimir / salvar em PDF</button>
  </div>
</body>
</html>`)
  // O popup herda a CSP: eventos são vinculados pelo código da aplicação, sem script inline.
  printWindow.document.getElementById('print-report')?.addEventListener('click', () => printWindow.print())
  printWindow.addEventListener('load', () => {
    printWindow.setTimeout(() => printWindow.print(), 250)
  }, { once: true })
  printWindow.document.close()
  printWindow.focus()
  return true
}

/** Gera a parte de data usada nos nomes dos arquivos exportados. */
export function dateStamp(date = new Date()): string {
  return date.toISOString().slice(0, 10)
}
