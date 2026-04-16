<template>
  <div ref="printRootRef" class="scheduling-page">
    <div class="plan-hd">
      <h2 class="plan-hd-title">
        <span class="plan-hd-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <path
              d="M7 2a1 1 0 0 1 1 1v1h8V3a1 1 0 1 1 2 0v1h1a3 3 0 0 1 3 3v3H2V7a3 3 0 0 1 3-3h1V3a1 1 0 0 1 1-1ZM2 12h20v5a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3v-5Zm6 3a1 1 0 0 0 0 2h2a1 1 0 0 0 0-2H8Zm5 0a1 1 0 1 0 0 2h3a1 1 0 1 0 0-2h-3Z"
            />
          </svg>
        </span>
        APS 生産スケジューリングボード
      </h2>
      <p class="plan-hd-sub">工程・設備・期間を指定して対象期間の生産計画を可視化し、ライン別の進捗をすばやく把握できます。</p>
    </div>

    <div class="plan-card filter-card">
      <el-form :inline="true" :model="searchForm" class="filter-form compact-form">
        <el-form-item label="工程">
          <el-select
            v-model="searchForm.processCd"
            clearable
            filterable
            placeholder="全工程"
            style="width: 90px"
            @change="handleProcessChange"
          >
            <el-option
              v-for="p in processOptions"
              :key="p.process_cd"
              :label="String(p.process_name || '').trim() || p.process_cd"
              :value="p.process_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="ライン">
          <el-select
            v-model="searchForm.lineId"
            clearable
            filterable
            placeholder="全ライン"
            style="width: 100px"
          >
            <el-option
              v-for="line in lines"
              :key="line.id"
              :value="line.id"
              :label="String(line.line_name || '').trim() || line.line_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="期間" required>
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            unlink-panels
            range-separator="~"
            start-placeholder="開始日"
            end-placeholder="終了日"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>
        <el-form-item label="製品">
          <el-select
            v-model="searchForm.itemName"
            clearable
            filterable
            placeholder="全製品"
            style="width: 220px"
          >
            <el-option v-for="name in schedulingProductOptions" :key="name" :label="name" :value="name" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <div class="stat-grid compact-grid">
      <div class="stat-card">
        <span class="stat-label">ライン数</span>
        <span class="stat-value">{{ lineCount }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">生産計画合計</span>
        <span class="stat-value">{{ formatQty(overallPlannedOutputTotal) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">能率(本/H)平均</span>
        <span class="stat-value">{{ formatEfficiency(avgEfficiencyRate) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">所要生産時間</span>
        <span class="stat-value">{{ formatHours(requiredProductionHours) }}</span>
      </div>
    </div>

    <div class="plan-card result-card" v-loading="loading">
      <div class="result-head">
        <div class="result-title">スケジューリングマトリクス</div>
        <div class="result-head-actions">
          <div class="result-note">期間：{{ displayDateRangeText }}</div>
          <el-button class="print-btn" size="small" @click="handlePrint">印刷</el-button>
        </div>
      </div>

      <el-empty v-if="!loading && gridDates.length === 0" description="期間を指定して検索してください" />

      <div v-else class="matrix-table-wrapper modern-scroll">
        <table class="matrix-table">
          <thead>
            <tr>
              <th class="sc-sticky-col sc-line-col">ライン</th>
              <th class="sc-sticky-col sc-order-col">順位</th>
              <th class="sc-sticky-col sc-item-col">製品</th>
              <th class="sc-sticky-col sc-eff-col numeric-cell">能率(本/H)</th>
              <th class="sc-sticky-col sc-total-col numeric-cell">生産計画</th>
              <th
                v-for="date in gridDates"
                :key="date"
                class="date-col"
                :class="{ 'is-weekend': isWeekend(date), 'is-today': isToday(date) }"
              >
                <div class="date-header">
                  <div class="date-text">{{ formatMatrixDate(date) }}</div>
                  <div class="weekday-text">{{ getWeekdayLabel(date) }}</div>
                </div>
              </th>
            </tr>
          </thead>
          <tbody v-for="section in matrixSections" :key="section.key" class="sc-line-section">
            <tr
              v-for="row in section.rows"
              :key="row.key"
              :class="[
                row.type === 'group' ? 'sc-group-header-row' : 'sc-item-row',
                row.type === 'item' && row.material_shortage ? 'sc-material-shortage-row' : '',
              ]"
            >
              <td class="sc-sticky-col sc-line-col">
                <div class="sc-line-cell">
                  <span class="sc-line-code">{{ row.type === 'group' ? row.line_name : '' }}</span>
                </div>
              </td>
              <td class="sc-sticky-col sc-order-col numeric-cell">
                {{ row.type === 'item' ? (row.order_no ?? '-') : '' }}
              </td>
              <td class="sc-sticky-col sc-item-col">
                <div class="sc-item-cell">
                  <div class="sc-item-name">{{ row.type === 'item' ? row.item_name : '' }}</div>
                  <div v-if="row.type === 'item' && row.material_shortage" class="sc-flag">資材不足</div>
                </div>
              </td>
              <td class="sc-sticky-col sc-eff-col numeric-cell">
                {{ formatEfficiency(row.type === 'item' ? row.efficiency_rate : row.avg_efficiency) }}
              </td>
              <td class="sc-sticky-col sc-total-col numeric-cell">
                {{ formatQty(row.type === 'item' ? row.planned_output_qty : row.sum_planned_output_qty) }}
              </td>
              <td
                v-for="date in gridDates"
                :key="`${row.key}-${date}`"
                class="numeric-cell data-cell"
                :class="getCellClass(row, date)"
                :title="getCellTitle(row, date)"
              >
                <span v-if="row.type === 'item' && getCellValue(row, date)">
                  {{ formatQty(getCellValue(row, date)) }}
                </span>
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="sc-total-footer-row">
              <td class="sc-sticky-col sc-line-col">合計</td>
              <td class="sc-sticky-col sc-order-col" />
              <td class="sc-sticky-col sc-item-col" />
              <td class="sc-sticky-col sc-eff-col" />
              <td class="sc-sticky-col sc-total-col numeric-cell">{{ formatQty(overallPlannedOutputTotal) }}</td>
              <td v-for="date in gridDates" :key="`total-${date}`" class="numeric-cell">
                {{ formatQty(overallDailyTotals[date] || 0) }}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import {
  fetchLines,
  fetchSchedulingGrid,
  type LineGridBlock,
  type ProductionLine,
  type ScheduleGridRow,
  type SchedulingGridResponse,
} from '@/api/aps'

type MatrixGroupRow = {
  key: string
  type: 'group'
  line_id: number
  line_code: string
  line_name: string
  utilization_rate?: number | null
  sum_planned_output_qty: number
  daily_totals: Record<string, number>
  sum_adjust_qty: number
  sum_setup_time: number
  avg_efficiency?: number | null
}

type MatrixItemRow = {
  key: string
  type: 'item'
  line_id: number
  line_code: string
  line_name: string
  order_no?: number | null
  item_name: string
  material_shortage: boolean
  adjust_qty: number
  material_date?: string | null
  setup_time: number
  efficiency_rate: number
  planned_output_qty: number
  completion_rate?: number | null
  due_date?: string | null
  daily: Record<string, number>
}

type MatrixRow = MatrixGroupRow | MatrixItemRow

const processOptions = ref<ProcessItem[]>([])
const lines = ref<ProductionLine[]>([])
const grid = ref<SchedulingGridResponse | null>(null)
const loading = ref(false)
const printRootRef = ref<HTMLElement | null>(null)

const searchForm = reactive<{
  processCd: string
  dateRange: [string, string]
  lineId: number | null
  itemName: string | null
}>({
  processCd: 'KT04',
  dateRange: [dayjs().subtract(1, 'day').format('YYYY-MM-DD'), dayjs().add(30, 'day').format('YYYY-MM-DD')],
  lineId: null,
  itemName: null,
})

const gridDates = computed(() => grid.value?.dates ?? [])
const visibleBlocks = computed(() => (grid.value?.blocks ?? []).filter((b) => !isIgnoredLine(resolveLineName(b.line_id, b.line_code))))

/** 当前网格中的品名（忽略已隐藏ライン），供製品下拉使用 */
const schedulingProductOptions = computed(() => {
  const names = new Set<string>()
  for (const b of visibleBlocks.value) {
    for (const r of b.rows ?? []) {
      const n = String(r.item_name || '').trim()
      if (n) names.add(n)
    }
  }
  return [...names].sort((a, b) => a.localeCompare(b, 'ja'))
})

/** 按製品筛选后的块；并重算日计与合計以便矩阵与统计一致 */
const displayBlocks = computed<LineGridBlock[]>(() => {
  const blocks = visibleBlocks.value
  const dates = gridDates.value
  const needle = (searchForm.itemName || '').trim()
  if (!needle) return blocks

  const out: LineGridBlock[] = []
  for (const block of blocks) {
    const rows = (block.rows ?? []).filter((r) => String(r.item_name || '').trim() === needle)
    if (!rows.length) continue

    const daily_totals: Record<string, number> = {}
    for (const d of dates) daily_totals[d] = 0
    let sum_planned_output_qty = 0
    let sum_planned_process_qty = 0
    for (const r of rows) {
      sum_planned_output_qty += Number(r.planned_output_qty ?? 0)
      sum_planned_process_qty += Number(r.planned_process_qty ?? 0)
      for (const d of dates) {
        daily_totals[d] = (daily_totals[d] ?? 0) + Number((r.daily ?? {})[d] ?? 0)
      }
    }
    out.push({
      ...block,
      rows,
      daily_totals,
      sum_planned_output_qty,
      sum_planned_process_qty,
    })
  }
  return out
})

const matrixRows = computed<MatrixRow[]>(() => {
  if (!grid.value) return []
  return buildMatrixRows(displayBlocks.value)
})
const matrixSections = computed(() => {
  const sections: Array<{ key: string; rows: MatrixRow[] }> = []
  let currentRows: MatrixRow[] = []
  let currentKey = ''

  matrixRows.value.forEach((row) => {
    if (row.type === 'group') {
      if (currentRows.length) sections.push({ key: currentKey, rows: currentRows })
      currentKey = row.key
      currentRows = [row]
      return
    }
    if (currentRows.length === 0) {
      currentKey = row.key
    }
    currentRows.push(row)
  })

  if (currentRows.length) sections.push({ key: currentKey, rows: currentRows })
  return sections
})

const lineCount = computed(() => displayBlocks.value.length)

const overallPlannedOutputTotal = computed(() =>
  displayBlocks.value.reduce(
    (acc, b) =>
      acc +
      (b.rows ?? []).reduce(
        (rowAcc, r) =>
          rowAcc +
          gridDates.value.reduce((dateAcc, date) => dateAcc + Number((r.daily ?? {})[date] ?? 0), 0),
        0,
      ),
    0,
  ),
)

const avgEfficiencyRate = computed(() => {
  const blocks = displayBlocks.value
  let weightedSum = 0
  let weightedDenom = 0
  for (const block of blocks) {
    for (const row of block.rows ?? []) {
      const rate = Number(row.efficiency_rate ?? row.efficiency ?? 0)
      const qty = Number(row.planned_process_qty ?? 0)
      if (!Number.isFinite(rate) || !Number.isFinite(qty) || qty <= 0) continue
      weightedSum += rate * qty
      weightedDenom += qty
    }
  }
  if (weightedDenom <= 0) return null
  return weightedSum / weightedDenom
})

const requiredProductionHours = computed(() => {
  const totalQty = Number(overallPlannedOutputTotal.value ?? 0)
  const avgRate = Number(avgEfficiencyRate.value ?? 0)
  if (!Number.isFinite(totalQty) || !Number.isFinite(avgRate) || avgRate <= 0) return null
  return totalQty / avgRate
})

const overallDailyTotals = computed(() => {
  const totals: Record<string, number> = {}
  for (const date of gridDates.value) totals[date] = 0
  for (const block of displayBlocks.value) {
    for (const [date, qty] of Object.entries(block.daily_totals ?? {})) {
      totals[date] = (totals[date] ?? 0) + (qty ?? 0)
    }
  }
  return totals
})

const displayDateRangeText = computed(() => {
  const [s, e] = searchForm.dateRange || []
  if (!s || !e) return '-'
  return `${s} ~ ${e}`
})

function formatQty(v: number) {
  const n = Number(v ?? 0)
  if (!Number.isFinite(n)) return '-'
  return n.toLocaleString()
}

function formatEfficiency(v?: number | null) {
  if (v == null || !Number.isFinite(v)) return '-'
  return v.toFixed(1)
}

function formatHours(v?: number | null) {
  if (v == null || !Number.isFinite(v)) return '-'
  return `${v.toFixed(1)}H`
}

function formatMatrixDate(iso: string) {
  return dayjs(iso).format('MM/DD')
}

function getWeekdayLabel(iso: string) {
  return ['日', '月', '火', '水', '木', '金', '土'][dayjs(iso).day()]
}

function isWeekend(iso: string) {
  const d = dayjs(iso).day()
  return d === 0 || d === 6
}

function isToday(iso: string) {
  return iso === dayjs().format('YYYY-MM-DD')
}

function buildMatrixRows(blocks: LineGridBlock[]): MatrixRow[] {
  const rows: MatrixRow[] = []
  blocks.forEach((block: LineGridBlock, blockIndex) => {
    const periodRows = (block.rows ?? []).filter((r) =>
      gridDates.value.some((date) => Number((r.daily ?? {})[date] ?? 0) > 0),
    )
    if (!periodRows.length) return

    const lineName = resolveLineName(block.line_id, block.line_code)
    const groupRow: MatrixGroupRow = {
      key: `group-${block.line_id}-${blockIndex}`,
      type: 'group',
      line_id: block.line_id,
      line_code: block.line_code,
      line_name: lineName,
      utilization_rate: null,
      sum_planned_output_qty: block.sum_planned_output_qty ?? 0,
      daily_totals: block.daily_totals ?? {},
      sum_adjust_qty: 0,
      sum_setup_time: 0,
      avg_efficiency: null,
    }
    rows.push(groupRow)

    let effWeightedSum = 0
    let effWeightedDenom = 0
    let adjustSum = 0
    let setupSum = 0

    periodRows.forEach((r: ScheduleGridRow) => {
      const adjustQty = r.prev_month_carryover ?? 0
      const setupTime = r.setup_time ?? 0
      const efficiencyRate = Number(r.efficiency_rate ?? r.efficiency ?? 0)
      const plannedProcess = r.planned_process_qty ?? 0

      adjustSum += adjustQty
      setupSum += setupTime
      effWeightedSum += efficiencyRate * plannedProcess
      effWeightedDenom += plannedProcess

      rows.push({
        key: `item-${block.line_id}-${r.id}`,
        type: 'item',
        line_id: block.line_id,
        line_code: block.line_code,
        line_name: lineName,
        order_no: r.order_no ?? null,
        item_name: r.item_name,
        material_shortage: !!r.material_shortage,
        adjust_qty: adjustQty,
        material_date: r.material_date ?? null,
        setup_time: setupTime,
        efficiency_rate: efficiencyRate,
        planned_output_qty: r.planned_output_qty ?? 0,
        completion_rate: r.completion_rate ?? null,
        due_date: r.due_date ?? null,
        daily: r.daily ?? {},
      })
    })

    groupRow.sum_adjust_qty = adjustSum
    groupRow.sum_setup_time = setupSum
    groupRow.avg_efficiency = effWeightedDenom > 0 ? effWeightedSum / effWeightedDenom : null
    const availableHours = Object.values(block.calendar ?? {}).reduce((acc, h) => acc + Number(h || 0), 0)
    let plannedHours = 0
    for (const r of periodRows) {
      const qty = Number(r.planned_output_qty ?? 0)
      const rate = Number(r.efficiency_rate ?? r.efficiency ?? 0)
      if (!Number.isFinite(qty) || !Number.isFinite(rate) || rate <= 0) continue
      plannedHours += qty / rate
    }
    groupRow.utilization_rate = availableHours > 0 ? (plannedHours / availableHours) * 100 : null
  })
  return rows
}

function resolveLineName(lineId: number, fallbackCode: string) {
  const line = lines.value.find((x) => x.id === lineId)
  const name = String(line?.line_name || '').trim()
  if (name) return name
  return fallbackCode
}

function isIgnoredLine(lineName: string) {
  const normalized = lineName.trim()
  return normalized === '成型他' || normalized === 'FM-026'
}

function getCellValue(row: MatrixRow, date: string): number {
  if (row.type === 'group') return row.daily_totals?.[date] ?? 0
  return row.daily?.[date] ?? 0
}

function getCellTitle(row: MatrixRow, date: string): string {
  const v = getCellValue(row, date) || 0
  if (!v) return `${date}: 計画なし`
  if (row.type === 'group') return `${date}: ライン合計 ${v}`
  return `${date}: ${row.item_name} / ${v}`
}

function getCellClass(row: MatrixRow, date: string): string {
  const v = getCellValue(row, date) || 0
  const dueMatch = row.type === 'item' && row.due_date ? row.due_date === date : false

  if (row.type === 'group') return ''
  if (!v) return dueMatch ? 'cell-due' : ''
  if (row.type === 'item' && row.material_shortage) return dueMatch ? 'tone-shortage cell-due' : 'tone-shortage'

  const rate = row.completion_rate
  if (rate != null && Number.isFinite(rate)) {
    if (rate >= 80) return dueMatch ? 'tone-high cell-due' : 'tone-high'
    if (rate >= 50) return dueMatch ? 'tone-mid cell-due' : 'tone-mid'
    return dueMatch ? 'tone-low cell-due' : 'tone-low'
  }
  return dueMatch ? 'tone-active cell-due' : 'tone-active'
}

function handlePrint() {
  const root = printRootRef.value
  if (!root) return

  const printTarget = root.querySelector('.result-card') as HTMLElement | null
  if (!printTarget) return

  const styleTags = Array.from(document.querySelectorAll('style, link[rel="stylesheet"]'))
    .map((el) => el.outerHTML)
    .join('\n')

  const win = window.open('', '_blank')
  if (!win) return

  win.document.open()
  win.document.write(`
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Scheduling Print</title>
        ${styleTags}
        <style>
          @page { size: A3 landscape; margin: 8mm; }
          html, body { margin: 0; padding: 0; }
          * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
          .matrix-table-wrapper { height: auto !important; max-height: none !important; overflow: visible !important; }
          .result-card { border: none !important; box-shadow: none !important; padding: 0 !important; margin: 0 !important; }
          .result-head-actions .el-button { display: none !important; }
          tfoot { display: table-row-group !important; }
          .sc-total-footer-row td { position: static !important; bottom: auto !important; }
          .sc-line-section { break-inside: avoid; page-break-inside: avoid; }
          .sc-line-section tr { break-inside: avoid; page-break-inside: avoid; }
        </style>
      </head>
      <body>
        ${printTarget.outerHTML}
      </body>
    </html>
  `)
  win.document.close()
  win.focus()
  win.print()
}

async function loadProcessOptions() {
  try {
    const res = await fetchProcesses({ page: 1, pageSize: 5000 })
    const data = (res?.data ?? res) as { list?: ProcessItem[] }
    processOptions.value = Array.isArray(data.list) ? data.list : []
    const hasDefault = processOptions.value.some((p) => (p.process_cd || '').trim() === 'KT04')
    if (!hasDefault && processOptions.value.length) {
      searchForm.processCd = processOptions.value[0].process_cd || ''
    }
  } catch {
    processOptions.value = []
  }
}

async function loadLines() {
  lines.value = await fetchLines((searchForm.processCd || '').trim() || undefined)
  lines.value = lines.value.filter((x) => !isIgnoredLine(String(x.line_name || '').trim() || x.line_code))
  if (searchForm.lineId && !lines.value.some((x) => x.id === searchForm.lineId)) {
    searchForm.lineId = null
  }
}

async function loadGrid() {
  const [startDate, endDate] = searchForm.dateRange
  if (!startDate || !endDate) return
  loading.value = true
  try {
    grid.value = await fetchSchedulingGrid(
      startDate,
      endDate,
      searchForm.lineId ?? undefined,
      (searchForm.processCd || '').trim() || undefined,
    )
  } finally {
    loading.value = false
  }
}

async function handleProcessChange() {
  await loadLines()
  await loadGrid()
}

let autoLoadTimer: ReturnType<typeof setTimeout> | null = null
function scheduleAutoLoad() {
  if (autoLoadTimer) clearTimeout(autoLoadTimer)
  autoLoadTimer = setTimeout(() => {
    void loadGrid()
  }, 240)
}

onMounted(async () => {
  await loadProcessOptions()
  await loadLines()
  await loadGrid()
})

watch(
  () => searchForm.lineId,
  () => {
    scheduleAutoLoad()
  },
)

watch(
  () => searchForm.dateRange,
  () => {
    scheduleAutoLoad()
  },
  { deep: true },
)

watch(
  () => grid.value,
  () => {
    const sel = (searchForm.itemName || '').trim()
    if (!sel) return
    if (!schedulingProductOptions.value.includes(sel)) {
      searchForm.itemName = null
    }
  },
)
</script>

<style scoped>
.scheduling-page {
  padding: 10px 12px 12px;
  background:
    radial-gradient(circle at 10% -20%, rgba(59, 130, 246, 0.1), transparent 35%),
    radial-gradient(circle at 110% -30%, rgba(16, 185, 129, 0.08), transparent 30%),
    #f3f6fb;
  min-height: 100%;
}

.plan-hd {
  margin-bottom: 8px;
  padding: 4px 2px 2px;
}

.plan-hd-title {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.2px;
  line-height: 1.1;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.55);
}

.plan-hd-icon {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  box-shadow:
    0 6px 14px rgba(37, 99, 235, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.plan-hd-icon svg {
  width: 15px;
  height: 15px;
  fill: #fff;
}

.plan-hd-sub {
  margin: 5px 0 0 34px;
  color: #5f6f86;
  font-size: 12px;
  line-height: 1.45;
}

.plan-card {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(3px);
  padding: 10px 12px;
  margin-bottom: 8px;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 20px rgba(15, 23, 42, 0.04);
}

.filter-card {
  padding: 7px 10px;
  border-color: rgba(191, 219, 254, 0.75);
  background:
    linear-gradient(135deg, rgba(239, 246, 255, 0.82) 0%, rgba(250, 245, 255, 0.76) 100%),
    rgba(255, 255, 255, 0.95);
  box-shadow:
    0 10px 22px rgba(37, 99, 235, 0.07),
    inset 0 1px 0 rgba(255, 255, 255, 0.74);
}

.filter-form :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #1e3a8a;
  padding-right: 5px;
  line-height: 30px;
}

.compact-form {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  row-gap: 2px;
  column-gap: 6px;
}

.compact-form :deep(.el-form-item) {
  margin-bottom: 2px;
  margin-right: 0;
}

.compact-form :deep(.el-input__wrapper),
.compact-form :deep(.el-select__wrapper) {
  border-radius: 10px;
  min-height: 32px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  transition: box-shadow 0.18s ease, border-color 0.18s ease;
}

.compact-form :deep(.el-input__wrapper:hover),
.compact-form :deep(.el-select__wrapper:hover) {
  box-shadow: 0 4px 10px rgba(37, 99, 235, 0.12);
}

.compact-form :deep(.el-input__wrapper.is-focus),
.compact-form :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18);
}

.compact-form :deep(.el-input__inner),
.compact-form :deep(.el-select__selected-item),
.compact-form :deep(.el-range-input) {
  font-size: 12px;
}

.compact-form :deep(.el-button) {
  border-radius: 8px;
  font-weight: 600;
  padding: 8px 14px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(140px, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}

.compact-grid {
  grid-template-columns: repeat(4, minmax(120px, 1fr));
}

.stat-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(191, 219, 254, 0.75);
  border-radius: 14px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  background:
    radial-gradient(circle at 100% 0%, rgba(99, 102, 241, 0.12), transparent 44%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.96) 0%, rgba(243, 248, 255, 0.95) 100%);
  box-shadow:
    0 10px 24px rgba(37, 99, 235, 0.09),
    0 2px 6px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
  transition: transform 0.18s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.stat-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
  opacity: 0.95;
}

.stat-card:hover {
  transform: translateY(-1px);
  border-color: rgba(147, 197, 253, 0.95);
  box-shadow:
    0 14px 28px rgba(37, 99, 235, 0.13),
    0 4px 10px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.78);
}

