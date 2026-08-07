<template>
  <div class="mes-page">
    <div class="page-ambient" aria-hidden="true">
      <div class="orb orb-a" />
      <div class="orb orb-b" />
      <div class="orb orb-c" />
    </div>

    <div class="mes-inner">
      <!-- ツールバー：タイトル + フィルタ一体 -->
      <header class="toolbar toolbar-elevated animate-in" style="--delay: 0ms">
        <div class="toolbar-brand-zone">
          <div class="brand-icon">
            <el-icon :size="18"><DataAnalysis /></el-icon>
          </div>
          <div class="brand-text">
            <h1 class="toolbar-title">実績修正統計</h1>
            <p class="toolbar-sub">実績修正 vs 実績集計の月次比較（手入力除外）</p>
          </div>
        </div>

        <div class="toolbar-filters-zone">
          <div class="filter-group filter-group--period">
            <span class="filter-group-tag">期間</span>
            <div class="filter-group-fields">
              <div class="filter-field">
                <label class="filter-label">対象月</label>
                <el-date-picker
                  v-model="filters.month"
                  type="month"
                  placeholder="YYYY-MM"
                  value-format="YYYY-MM"
                  size="small"
                  class="tf-control tf-control--month"
                />
              </div>
              <div class="filter-field">
                <label class="filter-label">比較月</label>
                <el-date-picker
                  v-model="filters.compareMonth"
                  type="month"
                  placeholder="YYYY-MM"
                  value-format="YYYY-MM"
                  size="small"
                  class="tf-control tf-control--month"
                />
              </div>
            </div>
          </div>

          <div class="filter-group filter-group--trend">
            <span class="filter-group-tag">推移</span>
            <div class="filter-group-fields">
              <div class="filter-field filter-field--trend">
                <el-select
                  v-model="filters.trendMonths"
                  size="small"
                  teleported
                  popper-class="mes-select-popper"
                  class="tf-control tf-control--trend"
                >
                  <el-option :value="3" label="3ヶ月" />
                  <el-option :value="6" label="6ヶ月" />
                  <el-option :value="12" label="12ヶ月" />
                </el-select>
              </div>
            </div>
          </div>

          <div class="filter-group filter-group--process">
            <span class="filter-group-tag">工程</span>
            <div class="filter-group-fields">
              <div class="filter-field filter-field--process">
                <el-select
                  v-model="filters.processCd"
                  placeholder="全工程"
                  clearable
                  filterable
                  size="small"
                  teleported
                  popper-class="mes-select-popper"
                  class="tf-control tf-control--process"
                >
                  <el-option
                    v-for="item in processOptions"
                    :key="item.cd"
                    :label="item.name || item.cd"
                    :value="item.cd"
                  />
                </el-select>
              </div>
            </div>
          </div>
        </div>

        <div class="toolbar-actions-zone">
          <button
            type="button"
            class="action-btn action-btn--primary"
            :disabled="loading"
            @click="fetchStats"
          >
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
            :disabled="loading || !stats"
            @click="handlePrintReport"
          >
            <el-icon><Printer /></el-icon>
            <span>印刷</span>
          </button>
        </div>
      </header>

      <!-- KPI -->
      <div class="dash-section kpi-grid" :class="{ 'is-ready': contentReady }" v-loading="loading">
        <article
          v-for="(kpi, i) in kpiCards"
          :key="kpi.key"
          class="kpi-card kpi-card--elevated"
          :class="`kpi-card--${kpi.tone}`"
          :style="{ '--delay': `${80 + i * 70}ms`, '--i': i }"
        >
          <div class="kpi-card__glow" aria-hidden="true" />
          <header class="kpi-card__head">
            <div class="kpi-icon">
              <el-icon :size="18"><component :is="kpi.icon" /></el-icon>
            </div>
            <div class="kpi-card__titles">
              <h3 class="kpi-card__name">{{ kpi.label }}</h3>
              <p v-if="kpi.desc" class="kpi-card__desc">{{ kpi.desc }}</p>
            </div>
          </header>

          <div class="kpi-metrics">
            <div class="kpi-metric">
              <div class="kpi-metric__main">
                <span class="kpi-metric__label">{{ kpi.countLabel }}</span>
                <span class="kpi-metric__value">
                  {{ kpi.value }}<small v-if="kpi.unit" class="kpi-metric__unit">{{ kpi.unit }}</small>
                </span>
              </div>
              <div class="kpi-metric__foot">
                <span
                  v-if="kpi.delta"
                  class="kpi-delta kpi-badge"
                  :class="deltaClass(kpi.deltaRaw)"
                >
                  {{ kpi.delta }}
                </span>
                <span v-if="kpi.sub" class="kpi-sub">{{ kpi.sub }}</span>
              </div>
            </div>

            <div v-if="kpi.qtyValue" class="kpi-metric kpi-metric--qty">
              <div class="kpi-metric__main">
                <span class="kpi-metric__label">{{ kpi.qtyLabel }}</span>
                <span class="kpi-metric__value kpi-metric__value--qty">
                  {{ kpi.qtyValue }}
                </span>
              </div>
              <div class="kpi-metric__foot">
                <span
                  v-if="kpi.qtyDelta"
                  class="kpi-delta kpi-badge"
                  :class="deltaClass(kpi.qtyDeltaRaw)"
                >
                  {{ kpi.qtyDelta }}
                </span>
                <span v-if="kpi.qtySub" class="kpi-sub">{{ kpi.qtySub }}</span>
              </div>
            </div>
          </div>
        </article>
      </div>

      <!-- 月次比較サマリ -->
      <section
        v-if="stats && contentReady"
        class="vs-panel vs-panel--elevated animate-in"
        style="--delay: 300ms"
      >
        <div class="vs-side vs-side--current">
          <div class="vs-side-head">
            <span class="vs-badge vs-badge--current">対象月</span>
            <strong class="vs-month">{{ stats.month }}</strong>
          </div>
          <div class="vs-metric-grid">
            <div class="vs-metric vs-metric--prod">
              <span class="vs-metric-label">実績修正</span>
              <span class="vs-metric-value">{{ fmtNum(current?.prodDataMgmt?.count) }}<small>件</small></span>
            </div>
            <div class="vs-metric vs-metric--auto">
              <span class="vs-metric-label">実績集計</span>
              <span class="vs-metric-value">{{ fmtNum(current?.auto?.count) }}<small>件</small></span>
            </div>
            <div class="vs-metric vs-metric--ratio">
              <span class="vs-metric-label">修正比率</span>
              <span class="vs-metric-value">{{ fmtPct(current?.prodDataMgmtCountRatio) }}</span>
            </div>
          </div>
          <div class="vs-section-divider">
            <span>数量比較</span>
            <small>絶対値合計</small>
          </div>
          <div class="vs-metric-grid">
            <div class="vs-metric vs-metric--prod">
              <span class="vs-metric-label">実績修正</span>
              <span class="vs-metric-value">{{ fmtQty(current?.prodDataMgmt?.quantity) }}</span>
            </div>
            <div class="vs-metric vs-metric--auto">
              <span class="vs-metric-label">実績集計</span>
              <span class="vs-metric-value">{{ fmtQty(current?.auto?.quantity) }}</span>
            </div>
            <div class="vs-metric vs-metric--ratio">
              <span class="vs-metric-label">修正数量比率</span>
              <span class="vs-metric-value">{{ fmtPct(current?.prodDataMgmtQuantityRatio) }}</span>
            </div>
          </div>
        </div>
        <div class="vs-center" aria-hidden="true">
          <span class="vs-pulse" />
          <span class="vs-center-text">VS</span>
        </div>
        <div class="vs-side vs-side--compare">
          <div class="vs-side-head">
            <span class="vs-badge vs-badge--compare">比較月</span>
            <strong class="vs-month">{{ stats.compareMonth }}</strong>
          </div>
          <div class="vs-metric-grid">
            <div class="vs-metric">
              <span class="vs-metric-label">実績修正</span>
              <span class="vs-metric-value">{{ fmtNum(compare?.prodDataMgmt?.count) }}<small>件</small></span>
            </div>
            <div class="vs-metric">
              <span class="vs-metric-label">実績集計</span>
              <span class="vs-metric-value">{{ fmtNum(compare?.auto?.count) }}<small>件</small></span>
            </div>
            <div class="vs-metric">
              <span class="vs-metric-label">修正比率</span>
              <span class="vs-metric-value">{{ fmtPct(compare?.prodDataMgmtCountRatio) }}</span>
            </div>
          </div>
          <div class="vs-section-divider vs-section-divider--ghost" aria-hidden="true">
            <span>数量比較</span>
            <small>絶対値合計</small>
          </div>
          <div class="vs-metric-grid">
            <div class="vs-metric">
              <span class="vs-metric-label">実績修正</span>
              <span class="vs-metric-value">{{ fmtQty(compare?.prodDataMgmt?.quantity) }}</span>
            </div>
            <div class="vs-metric">
              <span class="vs-metric-label">実績集計</span>
              <span class="vs-metric-value">{{ fmtQty(compare?.auto?.quantity) }}</span>
            </div>
            <div class="vs-metric">
              <span class="vs-metric-label">修正数量比率</span>
              <span class="vs-metric-value">{{ fmtPct(compare?.prodDataMgmtQuantityRatio) }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- チャート -->
      <div class="dash-section chart-grid">
        <section class="panel panel--chart animate-in" style="--delay: 380ms">
          <div class="panel-head">
            <span class="panel-accent panel-accent--blue" />
            <span class="panel-title">月次比較</span>
            <span class="panel-meta">件数</span>
          </div>
          <div class="chart-canvas-wrap">
            <div ref="monthCompareChartRef" class="chart-canvas" />
          </div>
        </section>
        <section class="panel panel--chart animate-in" style="--delay: 400ms">
          <div class="panel-head">
            <span class="panel-accent panel-accent--purple" />
            <span class="panel-title">月次数量比較</span>
            <span class="panel-meta">単位：千</span>
          </div>
          <div class="chart-canvas-wrap">
            <div ref="qtyCompareChartRef" class="chart-canvas" />
          </div>
        </section>
        <section class="panel panel--chart animate-in" style="--delay: 520ms">
          <div class="panel-head panel-head--chart-export">
            <span class="panel-accent panel-accent--orange" />
            <span class="panel-title">修正比率推移</span>
            <span class="panel-meta">件数</span>
            <el-button
              size="small"
              type="success"
              plain
              class="panel-export-btn"
              :icon="Download"
              :loading="exportingRatioTrend"
              :disabled="!(stats?.byMonthTrend?.length)"
              @click="exportRatioTrendExcel"
            >
              Excel出力
            </el-button>
          </div>
          <div class="chart-canvas-wrap">
            <div ref="trendChartRef" class="chart-canvas" />
          </div>
        </section>
        <section class="panel panel--chart animate-in" style="--delay: 540ms">
          <div class="panel-head">
            <span class="panel-accent panel-accent--purple" />
            <span class="panel-title">修正数量比率推移</span>
            <span class="panel-meta">{{ filters.trendMonths }}ヶ月</span>
          </div>
          <div class="chart-canvas-wrap">
            <div ref="qtyTrendChartRef" class="chart-canvas" />
          </div>
        </section>
        <section class="panel panel--chart panel--wide animate-in" style="--delay: 560ms">
          <div class="panel-head">
            <span class="panel-accent panel-accent--teal" />
            <span class="panel-title">工程別比較</span>
            <span class="panel-meta">{{ stats?.compareMonth }} vs {{ stats?.month }}</span>
          </div>
          <div class="chart-canvas-wrap chart-canvas-wrap--tall">
            <div ref="processCompareChartRef" class="chart-canvas chart-canvas--tall" />
          </div>
        </section>
        <section class="panel panel--chart panel--wide animate-in" style="--delay: 580ms">
          <div class="panel-head">
            <span class="panel-accent panel-accent--green" />
            <span class="panel-title">工程別内訳</span>
            <span class="panel-meta">{{ stats?.month }}</span>
          </div>
          <div class="chart-canvas-wrap chart-canvas-wrap--tall">
            <div ref="processChartRef" class="chart-canvas chart-canvas--tall" />
          </div>
        </section>
      </div>

      <!-- 工程別比較テーブル -->
      <section class="panel glass animate-in" style="--delay: 600ms">
        <div class="panel-head panel-head--table">
          <div class="panel-head-left">
            <span class="panel-title">工程別比較一覧</span>
            <span class="panel-hint">{{ stats?.compareMonth }} → {{ stats?.month }}</span>
          </div>
          <el-button
            size="small"
            type="success"
            plain
            :icon="Download"
            :loading="exportingProcessCompare"
            :disabled="!byProcessComparison.length"
            @click="exportProcessCompareExcel"
          >
            Excel出力
          </el-button>
        </div>
        <div class="table-wrap table-wrap--fluid">
          <el-table
            :data="byProcessComparison"
            border
            stripe
            fit
            size="small"
            class="data-table data-table--fluid data-table--process-compare"
            :max-height="tableMaxHeight"
          >
            <el-table-column
              prop="processName"
              label="工程"
              min-width="96"
              fixed="left"
              show-overflow-tooltip
              label-class-name="cmp-th cmp-th--process"
              class-name="cmp-td cmp-td--process"
            />
            <el-table-column align="center" min-width="188" label-class-name="cmp-th cmp-th--current cmp-th--prod">
              <template #header>
                <div class="cmp-col-head">
                  <span class="cmp-col-type cmp-col-type--prod">実績修正</span>
                  <span class="cmp-month-tag cmp-month-tag--current">{{ stats?.month }}</span>
                </div>
              </template>
              <el-table-column
                label="件数"
                min-width="52"
                align="center"
                label-class-name="cmp-th-sub cmp-th-sub--current cmp-th-sub--prod"
                class-name="cmp-td cmp-td--current cmp-td--prod"
              >
                <template #default="{ row }">{{ fmtNum(row.current.prodDataMgmt.count) }}</template>
              </el-table-column>
              <el-table-column
                label="数量"
                min-width="64"
                align="center"
                label-class-name="cmp-th-sub cmp-th-sub--current cmp-th-sub--prod"
                class-name="cmp-td cmp-td--current cmp-td--prod"
              >
                <template #default="{ row }">{{ fmtQty(row.current.prodDataMgmt.quantity) }}</template>
              </el-table-column>
              <el-table-column
                label="比率"
                min-width="52"
                align="center"
                label-class-name="cmp-th-sub cmp-th-sub--current cmp-th-sub--prod"
                class-name="cmp-td cmp-td--current cmp-td--prod"
              >
                <template #default="{ row }">
                  <span class="ratio-pill" :class="ratioTone(row.current.prodDataMgmtCountRatio)">
                    {{ fmtPct(row.current.prodDataMgmtCountRatio) }}
                  </span>
                </template>
              </el-table-column>
            </el-table-column>
            <el-table-column align="center" min-width="188" label-class-name="cmp-th cmp-th--compare cmp-th--prod">
              <template #header>
                <div class="cmp-col-head">
                  <span class="cmp-col-type cmp-col-type--prod">実績修正</span>
                  <span class="cmp-month-tag cmp-month-tag--compare">{{ stats?.compareMonth }}</span>
                </div>
              </template>
              <el-table-column
                label="件数"
                min-width="52"
                align="center"
                label-class-name="cmp-th-sub cmp-th-sub--compare cmp-th-sub--prod"
                class-name="cmp-td cmp-td--compare cmp-td--prod"
              >
                <template #default="{ row }">{{ fmtNum(row.compare.prodDataMgmt.count) }}</template>
              </el-table-column>
              <el-table-column
                label="数量"
                min-width="64"
                align="center"
                label-class-name="cmp-th-sub cmp-th-sub--compare cmp-th-sub--prod"
                class-name="cmp-td cmp-td--compare cmp-td--prod"
              >
                <template #default="{ row }">{{ fmtQty(row.compare.prodDataMgmt.quantity) }}</template>
              </el-table-column>
              <el-table-column
                label="比率"
                min-width="52"
                align="center"
                label-class-name="cmp-th-sub cmp-th-sub--compare cmp-th-sub--prod"
                class-name="cmp-td cmp-td--compare cmp-td--prod"
              >
                <template #default="{ row }">
                  {{ fmtPct(row.compare.prodDataMgmtCountRatio) }}
                </template>
              </el-table-column>
            </el-table-column>
            <el-table-column label="前月比" align="center" min-width="120" label-class-name="cmp-th cmp-th--delta">
              <el-table-column
                label="件数"
                min-width="56"
                align="center"
                label-class-name="cmp-th-sub cmp-th-sub--delta"
                class-name="cmp-td cmp-td--delta"
              >
                <template #default="{ row }">
                  <span class="cmp-delta" :class="deltaClass(row.prodCountChange)">
                    {{ fmtSignedNum(row.prodCountChange) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column
                label="数量"
                min-width="64"
                align="center"
                label-class-name="cmp-th-sub cmp-th-sub--delta"
                class-name="cmp-td cmp-td--delta"
              >
                <template #default="{ row }">
                  <span class="cmp-delta" :class="deltaClass(row.prodQtyChange)">
                    {{ fmtSignedQty(row.prodQtyChange) }}
                  </span>
                </template>
              </el-table-column>
            </el-table-column>
            <el-table-column align="center" min-width="72" label-class-name="cmp-th cmp-th--current cmp-th--auto">
              <template #header>
                <div class="cmp-col-head">
                  <span class="cmp-col-type cmp-col-type--auto">実績集計</span>
                  <span class="cmp-month-tag cmp-month-tag--current">{{ stats?.month }}</span>
                </div>
              </template>
              <el-table-column
                label="件数"
                min-width="52"
                align="center"
                label-class-name="cmp-th-sub cmp-th-sub--current cmp-th-sub--auto"
                class-name="cmp-td cmp-td--current cmp-td--auto"
              >
                <template #default="{ row }">{{ fmtNum(row.current.auto.count) }}</template>
              </el-table-column>
            </el-table-column>
            <el-table-column align="center" min-width="72" label-class-name="cmp-th cmp-th--compare cmp-th--auto">
              <template #header>
                <div class="cmp-col-head">
                  <span class="cmp-col-type cmp-col-type--auto">実績集計</span>
                  <span class="cmp-month-tag cmp-month-tag--compare">{{ stats?.compareMonth }}</span>
                </div>
              </template>
              <el-table-column
                label="件数"
                min-width="52"
                align="center"
                label-class-name="cmp-th-sub cmp-th-sub--compare cmp-th-sub--auto"
                class-name="cmp-td cmp-td--compare cmp-td--auto"
              >
                <template #default="{ row }">{{ fmtNum(row.compare.auto.count) }}</template>
              </el-table-column>
            </el-table-column>
          </el-table>
        </div>
      </section>

      <!-- テーブル -->
      <section class="panel glass animate-in" style="--delay: 490ms">
        <div class="panel-head panel-head--table">
          <div class="panel-head-left">
            <span class="panel-title">工程別一覧</span>
            <span class="panel-hint">行クリックで在庫取引記録へ</span>
          </div>
        </div>
        <div class="table-wrap table-wrap--fluid">
          <el-table
            :data="byProcess"
            border
            stripe
            fit
            size="small"
            class="data-table data-table--fluid data-table--clickable"
            highlight-current-row
            :max-height="tableMaxHeight"
            @row-click="openTransactionLog"
          >
            <el-table-column prop="processName" label="工程" min-width="96" fixed="left" show-overflow-tooltip />
            <el-table-column label="実績修正" align="center" min-width="188">
              <el-table-column label="件数" min-width="52" align="center">
                <template #default="{ row }">{{ fmtNum(row.prodDataMgmt?.count) }}</template>
              </el-table-column>
              <el-table-column label="数量" min-width="64" align="center">
                <template #default="{ row }">{{ fmtQty(row.prodDataMgmt?.quantity) }}</template>
              </el-table-column>
              <el-table-column label="比率" min-width="52" align="center">
                <template #default="{ row }">
                  <span class="ratio-pill" :class="ratioTone(row.prodDataMgmtCountRatio)">
                    {{ fmtPct(row.prodDataMgmtCountRatio) }}
                  </span>
                </template>
              </el-table-column>
            </el-table-column>
            <el-table-column label="実績集計" align="center" min-width="128">
              <el-table-column label="件数" min-width="52" align="center">
                <template #default="{ row }">{{ fmtNum(row.auto?.count) }}</template>
              </el-table-column>
              <el-table-column label="数量" min-width="64" align="center">
                <template #default="{ row }">{{ fmtQty(row.auto?.quantity) }}</template>
              </el-table-column>
            </el-table-column>
            <el-table-column label="総件数" min-width="56" align="center">
              <template #default="{ row }">{{ fmtNum(row.total?.count) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </section>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis,
  RefreshLeft,
  Search,
  EditPen,
  PieChart,
  TrendCharts,
  Loading,
  Printer,
  Download,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import type { OptionItem } from '@/types/master'
import { openPrintWindow, PRINT_POPUP_BLOCKED_MSG } from '@/utils/printWindow'
import { downloadExcelFromJson } from '@/utils/excelExport'
import { buildManualEntryStatisticsPrintHtml } from './manualEntryStatisticsPrint'

interface Bucket {
  count: number
  quantity: number
}

interface MonthSummary {
  prodDataMgmt: Bucket
  auto: Bucket
  total: Bucket
  prodDataMgmtCountRatio: number
  prodDataMgmtQuantityRatio: number
}

interface ProcessRow {
  processCd: string
  processName: string
  prodDataMgmt: Bucket
  auto: Bucket
  total: Bucket
  prodDataMgmtCountRatio: number
}

interface TrendRow {
  month: string
  prodDataMgmtCount: number
  autoCount: number
  totalCount: number
  prodDataMgmtCountRatio: number
  prodDataMgmtQuantity: number
  autoQuantity: number
  totalQuantity: number
  prodDataMgmtQuantityRatio: number
}

interface ProcessCompareRow {
  processCd: string
  processName: string
  current: ProcessRow
  compare: ProcessRow
  prodCountChange: number
  prodQtyChange: number
  autoCountChange: number
}

interface StatsResponse {
  month: string
  compareMonth: string
  trendMonths: number
  current: MonthSummary
  compare: MonthSummary
  monthOverMonth: {
    prodDataMgmtCountChange: number
    prodDataMgmtCountChangeRate: number | null
    prodDataMgmtQuantityChange: number
    prodDataMgmtQuantityChangeRate: number | null
    prodDataMgmtCountRatioChange: number
    prodDataMgmtQuantityRatioChange: number
    autoCountChange: number
    autoCountChangeRate: number | null
    autoQuantityChange: number
    autoQuantityChangeRate: number | null
  }
  byProcess: ProcessRow[]
  byProcessCompare: ProcessRow[]
  byMonthTrend: TrendRow[]
}

const CHART_THEME = {
  prod: '#f97316',
  auto: '#10b981',
  primary: '#3b82f6',
  muted: '#94a3b8',
  danger: '#ef4444',
  warn: '#f59e0b',
  text: '#64748b',
  grid: 'rgba(148, 163, 184, 0.2)',
}

const API_BASE = '/api/erp/stock-transaction-logs/manual-entry-statistics'
const router = useRouter()

const loading = ref(false)
const exportingProcessCompare = ref(false)
const exportingRatioTrend = ref(false)
const contentReady = ref(false)
const stats = ref<StatsResponse | null>(null)
const processOptions = ref<OptionItem[]>([])
const tableMaxHeight = ref(360)

const defaultMonth = dayjs().format('YYYY-MM')
const defaultCompare = dayjs().subtract(1, 'month').format('YYYY-MM')

const filters = ref({
  month: defaultMonth,
  compareMonth: defaultCompare,
  trendMonths: 6,
  processCd: '',
})

const current = computed(() => stats.value?.current)
const compare = computed(() => stats.value?.compare)
const mom = computed(() => stats.value?.monthOverMonth)
const byProcess = computed(() => stats.value?.byProcess ?? [])

function emptyProcessRow(processCd: string, processName: string): ProcessRow {
  return {
    processCd,
    processName,
    prodDataMgmt: { count: 0, quantity: 0 },
    auto: { count: 0, quantity: 0 },
    total: { count: 0, quantity: 0 },
    prodDataMgmtCountRatio: 0,
  }
}

const byProcessComparison = computed<ProcessCompareRow[]>(() => {
  const curList = stats.value?.byProcess ?? []
  const cmpList = stats.value?.byProcessCompare ?? []
  const curMap = new Map(curList.map((r) => [r.processCd, r]))
  const cmpMap = new Map(cmpList.map((r) => [r.processCd, r]))
  const keys = new Set([...curMap.keys(), ...cmpMap.keys()])
  return [...keys]
    .map((cd) => {
      const cur = curMap.get(cd)
      const cmp = cmpMap.get(cd)
      const name = cur?.processName || cmp?.processName || cd
      const current = cur ?? emptyProcessRow(cd, name)
      const compare = cmp ?? emptyProcessRow(cd, name)
      return {
        processCd: cd,
        processName: name,
        current,
        compare,
        prodCountChange: current.prodDataMgmt.count - compare.prodDataMgmt.count,
        prodQtyChange: current.prodDataMgmt.quantity - compare.prodDataMgmt.quantity,
        autoCountChange: current.auto.count - compare.auto.count,
      }
    })
    .sort((a, b) => b.current.prodDataMgmt.count - a.current.prodDataMgmt.count)
})

const kpiCards = computed(() => [
  {
    key: 'prod',
    tone: 'prod',
    icon: EditPen,
    label: '実績修正',
    desc: '生産データ管理由来',
    countLabel: '修正件数',
    value: fmtNum(current.value?.prodDataMgmt?.count),
    unit: '件',
    delta: `前月比 ${fmtDelta(mom.value?.prodDataMgmtCountChange, mom.value?.prodDataMgmtCountChangeRate)}`,
    deltaRaw: mom.value?.prodDataMgmtCountChange,
    qtyLabel: '修正数量',
    qtyValue: fmtQty(current.value?.prodDataMgmt?.quantity),
    qtyDelta: `前月比 ${fmtQtyDelta(mom.value?.prodDataMgmtQuantityChange, mom.value?.prodDataMgmtQuantityChangeRate)}`,
    qtyDeltaRaw: mom.value?.prodDataMgmtQuantityChange,
  },
  {
    key: 'auto',
    tone: 'auto',
    icon: TrendCharts,
    label: '実績集計',
    desc: '手入力を除く実績',
    countLabel: '集計件数',
    value: fmtNum(current.value?.auto?.count),
    unit: '件',
    delta: `前月比 ${fmtDelta(mom.value?.autoCountChange, mom.value?.autoCountChangeRate)}`,
    deltaRaw: mom.value?.autoCountChange,
    sub: `総件数 ${fmtNum(current.value?.total?.count)}`,
    qtyLabel: '集計数量',
    qtyValue: fmtQty(current.value?.auto?.quantity),
    qtyDelta: `前月比 ${fmtQtyDelta(mom.value?.autoQuantityChange, mom.value?.autoQuantityChangeRate)}`,
    qtyDeltaRaw: mom.value?.autoQuantityChange,
    qtySub: `総数量 ${fmtQty(current.value?.total?.quantity)}`,
  },
  {
    key: 'ratio',
    tone: 'ratio',
    icon: PieChart,
    label: '修正比率',
    desc: '修正 ÷ 総計',
    countLabel: '件数比率',
    value: fmtPct(current.value?.prodDataMgmtCountRatio),
    delta: `前月比 ${fmtPctPoint(mom.value?.prodDataMgmtCountRatioChange)}`,
    deltaRaw: mom.value?.prodDataMgmtCountRatioChange,
    qtyLabel: '数量比率',
    qtyValue: fmtPct(current.value?.prodDataMgmtQuantityRatio),
    qtyDelta: `前月比 ${fmtPctPoint(mom.value?.prodDataMgmtQuantityRatioChange)}`,
    qtyDeltaRaw: mom.value?.prodDataMgmtQuantityRatioChange,
  },
])

const monthCompareChartRef = ref<HTMLElement | null>(null)
const qtyCompareChartRef = ref<HTMLElement | null>(null)
const trendChartRef = ref<HTMLElement | null>(null)
const qtyTrendChartRef = ref<HTMLElement | null>(null)
const processChartRef = ref<HTMLElement | null>(null)
const processCompareChartRef = ref<HTMLElement | null>(null)
let monthCompareChart: echarts.ECharts | null = null
let qtyCompareChart: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null
let qtyTrendChart: echarts.ECharts | null = null
let processChart: echarts.ECharts | null = null
let processCompareChart: echarts.ECharts | null = null

const fmtNum = (v?: number | null) => (v == null ? '0' : Number(v).toLocaleString())
const fmtQty = (v?: number | null) =>
  v == null ? '0' : Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 })
const toQtySen = (v?: number | null) => (v == null ? 0 : Number(v) / 1000)
const fmtQtySen = (v?: number | null, withUnit = true) => {
  const n = toQtySen(v)
  const s = n.toFixed(1)
  return withUnit ? `${s}千` : s
}
const fmtSenVal = (v: number, withUnit = false) => {
  const s = Number(v).toFixed(1)
  return withUnit ? `${s}千` : s
}
const fmtPct = (v?: number | null) => (v == null ? '0.0%' : `${(Number(v) * 100).toFixed(1)}%`)
const fmtPctPoint = (v?: number | null) => {
  if (v == null) return '-'
  const n = Number(v) * 100
  return `${n >= 0 ? '+' : ''}${n.toFixed(1)}pt`
}
const fmtDelta = (change?: number | null, rate?: number | null) => {
  if (change == null) return '-'
  const sign = change > 0 ? '+' : ''
  const rateStr =
    rate == null ? '' : ` (${rate > 0 ? '+' : ''}${(Number(rate) * 100).toFixed(1)}%)`
  return `${sign}${change}${rateStr}`
}
const fmtQtyDelta = (change?: number | null, rate?: number | null) => {
  if (change == null) return '-'
  const sign = change > 0 ? '+' : ''
  const qtyStr = Number(change).toLocaleString(undefined, { maximumFractionDigits: 2 })
  const rateStr =
    rate == null ? '' : ` (${rate > 0 ? '+' : ''}${(Number(rate) * 100).toFixed(1)}%)`
  return `${sign}${qtyStr}${rateStr}`
}
const fmtSignedNum = (v?: number | null) => {
  if (v == null || v === 0) return v === 0 ? '0' : '-'
  return `${v > 0 ? '+' : ''}${Number(v).toLocaleString()}`
}
const fmtSignedQty = (v?: number | null) => {
  if (v == null || v === 0) return v === 0 ? '0' : '-'
  const s = Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 })
  return `${v > 0 ? '+' : ''}${s}`
}
const deltaClass = (change?: number | null) => {
  if (change == null || change === 0) return ''
  return change < 0 ? 'delta-good' : 'delta-bad'
}
const ratioTone = (ratio: number) => {
  if (ratio >= 0.1) return 'ratio-pill--high'
  if (ratio >= 0.03) return 'ratio-pill--mid'
  return 'ratio-pill--low'
}

