<template>
  <div class="opp-page" :class="`opp-page--${metric}`">
    <header class="opp-hero no-print">
      <div class="opp-hero__main">
        <span class="opp-hero__icon" aria-hidden="true">
          <el-icon><Brush /></el-icon>
        </span>
        <div class="opp-hero__copy">
          <h1 class="opp-hero__title">外注メッキ計画作成</h1>
          <p class="opp-hero__desc">
            生産データ管理から、外注メッキ（KT06）の直前工程の計画・実績を製品 × 日付で表示します。実績があれば実績、なければ計画です。
          </p>
        </div>
      </div>
      <div class="opp-hero__meta">
        <span class="opp-badge">
          <span class="opp-badge__dot" />
          APS 生産計画 · KT06
        </span>
        <span class="opp-hero__period">{{ periodLabel }}</span>
      </div>
    </header>

    <header class="opp-toolbar no-print">
      <div class="opp-toolbar__body">
        <div class="opp-toolbar__strip opp-toolbar__strip--period">
          <span class="opp-toolbar__strip-label">期間</span>
          <el-date-picker
            v-model="periodRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            format="YYYY/MM/DD"
            range-separator="～"
            start-placeholder="開始"
            end-placeholder="終了"
            size="small"
            class="opp-toolbar__range"
            :clearable="false"
            :shortcuts="periodRangeShortcuts"
          />
          <el-button size="small" class="opp-btn opp-btn--month" :icon="Calendar" @click="applyThisMonth">
            今月
          </el-button>
          <el-button size="small" class="opp-btn opp-btn--last" :icon="Calendar" @click="applyLastMonth">
            先月
          </el-button>
        </div>

        <div class="opp-toolbar__strip opp-toolbar__strip--view">
          <span class="opp-toolbar__strip-label">表示</span>
          <el-radio-group v-model="metric" size="small" class="opp-metric-group">
            <el-radio-button value="plan">前工程計画</el-radio-button>
            <el-radio-button value="actual">前工程実績</el-radio-button>
            <el-radio-button value="actual_plan">前工程実計</el-radio-button>
          </el-radio-group>
        </div>

        <div class="opp-toolbar__strip opp-toolbar__strip--filter">
          <span class="opp-toolbar__strip-label">絞込</span>
          <el-select
            v-model="selectedSuppliers"
            multiple
            collapse-tags
            collapse-tags-tooltip
            filterable
            clearable
            size="small"
            placeholder="外注先"
            class="opp-toolbar__supplier"
          >
            <el-option v-for="s in supplierOptions" :key="s" :label="s" :value="s" />
          </el-select>
          <el-input
            v-model="productKeyword"
            size="small"
            clearable
            placeholder="品番 / 品名"
            class="opp-toolbar__keyword"
            :prefix-icon="Search"
          />
          <el-checkbox v-model="showZeroRows">ゼロ行も表示</el-checkbox>
        </div>

        <div class="opp-toolbar__strip opp-toolbar__strip--actions">
          <el-button
            type="primary"
            size="small"
            class="opp-btn opp-btn--primary"
            :loading="loading"
            :icon="Refresh"
            @click="loadMatrix"
          >
            更新
          </el-button>
          <el-button
            size="small"
            class="opp-btn opp-btn--print"
            :icon="Printer"
            :disabled="loading || displayGroups.length === 0"
            @click="handlePrint"
          >
            印刷
          </el-button>
          <el-button
            size="small"
            class="opp-btn opp-btn--excel"
            :icon="Download"
            :disabled="loading || !canExport || displayGroups.length === 0"
            @click="exportExcel"
          >
            Excel
          </el-button>
        </div>
      </div>
    </header>

    <section class="opp-cards no-print" aria-label="概要">
      <div class="opp-card opp-card--plan">
        <span class="opp-card__icon"><el-icon><Histogram /></el-icon></span>
        <div class="opp-card__body">
          <span class="opp-card__label">前工程計画合計</span>
          <span class="opp-card__value">{{ fmt(filteredTotals.plan) }}</span>
        </div>
      </div>
      <div class="opp-card opp-card--actual">
        <span class="opp-card__icon"><el-icon><CircleCheckFilled /></el-icon></span>
        <div class="opp-card__body">
          <span class="opp-card__label">前工程実績合計</span>
          <span class="opp-card__value">{{ fmt(filteredTotals.actual) }}</span>
        </div>
      </div>
      <div class="opp-card" :class="filteredTotals.diff >= 0 ? 'opp-card--up' : 'opp-card--down'">
        <span class="opp-card__icon">
          <el-icon><component :is="filteredTotals.diff >= 0 ? Top : Bottom" /></el-icon>
        </span>
        <div class="opp-card__body">
          <span class="opp-card__label">差異（前工程実績 − 計画）</span>
          <span class="opp-card__value">{{ signed(filteredTotals.diff) }}</span>
        </div>
      </div>
      <div class="opp-card opp-card--rate">
        <span class="opp-card__icon"><el-icon><TrendCharts /></el-icon></span>
        <div class="opp-card__body">
          <span class="opp-card__label">達成率</span>
          <span class="opp-card__value">{{ rateText(filteredTotals.rate) }}</span>
        </div>
      </div>
      <div class="opp-card opp-card--count">
        <span class="opp-card__icon"><el-icon><OfficeBuilding /></el-icon></span>
        <div class="opp-card__body">
          <span class="opp-card__label">製品 / 外注先</span>
          <span class="opp-card__value">{{ filteredRows.length }} / {{ displayGroups.length }}</span>
        </div>
      </div>
    </section>

    <div class="print-head print-only">
      <h1>外注メッキ計画</h1>
      <div>{{ periodLabel }}　表示：{{ metricLabel }}</div>
    </div>

    <section class="opp-panel">
      <div class="opp-panel__head no-print">
        <div class="opp-panel__head-title">
          <span class="opp-panel__accent" />
          <span class="opp-panel__title">日別二次元表</span>
          <span class="opp-panel__metric" :class="`is-${metric}`">{{ metricLabel }}</span>
        </div>
        <div class="opp-legend" aria-label="凡例">
          <span class="opp-legend__item"><i class="opp-swatch opp-swatch--plan" />前工程計画</span>
          <span class="opp-legend__item"><i class="opp-swatch opp-swatch--actual" />前工程実績</span>
          <span class="opp-legend__item"><i class="opp-swatch opp-swatch--ap" />前工程実計</span>
          <span class="opp-legend__item"><i class="opp-swatch opp-swatch--weekend" />土日</span>
          <span class="opp-legend__item"><i class="opp-swatch opp-swatch--today" />今日</span>
        </div>
      </div>

      <div v-loading="loading" class="opp-panel__body">
        <el-empty
          v-if="!loading && displayGroups.length === 0"
          class="opp-empty"
          :image-size="72"
          description="対象期間の前工程計画・実績がありません"
        >
          <template #image>
            <el-icon class="opp-empty__icon"><Brush /></el-icon>
          </template>
        </el-empty>
        <div v-else class="opp-matrix-wrap">
          <table class="opp-matrix">
            <thead>
              <tr>
                <th class="opp-sticky opp-col-cd">品番</th>
                <th class="opp-sticky opp-col-name">品名</th>
                <th class="opp-sticky opp-col-prev">前工程</th>
                <th class="opp-sticky opp-col-total">合計</th>
                <th
                  v-for="(d, i) in dates"
                  :key="d"
                  class="opp-col-date"
                  :class="{ 'is-weekend': isWeekend(d), 'is-today': d === today }"
                >
                  <div class="opp-date-hd">{{ dateHead(d) }}</div>
                  <div class="opp-wd-hd">{{ weekdays[i] || weekdayLabel(d) }}</div>
                </th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(group, gi) in displayGroups" :key="group.supplier">
                <tr class="opp-group-row" :style="groupTone(gi)">
                  <td class="opp-sticky opp-col-cd opp-group-cell">外注先</td>
                  <td class="opp-sticky opp-col-name opp-group-cell" :title="group.supplier">
                    {{ group.supplier }}
                    <span class="opp-group-count">{{ group.rows.length }} 品</span>
                  </td>
                  <td class="opp-sticky opp-col-prev opp-group-cell" />
                  <td class="opp-sticky opp-col-total opp-group-cell opp-num">{{ fmt(group.total) }}</td>
                  <td
                    v-for="d in dates"
                    :key="`${group.supplier}-${d}`"
                    class="opp-group-cell opp-num"
                    :class="{ 'is-today': d === today }"
                  >
                    {{ fmtCell(group.byDate[d] || 0) }}
                  </td>
                </tr>
                <tr
                  v-for="(row, ri) in group.rows"
                  :key="`${group.supplier}-${row.product_cd}`"
                  class="opp-data-row"
                  :class="{ 'is-alt': ri % 2 === 1 }"
                >
                  <td class="opp-sticky opp-col-cd" :title="row.product_cd">{{ row.product_cd }}</td>
                  <td class="opp-sticky opp-col-name" :title="row.product_name">{{ row.product_name }}</td>
                  <td class="opp-sticky opp-col-prev">{{ row.prev_process_name || '—' }}</td>
                  <td class="opp-sticky opp-col-total opp-num">{{ fmt(rowMetricTotal(row)) }}</td>
                  <td
                    v-for="d in dates"
                    :key="`${row.product_cd}-${d}`"
                    class="opp-cell opp-num"
                    :class="cellClass(row, d)"
                  >
                    {{ fmtCell(cellValue(row, d)) }}
                  </td>
                </tr>
              </template>
            </tbody>
            <tfoot>
              <tr class="opp-total-row">
                <td class="opp-sticky opp-col-cd">合計</td>
                <td class="opp-sticky opp-col-name" />
                <td class="opp-sticky opp-col-prev" />
                <td class="opp-sticky opp-col-total opp-num">{{ fmt(filteredMetricTotal) }}</td>
                <td
                  v-for="d in dates"
                  :key="`total-${d}`"
                  class="opp-num"
                  :class="{ 'is-weekend': isWeekend(d), 'is-today': d === today }"
                >
                  {{ fmtCell(columnTotals[d] || 0) }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Bottom,
  Brush,
  Calendar,
  CircleCheckFilled,
  Download,
  Histogram,
  OfficeBuilding,
  Printer,
  Refresh,
  Search,
  Top,
  TrendCharts,
} from '@element-plus/icons-vue'
import {
  fetchOutsourcedPlatingPlanMatrix,
  type OutsourcedPlatingPlanMatrix,
  type OutsourcedPlatingPlanMatrixRow,
} from '@/api/aps'
import { useApsOperationPermission } from '@/composables/useApsOperationPermission'
import { downloadExcelFromJson } from '@/utils/excelExport'
import { formatDateToYmdJST, getJSTDayOfWeek, getJSTToday } from '@/utils/dateFormat'

