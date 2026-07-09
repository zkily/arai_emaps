import type { ProductLabelConfig } from '@/api/master/productLabelConfig'
import { productNameColorLabel } from '@/api/master/productLabelConfig'
import { buildPrintHtmlDocument, escapeHtml, openPrintWindow } from '@/utils/printWindow'

export interface ProductLabelConfigListPrintMeta {
  keyword?: string
  printedAt?: string
  total?: number
}

function normalizeSlots(row: ProductLabelConfig): (string | null)[] {
  const slots: (string | null)[] = []
  for (let i = 0; i < 8; i += 1) {
    const fromArr = row.process_slots?.[i]
    if (fromArr != null && String(fromArr).trim()) {
      slots.push(String(fromArr).trim())
      continue
    }
    const field = `process_slot_${i + 1}` as keyof ProductLabelConfig
    const val = row[field]
    slots.push(val != null && String(val).trim() ? String(val).trim() : null)
  }
  return slots
}

function cell(value: string | number | null | undefined): string {
  const text = value == null || value === '' ? '—' : String(value)
  return escapeHtml(text)
}

function topSlotHeader(i: number): string {
  if (i === 4) return '4（手直し）'
  return String(i)
}

function buildTableHeadHtml(): string {
  const topSlots = [1, 2, 3, 4].map((i) => `<th>${topSlotHeader(i)}</th>`).join('')
  const bottomSlots = [5, 6, 7, 8].map((i) => `<th>${i}</th>`).join('')
  return `
    <thead>
      <tr>
        <th rowspan="2">製品CD</th>
        <th rowspan="2">製品名（マスタ）</th>
        <th rowspan="2">終息</th>
        <th rowspan="2">加工用製品名</th>
        <th rowspan="2">入数</th>
        <th rowspan="2">区分</th>
        <th rowspan="2">用紙色</th>
        <th rowspan="2">製品名色</th>
        <th rowspan="2">固定</th>
        <th colspan="4">上段（枠1〜4）</th>
        <th colspan="4">下段（枠5〜8）</th>
        <th rowspan="2">備考</th>
      </tr>
      <tr>
        ${topSlots}
        ${bottomSlots}
      </tr>
    </thead>
  `
}

function buildTableRowHtml(row: ProductLabelConfig): string {
  const slots = normalizeSlots(row)
  const slotCells = slots.map((s) => `<td>${cell(s)}</td>`).join('')
  const supplyType = (row.supply_type || '社内').trim() === '外注' ? '外注' : '社内'
  const discontinued = row.is_discontinued ? '終息' : '現行'
  const upperLock = row.upper_slots_locked ? 'ON' : 'OFF'
  const nameColor = productNameColorLabel(row.product_name_color)

  return `
    <tr>
      <td class="col-cd">${cell(row.product_cd)}</td>
      <td class="col-name">${cell(row.master_product_name)}</td>
      <td class="col-center">${cell(discontinued)}</td>
      <td class="col-label">${cell(row.label_product_name)}</td>
      <td class="col-center">${cell(row.process_unit_qty)}</td>
      <td class="col-center">${cell(supplyType)}</td>
      <td class="col-center">${cell(row.paper_color || '白')}</td>
      <td class="col-center">${cell(nameColor)}</td>
      <td class="col-center">${cell(upperLock)}</td>
      ${slotCells}
      <td class="col-remark">${cell(row.remark)}</td>
    </tr>
  `
}

const LIST_PRINT_STYLES = `
  @page { size: A4 landscape; margin: 8mm 10mm; }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    padding: 0;
    font-family: 'Yu Gothic UI', 'Yu Gothic', 'MS Gothic', 'Hiragino Sans', sans-serif;
    color: #111;
    font-size: 9px;
    line-height: 1.35;
  }
  .print-header {
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 1.5pt solid #0d9488;
  }
  .print-title {
    margin: 0 0 4px;
    font-size: 14px;
    font-weight: 800;
    color: #0f766e;
    letter-spacing: 0.04em;
  }
  .print-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 16px;
    font-size: 9px;
    color: #475569;
  }
  .print-meta strong {
    color: #0f172a;
    font-weight: 700;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
  }
  thead {
    display: table-header-group;
  }
  tr {
    page-break-inside: avoid;
  }
  th, td {
    border: 0.6pt solid #64748b;
    padding: 2px 3px;
    vertical-align: middle;
    word-break: break-all;
    overflow-wrap: anywhere;
  }
  th {
    background: #ecfeff;
    color: #0f766e;
    font-weight: 700;
    text-align: center;
    font-size: 8px;
    padding: 3px 2px;
  }
  tbody tr:nth-child(even) td {
    background: #f8fafc;
  }
  .col-cd { width: 5.5%; text-align: center; font-weight: 700; }
  .col-name { width: 9%; }
  .col-label { width: 9%; }
  .col-center { text-align: center; width: 4.2%; }
  .col-remark { width: 7%; }
  td.col-cd { font-weight: 700; }
  @media print {
    .print-header { margin-bottom: 4px; }
    th {
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    tbody tr:nth-child(even) td {
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
  }
`

export function buildProductLabelConfigListPrintHtml(
  rows: ProductLabelConfig[],
  meta: ProductLabelConfigListPrintMeta = {}
): string {
  const printedAt = meta.printedAt ?? new Date().toLocaleString('ja-JP')
  const keyword = (meta.keyword || '').trim()
  const total = meta.total ?? rows.length
  const keywordLine = keyword
    ? `<span>検索: <strong>${escapeHtml(keyword)}</strong></span>`
    : '<span>検索: <strong>（なし）</strong></span>'

  const body = `
    <div class="print-header">
      <h1 class="print-title">成型用ラベル設定一覧</h1>
      <div class="print-meta">
        <span>印刷日時: <strong>${escapeHtml(printedAt)}</strong></span>
        ${keywordLine}
        <span>件数: <strong>${total}</strong> 件</span>
      </div>
    </div>
    <table>
      ${buildTableHeadHtml()}
      <tbody>
        ${rows.map((row) => buildTableRowHtml(row)).join('')}
      </tbody>
    </table>
  `

  return buildPrintHtmlDocument('成型用ラベル設定一覧', LIST_PRINT_STYLES, body)
}

export function printProductLabelConfigList(
  rows: ProductLabelConfig[],
  meta?: ProductLabelConfigListPrintMeta
): void {
  const html = buildProductLabelConfigListPrintHtml(rows, meta)
  openPrintWindow(html, { autoPrint: true, autoClose: true, delayMs: 400 })
}
