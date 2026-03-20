<template>
  <div class="scheduling-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h3>スケジューリング</h3>
          <div class="card-subtitle">排産スケジューリンググリッド（カラーマトリックス）</div>
        </div>
      </template>

      <div class="toolbar">
        <div class="toolbar-left">
          <el-form
            :inline="true"
            :model="searchForm"
            label-position="left"
            class="toolbar-form"
          >
            <el-form-item label="期間">
              <el-date-picker
                v-model="searchForm.dateRange"
                type="daterange"
                unlink-panels
                range-separator="〜"
                start-placeholder="開始日"
                end-placeholder="終了日"
                value-format="YYYY-MM-DD"
                format="YYYY-MM-DD"
                @change="handleDateRangeChange"
                class="date-picker"
              />
            </el-form-item>

            <el-form-item label="ライン">
              <el-select
                v-model="searchForm.lineId"
                placeholder="全て"
                clearable
                style="width: 180px"
              >
                <el-option
                  v-for="line in lines"
                  :key="line.id"
                  :value="line.id"
                  :label="line.line_code"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <div class="toolbar-right">
          <el-button type="primary" :loading="loading" @click="loadGrid">
            再取得
          </el-button>
          <el-button type="success" :loading="runningAll" @click="runAll">
            一括実行
          </el-button>
        </div>
      </div>

      <div v-loading="loading" element-loading-text="ロード中..." class="grid-section">
        <div v-if="gridDates.length === 0" class="empty-state">
          日付範囲を選択して「再取得」を押してください。
        </div>

        <div v-else class="matrix-table-wrapper">
          <table class="matrix-table scheduling-table">
            <thead>
              <tr>
                <th class="sc-sticky-col sc-line-col">ライン</th>
                <th class="sc-sticky-col sc-order-col">順位</th>
                <th class="sc-sticky-col sc-item-col">製品名</th>
                <th class="sc-sticky-col sc-adjust-col numeric-cell">調整数</th>
                <th class="sc-sticky-col sc-material-col">材料調達</th>
                <th class="sc-sticky-col sc-setup-col numeric-cell">段取時間</th>
                <th class="sc-sticky-col sc-eff-col numeric-cell">能率</th>
                <th class="sc-sticky-col sc-total-col numeric-cell">計画数</th>
                <th
                  v-for="date in gridDates"
                  :key="date"
                  class="date-col"
                  :class="{
                    'is-weekend': isWeekend(date),
                    'is-today': isToday(date),
                  }"
                >
                  <div class="date-header">
                    <div class="date-text">{{ formatMatrixDate(date) }}</div>
                    <div class="weekday-text">{{ getWeekdayLabel(date) }}</div>
                  </div>
                </th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="row in matrixRows"
                :key="row.key"
                :class="[
                  'matrix-row',
                  {
                    'sc-group-header-row': row.type === 'group',
                    'sc-item-row': row.type === 'item',
                    'sc-material-shortage-row': row.type === 'item' && row.material_shortage,
                  },
                ]"
              >
                <td
                  class="sc-sticky-col sc-line-col"
                  :title="row.type === 'group' ? row.line_code : ''"
                >
                  <div class="sc-line-cell">
                    <span class="sc-line-code">{{ row.line_code }}</span>
                    <span v-if="row.type === 'group'" class="sc-rate">
                      {{ formatPercent(row.completion_rate) }}
                    </span>
                  </div>
                </td>

                <td class="sc-sticky-col sc-order-col numeric-cell">
                  <span v-if="row.type === 'item'">{{ row.order_no ?? '' }}</span>
                </td>

                <td class="sc-sticky-col sc-item-col">
                  <div class="sc-item-cell">
                    <div class="sc-item-name">
                      {{ row.type === 'item' ? row.item_name : '' }}
                    </div>
                    <div v-if="row.type === 'item' && row.material_shortage" class="sc-flag">
                      資材不足
                    </div>
                  </div>
                </td>

                <td class="sc-sticky-col sc-adjust-col numeric-cell">
                  <span v-if="row.type === 'item'">{{ formatQty(row.adjust_qty) }}</span>
                  <span v-else>{{ formatQty(row.sum_adjust_qty) }}</span>
                </td>

                <td class="sc-sticky-col sc-material-col">
                  <span v-if="row.type === 'item'">
                    <span v-if="row.material_shortage" class="sc-flag">不足</span>
                    <span v-else>{{ formatMaterialDate(row.material_date) }}</span>
                  </span>
                  <span v-else>-</span>
                </td>

                <td class="sc-sticky-col sc-setup-col numeric-cell">
                  <span v-if="row.type === 'item'">{{ row.setup_time }}分</span>
                  <span v-else>{{ row.sum_setup_time }}分</span>
                </td>

                <td class="sc-sticky-col sc-eff-col numeric-cell">
                  <span v-if="row.type === 'item'">{{ formatEfficiency(row.efficiency) }}</span>
                  <span v-else>{{ formatEfficiency(row.avg_efficiency) }}</span>
                </td>

                <td class="sc-sticky-col sc-total-col numeric-cell">
                  <span v-if="row.type === 'group'">
                    {{ formatQty(row.sum_planned_output_qty) }}
                  </span>
                  <span v-else>
                    {{ formatQty(row.planned_output_qty) }}
                  </span>
                </td>

                <td
                  v-for="date in gridDates"
                  :key="row.key + '-' + date"
                  class="numeric-cell data-cell"
                  :class="getCellClass(row, date)"
                  :title="getCellTitle(row, date)"
                >
                  <span v-if="getCellValue(row, date) !== 0">
                    {{ formatQty(getCellValue(row, date)) }}
                  </span>
                  <span v-else class="cell-empty"></span>
                </td>
              </tr>
            </tbody>

            <tfoot>
              <tr class="sc-total-footer-row">
                <td class="sc-sticky-col sc-line-col">合計</td>
                <td class="sc-sticky-col sc-order-col"></td>
                <td class="sc-sticky-col sc-item-col"></td>
                <td class="sc-sticky-col sc-adjust-col numeric-cell"></td>
                <td class="sc-sticky-col sc-material-col"></td>
                <td class="sc-sticky-col sc-setup-col numeric-cell"></td>
                <td class="sc-sticky-col sc-eff-col numeric-cell"></td>
                <td class="sc-sticky-col sc-total-col numeric-cell">
                  {{ formatQty(overallPlannedOutputTotal) }}
                </td>
                <td
                  v-for="date in gridDates"
                  :key="'total-' + date"
                  class="numeric-cell"
                >
                  {{ formatQty(overallDailyTotals[date] || 0) }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { computed, onMounted, reactive, ref } from 'vue'
import {
  fetchLines,
  fetchSchedulingGrid,
  runAllSchedules,
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
  completion_rate?: number | null
  sum_planned_process_qty: number
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
  order_no?: number | null
  item_name: string
  material_shortage: boolean
  adjust_qty: number
  material_date?: string | null
  setup_time: number
  efficiency: number
  planned_output_qty: number
  completion_rate?: number | null
  due_date?: string | null
  daily: Record<string, number>
}

type MatrixRow = MatrixGroupRow | MatrixItemRow

const searchForm = reactive<{
  dateRange: [string, string]
  lineId: number | null
}>({
  dateRange: [
    dayjs().subtract(7, 'day').format('YYYY-MM-DD'),
    dayjs().add(13, 'day').format('YYYY-MM-DD'),
  ],
  lineId: null,
})

const lines = ref<ProductionLine[]>([])
const grid = ref<SchedulingGridResponse | null>(null)
const loading = ref(false)
const runningAll = ref(false)

const gridDates = computed(() => grid.value?.dates ?? [])

const overallDailyTotals = computed(() => {
  const totals: Record<string, number> = {}
  for (const date of gridDates.value) totals[date] = 0
  for (const block of grid.value?.blocks ?? []) {
    for (const [date, qty] of Object.entries(block.daily_totals ?? {})) {
      totals[date] = (totals[date] ?? 0) + (qty ?? 0)
    }
  }
  return totals
})

const overallPlannedOutputTotal = computed(() => {
  return (grid.value?.blocks ?? []).reduce((acc, b) => acc + (b.sum_planned_output_qty ?? 0), 0)
})

function formatQty(v: number) {
  const n = Number(v ?? 0)
  if (!Number.isFinite(n)) return ''
  return n.toLocaleString()
}

function formatPercent(v?: number | null) {
  if (v == null) return ''
  if (!Number.isFinite(v)) return ''
  return `${v.toFixed(1)}%`
}

function formatMaterialDate(iso?: string | null) {
  if (!iso) return '-'
  return dayjs(iso).format('MM/DD')
}

function formatEfficiency(v?: number | null) {
  if (v == null || !Number.isFinite(v)) return '-'
  // 能率設定画面の表示に合わせて小数 1 桁
  return v.toFixed(1)
}

function formatMatrixDate(iso: string) {
  // iso: YYYY-MM-DD
  return dayjs(iso).format('MM/DD')
}

function getWeekdayLabel(iso: string) {
  const d = dayjs(iso)
  const weekday = d.day()
  // 日月火水木金土
  return ['日', '月', '火', '水', '木', '金', '土'][weekday]
}

function isWeekend(iso: string) {
  const d = dayjs(iso).day()
  return d === 0 || d === 6
}

function isToday(iso: string) {
  return iso === dayjs().format('YYYY-MM-DD')
}

function handleDateRangeChange() {
  // 日付条件が変更されても自動で再取得しない（頻繁なAPI呼び出しを防ぐ）
}

function buildMatrixRows(res: SchedulingGridResponse): MatrixRow[] {
  const rows: MatrixRow[] = []
  res.blocks.forEach((block: LineGridBlock, blockIndex) => {
    const groupRow: MatrixGroupRow = {
      key: `group-${block.line_id}-${blockIndex}`,
      type: 'group',
      line_id: block.line_id,
      line_code: block.line_code,
      completion_rate: block.completion_rate ?? null,
      sum_planned_process_qty: block.sum_planned_process_qty ?? 0,
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

    ;(block.rows ?? []).forEach((r: ScheduleGridRow) => {
      const adjustQty = r.prev_month_carryover ?? 0
      const setupTime = r.setup_time ?? 0
      const efficiency = r.efficiency ?? 0
      const plannedProcess = r.planned_process_qty ?? 0

      adjustSum += adjustQty
      setupSum += setupTime
      effWeightedSum += efficiency * plannedProcess
      effWeightedDenom += plannedProcess

      rows.push({
        key: `item-${block.line_id}-${r.id}`,
        type: 'item',
        line_id: block.line_id,
        line_code: block.line_code,
        order_no: r.order_no ?? null,
        item_name: r.item_name,
        material_shortage: !!r.material_shortage,
        adjust_qty: adjustQty,
        material_date: r.material_date ?? null,
        setup_time: setupTime,
        efficiency,
        planned_output_qty: r.planned_output_qty ?? 0,
        completion_rate: r.completion_rate ?? null,
        due_date: r.due_date ?? null,
        daily: r.daily ?? {},
      })
    })

    groupRow.sum_adjust_qty = adjustSum
    groupRow.sum_setup_time = setupSum
    groupRow.avg_efficiency = effWeightedDenom > 0 ? effWeightedSum / effWeightedDenom : null
  })
  return rows
}

const matrixRows = computed<MatrixRow[]>(() => {
  if (!grid.value) return []
  return buildMatrixRows(grid.value)
})

function getCellValue(row: MatrixRow, date: string): number {
  if (row.type === 'group') return row.daily_totals?.[date] ?? 0
  return row.daily?.[date] ?? 0
}

function getCellTitle(row: MatrixRow, date: string): string {
  const v = getCellValue(row, date) ?? 0
  if (v === 0) return `${date}：予定なし`
  if (row.type === 'group') return `${date}：合計 ${v}`
  return `${date}：${row.item_name} / ${v}`
}

function getCellClass(row: MatrixRow, date: string): string {
  const v = getCellValue(row, date) ?? 0
  const dueMatch = row.type === 'item' && row.due_date ? row.due_date === date : false

  if (!v) {
    return dueMatch ? 'cell-due' : ''
  }

  // 優先1：資材不足
  if (row.type === 'item' && row.material_shortage) return dueMatch ? 'tone-shortage cell-due' : 'tone-shortage'

  // 優先2：完了率（行全体）で色付け（スクリーンショットの色味に近似）
  const rate = row.type === 'group' ? row.completion_rate : row.completion_rate
  if (rate != null && Number.isFinite(rate)) {
    if (rate >= 80) return dueMatch ? 'tone-high cell-due' : 'tone-high'
    if (rate >= 50) return dueMatch ? 'tone-mid cell-due' : 'tone-mid'
    return dueMatch ? 'tone-low cell-due' : 'tone-low'
  }

  // 完了率がない場合：計画値があるものは緑系
  return dueMatch ? 'tone-active cell-due' : 'tone-active'
}

async function loadGrid() {
  const [startDate, endDate] = searchForm.dateRange
  if (!startDate || !endDate) return

  loading.value = true
  try {
    grid.value = await fetchSchedulingGrid(startDate, endDate, searchForm.lineId ?? undefined)
  } finally {
    loading.value = false
  }
}

async function runAll() {
  const [startDate, endDate] = searchForm.dateRange
  if (!startDate || !endDate) return

  // 一括実行 -> backend は PLANNING / IN_PROGRESS をすべて再計算して予定を更新する想定
  // 実行後に現在のグリッドを再取得（期間は変更しない）
  runningAll.value = true
  try {
    await runAllSchedules(searchForm.lineId ?? undefined)
    await loadGrid()
  } finally {
    runningAll.value = false
  }
}

async function init() {
  lines.value = await fetchLines()
  await loadGrid()
}

onMounted(() => {
  init()
})
</script>

<style scoped>
.scheduling-container {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: baseline;
  gap: 16px;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
}

.card-subtitle {
  font-size: 12px;
  color: #64748b;
}

.toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.toolbar-left {
  flex: 1;
}

.toolbar-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #334155;
}

.date-picker :deep(.el-input__wrapper) {
  width: 280px;
}

.toolbar-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.grid-section {
  width: 100%;
}

.empty-state {
  padding: 22px 10px;
  text-align: center;
  color: #64748b;
}

.matrix-table-wrapper {
  width: 100%;
  height: 520px;
  max-height: 520px;
  overflow: auto;
  border-radius: 8px;
  border: 1px solid rgba(226, 232, 240, 0.7);
}

.matrix-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  background: #fff;
  font-size: 11px;
}

