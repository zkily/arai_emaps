<template>
  <div class="cmp-page">
    <div class="page-ambient" aria-hidden="true">
      <div class="orb orb-a" />
      <div class="orb orb-b" />
      <div class="orb orb-c" />
    </div>

    <div class="cmp-inner">
      <header class="toolbar toolbar-elevated animate-in" style="--delay: 0ms">
        <div class="toolbar-brand-zone">
          <div class="brand-icon">
            <el-icon :size="20"><DocumentChecked /></el-icon>
          </div>
          <div class="brand-copy">
            <h1 class="toolbar-title">不良・廃棄データ突合</h1>
            <p class="toolbar-sub">生産管理 × 製造 · 不良+廃棄合算</p>
          </div>
        </div>

        <div class="toolbar-filters-zone">
          <div class="filter-chip filter-chip--period">
            <span class="filter-chip__label">対象月</span>
            <el-date-picker
              v-model="filters.month"
              type="month"
              placeholder="YYYY-MM"
              value-format="YYYY-MM"
              size="default"
              class="tf-control tf-control--month"
            />
          </div>

          <div class="filter-chip filter-chip--process">
            <span class="filter-chip__label">工程</span>
            <el-select
              v-model="filters.processCd"
              placeholder="全工程"
              clearable
              filterable
              size="default"
              teleported
              class="tf-control tf-control--process"
            >
              <el-option label="全工程" value="" />
              <el-option
                v-for="p in processOptions"
                :key="p.cd"
                :label="`${p.name} (${p.cd})`"
                :value="p.cd"
              />
            </el-select>
          </div>

          <div class="filter-chip filter-chip--product">
            <span class="filter-chip__label">製品</span>
            <el-select
              v-model="filters.productCd"
              placeholder="全製品"
              clearable
              filterable
              size="default"
              teleported
              class="tf-control tf-control--product"
              :loading="productOptionsLoading"
            >
              <el-option label="全製品" value="" />
              <el-option
                v-for="p in productOptions"
                :key="p.product_cd"
                :label="`${p.product_name} (${p.product_cd})`"
                :value="p.product_cd"
              />
            </el-select>
          </div>

          <div class="filter-chip filter-chip--switch">
            <el-switch v-model="filters.onlyDiff" size="default" active-text="差異のみ" />
          </div>
        </div>

        <div class="toolbar-actions-zone">
          <button type="button" class="action-btn action-btn--primary" :disabled="loading" @click="fetchAll">
            <el-icon v-if="loading" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><Search /></el-icon>
            <span>実行</span>
          </button>
          <button
            type="button"
            class="action-btn action-btn--print"
            :disabled="!contentReady || !kpi"
            @click="handlePrint"
          >
            <el-icon><Printer /></el-icon>
            <span>印刷</span>
          </button>
          <button type="button" class="action-btn action-btn--ghost" @click="resetFilters">
            <el-icon><RefreshLeft /></el-icon>
            <span>リセット</span>
          </button>
        </div>
      </header>

      <div class="meta-strip animate-in" style="--delay: 40ms">
        <div class="meta-strip__left">
          <span v-if="dateRangeLabel" class="period-chip">
            <el-icon :size="15"><Calendar /></el-icon>
            {{ dateRangeLabel }}
          </span>
          <span class="vs-legend">
            <span class="vs-legend__item">
              <span class="vs-legend__dot vs-legend__dot--summary" />生産管理
            </span>
            <span class="vs-legend__vs">VS</span>
            <span class="vs-legend__item">
              <span class="vs-legend__dot vs-legend__dot--source" />製造
            </span>
          </span>
        </div>
        <div class="meta-strip__right">
          <el-icon :size="14"><InfoFilled /></el-icon>
          <span>メッキは日次合計。製造データなしは製造=0。</span>
        </div>
      </div>

      <div class="dash-section kpi-grid" :class="{ 'is-ready': contentReady }" v-loading="loading">
        <article
          v-for="(card, i) in kpiCards"
          :key="card.key"
          class="kpi-card kpi-card--elevated"
          :class="`kpi-card--${card.tone}`"
          :style="{ '--delay': `${60 + i * 55}ms`, '--i': i }"
        >
          <div class="kpi-card__glow" aria-hidden="true" />
          <header class="kpi-card__head">
            <div class="kpi-icon">
              <el-icon :size="18"><component :is="card.icon" /></el-icon>
            </div>
            <div class="kpi-card__titles">
              <h3 class="kpi-card__name">{{ card.label }}</h3>
              <p v-if="card.desc" class="kpi-card__desc">{{ card.desc }}</p>
            </div>
          </header>
          <div class="kpi-metric">
            <div class="kpi-metric__main">
              <span class="kpi-metric__label">{{ card.metricLabel }}</span>
              <span class="kpi-metric__value" :class="card.valueClass">{{ card.value }}</span>
            </div>
            <div v-if="card.sub" class="kpi-metric__foot">
              <span class="kpi-sub">{{ card.sub }}</span>
            </div>
            <div v-if="card.bar != null" class="kpi-bar">
              <div class="kpi-bar__fill" :style="{ width: `${card.bar}%` }" />
            </div>
          </div>
        </article>
      </div>

      <section class="panel panel--chart panel--elevated animate-in" style="--delay: 160ms">
        <div class="panel-head panel-head--chart">
          <div class="chart-head-left">
            <span class="panel-accent panel-accent--blue" />
            <div>
              <h3 class="panel-title">月次トレンド比較</h3>
              <p class="chart-sub">折線=数量 · 柱=差異 · ポイントに数値表示</p>
            </div>
          </div>
          <div class="chart-head-right">
            <span class="chart-range-label">比較期間</span>
            <el-date-picker
              v-model="chartMonthRange"
              type="monthrange"
              range-separator="〜"
              start-placeholder="開始月"
              end-placeholder="終了月"
              value-format="YYYY-MM"
              size="default"
              class="tf-control tf-control--monthrange"
              :clearable="false"
              :disabled-date="disableChartMonth"
            />
            <button
              type="button"
              class="action-btn action-btn--ghost action-btn--sm"
              :disabled="chartLoading"
              @click="fetchMonthly"
            >
              <el-icon v-if="chartLoading" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><TrendCharts /></el-icon>
              <span>更新</span>
            </button>
          </div>
        </div>
        <div class="chart-body" v-loading="chartLoading">
          <div ref="trendChartRef" class="trend-chart" />
          <div v-if="!chartLoading && !monthlyRows.length" class="chart-empty">
            比較期間を選んで「実行」または「更新」してください
          </div>
        </div>
      </section>

      <section
        v-if="kpi && contentReady"
        class="vs-panel vs-panel--elevated animate-in"
        style="--delay: 220ms"
      >
        <div class="vs-side vs-side--summary">
          <div class="vs-side-head">
            <span class="vs-badge vs-badge--summary">生産管理</span>
            <span class="vs-side-hint">production_summarys</span>
          </div>
          <div class="vs-metric-grid vs-metric-grid--single">
            <div class="vs-metric vs-metric--summary">
              <span class="vs-metric-label">不良+廃棄</span>
              <span class="vs-metric-value">{{ fmtNum(kpi.summary_total) }}</span>
            </div>
          </div>
        </div>
        <div class="vs-center" aria-hidden="true">
          <span class="vs-pulse" />
          <span class="vs-center-text">VS</span>
        </div>
        <div class="vs-side vs-side--source">
          <div class="vs-side-head">
            <span class="vs-badge vs-badge--source">製造</span>
            <span class="vs-side-hint">各工程指標 / MES</span>
          </div>
          <div class="vs-metric-grid">
            <div class="vs-metric vs-metric--source">
              <span class="vs-metric-label">不良+廃棄</span>
              <span class="vs-metric-value">{{ fmtNum(kpi.source_total) }}</span>
            </div>
            <div class="vs-metric vs-metric--match">
              <span class="vs-metric-label">一致率</span>
              <span class="vs-metric-value">{{ kpi.match_rate.toFixed(1) }}<small>%</small></span>
            </div>
          </div>
        </div>
        <div class="vs-diff-bar">
          <div class="vs-diff-label">
            <span>差異（製造 − 生産管理）</span>
            <strong :class="diffClass(kpi.total_diff)">{{ fmtSigned(kpi.total_diff) }}</strong>
          </div>
          <div class="vs-diff-track">
            <div
              class="vs-diff-fill"
              :class="diffClass(kpi.total_diff)"
              :style="{ width: `${diffBarWidth}%` }"
            />
          </div>
          <div class="vs-diff-stats">
            <span class="stat-chip stat-chip--danger">不一致 {{ fmtNum(kpi.mismatch_count) }}</span>
            <span class="stat-chip stat-chip--amber">生産のみ {{ fmtNum(kpi.only_summary_count) }}</span>
            <span class="stat-chip stat-chip--orange">製造のみ {{ fmtNum(kpi.only_source_count) }}</span>
          </div>
        </div>
      </section>

      <section class="panel panel--main panel--elevated animate-in" style="--delay: 280ms">
        <div class="panel-head panel-head--tabs">
          <div class="tab-switcher">
            <button
              type="button"
              class="tab-btn"
              :class="{ 'tab-btn--active': activeTab === 'summary' }"
              @click="switchTab('summary')"
            >
              <el-icon :size="15"><Histogram /></el-icon>
              工程別サマリ
            </button>
            <button
              type="button"
              class="tab-btn"
              :class="{ 'tab-btn--active': activeTab === 'detail' }"
              @click="switchTab('detail')"
            >
              <el-icon :size="15"><List /></el-icon>
              品番×日×工程明細
              <span v-if="detailTotal" class="tab-badge">{{ detailTotal }}</span>
            </button>
          </div>
          <span class="panel-hint">
            {{ activeTab === 'summary' ? `${summaryRows.length} 工程` : `${detailTotal} 行` }}
          </span>
        </div>

        <div v-show="activeTab === 'summary'" class="tab-body">
          <div class="table-wrap">
            <el-table
              :data="summaryRows"
              stripe
              size="default"
              class="data-table data-table--summary"
              empty-text="データがありません — 期間を選んで「実行」を押してください"
            >
              <el-table-column prop="process_name" label="工程" min-width="112" fixed>
                <template #default="{ row }">
                  <span class="process-tag" :class="processTagClass(row.process_cd)">
                    {{ row.process_name }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="生産管理" width="118" align="right" class-name="col-summary">
                <template #default="{ row }">
                  <span class="qty qty--summary">{{ fmtNum(row.summary_total) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="製造" width="108" align="right" class-name="col-source">
                <template #default="{ row }">
                  <span class="qty qty--source">{{ fmtNum(row.source_total) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="差異" width="100" align="right">
                <template #default="{ row }">
                  <span class="diff-pill" :class="diffClass(row.total_diff)">{{ fmtSigned(row.total_diff) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="件数" width="72" align="right">
                <template #default="{ row }">{{ fmtNum(row.item_count) }}</template>
              </el-table-column>
              <el-table-column label="一致率" min-width="140">
                <template #default="{ row }">
                  <div class="rate-cell">
                    <div class="rate-track">
                      <div
                        class="rate-fill"
                        :class="rateFillClass(row.match_rate)"
                        :style="{ width: `${clampRate(row.match_rate)}%` }"
                      />
                    </div>
                    <span class="rate-text">{{ row.match_rate.toFixed(1) }}%</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="備考" min-width="120" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="na-cell">{{ row.source_note || '' }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <div v-show="activeTab === 'detail'" class="tab-body" v-loading="detailLoading">
          <div class="table-wrap">
            <el-table
              :data="detailRows"
              stripe
              size="default"
              class="data-table data-table--detail"
              :row-class-name="detailRowClass"
              empty-text="データがありません"
            >
              <el-table-column prop="product_cd" label="品番" width="96" fixed>
                <template #default="{ row }">
                  <span class="mono-cd">{{ row.product_cd }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="品名" min-width="120" show-overflow-tooltip />
              <el-table-column prop="production_day" label="日付" width="104" />
              <el-table-column prop="process_name" label="工程" width="92">
                <template #default="{ row }">
                  <span class="process-tag" :class="processTagClass(row.process_cd)">
                    {{ row.process_name }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="生産管理" width="104" align="right" class-name="col-summary">
                <template #default="{ row }">
                  <span class="qty qty--summary">{{ fmtNum(row.summary_total) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="製造" width="96" align="right" class-name="col-source">
                <template #default="{ row }">
                  <el-tooltip
                    v-if="row.status === 'not_comparable'"
                    :content="row.source_note || '該当なし'"
                    placement="top"
                  >
                    <span class="na-cell">該当なし</span>
                  </el-tooltip>
                  <span v-else class="qty qty--source">{{ fmtSourceQty(row.source_total) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="差異" width="88" align="right">
                <template #default="{ row }">
                  <span v-if="row.total_diff != null" class="diff-pill" :class="diffClass(row.total_diff)">
                    {{ fmtSigned(row.total_diff) }}
                  </span>
                  <span v-else class="na-cell">—</span>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状態" width="112" align="center">
                <template #default="{ row }">
                  <span class="status-pill" :class="`status-pill--${row.status}`">
                    {{ statusLabel(row.status) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div class="pager-wrap">
            <el-pagination
              v-model:current-page="detailPage"
              v-model:page-size="detailLimit"
              :total="detailTotal"
              :page-sizes="[50, 100, 200, 500]"
              layout="total, sizes, prev, pager, next"
              size="default"
              background
              @current-change="fetchDetail"
              @size-change="onDetailSizeChange"
            />
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import {
  Calendar,
  DocumentChecked,
  Histogram,
  InfoFilled,
  List,
  Loading,
  PieChart,
  Printer,
  RefreshLeft,
  Search,
  TrendCharts,
  Warning,
  WarningFilled,
} from '@element-plus/icons-vue'
import { getProducts, type Product } from '@/api/stocktake/common'
import {
  defectScrapComparisonApi,
  type DefectScrapComparisonDetailRow,
  type DefectScrapComparisonKpi,
  type DefectScrapComparisonMonthlyRow,
  type DefectScrapComparisonStatus,
  type DefectScrapComparisonSummaryRow,
} from '@/api/erp/defectScrapComparison'
import { openPrintWindow, PRINT_POPUP_BLOCKED_MSG } from '@/utils/printWindow'
import { buildDefectScrapComparisonPrintHtml } from './defectScrapComparisonPrint'

const PROCESS_OPTIONS = [
  { cd: 'KT01', name: '切断' },
  { cd: 'KT02', name: '面取' },
  { cd: 'KT04', name: '成型' },
  { cd: 'KT05', name: 'メッキ' },
  { cd: 'KT07', name: '溶接' },
  { cd: 'KT09', name: '検査' },
]

const defaultMonth = dayjs().format('YYYY-MM')

function defaultChartRange(endMonth: string): [string, string] {
  const end = dayjs(`${endMonth}-01`)
  const start = end.subtract(2, 'month')
  return [start.format('YYYY-MM'), end.format('YYYY-MM')]
}

const loading = ref(false)
const detailLoading = ref(false)
const chartLoading = ref(false)
const contentReady = ref(false)
const activeTab = ref<'summary' | 'detail'>('summary')
const processOptions = PROCESS_OPTIONS
const productOptions = ref<Product[]>([])
const productOptionsLoading = ref(false)

const filters = ref({
  month: defaultMonth,
  processCd: '',
  productCd: '',
  onlyDiff: false,
})

const chartMonthRange = ref<[string, string]>(defaultChartRange(defaultMonth))
const monthlyRows = ref<DefectScrapComparisonMonthlyRow[]>([])
const trendChartRef = ref<HTMLDivElement | null>(null)
let trendChart: ECharts | null = null

const kpi = ref<DefectScrapComparisonKpi | null>(null)
const summaryRows = ref<DefectScrapComparisonSummaryRow[]>([])
const detailRows = ref<DefectScrapComparisonDetailRow[]>([])
const detailPage = ref(1)
const detailLimit = ref(50)
const detailTotal = ref(0)

const periodBounds = computed(() => {
  const m = filters.value.month
  if (!m) return { start: '', end: '' }
  const start = dayjs(`${m}-01`).startOf('month').format('YYYY-MM-DD')
  const end = dayjs(`${m}-01`).endOf('month').format('YYYY-MM-DD')
  return { start, end }
})

const dateRangeLabel = computed(() => {
  const { start, end } = periodBounds.value
  if (!start || !end) return ''
  return `${filters.value.month}（${start} ～ ${end}）`
})

const fmtNum = (v?: number | null) => (v == null ? '0' : Number(v).toLocaleString())
const fmtSigned = (v: number) => {
  const n = Number(v)
  if (n > 0) return `+${n.toLocaleString()}`
  return n.toLocaleString()
}
const fmtSourceQty = (v: number | null | undefined) => (v == null ? '—' : fmtNum(v))
const clampRate = (v: number) => Math.max(0, Math.min(100, Number(v) || 0))

const diffClass = (v: number) => {
  if (v > 0) return 'num-pos'
  if (v < 0) return 'num-neg'
  return 'num-zero'
}

const rateFillClass = (rate: number) => {
  if (rate >= 95) return 'rate-fill--good'
  if (rate >= 70) return 'rate-fill--mid'
  return 'rate-fill--low'
}

const processTagClass = (cd?: string) => {
  const map: Record<string, string> = {
    KT01: 'process-tag--cut',
    KT02: 'process-tag--chamfer',
    KT04: 'process-tag--form',
    KT05: 'process-tag--plate',
    KT07: 'process-tag--weld',
    KT09: 'process-tag--inspect',
  }
  return cd ? map[cd] || '' : ''
}

const STATUS_LABEL: Record<DefectScrapComparisonStatus, string> = {
  match: '一致',
  mismatch: '不一致',
  only_summary: '生産管理のみ',
  only_source: '製造のみ',
  not_comparable: '突合不可',
  plating_daily_only: '日次のみ',
}

const statusLabel = (s: DefectScrapComparisonStatus) => STATUS_LABEL[s] ?? s

const detailRowClass = ({ row }: { row: DefectScrapComparisonDetailRow }) => {
  if (row.status === 'mismatch') return 'row-mismatch'
  if (row.status === 'only_summary' || row.status === 'only_source') return 'row-partial'
  if (row.status === 'not_comparable') return 'row-muted'
  return ''
}

const diffBarWidth = computed(() => {
  const k = kpi.value
  if (!k) return 0
  const base = Math.max(Math.abs(k.summary_total), Math.abs(k.source_total), 1)
  return Math.min(100, (Math.abs(k.total_diff) / base) * 100)
})

const kpiCards = computed(() => {
  const k = kpi.value
  return [
    {
      key: 'summary',
      tone: 'summary',
      icon: WarningFilled,
      label: '生産管理',
      desc: 'production_summarys',
      metricLabel: '不良+廃棄',
      value: fmtNum(k?.summary_total),
      sub: '',
      valueClass: '',
      bar: null as number | null,
    },
    {
      key: 'source',
      tone: 'source',
      icon: Warning,
      label: '製造',
      desc: '工程指標 / MES',
      metricLabel: '不良+廃棄',
      value: fmtNum(k?.source_total),
      sub: '',
      valueClass: '',
      bar: null as number | null,
    },
    {
      key: 'diff',
      tone: 'diff',
      icon: Warning,
      label: '差異',
      desc: '製造 − 生産管理',
      metricLabel: '差分',
      value: fmtSigned(k?.total_diff ?? 0),
      sub: `生産のみ ${fmtNum(k?.only_summary_count)} / 製造のみ ${fmtNum(k?.only_source_count)}`,
      valueClass: diffClass(k?.total_diff ?? 0),
      bar: null as number | null,
    },
    {
      key: 'match',
      tone: 'match',
      icon: PieChart,
      label: '一致率',
      desc: '',
      metricLabel: '一致率',
      value: k ? `${k.match_rate.toFixed(1)}%` : '0%',
      sub: `不一致 ${fmtNum(k?.mismatch_count)}`,
      valueClass: '',
      bar: k ? clampRate(k.match_rate) : 0,
    },
  ]
})

function buildParams(extra: { view: 'summary' | 'detail' | 'monthly'; page?: number; limit?: number }) {
  const { start, end } = periodBounds.value
  return {
    startDate: start,
    endDate: end,
    processCd: filters.value.processCd || undefined,
    productCd: filters.value.productCd?.trim() || undefined,
    onlyDiff: filters.value.onlyDiff,
    view: extra.view,
    page: extra.page,
    limit: extra.limit,
    sort_by: 'total_diff',
    sort_order: 'desc' as const,
  }
}

function chartPeriodBounds() {
  const range = chartMonthRange.value
  if (!range?.[0] || !range?.[1]) return { start: '', end: '' }
  const start = dayjs(`${range[0]}-01`).startOf('month').format('YYYY-MM-DD')
  const end = dayjs(`${range[1]}-01`).endOf('month').format('YYYY-MM-DD')
  return { start, end }
}

function disableChartMonth(d: Date) {
  const range = chartMonthRange.value
  if (!range?.[0] || !range?.[1]) return false
  // Element Plus monthrange の片側選択中は内部状態任せ。将来月は制限しない。
  return dayjs(d).isAfter(dayjs(), 'month')
}

function buildTrendChartOption(rows: DefectScrapComparisonMonthlyRow[]): EChartsOption {
  if (!rows.length) {
    return {
      title: {
        text: 'データなし',
        left: 'center',
        top: 'middle',
        textStyle: { color: '#94a3b8', fontSize: 13, fontWeight: 600 },
      },
    }
  }
  const labels = rows.map((r) => r.label || r.year_month)
  const summary = rows.map((r) => r.summary_total)
  const source = rows.map((r) => r.source_total)
  const diff = rows.map((r) => r.total_diff)
  const fmt = (v: number) => {
    const n = Number(v) || 0
    return n > 0 ? `+${n.toLocaleString()}` : n.toLocaleString()
  }
  return {
    animationDuration: 650,
    animationEasing: 'cubicOut',
    labelLayout: { hideOverlap: true },
    legend: {
      top: 4,
      right: 10,
      itemWidth: 18,
      itemHeight: 11,
      itemGap: 16,
      icon: 'roundRect',
      textStyle: { fontSize: 12, color: '#475569', fontWeight: 700 },
    },
    grid: { left: 12, right: 20, top: 48, bottom: 14, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        crossStyle: { color: '#94a3b8' },
        lineStyle: { type: 'dashed', color: '#94a3b8' },
      },
      backgroundColor: 'rgba(255,255,255,0.97)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      padding: [10, 12],
      extraCssText: 'box-shadow:0 8px 24px rgba(15,23,42,0.12);border-radius:10px;',
      textStyle: { color: '#334155', fontSize: 13 },
      formatter: (params: unknown) => {
        const arr = Array.isArray(params) ? params : [params]
        const idx = (arr[0] as { dataIndex?: number })?.dataIndex ?? 0
        const row = rows[idx]
        const lines = [
          `<div style="font-weight:800;margin-bottom:6px;font-size:14px">${row?.year_month ?? ''}</div>`,
          ...arr.map((p) => {
            const item = p as { marker?: string; seriesName?: string; value?: number }
            const val = Number(item.value ?? 0)
            const shown = item.seriesName === '差異' ? fmt(val) : val.toLocaleString()
            return `<div style="display:flex;justify-content:space-between;gap:18px;margin:3px 0;font-size:13px">${item.marker ?? ''}<span>${item.seriesName}</span><b style="font-variant-numeric:tabular-nums">${shown}</b></div>`
          }),
          `<div style="margin-top:6px;padding-top:6px;border-top:1px solid #e2e8f0;color:#64748b;font-size:12px">一致率 <b>${row?.match_rate?.toFixed(1) ?? 0}%</b></div>`,
        ]
        return lines.join('')
      },
    },
    xAxis: {
      type: 'category',
      boundaryGap: true,
      data: labels,
      axisLabel: {
        color: '#334155',
        fontSize: 13,
        fontWeight: 800,
        margin: 12,
      },
      axisLine: { lineStyle: { color: '#cbd5e1', width: 1.5 } },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: 'value',
        name: '数量',
        nameTextStyle: { color: '#94a3b8', fontSize: 11, padding: [0, 0, 0, 8] },
        splitLine: { lineStyle: { type: 'dashed', color: '#e8eef5' } },
        axisLabel: {
          color: '#64748b',
          fontSize: 11,
          formatter: (v: number) => Number(v).toLocaleString(),
        },
      },
      {
        type: 'value',
        name: '差異',
        nameTextStyle: { color: '#94a3b8', fontSize: 11 },
        splitLine: { show: false },
        axisLabel: {
          color: '#94a3b8',
          fontSize: 11,
          formatter: (v: number) => fmt(v),
        },
      },
    ],
    series: [
      {
        name: '生産管理',
        type: 'line',
        smooth: 0.35,
        symbol: 'circle',
        symbolSize: 11,
        z: 3,
        data: summary,
        lineStyle: {
          width: 3.5,
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#60a5fa' },
            { offset: 1, color: '#2563eb' },
          ]),
          shadowColor: 'rgba(37, 99, 235, 0.35)',
          shadowBlur: 8,
          shadowOffsetY: 3,
        },
        itemStyle: {
          color: '#2563eb',
          borderWidth: 2.5,
          borderColor: '#fff',
          shadowColor: 'rgba(37, 99, 235, 0.4)',
          shadowBlur: 6,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(37, 99, 235, 0.28)' },
            { offset: 1, color: 'rgba(37, 99, 235, 0.02)' },
          ]),
        },
        label: {
          show: true,
          position: 'top',
          distance: 6,
          color: '#1d4ed8',
          fontSize: 12,
          fontWeight: 800,
          formatter: (p: { value?: number }) => Number(p.value ?? 0).toLocaleString(),
        },
        emphasis: { focus: 'series', scale: 1.15 },
      },
      {
        name: '製造',
        type: 'line',
        smooth: 0.35,
        symbol: 'circle',
        symbolSize: 11,
        z: 3,
        data: source,
        lineStyle: {
          width: 3.5,
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#fb923c' },
            { offset: 1, color: '#ea580c' },
          ]),
          shadowColor: 'rgba(234, 88, 12, 0.35)',
          shadowBlur: 8,
          shadowOffsetY: 3,
        },
        itemStyle: {
          color: '#ea580c',
          borderWidth: 2.5,
          borderColor: '#fff',
          shadowColor: 'rgba(234, 88, 12, 0.4)',
          shadowBlur: 6,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(234, 88, 12, 0.22)' },
            { offset: 1, color: 'rgba(234, 88, 12, 0.02)' },
          ]),
        },
        label: {
          show: true,
          position: 'top',
          distance: 6,
          color: '#c2410c',
          fontSize: 12,
          fontWeight: 800,
          formatter: (p: { value?: number }) => Number(p.value ?? 0).toLocaleString(),
        },
        emphasis: { focus: 'series', scale: 1.15 },
      },
      {
        name: '差異',
        type: 'bar',
        yAxisIndex: 1,
        barMaxWidth: 40,
        barGap: '30%',
        z: 1,
        data: diff.map((v) => ({
          value: v,
          itemStyle: {
            borderRadius: v >= 0 ? [7, 7, 2, 2] : [2, 2, 7, 7],
            color:
              v >= 0
                ? new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#f87171' },
                    { offset: 1, color: '#b91c1c' },
                  ])
                : new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#93c5fd' },
                    { offset: 1, color: '#1d4ed8' },
                  ]),
            shadowColor: v >= 0 ? 'rgba(185, 28, 28, 0.25)' : 'rgba(29, 78, 216, 0.25)',
            shadowBlur: 8,
            shadowOffsetY: 2,
          },
          label: {
            position: v >= 0 ? 'top' : 'bottom',
            color: v >= 0 ? '#b91c1c' : '#1d4ed8',
          },
        })),
        label: {
          show: true,
          distance: 5,
          fontSize: 11,
          fontWeight: 800,
          formatter: (p: { value?: number }) => fmt(Number(p.value ?? 0)),
        },
        emphasis: {
          focus: 'series',
          itemStyle: { shadowBlur: 12 },
        },
      },
    ],
  }
}

function ensureTrendChart() {
  if (!trendChartRef.value) return null
  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value, undefined, { renderer: 'canvas' })
  }
  return trendChart
}

