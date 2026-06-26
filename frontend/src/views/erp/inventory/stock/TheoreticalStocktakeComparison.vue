<template>
  <div class="cmp-page">
    <div class="page-ambient" aria-hidden="true">
      <div class="orb orb-a" />
      <div class="orb orb-b" />
      <div class="orb orb-c" />
    </div>

    <div class="cmp-inner">
      <!-- Toolbar：标题 + 筛选 + 操作 同一行 -->
      <header class="toolbar toolbar-elevated animate-in" style="--delay: 0ms">
        <div class="toolbar-brand-zone">
          <div class="brand-icon">
            <el-icon :size="18"><ScaleToOriginal /></el-icon>
          </div>
          <h1 class="toolbar-title">理論在庫 vs 棚卸在庫 比較</h1>
        </div>

        <div class="toolbar-filters-zone">
          <div class="filter-inline filter-inline--period">
            <span class="filter-inline__label">対象月</span>
            <el-date-picker
              v-model="filters.month"
              type="month"
              placeholder="YYYY-MM"
              value-format="YYYY-MM"
              size="small"
              class="tf-control tf-control--month"
              @change="onMonthChange"
            />
          </div>

          <span class="filter-sep" aria-hidden="true" />

          <div class="filter-inline filter-inline--process">
            <span class="filter-inline__label">工程</span>
            <el-select
              v-model="filters.processCd"
              placeholder="全工程"
              clearable
              filterable
              size="small"
              teleported
              popper-class="cmp-select-popper cmp-process-popper"
              class="tf-control tf-control--process"
            >
              <el-option label="全工程" value="">
                <div class="process-option process-option--all">
                  <span class="process-option__name">全工程</span>
                  <span v-if="allProcessStats" class="process-option__stats">
                    理論 {{ fmtNum(allProcessStats.theoretical_qty) }}
                    · 棚卸 {{ fmtNum(allProcessStats.stocktake_qty) }}
                    · <span :class="diffClass(allProcessStats.diff_qty)">Δ{{ fmtSigned(allProcessStats.diff_qty) }}</span>
                  </span>
                </div>
              </el-option>
              <el-option
                v-for="item in processSelectOptions"
                :key="item.cd"
                :label="item.displayLabel"
                :value="item.cd"
              >
                <div class="process-option">
                  <span class="process-option__name">{{ item.name }} ({{ item.cd }})</span>
                  <span v-if="item.hasStats" class="process-option__stats">
                    理論 {{ fmtNum(item.theoretical_qty) }}
                    · 棚卸 {{ fmtNum(item.stocktake_qty) }}
                    · <span :class="diffClass(item.diff_qty)">Δ{{ fmtSigned(item.diff_qty) }}</span>
                    · {{ fmtNum(item.item_count) }}品目
                  </span>
                  <span v-else class="process-option__stats process-option__stats--muted">実行後に数量表示</span>
                </div>
              </el-option>
            </el-select>
          </div>

          <span class="filter-sep" aria-hidden="true" />

          <div class="filter-inline filter-inline--product">
            <span class="filter-inline__label">製品</span>
            <el-select
              v-model="filters.productCd"
              placeholder="全製品"
              clearable
              filterable
              size="small"
              teleported
              popper-class="cmp-select-popper"
              class="tf-control tf-control--product"
              :loading="productOptionsLoading"
            >
              <el-option label="全製品" value="" />
              <el-option
                v-for="p in productOptions"
                :key="p.product_cd"
                :label="`${p.product_name} (${p.product_cd})`"
                :value="p.product_cd"
              >
                <div class="product-option">
                  <span class="product-option__name">{{ p.product_name }}</span>
                  <span class="product-option__cd">{{ p.product_cd }}</span>
                </div>
              </el-option>
            </el-select>
          </div>

          <span class="filter-sep" aria-hidden="true" />

          <div class="filter-inline filter-inline--switch">
            <el-switch v-model="filters.onlyDiff" size="small" active-text="差異のみ" />
          </div>
        </div>

        <div class="toolbar-actions-zone">
          <button type="button" class="action-btn action-btn--primary" :disabled="loading" @click="fetchAll">
            <el-icon v-if="loading" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><Search /></el-icon>
            <span>実行</span>
          </button>
          <button type="button" class="action-btn action-btn--ghost" @click="resetFilters">
            <el-icon><RefreshLeft /></el-icon>
            <span>リセット</span>
          </button>
          <button
            type="button"
            class="action-btn action-btn--ghost"
            :disabled="loading || !hasData"
            @click="handleExport"
          >
            <el-icon><Download /></el-icon>
            <span>Excel</span>
          </button>
          <button
            type="button"
            class="action-btn action-btn--ghost"
            :disabled="loading || !hasData"
            @click="handlePrint"
          >
            <el-icon><Printer /></el-icon>
            <span>サマリ印刷</span>
          </button>
          <button
            type="button"
            class="action-btn action-btn--ghost"
            :disabled="loading || !hasData"
            @click="handlePrintDetail"
          >
            <el-icon><Printer /></el-icon>
            <span>明細印刷</span>
          </button>
        </div>
      </header>

      <!-- Period ribbon -->
      <div v-if="asOfDate" class="period-ribbon animate-in" style="--delay: 60ms">
        <span class="period-chip period-chip--month">
          <el-icon :size="14"><Calendar /></el-icon>
          {{ filters.month }}
        </span>
        <span class="period-divider" />
        <span class="period-meta">理論基準日 <strong>{{ asOfDate }}</strong></span>
        <span class="period-divider" />
        <span class="period-meta">棚卸集計 <strong>{{ monthRangeLabel }}</strong></span>
      </div>

      <!-- KPI -->
      <div class="dash-section kpi-grid" :class="{ 'is-ready': contentReady }" v-loading="loading">
        <article
          v-for="(card, i) in kpiCards"
          :key="card.key"
          class="kpi-card kpi-card--elevated"
          :class="`kpi-card--${card.tone}`"
          :style="{ '--delay': `${80 + i * 70}ms`, '--i': i }"
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
              <span class="kpi-metric__label">数量</span>
              <span class="kpi-metric__value">{{ card.value }}</span>
            </div>
            <div v-if="card.sub" class="kpi-metric__foot">
              <span class="kpi-sub">{{ card.sub }}</span>
            </div>
          </div>
        </article>
      </div>

      <!-- VS 比較サマリ -->
      <section
        v-if="kpi && contentReady"
        class="vs-panel vs-panel--elevated animate-in"
        style="--delay: 280ms"
      >
        <div class="vs-side vs-side--theoretical">
          <div class="vs-side-head">
            <span class="vs-badge vs-badge--theoretical">理論在庫</span>
            <strong class="vs-month">{{ asOfDate }}</strong>
          </div>
          <div class="vs-metric-grid">
            <div class="vs-metric vs-metric--theoretical">
              <span class="vs-metric-label">合計数量</span>
              <span class="vs-metric-value">{{ fmtNum(kpi.theoretical_qty_total) }}</span>
            </div>
            <div class="vs-metric">
              <span class="vs-metric-label">理論のみ</span>
              <span class="vs-metric-value">{{ fmtNum(kpi.only_theoretical_count) }}<small>件</small></span>
            </div>
            <div class="vs-metric">
              <span class="vs-metric-label">品目×工程</span>
              <span class="vs-metric-value">{{ fmtNum(kpi.item_count) }}<small>件</small></span>
            </div>
          </div>
        </div>
        <div class="vs-center" aria-hidden="true">
          <span class="vs-pulse" />
          <span class="vs-center-text">VS</span>
        </div>
        <div class="vs-side vs-side--stocktake">
          <div class="vs-side-head">
            <span class="vs-badge vs-badge--stocktake">棚卸在庫</span>
            <strong class="vs-month">{{ filters.month }}</strong>
          </div>
          <div class="vs-metric-grid">
            <div class="vs-metric vs-metric--stocktake">
              <span class="vs-metric-label">合計数量</span>
              <span class="vs-metric-value">{{ fmtNum(kpi.stocktake_qty_total) }}</span>
            </div>
            <div class="vs-metric">
              <span class="vs-metric-label">棚卸のみ</span>
              <span class="vs-metric-value">{{ fmtNum(kpi.only_stocktake_count) }}<small>件</small></span>
            </div>
            <div class="vs-metric vs-metric--match">
              <span class="vs-metric-label">一致率</span>
              <span class="vs-metric-value">{{ kpi.match_rate.toFixed(1) }}<small>%</small></span>
            </div>
          </div>
        </div>
        <div class="vs-diff-bar">
          <div class="vs-diff-label">
            <span>差異合計</span>
            <strong :class="diffClass(kpi.diff_qty_total)">{{ fmtSigned(kpi.diff_qty_total) }}</strong>
          </div>
          <div class="vs-diff-track">
            <div
              class="vs-diff-fill"
              :class="kpi.diff_qty_total >= 0 ? 'vs-diff-fill--pos' : 'vs-diff-fill--neg'"
              :style="{ width: diffBarWidth + '%' }"
            />
          </div>
          <span class="vs-diff-hint">不一致 {{ fmtNum(kpi.mismatch_count) }} 件</span>
        </div>
      </section>

      <!-- Main content -->
      <section class="panel panel--main animate-in" style="--delay: 360ms">
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
              品目×工程明細
              <span v-if="detailTotal" class="tab-badge">{{ detailTotal }}</span>
            </button>
          </div>
          <span class="panel-hint">{{ activeTab === 'summary' ? `${summaryRows.length} 工程` : `${detailTotal} 行` }}</span>
        </div>

        <!-- Summary tab -->
        <div v-show="activeTab === 'summary'" class="tab-body">
          <div class="chart-panel">
            <div class="chart-panel-head">
              <span class="panel-accent panel-accent--blue" />
              <span class="chart-panel-title">工程別数量比較</span>
              <div class="chart-legend">
                <span class="legend-item legend-item--theoretical"><i />理論在庫</span>
                <span class="legend-item legend-item--stocktake"><i />棚卸在庫</span>
              </div>
            </div>
            <div class="chart-canvas-wrap">
              <div v-if="!summaryRows.length && !loading" class="chart-empty">
                <el-icon :size="40"><DataAnalysis /></el-icon>
                <p>データがありません — 対象月を選んで「実行」を押してください</p>
              </div>
              <div v-else ref="summaryChartRef" class="chart-canvas" />
            </div>
          </div>

          <div class="table-wrap">
            <el-table
              :data="summaryRows"
              stripe
              border
              size="small"
              class="data-table data-table--summary"
              empty-text="データがありません"
            >
              <el-table-column prop="process_name" label="工程" min-width="110" fixed>
                <template #default="{ row }">
                  <span class="process-cell">
                    <span class="process-dot" />
                    {{ row.process_name }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column
                prop="theoretical_qty"
                label="理論在庫"
                width="115"
                align="right"
                label-class-name="th-theoretical"
                class-name="td-theoretical"
              >
                <template #default="{ row }">
                  <span class="qty-pill qty-pill--theoretical">{{ fmtNum(row.theoretical_qty) }}</span>
                </template>
              </el-table-column>
              <el-table-column
                prop="stocktake_qty"
                label="棚卸在庫"
                width="115"
                align="right"
                label-class-name="th-stocktake"
                class-name="td-stocktake"
              >
                <template #default="{ row }">
                  <span class="qty-pill qty-pill--stocktake">{{ fmtNum(row.stocktake_qty) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="diff_qty" label="差異" width="100" align="right">
                <template #default="{ row }">
                  <span class="diff-pill" :class="diffClass(row.diff_qty)">{{ fmtSigned(row.diff_qty) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="diff_rate" label="差異率" width="88" align="right">
                <template #default="{ row }">
                  <span v-if="row.diff_rate != null" class="rate-text">{{ row.diff_rate.toFixed(1) }}%</span>
                  <span v-else class="rate-text rate-text--muted">—</span>
                </template>
              </el-table-column>
              <el-table-column prop="item_count" label="品目数" width="76" align="right" />
              <el-table-column prop="matched_count" label="一致" width="68" align="right">
                <template #default="{ row }">
                  <span class="count-good">{{ fmtNum(row.matched_count) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="mismatch_count" label="不一致" width="76" align="right">
                <template #default="{ row }">
                  <span class="count-bad">{{ fmtNum(row.mismatch_count) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="match_rate" label="一致率" width="88" align="right">
                <template #default="{ row }">
                  <span class="rate-text">{{ row.match_rate.toFixed(1) }}%</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- Detail tab -->
        <div v-show="activeTab === 'detail'" class="tab-body">
          <div class="table-wrap" v-loading="detailLoading">
            <el-table
              :data="detailRows"
              stripe
              border
              size="small"
              class="data-table data-table--detail"
              empty-text="データがありません"
              :row-class-name="detailRowClass"
            >
              <el-table-column prop="product_cd" label="製品CD" width="118" fixed>
                <template #default="{ row }">
                  <code class="product-code">{{ row.product_cd }}</code>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="製品名" min-width="160" show-overflow-tooltip />
              <el-table-column prop="process_name" label="工程" width="96">
                <template #default="{ row }">
                  <span class="process-tag">{{ row.process_name }}</span>
                </template>
              </el-table-column>
              <el-table-column
                prop="theoretical_qty"
                label="理論"
                width="92"
                align="right"
                class-name="td-theoretical"
              >
                <template #default="{ row }">{{ fmtNum(row.theoretical_qty) }}</template>
              </el-table-column>
              <el-table-column
                prop="stocktake_qty"
                label="棚卸"
                width="92"
                align="right"
                class-name="td-stocktake"
              >
                <template #default="{ row }">{{ fmtNum(row.stocktake_qty) }}</template>
              </el-table-column>
              <el-table-column prop="diff_qty" label="差異" width="92" align="right">
                <template #default="{ row }">
                  <span class="diff-pill" :class="diffClass(row.diff_qty)">{{ fmtSigned(row.diff_qty) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状態" width="108" align="center">
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
              size="small"
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
import * as echarts from 'echarts'
import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'
import { ElMessage } from 'element-plus'
import {
  Calendar,
  DataAnalysis,
  Download,
  Histogram,
  List,
  Loading,
  Printer,
  RefreshLeft,
  ScaleToOriginal,
  Search,
  Box,
  DocumentChecked,
  Warning,
  PieChart,
} from '@element-plus/icons-vue'
import { fetchProcesses } from '@/api/master/processMaster'
import { getProducts, type Product } from '@/api/stocktake/common'
import {
  inventoryComparisonApi,
  type ComparisonDetailRow,
  type ComparisonKpi,
  type ComparisonStatus,
  type ComparisonSummaryRow,
} from '@/api/inventoryComparison'
import type { OptionItem } from '@/types/master'
import { openPrintWindow, PRINT_POPUP_BLOCKED_MSG } from '@/utils/printWindow'
import {
  buildTheoreticalStocktakeComparisonDetailPrintHtml,
  buildTheoreticalStocktakeComparisonPrintHtml,
} from './theoreticalStocktakeComparisonPrint'

const STOCKTAKE_PROCESS_CDS = new Set([
  'KT01', 'KT02', 'KT04', 'KT05', 'KT06', 'KT07', 'KT08', 'KT09',
  'KT10', 'KT11', 'KT13', 'KT15', 'KT16', 'KT17',
])

const CHART_THEME = {
  theoretical: '#3b82f6',
  theoreticalEnd: '#6366f1',
  stocktake: '#f97316',
  stocktakeEnd: '#fb923c',
  text: '#64748b',
  grid: 'rgba(148, 163, 184, 0.18)',
}

const defaultMonth = dayjs().subtract(1, 'month').format('YYYY-MM')

const loading = ref(false)
const detailLoading = ref(false)
const contentReady = ref(false)
const activeTab = ref<'summary' | 'detail'>('summary')
const processOptions = ref<OptionItem[]>([])
const productOptions = ref<Product[]>([])
const productOptionsLoading = ref(false)

const filters = ref({
  month: defaultMonth,
  processCd: '',
  productCd: '',
  onlyDiff: false,
})

const kpi = ref<ComparisonKpi | null>(null)
const summaryRows = ref<ComparisonSummaryRow[]>([])
/** 工程下拉用：常に全工程サマリ（製品・工程フィルター無し） */
const processSummaryRows = ref<ComparisonSummaryRow[]>([])
const detailRows = ref<ComparisonDetailRow[]>([])
const detailPage = ref(1)
const detailLimit = ref(50)
const detailTotal = ref(0)

const summaryChartRef = ref<HTMLElement | null>(null)
let summaryChart: echarts.ECharts | null = null

const asOfDate = computed(() => {
  if (!filters.value.month) return ''
  return dayjs(`${filters.value.month}-01`).endOf('month').format('YYYY-MM-DD')
})

const monthRangeLabel = computed(() => {
  if (!filters.value.month) return ''
  const start = dayjs(`${filters.value.month}-01`).format('MM/DD')
  const end = dayjs(`${filters.value.month}-01`).endOf('month').format('MM/DD')
  return `${start} ～ ${end}`
})

const hasData = computed(() => summaryRows.value.length > 0 || detailRows.value.length > 0)

/** 工程下拉：合并サマリ数量（全工程ベース） */
const processSelectOptions = computed(() => {
  const statsMap = new Map(processSummaryRows.value.map((r) => [r.process_cd, r]))
  return processOptions.value.map((p) => {
    const cd = String(p.cd || '').trim()
    const stats = statsMap.get(cd)
    const name = String(p.name || cd).trim()
    const theoretical_qty = stats?.theoretical_qty ?? 0
    const stocktake_qty = stats?.stocktake_qty ?? 0
    const diff_qty = stats?.diff_qty ?? 0
    const item_count = stats?.item_count ?? 0
    const hasStats = processSummaryRows.value.length > 0
    const displayLabel = hasStats
      ? `${name} (${cd}) — 理論${fmtNum(theoretical_qty)} / 棚卸${fmtNum(stocktake_qty)}`
      : `${name} (${cd})`
    return {
      cd,
      name,
      displayLabel,
      theoretical_qty,
      stocktake_qty,
      diff_qty,
      item_count,
      hasStats,
    }
  })
})

const selectedProductLabel = computed(() => {
  const cd = filters.value.productCd
  if (!cd) return '全製品'
  const p = productOptions.value.find((x) => x.product_cd === cd)
  return p ? `${p.product_name} (${cd})` : cd
})

/** 工程下拉「全工程」行：全工程サマリ合計 */
const allProcessStats = computed(() => {
  const rows = processSummaryRows.value
  if (!rows.length) return null
  return {
    theoretical_qty: rows.reduce((s, r) => s + (r.theoretical_qty || 0), 0),
    stocktake_qty: rows.reduce((s, r) => s + (r.stocktake_qty || 0), 0),
    diff_qty: rows.reduce((s, r) => s + (r.diff_qty || 0), 0),
  }
})

const diffBarWidth = computed(() => {
  const k = kpi.value
  if (!k) return 0
  const max = Math.max(
    Math.abs(k.theoretical_qty_total),
    Math.abs(k.stocktake_qty_total),
    Math.abs(k.diff_qty_total),
    1,
  )
  return Math.min(100, Math.round((Math.abs(k.diff_qty_total) / max) * 100))
})

const fmtNum = (v?: number | null) => (v == null ? '0' : Number(v).toLocaleString())
const fmtSigned = (v: number) => {
  const n = Number(v)
  if (n > 0) return `+${n.toLocaleString()}`
  return n.toLocaleString()
}

const diffClass = (v: number) => {
  if (v > 0) return 'num-pos'
  if (v < 0) return 'num-neg'
  return 'num-zero'
}

const STATUS_LABEL: Record<ComparisonStatus, string> = {
  match: '一致',
  only_theoretical: '理論のみ',
  only_stocktake: '棚卸のみ',
  mismatch: '不一致',
}

const statusLabel = (s: ComparisonStatus) => STATUS_LABEL[s] ?? s

const detailRowClass = ({ row }: { row: ComparisonDetailRow }) => {
  if (row.status === 'mismatch') return 'row-mismatch'
  if (row.status === 'only_theoretical' || row.status === 'only_stocktake') return 'row-partial'
  return ''
}

const kpiCards = computed(() => {
  const k = kpi.value
  return [
    {
      key: 'theoretical',
      tone: 'theoretical',
      icon: Box,
      label: '理論在庫合計',
      desc: '月末生産サマリ',
      value: fmtNum(k?.theoretical_qty_total),
      sub: `品目×工程 ${fmtNum(k?.item_count)} 件`,
    },
    {
      key: 'stocktake',
      tone: 'stocktake',
      icon: DocumentChecked,
      label: '棚卸在庫合計',
      desc: '対象月内集計',
      value: fmtNum(k?.stocktake_qty_total),
    },
    {
      key: 'diff',
      tone: 'diff',
      icon: Warning,
      label: '差異合計',
      desc: '棚卸 − 理論',
      value: fmtSigned(k?.diff_qty_total ?? 0),
      sub: `理論のみ ${fmtNum(k?.only_theoretical_count)} / 棚卸のみ ${fmtNum(k?.only_stocktake_count)}`,
    },
    {
      key: 'match',
      tone: 'match',
      icon: PieChart,
      label: '一致率',
      desc: '完全一致の割合',
      value: k ? `${k.match_rate.toFixed(1)}%` : '0%',
      sub: `不一致 ${fmtNum(k?.mismatch_count)} 件`,
    },
  ]
})

function buildParams(extra: { view: 'summary' | 'detail'; page?: number; limit?: number }) {
  return {
    as_of: asOfDate.value,
    process_cd: filters.value.processCd || undefined,
    product_cd: filters.value.productCd?.trim() || undefined,
    only_diff: filters.value.onlyDiff,
    view: extra.view,
    page: extra.page,
    limit: extra.limit,
    sort_by: 'diff_qty',
    sort_order: 'desc' as const,
  }
}

/** 工程下拉用：製品・工程フィルターなしのサマリのみ取得 */
async function fetchProcessSummaryPreview() {
  if (!asOfDate.value) return
  try {
    const data = await inventoryComparisonApi.getProductComparison({
      as_of: asOfDate.value,
      view: 'summary',
      only_diff: false,
    })
    processSummaryRows.value = (data.list as ComparisonSummaryRow[]) ?? []
  } catch {
    processSummaryRows.value = []
  }
}

async function fetchSummary() {
  const data = await inventoryComparisonApi.getProductComparison(buildParams({ view: 'summary' }))
  summaryRows.value = (data.list as ComparisonSummaryRow[]) ?? []
  kpi.value = data.kpi
  await nextTick()
  renderSummaryChart()
}

async function fetchDetail() {
  if (!asOfDate.value) return
  detailLoading.value = true
  try {
    const data = await inventoryComparisonApi.getProductComparison(
      buildParams({ view: 'detail', page: detailPage.value, limit: detailLimit.value }),
    )
    detailRows.value = (data.list as ComparisonDetailRow[]) ?? []
    detailTotal.value = data.total ?? 0
    if (data.kpi) kpi.value = data.kpi
  } finally {
    detailLoading.value = false
  }
}

async function fetchAllDetailForExport(): Promise<{ rows: ComparisonDetailRow[]; total: number }> {
  const limit = 500
  let page = 1
  const rows: ComparisonDetailRow[] = []
  let total = 0
  while (true) {
    const data = await inventoryComparisonApi.getProductComparison(
      buildParams({ view: 'detail', page, limit }),
    )
    const list = (data.list as ComparisonDetailRow[]) ?? []
    if (page === 1) total = data.total ?? 0
    rows.push(...list)
    if (list.length < limit || rows.length >= total) break
    page += 1
  }
  return { rows, total }
}

async function fetchAll() {
  if (!asOfDate.value) {
    ElMessage.warning('対象月を選択してください')
    return
  }
  loading.value = true
  contentReady.value = false
  try {
    detailPage.value = 1
    await Promise.all([fetchProcessSummaryPreview(), fetchSummary(), fetchDetail()])
    contentReady.value = true
  } catch {
    ElMessage.error('比較データの取得に失敗しました')
    summaryRows.value = []
    detailRows.value = []
    kpi.value = null
  } finally {
    loading.value = false
  }
}

function onMonthChange() {
  fetchProcessSummaryPreview()
}

function resetFilters() {
  filters.value = {
    month: defaultMonth,
    processCd: '',
    productCd: '',
    onlyDiff: false,
  }
  summaryRows.value = []
  processSummaryRows.value = []
  detailRows.value = []
  kpi.value = null
  detailTotal.value = 0
  contentReady.value = false
  disposeChart()
}

function switchTab(name: 'summary' | 'detail') {
  activeTab.value = name
  if (name === 'summary') nextTick(() => renderSummaryChart())
}

function onDetailSizeChange() {
  detailPage.value = 1
  fetchDetail()
}

function renderSummaryChart() {
  if (!summaryChartRef.value || summaryRows.value.length === 0) {
    disposeChart()
    return
  }
  if (!summaryChart) {
    summaryChart = echarts.init(summaryChartRef.value)
  }
  const names = summaryRows.value.map((r) => r.process_name)
  summaryChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      borderColor: 'transparent',
      textStyle: { color: '#f1f5f9', fontSize: 12 },
    },
    grid: { left: 52, right: 20, top: 20, bottom: 56 },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: { rotate: 28, fontSize: 10, color: CHART_THEME.text, interval: 0 },
      axisLine: { lineStyle: { color: CHART_THEME.grid } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: CHART_THEME.grid, type: 'dashed' } },
      axisLabel: { color: CHART_THEME.text, fontSize: 10 },
    },
    series: [
      {
        name: '理論在庫',
        type: 'bar',
        barMaxWidth: 22,
        data: summaryRows.value.map((r) => r.theoretical_qty),
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: CHART_THEME.theoretical },
            { offset: 1, color: CHART_THEME.theoreticalEnd },
          ]),
        },
      },
      {
        name: '棚卸在庫',
        type: 'bar',
        barMaxWidth: 22,
        data: summaryRows.value.map((r) => r.stocktake_qty),
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: CHART_THEME.stocktake },
            { offset: 1, color: CHART_THEME.stocktakeEnd },
          ]),
        },
      },
    ],
  })
  summaryChart.resize()
}