.matrix-table th,
.matrix-table td {
  border: 1px solid rgba(226, 232, 240, 0.6);
  padding: 3px 5px;
  vertical-align: middle;
  font-size: 10px;
}

.matrix-table thead th {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  font-weight: 650;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 3;
  color: #475569;
}

.date-col {
  min-width: 42px;
}

.date-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.1;
  gap: 1px;
}

.date-text {
  font-size: 10px;
  color: #475569;
  font-weight: 520;
}

.weekday-text {
  font-size: 9px;
  color: #64748b;
}

.matrix-table tbody tr {
  height: 26px;
}

.matrix-table tbody tr:hover {
  background-color: rgba(248, 250, 252, 0.8);
}

.sc-sticky-col {
  position: sticky;
  left: 0;
  background: #fff;
  z-index: 2;
  white-space: nowrap;
  font-weight: 700;
}

.matrix-table thead .sc-sticky-col {
  z-index: 4;
}

/* 左側固定列の幅とオフセット（8列固定） */
.sc-line-col {
  width: 90px;
  min-width: 90px;
  left: 0;
}
.sc-order-col {
  width: 110px;
  min-width: 110px;
  left: 90px;
}
.sc-item-col {
  width: 260px;
  min-width: 260px;
  left: 200px;
}
.sc-adjust-col {
  width: 120px;
  min-width: 120px;
  left: 460px;
}
.sc-material-col {
  width: 170px;
  min-width: 170px;
  left: 580px;
}
.sc-setup-col {
  width: 130px;
  min-width: 130px;
  left: 750px;
}
.sc-eff-col {
  width: 110px;
  min-width: 110px;
  left: 880px;
}
.sc-total-col {
  width: 140px;
  min-width: 140px;
  left: 990px;
}