function renderTrendChart() {
  const chart = ensureTrendChart()
  if (!chart) return
  chart.setOption(buildTrendChartOption(monthlyRows.value), true)
}

function onTrendChartResize() {
  trendChart?.resize()
}

async function fetchSummary() {
  const data = await defectScrapComparisonApi.getComparison(buildParams({ view: 'summary' }))
  summaryRows.value = (data.list as DefectScrapComparisonSummaryRow[]) ?? []
  kpi.value = data.kpi
}

async function fetchDetail() {
  const { start, end } = periodBounds.value
  if (!start || !end) return
  detailLoading.value = true
  try {
    const data = await defectScrapComparisonApi.getComparison(
      buildParams({ view: 'detail', page: detailPage.value, limit: detailLimit.value }),
    )
    detailRows.value = (data.list as DefectScrapComparisonDetailRow[]) ?? []
    detailTotal.value = data.total ?? 0
    if (data.kpi) kpi.value = data.kpi
  } finally {
    detailLoading.value = false
  }
}

async function fetchMonthly() {
  const { start, end } = chartPeriodBounds()
  if (!start || !end) {
    ElMessage.warning('比較期間を選択してください')
    return
  }
  const months =
    dayjs(end).startOf('month').diff(dayjs(start).startOf('month'), 'month') + 1
  if (months > 12) {
    ElMessage.warning('比較期間は最大12ヶ月までです')
    return
  }
  chartLoading.value = true
  try {
    const data = await defectScrapComparisonApi.getComparison({
      startDate: start,
      endDate: end,
      processCd: filters.value.processCd || undefined,
      productCd: filters.value.productCd?.trim() || undefined,
      onlyDiff: false,
      view: 'monthly',
    })
    monthlyRows.value = (data.list as DefectScrapComparisonMonthlyRow[]) ?? []
    await nextTick()
    renderTrendChart()
  } catch {
    monthlyRows.value = []
    ElMessage.error('月次トレンドの取得に失敗しました')
    renderTrendChart()
  } finally {
    chartLoading.value = false
  }
}