function disposeChart() {
  summaryChart?.dispose()
  summaryChart = null
}

async function handleExport() {
  if (!hasData.value) return
  try {
    const { rows: allDetail } = await fetchAllDetailForExport()
    const workbook = new ExcelJS.Workbook()
    const ws1 = workbook.addWorksheet('工程別サマリ')
    ws1.addRow(['工程CD', '工程名', '理論在庫', '棚卸在庫', '差異', '差異率', '品目数', '一致', '不一致', '一致率'])
    for (const r of summaryRows.value) {
      ws1.addRow([
        r.process_cd,
        r.process_name,
        r.theoretical_qty,
        r.stocktake_qty,
        r.diff_qty,
        r.diff_rate != null ? `${r.diff_rate}%` : '',
        r.item_count,
        r.matched_count,
        r.mismatch_count,
        `${r.match_rate}%`,
      ])
    }
    const ws2 = workbook.addWorksheet('品目明細')
    ws2.addRow(['製品CD', '製品名', '工程CD', '工程名', '理論', '棚卸', '差異', '状態'])
    for (const r of allDetail) {
      ws2.addRow([
        r.product_cd,
        r.product_name,
        r.process_cd,
        r.process_name,
        r.theoretical_qty,
        r.stocktake_qty,
        r.diff_qty,
        statusLabel(r.status),
      ])
    }
    const buffer = await workbook.xlsx.writeBuffer()
    const blob = new Blob([buffer], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    saveAs(blob, `理論棚卸比較_${asOfDate.value}.xlsx`)
  } catch {
    ElMessage.error('Excel 出力に失敗しました')
  }
}

function buildPrintMeta() {
  const processLabel =
    filters.value.processCd
      ? processOptions.value.find((p) => p.cd === filters.value.processCd)?.name ||
        filters.value.processCd
      : '全工程'
  return {
    printedAt: dayjs().format('YYYY-MM-DD HH:mm'),
    asOf: asOfDate.value,
    processLabel,
    productLabel: selectedProductLabel.value === '全製品' ? '' : selectedProductLabel.value,
    onlyDiff: filters.value.onlyDiff,
  }
}

async function handlePrint() {
  if (!hasData.value || !kpi.value) return
  try {
    const html = buildTheoreticalStocktakeComparisonPrintHtml({
      ...buildPrintMeta(),
      kpi: kpi.value,
      summaryRows: summaryRows.value,
    })
    const ok = openPrintWindow(html)
    if (!ok) ElMessage.warning(PRINT_POPUP_BLOCKED_MSG)
  } catch {
    ElMessage.error('印刷の準備に失敗しました')
  }
}

async function handlePrintDetail() {
  if (!hasData.value) return
  try {
    const { rows, total } = await fetchAllDetailForExport()
    const html = buildTheoreticalStocktakeComparisonDetailPrintHtml({
      ...buildPrintMeta(),
      detailRows: rows,
      totalCount: total,
    })
    const ok = openPrintWindow(html)
    if (!ok) ElMessage.warning(PRINT_POPUP_BLOCKED_MSG)
  } catch {
    ElMessage.error('明細印刷の準備に失敗しました')
  }
}

async function loadProductOptions() {
  productOptionsLoading.value = true
  try {
    const rows = await getProducts()
    productOptions.value = rows
      .filter((p) => String(p.product_cd || '').trim().endsWith('1'))
      .sort((a, b) => (a.product_name || a.product_cd).localeCompare(b.product_name || b.product_cd))
  } catch {
    productOptions.value = []
  } finally {
    productOptionsLoading.value = false
  }
}

async function loadProcessOptions() {
  try {
    const res = await fetchProcesses({ page: 1, pageSize: 5000 })
    const r = res as { data?: { list?: OptionItem[] }; list?: OptionItem[] }
    const list = r?.data?.list ?? r?.list ?? []
    processOptions.value = list.filter((p) => STOCKTAKE_PROCESS_CDS.has(String(p.cd || '').trim()))
  } catch {
    processOptions.value = []
  }
}

function onResize() {
  summaryChart?.resize()
}

onMounted(async () => {
  await Promise.all([loadProcessOptions(), loadProductOptions()])
  window.addEventListener('resize', onResize)
  await fetchAll()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  disposeChart()
})

watch(
  () => filters.value.onlyDiff,
  () => {
    if (asOfDate.value) fetchAll()
  },
)
</script>

<style scoped>
/* ── Page shell ── */
.cmp-page {
  --cmp-accent: #3b82f6;
  --cmp-accent-2: #6366f1;
  --cmp-theoretical: #2563eb;
  --cmp-stocktake: #ea580c;
  --cmp-success: #059669;
  --cmp-danger: #dc2626;
  position: relative;
  min-height: 100%;
  padding: 14px 18px 28px;
  box-sizing: border-box;
}

.page-ambient {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
  background: linear-gradient(165deg, #f0f4ff 0%, #f8fafc 40%, #fff7ed 100%);
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.45;
  animation: orb-float 18s ease-in-out infinite;
}

.orb-a {
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, #93c5fd 0%, transparent 70%);
  top: -120px;
  right: 5%;
}

.orb-b {
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, #fdba74 0%, transparent 70%);
  bottom: 5%;
  left: -80px;
  animation-delay: -6s;
}

.orb-c {
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, #c4b5fd 0%, transparent 70%);
  top: 45%;
  right: 25%;
  animation-delay: -12s;
}

@keyframes orb-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(12px, -16px) scale(1.05); }
}

