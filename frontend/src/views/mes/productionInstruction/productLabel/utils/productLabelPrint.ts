import { buildPrintHtmlDocument, escapeHtml, openPrintWindow } from '@/utils/printWindow'
import type { ProductLabelPreview } from '@/api/mes/productLabel'

export interface ProductLabelPrintInput {
  label_product_name: string
  process_unit_qty: number | null
  product_name_color: string
  top_row: {
    machine_1: string
    machine_2: string
    machine_3: string
    machine_4_fixed: string
  }
  process_slots: (string | null)[]
}

export interface ProductLabelPrintOptions {
  pages?: number
  copiesPerPage?: number
}

const PRINT_COLUMNS = 4
const TENAOSHI = '手直し'

/** 8枠データを正規化 */
export function normalizePrintSlots(slots?: (string | null)[] | null): (string | null)[] {
  const result: (string | null)[] = []
  for (let i = 0; i < 8; i++) {
    const v = slots?.[i]
    result.push(v != null && String(v).trim() ? String(v).trim() : null)
  }
  return result
}

/**
 * 参考レイアウトに合わせた印刷用グリッド
 * 上段：枠1〜3（成型設備）＋空欄
 * 下段：枠5（空欄可）｜枠4（手直し）｜枠5〜8の後工程（右寄せ・末尾2件を表示）
 */
export function buildPrintGridFromSlots(slots?: (string | null)[] | null): {
  topRow: string[]
  bottomRow: string[]
} {
  const s = normalizePrintSlots(slots)

  const topRow = [s[0] || '', s[1] || '', s[2] || '', '']

  const postMolding = s.slice(4, 8).filter((v) => v)
  const postTail = postMolding.slice(-2)

  const bottomRow = [
    s[4] || '',
    s[3] || TENAOSHI,
    postTail[0] || '',
    postTail[1] || '',
  ]

  return { topRow, bottomRow }
}

function buildGridCell(text: string): string {
  const label = escapeHtml(text || '')
  return `<td><div class="cell-header">${label}</div><div class="cell-body"></div></td>`
}

function buildOneLabelHtml(data: ProductLabelPrintInput): string {
  const nameColor = escapeHtml(data.product_name_color || '#000000')
  const productName = escapeHtml(data.label_product_name || '')
  const qty =
    data.process_unit_qty != null && data.process_unit_qty !== ('' as unknown as number)
      ? escapeHtml(String(data.process_unit_qty))
      : ''

  const { topRow, bottomRow } = buildPrintGridFromSlots(data.process_slots)

  const topRowHtml = topRow.map((cell) => buildGridCell(cell)).join('')
  const bottomRowHtml = bottomRow.map((cell) => buildGridCell(cell)).join('')

  return `
    <div class="label-card">
      <div class="label-title">現品票</div>
      <div class="label-body">
        <div class="label-product" style="color:${nameColor}">${productName}</div>
        <div class="label-qty">
          <span class="label-qty-lbl">入数</span>
          <span class="label-qty-val">${qty}</span>
        </div>
      </div>
      <table class="route-grid">
        <tr class="route-row-top">${topRowHtml}</tr>
        <tr class="route-row-bottom">${bottomRowHtml}</tr>
      </table>
    </div>
  `
}

const PRINT_STYLES = `
  @page { size: A4 portrait; margin: 8mm; }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    padding: 0;
    font-family: 'Yu Gothic UI', 'Yu Gothic', 'MS Gothic', 'Hiragino Sans', sans-serif;
  }
  .sheet {
    width: 194mm;
    height: 281mm;
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: repeat(3, 1fr);
    gap: 2mm;
    page-break-after: always;
  }
  .sheet:last-child { page-break-after: auto; }
  .label-card {
    border: 1.5px solid #111;
    padding: 2.5mm 2.5mm 2mm;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
    background: #fff;
  }
  .label-title {
    text-align: center;
    font-size: 13px;
    font-weight: 700;
    text-decoration: underline;
    text-underline-offset: 2px;
    border: 1px solid #111;
    padding: 3px 6px;
    margin-bottom: 5px;
    letter-spacing: 0.12em;
    line-height: 1.2;
  }
  .label-body {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 6px;
    margin-bottom: 5px;
    min-height: 14mm;
    padding: 0 1mm;
  }
  .label-product {
    font-size: 26px;
    font-weight: 800;
    line-height: 1.05;
    flex: 1;
    word-break: break-word;
    letter-spacing: 0.02em;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .label-qty {
    display: flex;
    align-items: baseline;
    gap: 5px;
    white-space: nowrap;
    flex-shrink: 0;
    padding-bottom: 1px;
  }
  .label-qty-lbl {
    font-size: 13px;
    font-weight: 700;
    color: #111;
  }
  .label-qty-val {
    font-size: 22px;
    font-weight: 800;
    color: #111;
    line-height: 1;
  }
  .route-grid {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    margin-top: auto;
    border-top: 1px solid #111;
  }
  .route-grid td {
    border-left: 1px dotted #444;
    vertical-align: top;
    padding: 0;
    height: 18mm;
  }
  .route-grid td:first-child { border-left: none; }
  .cell-header {
    text-align: center;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 2px 3px;
    line-height: 1.2;
    min-height: 5mm;
    word-break: break-word;
    color: #111;
  }
  .cell-body {
    min-height: 11mm;
    border-top: none;
  }
  .route-row-top td {
    border-bottom: 1px solid #111;
  }
  .route-row-top .cell-header {
    font-size: 12px;
  }
  .route-row-bottom .cell-header {
    font-size: 11px;
  }
  @media print {
    .label-product {
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    .label-card {
      border-color: #000 !important;
    }
  }
`

export function buildProductLabelPrintHtml(
  data: ProductLabelPrintInput,
  options: ProductLabelPrintOptions = {}
): string {
  const pages = Math.max(1, options.pages ?? 1)
  const copiesPerPage = options.copiesPerPage ?? 6
  const oneLabel = buildOneLabelHtml(data)
  const labelsOnPage = Array.from({ length: copiesPerPage }, () => oneLabel).join('')
  const sheets = Array.from({ length: pages }, () => `<div class="sheet">${labelsOnPage}</div>`).join('')
  return buildPrintHtmlDocument('現品票', PRINT_STYLES, sheets)
}

export function printProductLabels(
  data: ProductLabelPrintInput,
  options: ProductLabelPrintOptions = {}
): void {
  const html = buildProductLabelPrintHtml(data, options)
  openPrintWindow(html, { autoPrint: true, autoClose: true, delayMs: 400 })
}

export function previewFromApiData(preview: ProductLabelPreview): ProductLabelPrintInput {
  return {
    label_product_name: preview.label_product_name,
    process_unit_qty: preview.process_unit_qty,
    product_name_color: preview.product_name_color || '#000000',
    top_row: preview.top_row,
    process_slots: [...(preview.process_slots || [])],
  }
}