async function fetchAll() {
  const { start, end } = periodBounds.value
  if (!start || !end) {
    ElMessage.warning('対象月を選択してください')
    return
  }
  // 対象月に合わせて比較期間の終端を追随（開始は維持、逆転時は再計算）
  const [, chartEnd] = chartMonthRange.value
  if (filters.value.month !== chartEnd) {
    const startKeep = chartMonthRange.value[0]
    if (dayjs(`${startKeep}-01`).isAfter(dayjs(`${filters.value.month}-01`), 'month')) {
      chartMonthRange.value = defaultChartRange(filters.value.month)
    } else {
      chartMonthRange.value = [startKeep, filters.value.month]
    }
  }
  loading.value = true
  contentReady.value = false
  try {
    detailPage.value = 1
    await Promise.all([fetchSummary(), fetchDetail(), fetchMonthly()])
    contentReady.value = true
  } catch {
    ElMessage.error('突合データの取得に失敗しました')
    summaryRows.value = []
    detailRows.value = []
    kpi.value = null
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.value = {
    month: defaultMonth,
    processCd: '',
    productCd: '',
    onlyDiff: false,
  }
  chartMonthRange.value = defaultChartRange(defaultMonth)
  summaryRows.value = []
  detailRows.value = []
  monthlyRows.value = []
  kpi.value = null
  detailTotal.value = 0
  contentReady.value = false
  renderTrendChart()
}

function switchTab(name: 'summary' | 'detail') {
  activeTab.value = name
}

function onDetailSizeChange() {
  detailPage.value = 1
  fetchDetail()
}

function buildPrintMeta() {
  const processLabel = filters.value.processCd
    ? processOptions.find((p) => p.cd === filters.value.processCd)?.name || filters.value.processCd
    : '全工程'
  const product = productOptions.value.find((p) => p.product_cd === filters.value.productCd)
  const productLabel = filters.value.productCd
    ? product
      ? `${product.product_name} (${product.product_cd})`
      : filters.value.productCd
    : '全製品'
  const [cStart, cEnd] = chartMonthRange.value || ['', '']
  return {
    printedAt: dayjs().format('YYYY-MM-DD HH:mm'),
    targetMonth: filters.value.month,
    dateRangeLabel: dateRangeLabel.value.replace(`${filters.value.month}（`, '').replace('）', ''),
    processLabel,
    productLabel,
    onlyDiff: filters.value.onlyDiff,
    chartRangeLabel: cStart && cEnd ? `${cStart} 〜 ${cEnd}` : '',
  }
}

function handlePrint() {
  if (!contentReady.value || !kpi.value) {
    ElMessage.warning('先に「実行」してデータを取得してください')
    return
  }
  try {
    const html = buildDefectScrapComparisonPrintHtml({
      ...buildPrintMeta(),
      kpi: kpi.value,
      summaryRows: summaryRows.value,
      monthlyRows: monthlyRows.value,
    })
    const ok = openPrintWindow(html)
    if (!ok) ElMessage.warning(PRINT_POPUP_BLOCKED_MSG)
  } catch {
    ElMessage.error('印刷レポートの作成に失敗しました')
  }
}

async function loadProductOptions() {
  productOptionsLoading.value = true
  try {
    productOptions.value = await getProducts()
  } catch {
    productOptions.value = []
  } finally {
    productOptionsLoading.value = false
  }
}

watch(contentReady, async (ready) => {
  if (ready) {
    await nextTick()
    renderTrendChart()
  }
})

onMounted(() => {
  loadProductOptions()
  window.addEventListener('resize', onTrendChartResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onTrendChartResize)
  trendChart?.dispose()
  trendChart = null
})
</script>

<style scoped lang="scss">
.cmp-page {
  --cmp-summary: #2563eb;
  --cmp-source: #ea580c;
  --cmp-success: #059669;
  --cmp-danger: #dc2626;
  --cmp-amber: #d97706;
  --fs-title: 1.08rem;
  --fs-subtitle: 0.78rem;
  --fs-body: 0.875rem;
  --fs-label: 0.75rem;
  --fs-meta: 0.8125rem;
  --fs-kpi: 1.65rem;
  --fs-kpi-sm: 1.35rem;
  --radius-lg: 16px;
  --radius-md: 12px;
  --radius-sm: 9px;
  --shadow-soft: 0 1px 0 rgba(255, 255, 255, 0.95) inset, 0 10px 28px rgba(15, 23, 42, 0.08),
    0 2px 8px rgba(15, 23, 42, 0.04);
  position: relative;
  min-height: 100%;
  padding: 14px 16px 22px;
  box-sizing: border-box;
  overflow: hidden;
  color: #0f172a;
  font-size: var(--fs-body);
  line-height: 1.45;
}

.page-ambient {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background: linear-gradient(155deg, #eef4ff 0%, #f7f9fc 38%, #fff8f1 100%);
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: orb-float 18s ease-in-out infinite;
}

.orb-a {
  width: 380px;
  height: 380px;
  top: -120px;
  right: 6%;
  background: radial-gradient(circle, #93c5fd 0%, transparent 70%);
}

.orb-b {
  width: 300px;
  height: 300px;
  bottom: 6%;
  left: -70px;
  background: radial-gradient(circle, #fdba74 0%, transparent 70%);
  animation-delay: -6s;
}

.orb-c {
  width: 240px;
  height: 240px;
  top: 46%;
  right: 20%;
  background: radial-gradient(circle, #6ee7b7 0%, transparent 70%);
  animation-delay: -11s;
}

@keyframes orb-float {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(12px, -14px) scale(1.05);
  }
}

.cmp-inner {
  position: relative;
  z-index: 1;
  max-width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.animate-in {
  animation: fade-up 0.48s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--delay, 0ms);
}

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Toolbar ── */
.toolbar {
  display: flex;
  align-items: stretch;
  flex-wrap: nowrap;
  gap: 0;
  border-radius: var(--radius-lg);
  overflow: hidden;
  min-height: 64px;
}

.toolbar-elevated {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.94) 100%);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: var(--shadow-soft);
}

.toolbar-brand-zone {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  flex-shrink: 0;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.9) 0%, rgba(255, 255, 255, 0.4) 100%);
}

.brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: linear-gradient(145deg, #3b82f6 0%, #1d4ed8 100%);
  color: #fff;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 6px 16px rgba(37, 99, 235, 0.42);
}

.brand-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.toolbar-title {
  margin: 0;
  font-size: var(--fs-title);
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
  line-height: 1.25;
  white-space: nowrap;
}

.toolbar-sub {
  margin: 0;
  font-size: var(--fs-label);
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}

.toolbar-filters-zone {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
  gap: 10px;
  padding: 0 12px;
  border-left: 1px solid rgba(15, 23, 42, 0.06);
  border-right: 1px solid rgba(15, 23, 42, 0.06);
  overflow-x: auto;
  scrollbar-width: thin;
}

.filter-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  padding: 6px 10px;
  border-radius: 10px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.9) inset;
}

.filter-chip__label {
  font-size: var(--fs-label);
  font-weight: 800;
  white-space: nowrap;
  letter-spacing: 0.02em;
}

.filter-chip--period .filter-chip__label {
  color: #2563eb;
}
.filter-chip--process .filter-chip__label {
  color: #0f766e;
}
.filter-chip--product .filter-chip__label {
  color: #c2410c;
}

.filter-chip--switch {
  padding: 6px 12px;
}

.filter-chip--switch :deep(.el-switch__label) {
  font-size: var(--fs-label) !important;
  font-weight: 700;
  color: #475569;
}