.stat-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.2px;
  color: #5b6b82;
}

.stat-value {
  font-size: 20px;
  font-weight: 800;
  color: #0b1220;
  line-height: 1.1;
  letter-spacing: 0.2px;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.55);
}

.stat-value--warn {
  color: #dc2626;
}

.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.result-head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.print-btn {
  border: none;
  color: #fff;
  font-weight: 700;
  letter-spacing: 0.2px;
  border-radius: 999px;
  padding: 7px 14px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  box-shadow:
    0 8px 18px rgba(37, 99, 235, 0.28),
    0 2px 4px rgba(124, 58, 237, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.34);
  transition:
    transform 0.16s ease,
    box-shadow 0.22s ease,
    filter 0.22s ease;
}

.print-btn:hover {
  transform: translateY(-1px);
  filter: brightness(1.03);
  box-shadow:
    0 12px 22px rgba(37, 99, 235, 0.33),
    0 4px 8px rgba(124, 58, 237, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.print-btn:active {
  transform: translateY(0);
  box-shadow:
    0 5px 12px rgba(37, 99, 235, 0.25),
    0 1px 3px rgba(124, 58, 237, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.28);
}

.print-btn.is-disabled,
.print-btn.is-disabled:hover,
.print-btn.is-disabled:active {
  transform: none;
  filter: none;
  opacity: 0.62;
  box-shadow: none;
}

.result-title {
  font-size: 14px;
  font-weight: 800;
  color: #0f172a;
}

.result-note {
  font-size: 11px;
  color: #64748b;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 2px 8px;
  border-radius: 999px;
}

.matrix-table-wrapper {
  height: 620px;
  overflow: auto;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
}

.modern-scroll {
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.matrix-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.matrix-table th,
.matrix-table td {
  border: 1px solid #e6edf5;
  padding: 3px 5px;
  white-space: nowrap;
}

.matrix-table thead th {
  background: linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
  font-weight: 700;
  color: #42526a;
  position: sticky;
  top: 0;
  z-index: 3;
  box-shadow: 0 1px 0 #dbe5f1;
}

.sc-sticky-col {
  position: sticky;
  left: 0;
  background: #fff;
  z-index: 2;
}

.matrix-table thead .sc-sticky-col {
  z-index: 4;
}

.sc-line-col {
  width: 50px;
  min-width: 50px;
  left: 0;
}

.sc-order-col {
  width: 50px;
  min-width: 50px;
  left: 50px;
}

.sc-item-col {
  width: 120px;
  min-width: 120px;
  left: 100px;
}

.sc-eff-col {
  width: 66px;
  min-width: 66px;
  left: 220px;
}

.sc-total-col {
  width: 90px;
  min-width: 90px;
  left: 286px;
}

.numeric-cell {
  text-align: center;
}

.date-col {
  min-width: 40px;
}

.date-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.1;
}

.date-text {
  font-size: 10px;
  font-weight: 650;
}

.weekday-text {
  font-size: 9px;
  color: #6b7a90;
}

.sc-group-header-row {
  font-weight: 700;
  border-top: 2px solid #bfdbfe;
}

.sc-group-header-row .sc-line-code {
  font-weight: 800;
  color: #1e3a8a;
}

.sc-item-row:nth-child(2n) {
  background: #fcfdff;
}

.sc-item-row:hover {
  background: #f1f7ff;
}

.sc-line-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-height: 18px;
}

.sc-rate {
  color: #1d4ed8;
  font-size: 10px;
  font-weight: 700;
}

.sc-item-name {
  max-width: 170px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sc-flag {
  color: #dc2626;
  font-size: 9px;
  font-weight: 700;
}

.tone-active {
  background: rgba(187, 247, 208, 0.5);
}

.tone-high {
  background: rgba(34, 197, 94, 0.22);
}

.tone-mid {
  background: rgba(245, 158, 11, 0.18);
}

.tone-low {
  background: rgba(239, 68, 68, 0.18);
}

.tone-shortage {
  background: rgba(239, 68, 68, 0.26);
}

.cell-due {
  outline: 1px solid #f59e0b;
  outline-offset: -2px;
}

.matrix-table thead th.is-weekend .date-text,
.matrix-table thead th.is-weekend .weekday-text {
  color: #dc2626;
}

.matrix-table thead th.is-today {
  background: linear-gradient(180deg, #fff3d4 0%, #ffeab0 100%);
}

.sc-total-footer-row td {
  background: #f3f8ff;
  font-weight: 700;
  position: sticky;
  bottom: 0;
  z-index: 3;
  box-shadow: 0 -1px 0 #dbe5f1;
}

.sc-total-footer-row .sc-sticky-col {
  z-index: 4;
}

@media (max-width: 1400px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(120px, 1fr));
  }
}
</style>