.cmp-inner {
  position: relative;
  z-index: 1;
  max-width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.animate-in {
  animation: fade-up 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--delay, 0ms);
}

@keyframes fade-up {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Toolbar ── */
.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 0;
  border-radius: 14px;
  overflow: hidden;
  min-height: 56px;
}

.toolbar-elevated {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97) 0%, rgba(248, 250, 252, 0.94) 100%);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.98) inset,
    0 8px 32px rgba(15, 23, 42, 0.08),
    0 2px 8px rgba(15, 23, 42, 0.04);
}

.toolbar-brand-zone {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  flex-shrink: 0;
  max-width: 280px;
}

.brand-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: linear-gradient(145deg, #3b82f6 0%, #6366f1 100%);
  color: #fff;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 4px 14px rgba(59, 130, 246, 0.4);
}

.toolbar-title {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.01em;
  line-height: 1.25;
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

.toolbar-filters-zone::-webkit-scrollbar {
  height: 4px;
}

.filter-inline {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.filter-inline__label {
  font-size: 0.62rem;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
  letter-spacing: 0.02em;
}

.filter-inline--period .filter-inline__label { color: #2563eb; }
.filter-inline--process .filter-inline__label { color: #7c3aed; }
.filter-inline--product .filter-inline__label { color: #d97706; }

.filter-sep {
  width: 1px;
  height: 22px;
  background: rgba(148, 163, 184, 0.35);
  flex-shrink: 0;
}

.filter-inline--switch {
  padding-left: 2px;
}

.filter-inline--switch :deep(.el-switch__label) {
  font-size: 0.65rem;
  font-weight: 600;
}

.tf-control--month { width: 108px !important; }
.tf-control--process { width: 168px !important; min-width: 168px !important; }
.tf-control--product { width: 156px !important; min-width: 156px !important; }

.tf-control :deep(.el-input__wrapper),
.tf-control :deep(.el-select__wrapper) {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 7px;
  min-height: 28px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 0 0 1px rgba(15, 23, 42, 0.07);
  transition: box-shadow 0.15s ease;
}

.tf-control :deep(.el-input__inner),
.tf-control :deep(.el-select__selected-item),
.tf-control :deep(.el-select__placeholder) {
  font-size: 0.72rem !important;
  font-weight: 600;
}

.tf-control :deep(.el-input__wrapper.is-focus),
.tf-control :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}

.toolbar-actions-zone {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0 10px;
  flex-shrink: 0;
  background: linear-gradient(180deg, rgba(241, 245, 249, 0.65) 0%, rgba(226, 232, 240, 0.35) 100%);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 28px;
  padding: 0 10px;
  border: none;
  border-radius: 7px;
  font-size: 0.68rem;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.action-btn--primary {
  color: #fff;
  background: linear-gradient(180deg, #4f8ef7 0%, #2563eb 100%);
  box-shadow: 0 2px 0 #1d4ed8, 0 4px 12px rgba(37, 99, 235, 0.35);
}

.action-btn--primary:hover:not(:disabled) { filter: brightness(1.06); }
.action-btn--primary:disabled { opacity: 0.6; cursor: not-allowed; }

.action-btn--ghost {
  color: #475569;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%);
  box-shadow: 0 1px 0 #cbd5e1, 0 2px 6px rgba(15, 23, 42, 0.07);
}

.action-btn--ghost:hover:not(:disabled) { color: #1e293b; }

.action-btn .is-loading { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Period ribbon ── */
.period-ribbon {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 8px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

.period-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.72rem;
  font-weight: 800;
  color: #1d4ed8;
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.9), rgba(191, 219, 254, 0.5));
}

.period-divider {
  width: 1px;
  height: 16px;
  background: rgba(148, 163, 184, 0.4);
}

.period-meta {
  font-size: 0.68rem;
  font-weight: 600;
  color: #64748b;
}

.period-meta strong {
  color: #334155;
  font-weight: 800;
}

/* ── KPI cards ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

@media (max-width: 1200px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}

.kpi-card {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  min-height: 120px;
}

.kpi-card--elevated {
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.92) 100%);
  border: 1px solid rgba(255, 255, 255, 0.95);
  border-radius: 14px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 8px 24px rgba(15, 23, 42, 0.07);
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.3s ease;
}

.kpi-card--elevated:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.1);
}

.kpi-card__glow {
  position: absolute;
  top: -40%;
  right: -15%;
  width: 110px;
  height: 110px;
  border-radius: 50%;
  opacity: 0.35;
  filter: blur(28px);
  pointer-events: none;
}

.kpi-card--theoretical .kpi-card__glow { background: #60a5fa; }
.kpi-card--stocktake .kpi-card__glow { background: #fb923c; }
.kpi-card--diff .kpi-card__glow { background: #f87171; }
.kpi-card--match .kpi-card__glow { background: #34d399; }

.kpi-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 12px;
  bottom: 12px;
  width: 4px;
  border-radius: 0 4px 4px 0;
}

.kpi-card--theoretical::before { background: linear-gradient(180deg, #93c5fd, #2563eb); }
.kpi-card--stocktake::before { background: linear-gradient(180deg, #fdba74, #ea580c); }
.kpi-card--diff::before { background: linear-gradient(180deg, #fca5a5, #dc2626); }
.kpi-card--match::before { background: linear-gradient(180deg, #6ee7b7, #059669); }

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
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
}

.kpi-card--theoretical .kpi-icon {
  background: linear-gradient(145deg, rgba(191, 219, 254, 0.95), rgba(59, 130, 246, 0.15));
  color: #2563eb;
}
.kpi-card--stocktake .kpi-icon {
  background: linear-gradient(145deg, rgba(254, 215, 170, 0.95), rgba(249, 115, 22, 0.15));
  color: #ea580c;
}
.kpi-card--diff .kpi-icon {
  background: linear-gradient(145deg, rgba(254, 202, 202, 0.95), rgba(239, 68, 68, 0.12));
  color: #dc2626;
}
.kpi-card--match .kpi-icon {
  background: linear-gradient(145deg, rgba(167, 243, 208, 0.95), rgba(16, 185, 129, 0.15));
  color: #059669;
}

.kpi-card__name {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 800;
  color: #0f172a;
}

.kpi-card__desc {
  margin: 2px 0 0;
  font-size: 0.6rem;
  font-weight: 600;
  color: #94a3b8;
}

.kpi-metric {
  position: relative;
  z-index: 1;
  padding: 8px 10px;
  border-radius: 9px;
  background: rgba(248, 250, 252, 0.75);
  border: 1px solid rgba(226, 232, 240, 0.85);
}

.kpi-metric__main {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.kpi-metric__label {
  font-size: 0.65rem;
  font-weight: 700;
  color: #64748b;
}

.kpi-metric__value {
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

.kpi-card--diff .kpi-metric__value { color: #b91c1c; }

.kpi-metric__foot { margin-top: 4px; }
.kpi-sub { font-size: 0.62rem; font-weight: 600; color: #94a3b8; }

.kpi-grid:not(.is-ready) .kpi-card--elevated { opacity: 0; }
.kpi-grid.is-ready .kpi-card--elevated {
  animation: kpi-pop 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--delay, 0ms);
}

@keyframes kpi-pop {
  from { opacity: 0; transform: translateY(12px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── VS panel ── */
.vs-panel {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  grid-template-rows: auto auto;
  gap: 0;
  overflow: hidden;
  border-radius: 14px;
}

.vs-panel--elevated {
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.95) 0%, rgba(255, 255, 255, 0.92) 100%);
  border: 1px solid rgba(147, 197, 253, 0.35);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 8px 28px rgba(37, 99, 235, 0.1);
}

.vs-side {
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.vs-side--theoretical {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, transparent 100%);
}

.vs-side--stocktake {
  background: linear-gradient(225deg, rgba(249, 115, 22, 0.08) 0%, transparent 100%);
}

.vs-side-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.vs-badge {
  font-size: 0.58rem;
  font-weight: 800;
  padding: 3px 9px;
  border-radius: 6px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.vs-badge--theoretical {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
}

.vs-badge--stocktake {
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: #fff;
  box-shadow: 0 2px 8px rgba(234, 88, 12, 0.35);
}

.vs-month {
  font-size: 0.88rem;
  font-weight: 800;
  color: #0f172a;
}

.vs-metric-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.vs-metric {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 8px 10px;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05);
  transition: transform 0.2s ease;
}

.vs-metric:hover { transform: translateY(-2px); }

.vs-metric-label {
  font-size: 0.6rem;
  font-weight: 700;
  color: #64748b;
}

.vs-metric-value {
  font-size: 1.05rem;
  font-weight: 800;
  color: #1e293b;
  font-variant-numeric: tabular-nums;
}

.vs-metric-value small {
  font-size: 0.6rem;
  font-weight: 600;
  color: #94a3b8;
  margin-left: 1px;
}

.vs-metric--theoretical .vs-metric-value { color: #2563eb; }
.vs-metric--stocktake .vs-metric-value { color: #ea580c; }
.vs-metric--match .vs-metric-value { color: #059669; }

.vs-center {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 56px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.6), rgba(241, 245, 249, 0.8));
  border-left: 1px solid rgba(148, 163, 184, 0.2);
  border-right: 1px solid rgba(148, 163, 184, 0.2);
}

.vs-pulse {
  position: absolute;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(99, 102, 241, 0.15);
  animation: vs-pulse 2s ease-in-out infinite;
}

@keyframes vs-pulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.3); opacity: 0.2; }
}

.vs-center-text {
  position: relative;
  z-index: 1;
  font-size: 0.75rem;
  font-weight: 900;
  color: #6366f1;
  letter-spacing: 0.05em;
}

.vs-diff-bar {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 18px;
  background: rgba(248, 250, 252, 0.85);
  border-top: 1px solid rgba(148, 163, 184, 0.2);
}

.vs-diff-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 0.62rem;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
}

.vs-diff-label strong {
  font-size: 1rem;
  font-weight: 800;
}

.vs-diff-track {
  flex: 1;
  height: 8px;
  border-radius: 99px;
  background: rgba(226, 232, 240, 0.9);
  overflow: hidden;
}

.vs-diff-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}

