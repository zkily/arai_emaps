/**
 * 成型計画試算 — 指定工程計画合計明細印刷（設備グループ対応）
 */
import type { DailyMatrixRow, OrderMatrixRow } from '@/api/formingDailyPlan'
import { formatDateTimeJST } from '@/utils/dateFormat'
import { fmtFormingNumber } from '../components/formingDailyPlanConstants'

export const UNSET_MACHINE_LABEL = '(設備未設定)'

const PRINT_LABELS_JA = {
  titleSuffix: '計画合計明細',
  period: '期間',
  printedAt: '印刷',
  processTotal: '工程合計',
  productCount: '製品数',
  machineGroupCount: '設備グループ数',
  colProductName: '製品名',
  colPeriodTotal: '期間合計',
  grandTotal: '合計',
  subtotal: '小計',
  noData: 'データがありません',
  machineLabel: '設備',
  productUnit: '製品',
  docTitle: '工程計画明細',
  orderTitleSuffix: '受注合計明細',
  orderDocTitle: '受注工程明細',
  orderProcessTotal: '受注合計',
} as const

export type ProcessPlanPrintLabels = typeof PRINT_LABELS_JA

const PRINT_STYLES = `
  * { box-sizing: border-box; }
  html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body {
    margin: 0;
    padding: 8mm 10mm;
    font-family: 'Meiryo', 'Hiragino Sans', 'Yu Gothic', 'Segoe UI', sans-serif;
    font-size: 9pt;
    color: #1e293b;
    line-height: 1.35;
  }
  .print-hd {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 6mm;
    padding-bottom: 3mm;
    border-bottom: 2px solid #2563eb;
  }
  .print-title { font-size: 14pt; font-weight: 700; margin: 0; }
  .print-meta { font-size: 8pt; color: #64748b; text-align: right; }
  .print-summary {
    margin-bottom: 4mm;
    font-size: 10pt;
    font-weight: 600;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 8pt;
  }
  th, td {
    border: 1px solid #cbd5e1;
    padding: 2px 4px;
    text-align: right;
  }
  th:first-child, td:first-child {
    text-align: left;
  }
  th {
    background: #f1f5f9;
    font-weight: 600;
  }
  tr:nth-child(even):not(.group-header):not(.group-subtotal) td { background: #f8fafc; }
  .col-total { font-weight: 600; background: #eff6ff !important; }
  tr.group-header td {
    background: #dbeafe !important;
    font-weight: 700;
    text-align: left !important;
    padding: 3px 6px;
    border-top: 2px solid #93c5fd;
  }
  tr.group-subtotal td {
    background: #fef3c7 !important;
    font-weight: 600;
  }
  tfoot td { font-weight: 700; background: #e0e7ff !important; }
  @page { size: A3 landscape; margin: 8mm; }
`

function escHtml(s: string) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function cellQty(cell: DailyMatrixRow['by_date'][string] | undefined): number {
  if (!cell) return 0
  if (cell.override_plan != null) return Number(cell.override_plan) || 0
  if (cell.final_plan != null) return Number(cell.final_plan) || 0
  return Number(cell.derived_plan) || 0
}

type MatrixSourceRow = {
  product_cd: string
  process_key: string
  by_date: Record<string, unknown>
}

type QtyReader = (byDate: Record<string, unknown>, date: string) => number

function planQtyReader(byDate: Record<string, unknown>, d: string): number {
  return cellQty(byDate[d] as DailyMatrixRow['by_date'][string])
}

function orderQtyReader(byDate: Record<string, unknown>, d: string): number {
  return Number(byDate[d] ?? 0) || 0
}

interface PrintProductRow {
  product_cd: string
  product_name: string
  machine: string
  byDate: Record<string, number>
  total: number
}

export interface ProcessPlanPrintOptions {
  processKey: string
  processLabel: string
  periodStart: string
  periodEnd: string
  dates: string[]
  matrixRows: DailyMatrixRow[]
  products: {
    product_cd: string
    product_name?: string | null
    machines?: Record<string, string>
    molding_order?: number | null
  }[]
  printedAt?: string
  labels?: Partial<ProcessPlanPrintLabels>
}