function updateTableHeight() {
  const vh = window.innerHeight
  const vw = window.innerWidth
  if (vw <= 640) {
    tableMaxHeight.value = Math.max(200, Math.min(320, vh - 420))
  } else if (vw <= 1100) {
    tableMaxHeight.value = Math.max(240, Math.min(380, vh - 480))
  } else {
    tableMaxHeight.value = Math.max(260, Math.min(460, vh - 500))
  }
}

function chartMonthRange(ym: string) {
  const start = `${ym}-01`
  const end = dayjs(start).endOf('month').format('YYYY-MM-DD')
  return `対象月 ${ym}（${start} ～ ${end}）`
}

const CHART_FONT =
  '"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", "Yu Gothic UI", Meiryo, system-ui, sans-serif'

function chartDpr() {
  return Math.min(Math.max(window.devicePixelRatio || 1, 1.5), 3)
}

function initChart(el: HTMLElement) {
  return echarts.init(el, undefined, {
    renderer: 'canvas',
    devicePixelRatio: chartDpr(),
  })
}

function chartTextStyle(fontSize = 12, color = '#334155') {
  return { fontFamily: CHART_FONT, fontSize, color }
}

function chartTooltipBase(extra: Record<string, unknown> = {}) {
  return {
    trigger: 'axis' as const,
    backgroundColor: 'rgba(15, 23, 42, 0.94)',
    borderWidth: 0,
    padding: [10, 14] as [number, number],
    textStyle: { color: '#f8fafc', fontSize: 12, fontFamily: CHART_FONT, fontWeight: 500 },
    extraCssText:
      'border-radius:10px;box-shadow:0 12px 28px rgba(0,0,0,0.22);backdrop-filter:blur(8px);',
    ...extra,
  }
}

