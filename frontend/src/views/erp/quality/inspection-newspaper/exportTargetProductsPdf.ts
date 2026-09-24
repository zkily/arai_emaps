import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'

export interface TargetProductPdfRow {
  product_cd: string
  product_name: string | null
  updated_by: string | null
}

const PAGE_WIDTH_PX = 794
const PAGE_HEIGHT_PX = 1123

const SHEET_CSS = `
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: #fff; }
  .sheet {
    width: ${PAGE_WIDTH_PX}px;
    background: #fff;
    color: #0f172a;
    font-family: "Yu Gothic UI", "Yu Gothic", "Meiryo", "Hiragino Sans", "MS PGothic", sans-serif;
  }
  .sheet--page {
    height: ${PAGE_HEIGHT_PX}px;
    padding: 32px 36px 28px;
  }
  .sheet--measure {
    width: ${PAGE_WIDTH_PX}px;
    padding: 32px 36px 0;
  }
  .sheet-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 16px;
    border-bottom: 2px solid #059669;
    padding-bottom: 10px;
    margin-bottom: 12px;
  }
  h1 { margin: 0; font-size: 20px; font-weight: 700; letter-spacing: 0.02em; }
  .sub { margin: 4px 0 0; font-size: 12px; color: #64748b; }
  .meta { text-align: right; font-size: 12px; color: #334155; line-height: 1.55; white-space: nowrap; }
  table { width: 100%; border-collapse: collapse; table-layout: fixed; }
  th {
    background: #ecfdf5;
    color: #065f46;
    font-size: 12px;
    font-weight: 700;
    text-align: left;
    padding: 7px 8px;
    border: 1px solid #a7f3d0;
  }
  td {
    font-size: 12px;
    line-height: 1.45;
    padding: 6px 8px;
    border: 1px solid #e2e8f0;
    vertical-align: top;
    word-break: break-all;
  }
  .no { width: 46px; text-align: right; font-variant-numeric: tabular-nums; }
  .cd { width: 130px; font-weight: 700; }
  .by { width: 110px; }
  .sheet-foot {
    margin-top: 10px;
    font-size: 11px;
    color: #64748b;
    display: flex;
    justify-content: space-between;
  }
`

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function rowsHtml(products: TargetProductPdfRow[], offset: number): string {
  return products
    .map((row, index) => {
      const name = (row.product_name || '').trim() || '—'
      const updatedBy = (row.updated_by || '').trim() || '—'
      return `<tr>
        <td class="no">${offset + index + 1}</td>
        <td class="cd">${escapeHtml(row.product_cd)}</td>
        <td>${escapeHtml(name)}</td>
        <td class="by">${escapeHtml(updatedBy)}</td>
      </tr>`
    })
    .join('')
}

function tableHtml(body: string): string {
  return `<table>
    <thead>
      <tr>
        <th class="no">No.</th>
        <th class="cd">製品CD</th>
        <th>製品名</th>
        <th class="by">更新者</th>
      </tr>
    </thead>
    <tbody>${body}</tbody>
  </table>`
}

function headHtml(exportedAt: string, total: number): string {
  return `<header class="sheet-head">
    <div>
      <h1>検査通知(防錆) 対象製品</h1>
      <p class="sub">新聞紙を入れる対象製品一覧　全 ${total} 件</p>
    </div>
    <div class="meta">出力日時<br>${escapeHtml(exportedAt)}</div>
  </header>`
}

function documentHtml(body: string): string {
  return `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>${SHEET_CSS}</style></head><body>${body}</body></html>`
}