.matrix-table tbody .sc-sticky-col {
  background: inherit;
}

.numeric-cell {
  text-align: center;
}

.cell-empty {
  color: #cbd5e0;
  text-align: center;
}

.sc-group-header-row {
  background-color: #e3f2fd;
  font-weight: 750;
}

.sc-line-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: flex-start;
}

.sc-line-code {
  color: #0f172a;
}

.sc-rate {
  font-size: 10px;
  color: #1d4ed8;
  font-weight: 800;
}

.sc-item-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sc-item-name {
  font-weight: 650;
  color: #0f172a;
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sc-flag {
  font-size: 9px;
  color: #b91c1c;
  font-weight: 800;
}

/* 色の基調（スクリーンショットの赤/緑のブロックに近似） */
.tone-active {
  background: rgba(220, 252, 231, 0.85);
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
  outline: 2px solid rgba(245, 158, 11, 0.9);
  outline-offset: -2px;
}

/* 周末/当日（カラー強調） */
.matrix-table thead th.is-weekend .date-text,
.matrix-table thead th.is-weekend .weekday-text {
  color: #e53e3e;
}

.matrix-table thead th.is-today {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
}

.matrix-table thead th.is-today .date-text,
.matrix-table thead th.is-today .weekday-text {
  color: #92400e;
  font-weight: 850;
}

/* フッター合計行 */
.sc-total-footer-row td {
  background: #f7fafc !important;
  font-weight: 800;
  border-top: 2px solid #cbd5e0;
  position: sticky;
  bottom: 0;
  z-index: 3;
}

.sc-total-footer-row .sc-sticky-col {
  z-index: 5;
}
</style>