.vs-diff-fill--pos {
  background: linear-gradient(90deg, #34d399, #059669);
}

.vs-diff-fill--neg {
  background: linear-gradient(90deg, #f87171, #dc2626);
}

.vs-diff-hint {
  font-size: 0.62rem;
  font-weight: 700;
  color: #94a3b8;
  white-space: nowrap;
}

/* ── Main panel ── */
.panel--main {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97) 0%, rgba(248, 250, 252, 0.95) 100%);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 14px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.98) inset,
    0 8px 28px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  background: rgba(248, 250, 252, 0.6);
}

.panel-hint {
  font-size: 0.65rem;
  font-weight: 700;
  color: #94a3b8;
}

.tab-switcher {
  display: flex;
  gap: 6px;
  padding: 3px;
  background: rgba(226, 232, 240, 0.5);
  border-radius: 10px;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border: none;
  border-radius: 8px;
  font-size: 0.72rem;
  font-weight: 700;
  color: #64748b;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover { color: #334155; }

.tab-btn--active {
  color: #1e293b;
  background: #fff;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.1);
}

.tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 99px;
  font-size: 0.58rem;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
}

.tab-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Chart ── */
.chart-panel {
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.85);
  background: rgba(255, 255, 255, 0.7);
  overflow: hidden;
}

