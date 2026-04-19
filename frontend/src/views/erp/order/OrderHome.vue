<template>
  <div class="order-home">
    <div class="dynamic-background" aria-hidden="true">
      <div class="gradient-orb orb-1" />
      <div class="gradient-orb orb-2" />
      <div class="gradient-orb orb-3" />
    </div>

    <header class="page-head">
      <div class="page-head-icon">
        <el-icon :size="28"><Document /></el-icon>
      </div>
      <div>
        <h1 class="page-head-title">受注管理</h1>
        <p class="page-head-sub">月次・日次の受注と納入先履歴を一元管理</p>
      </div>
    </header>

    <!-- 合計カード（OrderMonthlyList.vue と同一内容・当月サマリ） -->
    <div
      class="summary-cards"
      :class="{ 'animate-in-delay-1': !statsLoading }"
      v-loading="statsLoading"
      element-loading-background="rgba(255,255,255,0.6)"
    >
      <el-card class="summary-card modern-card info-card">
        <div class="card-content">
          <div class="card-icon info-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryForecastUnits') }}</div>
            <div class="summary-value">{{ summary.forecast_units?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card success-card">
        <div class="card-content">
          <div class="card-icon success-icon">
            <el-icon><Check /></el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryConfirmedUnits') }}</div>
            <div class="summary-value">{{ summary.forecast_total_units?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card diff-card">
        <div class="card-content">
          <div class="card-icon diff-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryForecastDiff') }}</div>
            <div
              class="summary-value"
              :style="{
                color:
                  summary.forecast_diff < 0
                    ? '#e74c3c'
                    : summary.forecast_diff > 0
                      ? '#2ecc71'
                      : '#606266',
              }"
            >
              {{ summary.forecast_diff?.toLocaleString() }}
            </div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card plating-card">
        <div class="card-content">
          <div class="card-icon plating-icon">
            <el-icon><Operation /></el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryPlating') }}</div>
            <div class="summary-value">{{ summary.plating_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card external-plating-card">
        <div class="card-content">
          <div class="card-icon external-plating-icon">
            <el-icon><Tools /></el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryExternalPlating') }}</div>
            <div class="summary-value">{{ summary.external_plating_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card internal-welding-card">
        <div class="card-content">
          <div class="card-icon internal-welding-icon">
            <el-icon><OfficeBuilding /></el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryInternalWelding') }}</div>
            <div class="summary-value">{{ summary.internal_welding_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card external-welding-card">
        <div class="card-content">
          <div class="card-icon external-welding-icon">
            <el-icon><Tools /></el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryExternalWelding') }}</div>
            <div class="summary-value">{{ summary.external_welding_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card internal-inspection-card">
        <div class="card-content">
          <div class="card-icon internal-inspection-icon">
            <el-icon><View /></el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryInternalInspection') }}</div>
            <div class="summary-value">{{ summary.internal_inspection_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card external-inspection-card">
        <div class="card-content">
          <div class="card-icon external-inspection-icon">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryExternalInspection') }}</div>
            <div class="summary-value">{{ summary.external_inspection_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>
    </div>

    <!-- 月別チャート + 日別チャート -->
    <section class="analytics-block">
      <el-card class="analytics-card chart-card chart-card--premium" shadow="never">
        <template #header>
          <div class="analytics-card-head analytics-card-head--chart">
            <div class="analytics-card-head-left">
              <el-icon class="analytics-card-head-icon"><TrendCharts /></el-icon>
              <div class="analytics-card-head-text">
                <span class="analytics-card-title">月別推移（過去6ヶ月＋未来2ヶ月）</span>
                <span class="analytics-card-sub">直近6ヶ月〜当月を実績、先2ヶ月は登録ベース（APIサマリ）</span>
              </div>
            </div>
            <div class="chart-legend-hint">
              <span class="legend-dot legend-dot--past" />実績帯
              <span class="legend-dot legend-dot--future" />先見込
            </div>
          </div>
        </template>
        <div class="monthly-chart-shell">
          <div
            ref="monthlyChartRef"
            class="monthly-chart-host"
            v-loading="chartLoading"
            element-loading-background="rgba(255,255,255,0.65)"
          />
        </div>
      </el-card>

      <el-card class="analytics-card daily-chart-card chart-card--premium-daily" shadow="never">
        <template #header>
          <div class="analytics-card-head analytics-card-head--chart">
            <div class="analytics-card-head-left">
              <el-icon class="analytics-card-head-icon"><Calendar /></el-icon>
              <div class="analytics-card-head-text">
                <span class="analytics-card-title">日別集計（当月）</span>
                <span class="analytics-card-sub">ダッシュボードと同じ棒グラフ（JST）。高さ＝確定本数。色は過去／当日／当月内の未来を区別</span>
              </div>
            </div>
            <div class="chart-legend-hint chart-legend-hint--daily">
              <span class="legend-dot legend-dot--daily-past" />過去
              <span class="legend-dot legend-dot--daily-today" />今日
              <span class="legend-dot legend-dot--daily-future" />未来
            </div>
          </div>
        </template>
        <div class="daily-chart-shell">
          <div
            ref="dailyChartRef"
            class="daily-chart-host"
            v-loading="dailyLoading"
            element-loading-background="rgba(255,255,255,0.65)"
          />
        </div>
      </el-card>

      <el-card class="analytics-card product-rank-card chart-card--premium-rank" shadow="never">
        <template #header>
          <div class="analytics-card-head analytics-card-head--chart">
            <div class="analytics-card-head-left">
              <el-icon class="analytics-card-head-icon"><Histogram /></el-icon>
              <div class="analytics-card-head-text">
                <span class="analytics-card-title">製品別ランキング（当月・確定本数）</span>
                <span class="analytics-card-sub">日別受注データを集計。上位{{ PRODUCT_RANK_LIMIT }}品目（同率は件数多い順）</span>
              </div>
            </div>
            <div class="chart-legend-hint chart-legend-hint--rank">
              <span class="legend-dot legend-dot--rank-top" />1〜3位
              <span class="legend-dot legend-dot--rank-rest" />その他
            </div>
          </div>
        </template>
        <div class="product-rank-chart-shell">
          <el-empty
            v-if="!productRankHasData"
            description="当月の受注データがありません"
            class="chart-empty-inline"
          />
          <div
            v-show="productRankHasData"
            ref="productRankChartRef"
            class="product-rank-chart-host"
            v-loading="dailyLoading"
            element-loading-background="rgba(255,255,255,0.65)"
          />
        </div>
      </el-card>
    </section>

    <!-- 中：アイコンリング（機能への導線） -->
    <section class="icon-ring" aria-label="機能メニュー">
      <router-link to="/erp/order/monthly" class="icon-ring-item icon-ring-item--violet">
        <div class="icon-bubble">
          <el-icon :size="36"><Calendar /></el-icon>
        </div>
        <span class="icon-ring-title">月受注</span>
        <span class="icon-ring-hint">月別・内示</span>
      </router-link>
      <div class="icon-ring-connector" aria-hidden="true" />
      <router-link to="/erp/order/daily" class="icon-ring-item icon-ring-item--cyan">
        <div class="icon-bubble">
          <el-icon :size="36"><Clock /></el-icon>
        </div>
        <span class="icon-ring-title">日受注</span>
        <span class="icon-ring-hint">日別・確定</span>
      </router-link>
      <div class="icon-ring-connector" aria-hidden="true" />
      <router-link to="/erp/order/destination-history" class="icon-ring-item icon-ring-item--amber">
        <div class="icon-bubble">
          <el-icon :size="36"><DataAnalysis /></el-icon>
        </div>
        <span class="icon-ring-title">納入先履歴</span>
        <span class="icon-ring-hint">分析・照会</span>
      </router-link>
    </section>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatInteger } from '@/utils/formatInteger'
import type { LocaleType } from '@/i18n'
import {
  Calendar,
  Check,
  Clock,
  DataAnalysis,
  Document,
  Monitor,
  OfficeBuilding,
  Operation,
  Tools,
  TrendCharts,
  View,
  Histogram,
} from '@element-plus/icons-vue'
import { fetchMonthlySummary, type OrderMonthlySummary } from '@/api/erp/orderMonthly'
import { fetchOrderDailyList, type OrderDailyItem } from '@/api/erp/orderDaily'

const { t, locale } = useI18n()

const statsLoading = ref(true)
const chartLoading = ref(false)
const dailyLoading = ref(false)

const monthlyChartRef = ref<HTMLDivElement | null>(null)
let monthlyEcharts: echarts.ECharts | null = null

const dailyChartRef = ref<HTMLDivElement | null>(null)
let dailyEcharts: echarts.ECharts | null = null

const productRankChartRef = ref<HTMLDivElement | null>(null)
let productRankEcharts: echarts.ECharts | null = null

/** 当月製品ランキング表示件数 */
const PRODUCT_RANK_LIMIT = 12

interface ProductRankRow {
  product_cd: string
  product_name: string
  confirmed_units: number
  line_count: number
}

const productRankRows = ref<ProductRankRow[]>([])

const productRankHasData = computed(() => productRankRows.value.length > 0)

interface DailyAggRow {
  date: string
  weekday: string
  count: number
  confirmed_units: number
}

const dailyRows = ref<DailyAggRow[]>([])

const WD_JA = ['日', '月', '火', '水', '木', '金', '土']

function getJapanDate(): Date {
  return new Date(new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' }))
}

/** JST の当日 YYYY-MM-DD（ダッシュボード日別チャートの「今日」区切りと同趣旨） */
function getJapanTodayStr(): string {
  const d = getJapanDate()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function emptySummary(): OrderMonthlySummary {
  return {
    forecast_units: 0,
    forecast_total_units: 0,
    forecast_diff: 0,
    plating_count: 0,
    external_plating_count: 0,
    internal_welding_count: 0,
    external_welding_count: 0,
    internal_inspection_count: 0,
    external_inspection_count: 0,
  }
}

/** 過去6ヶ月（当月含む）＋未来2ヶ月 ＝ 計8ヶ月、古い順→新しい順、日本日付基準。未来区間は index 6,7 */
function past6Future2MonthsJp(): { year: number; month: number; label: string }[] {
  const d = getJapanDate()
  const cy = d.getFullYear()
  const cm = d.getMonth() + 1
  let y = cy
  let m = cm - 5
  while (m < 1) {
    m += 12
    y -= 1
  }
  const buf: { year: number; month: number; label: string }[] = []
  for (let i = 0; i < 8; i++) {
    buf.push({
      year: y,
      month: m,
      label: `${y}/${String(m).padStart(2, '0')}`,
    })
    m += 1
    if (m > 12) {
      m = 1
      y += 1
    }
  }
  return buf
}

const FUTURE_MONTH_START_INDEX = 6

function onChartResize() {
  monthlyEcharts?.resize()
  dailyEcharts?.resize()
  productRankEcharts?.resize()
}

/** 月受注一覧と同条件（当月・フィルタなし）のサマリ */
const summary = reactive<OrderMonthlySummary>({
  forecast_units: 0,
  forecast_total_units: 0,
  forecast_diff: 0,
  plating_count: 0,
  external_plating_count: 0,
  internal_welding_count: 0,
  external_welding_count: 0,
  internal_inspection_count: 0,
  external_inspection_count: 0,
})

function disposeMonthlyChart() {
  monthlyEcharts?.dispose()
  monthlyEcharts = null
}

function disposeDailyChart() {
  dailyEcharts?.dispose()
  dailyEcharts = null
}

function disposeProductRankChart() {
  productRankEcharts?.dispose()
  productRankEcharts = null
}

/** 日別受注一覧から当月の製品別確定本数ランキングを算出 */
function aggregateProductRank(list: OrderDailyItem[]): ProductRankRow[] {
  const map = new Map<string, { name: string; units: number; lines: number }>()
  for (const row of list) {
    const cd = String(row.product_cd ?? '').trim()
    if (!cd) continue
    const displayName = (row.product_name || row.product_alias || cd).trim()
    if (displayName.includes('加工')) continue
    if (!map.has(cd)) {
      map.set(cd, { name: displayName || cd, units: 0, lines: 0 })
    }
    const a = map.get(cd)!
    a.units += Number(row.confirmed_units) || 0
    a.lines += 1
    if (displayName.length > a.name.length) a.name = displayName
  }
  return [...map.entries()]
    .map(([product_cd, v]) => ({
      product_cd,
      product_name: v.name,
      confirmed_units: v.units,
      line_count: v.lines,
    }))
    .sort((a, b) => b.confirmed_units - a.confirmed_units || b.line_count - a.line_count)
    .slice(0, PRODUCT_RANK_LIMIT)
}

function rankBarGradient(rankIndex: number): echarts.graphic.LinearGradient {
  if (rankIndex === 0) {
    return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#fcd34d' },
      { offset: 1, color: '#d97706' },
    ])
  }
  if (rankIndex === 1) {
    return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#e2e8f0' },
      { offset: 1, color: '#64748b' },
    ])
  }
  if (rankIndex === 2) {
    return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#fdba74' },
      { offset: 1, color: '#c2410c' },
    ])
  }
  return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
    { offset: 0, color: '#a5b4fc' },
    { offset: 1, color: '#4338ca' },
  ])
}

function productRankYLabel(row: ProductRankRow, index: number): string {
  const rank = index + 1
  const base = (row.product_name || row.product_cd).trim()
  const max = 22
  const s = base.length > max ? `${base.slice(0, max)}…` : base
  return `${rank}. ${s}`
}

function renderProductRankChart(rows: ProductRankRow[]) {
  if (!productRankChartRef.value) return
  if (!rows.length) {
    disposeProductRankChart()
    return
  }
  if (!productRankEcharts) {
    productRankEcharts = echarts.init(productRankChartRef.value, null, { renderer: 'canvas' })
  }

  const categories = rows.map((r, i) => productRankYLabel(r, i))
  const barData = rows.map((r, i) => ({
    value: r.confirmed_units,
    itemStyle: {
      color: rankBarGradient(i),
      borderRadius: [0, 8, 8, 0],
      shadowBlur: i < 3 ? 12 : 8,
      shadowColor:
        i === 0
          ? 'rgba(217, 119, 6, 0.25)'
          : i < 3
            ? 'rgba(100, 116, 139, 0.2)'
            : 'rgba(67, 56, 202, 0.18)',
      shadowOffsetX: 2,
    },
  }))

  productRankEcharts.setOption(
    {
      backgroundColor: 'transparent',
      animationDuration: 720,
      animationEasing: 'cubicOut',
      textStyle: { fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif' },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(99, 102, 241, 0.06)' } },
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        borderWidth: 0,
        borderRadius: 10,
        padding: [10, 14],
        textStyle: { color: '#f8fafc', fontSize: 12 },
        formatter: (params: unknown) => {
          const p = Array.isArray(params) ? params[0] : params
          const idx = (p as { dataIndex?: number }).dataIndex ?? 0
          const row = rows[idx]
          if (!row) return ''
          const u = formatInteger(row.confirmed_units, locale.value as LocaleType)
          const n = formatInteger(row.line_count, locale.value as LocaleType)
          return `<div style="font-weight:600;margin-bottom:6px">${row.product_name || row.product_cd}</div>
<div style="opacity:.88;font-size:11px;margin-bottom:4px">コード: ${row.product_cd}</div>
<span style="opacity:.95">確定本数: ${u} ${t('dashboard.dailyOrderChart.axis')}</span><br/>
<span style="opacity:.85">受注行数: ${n}</span>`
        },
      },
      grid: { left: 4, right: 20, top: 8, bottom: 8, containLabel: true },
      xAxis: {
        type: 'value',
        name: t('dashboard.dailyOrderChart.axis'),
        nameTextStyle: { fontSize: 10, color: '#94a3b8' },
        axisLabel: { fontSize: 10, color: '#94a3b8' },
        splitLine: { lineStyle: { type: 'dashed', color: '#e8ecf1', width: 1 } },
        axisLine: { show: false },
      },
      yAxis: {
        type: 'category',
        data: categories,
        inverse: true,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          fontSize: 10,
          color: '#475569',
          fontWeight: 600,
          width: 168,
          overflow: 'truncate',
        },
      },
      series: [
        {
          type: 'bar',
          barMaxWidth: 22,
          data: barData,
          label: {
            show: true,
            position: 'right',
            distance: 6,
            fontSize: 10,
            fontWeight: 600,
            color: '#64748b',
            formatter: (p: { data?: { value?: number }; value?: number }) => {
              const v =
                typeof p.data === 'object' && p.data && typeof p.data.value === 'number'
                  ? p.data.value
                  : typeof p.value === 'number'
                    ? p.value
                    : 0
              if (v === 0) return ''
              return formatInteger(v, locale.value as LocaleType)
            },
          },
          emphasis: {
            focus: 'series',
            itemStyle: { shadowBlur: 16, shadowColor: 'rgba(99, 102, 241, 0.35)' },
          },
        },
      ],
    },
    { notMerge: true }
  )
  nextTick(() => productRankEcharts?.resize())
}

function barGradient(
  dataIndex: number,
  topA: string,
  botA: string,
  topFut: string,
  botFut: string
): echarts.graphic.LinearGradient {
  const isFut = dataIndex >= FUTURE_MONTH_START_INDEX
  return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: isFut ? topFut : topA },
    { offset: 1, color: isFut ? botFut : botA },
  ])
}

function renderMonthlyChart(labels: string[], forecastUnits: number[], forecastTotal: number[]) {
  if (!monthlyChartRef.value) return
  if (!monthlyEcharts) {
    monthlyEcharts = echarts.init(monthlyChartRef.value, null, { renderer: 'canvas' })
  }
  monthlyEcharts.setOption(
    {
      color: ['#6366f1', '#14b8a6'],
      animationDuration: 780,
      animationEasing: 'cubicOut',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(99,102,241,0.12)' } },
        backgroundColor: 'rgba(255,255,255,0.97)',
        borderColor: '#e2e8f0',
        borderWidth: 1,
        padding: [10, 14],
        extraCssText: 'box-shadow:0 10px 40px rgba(15,23,42,0.12);border-radius:12px;',
        textStyle: { color: '#334155', fontSize: 12 },
      },
      legend: {
        data: ['内示本数', '確定合計本数'],
        bottom: 2,
        itemGap: 20,
        itemWidth: 12,
        itemHeight: 12,
        icon: 'roundRect',
        textStyle: { fontSize: 11, color: '#64748b', fontWeight: 600 },
      },
      grid: { left: 48, right: 16, top: 20, bottom: 52 },
      xAxis: {
        type: 'category',
        data: labels,
        axisTick: { show: false },
        axisLine: { lineStyle: { color: '#e2e8f0', width: 1 } },
        axisLabel: {
          fontSize: 10,
          margin: 10,
          rotate: 0,
          formatter: (val: string, idx: number) =>
            idx >= FUTURE_MONTH_START_INDEX ? `{f|${val}}` : `{p|${val}}`,
          rich: {
            p: { color: '#475569', fontWeight: 600, fontSize: 10 },
            f: { color: '#7c3aed', fontWeight: 700, fontSize: 10 },
          },
        },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        splitLine: {
          lineStyle: { color: '#f1f5f9', type: 'solid' },
        },
        axisLabel: {
          fontSize: 10,
          color: '#94a3b8',
        },
      },
      series: [
        {
          name: '内示本数',
          type: 'bar',
          data: forecastUnits,
          barMaxWidth: 26,
          barGap: '18%',
          emphasis: {
            focus: 'series',
            itemStyle: {
              shadowBlur: 12,
              shadowColor: 'rgba(99,102,241,0.35)',
            },
          },
          itemStyle: {
            borderRadius: [8, 8, 2, 2],
            color: (params: { dataIndex: number }) =>
              barGradient(
                params.dataIndex,
                '#a5b4fc',
                '#6366f1',
                'rgba(167,139,250,0.55)',
                'rgba(99,102,241,0.38)'
              ),
          },
        },
        {
          name: '確定合計本数',
          type: 'bar',
          data: forecastTotal,
          barMaxWidth: 26,
          emphasis: {
            focus: 'series',
            itemStyle: {
              shadowBlur: 12,
              shadowColor: 'rgba(20,184,166,0.35)',
            },
          },
          itemStyle: {
            borderRadius: [8, 8, 2, 2],
            color: (params: { dataIndex: number }) =>
              barGradient(
                params.dataIndex,
                '#5eead4',
                '#0d9488',
                'rgba(45,212,191,0.55)',
                'rgba(20,184,166,0.38)'
              ),
          },
        },
      ],
    },
    { notMerge: true }
  )
  nextTick(() => monthlyEcharts?.resize())
}

async function loadMonthlyChartSeries() {
  chartLoading.value = true
  try {
    const months = past6Future2MonthsJp()
    const results = await Promise.all(
      months.map(({ year, month }) =>
        fetchMonthlySummary({ year, month }).catch(() => emptySummary())
      )
    )
    const labels = months.map((x) => x.label)
    const fu = results.map((r) => Number(r.forecast_units) || 0)
    const ft = results.map((r) => Number(r.forecast_total_units) || 0)
    await nextTick()
    await nextTick()
    renderMonthlyChart(labels, fu, ft)
  } finally {
    chartLoading.value = false
  }
}

/** 当月の全日付を埋め、チャート用系列を生成 */
function buildFullMonthDailyRows(
  y: number,
  m: number,
  agg: Map<string, { count: number; units: number; weekday: string }>
): DailyAggRow[] {
  const pad = (n: number) => String(n).padStart(2, '0')
  const lastDay = new Date(y, m, 0).getDate()
  const rows: DailyAggRow[] = []
  for (let day = 1; day <= lastDay; day++) {
    const dateStr = `${y}-${pad(m)}-${pad(day)}`
    const ex = agg.get(dateStr)
    const dt = new Date(`${dateStr}T12:00:00`)
    const wd = !isNaN(dt.getTime()) ? WD_JA[dt.getDay()] : ''
    rows.push({
      date: dateStr,
      weekday: wd,
      count: ex?.count ?? 0,
      confirmed_units: ex?.units ?? 0,
    })
  }
  return rows
}

function renderDailyChart(rows: DailyAggRow[]) {
  if (!dailyChartRef.value || !rows.length) return
  if (!dailyEcharts) {
    dailyEcharts = echarts.init(dailyChartRef.value, null, { renderer: 'canvas' })
  }

  const asOf = getJapanTodayStr()
  const cats = rows.map((it) => dayjs(it.date).format('MM/DD'))
  const todayIdx = rows.findIndex((it) => it.date === asOf)

  const radiusBar: [number, number, number, number] = [7, 7, 0, 0]
  const barData = rows.map((it) => {
    let color: echarts.graphic.LinearGradient
    if (it.date < asOf) {
      color = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: '#c7d2fe' },
        { offset: 0.55, color: '#818cf8' },
        { offset: 1, color: '#4338ca' },
      ])
    } else if (it.date === asOf) {
      color = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: '#6ee7b7' },
        { offset: 0.5, color: '#34d399' },
        { offset: 1, color: '#047857' },
      ])
    } else {
      color = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: '#f1f5f9' },
        { offset: 1, color: '#94a3b8' },
      ])
    }
    return {
      value: it.confirmed_units,
      itemStyle: {
        color,
        borderRadius: radiusBar,
        shadowBlur: it.date === asOf ? 18 : 10,
        shadowColor:
          it.date === asOf ? 'rgba(4, 120, 87, 0.32)' : 'rgba(67, 56, 202, 0.2)',
        shadowOffsetY: 3,
      },
    }
  })

  dailyEcharts.setOption(
    {
      backgroundColor: 'transparent',
      animationDuration: 680,
      animationEasing: 'cubicOut',
      textStyle: { fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif' },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
          shadowStyle: { color: 'rgba(99, 102, 241, 0.08)' },
        },
        backgroundColor: 'rgba(15, 23, 42, 0.88)',
        borderWidth: 0,
        borderRadius: 10,
        padding: [10, 14],
        textStyle: { color: '#f8fafc', fontSize: 12 },
        formatter: (params: unknown) => {
          const p = Array.isArray(params) ? params[0] : params
          const idx = (p as { dataIndex?: number }).dataIndex ?? 0
          const row = rows[idx]
          if (!row) return ''
          const name = dayjs(row.date).format('YYYY-MM-DD')
          const u = formatInteger(row.confirmed_units, locale.value as LocaleType)
          const c = formatInteger(row.count, locale.value as LocaleType)
          const line1 = t('dashboard.dailyOrderChart.tooltip', { n: u })
          return `<div style="font-weight:600;margin-bottom:4px">${name}（${row.weekday}）</div>
<span style="opacity:.9">${line1}</span><br/><span style="opacity:.85">件数: ${c}</span>`
        },
      },
      grid: { left: 46, right: 14, top: 36, bottom: 48, containLabel: false },
      xAxis: {
        type: 'category',
        data: cats,
        axisLine: { lineStyle: { color: '#e2e8f0', width: 1 } },
        axisTick: { show: false },
        axisLabel: {
          fontSize: 10,
          rotate: 38,
          color: '#64748b',
          margin: 10,
          fontWeight: 500,
        },
      },
      yAxis: {
        type: 'value',
        name: t('dashboard.dailyOrderChart.axis'),
        nameGap: 8,
        nameTextStyle: { fontSize: 11, color: '#94a3b8', fontWeight: 500 },
        axisLabel: { fontSize: 10, color: '#94a3b8' },
        splitLine: {
          lineStyle: { type: 'dashed', color: '#e8ecf1', width: 1 },
        },
        axisLine: { show: false },
      },
      series: [
        {
          type: 'bar',
          barMaxWidth: 26,
          barGap: '28%',
          data: barData,
          label: {
            show: true,
            position: 'top',
            distance: 5,
            fontSize: 9,
            fontWeight: 500,
            color: '#64748b',
            formatter: (p: { data?: { value?: number }; value?: number }) => {
              const v =
                typeof p.data === 'object' && p.data && typeof p.data.value === 'number'
                  ? p.data.value
                  : typeof p.value === 'number'
                    ? p.value
                    : 0
              if (v === 0) return ''
              return formatInteger(v, locale.value as LocaleType)
            },
          },
          emphasis: {
            focus: 'series',
            itemStyle: {
              shadowBlur: 18,
              shadowColor: 'rgba(99, 102, 241, 0.45)',
            },
            label: { fontSize: 10, fontWeight: 600, color: '#475569' },
          },
          markLine:
            todayIdx >= 0
              ? {
                  symbol: 'none',
                  lineStyle: {
                    color: 'rgba(245, 158, 11, 0.95)',
                    type: 'dashed',
                    width: 1.5,
                  },
                  label: {
                    formatter: t('dashboard.dailyOrderChart.today'),
                    color: '#c2410c',
                    fontSize: 10,
                    fontWeight: 600,
                    padding: [2, 8],
                    borderRadius: 6,
                    backgroundColor: 'rgba(254, 243, 199, 0.95)',
                  },
                  data: [{ xAxis: todayIdx }],
                }
              : undefined,
        },
      ],
    },
    { notMerge: true }
  )
  nextTick(() => dailyEcharts?.resize())
}

