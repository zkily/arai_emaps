<template>
  <div class="matrix-print" :class="`matrix-print--${kind}`">
    <span class="matrix-print__label">
      <el-icon><Grid /></el-icon>外注先別
    </span>
    <el-date-picker
      v-model="printRange"
      type="daterange"
      value-format="YYYY-MM-DD"
      format="YYYY/MM/DD"
      range-separator="〜"
      start-placeholder="開始日"
      end-placeholder="終了日"
      :clearable="false"
      size="small"
      class="matrix-print__date"
    />
    <el-select
      v-model="supplierCd"
      placeholder="すべての外注先"
      clearable
      filterable
      size="small"
      class="matrix-print__supplier"
    >
      <el-option
        v-for="s in supplierOptions"
        :key="s.value"
        :label="s.label"
        :value="s.value"
      />
    </el-select>
    <el-button
      size="small"
      class="matrix-print__btn"
      :loading="printing"
      @click="printMatrix"
    >
      <el-icon><Printer /></el-icon>二次元表印刷
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Grid, Printer } from '@element-plus/icons-vue'
import { type PlatingLedgerRow } from '@/api/outsourcing'
import { recordPrintHistory } from '@/api/shipping/printHistory'
import { usePurchaseOperationPermission } from '@/composables/usePurchaseOperationPermission'
import { guardPurchaseOperation } from '@/utils/purchaseOperationGuard'
import { useLedger } from './ledgerContext'
import { notifyLedgerError } from './ledgerError'

const ledger = useLedger()

const props = defineProps<{
  kind: 'order' | 'receiving'
  /** 台帳の表示期間と双方向で連動（v-model:range） */
  range?: [string, string]
  defaultSupplierCd?: string
  supplierOptions: { value: string; label: string }[]
}>()

const emit = defineEmits<{
  'update:range': [range: [string, string]]
}>()

const MAX_FULL_DAYS = 62
const MAX_SPAN_DAYS = 366
const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土']

interface Cell {
  qty: number
  defect: number
}

interface ProductRow {
  product_cd: string
  product_name: string
  cells: Record<string, Cell>
  total: number
  defectTotal: number
}

interface SupplierBlock {
  supplier_cd: string
  supplier_name: string
  products: ProductRow[]
}

const { canExport } = usePurchaseOperationPermission()

const localRange = ref<string[]>([])
const printRange = computed<string[]>({
  get: () => (props.range?.length === 2 ? props.range : localRange.value),
  set: (v) => {
    localRange.value = v || []
    if (v?.length === 2 && v[0] && v[1]) emit('update:range', [v[0], v[1]])
  },
})

const supplierCd = ref(props.defaultSupplierCd || '')
const printing = ref(false)

watch(
  () => props.defaultSupplierCd,
  (v) => {
    supplierCd.value = v || ''
  },
)

const kindLabel = computed(() => (props.kind === 'order' ? '注文' : '受入'))

function parseYmd(ymd: string): Date {
  const [y, m, d] = ymd.split('-').map(Number)
  return new Date(y, m - 1, d)
}