defineOptions({ name: 'OutsourcedPlatingPlanning' })

type Metric = 'plan' | 'actual' | 'actual_plan'

const UNSPECIFIED_SUPPLIER = '(未設定)'
const WEEKDAYS_SUN = ['日', '月', '火', '水', '木', '金', '土']
const GROUP_TONES = [
  { bg: '#0f766e', fg: '#ecfdf5' },
  { bg: '#1d4ed8', fg: '#eff6ff' },
  { bg: '#7c3aed', fg: '#f5f3ff' },
  { bg: '#c2410c', fg: '#fff7ed' },
  { bg: '#0e7490', fg: '#ecfeff' },
  { bg: '#b45309', fg: '#fffbeb' },
  { bg: '#be185d', fg: '#fdf2f8' },
  { bg: '#4338ca', fg: '#eef2ff' },
]

const { canExport } = useApsOperationPermission()
const loading = ref(false)
const metric = ref<Metric>('actual_plan')
const selectedSuppliers = ref<string[]>([])
const productKeyword = ref('')
const showZeroRows = ref(false)
const today = getJSTToday()
const matrix = ref<OutsourcedPlatingPlanMatrix | null>(null)

function monthRange(offsetMonths: number): [string, string] {
  const base = getJSTToday()
  const d = new Date(`${base}T12:00:00+09:00`)
  d.setDate(1)
  d.setMonth(d.getMonth() + offsetMonths)
  const start = formatDateToYmdJST(d)
  d.setMonth(d.getMonth() + 1)
  d.setDate(0)
  return [start, formatDateToYmdJST(d)]
}