.tf-control--month {
  width: 128px !important;
}
.tf-control--monthrange {
  width: 250px !important;
}
.tf-control--process {
  width: 168px !important;
}
.tf-control--product {
  width: 190px !important;
}

.tf-control :deep(.el-input__wrapper),
.tf-control :deep(.el-select__wrapper) {
  background: #fff;
  border-radius: 8px;
  min-height: 34px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 0 0 1px rgba(15, 23, 42, 0.08);
}

.tf-control :deep(.el-input__inner),
.tf-control :deep(.el-select__selected-item),
.tf-control :deep(.el-select__placeholder) {
  font-size: 0.8125rem !important;
  font-weight: 600;
}

.toolbar-actions-zone {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  flex-shrink: 0;
  background: linear-gradient(180deg, rgba(241, 245, 249, 0.75) 0%, rgba(226, 232, 240, 0.45) 100%);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 16px;
  border: none;
  border-radius: 9px;
  font-size: 0.8125rem;
  font-weight: 800;
  cursor: pointer;
  white-space: nowrap;
  transition:
    transform 0.15s ease,
    filter 0.15s ease,
    box-shadow 0.15s ease;
}

.action-btn--primary {
  color: #fff;
  background: linear-gradient(180deg, #4f8ef7 0%, #2563eb 100%);
  box-shadow:
    0 2px 0 #1d4ed8,
    0 6px 16px rgba(37, 99, 235, 0.38);
}

.action-btn--primary:hover:not(:disabled) {
  filter: brightness(1.05);
  transform: translateY(-1px);
}
.action-btn--primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-btn--ghost {
  color: #334155;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%);
  box-shadow:
    0 1px 0 #cbd5e1,
    0 3px 8px rgba(15, 23, 42, 0.08);
}

.action-btn--ghost:hover:not(:disabled) {
  color: #0f172a;
  transform: translateY(-1px);
}

.action-btn--print {
  color: #fff;
  background: linear-gradient(180deg, #34d399 0%, #059669 100%);
  box-shadow:
    0 2px 0 #047857,
    0 6px 14px rgba(5, 150, 105, 0.32);
}

.action-btn--print:hover:not(:disabled) {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

.action-btn--print:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn--sm {
  height: 32px;
  padding: 0 12px;
  font-size: 0.75rem;
}

.action-btn .is-loading {
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── Meta strip ── */
.meta-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
}

.meta-strip__left {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.meta-strip__right {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: var(--fs-meta);
  font-weight: 600;
  color: #92400e;
  background: linear-gradient(135deg, rgba(254, 243, 199, 0.95), rgba(253, 230, 138, 0.4));
  padding: 7px 12px;
  border-radius: 8px;
  border: 1px solid rgba(251, 191, 36, 0.4);
}

.period-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 12px;
  border-radius: 9px;
  font-size: var(--fs-meta);
  font-weight: 800;
  color: #1d4ed8;
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.98), rgba(191, 219, 254, 0.5));
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.85) inset;
}

