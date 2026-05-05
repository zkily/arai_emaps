<template>
  <div class="scrap-page">
    <header class="scrap-hero">
      <div class="scrap-hero__left">
        <div class="scrap-hero__icon" :style="{ background: gradient }">
          <el-icon :size="22"><component :is="iconHero" /></el-icon>
        </div>
        <div class="scrap-hero__text">
          <h1 class="scrap-hero__title">廃棄率分析</h1>
          <p class="scrap-hero__meta">工程別／製品別</p>
        </div>
      </div>
    </header>

    <el-card class="scrap-card" shadow="never">
      <div class="scrap-toolbar">
        <div class="scrap-field">
          <el-icon class="scrap-field__ico" title="集計期間"><Calendar /></el-icon>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="～"
            start-placeholder="開始"
            end-placeholder="終了"
            value-format="YYYY-MM-DD"
            size="default"
            class="scrap-toolbar__date"
          />
        </div>
        <div class="scrap-field">
          <el-icon class="scrap-field__ico" title="工程フィルタ"><Operation /></el-icon>
          <el-select v-model="process" placeholder="工程" size="default" class="scrap-toolbar__proc" clearable>
            <el-option label="全工程" value="" />
            <el-option v-for="item in processOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div class="scrap-field scrap-field--grow">
          <el-icon class="scrap-field__ico" title="製品"><Goods /></el-icon>
          <el-select
            v-model="filterProductCd"
            placeholder="製品"
            size="default"
            class="scrap-toolbar__product"
            clearable
            filterable
          >
            <el-option label="（すべて）" value="" />
            <el-option
              v-for="p in productOptions"
              :key="p.product_cd"
              :label="productOptionLabel(p)"
              :value="p.product_cd"
            />
          </el-select>
        </div>
      </div>

      <div class="scrap-kpi">
        <div class="scrap-kpi__item">
          <el-icon class="scrap-kpi__water scrap-kpi__water--rose"><TrendCharts /></el-icon>
          <div class="scrap-kpi__label">{{ summaryCardTitle }}</div>
          <div class="scrap-kpi__value">{{ fmtPct(summary.rate_percent) }}</div>
          <div class="scrap-kpi__hint">{{ summaryCardSub }}</div>
        </div>
        <div v-if="summary.basis === 'rolled_main_line'" class="scrap-kpi__item">
          <el-icon class="scrap-kpi__water scrap-kpi__water--emerald"><CircleCheck /></el-icon>
          <div class="scrap-kpi__label">連乘合格率 RTY</div>
          <div class="scrap-kpi__value">{{ fmtPct(summary.rolled_yield_percent) }}</div>
          <div class="scrap-kpi__hint">{{ summaryCardSecondSubRolled }}</div>
        </div>
        <div v-else class="scrap-kpi__item">
          <el-icon class="scrap-kpi__water scrap-kpi__water--amber"><WarningFilled /></el-icon>
          <div class="scrap-kpi__label">不良＋廃棄（選択工程）</div>
          <div class="scrap-kpi__value">{{ fmtInt(summary.sum_defect_and_scrap) }}</div>
          <div class="scrap-kpi__hint">{{ summaryBadSub }}</div>
        </div>
        <div class="scrap-kpi__item scrap-kpi__item--accent">
          <el-icon class="scrap-kpi__water scrap-kpi__water--gold"><PieChart /></el-icon>
          <div class="scrap-kpi__label">不良＋廃棄（全工程合計）</div>
          <div class="scrap-kpi__value">{{ fmtInt(allProcessesDefectScrapTotal) }}</div>
          <div class="scrap-kpi__hint">全工程キー合計 · フィルタ無関係</div>
        </div>
      </div>

      <section class="scrap-block scrap-charts">
        <div class="scrap-block__head scrap-block__head--charts">
          <div class="scrap-block__head-main">
            <el-icon class="scrap-block__ico scrap-block__ico--chart"><TrendCharts /></el-icon>
            <span class="scrap-block__title">可視化</span>
          </div>
          <span class="scrap-charts__note">工程＝一覧と連動 · 製品チャート＝条件内全件（廃棄率高順・上位表示）</span>
        </div>
        <div class="scrap-charts__grid">
          <div class="scrap-chart-card">
            <div class="scrap-chart-card__title">工程別 比率（不良＋廃棄÷実績）</div>
            <div ref="processRateChartRef" class="scrap-chart-host" />
          </div>
          <div class="scrap-chart-card">
            <div class="scrap-chart-card__title">工程別 不良・廃棄（数量）</div>
            <div ref="processVolumeChartRef" class="scrap-chart-host" />
          </div>
          <div v-loading="productChartLoading" class="scrap-chart-card scrap-chart-card--span2">
            <div class="scrap-chart-card__title">製品別 不良＋廃棄（本）と 廃棄率（1−RTY）（％）</div>
            <div class="scrap-chart-card__sub">{{ productChartSubLine }}</div>
            <div ref="productComboChartRef" class="scrap-chart-host scrap-chart-host--wide" />
          </div>
        </div>
      </section>

      <section class="scrap-block">
        <div class="scrap-block__head">
          <el-icon class="scrap-block__ico scrap-block__ico--indigo"><Histogram /></el-icon>
          <span class="scrap-block__title">工程別集計</span>
        </div>
        <div class="scrap-table-shell scrap-table-shell--process">
          <el-table v-loading="loading" :data="rows" size="small" border stripe class="scrap-table scrap-table--process">
            <el-table-column
              prop="label"
              label="工程"
              width="140"
              fixed
              class-name="scrap-td--proc"
              label-class-name="scrap-th--proc"
            />
            <el-table-column
              prop="sum_actual"
              label="実績（合計）"
              width="120"
              align="right"
              class-name="scrap-td--num scrap-td--actual"
              label-class-name="scrap-th--num scrap-th--actual"
            >
              <template #default="{ row }">{{ fmtInt(row.sum_actual) }}</template>
            </el-table-column>
            <el-table-column
              prop="sum_defect"
              label="不良（合計）"
              width="120"
              align="right"
              class-name="scrap-td--num scrap-td--defect"
              label-class-name="scrap-th--num scrap-th--defect"
            >
              <template #default="{ row }">{{ fmtInt(row.sum_defect) }}</template>
            </el-table-column>
            <el-table-column
              prop="sum_scrap"
              label="廃棄（合計）"
              width="120"
              align="right"
              class-name="scrap-td--num scrap-td--scrap"
              label-class-name="scrap-th--num scrap-th--scrap"
            >
              <template #default="{ row }">{{ fmtInt(row.sum_scrap) }}</template>
            </el-table-column>
            <el-table-column
              prop="sum_defect_and_scrap"
              label="不良＋廃棄"
              width="120"
              align="right"
              class-name="scrap-td--num scrap-td--sum"
              label-class-name="scrap-th--num scrap-th--sum"
            >
              <template #default="{ row }">{{ fmtInt(row.sum_defect_and_scrap) }}</template>
            </el-table-column>
            <el-table-column
              label="廃棄率（％）"
              min-width="120"
              align="right"
              class-name="scrap-td--num scrap-td--rate"
              label-class-name="scrap-th--num scrap-th--rate"
            >
              <template #default="{ row }">
                {{ row.rate_percent != null ? row.rate_percent.toFixed(2) + ' %' : '—' }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>

      <section class="scrap-block">
        <div class="scrap-block__head scrap-block__head--with-actions">
          <div class="scrap-block__head-main">
            <el-icon class="scrap-block__ico scrap-block__ico--teal"><Grid /></el-icon>
            <span class="scrap-block__title">製品別集計</span>
          </div>
          <el-button type="primary" plain size="small" :loading="printProductLoading" @click="printProductTable">
            <el-icon class="scrap-print-btn-ico"><Printer /></el-icon>
            印刷
          </el-button>
        </div>
        <div class="scrap-table-shell scrap-table-shell--wide scrap-table-shell--product">
          <el-table
            v-loading="loading"
            :data="productRows"
            size="small"
            border
            stripe
            class="scrap-table scrap-table--product"
            :default-sort="{ prop: 'product_name', order: 'ascending' }"
            @sort-change="onProductSortChange"
          >
            <el-table-column
              prop="product_cd"
              label="製品CD"
              width="90"
              fixed
              class-name="scrap-td--sku"
              label-class-name="scrap-th--sku"
            />
            <el-table-column
              prop="product_name"
              label="製品名"
              min-width="130"
              show-overflow-tooltip
              fixed
              sortable="custom"
              class-name="scrap-td--name"
              label-class-name="scrap-th--name"
            />
            <el-table-column
              prop="all_processes_defect_scrap"
              label="不良＋廃棄"
              width="120"
              align="right"
              sortable="custom"
              class-name="scrap-td--num scrap-td--allbad"
              label-class-name="scrap-th--num scrap-th--allbad"
            >
              <template #default="{ row }">{{ fmtInt(row.all_processes_defect_scrap) }}</template>
            </el-table-column>
            <el-table-column
              v-for="col in mainLineLabels"
              :key="col.key"
              :prop="col.key"
              :label="col.label + '（％）'"
              width="130"
              align="right"
              sortable="custom"
              class-name="scrap-td--num scrap-td--pline"
              label-class-name="scrap-th--num scrap-th--pline"
            >
              <template #default="{ row }">
                {{ formatProcCell(row, col.key) }}
              </template>
            </el-table-column>
            <el-table-column
              prop="rty_loss"
              label="廃棄率"
              width="100"
              align="right"
              fixed="right"
              sortable="custom"
              class-name="scrap-td--num scrap-td--rty-loss"
              label-class-name="scrap-th--num scrap-th--rty-loss"
            >
              <template #default="{ row }">{{ formatProductRtyLoss(row) }}</template>
            </el-table-column>
            <el-table-column
              prop="rty"
              label="合格率"
              width="100"
              align="right"
              fixed="right"
              sortable="custom"
              class-name="scrap-td--num scrap-td--rty-yield"
              label-class-name="scrap-th--num scrap-th--rty-yield"
            >
              <template #default="{ row }">{{ formatProductRty(row) }}</template>
            </el-table-column>
          </el-table>
        </div>
        <el-pagination
          class="scrap-pager"
          layout="total, prev, pager, next"
          :total="productTotal"
          :page-size="productLimit"
          :current-page="productPage"
          small
          @current-change="onProductPageChange"
        />
      </section>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import {
  Calendar,
  CircleCheck,
  DataAnalysis,
  Goods,
  Grid,
  Histogram,
  Operation,
  PieChart,
  Printer,
  TrendCharts,
  WarningFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  getProductionSummarysProducts,
  getQualityRateByProcess,
  getQualityRateByProduct,
} from '@/api/database'

const iconHero = markRaw(DataAnalysis)
const gradient = 'linear-gradient(135deg, #f56c6c, #ff7875)'
const loading = ref(false)

const today = new Date()
const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)
const formatDate = (date: Date) => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const dateRange = ref<[string, string]>([formatDate(firstDay), formatDate(today)])
const process = ref('')
/** 製品別表のみ絞込（完全一致）。空＝全製品 */
const filterProductCd = ref('')
const productOptions = ref<Array<{ product_cd: string; product_name?: string | null }>>([])
const productPage = ref(1)
const productLimit = ref(50)
const productTotal = ref(0)
/** 製品別表：サーバー側ソート（既定＝品名昇順） */
const productSortProp = ref<string>('product_name')
const productSortOrder = ref<'asc' | 'desc'>('asc')
const printProductLoading = ref(false)