function formatExportedAt(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function formatFileStamp(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}`
}

async function withFrame<T>(
  width: number,
  height: number,
  html: string,
  run: (doc: Document) => Promise<T>,
): Promise<T> {
  const iframe = document.createElement('iframe')
  iframe.setAttribute('title', 'inspection-newspaper-pdf')
  iframe.style.cssText = `position:fixed;left:-12000px;top:0;width:${width}px;height:${height}px;border:0;opacity:0;pointer-events:none`
  document.body.appendChild(iframe)
  try {
    const doc = iframe.contentDocument
    if (!doc) throw new Error('PDFの生成に失敗しました')
    doc.open()
    doc.write(html)
    doc.close()
    if (doc.fonts?.ready) await doc.fonts.ready
    await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
    return await run(doc)
  } finally {
    iframe.remove()
  }
}

function paginate(heights: number[], available: number): number[][] {
  const pages: number[][] = []
  let current: number[] = []
  let used = 0
  heights.forEach((height, index) => {
    const rowHeight = Math.max(height, 1)
    if (current.length > 0 && used + rowHeight > available) {
      pages.push(current)
      current = []
      used = 0
    }
    current.push(index)
    used += rowHeight
  })
  if (current.length > 0) pages.push(current)
  return pages
}

async function measurePages(products: TargetProductPdfRow[], exportedAt: string): Promise<number[][]> {
  const html = documentHtml(
    `<div class="sheet sheet--measure">${headHtml(exportedAt, products.length)}${tableHtml(rowsHtml(products, 0))}</div>`,
  )
  const frameHeight = Math.max(600, products.length * 64 + 240)
  return withFrame(PAGE_WIDTH_PX, frameHeight, html, async (doc) => {
    const header = doc.querySelector('.sheet-head')
    const thead = doc.querySelector('thead')
    const headerHeight = header ? Math.ceil(header.getBoundingClientRect().height) : 72
    const theadHeight = thead ? Math.ceil(thead.getBoundingClientRect().height) : 32
    const available = PAGE_HEIGHT_PX - 32 - 28 - headerHeight - 12 - theadHeight - 40
    const heights = Array.from(doc.querySelectorAll('tbody tr')).map((row) =>
      Math.ceil(row.getBoundingClientRect().height),
    )
    return paginate(heights, Math.max(available, 120))
  })
}

async function capturePage(
  products: TargetProductPdfRow[],
  exportedAt: string,
  total: number,
  startIndex: number,
  pageIndex: number,
  pageCount: number,
): Promise<string> {
  const html = documentHtml(
    `<div class="sheet sheet--page">
      ${headHtml(exportedAt, total)}
      ${tableHtml(rowsHtml(products, startIndex))}
      <footer class="sheet-foot"><span>Smart-EMAP</span><span>${pageIndex + 1} / ${pageCount}</span></footer>
    </div>`,
  )
  return withFrame(PAGE_WIDTH_PX, PAGE_HEIGHT_PX, html, async (doc) => {
    const sheet = doc.querySelector('.sheet') as HTMLElement | null
    if (!sheet) throw new Error('PDFの生成に失敗しました')
    const canvas = await html2canvas(sheet, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
      width: PAGE_WIDTH_PX,
      height: PAGE_HEIGHT_PX,
      windowWidth: PAGE_WIDTH_PX,
      windowHeight: PAGE_HEIGHT_PX,
      scrollX: 0,
      scrollY: 0,
    })
    return canvas.toDataURL('image/jpeg', 0.92)
  })
}

export async function exportInspectionNewspaperProductsPdf(products: TargetProductPdfRow[]): Promise<void> {
  if (products.length === 0) return
  const now = new Date()
  const exportedAt = formatExportedAt(now)
  const pages = await measurePages(products, exportedAt)
  const pdf = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4', compress: true })
  for (let i = 0; i < pages.length; i += 1) {
    const indexes = pages[i]
    const slice = indexes.map((index) => products[index])
    const image = await capturePage(slice, exportedAt, products.length, indexes[0] ?? 0, i, pages.length)
    if (i > 0) pdf.addPage()
    pdf.addImage(image, 'JPEG', 0, 0, 210, 297, undefined, 'FAST')
  }
  pdf.save(`検査通知(防錆)_対象製品_${formatFileStamp(now)}.pdf`)
}