.vs-legend {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: var(--fs-meta);
  font-weight: 700;
  color: #475569;
}

.vs-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.vs-legend__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.22);
}

.vs-legend__dot--summary {
  background: var(--cmp-summary);
}
.vs-legend__dot--source {
  background: var(--cmp-source);
}

.vs-legend__vs {
  font-size: 0.7rem;
  font-weight: 900;
  color: #94a3b8;
  letter-spacing: 0.06em;
}

/* ── KPI ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  min-height: 118px;
}

@media (max-width: 1100px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.kpi-card {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
}

.kpi-card--elevated {
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.99) 0%, rgba(248, 250, 252, 0.94) 100%);
  border: 1px solid rgba(255, 255, 255, 0.95);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft);
  transition:
    transform 0.28s ease,
    box-shadow 0.28s ease;
}

.kpi-card--elevated:hover {
  transform: translateY(-3px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 14px 32px rgba(15, 23, 42, 0.12);
}

.kpi-card__glow {
  position: absolute;
  top: -30%;
  right: -10%;
  width: 110px;
  height: 110px;
  border-radius: 50%;
  opacity: 0.34;
  filter: blur(26px);
  pointer-events: none;
}

.kpi-card--summary .kpi-card__glow {
  background: #60a5fa;
}
.kpi-card--source .kpi-card__glow {
  background: #fb923c;
}
.kpi-card--diff .kpi-card__glow {
  background: #f87171;
}
.kpi-card--match .kpi-card__glow {
  background: #34d399;
}

.kpi-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 12px;
  bottom: 12px;
  width: 4px;
  border-radius: 0 4px 4px 0;
}

.kpi-card--summary::before {
  background: linear-gradient(180deg, #93c5fd, #2563eb);
}
.kpi-card--source::before {
  background: linear-gradient(180deg, #fdba74, #ea580c);
}
.kpi-card--diff::before {
  background: linear-gradient(180deg, #fca5a5, #dc2626);
}
.kpi-card--match::before {
  background: linear-gradient(180deg, #6ee7b7, #059669);
}

.kpi-card__head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  position: relative;
  z-index: 1;
}

.kpi-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.65) inset;
}

.kpi-card--summary .kpi-icon {
  background: linear-gradient(145deg, rgba(191, 219, 254, 0.95), rgba(59, 130, 246, 0.16));
  color: #2563eb;
}
.kpi-card--source .kpi-icon {
  background: linear-gradient(145deg, rgba(254, 215, 170, 0.95), rgba(249, 115, 22, 0.16));
  color: #ea580c;
}
.kpi-card--diff .kpi-icon {
  background: linear-gradient(145deg, rgba(254, 202, 202, 0.95), rgba(239, 68, 68, 0.14));
  color: #dc2626;
}
.kpi-card--match .kpi-icon {
  background: linear-gradient(145deg, rgba(167, 243, 208, 0.95), rgba(16, 185, 129, 0.16));
  color: #059669;
}

.kpi-card__name {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.kpi-card__desc {
  margin: 3px 0 0;
  font-size: var(--fs-label);
  font-weight: 600;
  color: #94a3b8;
}

.kpi-metric {
  position: relative;
  z-index: 1;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(248, 250, 252, 0.88);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.9) inset;
}

.kpi-metric__main {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.kpi-metric__label {
  font-size: var(--fs-label);
  font-weight: 700;
  color: #64748b;
}

.kpi-metric__value {
  font-size: var(--fs-kpi);
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.kpi-card--summary .kpi-metric__value {
  color: var(--cmp-summary);
}
.kpi-card--source .kpi-metric__value {
  color: var(--cmp-source);
}

.kpi-metric__foot {
  margin-top: 6px;
}
.kpi-sub {
  font-size: var(--fs-label);
  font-weight: 600;
  color: #64748b;
}

.kpi-bar {
  margin-top: 8px;
  height: 6px;
  border-radius: 99px;
  background: rgba(226, 232, 240, 0.95);
  overflow: hidden;
}

.kpi-bar__fill {
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, #34d399, #059669);
  box-shadow: 0 0 10px rgba(5, 150, 105, 0.35);
  transition: width 0.5s ease;
}

.kpi-grid:not(.is-ready) .kpi-card--elevated {
  opacity: 0;
}
.kpi-grid.is-ready .kpi-card--elevated {
  animation: kpi-pop 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--delay, 0ms);
}

@keyframes kpi-pop {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ── Chart / panels ── */
.panel--elevated {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.95) 100%);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.98), rgba(241, 245, 249, 0.6));
}

