<template>
  <div class="pmp-page">
    <!-- ツールバー -->
    <header class="pmp-toolbar">
      <div class="pmp-toolbar__lead">
        <h1 class="pmp-toolbar__title">工程別設備別計画</h1>
        <span class="pmp-toolbar__period">{{ periodLabel }}</span>
      </div>
      <div class="pmp-toolbar__filters">
        <el-date-picker
          v-model="periodRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          format="YYYY/MM/DD"
          range-separator="～"
          start-placeholder="開始日"
          end-placeholder="終了日"
          size="small"
          class="pmp-toolbar__range"
          :clearable="false"
          :shortcuts="periodRangeShortcuts"
        />
        <el-select
          v-model="selectedProcesses"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="全工程"
          size="small"
          class="pmp-toolbar__process"
        >
          <el-option
            v-for="p in allProcessOptions"
            :key="p.key"
            :label="p.label"
            :value="p.key"
          />
        </el-select>
        <el-select
          v-model="selectedMachines"
          multiple
          filterable
          clearable
          collapse-tags
          collapse-tags-tooltip
          :max-collapse-tags="2"
          placeholder="設備で絞込"
          size="small"
          class="pmp-toolbar__keyword"
          :prefix-icon="Search"
          no-data-text="設備データがありません"
          no-match-text="一致する設備がありません"
        >
          <el-option-group
            v-for="grp in machineOptionGroups"
            :key="grp.key"
            :label="grp.label"
          >
            <el-option
              v-for="m in grp.machines"
              :key="`${grp.key}__${m}`"
              :label="m"
              :value="m"
            />
          </el-option-group>
        </el-select>
        <div class="pmp-toolbar__actions">
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button value="summary">対比集計</el-radio-button>
            <el-radio-button value="daily">日別明細</el-radio-button>
            <el-radio-button value="trend">達成率トレンド</el-radio-button>
          </el-radio-group>
          <el-button
            type="primary"
            size="small"
            :loading="loading"
            :icon="Refresh"
            @click="loadData"
          >
            更新
          </el-button>
          <el-button
            type="success"
            plain
            size="small"
            :icon="Download"
            :disabled="loading || filteredSummary.length === 0"
            @click="exportExcel"
          >
            Excel出力
          </el-button>
        </div>
      </div>
    </header>

    <!-- 概要カード -->
    <section class="pmp-cards">
      <div class="pmp-card pmp-card--plan">
        <span class="pmp-card__icon"><el-icon><Histogram /></el-icon></span>
        <div class="pmp-card__body">
          <span class="pmp-card__label">計画合計</span>
          <span class="pmp-card__value">{{ fmt(grandTotal.plan) }}</span>
        </div>
      </div>
      <div class="pmp-card pmp-card--actual">
        <span class="pmp-card__icon"><el-icon><CircleCheckFilled /></el-icon></span>
        <div class="pmp-card__body">
          <span class="pmp-card__label">実績合計</span>
          <span class="pmp-card__value">{{ fmt(grandTotal.actual) }}</span>
        </div>
      </div>
      <div class="pmp-card" :class="grandTotal.diff >= 0 ? 'pmp-card--up' : 'pmp-card--down'">
        <span class="pmp-card__icon">
          <el-icon><component :is="grandTotal.diff >= 0 ? Top : Bottom" /></el-icon>
        </span>
        <div class="pmp-card__body">
          <span class="pmp-card__label">差異（実績-計画）</span>
          <span class="pmp-card__value">{{ signed(grandTotal.diff) }}</span>
        </div>
      </div>
      <div class="pmp-card pmp-card--rate">
        <span class="pmp-card__icon"><el-icon><TrendCharts /></el-icon></span>
        <div class="pmp-card__body">
          <span class="pmp-card__label">達成率</span>
          <span class="pmp-card__value" :class="achievementClass(grandTotal.achievement_rate)">{{ rateText(grandTotal.achievement_rate) }}</span>
        </div>
      </div>
      <div class="pmp-card pmp-card--defect">
        <span class="pmp-card__icon"><el-icon><WarningFilled /></el-icon></span>
        <div class="pmp-card__body">
          <span class="pmp-card__label">不良率</span>
          <span class="pmp-card__value">{{ rateText(grandTotal.defect_rate) }}</span>
        </div>
      </div>
    </section>

    <!-- 対比集計 -->
    <div v-show="viewMode === 'summary'" v-loading="loading" class="pmp-table-shell">
      <div class="pmp-daily-bar">
        <span class="pmp-daily-bar__hint">設備行をダブルクリックすると製品別明細を表示します</span>
      </div>
      <el-table
        :data="summaryTableData"
        border
        size="small"
        class="pmp-table"
        empty-text="データがありません"
        :row-class-name="summaryRowClass"
        :span-method="summarySpanMethod"
        height="100%"
        @row-dblclick="onRowDblclick"
      >
        <el-table-column prop="process_label" label="工程" width="92" fixed="left" />
        <el-table-column prop="machine" label="設備" min-width="150" fixed="left">
          <template #default="{ row }">
            <span :class="{ 'pmp-subtotal-label': row.__type !== 'machine' }">{{ row.machine }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="plan" label="計画" width="92" align="right">
          <template #default="{ row }"><span class="pmp-num">{{ fmt(row.plan) }}</span></template>
        </el-table-column>
        <el-table-column prop="actual" label="実績" width="92" align="right">
          <template #default="{ row }"><span class="pmp-num">{{ fmt(row.actual) }}</span></template>
        </el-table-column>
        <el-table-column prop="diff" label="差異" width="92" align="right">
          <template #default="{ row }">
            <span class="pmp-num" :class="diffClass(row.diff)">{{ signed(row.diff) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="achievement_rate" label="達成率" width="96" align="right">
          <template #default="{ row }">
            <span class="pmp-rate" :class="achievementClass(row.achievement_rate)">
              {{ rateText(row.achievement_rate) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="actual_plan" label="実計" width="90" align="right">
          <template #default="{ row }"><span class="pmp-num pmp-num--muted">{{ fmt(row.actual_plan) }}</span></template>
        </el-table-column>
        <el-table-column prop="defect" label="不良" width="80" align="right">
          <template #default="{ row }"><span class="pmp-num pmp-num--muted">{{ fmt(row.defect) }}</span></template>
        </el-table-column>
        <el-table-column prop="scrap" label="廃棄" width="80" align="right">
          <template #default="{ row }"><span class="pmp-num pmp-num--muted">{{ fmt(row.scrap) }}</span></template>
        </el-table-column>
        <el-table-column prop="defect_rate" label="不良率" width="90" align="right">
          <template #default="{ row }">
            <span class="pmp-rate" :class="{ 'pmp-rate--warn': (row.defect_rate ?? 0) >= 3 }">
              {{ rateText(row.defect_rate) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="days" label="稼働日" width="76" align="right">
          <template #default="{ row }"><span class="pmp-num pmp-num--muted">{{ row.days || 0 }}</span></template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 日別明細 -->
    <div v-show="viewMode === 'daily'" v-loading="loading" class="pmp-table-shell">
      <div class="pmp-daily-bar">
        <span class="pmp-daily-bar__label">表示指標</span>
        <el-radio-group v-model="dailyMetric" size="small">
          <el-radio-button value="plan">計画</el-radio-button>
          <el-radio-button value="actual">実績</el-radio-button>
          <el-radio-button value="diff">差異</el-radio-button>
        </el-radio-group>
        <span class="pmp-daily-bar__hint">セルは選択中の指標値（0 は空白表示）。設備行ダブルクリックで製品別明細</span>
      </div>
      <el-table
        :data="dailyTableData"
        border
        size="small"
        class="pmp-table pmp-table--daily"
        empty-text="データがありません"
        :row-class-name="summaryRowClass"
        :span-method="summarySpanMethod"
        height="100%"
        @row-dblclick="onRowDblclick"
      >
        <el-table-column prop="process_label" label="工程" width="84" fixed="left" />
        <el-table-column prop="machine" label="設備" min-width="140" fixed="left">
          <template #default="{ row }">
            <span :class="{ 'pmp-subtotal-label': row.__type !== 'machine' }">{{ row.machine }}</span>
          </template>
        </el-table-column>
        <el-table-column
          v-for="d in dates"
          :key="d"
          :label="formatDateLabel(d)"
          min-width="56"
          align="right"
          class-name="pmp-daycol"
        >
          <template #default="{ row }">
            <span class="pmp-num" :class="dailyCellClass(row, d)">{{ dailyCellText(row, d) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="__rowTotal" label="合計" width="84" align="right" fixed="right">
          <template #default="{ row }">
            <span class="pmp-num pmp-num--total">{{ signedIfDiff(row.__rowTotal) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 達成率トレンド -->
    <div v-show="viewMode === 'trend'" v-loading="loading" class="pmp-table-shell">
      <div class="pmp-daily-bar">
        <span class="pmp-daily-bar__label">集計単位</span>
        <el-radio-group v-model="trendGroup" size="small">
          <el-radio-button value="all">全工程合計</el-radio-button>
          <el-radio-button value="process">工程別</el-radio-button>
        </el-radio-group>
        <span class="pmp-daily-bar__hint">棒＝計画/実績（左軸）、折線＝達成率%（右軸）</span>
      </div>
      <div ref="trendChartRef" class="pmp-trend-chart"></div>
    </div>

    <!-- 製品別ドリルダウン -->
    <el-dialog
      v-model="drillVisible"
      :title="drillTitle"
      width="860px"
      top="6vh"
      class="pmp-drill-dialog"
      append-to-body
    >
      <div v-if="drillData" class="pmp-drill-summary">
        <span>計画 <b>{{ fmt(drillData.total.plan) }}</b></span>
        <span>実績 <b>{{ fmt(drillData.total.actual) }}</b></span>
        <span>差異 <b :class="diffClass(drillData.total.diff)">{{ signed(drillData.total.diff) }}</b></span>
        <span>達成率 <b :class="achievementClass(drillData.total.achievement_rate)">{{ rateText(drillData.total.achievement_rate) }}</b></span>
        <span>品目 <b>{{ drillData.products.length }}</b> 件</span>
      </div>
      <el-table
        v-loading="drillLoading"
        :data="drillData?.products ?? []"
        border
        stripe
        size="small"
        height="56vh"
        empty-text="該当する製品がありません"
      >
        <el-table-column type="index" label="#" width="48" align="center" />
        <el-table-column prop="product_cd" label="製品CD" width="120" show-overflow-tooltip />
        <el-table-column prop="product_name" label="製品名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="plan" label="計画" width="92" align="right" sortable>
          <template #default="{ row }"><span class="pmp-num">{{ fmt(row.plan) }}</span></template>
        </el-table-column>
        <el-table-column prop="actual" label="実績" width="92" align="right" sortable>
          <template #default="{ row }"><span class="pmp-num">{{ fmt(row.actual) }}</span></template>
        </el-table-column>
        <el-table-column prop="diff" label="差異" width="92" align="right" sortable>
          <template #default="{ row }"><span class="pmp-num" :class="diffClass(row.diff)">{{ signed(row.diff) }}</span></template>
        </el-table-column>
        <el-table-column prop="achievement_rate" label="達成率" width="96" align="right" sortable>
          <template #default="{ row }">
            <span class="pmp-rate" :class="achievementClass(row.achievement_rate)">{{ rateText(row.achievement_rate) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="defect" label="不良" width="80" align="right">
          <template #default="{ row }"><span class="pmp-num pmp-num--muted">{{ fmt(row.defect) }}</span></template>
        </el-table-column>
        <el-table-column prop="scrap" label="廃棄" width="80" align="right">
          <template #default="{ row }"><span class="pmp-num pmp-num--muted">{{ fmt(row.scrap) }}</span></template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button size="small" :icon="Download" :disabled="!drillData || drillData.products.length === 0" @click="exportDrillExcel">
          Excel出力
        </el-button>
        <el-button size="small" type="primary" @click="drillVisible = false">閉じる</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Download,
  Search,
  Histogram,
  CircleCheckFilled,
  TrendCharts,
  WarningFilled,
  Top,
  Bottom,
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import {
  getProcessMachinePlan,
  getProcessMachinePlanProducts,
  type ProcessMachineMetrics,
  type ProcessMachinePlanData,
  type ProcessMachinePlanKey,
  type ProcessMachinePlanRow,
  type ProcessMachineProductsData,
} from '@/api/database'
import { downloadExcelFromAoa } from '@/utils/excelExport'

type ViewMode = 'summary' | 'daily' | 'trend'
type DailyMetric = 'plan' | 'actual' | 'diff'
type TrendGroup = 'all' | 'process'

interface TableRow extends Partial<ProcessMachinePlanRow> {
  __type: 'machine' | 'subtotal' | 'grand'
  __key: string
  process_label: string
  machine: string
  plan: number
  actual: number
  actual_plan: number
  defect: number
  scrap: number
  diff: number
  achievement_rate: number | null
  defect_rate: number | null
  days: number
  /** 日別マトリクス用：日付 → 指標値 */
  __daily?: Record<string, number>
  __rowTotal?: number
}

const ALL_PROCESSES: { key: ProcessMachinePlanKey; label: string }[] = [
  { key: 'cutting', label: '切断' },
  { key: 'chamfering', label: '面取' },
  { key: 'molding', label: '成型' },
  { key: 'plating', label: 'メッキ' },
  { key: 'welding', label: '溶接' },
  { key: 'inspection', label: '検査' },
  { key: 'outsourced_plating', label: '外注メッキ' },
  { key: 'outsourced_welding', label: '外注溶接' },
]
const allProcessOptions = ALL_PROCESSES

function monthStartEnd(ym: string): { startDate: string; endDate: string } {
  const [yearStr, monthStr] = ym.split('-')
  const year = Number(yearStr)
  const month = Number(monthStr)
  const first = new Date(year, month - 1, 1)
  const last = new Date(year, month, 0)
  const fmtD = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  return { startDate: fmtD(first), endDate: fmtD(last) }
}

function initialPeriodRange(): [string, string] {
  const d = new Date()
  const ym = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  const { startDate, endDate } = monthStartEnd(ym)
  return [startDate, endDate]
}

const periodRange = ref<[string, string]>(initialPeriodRange())
const selectedProcesses = ref<ProcessMachinePlanKey[]>([])
const selectedMachines = ref<string[]>([])
const viewMode = ref<ViewMode>('summary')
const dailyMetric = ref<DailyMetric>('actual')
const trendGroup = ref<TrendGroup>('all')
const loading = ref(false)

// ドリルダウン（製品別明細）
const drillVisible = ref(false)
const drillLoading = ref(false)
const drillData = ref<ProcessMachineProductsData | null>(null)
const drillTitle = ref('製品別明細')

// 達成率トレンドチャート
const trendChartRef = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null

const planData = ref<ProcessMachinePlanData | null>(null)
const dates = computed(() => planData.value?.dates ?? [])

const emptyMetrics: ProcessMachineMetrics = {
  plan: 0,
  actual: 0,
  actual_plan: 0,
  defect: 0,
  scrap: 0,
  diff: 0,
  achievement_rate: null,
  defect_rate: null,
  days: 0,
}
const grandTotal = computed<ProcessMachineMetrics>(() => planData.value?.grandTotal ?? emptyMetrics)

const periodRangeShortcuts = [
  {
    text: '今月',
    value: () => {
      const d = new Date()
      const ym = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
      const { startDate, endDate } = monthStartEnd(ym)
      return [new Date(startDate), new Date(endDate)] as [Date, Date]
    },
  },
  {
    text: '先月',
    value: () => {
      const d = new Date()
      d.setMonth(d.getMonth() - 1)
      const ym = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
      const { startDate, endDate } = monthStartEnd(ym)
      return [new Date(startDate), new Date(endDate)] as [Date, Date]
    },
  },
]

const periodLabel = computed(() => {
  const [a, b] = periodRange.value ?? []
  if (!a || !b) return ''
  const fmtLabel = (iso: string) => {
    const [y, m, d] = iso.split('-').map(Number)
    if (!y || !m || !d) return iso
    return `${y}年${m}月${d}日`
  }
  return `${fmtLabel(a)} ～ ${fmtLabel(b)}`
})

/** 設備ドロップダウン選択肢（工程ごとにグループ化。設備名はグローバルに一意化） */
const machineOptionGroups = computed<{ key: string; label: string; machines: string[] }[]>(() => {
  const data = planData.value
  if (!data) return []
  const seen = new Set<string>()
  const groups: { key: string; label: string; machines: string[] }[] = []
  for (const proc of data.processes) {
    const machines: string[] = []
    for (const r of data.summary) {
      if (r.process_key !== proc.key) continue
      const name = r.machine ?? ''
      if (!name || seen.has(name)) continue
      seen.add(name)
      machines.push(name)
    }
    machines.sort((a, b) => a.localeCompare(b, 'ja'))
    if (machines.length > 0) {
      groups.push({ key: proc.key, label: proc.label, machines })
    }
  }
  return groups
})

/** 設備選択で絞り込んだ summary 行 */
const filteredSummary = computed<ProcessMachinePlanRow[]>(() => {
  const rows = planData.value?.summary ?? []
  const sel = selectedMachines.value
  if (!sel.length) return rows
  const set = new Set(sel)
  return rows.filter((r) => set.has(r.machine ?? ''))
})

const DAY_OF_WEEK_JA = ['日', '月', '火', '水', '木', '金', '土']
function formatDateLabel(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  if (!y || !m || !d) return iso
  const w = DAY_OF_WEEK_JA[new Date(y, m - 1, d).getDay()] ?? ''
  return `${m}/${d}(${w})`
}

function fmt(v: number | null | undefined): string {
  const n = Number(v ?? 0)
  if (!Number.isFinite(n) || n === 0) return '0'
  return n.toLocaleString('ja-JP')
}
function signed(v: number | null | undefined): string {
  const n = Number(v ?? 0)
  if (!Number.isFinite(n) || n === 0) return '0'
  return (n > 0 ? '+' : '') + n.toLocaleString('ja-JP')
}
function signedIfDiff(v: number | null | undefined): string {
  return dailyMetric.value === 'diff' ? signed(v) : fmt(v)
}
function rateText(v: number | null | undefined): string {
  if (v === null || v === undefined) return '-'
  return `${v.toFixed(1)}%`
}

function diffClass(v: number): string {
  if (v > 0) return 'pmp-num--pos'
  if (v < 0) return 'pmp-num--neg'
  return ''
}
function achievementClass(v: number | null): string {
  if (v === null || v === undefined) return ''
  if (v >= 100) return 'pmp-rate--good'
  if (v < 80) return 'pmp-rate--bad'
  return 'pmp-rate--mid'
}

/** subtotal / grand 行のスタイル付け */
function summaryRowClass({ row }: { row: TableRow }): string {
  if (row.__type === 'grand') return 'pmp-row-grand'
  if (row.__type === 'subtotal') return 'pmp-row-subtotal'
  return 'pmp-row-machine'
}

/** subtotal / grand 行は「工程」「設備」列をまとめる */
function summarySpanMethod({
  row,
  columnIndex,
}: {
  row: TableRow
  columnIndex: number
}) {
  if (row.__type === 'grand') {
    if (columnIndex === 0) return { rowspan: 1, colspan: 2 }
    if (columnIndex === 1) return { rowspan: 0, colspan: 0 }
  }
  return { rowspan: 1, colspan: 1 }
}

/** 工程ごとに 設備行 → 小計行、最後に総合計行を積む（対比集計用） */
const summaryTableData = computed<TableRow[]>(() => {
  const data = planData.value
  if (!data) return []
  const rows: TableRow[] = []
  for (const proc of data.processes) {
    const machineRows = filteredSummary.value.filter((r) => r.process_key === proc.key)
    if (machineRows.length === 0) continue
    for (const r of machineRows) {
      rows.push({
        __type: 'machine',
        __key: `${proc.key}__${r.machine}`,
        process_label: r.process_label,
        machine: r.machine,
        plan: r.plan,
        actual: r.actual,
        actual_plan: r.actual_plan,
        defect: r.defect,
        scrap: r.scrap,
        diff: r.diff,
        achievement_rate: r.achievement_rate,
        defect_rate: r.defect_rate,
        days: r.days,
      })
    }
    rows.push(buildSubtotal(proc.key, proc.label, machineRows))
  }
  if (rows.length > 0) rows.push(buildGrandRow())
  return rows
})

function aggregate(rows: ProcessMachinePlanRow[]): ProcessMachineMetrics {
  const acc = { plan: 0, actual: 0, actual_plan: 0, defect: 0, scrap: 0 }
  let days = 0
  for (const r of rows) {
    acc.plan += r.plan
    acc.actual += r.actual
    acc.actual_plan += r.actual_plan
    acc.defect += r.defect
    acc.scrap += r.scrap
    days = Math.max(days, r.days)
  }
  const diff = acc.actual - acc.plan
  const achievement_rate = acc.plan > 0 ? round1((acc.actual / acc.plan) * 100) : null
  const defectBase = acc.actual + acc.defect + acc.scrap
  const defect_rate = defectBase > 0 ? round1(((acc.defect + acc.scrap) / defectBase) * 100) : null
  return { ...acc, diff, achievement_rate, defect_rate, days }
}
function round1(v: number): number {
  return Math.round(v * 10) / 10
}

function buildSubtotal(
  key: ProcessMachinePlanKey,
  label: string,
  rows: ProcessMachinePlanRow[],
): TableRow {
  const m = aggregate(rows)
  return {
    __type: 'subtotal',
    __key: `${key}__subtotal`,
    process_label: label,
    machine: '小計',
    ...m,
  }
}

function buildGrandRow(): TableRow {
  const m = aggregate(filteredSummary.value)
  return {
    __type: 'grand',
    __key: 'grand',
    process_label: '合計',
    machine: '',
    ...m,
  }
}

/* ============ 日別明細 ============ */
function dailyValue(r: ProcessMachinePlanRow, d: string): number {
  const cell = r.daily?.[d]
  if (!cell) return 0
  return Number(cell[dailyMetric.value] ?? 0)
}

const dailyTableData = computed<TableRow[]>(() => {
  const data = planData.value
  if (!data) return []
  const ds = data.dates
  const rows: TableRow[] = []
  for (const proc of data.processes) {
    const machineRows = filteredSummary.value.filter((r) => r.process_key === proc.key)
    if (machineRows.length === 0) continue
    const subDaily: Record<string, number> = {}
    let subTotal = 0
    for (const r of machineRows) {
      const daily: Record<string, number> = {}
      let rowTotal = 0
      for (const d of ds) {
        const v = dailyValue(r, d)
        daily[d] = v
        rowTotal += v
        subDaily[d] = (subDaily[d] ?? 0) + v
      }
      subTotal += rowTotal
      rows.push({
        __type: 'machine',
        __key: `${proc.key}__${r.machine}__daily`,
        process_label: r.process_label,
        machine: r.machine,
        plan: r.plan,
        actual: r.actual,
        actual_plan: r.actual_plan,
        defect: r.defect,
        scrap: r.scrap,
        diff: r.diff,
        achievement_rate: r.achievement_rate,
        defect_rate: r.defect_rate,
        days: r.days,
        __daily: daily,
        __rowTotal: rowTotal,
      })
    }
    rows.push({
      __type: 'subtotal',
      __key: `${proc.key}__subtotal__daily`,
      process_label: proc.label,
      machine: '小計',
      ...aggregate(machineRows),
      __daily: subDaily,
      __rowTotal: subTotal,
    })
  }
  return rows
})

function dailyCellText(row: TableRow, d: string): string {
  const v = Number(row.__daily?.[d] ?? 0)
  if (v === 0) return ''
  return dailyMetric.value === 'diff' ? signed(v) : fmt(v)
}
function dailyCellClass(row: TableRow, d: string): string {
  const v = Number(row.__daily?.[d] ?? 0)
  if (dailyMetric.value === 'diff') return diffClass(v)
  return ''
}

/* ============ ドリルダウン（製品別明細） ============ */
async function onRowDblclick(row: TableRow) {
  if (row.__type !== 'machine') return
  const proc = planData.value?.processes.find((p) => p.label === row.process_label)
  if (!proc) return
  const [startDate, endDate] = periodRange.value ?? []
  if (!startDate || !endDate) return
  drillTitle.value = `製品別明細 — ${row.process_label} / ${row.machine}`
  drillVisible.value = true
  drillLoading.value = true
  drillData.value = null
  try {
    const res = await getProcessMachinePlanProducts({
      startDate,
      endDate,
      process: proc.key,
      machine: row.machine,
    })
    drillData.value = (res as any)?.data ?? null
  } catch (e) {
    console.error('製品別明細の読み込みに失敗しました', e)
    ElMessage.error('製品別明細の読み込みに失敗しました')
    drillVisible.value = false
  } finally {
    drillLoading.value = false
  }
}

async function exportDrillExcel() {
  const d = drillData.value
  if (!d || d.products.length === 0) return
  const header = ['製品CD', '製品名', '計画', '実績', '差異', '達成率(%)', '実計', '不良', '廃棄', '不良率(%)']
  const aoa: (string | number)[][] = [header]
  for (const p of d.products) {
    aoa.push([
      p.product_cd,
      p.product_name ?? '',
      p.plan,
      p.actual,
      p.diff,
      p.achievement_rate ?? '',
      p.actual_plan,
      p.defect,
      p.scrap,
      p.defect_rate ?? '',
    ])
  }
  try {
    await downloadExcelFromAoa(
      aoa,
      '製品別明細',
      `工程別設備別計画_${d.process_label}_${d.machine}_${d.startDate}_${d.endDate}.xlsx`,
    )
    ElMessage.success('Excel を出力しました')
  } catch (err) {
    console.error('Excel 出力に失敗しました', err)
    ElMessage.error('Excel 出力に失敗しました')
  }
}

/* ============ 達成率トレンドチャート ============ */
function buildTrendOption(): EChartsOption {
  const data = planData.value
  const ds = data?.dates ?? []
  const rows = filteredSummary.value
  const axisLabels = ds.map((d) => formatDateLabel(d))

  // 全工程合計：日付ごとに plan/actual を合算 → 達成率
  if (trendGroup.value === 'all') {
    const planByDate: number[] = []
    const actualByDate: number[] = []
    const rateByDate: (number | null)[] = []
    for (const d of ds) {
      let plan = 0
      let actual = 0
      for (const r of rows) {
        const cell = r.daily?.[d]
        if (cell) {
          plan += cell.plan
          actual += cell.actual
        }
      }
      planByDate.push(plan)
      actualByDate.push(actual)
      rateByDate.push(plan > 0 ? round1((actual / plan) * 100) : null)
    }
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['計画', '実績', '達成率'], top: 0 },
      grid: { left: 50, right: 56, top: 36, bottom: 48 },
      xAxis: { type: 'category', data: axisLabels, axisLabel: { fontSize: 10, rotate: ds.length > 20 ? 45 : 0 } },
      yAxis: [
        { type: 'value', name: '数量' },
        { type: 'value', name: '%', min: 0, axisLabel: { formatter: '{value}%' } },
      ],
      series: [
        { name: '計画', type: 'bar', data: planByDate, itemStyle: { color: '#a5c8f5' } },
        { name: '実績', type: 'bar', data: actualByDate, itemStyle: { color: '#67c23a' } },
        {
          name: '達成率',
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          connectNulls: true,
          data: rateByDate,
          itemStyle: { color: '#9254de' },
          lineStyle: { width: 2 },
        },
      ],
    }
  }

  // 工程別：工程ごとの達成率折線（日付別）
  const series: EChartsOption['series'] = []
  const legend: string[] = []
  for (const proc of data?.processes ?? []) {
    const procRows = rows.filter((r) => r.process_key === proc.key)
    if (procRows.length === 0) continue
    const rateByDate: (number | null)[] = ds.map((d) => {
      let plan = 0
      let actual = 0
      for (const r of procRows) {
        const cell = r.daily?.[d]
        if (cell) {
          plan += cell.plan
          actual += cell.actual
        }
      }
      return plan > 0 ? round1((actual / plan) * 100) : null
    })
    legend.push(proc.label)
    ;(series as any[]).push({
      name: proc.label,
      type: 'line',
      smooth: true,
      connectNulls: true,
      data: rateByDate,
    })
  }
  return {
    tooltip: { trigger: 'axis', valueFormatter: (v: any) => (v == null ? '-' : `${v}%`) },
    legend: { data: legend, top: 0, type: 'scroll' },
    grid: { left: 50, right: 24, top: 36, bottom: 48 },
    xAxis: { type: 'category', data: axisLabels, axisLabel: { fontSize: 10, rotate: ds.length > 20 ? 45 : 0 } },
    yAxis: { type: 'value', name: '達成率%', axisLabel: { formatter: '{value}%' } },
    series,
  }
}

function syncTrendChart() {
  if (viewMode.value !== 'trend') return
  nextTick(() => {
    const el = trendChartRef.value
    if (!el || el.clientWidth <= 0) return
    if (!trendChart) trendChart = echarts.init(el, undefined, { renderer: 'canvas' })
    trendChart.setOption(buildTrendOption(), true)
    trendChart.resize()
  })
}

function onWindowResize() {
  trendChart?.resize()
}

watch([viewMode, trendGroup, planData, selectedMachines], () => {
  syncTrendChart()
})

/* ============ データ取得 ============ */
async function loadData() {
  const [startDate, endDate] = periodRange.value ?? []
  if (!startDate || !endDate) {
    ElMessage.warning('期間を選択してください')
    return
  }
  loading.value = true
  try {
    const res = await getProcessMachinePlan({
      startDate,
      endDate,
      processes: selectedProcesses.value.length ? selectedProcesses.value.join(',') : undefined,
    })
    planData.value = (res as any)?.data ?? null
  } catch (e) {
    console.error('工程別設備別計画の読み込みに失敗しました', e)
    ElMessage.error('読み込みに失敗しました')
    planData.value = null
  } finally {
    loading.value = false
  }
}

/* ============ Excel 出力 ============ */
async function exportExcel() {
  const data = planData.value
  if (!data) return
  const [s, e] = periodRange.value ?? []
  try {
    if (viewMode.value === 'summary') {
      const header = ['工程', '設備', '計画', '実績', '差異', '達成率(%)', '実計', '不良', '廃棄', '不良率(%)', '稼働日']
      const aoa: (string | number)[][] = [header]
      for (const row of summaryTableData.value) {
        aoa.push([
          row.process_label,
          row.machine,
          row.plan,
          row.actual,
          row.diff,
          row.achievement_rate ?? '',
          row.actual_plan,
          row.defect,
          row.scrap,
          row.defect_rate ?? '',
          row.days,
        ])
      }
      await downloadExcelFromAoa(aoa, '対比集計', `工程別設備別計画_対比_${s}_${e}.xlsx`)
    } else {
      const metricLabel = dailyMetric.value === 'plan' ? '計画' : dailyMetric.value === 'actual' ? '実績' : '差異'
      const header = ['工程', '設備', ...data.dates.map((d) => formatDateLabel(d)), '合計']
      const aoa: (string | number)[][] = [header]
      for (const row of dailyTableData.value) {
        aoa.push([
          row.process_label,
          row.machine,
          ...data.dates.map((d) => Number(row.__daily?.[d] ?? 0)),
          Number(row.__rowTotal ?? 0),
        ])
      }
      await downloadExcelFromAoa(aoa, `日別_${metricLabel}`, `工程別設備別計画_日別${metricLabel}_${s}_${e}.xlsx`)
    }
    ElMessage.success('Excel を出力しました')
  } catch (err) {
    console.error('Excel 出力に失敗しました', err)
    ElMessage.error('Excel 出力に失敗しました')
  }
}

watch(periodRange, () => {
  void loadData()
})
watch(selectedProcesses, () => {
  void loadData()
})

onMounted(() => {
  window.addEventListener('resize', onWindowResize)
  void loadData()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onWindowResize)
  trendChart?.dispose()
  trendChart = null
})
</script>

<style scoped>
.pmp-page {
  /* ── デザイントークン ── */
  --pmp-blue: #3b82f6;
  --pmp-green: #22c55e;
  --pmp-purple: #8b5cf6;
  --pmp-amber: #f59e0b;
  --pmp-red: #ef4444;
  --pmp-ink: #1e293b;
  --pmp-sub: #64748b;
  --pmp-line: #e8edf4;
  --pmp-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 16px rgba(15, 23, 42, 0.05);
  --pmp-shadow-hover: 0 6px 22px rgba(15, 23, 42, 0.1);

  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: 12px 14px 14px;
  box-sizing: border-box;
  gap: 10px;
  background: radial-gradient(1200px 500px at 12% -8%, #eef4ff 0%, transparent 55%),
    radial-gradient(1000px 480px at 110% 0%, #f2fbf5 0%, transparent 50%), #f4f6fb;
}

/* ── ツールバー ── */
.pmp-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px 18px;
  padding: 11px 16px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(8px);
  border: 1px solid var(--pmp-line);
  border-radius: 12px;
  box-shadow: var(--pmp-shadow);
}
.pmp-toolbar__lead {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.pmp-toolbar__title {
  position: relative;
  margin: 0;
  padding-left: 12px;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--pmp-ink);
  white-space: nowrap;
}
.pmp-toolbar__title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 18px;
  border-radius: 3px;
  background: linear-gradient(180deg, var(--pmp-blue), var(--pmp-purple));
}
.pmp-toolbar__period {
  font-size: 12px;
  color: var(--pmp-sub);
  white-space: nowrap;
  padding: 2px 10px;
  background: #f1f5fb;
  border-radius: 999px;
}
.pmp-toolbar__filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.pmp-toolbar__range {
  width: 240px;
}
.pmp-toolbar__process {
  width: 180px;
}
.pmp-toolbar__keyword {
  width: 210px;
}
.pmp-toolbar__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ── 概要カード ── */
.pmp-cards {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}
.pmp-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: #fff;
  border: 1px solid var(--pmp-line);
  border-radius: 12px;
  box-shadow: var(--pmp-shadow);
  overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.pmp-card::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--pmp-accent, #c0c4cc);
}
.pmp-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--pmp-shadow-hover);
}
.pmp-card__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 11px;
  font-size: 20px;
  color: var(--pmp-accent, #909399);
  background: var(--pmp-accent-soft, #f0f2f5);
  flex-shrink: 0;
}
.pmp-card__body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.pmp-card__label {
  font-size: 12px;
  color: var(--pmp-sub);
  white-space: nowrap;
}
.pmp-card__value {
  font-size: 22px;
  line-height: 1.1;
  font-weight: 800;
  color: var(--pmp-ink);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.01em;
}
.pmp-card--plan {
  --pmp-accent: var(--pmp-blue);
  --pmp-accent-soft: #e8f0fe;
}
.pmp-card--actual {
  --pmp-accent: var(--pmp-green);
  --pmp-accent-soft: #e6f8ec;
}
.pmp-card--rate {
  --pmp-accent: var(--pmp-purple);
  --pmp-accent-soft: #f0eafe;
}
.pmp-card--defect {
  --pmp-accent: var(--pmp-amber);
  --pmp-accent-soft: #fdf2e0;
}
.pmp-card--up {
  --pmp-accent: var(--pmp-green);
  --pmp-accent-soft: #e6f8ec;
}
.pmp-card--up .pmp-card__value {
  color: #16a34a;
}
.pmp-card--down {
  --pmp-accent: var(--pmp-red);
  --pmp-accent-soft: #fdeaea;
}
.pmp-card--down .pmp-card__value {
  color: #dc2626;
}

/* ── コンテンツシェル ── */
.pmp-table-shell {
  flex: 1;
  min-height: 0;
  background: #fff;
  border: 1px solid var(--pmp-line);
  border-radius: 12px;
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--pmp-shadow);
}
.pmp-table {
  flex: 1;
  min-height: 0;
}

/* バー（操作行 / ヒント） */
.pmp-daily-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 2px 10px;
}
.pmp-daily-bar__label {
  font-size: 12px;
  font-weight: 700;
  color: #475467;
  letter-spacing: 0.02em;
}
.pmp-daily-bar__hint {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  color: var(--pmp-sub);
  padding: 3px 10px;
  background: #f6f8fc;
  border: 1px dashed #d8e0ec;
  border-radius: 999px;
}
.pmp-trend-chart {
  flex: 1;
  min-height: 320px;
  width: 100%;
}

/* ── 数値・レート ── */
.pmp-num {
  font-variant-numeric: tabular-nums;
}
.pmp-num--muted {
  color: #94a3b8;
}
.pmp-num--pos {
  color: #16a34a;
  font-weight: 600;
}
.pmp-num--neg {
  color: #dc2626;
  font-weight: 600;
}
.pmp-num--total {
  font-weight: 700;
}
.pmp-rate {
  display: inline-block;
  min-width: 52px;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}
.pmp-rate--good {
  color: #16a34a;
}
.pmp-rate--mid {
  color: #d97706;
}
.pmp-rate--bad {
  color: #dc2626;
}
.pmp-rate--warn {
  color: #dc2626;
}
.pmp-subtotal-label {
  font-weight: 700;
  color: #475467;
}

/* ── ドリルダウンダイアログ ── */
.pmp-drill-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 2px 0 14px;
  font-size: 13px;
  color: var(--pmp-sub);
}
.pmp-drill-summary span {
  padding: 5px 12px;
  background: #f5f8fd;
  border: 1px solid var(--pmp-line);
  border-radius: 999px;
}
.pmp-drill-summary b {
  font-variant-numeric: tabular-nums;
  color: var(--pmp-ink);
  margin-left: 2px;
}

/* ── el-table 細部チューニング ── */
:deep(.pmp-table) {
  --el-table-border-color: #eef2f7;
  --el-table-header-text-color: #41506a;
  border-radius: 8px;
}
:deep(.pmp-table th.el-table__cell) {
  background: linear-gradient(180deg, #f7f9fd 0%, #eef2f9 100%);
  font-weight: 700;
}
:deep(.pmp-table .el-table__cell) {
  padding: 5px 0;
}
:deep(.pmp-table .el-table__row:hover > td.el-table__cell) {
  background: #f3f8ff !important;
}
:deep(.pmp-daycol .cell) {
  padding: 0 4px;
}
:deep(.pmp-row-subtotal) td.el-table__cell {
  background: #eff4fb !important;
  font-weight: 700;
}
:deep(.pmp-row-grand) td.el-table__cell {
  background: linear-gradient(180deg, #e7effb 0%, #dfe9f9 100%) !important;
  font-weight: 800;
  color: var(--pmp-ink);
}
:deep(.pmp-row-machine) {
  cursor: pointer;
}

/* セグメント / 入力の角丸を統一 */
:deep(.pmp-toolbar .el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 8px 0 0 8px;
}
:deep(.pmp-toolbar .el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 8px 8px 0;
}
:deep(.pmp-drill-dialog .el-dialog__header) {
  margin-right: 0;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--pmp-line);
}
:deep(.pmp-drill-dialog .el-dialog__title) {
  font-weight: 700;
  color: var(--pmp-ink);
}
</style>