function chartLegendBase(data: string[]) {
  return {
    data,
    bottom: 4,
    itemWidth: 12,
    itemHeight: 12,
    itemGap: 18,
    textStyle: { fontSize: 11, color: '#475569', fontWeight: 600, fontFamily: CHART_FONT },
  }
}

function baseChartGrid() {
  return { left: 44, right: 16, top: 44, bottom: 40, containLabel: true }
}

function axisStyle() {
  return {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: CHART_THEME.text, fontSize: 11, fontFamily: CHART_FONT, fontWeight: 500 },
    splitLine: { lineStyle: { color: CHART_THEME.grid, type: 'dashed' as const } },
  }
}

async function loadProcessOptions() {
  try {
    const res = await request.get<OptionItem[]>('/api/master/processes/options')
    processOptions.value = Array.isArray(res) ? res : (res as { data?: OptionItem[] })?.data ?? []
  } catch {
    processOptions.value = []
  }
}

function buildParams() {
  return {
    month: filters.value.month || undefined,
    compare_month: filters.value.compareMonth || undefined,
    trend_months: filters.value.trendMonths,
    process_cd: filters.value.processCd || undefined,
  }
}

async function fetchStats() {
  if (!filters.value.month) {
    ElMessage.warning('対象月を選択してください')
    return
  }
  loading.value = true
  contentReady.value = false
  try {
    stats.value = (await request.get(API_BASE, { params: buildParams() })) as StatsResponse
    if (!filters.value.compareMonth && stats.value?.compareMonth) {
      filters.value.compareMonth = stats.value.compareMonth
    }
    await nextTick()
    contentReady.value = true
    await nextTick()
    renderCharts()
  } catch (e) {
    console.error(e)
    ElMessage.error('統計データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.value = {
    month: defaultMonth,
    compareMonth: defaultCompare,
    trendMonths: 6,
    processCd: '',
  }
  fetchStats()
}

function disposeCharts() {
  monthCompareChart?.dispose()
  qtyCompareChart?.dispose()
  trendChart?.dispose()
  qtyTrendChart?.dispose()
  processChart?.dispose()
  processCompareChart?.dispose()
  monthCompareChart = null
  qtyCompareChart = null
  trendChart = null
  qtyTrendChart = null
  processChart = null
  processCompareChart = null
}

function chartAnimBase() {
  return {
    animationDuration: 900,
    animationEasing: 'cubicOut' as const,
    animationDelay: (idx: number) => idx * 60,
  }
}

function barEmphasis(color: string) {
  return {
    focus: 'series' as const,
    itemStyle: {
      shadowBlur: 14,
      shadowColor: `${color}66`,
      shadowOffsetY: 4,
    },
  }
}

function barTopLabel(color = '#334155', fontSize = 10) {
  return {
    show: true,
    position: 'top' as const,
    distance: 5,
    fontSize,
    fontWeight: 700,
    fontFamily: CHART_FONT,
    color,
    formatter: (p: { value: number }) => (Number(p.value) > 0 ? fmtNum(p.value) : ''),
  }
}

function barTopQtyLabel(color = '#334155', fontSize = 10) {
  return {
    show: true,
    position: 'top' as const,
    distance: 5,
    fontSize,
    fontWeight: 700,
    fontFamily: CHART_FONT,
    color,
    formatter: (p: { value: number }) => (Number(p.value) > 0 ? fmtQty(p.value) : ''),
  }
}

function barTopQtySenLabel(color = '#334155', fontSize = 10) {
  return {
    show: true,
    position: 'top' as const,
    distance: 5,
    fontSize,
    fontWeight: 700,
    fontFamily: CHART_FONT,
    color,
    formatter: (p: { value: number }) => {
      const v = Number(p.value)
      return v > 0 ? fmtSenVal(v) : ''
    },
  }
}

function lineTopLabel(color: string, suffix = '') {
  return {
    show: true,
    position: 'top' as const,
    distance: 6,
    fontSize: 10,
    fontWeight: 700,
    fontFamily: CHART_FONT,
    color,
    formatter: (p: { value: number }) =>
      p.value == null || Number.isNaN(Number(p.value)) ? '' : `${p.value}${suffix}`,
  }
}

function renderCharts() {
  if (!stats.value) return
  disposeCharts()

  const anim = chartAnimBase()

  if (monthCompareChartRef.value) {
    monthCompareChart = initChart(monthCompareChartRef.value)
    const cur = stats.value.current
    const cmp = stats.value.compare
    monthCompareChart.setOption({
      ...anim,
      textStyle: chartTextStyle(),
      tooltip: chartTooltipBase(),
      legend: chartLegendBase([stats.value.compareMonth, stats.value.month]),
      grid: { ...baseChartGrid(), bottom: 48 },
      xAxis: {
        type: 'category',
        data: ['実績修正', '実績集計', '総件数'],
        axisLabel: { color: '#475569', fontSize: 11, fontWeight: 600, fontFamily: CHART_FONT, interval: 0 },
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisTick: { show: false },
      },
      yAxis: { type: 'value', minInterval: 1, ...axisStyle() },
      series: [
        {
          name: stats.value.compareMonth,
          type: 'bar',
          barMaxWidth: 28,
          barGap: '28%',
          label: barTopLabel('#64748b', 11),
          emphasis: barEmphasis('#94a3b8'),
          itemStyle: {
            borderRadius: [6, 6, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#e2e8f0' },
              { offset: 1, color: '#94a3b8' },
            ]),
          },
          data: [cmp.prodDataMgmt.count, cmp.auto.count, cmp.total.count],
        },
        {
          name: stats.value.month,
          type: 'bar',
          barMaxWidth: 28,
          label: barTopLabel('#1d4ed8', 11),
          emphasis: barEmphasis('#3b82f6'),
          itemStyle: {
            borderRadius: [6, 6, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#93c5fd' },
              { offset: 1, color: '#2563eb' },
            ]),
          },
          data: [cur.prodDataMgmt.count, cur.auto.count, cur.total.count],
        },
      ],
    })
  }

  if (qtyCompareChartRef.value) {
    qtyCompareChart = initChart(qtyCompareChartRef.value)
    const cur = stats.value.current
    const cmp = stats.value.compare
    qtyCompareChart.setOption({
      ...anim,
      textStyle: chartTextStyle(),
      tooltip: chartTooltipBase({
        valueFormatter: (v: number) => fmtSenVal(Number(v), true),
      }),
      legend: chartLegendBase([stats.value.compareMonth, stats.value.month]),
      grid: { ...baseChartGrid(), bottom: 48 },
      xAxis: {
        type: 'category',
        data: ['実績修正', '実績集計', '総数量'],
        axisLabel: { color: '#475569', fontSize: 11, fontWeight: 600, fontFamily: CHART_FONT, interval: 0 },
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        name: '千',
        nameTextStyle: { fontSize: 11, color: '#94a3b8', fontFamily: CHART_FONT },
        ...axisStyle(),
        axisLabel: {
          ...axisStyle().axisLabel,
          formatter: (v: number) => fmtSenVal(v),
        },
      },
      series: [
        {
          name: stats.value.compareMonth,
          type: 'bar',
          barMaxWidth: 28,
          barGap: '28%',
          label: barTopQtySenLabel('#64748b', 10),
          emphasis: barEmphasis('#94a3b8'),
          itemStyle: {
            borderRadius: [6, 6, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#e9d5ff' },
              { offset: 1, color: '#a78bfa' },
            ]),
          },
          data: [
            toQtySen(cmp.prodDataMgmt.quantity),
            toQtySen(cmp.auto.quantity),
            toQtySen(cmp.total.quantity),
          ],
        },
        {
          name: stats.value.month,
          type: 'bar',
          barMaxWidth: 28,
          label: barTopQtySenLabel('#6d28d9', 10),
          emphasis: barEmphasis('#8b5cf6'),
          itemStyle: {
            borderRadius: [6, 6, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#ddd6fe' },
              { offset: 1, color: '#7c3aed' },
            ]),
          },
          data: [
            toQtySen(cur.prodDataMgmt.quantity),
            toQtySen(cur.auto.quantity),
            toQtySen(cur.total.quantity),
          ],
        },
      ],
    })
  }

  if (trendChartRef.value) {
    trendChart = initChart(trendChartRef.value)
    const trend = stats.value.byMonthTrend
    trendChart.setOption({
      ...anim,
      textStyle: chartTextStyle(),
      tooltip: chartTooltipBase(),
      legend: chartLegendBase(['修正件数', '修正比率']),
      grid: { ...baseChartGrid(), right: 48, bottom: 48 },
      xAxis: {
        type: 'category',
        data: trend.map((t) => t.month),
        axisLabel: { color: '#475569', fontSize: 11, fontWeight: 500, fontFamily: CHART_FONT },
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisTick: { show: false },
      },
      yAxis: [
        {
          type: 'value',
          name: '件数',
          nameTextStyle: { fontSize: 11, color: '#94a3b8', fontFamily: CHART_FONT },
          minInterval: 1,
          ...axisStyle(),
        },
        {
          type: 'value',
          name: '%',
          min: 0,
          max: 20,
          nameTextStyle: { fontSize: 11, color: '#94a3b8', fontFamily: CHART_FONT },
          axisLabel: { formatter: '{value}%', color: '#94a3b8', fontSize: 11, fontFamily: CHART_FONT },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: '修正件数',
          type: 'bar',
          barMaxWidth: 22,
          label: barTopLabel('#ca8a04', 10),
          emphasis: barEmphasis('#fbbf24'),
          itemStyle: {
            borderRadius: [5, 5, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#fef9c3' },
              { offset: 1, color: '#fbbf24' },
            ]),
          },
          data: trend.map((t) => t.prodDataMgmtCount),
        },
        {
          name: '修正比率',
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          label: lineTopLabel(CHART_THEME.danger, '%'),
          lineStyle: { width: 3, color: CHART_THEME.danger, shadowColor: 'rgba(239,68,68,0.4)', shadowBlur: 8 },
          itemStyle: { color: '#fff', borderColor: CHART_THEME.danger, borderWidth: 2.5 },
          emphasis: { scale: 1.4 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(239, 68, 68, 0.22)' },
              { offset: 1, color: 'rgba(239, 68, 68, 0)' },
            ]),
          },
          data: trend.map((t) => Number((t.prodDataMgmtCountRatio * 100).toFixed(2))),
        },
      ],
    })
  }

  if (qtyTrendChartRef.value) {
    qtyTrendChart = initChart(qtyTrendChartRef.value)
    const trend = stats.value.byMonthTrend
    qtyTrendChart.setOption({
      ...anim,
      textStyle: chartTextStyle(),
      tooltip: chartTooltipBase({
        valueFormatter: (v: number, _idx: number, series: { seriesName?: string }) => {
          if (series?.seriesName === '修正数量比率') {
            return `${Number(v).toFixed(2)}%`
          }
          return fmtQty(Number(v))
        },
      }),
      legend: chartLegendBase(['修正数量', '修正数量比率']),
      grid: { ...baseChartGrid(), right: 48, bottom: 48 },
      xAxis: {
        type: 'category',
        data: trend.map((t) => t.month),
        axisLabel: { color: '#475569', fontSize: 11, fontWeight: 500, fontFamily: CHART_FONT },
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisTick: { show: false },
      },
      yAxis: [
        {
          type: 'value',
          name: '数量',
          nameTextStyle: { fontSize: 11, color: '#94a3b8', fontFamily: CHART_FONT },
          ...axisStyle(),
        },
        {
          type: 'value',
          name: '%',
          min: 0,
          max: 20,
          nameTextStyle: { fontSize: 11, color: '#94a3b8', fontFamily: CHART_FONT },
          axisLabel: { formatter: '{value}%', color: '#94a3b8', fontSize: 11, fontFamily: CHART_FONT },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: '修正数量',
          type: 'bar',
          barMaxWidth: 22,
          label: barTopQtyLabel('#6d28d9', 10),
          emphasis: barEmphasis('#a78bfa'),
          itemStyle: {
            borderRadius: [5, 5, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#ede9fe' },
              { offset: 1, color: '#a78bfa' },
            ]),
          },
          data: trend.map((t) => t.prodDataMgmtQuantity),
        },
        {
          name: '修正数量比率',
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          label: lineTopLabel('#7c3aed', '%'),
          lineStyle: { width: 3, color: '#7c3aed', shadowColor: 'rgba(124,58,237,0.4)', shadowBlur: 8 },
          itemStyle: { color: '#fff', borderColor: '#7c3aed', borderWidth: 2.5 },
          emphasis: { scale: 1.4 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(124, 58, 237, 0.22)' },
              { offset: 1, color: 'rgba(124, 58, 237, 0)' },
            ]),
          },
          data: trend.map((t) => Number((t.prodDataMgmtQuantityRatio * 100).toFixed(2))),
        },
      ],
    })
  }

  if (processCompareChartRef.value) {
    processCompareChart = initChart(processCompareChartRef.value)
    const rows = byProcessComparison.value.slice(0, 14)
    const cmpLabel = stats.value.compareMonth
    const curLabel = stats.value.month
    processCompareChart.setOption({
      ...anim,
      textStyle: chartTextStyle(),
      tooltip: chartTooltipBase({
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(20,184,166,0.08)' } },
      }),
      legend: chartLegendBase([
        `${cmpLabel} 実績修正`,
        `${curLabel} 実績修正`,
        `${cmpLabel} 実績集計`,
        `${curLabel} 実績集計`,
      ]),
      grid: { left: 44, right: 16, top: 44, bottom: 68, containLabel: true },
      xAxis: {
        type: 'category',
        data: rows.map((r) => r.processName),
        axisLabel: {
          color: '#475569',
          fontSize: 11,
          rotate: 28,
          fontWeight: 500,
          fontFamily: CHART_FONT,
        },
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisTick: { show: false },
      },
      yAxis: { type: 'value', minInterval: 1, ...axisStyle() },
      series: [
        {
          name: `${cmpLabel} 実績修正`,
          type: 'bar',
          barMaxWidth: 18,
          barGap: '18%',
          label: barTopLabel('#64748b', 9),
          emphasis: barEmphasis('#94a3b8'),
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#e2e8f0' },
              { offset: 1, color: '#94a3b8' },
            ]),
          },
          data: rows.map((r) => r.compare.prodDataMgmt.count),
        },
        {
          name: `${curLabel} 実績修正`,
          type: 'bar',
          barMaxWidth: 18,
          label: barTopLabel('#c2410c', 9),
          emphasis: barEmphasis(CHART_THEME.prod),
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#fdba74' },
              { offset: 1, color: CHART_THEME.prod },
            ]),
          },
          data: rows.map((r) => r.current.prodDataMgmt.count),
        },
        {
          name: `${cmpLabel} 実績集計`,
          type: 'bar',
          barMaxWidth: 18,
          label: barTopLabel('#64748b', 9),
          emphasis: barEmphasis('#94a3b8'),
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#f1f5f9' },
              { offset: 1, color: '#cbd5e1' },
            ]),
          },
          data: rows.map((r) => r.compare.auto.count),
        },
        {
          name: `${curLabel} 実績集計`,
          type: 'bar',
          barMaxWidth: 18,
          label: barTopLabel('#047857', 9),
          emphasis: barEmphasis(CHART_THEME.auto),
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#6ee7b7' },
              { offset: 1, color: CHART_THEME.auto },
            ]),
          },
          data: rows.map((r) => r.current.auto.count),
        },
      ],
    })
  }

  if (processChartRef.value) {
    processChart = initChart(processChartRef.value)
    const rows = stats.value.byProcess.slice(0, 14)
    processChart.setOption({
      ...anim,
      textStyle: chartTextStyle(),
      title: {
        text: '工程別内訳',
        subtext: chartMonthRange(stats.value.month),
        left: 'center',
        top: 2,
        textStyle: { fontSize: 12, fontWeight: 700, color: '#334155', fontFamily: CHART_FONT },
        subtextStyle: { fontSize: 11, fontWeight: 600, color: '#2563eb', fontFamily: CHART_FONT },
      },
      tooltip: chartTooltipBase({
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(59,130,246,0.08)' } },
      }),
      legend: chartLegendBase(['実績修正', '実績集計']),
      grid: { left: 44, right: 16, top: 54, bottom: 60, containLabel: true },
      xAxis: {
        type: 'category',
        data: rows.map((r) => r.processName),
        axisLabel: {
          color: '#475569',
          fontSize: 11,
          rotate: 28,
          fontWeight: 500,
          fontFamily: CHART_FONT,
        },
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisTick: { show: false },
      },
      yAxis: { type: 'value', minInterval: 1, ...axisStyle() },
      series: [
        {
          name: '実績修正',
          type: 'bar',
          barMaxWidth: 24,
          barGap: '28%',
          label: barTopLabel('#c2410c', 11),
          emphasis: barEmphasis(CHART_THEME.prod),
          itemStyle: {
            borderRadius: [5, 5, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#fb923c' },
              { offset: 1, color: CHART_THEME.prod },
            ]),
          },
          data: rows.map((r) => r.prodDataMgmt.count),
        },
        {
          name: '実績集計',
          type: 'bar',
          barMaxWidth: 24,
          label: barTopLabel('#047857', 11),
          emphasis: barEmphasis(CHART_THEME.auto),
          itemStyle: {
            borderRadius: [5, 5, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#34d399' },
              { offset: 1, color: CHART_THEME.auto },
            ]),
          },
          data: rows.map((r) => r.auto.count),
        },
      ],
    })
  }
}