.panel-head--chart {
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.panel-head--tabs {
  justify-content: space-between;
}

.chart-head-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chart-head-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.chart-range-label {
  font-size: var(--fs-label);
  font-weight: 800;
  color: #2563eb;
  white-space: nowrap;
}

.chart-sub {
  margin: 3px 0 0;
  font-size: var(--fs-label);
  font-weight: 600;
  color: #64748b;
}

.panel-accent {
  width: 4px;
  height: 34px;
  border-radius: 3px;
  flex-shrink: 0;
}

.panel-accent--blue {
  background: linear-gradient(180deg, #60a5fa, #2563eb);
  box-shadow: 0 2px 10px rgba(37, 99, 235, 0.35);
}

.panel-title {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.panel-hint {
  font-size: var(--fs-meta);
  font-weight: 700;
  color: #64748b;
}

.chart-body {
  position: relative;
  padding: 8px 14px 14px;
  min-height: 300px;
  background:
    radial-gradient(ellipse 80% 55% at 18% 0%, rgba(219, 234, 254, 0.4), transparent 55%),
    radial-gradient(ellipse 70% 50% at 88% 100%, rgba(255, 237, 213, 0.32), transparent 50%);
}

.trend-chart {
  width: 100%;
  height: 300px;
}

.chart-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--fs-meta);
  font-weight: 700;
  color: #94a3b8;
  pointer-events: none;
}

/* ── VS panel ── */
.vs-panel {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  grid-template-rows: auto auto;
  gap: 0;
  overflow: hidden;
  border-radius: var(--radius-lg);
}

.vs-panel--elevated {
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.96) 0%, rgba(255, 255, 255, 0.94) 100%);
  border: 1px solid rgba(147, 197, 253, 0.4);
  box-shadow: var(--shadow-soft);
}

.vs-side {
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.vs-side--summary {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%);
}

.vs-side--source {
  background: linear-gradient(225deg, rgba(249, 115, 22, 0.1) 0%, transparent 100%);
}

.vs-side-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.vs-side-hint {
  font-size: var(--fs-label);
  font-weight: 600;
  color: #94a3b8;
}

.vs-badge {
  font-size: 0.72rem;
  font-weight: 800;
  padding: 5px 11px;
  border-radius: 8px;
  letter-spacing: 0.04em;
}

.vs-badge--summary {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  box-shadow: 0 3px 10px rgba(37, 99, 235, 0.38);
}

.vs-badge--source {
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: #fff;
  box-shadow: 0 3px 10px rgba(234, 88, 12, 0.38);
}

.vs-metric-grid {
  display: grid;
  grid-template-columns: 1.25fr 1fr;
  gap: 10px;
}

.vs-metric-grid--single {
  grid-template-columns: 1fr;
}

.vs-metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.06);
}

.vs-metric-label {
  font-size: var(--fs-label);
  font-weight: 700;
  color: #64748b;
}

.vs-metric-value {
  font-size: 1.35rem;
  font-weight: 800;
  color: #1e293b;
  font-variant-numeric: tabular-nums;
  line-height: 1.15;
  letter-spacing: -0.02em;
}

.vs-metric-value--sm {
  font-size: 1.15rem;
}

.vs-metric-value small {
  font-size: 0.75rem;
  font-weight: 700;
  color: #94a3b8;
  margin-left: 2px;
}

.vs-metric--summary .vs-metric-value {
  color: var(--cmp-summary);
}
.vs-metric--source .vs-metric-value {
  color: var(--cmp-source);
}
.vs-metric--match .vs-metric-value {
  color: var(--cmp-success);
}

.vs-center {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 56px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.7), rgba(241, 245, 249, 0.9));
  border-left: 1px solid rgba(148, 163, 184, 0.2);
  border-right: 1px solid rgba(148, 163, 184, 0.2);
}

.vs-pulse {
  position: absolute;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(37, 99, 235, 0.16);
  animation: vs-pulse 2s ease-in-out infinite;
}

@keyframes vs-pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.55;
  }
  50% {
    transform: scale(1.35);
    opacity: 0.15;
  }
}

.vs-center-text {
  position: relative;
  z-index: 1;
  font-size: 0.8125rem;
  font-weight: 900;
  color: #2563eb;
  letter-spacing: 0.06em;
}

.vs-diff-bar {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 18px;
  background: rgba(248, 250, 252, 0.92);
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.vs-diff-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: var(--fs-label);
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
  min-width: 140px;
}