const DEFAULT_MAIN_LINE: Array<{ key: string; label: string }> = [
  { key: 'cutting', label: '切断' },
  { key: 'chamfering', label: '面取' },
  { key: 'molding', label: '成型' },
  { key: 'plating', label: 'メッキ' },
  { key: 'welding', label: '溶接' },
  { key: 'inspection', label: '検査' },
]
/** 製品別 RTY の積順序（後端と同一） */
const MAIN_LINE_KEYS_ORDER = DEFAULT_MAIN_LINE.map((c) => c.key)
const mainLineLabels = ref(DEFAULT_MAIN_LINE)

type ProductMatrixRow = {
  product_cd: string
  product_name: string
  all_processes_defect_scrap: number
  processes: Array<{
    key: string
    label: string
    sum_actual: number
    sum_defect: number
    sum_scrap: number
    sum_defect_and_scrap: number
    rate: number | null
    rate_percent: number | null
  }>
}

const productRows = ref<ProductMatrixRow[]>([])
/** 製品チャート用：期間・製品絞込下の全ページを rty_loss 降順で取得した一覧（表示は上位のみ切詰） */
const productChartRows = ref<ProductMatrixRow[]>([])
const productChartLoading = ref(false)
const productChartTotal = ref(0)
const CHART_PRODUCT_DISPLAY_CAP = 80
/** 印刷・製品チャート全件取得のページサイズ（API 上限 500） */
const PRINT_FETCH_LIMIT = 500
const PRINT_MAX_PAGES = 40