function chartToPng(chart: echarts.ECharts | null): string | undefined {
  if (!chart) return undefined
  try {
    return chart.getDataURL({
      type: 'png',
      pixelRatio: Math.min(chartDpr(), 2.5),
      backgroundColor: '#fff',
    })
  } catch {
    return undefined
  }
}

function selectedProcessLabel(): string {
  if (!filters.value.processCd) return '全工程'
  const found = processOptions.value.find((p) => p.cd === filters.value.processCd)
  return found?.name || filters.value.processCd
}

async function exportRatioTrendExcel() {
  const trend = stats.value?.byMonthTrend ?? []
  if (!trend.length) {
    ElMessage.warning('出力するデータがありません。先に検索を実行してください。')
    return
  }

  const months = filters.value.trendMonths || stats.value?.trendMonths || trend.length
  const pct = (v?: number | null) =>
    v == null ? 0 : Number((Number(v) * 100).toFixed(2))

  exportingRatioTrend.value = true
  try {
    const exportRows = trend.map((row) => ({
      月: row.month,
      修正件数: row.prodDataMgmtCount,
      実績集計件数: row.autoCount,
      総件数: row.totalCount,
      '修正比率(%)': pct(row.prodDataMgmtCountRatio),
    }))

    await downloadExcelFromJson(
      exportRows,
      '修正比率推移',
      `修正比率推移_${months}ヶ月.xlsx`,
    )
    ElMessage.success('Excelを出力しました')
  } catch (e) {
    console.error(e)
    ElMessage.error('Excel出力に失敗しました')
  } finally {
    exportingRatioTrend.value = false
  }
}