function toYmd(d: Date): string {
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

function formatSlash(ymd: string): string {
  return ymd.replace(/-/g, '/')
}

function weekdayOf(ymd: string): number {
  return parseYmd(ymd).getDay()
}

function dayHead(ymd: string): string {
  const d = parseYmd(ymd)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function esc(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function fmt(n: number): string {
  return n.toLocaleString('ja-JP')
}

function spanDays(start: string, end: string): number {
  return Math.round((parseYmd(end).getTime() - parseYmd(start).getTime()) / 86400000)
}

function buildDates(start: string, end: string, rows: PlatingLedgerRow[]): string[] {
  const span = spanDays(start, end) + 1
  if (span > 0 && span <= MAX_FULL_DAYS) {
    const list: string[] = []
    const cursor = parseYmd(start)
    for (let i = 0; i < span; i++) {
      list.push(toYmd(new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() + i)))
    }
    return list
  }
  return [...new Set(rows.map((r) => r.order_date).filter(Boolean))].sort()
}

function cellQty(row: PlatingLedgerRow): number {
  return props.kind === 'order' ? Number(row.order_qty) || 0 : Number(row.receiving_qty) || 0
}

function cellDefect(row: PlatingLedgerRow): number {
  return props.kind === 'order' ? 0 : Number(row.defect_qty) || 0
}

function buildBlocks(rows: PlatingLedgerRow[]): SupplierBlock[] {
  const suppliers = new Map<string, SupplierBlock>()
  for (const row of rows) {
    const cd = row.supplier_cd || ''
    let block = suppliers.get(cd)
    if (!block) {
      block = {
        supplier_cd: cd,
        supplier_name: row.supplier_name || cd || '（未設定）',
        products: [],
      }
      suppliers.set(cd, block)
    }
    let product = block.products.find((p) => p.product_cd === row.product_cd)
    if (!product) {
      product = {
        product_cd: row.product_cd,
        product_name: row.product_name || row.product_cd,
        cells: {},
        total: 0,
        defectTotal: 0,
      }
      block.products.push(product)
    }
    const date = row.order_date
    const cell = product.cells[date] || { qty: 0, defect: 0 }
    const qty = cellQty(row)
    const defect = cellDefect(row)
    cell.qty += qty
    cell.defect += defect
    product.cells[date] = cell
    product.total += qty
    product.defectTotal += defect
  }

  const nameCmp = (a: string, b: string) =>
    a.localeCompare(b, 'ja-JP', { numeric: true, sensitivity: 'base' })

  return [...suppliers.values()]
    .map((block) => ({
      ...block,
      products: [...block.products].sort(
        (a, b) => nameCmp(a.product_name, b.product_name) || nameCmp(a.product_cd, b.product_cd),
      ),
    }))
    .sort((a, b) => nameCmp(a.supplier_name, b.supplier_name) || nameCmp(a.supplier_cd, b.supplier_cd))
}

function dayClass(ymd: string): string {
  const wd = weekdayOf(ymd)
  if (wd === 0) return 'is-sun'
  if (wd === 6) return 'is-sat'
  return ''
}

function cellHtml(cell: Cell | undefined, ymd: string): string {
  const qty = cell?.qty || 0
  const defect = cell?.defect || 0
  const qtyText = qty ? fmt(qty) : ''
  const defectText = defect ? `<span class="def">(${fmt(defect)})</span>` : ''
  return `<td class="q ${dayClass(ymd)}">${qtyText}${defectText}</td>`
}

function totalHtml(qty: number, defect: number, extraClass = ''): string {
  const defectText = defect ? `<span class="def">(${fmt(defect)})</span>` : ''
  const cls = ['sum', extraClass].filter(Boolean).join(' ')
  return `<td class="${cls}">${qty ? fmt(qty) : ''}${defectText}</td>`
}

function printedAtLabel(): string {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}/${p(d.getMonth() + 1)}/${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

function dayOfMonth(ymd: string): number {
  return parseYmd(ymd).getDate()
}

function monthLabel(ym: string): string {
  const [y, m] = ym.split('-').map(Number)
  return `${y}年${m}月`
}

function lastDayOfMonth(ym: string): number {
  const [y, m] = ym.split('-').map(Number)
  return new Date(y, m, 0).getDate()
}

/** 期間に含まれる YYYY-MM を昇順で返す */
function monthsInRange(start: string, end: string): string[] {
  const list: string[] = []
  const cursor = parseYmd(start)
  cursor.setDate(1)
  const endMonth = parseYmd(end)
  endMonth.setDate(1)
  while (cursor <= endMonth) {
    list.push(`${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, '0')}`)
    cursor.setMonth(cursor.getMonth() + 1)
  }
  return list
}

/**
 * 注文・受入印刷用：月ごとに必ず 1〜15 / 16〜末日 の2段に分ける。
 * 列は期間内に含まれる日だけ（その半月に日が無ければ表自体を出さない）。
 */
function buildMonthHalves(
  start: string,
  end: string,
): { ym: string; early: string[]; late: string[] }[] {
  return monthsInRange(start, end).map((ym) => {
    const last = lastDayOfMonth(ym)
    const early: string[] = []
    const late: string[] = []
    for (let day = 1; day <= last; day++) {
      const ymd = `${ym}-${String(day).padStart(2, '0')}`
      if (ymd < start || ymd > end) continue
      if (day <= 15) early.push(ymd)
      else late.push(ymd)
    }
    return { ym, early, late }
  })
}

function productRangeTotal(product: ProductRow, dates: string[]): { qty: number; defect: number } {
  let qty = 0
  let defect = 0
  for (const d of dates) {
    const cell = product.cells[d]
    if (!cell) continue
    qty += cell.qty
    defect += cell.defect
  }
  return { qty, defect }
}

function renderMatrixTable(
  products: ProductRow[],
  dates: string[],
  opts: {
    caption?: string
    sumLabel?: string
    tall?: boolean
    half?: 'early' | 'late'
  },
): string {
  if (!dates.length) return ''
  const colQty = new Map<string, number>()
  const colDefect = new Map<string, number>()
  for (const d of dates) {
    colQty.set(d, 0)
    colDefect.set(d, 0)
  }
  let grandQty = 0
  let grandDefect = 0
  const headDates = dates
    .map((d) => `<th class="day ${dayClass(d)}">${dayHead(d)}<small>${WEEKDAYS[weekdayOf(d)]}</small></th>`)
    .join('')
  const body = products
    .map((product, i) => {
      const range = productRangeTotal(product, dates)
      grandQty += range.qty
      grandDefect += range.defect
      const days = dates
        .map((d) => {
          const cell = product.cells[d]
          colQty.set(d, (colQty.get(d) || 0) + (cell?.qty || 0))
          colDefect.set(d, (colDefect.get(d) || 0) + (cell?.defect || 0))
          return cellHtml(cell, d)
        })
        .join('')
      const alt = i % 2 === 1 ? ' class="alt"' : ''
      return `<tr${alt}><td class="cd">${esc(product.product_cd)}</td><td class="name">${esc(product.product_name)}</td>${days}${totalHtml(range.qty, range.defect)}</tr>`
    })
    .join('')
  const footDays = dates
    .map((d) => totalHtml(colQty.get(d) || 0, colDefect.get(d) || 0, dayClass(d)))
    .join('')
  const sumLabel = opts.sumLabel || '合計'
  const halfCls = opts.half ? ` table-block--${opts.half}` : ''
  const captionHtml = opts.caption
    ? `<div class="table-caption${opts.half ? ` table-caption--${opts.half}` : ''}">${esc(opts.caption)}</div>`
    : ''
  return `
    <div class="table-block${halfCls}">
      ${captionHtml}
      <table class="matrix-table${opts.tall ? ' is-tall' : ''}">
        <thead>
          <tr>
            <th class="cd">製品CD</th>
            <th class="name">製品名</th>
            ${headDates}
            <th class="sum">${esc(sumLabel)}</th>
          </tr>
        </thead>
        <tbody>${body}</tbody>
        <tfoot>
          <tr>
            <td class="label" colspan="2">${esc(sumLabel)}（${products.length} 製品）</td>
            ${footDays}
            ${totalHtml(grandQty, grandDefect)}
          </tr>
        </tfoot>
      </table>
    </div>`
}

function buildSupplierTables(block: SupplierBlock, dates: string[], start: string, end: string): string {
  // 注文・受入とも：月ごとに上段(1〜15)・下段(16〜末日)の2表
  const halves = buildMonthHalves(start, end)
  const multiMonth = halves.length > 1
  const parts: string[] = []
  for (const { ym, early, late } of halves) {
    const prefix = multiMonth ? `${monthLabel(ym)}　` : ''
    if (early.length) {
      parts.push(
        renderMatrixTable(block.products, early, {
          caption: `【上段】${prefix}1〜15日`,
          sumLabel: '小計',
          tall: true,
          half: 'early',
        }),
      )
    }
    if (late.length) {
      const lateEnd = dayOfMonth(late[late.length - 1])
      parts.push(
        renderMatrixTable(block.products, late, {
          caption: `【下段】${prefix}16〜${lateEnd}日`,
          sumLabel: '小計',
          tall: true,
          half: 'late',
        }),
      )
    }
  }
  return (
    parts.join('') ||
    renderMatrixTable(block.products, dates, {
      caption: '期間',
      sumLabel: '合計',
      tall: true,
      half: 'early',
    })
  )
}

function buildHtml(rows: PlatingLedgerRow[], start: string, end: string): string {
  const dates = buildDates(start, end, rows)
  const blocks = buildBlocks(rows)
  const dataDaysOnly = spanDays(start, end) + 1 > MAX_FULL_DAYS
  const title = `${ledger.title}　${kindLabel.value}　外注先別二次元表`
  const period = `${formatSlash(start)} 〜 ${formatSlash(end)}`
  const note =
    props.kind === 'receiving'
      ? 'セルの数値は受入数、（ ）内は不良数。外注先ごとに上段（1〜15日）と下段（16〜末日）の2表。土曜は青、日曜は赤。'
      : 'セルの数値は注文数。外注先ごとに上段（1〜15日）と下段（16〜末日）の2表。土曜は青、日曜は赤。'
  const omitNote = dataDaysOnly ? '期間が62日を超えるため、データのある日だけを表示しています。' : ''
  const printedAt = printedAtLabel()

  return blocks
    .map((block, index) => {
      return `
        <section class="sheet sheet-split${index === blocks.length - 1 ? ' is-last' : ''}${props.kind === 'receiving' ? ' sheet-receiving' : ' sheet-order'}">
          <header class="head">
            <div>
              <div class="title">${esc(title)}</div>
              <div class="meta">期間　${esc(period)}　／　外注先　${esc(block.supplier_name)}${block.supplier_cd ? `（${esc(block.supplier_cd)}）` : ''}</div>
            </div>
            <div class="issued">印刷　${esc(printedAt)}<br>${index + 1} / ${blocks.length} 外注先</div>
          </header>
          ${buildSupplierTables(block, dates, start, end)}
          <footer class="foot">${esc(note)}${omitNote ? ` ${esc(omitNote)}` : ''}</footer>
        </section>`
    })
    .join('')
}

const PRINT_STYLE = `
@page { size: A3 landscape; margin: 8mm; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fff; }
body {
  font-family: 'Yu Gothic', 'Yu Gothic UI', 'Meiryo', sans-serif;
  color: #0f172a;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.sheet { break-after: page; page-break-after: always; }
.sheet.is-last { break-after: auto; page-break-after: auto; }
.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 8mm;
  margin-bottom: 3mm;
  padding-bottom: 2mm;
  border-bottom: 0.6mm solid #1e3a8a;
}
.title { font-size: 16pt; font-weight: 800; letter-spacing: 0.04em; }
.meta { margin-top: 1mm; font-size: 10pt; font-weight: 700; }
.issued { font-size: 8.5pt; line-height: 1.45; text-align: right; color: #334155; }
.table-block { margin-bottom: 5mm; }
.table-block:last-of-type { margin-bottom: 0; }
.table-block--late {
  margin-top: 5mm;
  padding-top: 4mm;
  border-top: 0.5mm dashed #1d4ed8;
}
.sheet-receiving .table-block--late { border-top-color: #0f766e; }
.table-caption {
  display: inline-block;
  margin: 0 0 1.8mm;
  padding: 1mm 3mm;
  font-size: 10pt;
  font-weight: 800;
  color: #fff;
  border-radius: 1.2mm;
  background: #2563eb;
}
.table-caption--early { background: #2563eb; }
.table-caption--late { background: #1d4ed8; }
.sheet-receiving .table-caption--early { background: #0d9488; }
.sheet-receiving .table-caption--late { background: #0e7490; }
table { width: 100%; border-collapse: collapse; table-layout: fixed; }
th, td {
  border: 0.2mm solid #94a3b8;
  padding: 0.6mm 0.4mm;
  font-size: 7.5pt;
  line-height: 1.2;
  vertical-align: middle;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
table.is-tall thead th { height: 9mm; padding: 1.2mm 0.6mm; font-size: 8.5pt; }
table.is-tall thead th small { font-size: 7pt; margin-top: 0.3mm; }
table.is-tall tbody td,
table.is-tall tfoot td {
  height: 8.5mm;
  padding: 1.4mm 0.8mm;
  font-size: 9pt;
  line-height: 1.35;
}
table.is-tall .def { font-size: 8pt; }
thead th {
  font-weight: 700;
  text-align: center;
  color: #1e3a8a;
  background: #dbeafe;
}
thead th small { display: block; font-size: 6pt; font-weight: 600; }
th.day, td.q, td.sum { text-align: center; font-variant-numeric: tabular-nums; }
th.cd, td.cd { width: 18mm; text-align: center; }
th.name, td.name { width: 48mm; text-align: left; font-weight: 700; }
th.sum, td.sum { width: 18mm; font-weight: 800; background: #eff6ff; }
tbody tr.alt td { background: #f8fafc; }
tbody tr.alt td.sum { background: #e0e7ff; }
.def { margin-left: 0.4mm; font-size: 6.5pt; font-weight: 700; color: #be123c; }
tfoot td { font-weight: 800; background: #e2e8f0; }
tfoot td.label { text-align: right; padding-right: 2mm; }
.foot { margin-top: 2mm; font-size: 8pt; color: #475569; }
.sheet-split .foot { margin-top: 2.5mm; }
.kind-receiving .head { border-bottom-color: #0f766e; }
.kind-receiving .title { color: #115e59; }
.kind-receiving thead th { color: #115e59; background: #ccfbf1; }
.kind-receiving th.sum, .kind-receiving td.sum { background: #ecfdf5; }
.kind-receiving tbody tr.alt td.sum { background: #d1fae5; }
th.is-sat, td.is-sat, td.sum.is-sat,
tbody tr.alt td.is-sat, tbody tr.alt td.sum.is-sat,
.kind-receiving thead th.is-sat, .kind-receiving td.sum.is-sat,
.kind-receiving tbody tr.alt td.sum.is-sat {
  color: #1d4ed8;
  background: #dbeafe;
}
th.is-sun, td.is-sun, td.sum.is-sun,
tbody tr.alt td.is-sun, tbody tr.alt td.sum.is-sun,
.kind-receiving thead th.is-sun, .kind-receiving td.sum.is-sun,
.kind-receiving tbody tr.alt td.sum.is-sun {
  color: #be123c;
  background: #ffe4e6;
}
`

async function printMatrix() {
  if (!guardPurchaseOperation(canExport)) return
  const [start, end] = printRange.value || []
  if (!start || !end) {
    ElMessage.warning('期間を指定してください')
    return
  }
  if (start > end) {
    ElMessage.warning('終了日は開始日以降を指定してください')
    return
  }
  if (spanDays(start, end) > MAX_SPAN_DAYS) {
    ElMessage.warning('期間は366日以内にしてください')
    return
  }

  printing.value = true
  try {
    const res = await ledger.getHistory({
      kind: props.kind,
      startDate: start,
      endDate: end,
      supplierCd: supplierCd.value || undefined,
    })
    const rows = res?.data || []
    if (rows.length === 0) {
      ElMessage.warning(
        props.kind === 'order'
          ? '指定した期間の注文はありません'
          : '指定した期間の受入・不良はありません',
      )
      return
    }

    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('印刷ウィンドウを開けませんでした。ポップアップを許可してください')
      return
    }
    const kindClass = props.kind === 'receiving' ? 'kind-receiving' : 'kind-order'
    printWindow.document.write(`<!DOCTYPE html><html class="${kindClass}"><head><meta charset="UTF-8"><title>${esc(ledger.title)} ${kindLabel.value} 外注先別二次元表</title><style>${PRINT_STYLE}</style></head><body class="${kindClass}">${buildHtml(rows, start, end)}</body></html>`)
    printWindow.document.close()
    printWindow.onload = () => {
      printWindow.focus()
      printWindow.print()
    }

    const supplierName =
      props.supplierOptions.find((s) => s.value === supplierCd.value)?.label || supplierCd.value
    try {
      await recordPrintHistory({
        report_type: `${ledger.process}_${props.kind}_matrix`,
        report_title: `${ledger.title} ${kindLabel.value} 外注先別二次元表`,
        filters: {
          startDate: start,
          endDate: end,
          supplierCd: supplierCd.value || '',
          supplierName: supplierName || 'すべて',
        },
        record_count: rows.length,
        status: '成功',
      })
    } catch (err) {
      console.error('印刷履歴の保存に失敗しました:', err)
    }
  } catch (error: any) {
    notifyLedgerError(error, '二次元表の取得に失敗しました')
  } finally {
    printing.value = false
  }
}
</script>

<style scoped>
.matrix-print {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.matrix-print__label {
  flex-shrink: 0;
  height: 22px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.matrix-print--order .matrix-print__label {
  color: #1d4ed8;
  background: #eff6ff;
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -1px 0 #bfdbfe;
}

.matrix-print--receiving .matrix-print__label {
  color: #0e7490;
  background: #ecfeff;
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -1px 0 #a5f3fc;
}

.matrix-print__date {
  width: 228px !important;
  flex: 0 0 228px;
}

.matrix-print__supplier {
  width: 160px;
}

.matrix-print :deep(.el-input__wrapper),
.matrix-print :deep(.el-select__wrapper) {
  border-radius: 8px;
  background-color: #fff;
}

.matrix-print--order :deep(.el-input__wrapper),
.matrix-print--order :deep(.el-select__wrapper) {
  box-shadow: 0 0 0 1px #bfdbfe inset;
}

.matrix-print--receiving :deep(.el-input__wrapper),
.matrix-print--receiving :deep(.el-select__wrapper) {
  box-shadow: 0 0 0 1px #a5f3fc inset;
}

.matrix-print__btn {
  height: 26px;
  padding: 0 12px;
  border-radius: 8px;
  font-weight: 700;
  color: #fff;
}

.matrix-print--order .matrix-print__btn {
  border: 1px solid #1d4ed8;
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}

.matrix-print--receiving .matrix-print__btn {
  border: 1px solid #0e7490;
  background: linear-gradient(135deg, #22d3ee, #0891b2);
}
</style>