const periodRange = ref<[string, string]>(monthRange(0))

const periodRangeShortcuts = [
  {
    text: '今月',
    value: () => {
      const [a, b] = monthRange(0)
      return [new Date(`${a}T00:00:00+09:00`), new Date(`${b}T00:00:00+09:00`)] as [Date, Date]
    },
  },
  {
    text: '先月',
    value: () => {
      const [a, b] = monthRange(-1)
      return [new Date(`${a}T00:00:00+09:00`), new Date(`${b}T00:00:00+09:00`)] as [Date, Date]
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

const metricLabel = computed(() => {
  if (metric.value === 'actual') return '前工程実績'
  if (metric.value === 'actual_plan') return '前工程実計'
  return '前工程計画'
})

const dates = computed(() => matrix.value?.dates ?? [])
const weekdays = computed(() => matrix.value?.weekdays ?? [])
const supplierOptions = computed(() => {
  const set = new Set<string>()
  for (const row of matrix.value?.rows ?? []) {
    set.add((row.supplier || '').trim() || UNSPECIFIED_SUPPLIER)
  }
  return [...set].sort((a, b) => a.localeCompare(b, 'ja'))
})

function cellValue(row: OutsourcedPlatingPlanMatrixRow, date: string): number {
  const cell = row.by_date?.[date]
  if (!cell) return 0
  return Number(cell[metric.value] || 0)
}

function rowMetricTotal(row: OutsourcedPlatingPlanMatrixRow): number {
  if (metric.value === 'actual') return Number(row.actual_total || 0)
  if (metric.value === 'actual_plan') return Number(row.actual_plan_total || 0)
  return Number(row.plan_total || 0)
}

const filteredRows = computed(() => {
  const keyword = productKeyword.value.trim().toLowerCase()
  const suppliers = new Set(selectedSuppliers.value)
  return (matrix.value?.rows ?? []).filter((row) => {
    const supplier = (row.supplier || '').trim() || UNSPECIFIED_SUPPLIER
    if (suppliers.size && !suppliers.has(supplier)) return false
    if (keyword) {
      const hay = `${row.product_cd} ${row.product_name}`.toLowerCase()
      if (!hay.includes(keyword)) return false
    }
    if (!showZeroRows.value && rowMetricTotal(row) === 0) return false
    return true
  })
})

const displayGroups = computed(() => {
  const map = new Map<string, OutsourcedPlatingPlanMatrixRow[]>()
  for (const row of filteredRows.value) {
    const supplier = (row.supplier || '').trim() || UNSPECIFIED_SUPPLIER
    const list = map.get(supplier)
    if (list) list.push(row)
    else map.set(supplier, [row])
  }
  return [...map.entries()]
    .sort(([a], [b]) => a.localeCompare(b, 'ja'))
    .map(([supplier, rows]) => {
      const byDate: Record<string, number> = {}
      let total = 0
      for (const row of rows) {
        total += rowMetricTotal(row)
        for (const d of dates.value) {
          byDate[d] = (byDate[d] || 0) + cellValue(row, d)
        }
      }
      return { supplier, rows, total, byDate }
    })
})

const heatMax = computed(() => {
  let max = 0
  for (const row of filteredRows.value) {
    for (const d of dates.value) {
      max = Math.max(max, cellValue(row, d))
    }
  }
  return max
})

const filteredTotals = computed(() => {
  let plan = 0
  let actual = 0
  for (const row of filteredRows.value) {
    plan += Number(row.plan_total || 0)
    actual += Number(row.actual_total || 0)
  }
  return {
    plan,
    actual,
    diff: actual - plan,
    rate: plan > 0 ? (actual / plan) * 100 : null,
  }
})

const filteredMetricTotal = computed(() => {
  if (metric.value === 'actual') return filteredTotals.value.actual
  if (metric.value === 'actual_plan') {
    return filteredRows.value.reduce((sum, row) => sum + Number(row.actual_plan_total || 0), 0)
  }
  return filteredTotals.value.plan
})

const columnTotals = computed(() => {
  const totals: Record<string, number> = {}
  for (const group of displayGroups.value) {
    for (const d of dates.value) {
      totals[d] = (totals[d] || 0) + (group.byDate[d] || 0)
    }
  }
  return totals
})

function isWeekend(ymd: string): boolean {
  const w = getJSTDayOfWeek(ymd)
  return w === 0 || w === 6
}

function weekdayLabel(ymd: string): string {
  return WEEKDAYS_SUN[getJSTDayOfWeek(ymd)] ?? ''
}

function dateHead(ymd: string): string {
  return ymd.slice(5).replace('-', '/')
}

function fmt(n: number): string {
  return Number(n || 0).toLocaleString()
}

function fmtCell(n: number): string {
  if (!n) return ''
  return fmt(n)
}

function signed(n: number): string {
  const v = Number(n || 0)
  if (v > 0) return `+${v.toLocaleString()}`
  return v.toLocaleString()
}

function rateText(rate: number | null): string {
  if (rate == null) return '—'
  return `${rate.toFixed(1)}%`
}

function heatLevel(v: number): number {
  if (!v) return 0
  const max = heatMax.value
  if (max <= 0) return 1
  const r = v / max
  if (r >= 0.75) return 4
  if (r >= 0.5) return 3
  if (r >= 0.25) return 2
  return 1
}

function cellClass(row: OutsourcedPlatingPlanMatrixRow, d: string): Record<string, boolean> {
  const v = cellValue(row, d)
  const heat = heatLevel(v)
  return {
    'is-weekend': isWeekend(d) && v === 0,
    'is-today': d === today,
    'is-filled': v > 0,
    [`is-${metric.value}`]: v > 0,
    [`is-heat-${heat}`]: heat > 0,
  }
}

function groupTone(index: number): Record<string, string> {
  const tone = GROUP_TONES[index % GROUP_TONES.length]!
  return {
    '--opp-group-bg': tone.bg,
    '--opp-group-fg': tone.fg,
  }
}

function applyThisMonth() {
  periodRange.value = monthRange(0)
  void loadMatrix()
}

function applyLastMonth() {
  periodRange.value = monthRange(-1)
  void loadMatrix()
}

async function loadMatrix() {
  const [startDate, endDate] = periodRange.value ?? []
  if (!startDate || !endDate) {
    ElMessage.warning('期間を指定してください')
    return
  }
  loading.value = true
  try {
    matrix.value = await fetchOutsourcedPlatingPlanMatrix({ startDate, endDate })
  } catch {
    matrix.value = null
  } finally {
    loading.value = false
  }
}

function handlePrint() {
  window.print()
}

async function exportExcel() {
  const [startDate, endDate] = periodRange.value ?? []
  const rows: Record<string, string | number>[] = []
  for (const group of displayGroups.value) {
    for (const row of group.rows) {
      const rec: Record<string, string | number> = {
        外注先: group.supplier,
        品番: row.product_cd,
        品名: row.product_name,
        前工程: row.prev_process_name || '',
        合計: rowMetricTotal(row),
      }
      for (const d of dates.value) {
        rec[d] = cellValue(row, d) || ''
      }
      rows.push(rec)
    }
  }
  if (!rows.length) {
    ElMessage.warning('出力するデータがありません')
    return
  }
  const stamp = `${(startDate || '').replaceAll('-', '')}-${(endDate || '').replaceAll('-', '')}`
  await downloadExcelFromJson(rows, metricLabel.value, `外注メッキ計画_${stamp}.xlsx`)
}

onMounted(() => {
  void loadMatrix()
})
</script>

<style scoped>
.opp-page {
  --opp-ink: #134e4a;
  --opp-sub: #64748b;
  --opp-line: #d4dce8;
  --opp-teal: #0d9488;
  --opp-teal-deep: #0f766e;
  --opp-blue: #2563eb;
  --opp-violet: #7c3aed;
  --opp-copper: #c2410c;
  --opp-amber: #d97706;
  --opp-green: #16a34a;
  --opp-red: #dc2626;
  --opp-elev-inset: inset 0 1px 0 rgba(255, 255, 255, 0.92);
  --opp-elev-1: 0 1px 3px rgba(15, 23, 42, 0.07), 0 4px 14px rgba(15, 23, 42, 0.06);
  --opp-metric: var(--opp-teal);
  --opp-metric-soft: #ccfbf1;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: 8px;
  padding: 10px 12px 12px;
  box-sizing: border-box;
  background:
    radial-gradient(900px 420px at 6% -8%, rgba(13, 148, 136, 0.16) 0%, transparent 55%),
    radial-gradient(720px 360px at 100% 0%, rgba(194, 65, 12, 0.1) 0%, transparent 48%),
    linear-gradient(180deg, #f0fdfa 0%, #eef2f8 42%, #e8edf4 100%);
}
.opp-page--actual {
  --opp-metric: var(--opp-blue);
  --opp-metric-soft: #dbeafe;
}
.opp-page--actual_plan {
  --opp-metric: var(--opp-violet);
  --opp-metric-soft: #ede9fe;
}

.opp-hero {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 12px 16px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: var(--opp-elev-1);
  overflow: hidden;
}
.opp-hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--opp-teal-deep) 0%, var(--opp-teal) 42%, var(--opp-copper) 100%);
}
.opp-hero__main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.opp-hero__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(145deg, #2dd4bf 0%, var(--opp-teal) 52%, var(--opp-copper) 100%);
  box-shadow:
    0 6px 14px rgba(13, 148, 136, 0.32),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
  font-size: 20px;
  flex-shrink: 0;
}
.opp-hero__title {
  margin: 0 0 2px;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.01em;
  line-height: 1.2;
  background: linear-gradient(135deg, #134e4a 0%, var(--opp-teal) 70%, var(--opp-copper) 120%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.opp-hero__desc {
  margin: 0;
  font-size: 12px;
  color: var(--opp-sub);
  line-height: 1.45;
}
.opp-hero__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.opp-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 11px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: var(--opp-teal-deep);
  background: linear-gradient(180deg, #fff 0%, #ccfbf1 100%);
  border: 1px solid rgba(13, 148, 136, 0.22);
}
.opp-badge__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--opp-teal);
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.18);
}
.opp-hero__period {
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  padding: 4px 10px;
  border-radius: 999px;
  background: linear-gradient(180deg, #fff 0%, #eef2f7 100%);
  border: 1px solid #d8e2ec;
  font-variant-numeric: tabular-nums;
}

.opp-toolbar {
  padding: 6px 8px;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 55%, #e8eef5 100%);
  border: 1px solid var(--opp-line);
  border-radius: 12px;
  box-shadow: var(--opp-elev-inset), var(--opp-elev-1);
}
.opp-toolbar__body {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.opp-toolbar__strip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 7px;
  border-radius: 8px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  border: 1px solid #d5dde8;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9), 0 1px 3px rgba(15, 23, 42, 0.06);
}
.opp-toolbar__strip--period {
  background: linear-gradient(180deg, #f0fdfa 0%, #ccfbf1 100%);
  border-color: #99f6e4;
}
.opp-toolbar__strip--view {
  background: linear-gradient(180deg, #fff 0%, var(--opp-metric-soft) 100%);
  border-color: #99f6e4;
}
.opp-page--actual .opp-toolbar__strip--view { border-color: #93c5fd; }
.opp-page--actual_plan .opp-toolbar__strip--view { border-color: #c4b5fd; }
.opp-toolbar__strip--filter {
  background: linear-gradient(180deg, #fff7ed 0%, #ffedd5 100%);
  border-color: #fed7aa;
}
.opp-toolbar__strip-label {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #64748b;
  flex-shrink: 0;
}
.opp-toolbar__range { width: 236px; }
.opp-toolbar__supplier { width: 168px; }
.opp-toolbar__keyword { width: 156px; }

.opp-cards {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  flex-shrink: 0;
}
.opp-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 8px 12px;
  background: linear-gradient(165deg, #ffffff 0%, #f8fafc 55%, #f1f5f9 100%);
  border: 1px solid var(--opp-line);
  border-radius: 10px;
  box-shadow: var(--opp-elev-inset), var(--opp-elev-1);
  overflow: hidden;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.opp-card::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--opp-accent, #94a3b8);
}
.opp-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--opp-elev-inset), 0 6px 20px rgba(15, 23, 42, 0.12);
}
.opp-card__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 9px;
  font-size: 16px;
  color: var(--opp-accent, #64748b);
  background: linear-gradient(145deg, #fff 0%, var(--opp-accent-soft, #f1f5f9) 100%);
  border: 1px solid rgba(255, 255, 255, 0.85);
  box-shadow: inset 0 1px 0 #fff, 0 1px 3px rgba(15, 23, 42, 0.08);
  flex-shrink: 0;
}
.opp-card__body {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}
.opp-card__label {
  font-size: 10px;
  font-weight: 700;
  color: var(--opp-sub);
  letter-spacing: 0.02em;
}
.opp-card__value {
  font-size: 18px;
  font-weight: 800;
  line-height: 1.15;
  color: var(--opp-ink);
  font-variant-numeric: tabular-nums;
}
.opp-card--plan { --opp-accent: var(--opp-teal); --opp-accent-soft: #ccfbf1; }
.opp-card--plan .opp-card__value { color: var(--opp-teal-deep); }
.opp-card--actual { --opp-accent: var(--opp-blue); --opp-accent-soft: #dbeafe; }
.opp-card--actual .opp-card__value { color: #1d4ed8; }
.opp-card--rate { --opp-accent: var(--opp-violet); --opp-accent-soft: #ede9fe; }
.opp-card--rate .opp-card__value { color: #6d28d9; }
.opp-card--count { --opp-accent: var(--opp-copper); --opp-accent-soft: #ffedd5; }
.opp-card--count .opp-card__value { color: var(--opp-copper); }
.opp-card--up { --opp-accent: var(--opp-green); --opp-accent-soft: #dcfce7; }
.opp-card--up .opp-card__value { color: var(--opp-green); }
.opp-card--down { --opp-accent: var(--opp-red); --opp-accent-soft: #fee2e2; }
.opp-card--down .opp-card__value { color: var(--opp-red); }

.opp-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid var(--opp-line);
  border-radius: 12px;
  box-shadow: var(--opp-elev-inset), var(--opp-elev-1);
  overflow: hidden;
}
.opp-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  padding: 7px 12px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%);
}
.opp-panel__head-title {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.opp-panel__accent {
  width: 3px;
  height: 14px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--opp-teal), var(--opp-copper));
}
.opp-panel__title {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
}
.opp-panel__metric {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  color: var(--opp-metric);
  background: var(--opp-metric-soft);
  border: 1px solid var(--opp-metric-soft);
}
.opp-legend {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 12px;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}
.opp-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.opp-swatch {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  border: 1px solid rgba(15, 23, 42, 0.12);
}
.opp-swatch--plan { background: #99f6e4; }
.opp-swatch--actual { background: #93c5fd; }
.opp-swatch--ap { background: #c4b5fd; }
.opp-swatch--weekend { background: #fecaca; }
.opp-swatch--today {
  background: #fff;
  box-shadow: inset 0 -3px 0 var(--opp-teal);
}

.opp-panel__body {
  flex: 1;
  min-height: 220px;
  overflow: hidden;
}
.opp-empty {
  padding: 48px 0;
}
.opp-empty__icon {
  font-size: 42px;
  color: #99f6e4;
}
.opp-matrix-wrap {
  height: 100%;
  max-height: calc(100vh - 292px);
  overflow: auto;
}
.opp-matrix {
  width: max-content;
  min-width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 12px;
}
.opp-matrix th,
.opp-matrix td {
  border-right: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
  padding: 4px 6px;
  white-space: nowrap;
}
.opp-matrix thead th {
  position: sticky;
  top: 0;
  z-index: 3;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  text-align: center;
  font-weight: 700;
  color: #334155;
  box-shadow: 0 1px 0 #d8e2ec;
}
.opp-sticky {
  position: sticky;
  background: #fff;
  z-index: 2;
}
.opp-matrix thead .opp-sticky {
  z-index: 4;
  background: linear-gradient(180deg, #e2e8f0 0%, #cbd5e1 100%);
  color: #0f172a;
}
.opp-col-cd {
  left: 0;
  width: 92px;
  min-width: 92px;
  max-width: 92px;
  text-align: left;
  font-weight: 700;
  color: #334155;
}
.opp-col-name {
  left: 92px;
  width: 140px;
  min-width: 140px;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: left;
  color: #475569;
}
.opp-col-prev {
  left: 232px;
  width: 80px;
  min-width: 80px;
  max-width: 80px;
  text-align: center;
  color: #0f766e;
  font-weight: 700;
  background: #f0fdfa;
}
.opp-matrix thead .opp-col-prev {
  background: #ccfbf1;
  color: #0f766e;
}
.opp-col-total {
  left: 312px;
  width: 72px;
  min-width: 72px;
  text-align: right;
  font-weight: 800;
  background: #f8fafc;
  color: var(--opp-metric);
}
.opp-matrix thead .opp-col-total {
  background: var(--opp-metric-soft);
  color: var(--opp-metric);
}
.opp-col-date {
  min-width: 48px;
  width: 48px;
}
.opp-date-hd {
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}
.opp-wd-hd {
  font-size: 10px;
  color: #64748b;
  line-height: 1.1;
}
.opp-num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.opp-group-row td,
.opp-group-row .opp-sticky {
  background: var(--opp-group-bg, var(--opp-teal-deep));
  color: #fff;
  font-weight: 700;
  border-color: rgba(15, 23, 42, 0.18);
}
.opp-group-row .opp-col-prev {
  background: var(--opp-group-bg, var(--opp-teal-deep));
  color: #fff;
}
.opp-group-count {
  margin-left: 8px;
  font-weight: 500;
  opacity: 0.82;
  font-size: 11px;
}
.opp-total-row .opp-col-prev {
  background: #0f172a;
  color: #fff;
}

.opp-data-row.is-alt td {
  background: #f8fafc;
}
.opp-data-row.is-alt .opp-sticky {
  background: #f8fafc;
}
.opp-data-row:hover td {
  background: #ecfeff;
}
.opp-data-row:hover .opp-sticky {
  background: #ccfbf1;
}
.opp-data-row .opp-col-prev {
  background: #f0fdfa;
}
.opp-data-row.is-alt .opp-col-prev {
  background: #ecfdf5;
}
.opp-data-row:hover .opp-col-prev {
  background: #ccfbf1;
}

.opp-cell.is-plan.is-heat-1 { background: #f0fdfa; color: #0f766e; }
.opp-cell.is-plan.is-heat-2 { background: #ccfbf1; color: #0f766e; font-weight: 700; }
.opp-cell.is-plan.is-heat-3 { background: #5eead4; color: #134e4a; font-weight: 800; }
.opp-cell.is-plan.is-heat-4 { background: #0d9488; color: #fff; font-weight: 800; }

.opp-cell.is-actual.is-heat-1 { background: #eff6ff; color: #1d4ed8; }
.opp-cell.is-actual.is-heat-2 { background: #dbeafe; color: #1d4ed8; font-weight: 700; }
.opp-cell.is-actual.is-heat-3 { background: #93c5fd; color: #1e3a8a; font-weight: 800; }
.opp-cell.is-actual.is-heat-4 { background: #2563eb; color: #fff; font-weight: 800; }

.opp-cell.is-actual_plan.is-heat-1 { background: #f5f3ff; color: #6d28d9; }
.opp-cell.is-actual_plan.is-heat-2 { background: #ede9fe; color: #6d28d9; font-weight: 700; }
.opp-cell.is-actual_plan.is-heat-3 { background: #c4b5fd; color: #4c1d95; font-weight: 800; }
.opp-cell.is-actual_plan.is-heat-4 { background: #7c3aed; color: #fff; font-weight: 800; }

.opp-col-date.is-weekend,
.opp-cell.is-weekend,
.opp-total-row td.is-weekend {
  background: #fff1f2;
}
.opp-col-date.is-weekend .opp-wd-hd,
.opp-col-date.is-weekend .opp-date-hd {
  color: #e11d48;
}
.opp-col-date.is-today {
  background: linear-gradient(180deg, #ecfdf5 0%, #ccfbf1 100%);
  box-shadow: inset 0 -2px 0 var(--opp-teal);
}
.opp-cell.is-today,
.opp-total-row td.is-today,
.opp-group-cell.is-today {
  box-shadow: inset 0 -2px 0 #f59e0b;
}

.opp-total-row td,
.opp-total-row .opp-sticky {
  background: #0f172a;
  color: #fff;
  font-weight: 800;
  border-color: #1e293b;
}
.opp-total-row .opp-col-total {
  color: #5eead4;
}

.print-only { display: none; }

:deep(.opp-toolbar__strip .el-input__wrapper),
:deep(.opp-toolbar__strip .el-select__wrapper) {
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.07);
  background: #fff;
}
:deep(.opp-metric-group .el-radio-button__inner) {
  padding: 5px 11px;
  font-size: 12px;
  font-weight: 700;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
}
:deep(.opp-metric-group .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  color: #fff;
  background: var(--opp-metric);
  border-color: var(--opp-metric) !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.28), 0 2px 6px rgba(13, 148, 136, 0.35);
}
.opp-btn {
  font-weight: 700;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}
.opp-btn:hover:not(:disabled) { transform: translateY(-1px); }
.opp-btn--month {
  color: var(--opp-teal-deep) !important;
  background: linear-gradient(180deg, #fff 0%, #ccfbf1 100%) !important;
  border-color: #5eead4 !important;
}
.opp-btn--last {
  color: #9a3412 !important;
  background: linear-gradient(180deg, #fff 0%, #ffedd5 100%) !important;
  border-color: #fdba74 !important;
}
.opp-btn--primary {
  background: linear-gradient(180deg, #2dd4bf 0%, #0d9488 55%, #0f766e 100%) !important;
  border-color: #0f766e !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.32), 0 2px 6px rgba(13, 148, 136, 0.38) !important;
}
.opp-btn--print {
  color: #b45309 !important;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%) !important;
  border-color: #fcd34d !important;
}
.opp-btn--excel {
  color: #15803d !important;
  background: linear-gradient(180deg, #f0fdf4 0%, #dcfce7 100%) !important;
  border-color: #86efac !important;
}

@media (max-width: 1280px) {
  .opp-cards {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 900px) {
  .opp-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media print {
  .no-print { display: none !important; }
  .print-only { display: block; margin-bottom: 8px; }
  .opp-page {
    padding: 0;
    background: #fff;
    height: auto;
  }
  .opp-panel {
    border: none;
    box-shadow: none;
  }
  .opp-matrix-wrap {
    max-height: none;
    overflow: visible;
  }
  .opp-sticky,
  .opp-matrix thead th {
    position: static;
  }
}
</style>