async function exportProcessCompareExcel() {
  const rows = byProcessComparison.value
  if (!rows.length) {
    ElMessage.warning('出力するデータがありません。先に検索を実行してください。')
    return
  }

  const month = stats.value?.month || filters.value.month
  const compareMonth = stats.value?.compareMonth || filters.value.compareMonth
  const pct = (v?: number | null) =>
    v == null ? 0 : Number((Number(v) * 100).toFixed(1))

  exportingProcessCompare.value = true
  try {
    const exportRows = rows.map((row) => ({
      工程: row.processName,
      [`実績修正件数_${month}`]: row.current.prodDataMgmt.count,
      [`実績修正数量_${month}`]: row.current.prodDataMgmt.quantity,
      [`実績修正比率%_${month}`]: pct(row.current.prodDataMgmtCountRatio),
      [`実績修正件数_${compareMonth}`]: row.compare.prodDataMgmt.count,
      [`実績修正数量_${compareMonth}`]: row.compare.prodDataMgmt.quantity,
      [`実績修正比率%_${compareMonth}`]: pct(row.compare.prodDataMgmtCountRatio),
      前月比件数: row.prodCountChange,
      前月比数量: row.prodQtyChange,
      [`実績集計件数_${month}`]: row.current.auto.count,
      [`実績集計件数_${compareMonth}`]: row.compare.auto.count,
    }))

    const fileTag = `${compareMonth}_${month}`.replace(/[^\d_-]/g, '')
    await downloadExcelFromJson(
      exportRows,
      '工程別比較一覧',
      `工程別比較一覧_${fileTag}.xlsx`,
    )
    ElMessage.success('Excelを出力しました')
  } catch (e) {
    console.error(e)
    ElMessage.error('Excel出力に失敗しました')
  } finally {
    exportingProcessCompare.value = false
  }
}

