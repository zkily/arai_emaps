<template>
  <div class="history-panel">
    <el-table
      v-if="view === 'list'"
      :key="`list-${kind}`"
      v-loading="loading"
      :data="rows"
      border
      stripe
      show-summary
      :summary-method="listSummary"
      height="calc(100vh - 300px)"
      size="small"
    >
      <el-table-column
        prop="order_date"
        :label="kind === 'order' ? '注文日' : '受入日'"
        width="136"
        align="center"
        fixed="left"
      >
        <template #default="{ row }">
          <span class="date-cell" :class="dayClass(row.order_date)">
            {{ row.order_date }}<small>({{ weekdayLabel(row.order_date) }})</small>
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="supplier_name" label="外注先" width="160" show-overflow-tooltip />
      <el-table-column prop="product_cd" label="製品CD" width="86" align="center" class-name="col-code" />
      <el-table-column prop="product_name" label="製品名" min-width="180" show-overflow-tooltip />
      <template v-if="kind === 'order'">
        <el-table-column prop="order_qty" label="注文数" width="100" align="right" class-name="col-order">
          <template #default="{ row }"><span class="qty qty--order">{{ formatNum(row.order_qty) }}</span></template>
        </el-table-column>
        <el-table-column prop="unit_price" label="単価" width="80" align="right" class-name="col-order">
          <template #default="{ row }"><span class="num-muted">{{ formatNum(row.unit_price) }}</span></template>
        </el-table-column>
        <el-table-column prop="order_amount" label="金額" width="116" align="right" class-name="col-order">
          <template #default="{ row }"><span class="num-strong">{{ formatNum(row.order_amount) }}</span></template>
        </el-table-column>
        <el-table-column prop="delivery_date" label="納期" width="104" align="center" class-name="col-order" />
        <el-table-column label="注文番号" width="176" align="center" class-name="col-order">
          <template #default="{ row }">
            <span v-if="row.order_no" class="no-chip no-chip--order">{{ row.order_no }}</span>
          </template>
        </el-table-column>
      </template>
      <template v-else>
        <el-table-column prop="receiving_qty" label="受入数" width="100" align="right" class-name="col-recv">
          <template #default="{ row }"><span class="qty qty--recv">{{ blankIfZero(row.receiving_qty) }}</span></template>
        </el-table-column>
        <el-table-column label="受入番号" width="186" align="center" class-name="col-recv">
          <template #default="{ row }">
            <span v-if="row.receiving_no" class="no-chip no-chip--recv">{{ row.receiving_no }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="defect_qty" label="不良数" width="100" align="right" class-name="col-defect">
          <template #default="{ row }"><span class="qty qty--defect">{{ blankIfZero(row.defect_qty) }}</span></template>
        </el-table-column>
        <el-table-column label="不良番号" width="186" align="center" class-name="col-defect">
          <template #default="{ row }">
            <span v-if="row.disposal_no" class="no-chip no-chip--defect">{{ row.disposal_no }}</span>
          </template>
        </el-table-column>
      </template>
      <template #empty>
        <span>{{ emptyText }}</span>
      </template>
    </el-table>

    <el-table
      v-else
      :key="`pivot-${kind}-${dates.length}`"
      v-loading="loading"
      :data="pivotRows"
      border
      show-summary
      :summary-method="pivotSummary"
      height="calc(100vh - 324px)"
      size="small"
      class="pivot-table"
      :class="`pivot-table--${kind}`"
      :header-cell-class-name="pivotHeaderClass"
      :cell-class-name="pivotCellClass"
      :cell-style="pivotCellStyle"
    >
      <el-table-column prop="supplier_name" label="外注先" width="160" fixed="left" show-overflow-tooltip />
      <el-table-column prop="product_cd" label="製品CD" width="86" fixed="left" align="center" class-name="col-code" />
      <el-table-column prop="product_name" label="製品名" width="160" fixed="left" show-overflow-tooltip />
      <el-table-column
        v-for="d in dates"
        :key="d"
        :prop="d"
        :column-key="d"
        :width="kind === 'order' ? 72 : 100"
        align="right"
      >
        <template #header>
          <div class="day-head">
            <span>{{ dayLabel(d) }}</span>
            <span class="day-head__wd">{{ weekdayLabel(d) }}</span>
          </div>
        </template>
        <template #default="{ row }">
          <template v-if="row.cells[d]">
            <span v-if="row.cells[d].qty">{{ formatNum(row.cells[d].qty) }}</span>
            <span v-if="row.cells[d].defect" class="defect-num defect-num--sub">
              ({{ formatNum(row.cells[d].defect) }})
            </span>
          </template>
        </template>
      </el-table-column>
      <el-table-column
        label="合計"
        :width="kind === 'order' ? 100 : 128"
        align="right"
        fixed="right"
        column-key="__total"
        :class-name="kind === 'order' ? 'col-order' : 'col-recv'"
      >
        <template #default="{ row }">
          <span class="total-num">{{ formatNum(row.total) }}</span>
          <span v-if="row.defectTotal" class="defect-num defect-num--sub">
            ({{ formatNum(row.defectTotal) }})
          </span>
        </template>
      </el-table-column>
      <template #empty>
        <span>{{ emptyText }}</span>
      </template>
    </el-table>
    <div v-if="view === 'pivot'" class="pivot-note">
      <span class="pivot-note__legend" :class="`pivot-note__legend--${kind}`">
        <i /><i /><i /><i />
      </span>
      <span>色が濃いほど数量が多い</span>
      <span v-if="kind === 'receiving'" class="pivot-note__sep">
        セルは受入数、<em class="defect-num">( )</em> 内は不良数
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { TableColumnCtx } from 'element-plus'
import { type PlatingLedgerRow } from '@/api/outsourcing'
import { useLedger } from './ledgerContext'
import { notifyLedgerError } from './ledgerError'

const ledger = useLedger()

const props = defineProps<{
  kind: 'order' | 'receiving'
  view: 'list' | 'pivot'
  startDate: string
  endDate: string
  supplierCd?: string
  productCd?: string
}>()

const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土']
// 期間がこれ以下なら全日付を列にし、超える場合はデータのある日だけを列にする
const MAX_FULL_DAYS = 62

interface PivotCell {
  qty: number
  defect: number
}

interface PivotRow {
  key: string
  supplier_name: string
  product_cd: string
  product_name: string
  cells: Record<string, PivotCell>
  total: number
  defectTotal: number
}

const rows = ref<PlatingLedgerRow[]>([])
const loading = ref(false)
let loadSeq = 0

const emptyText = computed(() =>
  props.kind === 'order' ? '指定期間の注文はありません' : '指定期間の受入・不良はありません',
)

function formatNum(value: number | null | undefined): string {
  return Number(value || 0).toLocaleString()
}

function blankIfZero(value: number | null | undefined): string {
  return value ? formatNum(value) : ''
}

function parseYmd(ymd: string): Date {
  const [y, m, d] = ymd.split('-').map(Number)
  return new Date(y, m - 1, d)
}

function toYmd(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function dayLabel(ymd: string): string {
  const d = parseYmd(ymd)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function weekdayLabel(ymd: string): string {
  return WEEKDAYS[parseYmd(ymd).getDay()]
}

function cellQty(r: PlatingLedgerRow): number {
  return props.kind === 'order' ? r.order_qty || 0 : r.receiving_qty || 0
}

function cellDefect(r: PlatingLedgerRow): number {
  return props.kind === 'order' ? 0 : r.defect_qty || 0
}

const dates = computed<string[]>(() => {
  if (!props.startDate || !props.endDate) return []
  const start = parseYmd(props.startDate)
  const end = parseYmd(props.endDate)
  const span = Math.round((end.getTime() - start.getTime()) / 86400000) + 1
  if (span > 0 && span <= MAX_FULL_DAYS) {
    const list: string[] = []
    for (let i = 0; i < span; i++) {
      list.push(toYmd(new Date(start.getFullYear(), start.getMonth(), start.getDate() + i)))
    }
    return list
  }
  return [...new Set(rows.value.map((r) => r.order_date))].sort()
})

const pivotRows = computed<PivotRow[]>(() => {
  const map = new Map<string, PivotRow>()
  for (const r of rows.value) {
    const key = `${r.supplier_cd}|${r.product_cd}`
    let pr = map.get(key)
    if (!pr) {
      pr = {
        key,
        supplier_name: r.supplier_name,
        product_cd: r.product_cd,
        product_name: r.product_name,
        cells: {},
        total: 0,
        defectTotal: 0,
      }
      map.set(key, pr)
    }
    const qty = cellQty(r)
    const defect = cellDefect(r)
    const cell = pr.cells[r.order_date] || { qty: 0, defect: 0 }
    cell.qty += qty
    cell.defect += defect
    pr.cells[r.order_date] = cell
    pr.total += qty
    pr.defectTotal += defect
  }
  return [...map.values()].sort(
    (a, b) =>
      a.supplier_name.localeCompare(b.supplier_name, 'ja') ||
      a.product_name.localeCompare(b.product_name, 'ja') ||
      a.product_cd.localeCompare(b.product_cd),
  )
})

function withDefect(qty: number, defect: number): string {
  if (!qty && !defect) return ''
  return defect ? `${formatNum(qty)} (${formatNum(defect)})` : formatNum(qty)
}

function listSummary({ columns }: { columns: TableColumnCtx<PlatingLedgerRow>[] }): string[] {
  const sumKeys = ['order_qty', 'order_amount', 'receiving_qty', 'defect_qty']
  return columns.map((col, i) => {
    if (i === 0) return '合計'
    if (!sumKeys.includes(col.property)) return ''
    const key = col.property as keyof PlatingLedgerRow
    return formatNum(rows.value.reduce((s, r) => s + (Number(r[key]) || 0), 0))
  })
}

function pivotSummary({ columns }: { columns: TableColumnCtx<PivotRow>[] }): string[] {
  return columns.map((col, i) => {
    if (i === 0) return '合計'
    if (col.columnKey === '__total') {
      const qty = pivotRows.value.reduce((s, r) => s + r.total, 0)
      const defect = pivotRows.value.reduce((s, r) => s + r.defectTotal, 0)
      return withDefect(qty, defect)
    }
    const d = col.columnKey
    if (!d || !dates.value.includes(d)) return ''
    let qty = 0
    let defect = 0
    for (const r of pivotRows.value) {
      qty += r.cells[d]?.qty || 0
      defect += r.cells[d]?.defect || 0
    }
    return withDefect(qty, defect)
  })
}

function dayClass(ymd: string | undefined): string {
  if (!ymd) return ''
  const wd = parseYmd(ymd).getDay()
  if (wd === 0) return 'is-sun'
  if (wd === 6) return 'is-sat'
  return ''
}

function weekendClass(ymd: string | undefined): string {
  if (!ymd || !dates.value.includes(ymd)) return ''
  return dayClass(ymd)
}

// ヒートマップ：注文=インディゴ / 受入=エメラルド
const HEAT_RGB = { order: '79, 70, 229', receiving: '16, 185, 129' } as const

const maxCellQty = computed(() => {
  let max = 0
  for (const r of pivotRows.value) {
    for (const c of Object.values(r.cells)) max = Math.max(max, c.qty)
  }
  return max
})

function pivotCellStyle({
  row,
  column,
}: {
  row: PivotRow
  column: TableColumnCtx<PivotRow>
}): Record<string, string> {
  const d = column.columnKey
  if (!d || !dates.value.includes(d)) return {}
  const qty = row.cells[d]?.qty || 0
  if (!qty || !maxCellQty.value) return {}
  const alpha = 0.1 + 0.5 * (qty / maxCellQty.value)
  return {
    background: `rgba(${HEAT_RGB[props.kind]}, ${alpha.toFixed(3)})`,
    color: alpha > 0.42 ? '#fff' : '',
    fontWeight: '700',
  }
}

function pivotHeaderClass({ column }: { column: TableColumnCtx<PivotRow> }): string {
  return weekendClass(column.columnKey)
}

function pivotCellClass({ column }: { column: TableColumnCtx<PivotRow> }): string {
  return weekendClass(column.columnKey)
}

async function load() {
  if (!props.startDate || !props.endDate) return
  const seq = ++loadSeq
  loading.value = true
  try {
    const res = await ledger.getHistory({
      kind: props.kind,
      startDate: props.startDate,
      endDate: props.endDate,
      supplierCd: props.supplierCd || undefined,
      productCd: props.productCd || undefined,
    })
    if (seq !== loadSeq) return
    rows.value = res?.data || []
  } catch (error: any) {
    if (seq !== loadSeq) return
    rows.value = []
    notifyLedgerError(error, '履歴の取得に失敗しました')
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

watch(
  () => [props.kind, props.startDate, props.endDate, props.supplierCd, props.productCd],
  load,
  { immediate: true },
)

defineExpose({ reload: load })
</script>

<style scoped>
.history-panel {
  position: relative;
}

.day-head {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.2;
}

.day-head__wd {
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
}

.pivot-table :deep(th.is-sat),
.pivot-table :deep(th.is-sat .day-head__wd) {
  color: #2563eb !important;
}

.pivot-table :deep(th.is-sun),
.pivot-table :deep(th.is-sun .day-head__wd) {
  color: #dc2626 !important;
}

.pivot-table :deep(td.is-sat) {
  background: #f5f9ff;
}

.pivot-table :deep(td.is-sun) {
  background: #fff6f6;
}

.pivot-table :deep(td.el-table__cell .cell) {
  font-variant-numeric: tabular-nums;
}

.date-cell {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  font-variant-numeric: tabular-nums;
  color: #334155;
}

.date-cell small {
  font-size: 11px;
  color: #94a3b8;
}

.date-cell.is-sat,
.date-cell.is-sat small {
  color: #2563eb;
}

.date-cell.is-sun,
.date-cell.is-sun small {
  color: #dc2626;
}

.qty {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.qty--order {
  color: #3730a3;
}

.qty--recv {
  color: #047857;
}

.qty--defect {
  color: #be123c;
}

.num-muted {
  color: #64748b;
  font-variant-numeric: tabular-nums;
}

.num-strong {
  font-weight: 700;
  color: #3730a3;
  font-variant-numeric: tabular-nums;
}

.no-chip {
  display: inline-block;
  max-width: 100%;
  padding: 1px 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
  border-radius: 6px;
  font-family: ui-monospace, 'SFMono-Regular', Consolas, monospace;
  font-size: 11.5px;
  font-weight: 600;
}

.no-chip--order {
  color: #3730a3;
  background: #e0e7ff;
  border: 1px solid #c7d2fe;
}

.no-chip--recv {
  color: #047857;
  background: #d1fae5;
  border: 1px solid #a7f3d0;
}

.no-chip--defect {
  color: #be123c;
  background: #ffe4e6;
  border: 1px solid #fecdd3;
}

.total-num {
  font-weight: 800;
}

.pivot-table--order .total-num {
  color: #3730a3;
}

.pivot-table--receiving .total-num {
  color: #047857;
}

.defect-num {
  color: #dc2626;
  font-style: normal;
}

.defect-num--sub {
  margin-left: 2px;
  padding: 0 3px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.9);
}

.pivot-note {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
}

.pivot-note__legend {
  display: inline-flex;
  gap: 2px;
}

.pivot-note__legend i {
  width: 14px;
  height: 10px;
  border-radius: 3px;
}

.pivot-note__legend--order i:nth-child(1) { background: rgba(79, 70, 229, 0.12); }
.pivot-note__legend--order i:nth-child(2) { background: rgba(79, 70, 229, 0.28); }
.pivot-note__legend--order i:nth-child(3) { background: rgba(79, 70, 229, 0.44); }
.pivot-note__legend--order i:nth-child(4) { background: rgba(79, 70, 229, 0.6); }
.pivot-note__legend--receiving i:nth-child(1) { background: rgba(16, 185, 129, 0.12); }
.pivot-note__legend--receiving i:nth-child(2) { background: rgba(16, 185, 129, 0.28); }
.pivot-note__legend--receiving i:nth-child(3) { background: rgba(16, 185, 129, 0.44); }
.pivot-note__legend--receiving i:nth-child(4) { background: rgba(16, 185, 129, 0.6); }

.pivot-note__sep {
  padding-left: 8px;
  border-left: 1px solid #e2e8f0;
}
</style>