const productChartSubLine = computed(() => {
  const n = productChartRows.value.length
  const t = productChartTotal.value
  if (productChartLoading.value && !n) return '全件を読込中…'
  if (!n) return '該当データなし'
  if (t > n) return `全 ${t.toLocaleString('ja-JP')} 件中 廃棄率高い順で上位 ${n.toLocaleString('ja-JP')} 件を表示`
  return `全 ${t.toLocaleString('ja-JP')} 件 · 廃棄率（1−RTY）降順`
})

const processOptions = [
  { label: '切断', value: 'cutting' },
  { label: '面取', value: 'chamfering' },
  { label: '成型', value: 'molding' },
  { label: 'メッキ', value: 'plating' },
  { label: '溶接', value: 'welding' },
  { label: '検査', value: 'inspection' },
  { label: '倉庫', value: 'warehouse' },
  { label: '外注倉庫', value: 'outsourced_warehouse' },
  { label: '外注メッキ', value: 'outsourced_plating' },
  { label: '外注溶接', value: 'outsourced_welding' },
  { label: '溶接前検査', value: 'pre_welding_inspection' },
  { label: '外注支給前', value: 'pre_inspection' },
  { label: '外注検査前', value: 'pre_outsourcing' },
]

const rows = ref<
  Array<{
    key: string
    label: string
    sum_actual: number
    sum_defect: number
    sum_scrap: number
    sum_defect_and_scrap: number
    rate: number | null
    rate_percent: number | null
  }>
>([])

type Summary = {
  basis: 'rolled_main_line' | 'selected_process'
  reference_process_key: string
  reference_process_label: string
  sum_actual: number
  sum_defect: number
  sum_scrap: number
  sum_defect_and_scrap: number
  rate: number | null
  rate_percent: number | null
  rolled_yield_rate: number | null
  rolled_yield_percent: number | null
}

const emptySummary = (): Summary => ({
  basis: 'rolled_main_line',
  reference_process_key: 'main_line_rolled',
  reference_process_label: '主ライン連乘',
  sum_actual: 0,
  sum_defect: 0,
  sum_scrap: 0,
  sum_defect_and_scrap: 0,
  rate: null,
  rate_percent: null,
  rolled_yield_rate: null,
  rolled_yield_percent: null,
})

const summary = ref<Summary>(emptySummary())

/** API「全工程」の不良＋廃棄合計（カード3）。工程フィルタとは独立 */
const allProcessesDefectScrapTotal = ref(0)

const summaryCardTitle = computed(() => {
  if (summary.value.basis === 'rolled_main_line') {
    return '連乘廃棄率 1−RTY'
  }
  return `選択工程比率`
})

const summaryCardSub = computed(() => {
  if (summary.value.basis === 'rolled_main_line') {
    return '主ライン・プール集計 · 実績0の工程は除外'
  }
  return `${summary.value.reference_process_label} · （不良＋廃棄）÷ 実績`
})

const summaryCardSecondSubRolled = computed(() => {
  return 'RTY＝Π(1−r)'
})

const summaryBadSub = computed(() => {
  return '期間内合計'
})

function fmtInt(n: number | null | undefined) {
  if (n == null || Number.isNaN(n)) return '—'
  return n.toLocaleString('ja-JP')
}

function fmtPct(p: number | null | undefined) {
  if (p == null || Number.isNaN(p)) return '—'
  return `${p.toFixed(2)} %`
}

function formatProcCell(row: ProductMatrixRow, key: string) {
  const p = row.processes?.find((x) => x.key === key)
  if (!p || p.rate_percent == null) return '—'
  return `${p.rate_percent.toFixed(2)} %`
}

/** 品番単位：主ラインで実績>0 の工程のみ Π(1−r_i)、RTY を％で返す */
function computeProductMainLineRty(row: ProductMatrixRow): { rty: number; loss: number } | null {
  let prod = 1
  let used = false
  for (const key of MAIN_LINE_KEYS_ORDER) {
    const p = row.processes?.find((x) => x.key === key)
    if (!p) continue
    const sa = p.sum_actual ?? 0
    if (sa <= 0) continue
    const bad = p.sum_defect_and_scrap ?? 0
    let r = bad / sa
    if (r > 1) r = 1
    if (r < 0) r = 0
    prod *= 1 - r
    used = true
  }
  if (!used) return null
  return {
    rty: prod * 100,
    loss: (1 - prod) * 100,
  }
}

function formatProductRty(row: ProductMatrixRow) {
  const x = computeProductMainLineRty(row)
  if (!x) return '—'
  return `${x.rty.toFixed(2)} %`
}

function formatProductRtyLoss(row: ProductMatrixRow) {
  const x = computeProductMainLineRty(row)
  if (!x) return '—'
  return `${x.loss.toFixed(2)} %`
}

const processRateChartRef = ref<HTMLDivElement | null>(null)
const processVolumeChartRef = ref<HTMLDivElement | null>(null)
const productComboChartRef = ref<HTMLDivElement | null>(null)
let chartProcessRate: ECharts | null = null
let chartProcessVolume: ECharts | null = null
let chartProductCombo: ECharts | null = null
let resizeTimer: ReturnType<typeof setTimeout> | null = null

function disposeScrapCharts() {
  chartProcessRate?.dispose()
  chartProcessVolume?.dispose()
  chartProductCombo?.dispose()
  chartProcessRate = null
  chartProcessVolume = null
  chartProductCombo = null
}