function resolveMachine(
  productCd: string,
  processKey: string,
  products: ProcessPlanPrintOptions['products'],
): string {
  const p = products.find((x) => x.product_cd === productCd)
  const m = (p?.machines?.[processKey] || '').trim()
  return m || UNSET_MACHINE_LABEL
}

function getMoldingOrder(
  productCd: string,
  products: ProcessPlanPrintOptions['products'],
): number | null {
  const p = products.find((x) => x.product_cd === productCd)
  const o = p?.molding_order
  if (o == null || !Number.isFinite(Number(o))) return null
  return Number(o)
}

function compareByMoldingOrder(
  a: PrintProductRow,
  b: PrintProductRow,
  products: ProcessPlanPrintOptions['products'],
): number {
  const oa = getMoldingOrder(a.product_cd, products)
  const ob = getMoldingOrder(b.product_cd, products)
  if (oa != null && ob != null && oa !== ob) return oa - ob
  if (oa != null && ob == null) return -1
  if (oa == null && ob != null) return 1
  const nc = a.product_name.localeCompare(b.product_name, 'ja')
  if (nc !== 0) return nc
  return a.product_cd.localeCompare(b.product_cd, 'ja')
}

function sortMachineKeys(keys: string[]): string[] {
  return [...keys].sort((a, b) => {
    if (a === UNSET_MACHINE_LABEL) return 1
    if (b === UNSET_MACHINE_LABEL) return -1
    return a.localeCompare(b, 'ja')
  })
}

function sumByDate(rows: PrintProductRow[], dates: string[]): Record<string, number> {
  const out: Record<string, number> = {}
  for (const d of dates) {
    out[d] = rows.reduce((s, r) => s + (r.byDate[d] || 0), 0)
  }
  return out
}

function buildDayCells(byDate: Record<string, number>, dates: string[]): string {
  return dates.map((d) => `<td>${fmtFormingNumber(byDate[d])}</td>`).join('')
}

export function buildProcessPlanPrintHtml(opts: ProcessPlanPrintOptions): string {
  return buildDetailPrintHtml({ ...opts, readQty: planQtyReader })
}

export function buildOrderProcessPrintHtml(
  opts: Omit<ProcessPlanPrintOptions, 'matrixRows'> & { matrixRows: OrderMatrixRow[] },
): string {
  return buildDetailPrintHtml({ ...opts, readQty: orderQtyReader })
}