async function loadDailyChartData() {
  dailyLoading.value = true
  try {
    const d = getJapanDate()
    const y = d.getFullYear()
    const m = d.getMonth() + 1
    const pad = (n: number) => String(n).padStart(2, '0')
    const start = `${y}-${pad(m)}-01`
    const lastDay = new Date(y, m, 0).getDate()
    const end = `${y}-${pad(m)}-${pad(lastDay)}`
    const list = await fetchOrderDailyList({ start_date: start, end_date: end })
    productRankRows.value = aggregateProductRank(list)
    const map = new Map<string, { count: number; units: number; weekday: string }>()
    for (const row of list) {
      const key = row.date
      if (!map.has(key)) {
        let wd = row.weekday || ''
        if (!wd && key) {
          const dt = new Date(`${key}T12:00:00`)
          if (!isNaN(dt.getTime())) wd = WD_JA[dt.getDay()]
        }
        map.set(key, { count: 0, units: 0, weekday: wd })
      }
      const a = map.get(key)!
      a.count += 1
      a.units += Number(row.confirmed_units) || 0
    }
    dailyRows.value = buildFullMonthDailyRows(y, m, map)
    await nextTick()
    await nextTick()
    renderDailyChart(dailyRows.value)
    renderProductRankChart(productRankRows.value)
  } finally {
    dailyLoading.value = false
  }
}