.chart-panel-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
}

.panel-accent {
  width: 4px;
  height: 18px;
  border-radius: 2px;
  flex-shrink: 0;
}

.panel-accent--blue {
  background: linear-gradient(180deg, #60a5fa, #2563eb);
}

.chart-panel-title {
  font-size: 0.78rem;
  font-weight: 800;
  color: #1e293b;
  flex: 1;
}

.chart-legend {
  display: flex;
  gap: 14px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.65rem;
  font-weight: 700;
  color: #64748b;
}

.legend-item i {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

.legend-item--theoretical i {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
}

.legend-item--stocktake i {
  background: linear-gradient(135deg, #f97316, #fb923c);
}

.chart-canvas-wrap {
  position: relative;
  min-height: 300px;
}

.chart-canvas {
  width: 100%;
  height: 300px;
}

.chart-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 600;
}

/* ── Tables ── */
.table-wrap {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.85);
}

.data-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
  font-size: 0.68rem;
  font-weight: 800;
  color: #475569;
}

.data-table :deep(.th-theoretical) {
  background: linear-gradient(180deg, #eff6ff, #dbeafe) !important;
  color: #1d4ed8 !important;
}

.data-table :deep(.th-stocktake) {
  background: linear-gradient(180deg, #fff7ed, #ffedd5) !important;
  color: #c2410c !important;
}

.data-table :deep(.td-theoretical) {
  background: rgba(239, 246, 255, 0.35) !important;
}

.data-table :deep(.td-stocktake) {
  background: rgba(255, 247, 237, 0.35) !important;
}

.process-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #334155;
}

.process-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #3b82f6);
  flex-shrink: 0;
}