function buildProcessRateChartOption(): EChartsOption {
  const list = rows.value
  if (!list.length) {
    return {
      title: { text: 'データなし', left: 'center', top: 'middle', textStyle: { color: '#94a3b8', fontSize: 14 } },
    }
  }
  const labels = list.map((r) => r.label)
  const values = list.map((r) => (r.rate_percent != null ? Number(r.rate_percent.toFixed(2)) : null))
  const hasAny = values.some((v) => v != null)
  return {
    grid: { left: 8, right: 36, top: 10, bottom: 8, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: unknown) => {
        const arr = Array.isArray(params) ? params : [params]
        const p = arr[0] as { name?: string; dataIndex?: number }
        const i = p.dataIndex ?? 0
        const v = list[i]?.rate_percent
        return `${p.name ?? ''}<br/>比率: ${v != null ? `${v.toFixed(2)} %` : '—'}`
      },
    },
    xAxis: {
      type: 'value',
      name: '%',
      min: 0,
      splitLine: { lineStyle: { type: 'dashed', color: '#e2e8f0' } },
      axisLabel: { color: '#64748b', fontSize: 10 },
    },
    yAxis: {
      type: 'category',
      data: labels,
      inverse: true,
      axisLabel: { color: '#475569', fontSize: 10 },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
    },
    series: [
      {
        type: 'bar',
        name: '比率',
        data: values.map((v, idx) => ({
          value: v ?? 0,
          itemStyle: {
            color:
              v == null
                ? '#e2e8f0'
                : new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: '#fda4af' },
                    { offset: 1, color: '#f43f5e' },
                  ]),
            borderRadius: [0, 4, 4, 0],
          },
        })),
        barMaxWidth: 22,
        label: {
          show: hasAny,
          position: 'right',
          fontSize: 10,
          color: '#64748b',
          formatter: (p: { dataIndex?: number }) => {
            const i = p.dataIndex ?? 0
            const v = list[i]?.rate_percent
            return v != null ? `${Number(v.toFixed(2))}%` : '—'
          },
        },
      },
    ],
  }
}

function buildProcessVolumeChartOption(): EChartsOption {
  const list = rows.value
  if (!list.length) {
    return {
      title: { text: 'データなし', left: 'center', top: 'middle', textStyle: { color: '#94a3b8', fontSize: 14 } },
    }
  }
  return {
    legend: { top: 0, textStyle: { fontSize: 11, color: '#64748b' } },
    grid: { left: 8, right: 12, top: 28, bottom: 4, containLabel: true },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: list.map((r) => r.label),
      axisLabel: { rotate: list.length > 8 ? 32 : 0, fontSize: 10, color: '#475569' },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#e2e8f0' } },
      axisLabel: { fontSize: 10, color: '#64748b' },
    },
    series: [
      {
        name: '不良',
        type: 'bar',
        stack: 'bad',
        data: list.map((r) => r.sum_defect ?? 0),
        itemStyle: { color: '#fb923c' },
        barMaxWidth: 28,
      },
      {
        name: '廃棄',
        type: 'bar',
        stack: 'bad',
        data: list.map((r) => r.sum_scrap ?? 0),
        itemStyle: { color: '#f43f5e' },
        barMaxWidth: 28,
      },
    ],
  }
}

function buildProductComboChartOption(): EChartsOption {
  if (productChartLoading.value && !productChartRows.value.length) {
    return {
      title: {
        text: '全件読込中…',
        left: 'center',
        top: 'middle',
        textStyle: { color: '#94a3b8', fontSize: 14 },
      },
    }
  }
  const list = productChartRows.value
  if (!list.length) {
    return {
      title: { text: 'データなし', left: 'center', top: 'middle', textStyle: { color: '#94a3b8', fontSize: 14 } },
    }
  }
  const cats = list.map((r) => {
    const name = (r.product_name || '').trim()
    const cd = (r.product_cd || '').trim()
    const base = name || cd || '—'
    return base.length > 16 ? `${base.slice(0, 15)}…` : base
  })
  const bad = list.map((r) => r.all_processes_defect_scrap ?? 0)
  const lossVals = list.map((r) => {
    const x = computeProductMainLineRty(r)
    return x != null ? Number(x.loss.toFixed(2)) : null
  })
  const rotate = list.length > 8 ? 48 : 28
  return {
    legend: { top: 0, textStyle: { fontSize: 11, color: '#64748b' } },
    grid: { left: 48, right: 52, top: 32, bottom: list.length > 6 ? 72 : 44, containLabel: false },
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => {
        const arr = Array.isArray(params) ? params : [params]
        const head = arr[0] as { dataIndex?: number }
        const i = head?.dataIndex ?? 0
        const row = list[i]
        if (!row) return ''
        const nm = (row.product_name || '').trim()
        const title = nm
          ? `${escapeHtml(row.product_cd)}<br/>${escapeHtml(nm)}`
          : escapeHtml(row.product_cd || '—')
        const lines = arr.map((x) => {
          const p = x as { seriesName?: string; value?: number | null; marker?: string }
          const v = p.value
          const m = p.marker ?? ''
          if (p.seriesName === '廃棄率（1−RTY）') {
            return `${m}${p.seriesName}: ${v != null && !Number.isNaN(Number(v)) ? `${v} %` : '—'}`
          }
          return `${m}${p.seriesName}: ${typeof v === 'number' ? fmtInt(v) : '—'}`
        })
        return [title, ...lines].join('<br/>')
      },
    },
    xAxis: {
      type: 'category',
      data: cats,
      axisLabel: { rotate, fontSize: 9, color: '#475569', interval: 0 },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
    },
    yAxis: [
      {
        type: 'value',
        name: '本数',
        position: 'left',
        splitLine: { lineStyle: { type: 'dashed', color: '#e2e8f0' } },
        axisLabel: { fontSize: 10, color: '#64748b' },
      },
      {
        type: 'value',
        name: '廃棄率 %',
        position: 'right',
        splitLine: { show: false },
        min: -10,
        max: 30,
        axisLabel: { fontSize: 10, color: '#c2410c', formatter: '{value}' },
      },
    ],
    series: [
      {
        name: '不良＋廃棄',
        type: 'bar',
        yAxisIndex: 0,
        data: bad,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#c4b5fd' },
            { offset: 1, color: '#7c3aed' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
        barMaxWidth: 36,
      },
      {
        name: '廃棄率（1−RTY）',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: lossVals,
        connectNulls: false,
        lineStyle: { width: 2, color: '#ea580c' },
        itemStyle: { color: '#ea580c' },
      },
    ],
  }
}

function resizeScrapCharts() {
  chartProcessRate?.resize()
  chartProcessVolume?.resize()
  chartProductCombo?.resize()
}

function scheduleChartResize() {
  if (resizeTimer) clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => {
    resizeTimer = null
    resizeScrapCharts()
  }, 120)
}