async function loadStats() {
  statsLoading.value = true
  try {
    const d = getJapanDate()
    const summaryRes = await fetchMonthlySummary({
      year: d.getFullYear(),
      month: d.getMonth() + 1,
    })
    Object.assign(summary, summaryRes)
  } finally {
    statsLoading.value = false
  }
}

onMounted(() => {
  loadStats()
  loadMonthlyChartSeries()
  loadDailyChartData()
  window.addEventListener('resize', onChartResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onChartResize)
  disposeMonthlyChart()
  disposeDailyChart()
  disposeProductRankChart()
})
</script>

<style scoped>
.order-home {
  position: relative;
  min-height: 100%;
  padding: 20px 22px 28px;
  overflow: hidden;
  max-width: 1200px;
  margin: 0 auto;
}

.dynamic-background {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.18;
}

.orb-1 {
  width: 380px;
  height: 380px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  top: -120px;
  right: -80px;
}

.orb-2 {
  width: 280px;
  height: 280px;
  background: linear-gradient(135deg, #06b6d4, #22d3ee);
  bottom: 25%;
  left: -60px;
}

.orb-3 {
  width: 220px;
  height: 220px;
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  bottom: -40px;
  right: 15%;
}

.page-head {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 18px;
}

.page-head-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: linear-gradient(145deg, #4f46e5 0%, #7c3aed 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 8px 24px rgba(79, 70, 229, 0.35);
}

.page-head-title {
  font-size: 22px;
  font-weight: 800;
  margin: 0;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.page-head-sub {
  margin: 4px 0 0;
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

/* --- Summary Cards（OrderMonthlyList と同一） --- */
.summary-cards {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
  gap: 8px;
  margin-bottom: 22px;
  min-height: 72px;
}

.summary-cards.animate-in-delay-1 {
  animation: oh-fade-slide-up 0.45s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes oh-fade-slide-up {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.summary-card.modern-card {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.65);
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(14px) saturate(160%);
  -webkit-backdrop-filter: blur(14px) saturate(160%);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}

.summary-card.modern-card:hover {
  transform: translateY(-3px) scale(1.01);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: rgba(99, 102, 241, 0.2);
}

.summary-card :deep(.el-card__body) {
  padding: 10px 12px;
  position: relative;
  overflow: hidden;
}

.card-content {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}

.card-icon {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  font-size: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.card-icon.info-icon {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.card-icon.success-icon {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.card-icon.diff-icon {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
}

.card-icon.plating-icon {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.card-icon.external-plating-icon {
  background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
}

.card-icon.internal-welding-icon {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
}

.card-icon.external-welding-icon {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
}

.card-icon.internal-inspection-icon {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
}

.card-icon.external-inspection-icon {
  background: linear-gradient(135deg, #a855f7 0%, #9333ea 100%);
}

.card-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.summary-title {
  font-size: 10.5px;
  color: #64748b;
  margin-bottom: 1px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
  letter-spacing: 0.2px;
}

.summary-value {
  font-size: 17px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  font-variant-numeric: tabular-nums;
}

.card-decoration {
  position: absolute;
  right: -8px;
  bottom: -8px;
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, transparent 100%);
  border-radius: 50%;
  pointer-events: none;
}

/* --- 月別チャート・日別表 --- */
.analytics-block {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 22px;
}

.analytics-card {
  border-radius: 14px !important;
  border: 1px solid rgba(226, 232, 240, 0.95) !important;
  background: rgba(255, 255, 255, 0.88) !important;
  backdrop-filter: blur(12px);
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.06) !important;
  overflow: hidden;
}

.analytics-card :deep(.el-card__header) {
  padding: 10px 14px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #f8fafc 0%, #fff 100%);
}

.analytics-card :deep(.el-card__body) {
  padding: 12px 14px 14px;
}

.analytics-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.analytics-card-head--chart {
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px 16px;
}

.analytics-card-head-left {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.analytics-card-head-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.analytics-card-head-icon {
  font-size: 20px;
  color: #6366f1;
  flex-shrink: 0;
  margin-top: 2px;
}

.analytics-card-title {
  font-size: 14px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
  line-height: 1.35;
}

.analytics-card-sub {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
  line-height: 1.4;
  max-width: 520px;
}

.chart-legend-hint {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  padding: 6px 10px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.9) 100%);
  border: 1px solid #e2e8f0;
}

.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 5px;
  vertical-align: -1px;
}

.legend-dot--past {
  background: linear-gradient(145deg, #6366f1, #14b8a6);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.legend-dot--future {
  background: linear-gradient(145deg, #a78bfa, #5eead4);
  opacity: 0.85;
  box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.25);
}

.chart-card--premium :deep(.el-card__header) {
  background: linear-gradient(135deg, #fafbff 0%, #f8fafc 45%, #ffffff 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
}

.chart-card--premium :deep(.el-card__body) {
  padding: 0;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 28%);
}

.monthly-chart-shell {
  padding: 8px 12px 14px;
  position: relative;
}

.monthly-chart-shell::before {
  content: '';
  position: absolute;
  inset: 0;
  margin: 8px 12px 14px;
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(99, 102, 241, 0.04) 0%, rgba(20, 184, 166, 0.03) 100%);
  border: 1px solid rgba(226, 232, 240, 0.65);
  pointer-events: none;
  z-index: 0;
}

.monthly-chart-host {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 318px;
}

.chart-card--premium-daily :deep(.el-card__header) {
  background: linear-gradient(135deg, #f6fdfa 0%, #f8fafc 50%, #ffffff 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
}

.chart-card--premium-daily :deep(.el-card__body) {
  padding: 0;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 30%);
}

.daily-chart-shell {
  padding: 8px 12px 14px;
  position: relative;
}

.daily-chart-shell::before {
  content: '';
  position: absolute;
  inset: 0;
  margin: 8px 12px 14px;
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(20, 184, 166, 0.05) 0%, rgba(99, 102, 241, 0.04) 100%);
  border: 1px solid rgba(226, 232, 240, 0.65);
  pointer-events: none;
  z-index: 0;
}

.daily-chart-host {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 340px;
}

.chart-card--premium-rank :deep(.el-card__header) {
  background: linear-gradient(135deg, #faf8ff 0%, #f8fafc 50%, #ffffff 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
}

.chart-card--premium-rank :deep(.el-card__body) {
  padding: 0;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 32%);
}

.product-rank-chart-shell {
  padding: 8px 12px 14px;
  position: relative;
  min-height: 120px;
}

.chart-empty-inline {
  padding: 36px 16px 44px;
}

.product-rank-chart-host {
  position: relative;
  z-index: 1;
  width: 100%;
  min-height: 360px;
  height: 380px;
}

.chart-legend-hint--rank {
  gap: 10px 14px;
}

.legend-dot--rank-top {
  background: linear-gradient(90deg, #fcd34d, #64748b 50%, #a5b4fc);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15);
}

.legend-dot--rank-rest {
  background: linear-gradient(90deg, #a5b4fc, #4338ca);
  box-shadow: 0 0 0 2px rgba(67, 56, 202, 0.18);
}

.chart-legend-hint--daily {
  flex-wrap: wrap;
  gap: 8px 12px;
}

.legend-dot--daily-past {
  background: linear-gradient(180deg, #c7d2fe, #4338ca);
  box-shadow: 0 0 0 2px rgba(67, 56, 202, 0.2);
}

.legend-dot--daily-today {
  background: linear-gradient(180deg, #6ee7b7, #047857);
  box-shadow: 0 0 0 2px rgba(4, 120, 87, 0.22);
}

.legend-dot--daily-future {
  background: linear-gradient(180deg, #f1f5f9, #94a3b8);
  box-shadow: 0 0 0 2px rgba(148, 163, 184, 0.35);
}

/* --- アイコンリング --- */
.icon-ring {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px 4px;
  padding: 20px 16px;
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 18px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
}

.icon-ring-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  text-decoration: none;
  color: inherit;
  border-radius: 16px;
  transition:
    transform 0.2s ease,
    background 0.2s ease;
  min-width: 120px;
}

.icon-ring-item:hover {
  transform: translateY(-3px);
  background: rgba(255, 255, 255, 0.85);
}

.icon-bubble {
  width: 80px;
  height: 80px;
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.15);
}

.icon-ring-item--violet .icon-bubble {
  background: linear-gradient(145deg, #7c3aed 0%, #a78bfa 100%);
}

.icon-ring-item--cyan .icon-bubble {
  background: linear-gradient(145deg, #0891b2 0%, #22d3ee 100%);
}

.icon-ring-item--amber .icon-bubble {
  background: linear-gradient(145deg, #d97706 0%, #fbbf24 100%);
}

.icon-ring-title {
  font-size: 15px;
  font-weight: 800;
  color: #0f172a;
}

.icon-ring-hint {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.icon-ring-connector {
  width: 32px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #cbd5e1, transparent);
  align-self: center;
  margin-top: -28px;
  opacity: 0.9;
}

@media (max-width: 720px) {
  .icon-ring-connector {
    display: none;
  }
}

@media (max-width: 480px) {

  .order-home {
    padding: 14px;
  }

  .page-head-title {
    font-size: 18px;
  }
}
</style>
