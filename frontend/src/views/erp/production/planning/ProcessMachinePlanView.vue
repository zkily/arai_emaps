<template>
  <div class="pmp-page">
    <!-- ツールバー（コンパクト・立体） -->
    <header class="pmp-toolbar">
      <div class="pmp-toolbar__brand">
        <h1 class="pmp-toolbar__title">工程別設備別計画</h1>
        <span class="pmp-toolbar__period">{{ periodLabel }}</span>
      </div>

      <div class="pmp-toolbar__body">
        <div class="pmp-toolbar__strip pmp-toolbar__strip--filter">
          <span class="pmp-toolbar__strip-label">条件</span>
          <el-date-picker
            v-model="periodRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            format="YYYY/MM/DD"
            range-separator="～"
            start-placeholder="開始"
            end-placeholder="終了"
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
            :max-collapse-tags="1"
            placeholder="設備"
            size="small"
            class="pmp-toolbar__machine"
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
        </div>

        <div class="pmp-toolbar__strip pmp-toolbar__strip--view">
          <el-radio-group v-model="viewMode" size="small" class="pmp-toolbar__view">
            <el-radio-button value="summary">対比集計</el-radio-button>
            <el-radio-button value="daily">日別明細</el-radio-button>
            <el-radio-button value="trend">達成率</el-radio-button>
          </el-radio-group>
        </div>

        <div class="pmp-toolbar__strip pmp-toolbar__strip--actions">
          <el-button
            type="primary"
            size="small"
            class="pmp-toolbar__btn pmp-toolbar__btn--primary"
            :loading="loading"
            :icon="Refresh"
            @click="loadData"
          >
            更新
          </el-button>
          <el-button
            size="small"
            class="pmp-toolbar__btn pmp-toolbar__btn--print"
            :icon="Printer"
            :disabled="printDisabled"
            @click="handlePrint"
          >
            印刷
          </el-button>
          <el-button
            size="small"
            class="pmp-toolbar__btn pmp-toolbar__btn--excel"
            :icon="Download"
            :disabled="loading || filteredSummary.length === 0"
            @click="exportExcel"
          >
            Excel
          </el-button>
        </div>
      </div>
    </header>

    <main class="pmp-main">
    <!-- 概要カード -->
    <section class="pmp-cards" aria-label="概要">
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
    <section v-show="viewMode === 'summary'" class="pmp-panel">
      <div class="pmp-panel__head">
        <span class="pmp-panel__title">対比集計</span>
        <span class="pmp-panel__hint">設備行ダブルクリック → 製品別明細</span>
      </div>
      <div v-loading="loading" class="pmp-panel__body">
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
        <el-table-column prop="process_label" label="工程" width="72" align="center" fixed="left" />
        <el-table-column prop="machine" label="設備" width="120" align="center" fixed="left" show-overflow-tooltip>
          <template #default="{ row }">
            <span :class="{ 'pmp-subtotal-label': row.__type !== 'machine' }">{{ row.machine }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="plan" label="計画" width="76" align="center">
          <template #default="{ row }"><span class="pmp-num">{{ fmt(row.plan) }}</span></template>
        </el-table-column>
        <el-table-column prop="actual" label="実績" width="76" align="center">
          <template #default="{ row }"><span class="pmp-num">{{ fmt(row.actual) }}</span></template>
        </el-table-column>
        <el-table-column prop="diff" label="差異" width="76" align="center">
          <template #default="{ row }">
            <span class="pmp-num" :class="diffClass(row.diff)">{{ signed(row.diff) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="achievement_rate" label="達成率" width="72" align="center">
          <template #default="{ row }">
            <span class="pmp-rate" :class="achievementClass(row.achievement_rate)">
              {{ rateText(row.achievement_rate) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="actual_plan" label="実計" width="72" align="center">
          <template #default="{ row }"><span class="pmp-num pmp-num--muted">{{ fmt(row.actual_plan) }}</span></template>
        </el-table-column>
        <el-table-column prop="defect" label="不良" width="64" align="center">
          <template #default="{ row }"><span class="pmp-num pmp-num--muted">{{ fmt(row.defect) }}</span></template>
        </el-table-column>
        <el-table-column prop="scrap" label="廃棄" width="64" align="center">
          <template #default="{ row }"><span class="pmp-num pmp-num--muted">{{ fmt(row.scrap) }}</span></template>
        </el-table-column>
        <el-table-column prop="defect_rate" label="不良率" width="72" align="center">
          <template #default="{ row }">
            <span class="pmp-rate" :class="{ 'pmp-rate--warn': (row.defect_rate ?? 0) >= 3 }">
              {{ rateText(row.defect_rate) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="days" label="稼働日" width="60" align="center">
          <template #default="{ row }"><span class="pmp-num pmp-num--muted">{{ row.days || 0 }}</span></template>
        </el-table-column>
      </el-table>
      </div>
    </section>

    <!-- 日別明細 -->
    <section v-show="viewMode === 'daily'" class="pmp-panel">
      <div class="pmp-panel__head">
        <span class="pmp-panel__title">日別明細</span>
        <span class="pmp-panel__label">指標</span>
        <el-radio-group v-model="dailyMetric" size="small" class="pmp-panel__seg">
          <el-radio-button value="plan">計画</el-radio-button>
          <el-radio-button value="actual">実績</el-radio-button>
          <el-radio-button value="diff">差異</el-radio-button>
        </el-radio-group>
        <span class="pmp-panel__hint">0 は「—」表示・設備行ダブルクリックで明細</span>
      </div>
      <div v-loading="loading" class="pmp-panel__body">
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
        <el-table-column prop="process_label" label="工程" width="68" align="center" fixed="left" />
        <el-table-column prop="machine" label="設備" width="108" align="center" fixed="left" show-overflow-tooltip>
          <template #default="{ row }">
            <span :class="{ 'pmp-subtotal-label': row.__type !== 'machine' }">{{ row.machine }}</span>
          </template>
        </el-table-column>
        <el-table-column
          v-for="d in dates"
          :key="d"
          :label="formatDateHeaderDate(d)"
          align="center"
          header-align="center"
          class-name="pmp-daycol-group"
        >
          <el-table-column
            :label="formatDateHeaderWeek(d)"
            :class-name="dailyWeekHeaderClass(d)"
            width="44"
            align="center"
            header-align="center"
          >
            <template #default="{ row }">
              <span class="pmp-num" :class="dailyCellClass(row, d)">{{ dailyCellText(row, d) }}</span>
            </template>
          </el-table-column>
        </el-table-column>
        <el-table-column prop="__rowTotal" label="合計" width="64" align="center" header-align="center" fixed="right">
          <template #default="{ row }">
            <span class="pmp-num pmp-num--total">{{ signedIfDiff(row.__rowTotal) }}</span>
          </template>
        </el-table-column>
      </el-table>
      </div>
    </section>

    <!-- 達成率トレンド -->
    <section v-show="viewMode === 'trend'" v-loading="loading" class="pmp-panel pmp-panel--trend">
      <div class="pmp-panel__head">
        <span class="pmp-panel__title">達成率トレンド</span>
        <span class="pmp-panel__label">集計</span>
        <el-radio-group v-model="trendGroup" size="small" class="pmp-panel__seg">
          <el-radio-button value="all">全工程合計</el-radio-button>
          <el-radio-button value="process">工程別</el-radio-button>
        </el-radio-group>
        <span class="pmp-panel__hint">棒＝計画/実績　折線＝達成率%</span>
      </div>
      <div class="pmp-panel__body pmp-panel__body--trend">

      <section v-if="trendStats" class="pmp-trend-kpis" aria-label="トレンド概要">
        <div class="pmp-trend-kpi pmp-trend-kpi--plan">
          <span class="pmp-trend-kpi__label">期間計画</span>
          <span class="pmp-trend-kpi__value">{{ fmt(trendStats.totalPlan) }}</span>
        </div>
        <div class="pmp-trend-kpi pmp-trend-kpi--actual">
          <span class="pmp-trend-kpi__label">期間実績</span>
          <span class="pmp-trend-kpi__value">{{ fmt(trendStats.totalActual) }}</span>
        </div>
        <div class="pmp-trend-kpi pmp-trend-kpi--avg">
          <span class="pmp-trend-kpi__label">平均達成率</span>
          <span class="pmp-trend-kpi__value" :class="achievementClass(trendStats.avgRate)">
            {{ rateText(trendStats.avgRate) }}
          </span>
        </div>
        <div class="pmp-trend-kpi pmp-trend-kpi--best">
          <span class="pmp-trend-kpi__label">最高日</span>
          <span class="pmp-trend-kpi__value pmp-trend-kpi__value--sm">
            {{ trendStats.best ? `${formatDateHeaderDate(trendStats.best.date)} ${rateText(trendStats.best.rate)}` : '—' }}
          </span>
        </div>
        <div class="pmp-trend-kpi pmp-trend-kpi--worst">
          <span class="pmp-trend-kpi__label">最低日</span>
          <span class="pmp-trend-kpi__value pmp-trend-kpi__value--sm">
            {{ trendStats.worst ? `${formatDateHeaderDate(trendStats.worst.date)} ${rateText(trendStats.worst.rate)}` : '—' }}
          </span>
        </div>
      </section>

      <div class="pmp-trend-chart-card">
        <div class="pmp-trend-chart-card__head">
          <span class="pmp-trend-chart-card__title">
            {{ trendGroup === 'all' ? '日別 計画・実績・達成率' : '工程別 日別達成率' }}
          </span>
          <span class="pmp-trend-chart-card__badge">100% 基準線あり</span>
        </div>
        <div ref="trendChartRef" class="pmp-trend-chart"></div>
      </div>

      <div v-if="trendDailyRows.length > 0" class="pmp-trend-table-card">
        <div class="pmp-trend-table-card__head">日別数値一覧</div>
        <el-table
          :data="trendGroup === 'all' ? trendDailyRows : trendProcessDayRows"
          border
          stripe
          size="small"
          class="pmp-trend-table"
          max-height="220"
        >
          <el-table-column label="日付" width="72" align="center" fixed="left">
            <template #default="{ row }">{{ formatDateHeaderDate(row.date) }}</template>
          </el-table-column>
          <el-table-column label="曜" width="44" align="center" fixed="left">
            <template #default="{ row }">
              <span :class="weekdayCellClass(row.date)">{{ formatDateHeaderWeek(row.date) }}</span>
            </template>
          </el-table-column>
          <template v-if="trendGroup === 'all'">
            <el-table-column prop="plan" label="計画" width="80" align="center">
              <template #default="{ row }"><span class="pmp-num">{{ fmt(row.plan) }}</span></template>
            </el-table-column>
            <el-table-column prop="actual" label="実績" width="80" align="center">
              <template #default="{ row }"><span class="pmp-num">{{ fmt(row.actual) }}</span></template>
            </el-table-column>
            <el-table-column prop="diff" label="差異" width="80" align="center">
              <template #default="{ row }">
                <span class="pmp-num" :class="diffClass(row.diff)">{{ signed(row.diff) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="rate" label="達成率" width="80" align="center">
              <template #default="{ row }">
                <span class="pmp-rate" :class="achievementClass(row.rate)">{{ rateText(row.rate) }}</span>
              </template>
            </el-table-column>
          </template>
          <template v-else>
            <el-table-column
              v-for="col in trendProcessColumns"
              :key="col.key"
              :label="col.label"
              width="72"
              align="center"
            >
              <template #default="{ row }">
                <span class="pmp-rate" :class="achievementClass(row.rates[col.key])">
                  {{ rateText(row.rates[col.key]) }}
                </span>
              </template>
            </el-table-column>
          </template>
        </el-table>
      </div>
      </div>
    </section>
    </main>

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
        class="pmp-drill-table"
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
        <el-button
          size="small"
          class="pmp-toolbar__btn pmp-toolbar__btn--excel"
          :icon="Download"
          :disabled="!drillData || drillData.products.length === 0"
          @click="exportDrillExcel"
        >
          Excel
        </el-button>
        <el-button size="small" class="pmp-toolbar__btn pmp-toolbar__btn--primary" @click="drillVisible = false">
          閉じる
        </el-button>
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
  Printer,
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

function parseIsoDate(iso: string): { y: number; m: number; d: number } | null {
  const [y, m, d] = iso.split('-').map(Number)
  if (!y || !m || !d) return null
  return { y, m, d }
}

/** 日別明細：表頭第1層（日付） */
function formatDateHeaderDate(iso: string): string {
  const p = parseIsoDate(iso)
  if (!p) return iso
  return `${p.m}/${p.d}`
}

/** 日別明細：表頭第2層（曜日） */
function formatDateHeaderWeek(iso: string): string {
  const p = parseIsoDate(iso)
  if (!p) return ''
  return DAY_OF_WEEK_JA[new Date(p.y, p.m - 1, p.d).getDay()] ?? ''
}

/** チャート軸ラベル等（日付+曜日1行） */
function formatDateLabel(iso: string): string {
  const p = parseIsoDate(iso)
  if (!p) return iso
  const w = DAY_OF_WEEK_JA[new Date(p.y, p.m - 1, p.d).getDay()] ?? ''
  return `${p.m}/${p.d}(${w})`
}

/** 土日の曜日セル用 */
function dailyWeekHeaderClass(iso: string): string {
  const p = parseIsoDate(iso)
  if (!p) return 'pmp-daycol'
  const dow = new Date(p.y, p.m - 1, p.d).getDay()
  if (dow === 0) return 'pmp-daycol pmp-daycol--sun'
  if (dow === 6) return 'pmp-daycol pmp-daycol--sat'
  return 'pmp-daycol'
}

function weekdayCellClass(iso: string): string {
  const p = parseIsoDate(iso)
  if (!p) return ''
  const dow = new Date(p.y, p.m - 1, p.d).getDay()
  if (dow === 0) return 'pmp-week--sun'
  if (dow === 6) return 'pmp-week--sat'
  return ''
}

/* ============ トレンド集計 ============ */
const TREND_PROCESS_COLORS = [
  '#3b82f6',
  '#22c55e',
  '#8b5cf6',
  '#f59e0b',
  '#ef4444',
  '#06b6d4',
  '#ec4899',
  '#64748b',
]

interface TrendDayAgg {
  date: string
  plan: number
  actual: number
  diff: number
  rate: number | null
}

interface TrendProcessDayRow {
  date: string
  rates: Record<string, number | null>
}

function sumDailyForDate(rows: ProcessMachinePlanRow[], d: string): { plan: number; actual: number } {
  let plan = 0
  let actual = 0
  for (const r of rows) {
    const cell = r.daily?.[d]
    if (cell) {
      plan += cell.plan
      actual += cell.actual
    }
  }
  return { plan, actual }
}

function buildTrendDayAggs(dates: string[], rows: ProcessMachinePlanRow[]): TrendDayAgg[] {
  return dates.map((date) => {
    const { plan, actual } = sumDailyForDate(rows, date)
    const diff = actual - plan
    const rate = plan > 0 ? round1((actual / plan) * 100) : null
    return { date, plan, actual, diff, rate }
  })
}

const trendDayAggs = computed<TrendDayAgg[]>(() => {
  const data = planData.value
  if (!data?.dates?.length) return []
  return buildTrendDayAggs(data.dates, filteredSummary.value)
})

const trendStats = computed(() => {
  const aggs = trendDayAggs.value
  if (!aggs.length) return null
  let totalPlan = 0
  let totalActual = 0
  const withRate = aggs
    .filter((a) => a.rate !== null)
    .map((a) => ({ date: a.date, rate: a.rate as number }))
  for (const a of aggs) {
    totalPlan += a.plan
    totalActual += a.actual
  }
  const avgRate =
    withRate.length > 0
      ? round1(withRate.reduce((s, a) => s + a.rate, 0) / withRate.length)
      : null
  let best: { date: string; rate: number } | null = null
  let worst: { date: string; rate: number } | null = null
  for (const a of withRate) {
    if (!best || a.rate > best.rate) best = { date: a.date, rate: a.rate }
    if (!worst || a.rate < worst.rate) worst = { date: a.date, rate: a.rate }
  }
  return { totalPlan, totalActual, avgRate, best, worst }
})

const trendDailyRows = computed(() => trendDayAggs.value)

const trendProcessColumns = computed(() => {
  const data = planData.value
  if (!data) return []
  return data.processes
    .filter((p) => filteredSummary.value.some((r) => r.process_key === p.key))
    .map((p) => ({ key: p.key, label: p.label }))
})

const trendProcessDayRows = computed<TrendProcessDayRow[]>(() => {
  const data = planData.value
  if (!data?.dates?.length) return []
  const cols = trendProcessColumns.value
  return data.dates.map((date) => {
    const rates: Record<string, number | null> = {}
    for (const col of cols) {
      const procRows = filteredSummary.value.filter((r) => r.process_key === col.key)
      const { plan, actual } = sumDailyForDate(procRows, date)
      rates[col.key] = plan > 0 ? round1((actual / plan) * 100) : null
    }
    return { date, rates }
  })
})

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
  if (v === 0) return '—'
  return dailyMetric.value === 'diff' ? signed(v) : fmt(v)
}
function dailyCellClass(row: TableRow, d: string): string {
  const v = Number(row.__daily?.[d] ?? 0)
  const parts: string[] = []
  if (v === 0) parts.push('pmp-num--zero')
  if (dailyMetric.value === 'diff') parts.push(diffClass(v))
  return parts.filter(Boolean).join(' ')
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
const TREND_BASE_TOOLTIP = {
  trigger: 'axis' as const,
  backgroundColor: 'rgba(255, 255, 255, 0.97)',
  borderColor: '#e2e8f0',
  borderWidth: 1,
  padding: [10, 14],
  textStyle: { color: '#334155', fontSize: 12 },
  axisPointer: {
    type: 'cross' as const,
    crossStyle: { color: '#94a3b8', width: 1 },
    lineStyle: { color: '#cbd5e1', type: 'dashed' as const },
  },
}

function trendXAxisLabels(dates: string[]): string[] {
  return dates.map((d) => `${formatDateHeaderDate(d)}\n${formatDateHeaderWeek(d)}`)
}

function qtyBarLabelFormatter(v: unknown): string {
  const n = Number(v)
  if (!Number.isFinite(n) || n === 0) return ''
  return n >= 10000 ? `${Math.round(n / 1000)}k` : String(n)
}

function rateLabelFormatter(v: unknown): string {
  if (v === null || v === undefined || v === '') return ''
  const n = Number(v)
  if (!Number.isFinite(n)) return ''
  return `${n}%`
}

function trendRateAxisMax(rates: (number | null)[]): number {
  const nums = rates.filter((r): r is number => r !== null && Number.isFinite(r))
  const peak = nums.length ? Math.max(...nums, 100) : 100
  return Math.min(160, Math.ceil(peak / 10) * 10 + 10)
}

function buildTrendOption(): EChartsOption {
  const data = planData.value
  const ds = data?.dates ?? []
  const axisLabels = trendXAxisLabels(ds)
  const rotate = ds.length > 14 ? 35 : 0
  const dataZoom =
    ds.length > 16
      ? [{ type: 'slider' as const, start: Math.max(0, 100 - Math.round((16 / ds.length) * 100)), end: 100, height: 18, bottom: 4 }]
      : undefined

  if (trendGroup.value === 'all') {
    const aggs = trendDayAggs.value
    const planByDate = aggs.map((a) => a.plan)
    const actualByDate = aggs.map((a) => a.actual)
    const rateByDate = aggs.map((a) => a.rate)

    return {
      color: ['#93c5fd', '#4ade80', '#a78bfa'],
      tooltip: {
        ...TREND_BASE_TOOLTIP,
        formatter(params: unknown) {
          const list = Array.isArray(params) ? params : [params]
          const first = list[0] as { axisValue?: string; dataIndex?: number }
          const idx = first?.dataIndex ?? 0
          const agg = aggs[idx]
          if (!agg) return ''
          const lines = [
            `<div style="font-weight:700;margin-bottom:6px">${escHtml(axisLabels[idx] ?? '')}</div>`,
            `計画：<b>${fmt(agg.plan)}</b>`,
            `実績：<b>${fmt(agg.actual)}</b>`,
            `差異：<b>${signed(agg.diff)}</b>`,
            `達成率：<b>${rateText(agg.rate)}</b>`,
          ]
          return lines.join('<br/>')
        },
      },
      legend: {
        data: ['計画', '実績', '達成率'],
        top: 4,
        itemGap: 16,
        textStyle: { fontSize: 12, color: '#475467' },
      },
      grid: { left: 52, right: 52, top: 52, bottom: dataZoom ? 56 : 44 },
      dataZoom,
      xAxis: {
        type: 'category',
        data: axisLabels,
        axisLabel: { fontSize: 10, color: '#64748b', lineHeight: 14, rotate },
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisTick: { alignWithLabel: true },
      },
      yAxis: [
        {
          type: 'value',
          name: '数量',
          nameTextStyle: { color: '#64748b', fontSize: 11 },
          splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
          axisLabel: { color: '#64748b', fontSize: 10 },
        },
        {
          type: 'value',
          name: '達成率',
          min: 0,
          max: trendRateAxisMax(rateByDate),
          nameTextStyle: { color: '#7c3aed', fontSize: 11 },
          splitLine: { show: false },
          axisLabel: { formatter: '{value}%', color: '#7c3aed', fontSize: 10 },
        },
      ],
      series: [
        {
          name: '計画',
          type: 'bar',
          barGap: '12%',
          barMaxWidth: 28,
          data: planByDate,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#93c5fd' },
                { offset: 1, color: '#60a5fa' },
              ],
            },
            borderRadius: [4, 4, 0, 0],
          },
          label: {
            show: true,
            position: 'top',
            fontSize: 9,
            color: '#3b82f6',
            formatter: (p: { value?: unknown }) => qtyBarLabelFormatter(p.value),
          },
        },
        {
          name: '実績',
          type: 'bar',
          barMaxWidth: 28,
          data: actualByDate,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#86efac' },
                { offset: 1, color: '#22c55e' },
              ],
            },
            borderRadius: [4, 4, 0, 0],
          },
          label: {
            show: true,
            position: 'top',
            fontSize: 9,
            color: '#15803d',
            formatter: (p: { value?: unknown }) => qtyBarLabelFormatter(p.value),
          },
        },
        {
          name: '達成率',
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          connectNulls: true,
          symbol: 'circle',
          symbolSize: 7,
          data: rateByDate,
          lineStyle: { width: 3, color: '#8b5cf6', shadowColor: 'rgba(139,92,246,0.25)', shadowBlur: 6 },
          itemStyle: { color: '#8b5cf6', borderColor: '#fff', borderWidth: 2 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(139, 92, 246, 0.22)' },
                { offset: 1, color: 'rgba(139, 92, 246, 0.02)' },
              ],
            },
          },
          label: {
            show: true,
            position: 'top',
            distance: 6,
            fontSize: 10,
            fontWeight: 700,
            color: '#6d28d9',
            formatter: (p: { value?: unknown }) => rateLabelFormatter(p.value),
          },
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: { color: '#f59e0b', type: 'dashed', width: 1.5 },
            label: { formatter: '100%', color: '#d97706', fontSize: 10 },
            data: [{ yAxis: 100 }],
          },
        },
      ],
    }
  }

  const series: object[] = []
  const legend: string[] = []
  const allRates: (number | null)[] = []
  trendProcessColumns.value.forEach((col, i) => {
    const procRows = filteredSummary.value.filter((r) => r.process_key === col.key)
    const rateByDate = ds.map((d) => {
      const { plan, actual } = sumDailyForDate(procRows, d)
      return plan > 0 ? round1((actual / plan) * 100) : null
    })
    allRates.push(...rateByDate)
    const color = TREND_PROCESS_COLORS[i % TREND_PROCESS_COLORS.length]
    legend.push(col.label)
    series.push({
      name: col.label,
      type: 'line',
      smooth: true,
      connectNulls: true,
      symbol: 'circle',
      symbolSize: 6,
      data: rateByDate,
      itemStyle: { color },
      lineStyle: { width: 2.5, color },
      label: {
        show: ds.length <= 12,
        position: 'top',
        fontSize: 9,
        fontWeight: 600,
        color,
        formatter: (p: { value?: unknown }) => rateLabelFormatter(p.value),
      },
      markLine:
        i === 0
          ? {
              silent: true,
              symbol: 'none',
              lineStyle: { color: '#f59e0b', type: 'dashed', width: 1.5 },
              label: { formatter: '100%', color: '#d97706', fontSize: 10 },
              data: [{ yAxis: 100 }],
            }
          : undefined,
    })
  })

  return {
    color: TREND_PROCESS_COLORS,
    tooltip: {
      ...TREND_BASE_TOOLTIP,
      valueFormatter: (v: unknown) => (v == null || v === '' ? '—' : `${v}%`),
    },
    legend: {
      data: legend,
      top: 4,
      type: 'scroll',
      textStyle: { fontSize: 11, color: '#475467' },
    },
    grid: { left: 48, right: 28, top: 52, bottom: dataZoom ? 56 : 44 },
    dataZoom,
    xAxis: {
      type: 'category',
      data: axisLabels,
      axisLabel: { fontSize: 10, color: '#64748b', lineHeight: 14, rotate },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
    },
    yAxis: {
      type: 'value',
      name: '達成率 %',
      min: 0,
      max: trendRateAxisMax(allRates),
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
      axisLabel: { formatter: '{value}%', color: '#64748b', fontSize: 10 },
    },
    series: series as EChartsOption['series'],
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

/* ============ 印刷 ============ */
const PRINT_DOCUMENT_STYLES = `
  * { box-sizing: border-box; }
  html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body {
    margin: 0;
    padding: 6mm 7mm;
    font-family: 'Segoe UI', 'Meiryo', 'Hiragino Sans', 'Microsoft YaHei', sans-serif;
    font-size: 9pt;
    color: #0f172a;
    line-height: 1.35;
    background: #fff;
  }
  .print-header {
    margin-bottom: 4mm;
    padding-bottom: 3mm;
    border-bottom: 2px solid #3b82f6;
  }
  .print-title {
    font-size: 14pt;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 2mm;
  }
  .print-meta {
    font-size: 8.5pt;
    color: #475569;
    line-height: 1.45;
  }
  .print-kpi {
    display: flex;
    flex-wrap: wrap;
    gap: 3mm 8mm;
    margin: 3mm 0 4mm;
    font-size: 8.5pt;
    color: #334155;
  }
  .print-kpi b {
    font-variant-numeric: tabular-nums;
    color: #0f172a;
  }
  .print-view-label {
    font-size: 9pt;
    font-weight: 700;
    color: #1e40af;
    margin: 2mm 0 2mm;
  }
  .print-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 8pt;
  }
  .print-table th,
  .print-table td {
    border: 1px solid #cbd5e1;
    padding: 1px 3px;
    text-align: center;
  }
  .print-table th {
    background: #eef2f9;
    font-weight: 700;
    color: #334155;
  }
  .print-table .text-left { text-align: center; }
  .print-table .num-zero { color: #94a3b8; }
  .print-table .num { font-variant-numeric: tabular-nums; }
  .print-table tr.subtotal td { background: #f1f5f9; font-weight: 700; }
  .print-table tr.grand td { background: #e2e8f0; font-weight: 800; }
  .print-chart {
    width: 100%;
    max-height: 140mm;
    object-fit: contain;
    margin-top: 3mm;
    page-break-inside: avoid;
  }
  /* @PAGE_RULE プレースホルダ（openPrintDocument で差し替え） */
  @page { margin: 10mm; }
`

function escHtml(s: string): string {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const printDisabled = computed(() => {
  if (loading.value) return true
  if (viewMode.value === 'trend') return !planData.value || filteredSummary.value.length === 0
  return filteredSummary.value.length === 0
})

function buildPrintFilterSummary(): string {
  const proc =
    selectedProcesses.value.length > 0
      ? selectedProcesses.value
          .map((k) => ALL_PROCESSES.find((p) => p.key === k)?.label ?? k)
          .join('、')
      : '全工程'
  const mach = selectedMachines.value.length > 0 ? selectedMachines.value.join('、') : '全設備'
  return `期間：${escHtml(periodLabel.value)}　工程：${escHtml(proc)}　設備：${escHtml(mach)}`
}

function buildPrintKpiHtml(): string {
  const g = grandTotal.value
  return `<div class="print-kpi">
    <span>計画合計 <b>${escHtml(fmt(g.plan))}</b></span>
    <span>実績合計 <b>${escHtml(fmt(g.actual))}</b></span>
    <span>差異 <b>${escHtml(signed(g.diff))}</b></span>
    <span>達成率 <b>${escHtml(rateText(g.achievement_rate))}</b></span>
    <span>不良率 <b>${escHtml(rateText(g.defect_rate))}</b></span>
  </div>`
}

function printRowClass(row: TableRow): string {
  if (row.__type === 'grand') return 'grand'
  if (row.__type === 'subtotal') return 'subtotal'
  return ''
}

function buildPrintSummaryTableHtml(): string {
  const cols = [
    '工程',
    '設備',
    '計画',
    '実績',
    '差異',
    '達成率',
    '実計',
    '不良',
    '廃棄',
    '不良率',
    '稼働日',
  ]
  const head = cols.map((c) => `<th>${escHtml(c)}</th>`).join('')
  const body = summaryTableData.value
    .map(
      (row) => `<tr class="${printRowClass(row)}">
        <td>${escHtml(row.process_label)}</td>
        <td>${escHtml(row.machine)}</td>
        <td class="num">${escHtml(fmt(row.plan))}</td>
        <td class="num">${escHtml(fmt(row.actual))}</td>
        <td class="num">${escHtml(signed(row.diff))}</td>
        <td class="num">${escHtml(rateText(row.achievement_rate))}</td>
        <td class="num">${escHtml(fmt(row.actual_plan))}</td>
        <td class="num">${escHtml(fmt(row.defect))}</td>
        <td class="num">${escHtml(fmt(row.scrap))}</td>
        <td class="num">${escHtml(rateText(row.defect_rate))}</td>
        <td class="num">${escHtml(String(row.days || 0))}</td>
      </tr>`,
    )
    .join('')
  return `<div class="print-view-label">対比集計</div>
    <table class="print-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`
}

function buildPrintDailyTableHtml(): string {
  const data = planData.value
  if (!data) return ''
  const metricLabel =
    dailyMetric.value === 'plan' ? '計画' : dailyMetric.value === 'actual' ? '実績' : '差異'
  const headRow1 = `<tr>
    <th rowspan="2">工程</th>
    <th rowspan="2">設備</th>
    ${data.dates.map((d) => `<th>${escHtml(formatDateHeaderDate(d))}</th>`).join('')}
    <th rowspan="2">合計</th>
  </tr>`
  const headRow2 = `<tr>${data.dates.map((d) => `<th>${escHtml(formatDateHeaderWeek(d))}</th>`).join('')}</tr>`
  const body = dailyTableData.value
    .map((row) => {
      const cells = data.dates
        .map((d) => {
          const v = Number(row.__daily?.[d] ?? 0)
          const text = v === 0 ? '—' : dailyMetric.value === 'diff' ? signed(v) : fmt(v)
          const zc = v === 0 ? ' num-zero' : ''
          return `<td class="num${zc}">${escHtml(text)}</td>`
        })
        .join('')
      const rt = Number(row.__rowTotal ?? 0)
      const totalText =
        rt === 0 ? '—' : dailyMetric.value === 'diff' ? signed(row.__rowTotal) : fmt(row.__rowTotal)
      const tz = rt === 0 ? ' num-zero' : ''
      return `<tr class="${printRowClass(row)}">
        <td>${escHtml(row.process_label)}</td>
        <td>${escHtml(row.machine)}</td>
        ${cells}
        <td class="num${tz}">${escHtml(totalText)}</td>
      </tr>`
    })
    .join('')
  return `<div class="print-view-label">日別明細（${escHtml(metricLabel)}）</div>
    <table class="print-table"><thead>${headRow1}${headRow2}</thead><tbody>${body}</tbody></table>`
}

function buildPrintTrendHtml(): string {
  const groupLabel = trendGroup.value === 'all' ? '全工程合計' : '工程別'
  let chartHtml = ''
  if (trendChart) {
    try {
      const url = trendChart.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#fff' })
      chartHtml = `<img class="print-chart" src="${url}" alt="達成率トレンド" />`
    } catch {
      chartHtml = '<p>チャートの画像化に失敗しました</p>'
    }
  }
  return `<div class="print-view-label">達成率トレンド（${escHtml(groupLabel)}）</div>${chartHtml}`
}

function buildPrintHtml(): string {
  const printDate = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
  let content = ''
  if (viewMode.value === 'summary') content = buildPrintSummaryTableHtml()
  else if (viewMode.value === 'daily') content = buildPrintDailyTableHtml()
  else content = buildPrintTrendHtml()

  return `
    <div class="print-header">
      <div class="print-title">工程別設備別計画</div>
      <div class="print-meta">
        <div>印刷日時：${escHtml(printDate)}</div>
        <div>${buildPrintFilterSummary()}</div>
      </div>
    </div>
    ${buildPrintKpiHtml()}
    ${content}
  `
}

function openPrintDocument(html: string, landscape = false) {
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('ポップアップがブロックされました。ブラウザの設定を確認してください')
    return
  }
  const pageRule = landscape ? '@page { size: landscape; margin: 8mm; }' : '@page { margin: 10mm; }'
  const styles = PRINT_DOCUMENT_STYLES.replace('@page { margin: 10mm; }', pageRule)
  printWindow.document.write(`<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>工程別設備別計画</title>
  <style>${styles}</style>
</head>
<body>${html}</body>
</html>`)
  printWindow.document.close()
  printWindow.onload = () => {
    printWindow.print()
    setTimeout(() => printWindow.close(), 400)
  }
}

function handlePrint() {
  if (printDisabled.value) {
    ElMessage.warning('印刷するデータがありません')
    return
  }
  const run = () => {
    const html = buildPrintHtml()
    openPrintDocument(html, viewMode.value === 'daily')
  }
  if (viewMode.value === 'trend') {
    syncTrendChart()
    nextTick(() => {
      setTimeout(run, 280)
    })
    return
  }
  run()
}

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
  --pmp-line: #d8e2ec;
  --pmp-elev-inset: inset 0 1px 0 rgba(255, 255, 255, 0.92);
  --pmp-elev-1: 0 1px 3px rgba(15, 23, 42, 0.07), 0 4px 14px rgba(15, 23, 42, 0.06);
  --pmp-elev-2: 0 4px 12px rgba(15, 23, 42, 0.1);
  --pmp-shadow-hover: 0 6px 20px rgba(15, 23, 42, 0.12);

  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: 8px 10px 10px;
  box-sizing: border-box;
  gap: 6px;
  background:
    radial-gradient(900px 420px at 8% -5%, rgba(191, 219, 254, 0.45) 0%, transparent 55%),
    radial-gradient(800px 400px at 100% 0%, rgba(187, 247, 208, 0.35) 0%, transparent 48%),
    linear-gradient(180deg, #eef2f8 0%, #e8edf4 100%);
}
.pmp-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ── ツールバー（コンパクト・立体） ── */
.pmp-toolbar {
  display: flex;
  align-items: stretch;
  gap: 10px;
  padding: 6px 8px;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 55%, #e8eef5 100%);
  border: 1px solid #d4dce8;
  border-radius: 10px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 2px 4px rgba(15, 23, 42, 0.06),
    0 6px 18px rgba(15, 23, 42, 0.07);
}
.pmp-toolbar__brand {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  padding: 4px 10px 4px 12px;
  min-width: 0;
  border-right: 1px solid #dde4ee;
  flex-shrink: 0;
}
.pmp-toolbar__title {
  position: relative;
  margin: 0;
  padding-left: 10px;
  font-size: 15px;
  font-weight: 800;
  line-height: 1.2;
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
  width: 3px;
  height: 15px;
  border-radius: 2px;
  background: linear-gradient(180deg, #60a5fa, #8b5cf6);
  box-shadow: 0 1px 3px rgba(59, 130, 246, 0.45);
}
.pmp-toolbar__period {
  font-size: 11px;
  color: #475569;
  white-space: nowrap;
  padding: 1px 8px;
  background: linear-gradient(180deg, #fff 0%, #eef2f7 100%);
  border: 1px solid #d8e2ec;
  border-radius: 999px;
  box-shadow: inset 0 1px 0 #fff, 0 1px 2px rgba(15, 23, 42, 0.05);
  font-variant-numeric: tabular-nums;
}
.pmp-toolbar__body {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.pmp-toolbar__strip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 6px;
  border-radius: 8px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  border: 1px solid #d5dde8;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 1px 3px rgba(15, 23, 42, 0.07);
}
.pmp-toolbar__strip-label {
  font-size: 10px;
  font-weight: 800;
  color: #64748b;
  letter-spacing: 0.06em;
  padding: 2px 4px;
  flex-shrink: 0;
}
.pmp-toolbar__strip--view {
  padding: 2px 4px;
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
  border-color: #c7d2fe;
}
.pmp-toolbar__strip--actions {
  gap: 5px;
  padding: 3px 5px;
  margin-left: auto;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}
.pmp-toolbar__range {
  width: 218px;
}
.pmp-toolbar__process {
  width: 128px;
}
.pmp-toolbar__machine {
  width: 150px;
}

/* ── 概要カード（コンパクト・立体） ── */
.pmp-cards {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 6px;
  flex-shrink: 0;
}
.pmp-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px 7px 11px;
  background: linear-gradient(165deg, #ffffff 0%, #f8fafc 55%, #f1f5f9 100%);
  border: 1px solid var(--pmp-line);
  border-radius: 9px;
  box-shadow: var(--pmp-elev-inset), var(--pmp-elev-1);
  overflow: hidden;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.pmp-card::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--pmp-accent, #c0c4cc);
  box-shadow: 1px 0 4px rgba(15, 23, 42, 0.08);
}
.pmp-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--pmp-elev-inset), var(--pmp-shadow-hover);
}
.pmp-card__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 9px;
  font-size: 17px;
  color: var(--pmp-accent, #909399);
  background: linear-gradient(145deg, #fff 0%, var(--pmp-accent-soft, #f0f2f5) 100%);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: inset 0 1px 0 #fff, 0 1px 3px rgba(15, 23, 42, 0.08);
  flex-shrink: 0;
}
.pmp-card__body {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}
.pmp-card__label {
  font-size: 10px;
  font-weight: 700;
  color: var(--pmp-sub);
  white-space: nowrap;
  letter-spacing: 0.02em;
}
.pmp-card__value {
  font-size: 18px;
  line-height: 1.15;
  font-weight: 800;
  color: var(--pmp-ink);
  font-variant-numeric: tabular-nums;
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

/* ── コンテンツパネル（表・トレンド共通） ── */
.pmp-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #d4dce8;
  border-radius: 10px;
  box-shadow: var(--pmp-elev-inset), var(--pmp-elev-1);
  overflow: hidden;
}
.pmp-panel__head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 8px;
  padding: 5px 10px;
  flex-shrink: 0;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  border-bottom: 1px solid #dde4ee;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}
.pmp-panel__title {
  font-size: 12px;
  font-weight: 800;
  color: var(--pmp-ink);
  letter-spacing: 0.02em;
  margin-right: 2px;
}
.pmp-panel__label {
  font-size: 10px;
  font-weight: 800;
  color: #64748b;
  letter-spacing: 0.05em;
}
.pmp-panel__hint {
  font-size: 11px;
  color: var(--pmp-sub);
  padding: 2px 8px;
  margin-left: auto;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%);
  border: 1px dashed #d0dae6;
  border-radius: 999px;
  box-shadow: inset 0 1px 0 #fff;
}
.pmp-panel__body {
  flex: 1;
  min-height: 0;
  padding: 6px 8px 8px;
  display: flex;
  flex-direction: column;
}
.pmp-panel__body--trend {
  gap: 6px;
  overflow: auto;
}
.pmp-table {
  flex: 1;
  min-height: 0;
  border-radius: 6px;
  overflow: hidden;
}

/* ── トレンド内ブロック ── */
.pmp-trend-kpis {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 6px;
  flex-shrink: 0;
}
.pmp-trend-kpi {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 6px 8px;
  background: linear-gradient(165deg, #fff 0%, #f8fafc 100%);
  border: 1px solid var(--pmp-line);
  border-radius: 8px;
  border-left: 3px solid #cbd5e1;
  box-shadow: var(--pmp-elev-inset), 0 1px 2px rgba(15, 23, 42, 0.05);
}
.pmp-trend-kpi__label {
  font-size: 10px;
  font-weight: 700;
  color: var(--pmp-sub);
}
.pmp-trend-kpi__value {
  font-size: 15px;
  font-weight: 800;
  color: var(--pmp-ink);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}
.pmp-trend-kpi__value--sm {
  font-size: 12px;
  font-weight: 700;
}
.pmp-trend-kpi--plan {
  border-left-color: var(--pmp-blue);
}
.pmp-trend-kpi--actual {
  border-left-color: var(--pmp-green);
}
.pmp-trend-kpi--avg {
  border-left-color: var(--pmp-purple);
}
.pmp-trend-kpi--best {
  border-left-color: #16a34a;
}
.pmp-trend-kpi--worst {
  border-left-color: var(--pmp-red);
}
.pmp-trend-chart-card {
  flex: 1;
  min-height: 260px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #fff 0%, #fafbfc 100%);
  border: 1px solid var(--pmp-line);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: var(--pmp-elev-inset), 0 2px 8px rgba(15, 23, 42, 0.05);
}
.pmp-trend-chart-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 5px 10px;
  background: linear-gradient(90deg, #f1f5f9 0%, #fff 100%);
  border-bottom: 1px solid #e8edf4;
}
.pmp-trend-chart-card__title {
  font-size: 12px;
  font-weight: 700;
  color: var(--pmp-ink);
}
.pmp-trend-chart-card__badge {
  font-size: 10px;
  font-weight: 600;
  color: #b45309;
  padding: 2px 7px;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fde68a;
  border-radius: 999px;
  box-shadow: inset 0 1px 0 #fff;
}
.pmp-trend-chart {
  flex: 1;
  min-height: 240px;
  width: 100%;
  padding: 4px 6px 6px;
}
.pmp-trend-table-card {
  flex-shrink: 0;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
  border: 1px solid var(--pmp-line);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: var(--pmp-elev-inset), 0 1px 3px rgba(15, 23, 42, 0.05);
}
.pmp-trend-table-card__head {
  padding: 5px 10px;
  font-size: 11px;
  font-weight: 800;
  color: #475467;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  border-bottom: 1px solid #e8edf4;
}
.pmp-week--sat {
  color: #1d4ed8;
  font-weight: 600;
}
.pmp-week--sun {
  color: #dc2626;
  font-weight: 600;
}
:deep(.pmp-trend-table .el-table__cell) {
  padding: 2px 0;
}
:deep(.pmp-trend-table th.el-table__cell) {
  text-align: center;
  background: #f7f9fd;
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
  min-width: 0;
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
  gap: 6px;
  padding: 0 0 10px;
  font-size: 12px;
  color: var(--pmp-sub);
}
.pmp-drill-summary span {
  padding: 4px 10px;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%);
  border: 1px solid var(--pmp-line);
  border-radius: 999px;
  box-shadow: inset 0 1px 0 #fff, 0 1px 2px rgba(15, 23, 42, 0.04);
}
.pmp-drill-summary b {
  font-variant-numeric: tabular-nums;
  color: var(--pmp-ink);
  margin-left: 2px;
}

/* ── el-table 細部チューニング ── */
:deep(.pmp-table),
:deep(.pmp-trend-table),
:deep(.pmp-drill-table) {
  --el-table-border-color: #e2e8f0;
  --el-table-header-text-color: #334155;
  border-radius: 6px;
}
:deep(.pmp-table th.el-table__cell),
:deep(.pmp-trend-table th.el-table__cell),
:deep(.pmp-drill-table th.el-table__cell) {
  background: linear-gradient(180deg, #f8fafc 0%, #e8eef5 100%);
  font-weight: 700;
  font-size: 12px;
  text-align: center;
  box-shadow: inset 0 -1px 0 #dde4ee;
}
:deep(.pmp-table th.el-table__cell .cell),
:deep(.pmp-trend-table th.el-table__cell .cell),
:deep(.pmp-drill-table th.el-table__cell .cell) {
  justify-content: center;
}
:deep(.pmp-table td.el-table__cell),
:deep(.pmp-trend-table td.el-table__cell),
:deep(.pmp-drill-table td.el-table__cell) {
  background: #fff;
}
:deep(.pmp-table .el-table__cell) {
  padding: 2px 0;
}
:deep(.pmp-table .cell) {
  padding: 0 2px;
  line-height: 1.2;
}
:deep(.pmp-table .el-table__row:hover > td.el-table__cell),
:deep(.pmp-trend-table .el-table__row:hover > td.el-table__cell),
:deep(.pmp-drill-table .el-table__row:hover > td.el-table__cell) {
  background: #eff6ff !important;
}
:deep(.pmp-table--daily .el-table--border .el-table__inner-wrapper::after),
:deep(.pmp-table--daily .el-table--border::before),
:deep(.pmp-table--daily .el-table--border::after) {
  background-color: #e2e8f0;
}

/* 日別明細：居中・コンパクト */
:deep(.pmp-table--daily .el-table__cell) {
  padding: 1px 0;
}
:deep(.pmp-table--daily .cell) {
  padding: 0 1px;
  text-align: center;
  justify-content: center;
}
:deep(.pmp-table--daily .pmp-daycol .cell) {
  padding: 0 1px;
}
:deep(.pmp-table--daily .pmp-num--zero) {
  color: #cbd5e1;
  font-weight: 400;
}
/* 2段表頭（日付 / 曜日） */
:deep(.pmp-table--daily .pmp-daycol-group > .cell) {
  font-weight: 700;
  font-size: 11px;
  color: #334155;
  padding: 2px 0 0;
  line-height: 1.15;
}
:deep(.pmp-table--daily th.pmp-daycol > .cell) {
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
  padding: 0 0 2px;
  line-height: 1.15;
}
:deep(.pmp-table--daily th.pmp-daycol--sat > .cell) {
  color: #1d4ed8;
  background: #eff6ff;
}
:deep(.pmp-table--daily th.pmp-daycol--sun > .cell) {
  color: #dc2626;
  background: #fef2f2;
}
:deep(.pmp-row-subtotal) td.el-table__cell {
  background: linear-gradient(180deg, #f1f5f9 0%, #e8eef5 100%) !important;
  font-weight: 700;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
}
:deep(.pmp-row-grand) td.el-table__cell {
  background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%) !important;
  font-weight: 800;
  color: #1e3a8a;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5);
}
:deep(.pmp-row-machine) {
  cursor: pointer;
}
:deep(.pmp-row-machine:hover) td.el-table__cell {
  background: #f0f9ff !important;
}

/* パネル内セグメント（日別指標・トレンド集計） */
:deep(.pmp-panel__seg.el-radio-group) {
  flex-wrap: nowrap;
}
:deep(.pmp-panel__seg .el-radio-button__inner) {
  padding: 4px 9px;
  font-size: 11px;
  font-weight: 600;
  border-color: #d0dae6 !important;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%);
  box-shadow: inset 0 -1px 0 rgba(15, 23, 42, 0.04);
}
:deep(.pmp-panel__seg .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  color: #fff;
  background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 55%, #2563eb 100%);
  border-color: #2563eb !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3), 0 1px 4px rgba(37, 99, 235, 0.3);
}
:deep(.pmp-panel__seg .el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 5px 0 0 5px;
}
:deep(.pmp-panel__seg .el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 5px 5px 0;
}

/* ツールバー内コントロール：凹み入力 + 立体ボタン */
:deep(.pmp-toolbar__strip .el-input__wrapper),
:deep(.pmp-toolbar__strip .el-select__wrapper) {
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.07);
  background: #fff;
}
:deep(.pmp-toolbar__view.el-radio-group) {
  flex-wrap: nowrap;
}
:deep(.pmp-toolbar__view .el-radio-button__inner) {
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 600;
  border-color: #c7d2fe !important;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%);
  box-shadow: inset 0 -1px 0 rgba(15, 23, 42, 0.04);
}
:deep(.pmp-toolbar__view .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  color: #fff;
  background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 55%, #2563eb 100%);
  border-color: #2563eb !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    0 2px 6px rgba(37, 99, 235, 0.35);
}
:deep(.pmp-toolbar__view .el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 6px 0 0 6px;
}
:deep(.pmp-toolbar__view .el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 6px 6px 0;
}
:deep(.pmp-toolbar__btn) {
  font-weight: 600;
  border: 1px solid transparent;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}
:deep(.pmp-toolbar__btn:hover:not(:disabled)) {
  transform: translateY(-1px);
}
:deep(.pmp-toolbar__btn:active:not(:disabled)) {
  transform: translateY(0);
}
:deep(.pmp-toolbar__btn--primary) {
  background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 50%, #2563eb 100%) !important;
  border-color: #1d4ed8 !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    0 2px 6px rgba(37, 99, 235, 0.4) !important;
}
:deep(.pmp-toolbar__btn--print) {
  color: #b45309 !important;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%) !important;
  border-color: #fcd34d !important;
  box-shadow:
    inset 0 1px 0 #fff,
    0 2px 5px rgba(245, 158, 11, 0.25) !important;
}
:deep(.pmp-toolbar__btn--excel) {
  color: #15803d !important;
  background: linear-gradient(180deg, #f0fdf4 0%, #dcfce7 100%) !important;
  border-color: #86efac !important;
  box-shadow:
    inset 0 1px 0 #fff,
    0 2px 5px rgba(34, 197, 94, 0.22) !important;
}
:deep(.pmp-drill-dialog.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.18);
}
:deep(.pmp-drill-dialog .el-dialog__header) {
  margin-right: 0;
  padding: 12px 16px 10px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  border-bottom: 1px solid var(--pmp-line);
}
:deep(.pmp-drill-dialog .el-dialog__title) {
  font-weight: 800;
  font-size: 15px;
  color: var(--pmp-ink);
}
:deep(.pmp-drill-dialog .el-dialog__body) {
  padding: 12px 16px 8px;
  background: #fff;
}
:deep(.pmp-drill-dialog .el-dialog__footer) {
  padding: 10px 16px 12px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-top: 1px solid var(--pmp-line);
}
</style>