.qty-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.qty-pill--theoretical {
  background: rgba(219, 234, 254, 0.7);
  color: #1d4ed8;
}

.qty-pill--stocktake {
  background: rgba(254, 215, 170, 0.55);
  color: #c2410c;
}

.diff-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  font-size: 0.72rem;
}

.num-pos {
  color: #15803d;
  background: rgba(22, 163, 74, 0.12);
}

.num-neg {
  color: #b91c1c;
  background: rgba(220, 38, 38, 0.1);
}

.num-zero { color: #64748b; }

.count-good { color: #059669; font-weight: 700; }
.count-bad { color: #dc2626; font-weight: 700; }
.rate-text { font-weight: 600; color: #475569; }
.rate-text--muted { color: #cbd5e1; }

.product-code {
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 0.68rem;
  font-weight: 700;
  color: #4338ca;
  background: rgba(238, 242, 255, 0.8);
  padding: 2px 6px;
  border-radius: 4px;
}

.process-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 5px;
  font-size: 0.65rem;
  font-weight: 700;
  color: #5b21b6;
  background: rgba(237, 233, 254, 0.8);
}

.status-pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.status-pill--match {
  color: #047857;
  background: rgba(209, 250, 229, 0.9);
  border: 1px solid rgba(52, 211, 153, 0.35);
}

.status-pill--mismatch {
  color: #b91c1c;
  background: rgba(254, 226, 226, 0.9);
  border: 1px solid rgba(248, 113, 113, 0.35);
}

.status-pill--only_theoretical {
  color: #1d4ed8;
  background: rgba(219, 234, 254, 0.9);
  border: 1px solid rgba(96, 165, 250, 0.35);
}

.status-pill--only_stocktake {
  color: #c2410c;
  background: rgba(254, 215, 170, 0.55);
  border: 1px solid rgba(251, 146, 60, 0.35);
}

:deep(.row-mismatch) {
  background: rgba(254, 226, 226, 0.25) !important;
}

:deep(.row-partial) {
  background: rgba(254, 243, 199, 0.25) !important;
}

.pager-wrap {
  display: flex;
  justify-content: flex-end;
  padding-top: 4px;
}

@media (max-width: 900px) {
  .vs-panel { grid-template-columns: 1fr; }
  .vs-center { display: none; }
  .vs-metric-grid { grid-template-columns: 1fr 1fr; }
  .toolbar {
    flex-wrap: wrap;
    min-height: auto;
  }
  .toolbar-brand-zone {
    width: 100%;
    max-width: none;
    padding: 10px 12px;
    border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  }
  .toolbar-filters-zone {
    width: 100%;
    border-left: none;
    border-right: none;
    padding: 8px 12px;
  }
  .toolbar-actions-zone {
    width: 100%;
    justify-content: flex-end;
    padding: 8px 12px;
    border-top: 1px solid rgba(15, 23, 42, 0.06);
  }
}

/* ── Select option rows ── */
.process-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 2px 0;
  line-height: 1.3;
}

.process-option--all .process-option__name {
  font-weight: 800;
  color: #1e293b;
}

.process-option__name {
  font-size: 0.72rem;
  font-weight: 700;
  color: #334155;
}

.process-option__stats {
  font-size: 0.62rem;
  font-weight: 600;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}

.process-option__stats--muted {
  color: #cbd5e1;
  font-style: italic;
}

.product-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
}

.product-option__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.72rem;
  font-weight: 600;
  color: #334155;
}

.product-option__cd {
  flex-shrink: 0;
  font-size: 0.65rem;
  font-weight: 700;
  font-family: ui-monospace, monospace;
  color: #6366f1;
  background: rgba(238, 242, 255, 0.9);
  padding: 1px 6px;
  border-radius: 4px;
}
</style>

<style>
.cmp-select-popper.el-popper {
  border-radius: 10px !important;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12) !important;
}

.cmp-process-popper.el-select-dropdown__item {
  height: auto !important;
  min-height: 34px;
  padding-top: 6px !important;
  padding-bottom: 6px !important;
  line-height: 1.35 !important;
}
</style>