.vs-diff-label strong {
  font-size: 1.2rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.vs-diff-track {
  flex: 1;
  height: 8px;
  border-radius: 99px;
  background: rgba(226, 232, 240, 0.95);
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06) inset;
}

.vs-diff-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.45s ease;
  max-width: 100%;
}

.vs-diff-fill.num-pos {
  background: linear-gradient(90deg, #fca5a5, #dc2626);
}
.vs-diff-fill.num-neg {
  background: linear-gradient(90deg, #93c5fd, #2563eb);
}
.vs-diff-fill.num-zero {
  background: #cbd5e1;
  width: 2% !important;
}

.vs-diff-stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.stat-chip {
  font-size: var(--fs-label);
  font-weight: 750;
  padding: 5px 10px;
  border-radius: 8px;
  white-space: nowrap;
}

.stat-chip--danger {
  background: rgba(254, 226, 226, 0.95);
  color: #b91c1c;
}
.stat-chip--amber {
  background: rgba(254, 243, 199, 0.95);
  color: #b45309;
}
.stat-chip--orange {
  background: rgba(255, 237, 213, 0.98);
  color: #c2410c;
}

/* ── Tabs ── */
.tab-switcher {
  display: flex;
  gap: 6px;
  padding: 4px;
  border-radius: 11px;
  background: rgba(226, 232, 240, 0.6);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06) inset;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 14px;
  border: none;
  border-radius: 8px;
  background: transparent;
  font-size: 0.8125rem;
  font-weight: 750;
  color: #64748b;
  cursor: pointer;
  transition:
    background 0.15s ease,
    color 0.15s ease,
    box-shadow 0.15s ease;
}

.tab-btn--active {
  color: #1d4ed8;
  background: linear-gradient(180deg, #fff 0%, #eff6ff 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 3px 8px rgba(37, 99, 235, 0.16);
}

.tab-badge {
  background: linear-gradient(180deg, #60a5fa, #2563eb);
  color: #fff;
  font-size: 0.7rem;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 999px;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.35);
}

.tab-body {
  padding: 12px 14px 14px;
}

.table-wrap {
  overflow: auto;
  border-radius: 10px;
  border: 1px solid rgba(226, 232, 240, 0.98);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.85) inset;
}

.pager-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

/* ── Table ── */
.data-table {
  --el-table-border-color: rgba(226, 232, 240, 0.95);
  --el-table-header-bg-color: #f1f5f9;
  --el-table-row-hover-bg-color: rgba(239, 246, 255, 0.6);
  font-size: 0.875rem;
}

.data-table :deep(.el-table__header th) {
  font-size: 0.78rem;
  font-weight: 800;
  color: #475569;
  letter-spacing: 0.02em;
  padding: 12px 0;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%) !important;
}

.data-table :deep(.el-table__cell) {
  padding: 10px 0;
  font-size: 0.875rem;
}

.data-table :deep(.col-summary) {
  background: rgba(239, 246, 255, 0.5) !important;
}

.data-table :deep(.col-source) {
  background: rgba(255, 247, 237, 0.58) !important;
}

.data-table :deep(th.col-summary) {
  color: #1d4ed8 !important;
  background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%) !important;
}

.data-table :deep(th.col-source) {
  color: #c2410c !important;
  background: linear-gradient(180deg, #ffedd5 0%, #fed7aa 100%) !important;
}

.qty {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  font-size: 0.9rem;
}

.qty--summary {
  color: var(--cmp-summary);
}
.qty--source {
  color: var(--cmp-source);
}

.mono-cd {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-weight: 750;
  font-size: 0.8125rem;
  color: #334155;
}

.process-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 9px;
  border-radius: 7px;
  font-size: 0.75rem;
  font-weight: 800;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.55) inset;
}

.process-tag--cut {
  background: rgba(219, 234, 254, 0.98);
  color: #1d4ed8;
}
.process-tag--chamfer {
  background: rgba(204, 251, 241, 0.98);
  color: #0f766e;
}
.process-tag--form {
  background: rgba(237, 233, 254, 0.98);
  color: #6d28d9;
}
.process-tag--plate {
  background: rgba(254, 249, 195, 0.98);
  color: #a16207;
}
.process-tag--weld {
  background: rgba(255, 237, 213, 0.98);
  color: #c2410c;
}
.process-tag--inspect {
  background: rgba(220, 252, 231, 0.98);
  color: #15803d;
}

.rate-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rate-track {
  flex: 1;
  height: 7px;
  border-radius: 99px;
  background: rgba(226, 232, 240, 0.95);
  overflow: hidden;
  min-width: 56px;
}

.rate-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.4s ease;
}

.rate-fill--good {
  background: linear-gradient(90deg, #34d399, #059669);
}
.rate-fill--mid {
  background: linear-gradient(90deg, #fbbf24, #d97706);
}
.rate-fill--low {
  background: linear-gradient(90deg, #f87171, #dc2626);
}

.rate-text {
  font-size: 0.8125rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #475569;
  min-width: 48px;
  text-align: right;
}

.diff-pill {
  display: inline-block;
  padding: 3px 9px;
  border-radius: 7px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  font-size: 0.8125rem;
}

.diff-pill.num-pos {
  color: #b91c1c;
  background: rgba(254, 226, 226, 0.9);
}
.diff-pill.num-neg {
  color: #1d4ed8;
  background: rgba(219, 234, 254, 0.95);
}
.diff-pill.num-zero {
  color: #94a3b8;
  background: rgba(241, 245, 249, 0.95);
}

.num-pos {
  color: #dc2626;
}
.num-neg {
  color: #2563eb;
}
.num-zero {
  color: #94a3b8;
}

.na-cell {
  color: #94a3b8;
  font-style: italic;
  font-size: 0.8125rem;
}

.status-pill {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 7px;
  font-size: 0.72rem;
  font-weight: 800;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.5) inset;
}

.status-pill--match {
  background: rgba(16, 185, 129, 0.16);
  color: #059669;
}
.status-pill--mismatch {
  background: rgba(239, 68, 68, 0.16);
  color: #dc2626;
}
.status-pill--only_summary,
.status-pill--only_source {
  background: rgba(251, 191, 36, 0.2);
  color: #d97706;
}
.status-pill--not_comparable,
.status-pill--plating_daily_only {
  background: rgba(148, 163, 184, 0.2);
  color: #64748b;
}

:deep(.row-mismatch > td) {
  background: rgba(254, 226, 226, 0.45) !important;
}
:deep(.row-partial > td) {
  background: rgba(254, 243, 199, 0.35) !important;
}
:deep(.row-muted > td) {
  opacity: 0.75;
}

@media (max-width: 960px) {
  .toolbar {
    flex-wrap: wrap;
  }
  .toolbar-brand-zone {
    width: 100%;
    padding: 12px 14px;
  }
  .toolbar-actions-zone {
    width: 100%;
    justify-content: flex-end;
    padding: 10px 14px;
  }
  .vs-panel {
    grid-template-columns: 1fr;
  }
  .vs-center {
    width: 100%;
    height: 40px;
    border: none;
    border-top: 1px solid rgba(148, 163, 184, 0.2);
    border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  }
}
</style>