function handlePrintReport() {
  if (!stats.value) {
    ElMessage.warning('印刷するデータがありません。先に検索を実行してください。')
    return
  }

  try {
    const html = buildManualEntryStatisticsPrintHtml({
      printedAt: dayjs().format('YYYY-MM-DD HH:mm'),
      month: stats.value.month,
      compareMonth: stats.value.compareMonth,
      trendMonths: stats.value.trendMonths,
      processLabel: selectedProcessLabel(),
      current: stats.value.current,
      compare: stats.value.compare,
      monthOverMonth: stats.value.monthOverMonth,
      kpiCards: kpiCards.value.map((k) => ({
        label: k.label,
        desc: k.desc,
        countLabel: k.countLabel,
        value: k.value,
        unit: k.unit,
        delta: k.delta,
        sub: k.sub,
        qtyLabel: k.qtyLabel,
        qtyValue: k.qtyValue,
        qtyDelta: k.qtyDelta,
        qtySub: k.qtySub,
      })),
      byProcess: stats.value.byProcess,
      byProcessComparison: byProcessComparison.value,
      byMonthTrend: stats.value.byMonthTrend,
      chartImages: {
        monthCompare: chartToPng(monthCompareChart),
        qtyCompare: chartToPng(qtyCompareChart),
        countTrend: chartToPng(trendChart),
        qtyTrend: chartToPng(qtyTrendChart),
        processCompare: chartToPng(processCompareChart),
        process: chartToPng(processChart),
      },
      formatters: {
        fmtNum,
        fmtQty,
        fmtPct,
        fmtQtySen,
        fmtDelta,
        fmtQtyDelta,
        fmtPctPoint,
        fmtSignedNum,
        fmtSignedQty,
      },
    })

    const win = openPrintWindow(html, { autoPrint: true, autoClose: true, delayMs: 500 })
    if (!win) {
      ElMessage.error(PRINT_POPUP_BLOCKED_MSG)
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('印刷レポートの作成に失敗しました')
  }
}

function openTransactionLog(row: ProcessRow) {
  const month = stats.value?.month || filters.value.month
  const start = `${month}-01`
  const end = dayjs(start).endOf('month').format('YYYY-MM-DD')
  const proc = row.processCd === '(未設定)' ? '' : row.processCd
  router.push({
    path: '/erp/inventory/stock-transaction-logs',
    query: {
      transaction_type: '実績',
      source_file: '生産データ管理',
      process_cd: proc || undefined,
      date_start: start,
      date_end: end,
    },
  })
}

let resizeTimer: ReturnType<typeof setTimeout> | null = null

function onResize() {
  if (resizeTimer) clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => {
    updateTableHeight()
    monthCompareChart?.resize()
    qtyCompareChart?.resize()
    trendChart?.resize()
    qtyTrendChart?.resize()
    processChart?.resize()
    processCompareChart?.resize()
  }, 90)
}

watch(
  () => [filters.value.trendMonths],
  () => {
    if (stats.value) fetchStats()
  }
)

onMounted(async () => {
  updateTableHeight()
  await loadProcessOptions()
  await fetchStats()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (resizeTimer) clearTimeout(resizeTimer)
  disposeCharts()
})
</script>

<style scoped>
/* ── ベース / デザイントークン ── */
.mes-page {
  --mes-accent: #3b82f6;
  --mes-radius: 12px;
  --mes-gap: clamp(8px, 1.2vw, 14px);
  --mes-font: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Noto Sans JP', 'Yu Gothic UI',
    'Yu Gothic', Meiryo, 'Segoe UI', system-ui, sans-serif;
  --mes-font-num: 'DIN Alternate', 'TabularNums', 'Hiragino Sans', 'Noto Sans JP', Meiryo,
    system-ui, sans-serif;
  --mes-fs-xs: clamp(0.62rem, 0.55rem + 0.2vw, 0.7rem);
  --mes-fs-sm: clamp(0.7rem, 0.64rem + 0.25vw, 0.8rem);
  --mes-fs-md: clamp(0.78rem, 0.72rem + 0.3vw, 0.9rem);
  --mes-fs-lg: clamp(0.95rem, 0.88rem + 0.35vw, 1.15rem);
  --mes-fs-xl: clamp(1.15rem, 1.05rem + 0.45vw, 1.4rem);
  --mes-text: #0f172a;
  --mes-muted: #64748b;
  --mes-border: rgba(148, 163, 184, 0.28);
  position: relative;
  min-height: 100%;
  padding: clamp(8px, 1.2vw, 14px) clamp(8px, 1.5vw, 16px) clamp(12px, 1.5vw, 20px);
  font-family: var(--mes-font);
  font-size: var(--mes-fs-sm);
  color: var(--mes-text);
  line-height: 1.45;
  letter-spacing: 0.01em;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  overflow-x: hidden;
}

.page-ambient {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(1200px 600px at 12% -10%, rgba(147, 197, 253, 0.35), transparent 55%),
    radial-gradient(900px 500px at 92% 8%, rgba(196, 181, 253, 0.28), transparent 50%),
    linear-gradient(155deg, #eef2f7 0%, #e6ebf3 48%, #edf1f7 100%);
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(72px);
  opacity: 0.45;
  animation: orb-float 18s ease-in-out infinite;
}
.orb-a {
  width: 280px;
  height: 280px;
  background: #93c5fd;
  top: -80px;
  right: 8%;
}
.orb-b {
  width: 220px;
  height: 220px;
  background: #c4b5fd;
  bottom: 12%;
  left: -40px;
  animation-delay: -6s;
}
.orb-c {
  width: 180px;
  height: 180px;
  background: #fdba74;
  top: 42%;
  right: -30px;
  animation-delay: -12s;
}

@keyframes orb-float {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(12px, -16px) scale(1.06);
  }
}

.mes-inner {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: var(--mes-gap);
  width: 100%;
  max-width: min(1680px, 100%);
  margin: 0 auto;
}

.glass {
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255, 255, 255, 0.85);
  box-shadow:
    0 2px 12px rgba(15, 23, 42, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  border-radius: var(--mes-radius);
  transition:
    box-shadow 0.25s ease,
    transform 0.25s ease;
}

.glass:hover {
  box-shadow:
    0 6px 20px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

/* ── 入場アニメ ── */
.animate-in {
  opacity: 0;
  transform: translateY(10px);
  animation: fade-up 0.55s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: var(--delay, 0ms);
}

@keyframes fade-up {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── ツールバー ── */
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 0;
  padding: 0;
  overflow: visible;
}

.toolbar-elevated {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 250, 252, 0.88) 100%);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 8px 24px rgba(15, 23, 42, 0.08),
    0 2px 6px rgba(15, 23, 42, 0.04);
}

/* ブランド帯 */
.toolbar-brand-zone {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  flex: 0 0 auto;
  min-width: 168px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(99, 102, 241, 0.06) 100%);
  border-right: 1px solid rgba(59, 130, 246, 0.12);
  position: relative;
}

.toolbar-brand-zone::after {
  content: '';
  position: absolute;
  top: 8px;
  bottom: 8px;
  right: 0;
  width: 1px;
  background: linear-gradient(180deg, transparent, rgba(59, 130, 246, 0.25), transparent);
}

.brand-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(145deg, #4f8ef7 0%, #3b5bdb 55%, #6366f1 100%);
  box-shadow:
    0 2px 0 rgba(29, 78, 216, 0.5),
    0 6px 14px rgba(59, 130, 246, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.toolbar-title {
  margin: 0;
  font-size: var(--mes-fs-md);
  font-weight: 800;
  letter-spacing: 0.04em;
  line-height: 1.25;
  color: #1e3a5f;
}

.toolbar-sub {
  margin: 3px 0 0;
  font-size: var(--mes-fs-xs);
  color: var(--mes-muted);
  line-height: 1.3;
  font-weight: 500;
}

/* フィルタ帯 */
.toolbar-filters-zone {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  flex: 1 1 auto;
  gap: 6px;
  padding: 8px 10px;
  min-width: 0;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px 5px 6px;
  border-radius: 8px;
  border: 1px solid transparent;
  box-shadow:
    inset 0 1px 2px rgba(255, 255, 255, 0.8),
    0 1px 3px rgba(15, 23, 42, 0.06);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.filter-group:hover {
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 2px rgba(255, 255, 255, 0.9),
    0 4px 10px rgba(15, 23, 42, 0.08);
}

.filter-group--period {
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
  border-color: rgba(59, 130, 246, 0.2);
}

.filter-group--trend {
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  border-color: rgba(245, 158, 11, 0.22);
}

.filter-group--process {
  background: linear-gradient(180deg, #f5f3ff 0%, #ede9fe 100%);
  border-color: rgba(139, 92, 246, 0.2);
  flex: 1 1 180px;
  min-width: 168px;
  max-width: 280px;
}

.filter-group-tag {
  flex-shrink: 0;
  font-size: 0.6rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  padding: 3px 7px;
  border-radius: 5px;
  line-height: 1.2;
  white-space: nowrap;
  align-self: center;
}

.filter-group--period .filter-group-tag {
  background: rgba(37, 99, 235, 0.15);
  color: #1d4ed8;
}

.filter-group--trend .filter-group-tag {
  background: rgba(217, 119, 6, 0.15);
  color: #b45309;
}

.filter-group--process .filter-group-tag {
  background: rgba(124, 58, 237, 0.15);
  color: #6d28d9;
}

.filter-group-fields {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  min-width: 0;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.filter-label {
  font-size: 0.58rem;
  font-weight: 600;
  color: #64748b;
  line-height: 1;
  padding-left: 2px;
}

.filter-group--period .filter-label {
  color: #3b82f6;
}

.tf-control--month {
  width: 118px !important;
  max-width: 118px;
}

.tf-control--month:deep(.el-input__wrapper) {
  width: 100%;
}

.tf-control--trend {
  width: 76px !important;
}

.filter-field--process {
  flex: 1;
  min-width: 0;
}

.tf-control--process {
  width: 100% !important;
  min-width: 130px;
}

.tf-control :deep(.el-input__inner) {
  font-size: 0.72rem;
  font-weight: 600;
  color: #1e293b;
}

.tf-control :deep(.el-select__wrapper) {
  width: 100%;
}

.tf-control :deep(.el-select__selection),
.tf-control :deep(.el-select__selected-item),
.tf-control :deep(.el-select__placeholder) {
  font-size: 0.72rem;
  font-weight: 600;
  color: #1e293b;
}

.tf-control :deep(.el-select__placeholder) {
  color: #94a3b8;
  font-weight: 500;
}

.tf-control :deep(.el-input__wrapper),
.tf-control :deep(.el-select__wrapper) {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 6px;
  min-height: 28px;
  padding: 0 8px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 1px 2px rgba(15, 23, 42, 0.08),
    0 0 0 1px rgba(15, 23, 42, 0.06);
  transition: box-shadow 0.15s ease;
}

.tf-control :deep(.el-input__wrapper:hover),
.tf-control :deep(.el-select__wrapper:hover) {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 2px 6px rgba(15, 23, 42, 0.1),
    0 0 0 1px rgba(59, 130, 246, 0.25);
}

.tf-control :deep(.el-input__wrapper.is-focus),
.tf-control :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 0 0 2px rgba(59, 130, 246, 0.35);
}

.filter-group--trend .tf-control :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 0 0 2px rgba(245, 158, 11, 0.4);
}

.filter-group--process .tf-control :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 0 0 2px rgba(139, 92, 246, 0.35);
}

/* 操作ボタン帯 */
.toolbar-actions-zone {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  flex-shrink: 0;
  background: linear-gradient(180deg, rgba(241, 245, 249, 0.6) 0%, rgba(226, 232, 240, 0.4) 100%);
  border-left: 1px solid rgba(15, 23, 42, 0.06);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 30px;
  padding: 0 12px;
  border: none;
  border-radius: 7px;
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
  white-space: nowrap;
}

.action-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.action-btn--primary {
  color: #fff;
  background: linear-gradient(180deg, #4f8ef7 0%, #2563eb 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.25) inset,
    0 2px 0 #1d4ed8,
    0 4px 12px rgba(37, 99, 235, 0.35);
}

.action-btn--primary:hover:not(:disabled) {
  filter: brightness(1.05);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 2px 0 #1d4ed8,
    0 6px 16px rgba(37, 99, 235, 0.45);
}

.action-btn--primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.action-btn--ghost {
  color: #475569;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 1px 0 #cbd5e1,
    0 2px 6px rgba(15, 23, 42, 0.08);
}

.action-btn--ghost:hover {
  color: #1e293b;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 1px 0 #94a3b8,
    0 4px 10px rgba(15, 23, 42, 0.1);
}

.action-btn .is-loading {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── KPI ── */
.dash-section {
  position: relative;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--mes-gap);
}

.kpi-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 14px 12px;
  position: relative;
  overflow: hidden;
  min-height: 168px;
}

.kpi-card--elevated {
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.92) 100%);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.95);
  border-radius: 14px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 10px 28px rgba(15, 23, 42, 0.09),
    0 2px 6px rgba(15, 23, 42, 0.05);
  transition:
    transform 0.3s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.3s ease;
}