function buildDetailPrintHtml(
  opts: Omit<ProcessPlanPrintOptions, 'matrixRows'> & {
    matrixRows: MatrixSourceRow[]
    readQty: QtyReader
  },
): string {
  const L = { ...PRINT_LABELS_JA, ...opts.labels }
  const { processKey, processLabel, periodStart, periodEnd, dates, matrixRows, products, readQty } = opts
  const nameMap = new Map(products.map((p) => [p.product_cd, p.product_name || '']))
  const processRows = matrixRows.filter((r) => r.process_key === processKey)
  const colSpan = 2 + dates.length

  const tableRows: PrintProductRow[] = processRows
    .map((r) => {
      const byDate: Record<string, number> = {}
      let total = 0
      for (const d of dates) {
        const q = readQty(r.by_date, d)
        byDate[d] = q
        total += q
      }
      return {
        product_cd: r.product_cd,
        product_name: nameMap.get(r.product_cd) || '',
        machine: resolveMachine(r.product_cd, processKey, products),
        byDate,
        total,
      }
    })
    .filter((r) => r.total > 0)

  const grouped = new Map<string, PrintProductRow[]>()
  for (const row of tableRows) {
    const list = grouped.get(row.machine) || []
    list.push(row)
    grouped.set(row.machine, list)
  }
  for (const items of grouped.values()) {
    items.sort((a, b) => compareByMoldingOrder(a, b, products))
  }

  const flatRows = [...tableRows].sort((a, b) => compareByMoldingOrder(a, b, products))

  const hasRealMachine = [...grouped.keys()].some((k) => k !== UNSET_MACHINE_LABEL)
  const machineKeys = sortMachineKeys([...grouped.keys()])

  let bodyRows = ''
  if (tableRows.length === 0) {
    bodyRows = `<tr><td colspan="${colSpan}">${escHtml(L.noData)}</td></tr>`
  } else if (hasRealMachine) {
    for (const machine of machineKeys) {
      const items = grouped.get(machine) || []
      if (!items.length) continue
      bodyRows += `<tr class="group-header"><td colspan="${colSpan}">${escHtml(L.machineLabel)}：${escHtml(machine)}（${items.length} ${escHtml(L.productUnit)}）</td></tr>`
      for (const r of items) {
        bodyRows += `<tr>
          <td>${escHtml(r.product_name)}</td>
          <td class="col-total">${fmtFormingNumber(r.total)}</td>
          ${buildDayCells(r.byDate, dates)}
        </tr>`
      }
      const subByDate = sumByDate(items, dates)
      const subTotal = items.reduce((s, r) => s + r.total, 0)
      bodyRows += `<tr class="group-subtotal">
        <td>${escHtml(L.subtotal)}（${escHtml(machine)}）</td>
        <td class="col-total">${fmtFormingNumber(subTotal)}</td>
        ${buildDayCells(subByDate, dates)}
      </tr>`
    }
  } else {
    for (const r of flatRows) {
      bodyRows += `<tr>
        <td>${escHtml(r.product_name)}</td>
        <td class="col-total">${fmtFormingNumber(r.total)}</td>
        ${buildDayCells(r.byDate, dates)}
      </tr>`
    }
  }

  const grandTotal = tableRows.reduce((s, r) => s + r.total, 0)
  const dailyTotals = sumByDate(tableRows, dates)
  const footDayCells = buildDayCells(dailyTotals, dates)
  const printedAt = opts.printedAt || formatDateTimeJST(new Date(), 'ja-JP')
  const groupHint = hasRealMachine
    ? `　／　${escHtml(L.machineGroupCount)}：${machineKeys.filter((k) => k !== UNSET_MACHINE_LABEL).length}`
    : ''

  const dateHeaders = dates.map((d) => `<th>${escHtml(d.slice(5))}</th>`).join('')

  return `
    <div class="print-hd">
      <h1 class="print-title">${escHtml(processLabel)} — ${escHtml(L.titleSuffix)}</h1>
      <div class="print-meta">
        <div>${escHtml(L.period)}：${escHtml(periodStart)} ～ ${escHtml(periodEnd)}</div>
        <div>${escHtml(L.printedAt)}：${escHtml(printedAt)}</div>
      </div>
    </div>
    <div class="print-summary">${escHtml(L.processTotal)}：${fmtFormingNumber(grandTotal, false)}　／　${escHtml(L.productCount)}：${tableRows.length}${groupHint}</div>
    <table>
      <thead>
        <tr>
          <th>${escHtml(L.colProductName)}</th>
          <th>${escHtml(L.colPeriodTotal)}</th>
          ${dateHeaders}
        </tr>
      </thead>
      <tbody>${bodyRows}</tbody>
      <tfoot>
        <tr>
          <td>${escHtml(L.grandTotal)}</td>
          <td class="col-total">${fmtFormingNumber(grandTotal, false)}</td>
          ${footDayCells}
        </tr>
      </tfoot>
    </table>
  `
}

export function openProcessPlanPrintDocument(html: string, docTitle: string) {
  const win = window.open('', '_blank')
  if (!win) {
    throw new Error('POPUP_BLOCKED')
  }
  win.document.write(`<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8" /><title>${escHtml(docTitle)}</title><style>${PRINT_STYLES}</style></head>
<body>${html}</body></html>`)
  win.document.close()
  win.onload = () => {
    win.print()
    setTimeout(() => win.close(), 400)
  }
}

export function printProcessPlanDetail(opts: ProcessPlanPrintOptions) {
  const L = { ...PRINT_LABELS_JA, ...opts.labels }
  const html = buildProcessPlanPrintHtml(opts)
  openProcessPlanPrintDocument(html, L.docTitle)
}

export function printOrderProcessDetail(
  opts: Omit<ProcessPlanPrintOptions, 'matrixRows'> & { matrixRows: OrderMatrixRow[] },
) {
  const L = {
    ...PRINT_LABELS_JA,
    titleSuffix: PRINT_LABELS_JA.orderTitleSuffix,
    processTotal: PRINT_LABELS_JA.orderProcessTotal,
    docTitle: PRINT_LABELS_JA.orderDocTitle,
    ...opts.labels,
  }
  const html = buildOrderProcessPrintHtml({ ...opts, labels: L })
  openProcessPlanPrintDocument(html, L.docTitle)
}
