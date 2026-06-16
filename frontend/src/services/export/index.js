import { toast } from '@/services/toast'

function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  setTimeout(() => {
    a.remove()
    URL.revokeObjectURL(url)
  }, 100)
}

const esc = (v) => String(v ?? '')

export function exportRows(format, filename, headers, rows) {
  if (format === 'copy') {
    const tsv = [headers.join('\t'), ...rows.map((r) => r.map(esc).join('\t'))].join('\n')
    const done = () => toast('success', 'Copiado al portapapeles', `${headers.length} columnas · ${rows.length} filas`)
    if (navigator.clipboard) {
      navigator.clipboard.writeText(tsv).then(done, done)
    } else {
      done()
    }
    return
  }
  if (format === 'csv') {
    const csv = [headers, ...rows]
      .map((r) => r.map((c) => `"${esc(c).replace(/"/g, '""')}"`).join(','))
      .join('\n')
    downloadBlob(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' }), filename + '.csv')
    toast('success', 'CSV descargado', filename + '.csv')
    return
  }
  if (format === 'xlsx') {
    const cells = (cols) => cols.map((c) => `<td>${esc(c)}</td>`).join('')
    const html = `<html xmlns:x="urn:schemas-microsoft-com:office:excel"><head><meta charset="utf-8"></head><body><table><tr>${headers
      .map((h) => `<th>${esc(h)}</th>`)
      .join('')}</tr>${rows.map((r) => `<tr>${cells(r)}</tr>`).join('')}</table></body></html>`
    downloadBlob(new Blob([html], { type: 'application/vnd.ms-excel' }), filename + '.xls')
    toast('success', 'Excel descargado', filename + '.xls')
    return
  }
  if (format === 'pdf') {
    const win = window.open('', '_blank')
    if (!win) {
      toast('error', 'No se pudo abrir el PDF', 'Permite las ventanas emergentes')
      return
    }
    const style = `body{font-family:'Segoe UI',Arial,sans-serif;color:#242424;padding:32px}h1{font-size:18px;color:#107c41;border-bottom:2px solid #107c41;padding-bottom:8px}table{border-collapse:collapse;width:100%;margin-top:16px;font-size:12px}th{text-align:left;background:#f3f2f1;padding:6px 10px;border:1px solid #e1dfdd}td{padding:6px 10px;border:1px solid #e1dfdd;font-variant-numeric:tabular-nums}`
    win.document.write(
      `<html><head><title>${filename}</title><style>${style}</style></head><body><h1>${filename}</h1><table><thead><tr>${headers
        .map((h) => `<th>${esc(h)}</th>`)
        .join('')}</tr></thead><tbody>${rows
        .map((r) => `<tr>${r.map((c) => `<td>${esc(c)}</td>`).join('')}</tr>`)
        .join('')}</tbody></table></body></html>`,
    )
    win.document.close()
    setTimeout(() => win.print(), 300)
    toast('info', 'Preparando PDF…', filename)
  }
}