.kpi-card--elevated:hover {
  transform: translateY(-3px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.98) inset,
    0 16px 36px rgba(15, 23, 42, 0.12),
    0 4px 10px rgba(15, 23, 42, 0.06);
}

.kpi-card__glow {
  position: absolute;
  top: -40%;
  right: -20%;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  opacity: 0.35;
  filter: blur(28px);
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.kpi-card--elevated:hover .kpi-card__glow {
  opacity: 0.55;
}

.kpi-card--prod .kpi-card__glow {
  background: #fb923c;
}
.kpi-card--ratio .kpi-card__glow {
  background: #60a5fa;
}
.kpi-card--auto .kpi-card__glow {
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.kpi-card--prod::before {
  background: linear-gradient(180deg, #fdba74, #ea580c);
}
.kpi-card--ratio::before {
  background: linear-gradient(180deg, #93c5fd, #2563eb);
}
.kpi-card--auto::before {
  background: linear-gradient(180deg, #6ee7b7, #059669);
}

.kpi-card__head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  position: relative;
  z-index: 1;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.22);
}

.kpi-card__titles {
  flex: 1;
  min-width: 0;
}

.kpi-card__name {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.01em;
  line-height: 1.25;
}

.kpi-card__desc {
  margin: 2px 0 0;
  font-size: 0.62rem;
  font-weight: 600;
  color: #94a3b8;
  line-height: 1.35;
}

.kpi-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(59, 130, 246, 0.1);
  color: var(--mes-accent);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.8) inset,
    0 3px 8px rgba(15, 23, 42, 0.08);
}

.kpi-card--prod .kpi-icon {
  background: linear-gradient(145deg, rgba(254, 215, 170, 0.9), rgba(249, 115, 22, 0.15));
  color: #ea580c;
}
.kpi-card--ratio .kpi-icon {
  background: linear-gradient(145deg, rgba(191, 219, 254, 0.9), rgba(59, 130, 246, 0.15));
  color: #2563eb;
}
.kpi-card--auto .kpi-icon {
  background: linear-gradient(145deg, rgba(167, 243, 208, 0.9), rgba(16, 185, 129, 0.15));
  color: #059669;
}

.kpi-metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
  z-index: 1;
}

.kpi-metric {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 8px 10px;
  border-radius: 9px;
  background: rgba(248, 250, 252, 0.72);
  border: 1px solid rgba(226, 232, 240, 0.85);
}

.kpi-metric--qty {
  background: rgba(255, 255, 255, 0.55);
}

.kpi-card--prod .kpi-metric {
  background: rgba(255, 247, 237, 0.65);
  border-color: rgba(251, 146, 60, 0.18);
}
.kpi-card--prod .kpi-metric--qty {
  background: rgba(255, 255, 255, 0.5);
}

.kpi-card--auto .kpi-metric {
  background: rgba(236, 253, 245, 0.65);
  border-color: rgba(52, 211, 153, 0.2);
}
.kpi-card--auto .kpi-metric--qty {
  background: rgba(255, 255, 255, 0.5);
}

.kpi-card--ratio .kpi-metric {
  background: rgba(239, 246, 255, 0.7);
  border-color: rgba(96, 165, 250, 0.22);
}
.kpi-card--ratio .kpi-metric--qty {
  background: rgba(255, 255, 255, 0.5);
}

.kpi-metric__main {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.kpi-metric__label {
  font-size: 0.68rem;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.kpi-metric__value {
  font-size: var(--mes-fs-xl);
  font-weight: 800;
  color: #0f172a;
  line-height: 1.1;
  font-family: var(--mes-font-num);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
  text-align: right;
}

.kpi-metric__value--qty {
  font-size: var(--mes-fs-lg);
  color: #334155;
}

.kpi-card--prod .kpi-metric__value--qty {
  color: #9a3412;
}
.kpi-card--auto .kpi-metric__value--qty {
  color: #047857;
}
.kpi-card--ratio .kpi-metric__value--qty {
  color: #1d4ed8;
}

.kpi-metric__unit {
  font-size: 0.68rem;
  font-weight: 700;
  color: #94a3b8;
  margin-left: 2px;
}

.kpi-metric__foot {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.kpi-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 7px;
  border-radius: 6px;
  font-size: 0.65rem;
  font-weight: 700;
  background: rgba(15, 23, 42, 0.04);
}

.kpi-sub {
  font-size: 0.62rem;
  color: #94a3b8;
  font-weight: 600;
}

.delta-good {
  color: #15803d !important;
  background: rgba(22, 163, 74, 0.1) !important;
}
.delta-bad {
  color: #b91c1c !important;
  background: rgba(220, 38, 38, 0.1) !important;
}

.kpi-grid:not(.is-ready) .kpi-card--elevated {
  opacity: 0;
}

.kpi-grid.is-ready .kpi-card--elevated {
  animation: kpi-pop 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: calc(var(--delay, 0ms));
}

@keyframes kpi-pop {
  0% {
    opacity: 0;
    transform: translateY(14px) scale(0.96);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ── VS 比較パネル ── */
.vs-panel {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: stretch;
  gap: 0;
  padding: 0;
  overflow: hidden;
}

.vs-panel--elevated {
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.95) 0%, rgba(255, 255, 255, 0.9) 100%);
  border: 1px solid rgba(147, 197, 253, 0.35);
  border-radius: 12px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 8px 24px rgba(37, 99, 235, 0.1),
    0 2px 6px rgba(15, 23, 42, 0.05);
}

.vs-side {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.vs-side--current {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, transparent 100%);
}

.vs-side--compare {
  background: linear-gradient(225deg, rgba(148, 163, 184, 0.1) 0%, transparent 100%);
}

.vs-side-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.vs-badge {
  font-size: 0.6rem;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 5px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.vs-badge--current {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
}

.vs-badge--compare {
  background: rgba(148, 163, 184, 0.25);
  color: #475569;
}

.vs-month {
  font-size: 0.95rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.02em;
}

.vs-metric-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.vs-metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 2px 6px rgba(15, 23, 42, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.vs-metric:hover {
  transform: translateY(-2px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 6px 14px rgba(15, 23, 42, 0.08);
}

.vs-metric--prod .vs-metric-value {
  color: #ea580c;
}
.vs-metric--auto .vs-metric-value {
  color: #059669;
}
.vs-metric--ratio .vs-metric-value {
  color: #2563eb;
}

.vs-metric-label {
  font-size: 0.62rem;
  font-weight: 600;
  color: #64748b;
}

.vs-metric-value {
  font-size: var(--mes-fs-lg);
  font-weight: 800;
  color: #1e293b;
  font-family: var(--mes-font-num);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.vs-metric-value small {
  font-size: 0.62rem;
  font-weight: 600;
  color: #94a3b8;
  margin-left: 1px;
}

.vs-section-divider {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 2px 0 4px;
  padding-top: 8px;
  border-top: 1px dashed rgba(148, 163, 184, 0.45);
}

.vs-section-divider span {
  font-size: 0.62rem;
  font-weight: 800;
  color: #7c3aed;
  letter-spacing: 0.04em;
}

.vs-section-divider small {
  font-size: 0.58rem;
  font-weight: 600;
  color: #94a3b8;
}

.vs-section-divider--ghost {
  visibility: hidden;
  pointer-events: none;
}

.vs-center {
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: center;
  position: relative;
  width: 52px;
  flex-shrink: 0;
}

.vs-pulse {
  position: absolute;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.15);
  animation: vs-pulse 2s ease-in-out infinite;
}

@keyframes vs-pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.25);
    opacity: 0.2;
  }
}

.vs-center-text {
  position: relative;
  z-index: 1;
  font-size: 0.7rem;
  font-weight: 900;
  color: #3b82f6;
  background: #fff;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 2px 0 #93c5fd,
    0 4px 12px rgba(59, 130, 246, 0.3);
}

/* ── パネル・チャート ── */
.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--mes-gap);
}

.panel {
  min-width: 0;
}

.panel.glass {
  padding: 10px 12px 8px;
}

.panel--chart {
  padding: 12px 14px 10px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 250, 252, 0.9) 100%);
  border: 1px solid rgba(255, 255, 255, 0.95);
  border-radius: var(--mes-radius);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 8px 22px rgba(15, 23, 42, 0.07),
    0 2px 5px rgba(15, 23, 42, 0.04);
  transition:
    transform 0.3s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.3s ease;
}

.panel--chart:hover {
  transform: translateY(-2px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.98) inset,
    0 14px 32px rgba(15, 23, 42, 0.1),
    0 4px 8px rgba(15, 23, 42, 0.05);
}

.panel--wide {
  grid-column: 1 / -1;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 0 2px;
  flex-wrap: wrap;
}

.panel-head--table {
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 10px;
}

.panel-head--chart-export {
  width: 100%;
}

.panel-head--chart-export .panel-export-btn {
  margin-left: auto;
}

.panel-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: wrap;
}

.panel-accent {
  width: 4px;
  height: 18px;
  border-radius: 4px;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.panel-accent--blue {
  background: linear-gradient(180deg, #60a5fa, #2563eb);
}
.panel-accent--purple {
  background: linear-gradient(180deg, #c4b5fd, #7c3aed);
}
.panel-accent--teal {
  background: linear-gradient(180deg, #5eead4, #0d9488);
}
.panel-accent--orange {
  background: linear-gradient(180deg, #fdba74, #ea580c);
}
.panel-accent--green {
  background: linear-gradient(180deg, #6ee7b7, #059669);
}

.panel-title {
  flex: 0 1 auto;
  font-size: var(--mes-fs-md);
  font-weight: 800;
  color: #1e293b;
  letter-spacing: 0.03em;
}

.panel-meta,
.panel-hint {
  font-size: var(--mes-fs-xs);
  font-weight: 600;
  color: #64748b;
  padding: 3px 9px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.045);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.chart-canvas-wrap {
  position: relative;
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.75) 0%, rgba(255, 255, 255, 0.55) 100%);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: inset 0 1px 3px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

.chart-canvas-wrap::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.28) 0%, transparent 42%);
  border-radius: inherit;
}

.chart-canvas {
  height: clamp(200px, 28vh, 280px);
  width: 100%;
}

.chart-canvas-wrap--tall .chart-canvas,
.chart-canvas--tall {
  height: clamp(240px, 34vh, 340px);
}

/* ── テーブル ── */
.table-wrap {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--mes-border);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.table-wrap--fluid {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
}

.table-wrap--fluid::-webkit-scrollbar {
  height: 8px;
}
.table-wrap--fluid::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.35);
  border-radius: 999px;
}