function syncScrapCharts() {
  nextTick(() => {
    const rEl = processRateChartRef.value
    const vEl = processVolumeChartRef.value
    const pEl = productComboChartRef.value
    if (rEl && rEl.clientWidth > 0) {
      if (!chartProcessRate) chartProcessRate = echarts.init(rEl, null, { renderer: 'canvas' })
      chartProcessRate.setOption(buildProcessRateChartOption(), true)
    }
    if (vEl && vEl.clientWidth > 0) {
      if (!chartProcessVolume) chartProcessVolume = echarts.init(vEl, null, { renderer: 'canvas' })
      chartProcessVolume.setOption(buildProcessVolumeChartOption(), true)
    }
    if (pEl && pEl.clientWidth > 0) {
      if (!chartProductCombo) chartProductCombo = echarts.init(pEl, null, { renderer: 'canvas' })
      chartProductCombo.setOption(buildProductComboChartOption(), true)
    }
    resizeScrapCharts()
  })
}

watch(
  () => [rows.value, productRows.value, productChartRows.value, productChartLoading.value, loading.value],
  () => {
    syncScrapCharts()
  },
  { deep: true }
)

async function fetchProcessSummary() {
  const dr = dateRange.value
  if (!dr?.[0] || !dr?.[1]) return
  const res = await getQualityRateByProcess({
    startDate: dr[0],
    endDate: dr[1],
    process: process.value || undefined,
  })
  const body = res as {
    data?: {
      processes?: typeof rows.value
      summary?: Summary
      all_processes_defect_scrap_total?: number
    }
  }
  const d = body.data
  if (!d) {
    rows.value = []
    summary.value = emptySummary()
    allProcessesDefectScrapTotal.value = 0
    return
  }
  allProcessesDefectScrapTotal.value = d.all_processes_defect_scrap_total ?? 0
  rows.value = d.processes ?? []
  const s = d.summary
  summary.value = s
    ? {
        basis: s.basis,
        reference_process_key: s.reference_process_key,
        reference_process_label: s.reference_process_label,
        sum_actual: s.sum_actual ?? 0,
        sum_defect: s.sum_defect ?? 0,
        sum_scrap: s.sum_scrap ?? 0,
        sum_defect_and_scrap: s.sum_defect_and_scrap ?? 0,
        rate: s.rate ?? null,
        rate_percent: s.rate_percent ?? null,
        rolled_yield_rate: s.rolled_yield_rate ?? null,
        rolled_yield_percent: s.rolled_yield_percent ?? null,
      }
    : emptySummary()
}

function productOptionLabel(p: { product_cd: string; product_name?: string | null }) {
  const name = (p.product_name || '').trim()
  return name ? `${p.product_cd} · ${name}` : p.product_cd
}

async function fetchProductOptions() {
  try {
    const res = await getProductionSummarysProducts()
    const data = (res as { data?: unknown })?.data ?? res
    productOptions.value = Array.isArray(data) ? (data as typeof productOptions.value) : []
  } catch {
    productOptions.value = []
  }
}

type QualityProductPayload = {
  main_line_labels?: typeof mainLineLabels.value
  pagination?: { total?: number }
  products?: ProductMatrixRow[]
}

/** axios インターセプタ後は response.data 本体。{ data: {...} } またはネストに両対応 */
function unwrapQualityRateByProductPayload(res: unknown): QualityProductPayload | null {
  if (res == null || typeof res !== 'object') return null
  const r = res as Record<string, unknown>
  const inner = r.data
  if (inner != null && typeof inner === 'object') {
    const mid = inner as Record<string, unknown>
    const nested = mid.data
    if (nested != null && typeof nested === 'object' && Array.isArray((nested as QualityProductPayload).products)) {
      return nested as QualityProductPayload
    }
    if (Array.isArray((inner as QualityProductPayload).products)) {
      return inner as QualityProductPayload
    }
  }
  if (Array.isArray((r as QualityProductPayload).products)) {
    return r as QualityProductPayload
  }
  return null
}

async function fetchProductMatrix() {
  const dr = dateRange.value
  if (!dr?.[0] || !dr?.[1]) return
  const res = await getQualityRateByProduct({
    startDate: dr[0],
    endDate: dr[1],
    page: productPage.value,
    limit: productLimit.value,
    productCd: String(filterProductCd.value ?? '').trim() || undefined,
    sortBy: productSortProp.value,
    sortOrder: productSortOrder.value,
  })
  const d = unwrapQualityRateByProductPayload(res)
  if (!d) {
    productRows.value = []
    productTotal.value = 0
    return
  }
  if (d.main_line_labels?.length) {
    mainLineLabels.value = d.main_line_labels
  }
  productRows.value = d.products ?? []
  productTotal.value = d.pagination?.total ?? 0
}

/** 製品チャート：期間・製品絞込で全ページ取得し、API 側 rty_loss 降順に合わせた上で上位のみ描画 */
async function refreshProductChartAllPages() {
  const dr = dateRange.value
  if (!dr?.[0] || !dr?.[1]) {
    productChartRows.value = []
    productChartTotal.value = 0
    syncScrapCharts()
    return
  }
  productChartLoading.value = true
  try {
    const pcd = String(filterProductCd.value ?? '').trim() || undefined
    const out: ProductMatrixRow[] = []
    let total = 0
    for (let page = 1; page <= PRINT_MAX_PAGES; page += 1) {
      const res = await getQualityRateByProduct({
        startDate: dr[0],
        endDate: dr[1],
        page,
        limit: PRINT_FETCH_LIMIT,
        productCd: pcd,
        sortBy: 'rty_loss',
        sortOrder: 'desc',
      })
      const d = unwrapQualityRateByProductPayload(res)
      if (!d) break
      total = d.pagination?.total ?? 0
      const batch = d.products ?? []
      out.push(...batch)
      if (batch.length < PRINT_FETCH_LIMIT || out.length >= total) break
    }
    productChartTotal.value = total
    productChartRows.value = out.slice(0, CHART_PRODUCT_DISPLAY_CAP)
  } catch (e) {
    console.error(e)
    productChartRows.value = []
    productChartTotal.value = 0
  } finally {
    productChartLoading.value = false
    syncScrapCharts()
  }
}

async function fetchAll() {
  const dr = dateRange.value
  if (!dr || !dr[0] || !dr[1]) {
    ElMessage.warning('期間を選択してください')
    return
  }
  loading.value = true
  try {
    await Promise.all([fetchProcessSummary(), fetchProductMatrix()])
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error('データの取得に失敗しました')
  } finally {
    loading.value = false
    void refreshProductChartAllPages()
  }
}

let filterDebounce: ReturnType<typeof setTimeout> | null = null
function scheduleAutoFetch() {
  if (filterDebounce) clearTimeout(filterDebounce)
  filterDebounce = setTimeout(() => {
    filterDebounce = null
    productPage.value = 1
    fetchAll()
  }, 320)
}

