<template>
  <div class="wit-matrix-wrap">
    <el-table
      :data="rows"
      border
      size="small"
      height="100%"
      class="wit-matrix"
      :row-class-name="rowClassName"
      :cell-class-name="cellClassName"
      :header-cell-class-name="headerCellClassName"
      @row-click="onRowClick"
    >
      <el-table-column label="製品名 / 指標" min-width="230" fixed="left" prop="label">
        <template #default="{ row }">
          <div class="wit-label" :style="{ paddingLeft: `${row.depth * 14}px` }">
            <button
              v-if="row.expandable"
              type="button"
              class="wit-expand"
              :class="{ 'is-open': expanded.has(row.productCd) }"
              @click.stop="emit('toggle', row.productCd)"
            >
              {{ expanded.has(row.productCd) ? '▾' : '▸' }}
            </button>
            <span v-else class="wit-dot" :class="dotClass(row)" />
            <div class="wit-label__text">
              <span class="wit-label__main" :class="labelToneClass(row)">{{ row.label }}</span>
              <span v-if="row.sub" class="wit-label__sub">{{ row.sub }}</span>
            </div>
            <span v-if="row.shortage" class="wit-flag">不足</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column
        v-for="d in dates"
        :key="d"
        :prop="d"
        :label="dayLabel(d)"
        width="78"
        min-width="78"
        align="right"
        class-name="wit-qty-col"
      >
        <template #default="{ row }">
          <span v-if="row.dash" class="is-empty">—</span>
          <span v-else-if="!showOnDay(row, d)" />
          <span v-else class="wit-qty" :class="qtyClass(row, d)">{{ formatQty(cellQty(row, d)) }}</span>
        </template>
      </el-table-column>
      <el-table-column
        label="合計 / 期末"
        width="108"
        min-width="108"
        align="right"
        fixed="right"
        prop="summary"
        class-name="wit-summary-col"
        label-class-name="wit-summary-col"
      >
        <template #default="{ row }">
          <span v-if="row.dash" class="is-empty">—</span>
          <span v-else class="wit-qty" :class="summaryClass(row)">{{ formatQty(row.summaryValue) }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
export interface TrendMatrixRow {
  rowKey: string
  productCd: string
  kind: 'summary' | 'metric' | 'part-stock' | 'part-usage'
  metricKey?: string
  label: string
  sub?: string
  depth: number
  expandable: boolean
  dash: boolean
  shortage: boolean
  daily: Record<string, number>
  compareDaily?: Record<string, number>
  summaryValue: number
  chartable: boolean
}

defineProps<{
  dates: string[]
  rows: TrendMatrixRow[]
  expanded: Set<string>
}>()

const emit = defineEmits<{
  (e: 'toggle', productCd: string): void
}>()

const METRIC_TONE: Record<string, string> = {
  forecast: 'tone-blue',
  molding_actual_plan: 'tone-emerald',
  pre_welding_inventory: 'tone-amber',
  welding_plan: 'tone-indigo',
  welding_actual: 'tone-violet',
  welding_inventory: 'tone-cyan',
  welding_trend: 'tone-teal',
  warehouse_inventory: 'tone-slate',
}

/** 土日列に表示する指標のみ */
const WEEKEND_VISIBLE_METRICS = new Set([
  'molding_actual_plan',
  'welding_plan',
  'welding_actual',
])

function rowTone(row: TrendMatrixRow): string {
  if (row.kind === 'part-stock') return 'tone-amber'
  if (row.kind === 'part-usage') return 'tone-sky'
  if (row.metricKey) return METRIC_TONE[row.metricKey] || 'tone-slate'
  return ''
}

function dotClass(row: TrendMatrixRow): string {
  return rowTone(row)
}

function labelToneClass(row: TrendMatrixRow): string {
  return rowTone(row)
}

function formatQty(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return ''
  if (v === 0) return ''
  return Math.round(v).toLocaleString('ja-JP')
}

function cellQty(row: TrendMatrixRow, d: string): number {
  return row.daily[d] ?? 0
}

function weekdayOf(iso: string): number {
  const [y, m, day] = iso.split('-').map(Number)
  return new Date(y, (m || 1) - 1, day || 1).getDay()
}

function dayLabel(iso: string): string {
  return iso.slice(5).replace('-', '/')
}

function todayIso(): string {
  const n = new Date()
  const y = n.getFullYear()
  const m = String(n.getMonth() + 1).padStart(2, '0')
  const d = String(n.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function isWeekend(iso: string): boolean {
  const wd = weekdayOf(iso)
  return wd === 0 || wd === 6
}

function dayColumnClass(iso: string): string {
  const bits: string[] = []
  if (iso === todayIso()) bits.push('is-today')
  const wd = weekdayOf(iso)
  if (wd === 6) bits.push('is-saturday')
  else if (wd === 0) bits.push('is-sunday')
  return bits.join(' ')
}

/** 土日は成型計画・溶接計画・溶接実績のみ表示 */
function showOnDay(row: TrendMatrixRow, d: string): boolean {
  if (!isWeekend(d)) return true
  return row.kind === 'metric' && !!row.metricKey && WEEKEND_VISIBLE_METRICS.has(row.metricKey)
}

function qtyClass(row: TrendMatrixRow, d: string): string {
  const v = cellQty(row, d)
  if (v < 0) return 'is-neg'
  if (v > 0) return ['is-pos', rowTone(row)].filter(Boolean).join(' ')
  return ''
}

function summaryClass(row: TrendMatrixRow): string {
  if (row.summaryValue < 0) return 'is-neg'
  if (row.summaryValue > 0) return ['is-pos', rowTone(row)].filter(Boolean).join(' ')
  return ''
}

function onRowClick(row: TrendMatrixRow) {
  if (row.expandable) emit('toggle', row.productCd)
}

function rowClassName({ row }: { row: TrendMatrixRow }): string {
  const bits = [`wit-row--${row.kind}`]
  if (row.metricKey) bits.push(`wit-metric--${row.metricKey}`)
  return bits.join(' ')
}

function cellClassName({
  column,
}: {
  column: { property?: string }
}): string {
  const prop = column.property || ''
  if (/^\d{4}-\d{2}-\d{2}$/.test(prop)) return dayColumnClass(prop)
  return ''
}

function headerCellClassName({
  column,
}: {
  column: { property?: string }
}): string {
  const prop = column.property || ''
  if (/^\d{4}-\d{2}-\d{2}$/.test(prop)) return dayColumnClass(prop)
  return ''
}
</script>

<style scoped>
.wit-matrix-wrap {
  flex: 1 1 auto;
  min-height: 0;
  height: 100%;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  background: #ffffff;
}

.wit-matrix {
  --el-table-border-color: #eef2f6;
  --el-table-row-hover-bg-color: #f8fafc;
  font-variant-numeric: tabular-nums;
  -webkit-font-smoothing: antialiased;
  text-rendering: geometricPrecision;
}

.wit-matrix,
.wit-matrix :deep(*) {
  text-shadow: none !important;
  filter: none !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

.wit-label {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  line-height: 1.45;
  min-height: 28px;
}

.wit-expand {
  width: 18px;
  height: 18px;
  flex: 0 0 18px;
  border: 1px solid #e2e8f0;
  border-radius: 5px;
  background: #f8fafc;
  color: #475569;
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.wit-expand.is-open {
  background: #0f766e;
  border-color: #0f766e;
  color: #ffffff;
}

.wit-dot {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  margin: 0 3px;
  border-radius: 999px;
  background: #cbd5e1;
}

.wit-label__text {
  min-width: 0;
  display: flex;
  align-items: baseline;
  gap: 6px;
  overflow: hidden;
}

.wit-label__main {
  font-size: 12px;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wit-label__sub {
  font-size: 10.5px;
  font-weight: 500;
  color: #94a3b8;
  white-space: nowrap;
  flex-shrink: 0;
}

.wit-flag {
  margin-left: auto;
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 600;
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 999px;
  padding: 0 6px;
  line-height: 1.5;
}

.is-empty {
  color: #cbd5e1;
}

/* 数値はすべて太字、-10,000 等も折り返さない */
.wit-qty,
.is-pos,
.is-neg,
.is-empty {
  white-space: nowrap;
  display: inline-block;
  font-weight: 700;
}

.is-pos {
  color: #1e293b;
}

.is-neg {
  color: #dc2626 !important;
}

:deep(.wit-matrix .wit-qty-col .cell),
:deep(.wit-matrix .wit-summary-col .cell) {
  white-space: nowrap !important;
  overflow: visible;
}

/* 指標別トーン（ドット＋ラベル＋数値の控えめな色分け） */
.wit-dot.tone-blue { background: #2563eb; }
.wit-dot.tone-emerald { background: #16a34a; }
.wit-dot.tone-amber { background: #d97706; }
.wit-dot.tone-indigo { background: #4f46e5; }
.wit-dot.tone-violet { background: #7c3aed; }
.wit-dot.tone-cyan { background: #0891b2; }
.wit-dot.tone-teal { background: #0d9488; }
.wit-dot.tone-slate { background: #64748b; }
.wit-dot.tone-sky { background: #0284c7; }

.wit-label__main.tone-blue,
.is-pos.tone-blue { color: #1d4ed8; }
.wit-label__main.tone-emerald,
.is-pos.tone-emerald { color: #15803d; }
.wit-label__main.tone-amber,
.is-pos.tone-amber { color: #b45309; }
.wit-label__main.tone-indigo,
.is-pos.tone-indigo { color: #4338ca; }
.wit-label__main.tone-violet,
.is-pos.tone-violet { color: #6d28d9; }
.wit-label__main.tone-cyan,
.is-pos.tone-cyan { color: #0e7490; }
.wit-label__main.tone-teal,
.is-pos.tone-teal { color: #0f766e; }
.wit-label__main.tone-slate,
.is-pos.tone-slate { color: #334155; }
.wit-label__main.tone-sky,
.is-pos.tone-sky { color: #0369a1; }

/* 表ヘッダー（モダンなスレート調） */
:deep(.wit-matrix .el-table__header th) {
  padding: 8px 4px !important;
  background: #f8fafc !important;
  color: #475569;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.35;
  border-bottom: 1px solid #e2e8f0 !important;
}

:deep(.wit-matrix .el-table__header th.el-table-fixed-column--left) {
  background: #f1f5f9 !important;
  color: #334155;
}

:deep(.wit-matrix .el-table__cell) {
  padding: 8px 6px !important;
}

:deep(.wit-matrix .el-table__body .el-table__cell) {
  height: 36px;
}

:deep(.wit-matrix .cell) {
  padding: 0 4px !important;
  line-height: 1.45;
  font-size: 12px;
}

/* 固定列は不透明背景で横スクロール時の透けを防ぐ */
:deep(.wit-matrix .el-table__body td.el-table-fixed-column--left) {
  background: #ffffff !important;
}

/* 右側固定：合計 / 期末（横スクロール時に浮遊） */
:deep(.wit-matrix .el-table__header th.el-table-fixed-column--right),
:deep(.wit-matrix .el-table__header th.wit-summary-col) {
  background: #f1f5f9 !important;
  color: #334155;
  font-weight: 700;
  box-shadow: -6px 0 10px -6px rgba(15, 23, 42, 0.18);
}

:deep(.wit-matrix .el-table__body td.el-table-fixed-column--right),
:deep(.wit-matrix .el-table__body td.wit-summary-col) {
  background: #fafbfc !important;
  box-shadow: -6px 0 10px -6px rgba(15, 23, 42, 0.14);
}

:deep(.wit-matrix .el-table__body td.wit-summary-col .cell) {
  font-variant-numeric: tabular-nums;
}

/* 製品行（展開前は背景色なし） */
:deep(.wit-row--summary .wit-label__main) {
  font-size: 12.5px;
  font-weight: 600;
  color: #0f172a;
}
:deep(.el-table__body tr.wit-row--summary) {
  cursor: pointer;
}

/* 展開した子行は極薄のティントで階層感を出す */
:deep(.wit-row--metric > td),
:deep(.wit-row--part-stock > td),
:deep(.wit-row--part-usage > td) {
  background: #fcfcfd !important;
}
:deep(.wit-row--metric td.el-table-fixed-column--left),
:deep(.wit-row--part-stock td.el-table-fixed-column--left),
:deep(.wit-row--part-usage td.el-table-fixed-column--left) {
  background: #f8fafc !important;
}
:deep(.wit-row--metric td.el-table-fixed-column--right),
:deep(.wit-row--part-stock td.el-table-fixed-column--right),
:deep(.wit-row--part-usage td.el-table-fixed-column--right) {
  background: #f5f7fa !important;
}

/* 土日列 */
:deep(.wit-matrix .el-table__body td.is-saturday),
:deep(.wit-matrix .el-table__body td.is-sunday) {
  background: #f8fafc !important;
}

:deep(.wit-matrix .el-table__header th.is-saturday),
:deep(.wit-matrix .el-table__header th.is-saturday .cell) {
  color: #dc2626 !important;
  font-weight: 700;
}

:deep(.wit-matrix .el-table__header th.is-sunday),
:deep(.wit-matrix .el-table__header th.is-sunday .cell) {
  color: #2563eb !important;
  font-weight: 700;
}

/* 当日列（特別な枠線なし） */
:deep(.wit-matrix .el-table__header th.is-today) {
  background: #fef3c7 !important;
}
:deep(.wit-matrix .el-table__header th.is-today),
:deep(.wit-matrix .el-table__header th.is-today .cell) {
  color: #b45309 !important;
  font-weight: 700;
}
:deep(.wit-matrix .el-table__body td.is-today) {
  background: #fffbeb !important;
}

/* 行ホバー */
:deep(.wit-matrix .el-table__body tr:hover > td),
:deep(.wit-matrix .el-table__body tr:hover > td.el-table-fixed-column--left),
:deep(.wit-matrix .el-table__body tr:hover > td.el-table-fixed-column--right) {
  background: #f1f5f9 !important;
}
:deep(.wit-matrix .el-table__body tr:hover > td.is-today) {
  background: #fef3c7 !important;
}
</style>