.data-table--fluid {
  width: 100%;
  font-family: var(--mes-font);
}

.data-table--fluid :deep(.el-table__header th) {
  padding: 8px 0;
}

.data-table--fluid :deep(.el-table__header th .cell) {
  white-space: nowrap;
  word-break: keep-all;
  line-height: 1.3;
  padding: 0 8px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.data-table--fluid :deep(.el-table__body td .cell) {
  white-space: nowrap;
  padding: 0 8px;
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum' 1;
}

.data-table--fluid:not(.data-table--clickable) :deep(.el-table__row) {
  cursor: default;
}

.data-table--fluid:not(.data-table--clickable) :deep(.el-table__row:hover > td) {
  background: rgba(241, 245, 249, 0.65) !important;
}

/* ── 工程別比較テーブル ── */
.data-table--process-compare :deep(.el-table__border-left-patch),
.data-table--process-compare :deep(.el-table__border-right-patch) {
  background: #f8fafc;
}

.data-table--process-compare :deep(th.cmp-th--process) {
  background: linear-gradient(180deg, #f1f5f9, #e2e8f0) !important;
  font-weight: 800;
  color: #334155;
}

.data-table--process-compare :deep(th.cmp-th--current.cmp-th--prod) {
  background: linear-gradient(180deg, #fff7ed, #ffedd5) !important;
  border-bottom: 2px solid #fb923c !important;
}

.data-table--process-compare :deep(th.cmp-th--compare.cmp-th--prod) {
  background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
  border-bottom: 2px solid #94a3b8 !important;
}

.data-table--process-compare :deep(th.cmp-th--current.cmp-th--auto) {
  background: linear-gradient(180deg, #ecfdf5, #d1fae5) !important;
  border-bottom: 2px solid #34d399 !important;
}

.data-table--process-compare :deep(th.cmp-th--compare.cmp-th--auto) {
  background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
  border-bottom: 2px solid #94a3b8 !important;
}

.data-table--process-compare :deep(th.cmp-th--delta) {
  background: linear-gradient(180deg, #eef2ff, #e0e7ff) !important;
  border-bottom: 2px solid #818cf8 !important;
  color: #4338ca;
  font-weight: 800;
}

.data-table--process-compare :deep(th.cmp-th-sub--current.cmp-th-sub--prod) {
  background: rgba(255, 237, 213, 0.65) !important;
  color: #c2410c;
}

.data-table--process-compare :deep(th.cmp-th-sub--compare.cmp-th-sub--prod) {
  background: rgba(241, 245, 249, 0.95) !important;
  color: #64748b;
}

.data-table--process-compare :deep(th.cmp-th-sub--current.cmp-th-sub--auto) {
  background: rgba(209, 250, 229, 0.65) !important;
  color: #047857;
}

.data-table--process-compare :deep(th.cmp-th-sub--compare.cmp-th-sub--auto) {
  background: rgba(241, 245, 249, 0.95) !important;
  color: #64748b;
}

.data-table--process-compare :deep(th.cmp-th-sub--delta) {
  background: rgba(224, 231, 255, 0.55) !important;
  color: #4f46e5;
}

.data-table--process-compare :deep(td.cmp-td--process) {
  background: rgba(248, 250, 252, 0.7) !important;
  font-weight: 600;
  color: #1e293b;
}

.data-table--process-compare :deep(td.cmp-td--current.cmp-td--prod) {
  background: rgba(255, 247, 237, 0.35) !important;
}

.data-table--process-compare :deep(td.cmp-td--compare.cmp-td--prod) {
  background: rgba(248, 250, 252, 0.55) !important;
  color: #475569;
}

.data-table--process-compare :deep(td.cmp-td--current.cmp-td--auto) {
  background: rgba(236, 253, 245, 0.4) !important;
}

.data-table--process-compare :deep(td.cmp-td--compare.cmp-td--auto) {
  background: rgba(248, 250, 252, 0.55) !important;
  color: #475569;
}

.data-table--process-compare :deep(td.cmp-td--delta) {
  background: rgba(238, 242, 255, 0.35) !important;
}

.data-table--process-compare :deep(.el-table__row:hover > td.cmp-td--process) {
  background: rgba(226, 232, 240, 0.85) !important;
}

.data-table--process-compare :deep(.el-table__row:hover > td.cmp-td--current) {
  background: rgba(254, 215, 170, 0.45) !important;
}

.data-table--process-compare :deep(.el-table__row:hover > td.cmp-td--compare) {
  background: rgba(226, 232, 240, 0.65) !important;
}

.data-table--process-compare :deep(.el-table__row:hover > td.cmp-td--delta) {
  background: rgba(199, 210, 254, 0.45) !important;
}

.cmp-col-head {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 2px 4px;
  line-height: 1.2;
}

.cmp-col-type {
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.cmp-col-type--prod {
  color: #ea580c;
}

.cmp-col-type--auto {
  color: #059669;
}

.cmp-month-tag {
  display: inline-block;
  font-size: 0.6rem;
  font-weight: 800;
  padding: 2px 9px;
  border-radius: 10px;
  letter-spacing: 0.03em;
  line-height: 1.3;
}

.cmp-month-tag--current {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.35);
}

.cmp-month-tag--compare {
  background: linear-gradient(135deg, #94a3b8, #64748b);
  color: #fff;
  box-shadow: 0 1px 3px rgba(100, 116, 139, 0.3);
}

.cmp-delta {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 6px;
  font-size: var(--mes-fs-xs);
  font-weight: 700;
  font-family: var(--mes-font-num);
  font-variant-numeric: tabular-nums;
}

.cmp-delta.delta-good {
  background: rgba(22, 163, 74, 0.12);
  color: #15803d !important;
}

.cmp-delta.delta-bad {
  background: rgba(220, 38, 38, 0.1);
  color: #b91c1c !important;
}

.data-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
  font-size: var(--mes-fs-xs);
  padding: 6px 0;
  color: #334155;
  border-bottom-color: rgba(148, 163, 184, 0.35) !important;
}

.data-table :deep(.el-table__body td) {
  font-size: var(--mes-fs-sm);
  padding: 5px 0;
  color: #1e293b;
}

.data-table :deep(.el-table__row) {
  cursor: pointer;
  transition: background 0.15s ease;
}

.data-table :deep(.el-table__row:hover > td) {
  background: rgba(59, 130, 246, 0.07) !important;
}

.data-table :deep(.el-table__body tr.el-table__row--striped td) {
  background: rgba(248, 250, 252, 0.7);
}

.ratio-pill {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: var(--mes-fs-xs);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.01em;
}

.ratio-pill--low {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
}
.ratio-pill--mid {
  background: rgba(245, 158, 11, 0.15);
  color: #d97706;
}
.ratio-pill--high {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

/* ── レスポンシブ ── */
@media (max-width: 1400px) {
  .mes-inner {
    max-width: 100%;
  }
}

@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
  }

  .chart-grid {
    grid-template-columns: 1fr;
  }

  .panel--wide {
    grid-column: auto;
  }

  .filter-group--process {
    max-width: none;
    flex: 1 1 220px;
  }
}

@media (max-width: 980px) {
  .toolbar {
    flex-direction: column;
  }

  .toolbar-brand-zone {
    border-right: none;
    border-bottom: 1px solid rgba(59, 130, 246, 0.12);
    width: 100%;
    min-width: 0;
  }

  .toolbar-brand-zone::after {
    display: none;
  }

  .toolbar-filters-zone {
    width: 100%;
  }

  .toolbar-actions-zone {
    width: 100%;
    justify-content: flex-end;
    border-left: none;
    border-top: 1px solid rgba(15, 23, 42, 0.06);
  }

  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .kpi-grid .kpi-card:last-child {
    grid-column: 1 / -1;
  }

  .vs-metric-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .mes-page {
    padding: 6px 8px 12px;
  }

  .toolbar-filters-zone {
    flex-direction: column;
  }

  .filter-group {
    width: 100%;
  }

  .filter-group--process {
    max-width: none;
  }

  .filter-group-fields {
    flex: 1;
    flex-wrap: wrap;
  }

  .tf-control--month {
    width: min(132px, 42vw) !important;
    max-width: none;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .kpi-grid .kpi-card:last-child {
    grid-column: auto;
  }

  .kpi-card {
    min-height: 0;
  }

  .vs-panel {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
  }

  .vs-center {
    width: 100%;
    height: 40px;
    order: 2;
  }

  .vs-side--compare {
    order: 3;
  }

  .vs-section-divider--ghost {
    display: none;
  }

  .vs-metric-grid {
    grid-template-columns: 1fr;
  }

  .chart-canvas {
    height: clamp(180px, 32vh, 240px);
  }

  .chart-canvas-wrap--tall .chart-canvas,
  .chart-canvas--tall {
    height: clamp(200px, 38vh, 280px);
  }

  .panel-head--table {
    flex-direction: column;
    align-items: stretch;
  }

  .panel-head--table .el-button {
    align-self: flex-end;
  }

  .cmp-col-head {
    gap: 3px;
  }
}

@media (max-width: 480px) {
  .toolbar-actions-zone {
    flex-wrap: wrap;
    justify-content: stretch;
  }

  .action-btn {
    flex: 1 1 auto;
    min-width: 96px;
  }

  .kpi-metric__main {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .kpi-metric__value,
  .kpi-metric__value--qty {
    text-align: left;
  }

  .vs-month {
    font-size: var(--mes-fs-md);
  }
}

@media (prefers-reduced-motion: reduce) {
  .animate-in,
  .orb,
  .kpi-grid.is-ready .kpi-card--elevated,
  .vs-pulse {
    animation: none;
    opacity: 1;
    transform: none;
  }

  .kpi-card--elevated:hover,
  .panel--chart:hover,
  .vs-metric:hover {
    transform: none;
  }
}
</style>

<style>
/* ツールバー select ドロップダウン（teleport 先） */
.mes-select-popper.el-popper {
  z-index: 4000 !important;
}

.mes-select-popper .el-select-dropdown__item {
  font-size: 12px;
  color: #1e293b;
  padding: 0 12px;
  line-height: 32px;
}

.mes-select-popper .el-select-dropdown__item.is-selected {
  color: #2563eb;
  font-weight: 600;
}

.mes-select-popper .el-select-dropdown__item.is-hovering {
  background: rgba(59, 130, 246, 0.08);
}
</style>