watch([dateRange, process, filterProductCd], () => scheduleAutoFetch(), { deep: true })

async function loadProductMatrixWithSpinner() {
  const dr = dateRange.value
  if (!dr?.[0] || !dr?.[1]) return
  loading.value = true
  try {
    await fetchProductMatrix()
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error('製品別データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

function onProductSortChange(payload: { prop?: string; order?: string | null }) {
  const prop = payload.prop
  const order = payload.order
  if (!prop || order == null) {
    productSortProp.value = 'product_name'
    productSortOrder.value = 'asc'
  } else {
    productSortProp.value = prop
    productSortOrder.value = order === 'descending' ? 'desc' : 'asc'
  }
  productPage.value = 1
  void loadProductMatrixWithSpinner()
}

async function onProductPageChange(p: number) {
  productPage.value = p
  await loadProductMatrixWithSpinner()
}

function escapeHtml(s: string) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function describeProductSortJp(): string {
  const p = productSortProp.value
  const ord = productSortOrder.value === 'desc' ? '降順' : '昇順'
  const ml = mainLineLabels.value.find((c) => c.key === p)
  if (ml) return `${ml.label}（％）·${ord}`
  const fixed: Record<string, string> = {
    product_cd: '製品CD',
    product_name: '製品名',
    all_processes_defect_scrap: '不良＋廃棄',
    rty: '合格率',
    rty_loss: '廃棄率',
  }
  return `${fixed[p] ?? p}·${ord}`
}

async function fetchAllProductRowsForPrint(): Promise<{ rows: ProductMatrixRow[]; total: number }> {
  const dr = dateRange.value
  if (!dr?.[0] || !dr?.[1]) return { rows: [], total: 0 }
  const pcd = String(filterProductCd.value ?? '').trim() || undefined
  const sortBy = productSortProp.value
  const sortOrder = productSortOrder.value
  const out: ProductMatrixRow[] = []
  let total = 0
  for (let page = 1; page <= PRINT_MAX_PAGES; page += 1) {
    const res = await getQualityRateByProduct({
      startDate: dr[0],
      endDate: dr[1],
      page,
      limit: PRINT_FETCH_LIMIT,
      productCd: pcd,
      sortBy,
      sortOrder,
    })
    const d = unwrapQualityRateByProductPayload(res)
    if (!d) break
    total = d.pagination?.total ?? 0
    const batch = d.products ?? []
    out.push(...batch)
    if (batch.length < PRINT_FETCH_LIMIT || out.length >= total) break
  }
  return { rows: out, total }
}

function buildProductPrintHtml(rows: ProductMatrixRow[], total: number): string {
  const dr = dateRange.value!
  const cols = mainLineLabels.value
  const thProc = cols.map((c) => `<th>${escapeHtml(c.label)}（％）</th>`).join('')
  const bodyRows = rows
    .map((row) => {
      const tds = [
        `<td class="num">${escapeHtml(row.product_cd)}</td>`,
        `<td>${escapeHtml(row.product_name || '')}</td>`,
        `<td class="num">${escapeHtml(fmtInt(row.all_processes_defect_scrap))}</td>`,
        ...cols.map((c) => `<td class="num">${escapeHtml(formatProcCell(row, c.key))}</td>`),
        `<td class="num">${escapeHtml(formatProductRtyLoss(row))}</td>`,
        `<td class="num">${escapeHtml(formatProductRty(row))}</td>`,
      ]
      return `<tr>${tds.join('')}</tr>`
    })
    .join('')
  const filterPcd = String(filterProductCd.value ?? '').trim()
  const filterLine = filterPcd
    ? `製品絞込: ${escapeHtml(filterPcd)}`
    : '製品絞込: （すべて）'
  const sortLine = escapeHtml(describeProductSortJp())
  const truncated = total > rows.length
  const note = truncated
    ? `<p class="note">※ 全 ${fmtInt(total)} 件中 ${fmtInt(rows.length)} 件を印刷（上限 ${PRINT_FETCH_LIMIT * PRINT_MAX_PAGES} 件）</p>`
    : `<p class="meta">件数: ${fmtInt(rows.length)} 件</p>`

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <title>製品別集計</title>
  <style>
    /* 用紙: A4 横向（プレビュー・印刷の両方で有効な環境が多い） */
    @page {
      size: A4 landscape;
      margin: 8mm 10mm;
    }
    html {
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    body {
      font-family: 'Segoe UI', 'Hiragino Sans', 'Meiryo', sans-serif;
      font-size: 11px;
      color: #0f172a;
      margin: 14px 18px;
      box-sizing: border-box;
    }
    h1 { font-size: 15px; margin: 0 0 8px; }
    .meta { margin: 3px 0; color: #475569; font-size: 10.5px; }
    .note { margin: 6px 0 0; color: #b45308; font-size: 10px; }
    table {
      border-collapse: collapse;
      width: 100%;
      margin-top: 8px;
      table-layout: fixed;
    }
    th, td {
      border: 1px solid #94a3b8;
      padding: 3px 5px;
      vertical-align: middle;
      word-wrap: break-word;
    }
    th {
      background: #e2e8f0;
      font-weight: 600;
      text-align: center;
      font-size: 10px;
    }
    td.num {
      text-align: right;
      font-variant-numeric: tabular-nums;
    }
    @media print {
      body {
        margin: 0;
        padding: 0;
        font-size: 10px;
      }
      h1 { font-size: 14px; }
      table { margin-top: 6px; }
      th, td { padding: 2px 4px; }
    }
  </style>
</head>
<body>
  <h1>廃棄率分析 · 製品別集計</h1>
  <p class="meta">集計期間: ${escapeHtml(dr[0])} ～ ${escapeHtml(dr[1])}</p>
  <p class="meta">${filterLine}</p>
  <p class="meta">並び順: ${sortLine}</p>
  ${note}
  <table>
    <thead>
      <tr>
        <th>製品CD</th>
        <th>製品名</th>
        <th>不良＋廃棄</th>
        ${thProc}
        <th>廃棄率</th>
        <th>合格率</th>
      </tr>
    </thead>
    <tbody>${bodyRows}</tbody>
  </table>
</body>
</html>`
}

async function printProductTable() {
  const dr = dateRange.value
  if (!dr?.[0] || !dr?.[1]) {
    ElMessage.warning('期間を選択してください')
    return
  }
  printProductLoading.value = true
  try {
    const { rows, total } = await fetchAllProductRowsForPrint()
    if (!rows.length) {
      ElMessage.info('印刷するデータがありません')
      return
    }
    const html = buildProductPrintHtml(rows, total)
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    // noopener 付与だと window.open が null になる環境があり、document.write も about:blank で不安定なため Blob URL を使用
    const w = window.open(url, '_blank')
    if (!w) {
      URL.revokeObjectURL(url)
      ElMessage.warning('ポップアップを許可してください')
      return
    }
    const cleanup = () => {
      try {
        URL.revokeObjectURL(url)
        w.close()
      } catch {
        /* ignore */
      }
    }
    setTimeout(() => {
      try {
        w.focus()
        w.addEventListener('afterprint', cleanup, { once: true })
        w.print()
      } catch {
        /* ignore */
      }
      setTimeout(cleanup, 2500)
    }, 400)
  } catch (e) {
    console.error(e)
    ElMessage.error('印刷用データの取得に失敗しました')
  } finally {
    printProductLoading.value = false
  }
}

onMounted(() => {
  fetchProductOptions()
  fetchAll()
  window.addEventListener('resize', scheduleChartResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', scheduleChartResize)
  if (resizeTimer) {
    clearTimeout(resizeTimer)
    resizeTimer = null
  }
  disposeScrapCharts()
})
</script>

<style scoped>
.scrap-page {
  min-height: 100%;
  padding: 10px 12px 16px;
  background:
    radial-gradient(ellipse 90% 55% at 10% -10%, rgba(239, 68, 68, 0.09), transparent 52%),
    linear-gradient(165deg, #f8fafc 0%, #f1f5f9 55%, #e8eef4 100%);
  box-sizing: border-box;
}

.scrap-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 2px 2px 6px;
}

.scrap-hero__left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.scrap-hero__icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  color: #fff;
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.28);
}

.scrap-hero__title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
}

.scrap-hero__meta {
  margin: 2px 0 0;
  font-size: 0.72rem;
  color: #64748b;
  letter-spacing: 0.02em;
}

.scrap-card {
  border-radius: 14px !important;
  border: 1px solid rgba(148, 163, 184, 0.22) !important;
  background: rgba(255, 255, 255, 0.92) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 12px 40px rgba(15, 23, 42, 0.06) !important;
}

.scrap-card :deep(.el-card__body) {
  padding: 14px 14px 16px;
}

.scrap-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 12px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.scrap-field {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.scrap-field--grow {
  flex: 1 1 200px;
}

.scrap-field__ico {
  flex-shrink: 0;
  font-size: 16px;
  color: #94a3b8;
}

.scrap-toolbar__date {
  width: 248px;
}

.scrap-toolbar__proc {
  width: 152px;
}

.scrap-toolbar__product {
  width: min(260px, 100%);
  flex: 1 1 200px;
}

.scrap-kpi {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.scrap-kpi__item {
  position: relative;
  overflow: hidden;
  padding: 10px 12px;
  border-radius: 10px;
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.scrap-kpi__water {
  position: absolute;
  right: 4px;
  top: 2px;
  font-size: 2.25rem;
  pointer-events: none;
}

.scrap-kpi__water--rose {
  color: #f43f5e;
  opacity: 0.11;
}

.scrap-kpi__water--emerald {
  color: #10b981;
  opacity: 0.13;
}

.scrap-kpi__water--amber {
  color: #d97706;
  opacity: 0.11;
}

.scrap-kpi__water--gold {
  color: #ca8a04;
  opacity: 0.14;
}

.scrap-kpi__item--accent {
  background: linear-gradient(145deg, #fffbeb 0%, #fef9c3 100%);
  border-color: rgba(234, 179, 8, 0.28);
}

.scrap-kpi__label {
  font-size: 0.72rem;
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.02em;
  line-height: 1.25;
}

.scrap-kpi__value {
  margin-top: 4px;
  font-size: 1.35rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
  letter-spacing: -0.03em;
  line-height: 1.15;
}

.scrap-kpi__hint {
  margin-top: 4px;
  font-size: 0.68rem;
  color: #94a3b8;
  line-height: 1.35;
}

.scrap-block {
  margin-top: 10px;
}

.scrap-block:first-of-type {
  margin-top: 0;
}

.scrap-block__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.scrap-block__head--with-actions {
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.scrap-block__head-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.scrap-print-btn-ico {
  margin-right: 4px;
  vertical-align: middle;
}

.scrap-block__ico {
  flex-shrink: 0;
  font-size: 17px;
}

.scrap-block__ico--indigo {
  color: #6366f1;
}

.scrap-block__ico--teal {
  color: #14b8a6;
}

.scrap-block__title {
  font-size: 0.8rem;
  font-weight: 700;
  color: #334155;
  letter-spacing: -0.01em;
}

.scrap-block__head--charts {
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 6px 12px;
}

.scrap-block__ico--chart {
  color: #0ea5e9;
}

.scrap-charts__note {
  font-size: 0.68rem;
  color: #94a3b8;
  white-space: nowrap;
}

.scrap-charts__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.scrap-chart-card {
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  background: linear-gradient(180deg, #fafbff 0%, #fff 55%);
  padding: 8px 10px 10px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.scrap-chart-card--span2 {
  grid-column: 1 / -1;
}

.scrap-chart-card__title {
  font-size: 0.72rem;
  font-weight: 700;
  color: #475569;
  margin-bottom: 2px;
  letter-spacing: 0.01em;
}

.scrap-chart-card__sub {
  font-size: 0.65rem;
  color: #94a3b8;
  margin-bottom: 4px;
  line-height: 1.35;
}

.scrap-chart-host {
  width: 100%;
  height: 240px;
}

.scrap-chart-host--wide {
  height: 260px;
}

@media (max-width: 960px) {
  .scrap-charts__grid {
    grid-template-columns: 1fr;
  }

  .scrap-chart-card--span2 {
    grid-column: auto;
  }
}

.scrap-table-shell {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #fff;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.85) inset,
    0 4px 18px rgba(15, 23, 42, 0.05);
}

.scrap-table-shell--process {
  background: linear-gradient(180deg, #fafbff 0%, #fff 48%);
}

.scrap-table-shell--product {
  background: linear-gradient(180deg, #fafffe 0%, #fff 40%);
}

.scrap-table-shell--wide {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.scrap-table {
  width: 100%;
  --scrap-table-header-bg: linear-gradient(180deg, #f1f5f9 0%, #e8eef5 100%);
  --scrap-table-header-fg: #334155;
  --scrap-table-border: #e2e8f0;
}

.scrap-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.scrap-table :deep(.el-table__border-left-patch) {
  border-color: var(--scrap-table-border);
}

.scrap-table :deep(.el-table__header-wrapper .el-table__cell) {
  padding: 9px 10px;
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--scrap-table-header-fg);
  background: var(--scrap-table-header-bg) !important;
  border-bottom: 1px solid #cbd5e1 !important;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.65) inset;
}

.scrap-table :deep(.el-table__body .el-table__cell) {
  padding: 7px 10px;
  font-size: 12.5px;
  color: #1e293b;
  border-color: rgba(226, 232, 240, 0.95) !important;
}

.scrap-table :deep(.el-table__row) {
  font-variant-numeric: tabular-nums;
  transition: background-color 0.12s ease;
}

.scrap-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: rgba(241, 245, 249, 0.75) !important;
}

.scrap-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background-color: rgba(248, 250, 252, 0.92);
}

.scrap-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped:hover > td.el-table__cell) {
  background-color: rgba(241, 245, 249, 0.95) !important;
}

.scrap-table :deep(.el-table__fixed-right) {
  box-shadow: -6px 0 14px rgba(15, 23, 42, 0.06);
}

.scrap-table :deep(.el-table__fixed) {
  box-shadow: 6px 0 14px rgba(15, 23, 42, 0.05);
}

/* 工程別：列ごとのヘッダー帯 */
.scrap-table--process :deep(th.scrap-th--proc .cell) {
  font-weight: 700;
  color: #312e81;
}

.scrap-table--process :deep(th.scrap-th--actual) {
  border-left: 1px solid rgba(203, 213, 225, 0.9);
}

.scrap-table--process :deep(th.scrap-th--defect .cell),
.scrap-table--process :deep(td.scrap-td--defect) {
  color: #9a3412;
}

.scrap-table--process :deep(th.scrap-th--scrap .cell),
.scrap-table--process :deep(td.scrap-td--scrap) {
  color: #b91c1c;
}

.scrap-table--process :deep(th.scrap-th--sum .cell),
.scrap-table--process :deep(td.scrap-td--sum) {
  color: #a21caf;
  font-weight: 600;
}

.scrap-table--process :deep(th.scrap-th--rate) {
  background: linear-gradient(180deg, #fff1f2 0%, #ffe4e6 100%) !important;
  border-left: 2px solid #fb7185 !important;
}

.scrap-table--process :deep(th.scrap-th--rate .cell) {
  color: #9f1239;
}

.scrap-table--process :deep(td.scrap-td--rate) {
  font-weight: 700;
  color: #be123c;
  letter-spacing: -0.02em;
  background: rgba(255, 241, 242, 0.35);
}

.scrap-table--process :deep(.el-table__row--striped td.scrap-td--rate) {
  background: rgba(254, 226, 226, 0.45);
}

.scrap-table--process :deep(.el-table__body tr:hover > td.scrap-td--rate) {
  background: rgba(254, 202, 202, 0.55) !important;
}

.scrap-table--process :deep(td.scrap-td--proc) {
  font-weight: 600;
  color: #334155;
}

/* 製品別：識別列・工程％・RTY */
.scrap-table--product :deep(td.scrap-td--sku) {
  font-weight: 600;
  font-family: ui-monospace, 'Cascadia Code', 'Segoe UI Mono', monospace;
  font-size: 12px;
  color: #0f172a;
  letter-spacing: -0.03em;
}

.scrap-table--product :deep(th.scrap-th--sku .cell) {
  color: #1e3a5f;
}

.scrap-table--product :deep(td.scrap-td--name) {
  color: #475569;
}

.scrap-table--product :deep(th.scrap-th--allbad) {
  background: linear-gradient(180deg, #fdf4ff 0%, #fae8ff 100%) !important;
}

.scrap-table--product :deep(th.scrap-th--allbad .cell) {
  color: #86198f;
  font-size: 11px;
}

.scrap-table--product :deep(td.scrap-td--allbad) {
  font-weight: 600;
  color: #701a75;
  background: rgba(250, 245, 255, 0.45);
}

.scrap-table--product :deep(.el-table__row--striped td.scrap-td--allbad) {
  background: rgba(243, 232, 255, 0.55);
}

.scrap-table--product :deep(th.scrap-th--pline) {
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%) !important;
}

.scrap-table--product :deep(th.scrap-th--pline .cell) {
  color: #3730a3;
  font-size: 11px;
}

.scrap-table--product :deep(td.scrap-td--pline) {
  color: #4338ca;
}

.scrap-table--product :deep(th.scrap-th--rty-loss) {
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%) !important;
  border-left: 2px solid #fbbf24 !important;
}

.scrap-table--product :deep(th.scrap-th--rty-loss .cell) {
  color: #92400e;
}

.scrap-table--product :deep(td.scrap-td--rty-loss) {
  font-weight: 600;
  color: #b45309;
  background: rgba(255, 251, 235, 0.5);
}

.scrap-table--product :deep(.el-table__row--striped td.scrap-td--rty-loss) {
  background: rgba(254, 243, 199, 0.35);
}

.scrap-table--product :deep(th.scrap-th--rty-yield) {
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%) !important;
  border-left: 2px solid #34d399 !important;
}

.scrap-table--product :deep(th.scrap-th--rty-yield .cell) {
  color: #065f46;
}

.scrap-table--product :deep(td.scrap-td--rty-yield) {
  font-weight: 700;
  color: #047857;
  background: rgba(236, 253, 245, 0.55);
}

.scrap-table--product :deep(.el-table__row--striped td.scrap-td--rty-yield) {
  background: rgba(209, 250, 229, 0.4);
}

.scrap-table--product :deep(.el-table__body tr:hover > td.scrap-td--rty-loss) {
  background: rgba(253, 230, 138, 0.72) !important;
}

.scrap-table--product :deep(.el-table__body tr:hover > td.scrap-td--rty-yield) {
  background: rgba(167, 243, 208, 0.85) !important;
}

.scrap-pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

@media (max-width: 1100px) {
  .scrap-kpi {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .scrap-page {
    padding: 8px 10px 14px;
  }

  .scrap-toolbar__date,
  .scrap-toolbar__proc {
    width: 100%;
  }

  .scrap-toolbar__product {
    flex: 1 1 100%;
    width: 100%;
  }
}
</style>
