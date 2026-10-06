<template>
  <section ref="rootRef" class="analysis">
    <header class="analysis-head">
      <div class="analysis-title">
        <span class="analysis-icon"><el-icon><DataAnalysis /></el-icon></span>
        <div class="analysis-copy">
          <h3>在庫分析</h3>
          <p>
            {{ monthLabel }}1日〜基準日 {{ asOf }}<template v-if="ledger.stockScopeNote">・{{ ledger.stockScopeNote }}</template>
          </p>
        </div>
      </div>
      <div class="insights">
        <div class="insight insight--net">
          <span class="insight__label">当月純増減</span>
          <span class="insight__value">{{ signed(netChange) }}</span>
        </div>
        <div class="insight insight--rate">
          <span class="insight__label">当月不良率</span>
          <span class="insight__value">{{ overallDefectRate }}</span>
        </div>
        <div class="insight insight--cover">
          <span class="insight__label">在庫消化見込</span>
          <span class="insight__value">{{ overallCoverLabel }}</span>
        </div>
        <div class="insight insight--stale" :class="{ 'is-alert': staleCount > 0 }">
          <span class="insight__label">滞留（14日以上）</span>
          <span class="insight__value">{{ staleCount }}<small>件</small></span>
        </div>
      </div>
    </header>

    <div class="grid">
      <article class="card span-8">
        <div class="card-head">
          <span class="card-icon card-icon--violet"><el-icon><TrendCharts /></el-icon></span>
          <span class="card-title">日別在庫推移</span>
          <small class="card-sub">現在庫合計（線）と日別の注文・受入・不良（棒）</small>
        </div>
        <div class="chart-box">
          <div ref="trendRef" class="chart chart--lg" />
          <div v-if="!hasTrend" class="chart-empty">当月のデータがありません</div>
        </div>
      </article>

      <article class="card span-4">
        <div class="card-head">
          <span class="card-icon card-icon--cyan"><el-icon><PieChart /></el-icon></span>
          <span class="card-title">外注先別 在庫構成</span>
          <small class="card-sub">現在庫（プラス分）</small>
        </div>
        <div class="chart-box">
          <div ref="donutRef" class="chart chart--lg" />
          <div v-if="!supplierStock.length" class="chart-empty">在庫がありません</div>
        </div>
      </article>

      <article class="card span-6">
        <div class="card-head">
          <span class="card-icon card-icon--purple"><el-icon><Histogram /></el-icon></span>
          <span class="card-title">在庫上位 TOP10</span>
          <small class="card-sub">外注先手元の在庫が多い品目</small>
        </div>
        <div class="chart-box">
          <div ref="topRef" class="chart chart--md" />
          <div v-if="!topItems.length" class="chart-empty">在庫がありません</div>
        </div>
      </article>

      <article class="card span-6">
        <div class="card-head">
          <span class="card-icon card-icon--indigo"><el-icon><Switch /></el-icon></span>
          <span class="card-title">外注先別 当月フロー</span>
          <small class="card-sub">注文（出し）と受入・不良（戻り）の比較</small>
        </div>
        <div class="chart-box">
          <div ref="flowRef" class="chart chart--md" />
          <div v-if="!hasFlow" class="chart-empty">当月の入出庫がありません</div>
        </div>
      </article>

      <article class="card span-6">
        <div class="card-head">
          <span class="card-icon card-icon--rose"><el-icon><Warning /></el-icon></span>
          <span class="card-title">不良率ランキング</span>
          <small class="card-sub">当月 不良数 ÷（受入数＋不良数）</small>
        </div>
        <ul v-if="defectRanking.length" class="rank-list">
          <li v-for="(item, i) in defectRanking" :key="item.key" class="rank-item">
            <span class="rank-no" :class="`rank-no--${Math.min(i + 1, 4)}`">{{ i + 1 }}</span>
            <div class="rank-main">
              <div class="rank-name">
                <span class="rank-product">{{ item.product_name }}</span>
                <span class="rank-supplier">{{ item.supplier_name }}</span>
              </div>
              <div class="rank-bar">
                <span class="rank-bar__fill" :style="{ width: `${item.barWidth}%` }" />
              </div>
            </div>
            <div class="rank-stat">
              <span class="rank-rate">{{ formatRate(item.rate) }}</span>
              <span class="rank-detail">{{ formatNum(item.defect) }} / {{ formatNum(item.total) }}</span>
            </div>
          </li>
        </ul>
        <div v-else class="list-empty">
          <el-icon><CircleCheckFilled /></el-icon>当月の不良はありません
        </div>
      </article>

      <article class="card span-6">
        <div class="card-head">
          <span class="card-icon card-icon--amber"><el-icon><AlarmClock /></el-icon></span>
          <span class="card-title">滞留アラート</span>
          <small class="card-sub">在庫があり受入が止まっている品目</small>
        </div>
        <div v-if="staleList.length" class="stale-table">
          <div class="stale-row stale-row--head">
            <span>製品名</span>
            <span class="t-right">在庫</span>
            <span class="t-center">最終受入から</span>
            <span class="t-center">消化見込</span>
          </div>
          <div v-for="item in staleList" :key="item.key" class="stale-row">
            <span class="stale-name">
              <span class="rank-product">{{ item.product_name }}</span>
              <span class="rank-supplier">{{ item.supplier_name }}</span>
            </span>
            <span class="t-right stale-stock">{{ formatNum(item.stock) }}</span>
            <span class="t-center">
              <span class="days-badge" :class="`days-badge--${item.level}`">
                {{ item.days == null ? '受入なし' : `${item.days}日` }}
              </span>
            </span>
            <span class="t-center stale-cover">{{ item.cover == null ? '—' : `約${item.cover}日` }}</span>
          </div>
        </div>
        <div v-else class="list-empty">
          <el-icon><CircleCheckFilled /></el-icon>在庫のある品目はありません
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  AlarmClock,
  CircleCheckFilled,
  DataAnalysis,
  Histogram,
  PieChart,
  Switch,
  TrendCharts,
  Warning,
} from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import type { EChartsOption } from '@/utils/echarts'
import type { PlatingStockItem, PlatingStockTrendItem } from '@/api/outsourcing'
import { useLedger } from './ledgerContext'

const ledger = useLedger()

const props = defineProps<{
  rows: PlatingStockItem[]
  trend: PlatingStockTrendItem[]
  asOf: string
}>()

const C = {
  order: '#6366f1',
  recv: '#10b981',
  defect: '#f43f5e',
  stock: '#8b5cf6',
  axis: '#94a3b8',
  grid: '#f1f5f9',
  text: '#475569',
}
const PALETTE = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e', '#6366f1', '#14b8a6', '#ec4899']
// 最終受入からこの日数以上を滞留とみなす
const STALE_DAYS = 14

const rootRef = ref<HTMLElement | null>(null)
const trendRef = ref<HTMLDivElement | null>(null)
const donutRef = ref<HTMLDivElement | null>(null)
const topRef = ref<HTMLDivElement | null>(null)
const flowRef = ref<HTMLDivElement | null>(null)

function formatNum(value: number | null | undefined): string {
  return Number(value || 0).toLocaleString()
}

function signed(value: number): string {
  if (value > 0) return `+${formatNum(value)}`
  return formatNum(value)
}

function formatRate(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`
}

function parseYmd(ymd: string): Date {
  const [y, m, d] = ymd.split('-').map(Number)
  return new Date(y, m - 1, d)
}

function daysBetween(from: string, to: string): number {
  return Math.round((parseYmd(to).getTime() - parseYmd(from).getTime()) / 86_400_000)
}

const monthLabel = computed(() => {
  if (!props.asOf) return ''
  const [y, m] = props.asOf.split('-')
  return `${y}年${Number(m)}月`
})

const elapsedDays = computed(() => (props.asOf ? parseYmd(props.asOf).getDate() : 1))

const sums = computed(() => {
  let order = 0
  let recv = 0
  let defect = 0
  let stock = 0
  for (const r of props.rows) {
    order += r.month_order_qty || 0
    recv += r.month_receiving_qty || 0
    defect += r.month_defect_qty || 0
    stock += Math.max(r.current_stock || 0, 0)
  }
  return { order, recv, defect, stock }
})

const netChange = computed(() => sums.value.order - sums.value.recv - sums.value.defect)

const overallDefectRate = computed(() => {
  const total = sums.value.recv + sums.value.defect
  return total > 0 ? formatRate(sums.value.defect / total) : '—'
})

// 当月の1日あたり戻り数（受入＋不良）で現在庫を割った日数
function coverDays(stock: number, monthOut: number): number | null {
  if (stock <= 0 || monthOut <= 0) return null
  return Math.round(stock / (monthOut / elapsedDays.value))
}

const overallCoverLabel = computed(() => {
  const days = coverDays(sums.value.stock, sums.value.recv + sums.value.defect)
  return days == null ? '—' : `約${days}日`
})

// ---------- 日別推移 ----------
const hasTrend = computed(() =>
  props.trend.some((d) => d.current_stock || d.order_qty || d.receiving_qty || d.defect_qty),
)

const trendOption = computed<EChartsOption>(() => {
  const labels = props.trend.map((d) => {
    const dt = parseYmd(d.date)
    return `${dt.getMonth() + 1}/${dt.getDate()}`
  })
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(139, 92, 246, 0.06)' } },
      valueFormatter: (v) => formatNum(Number(v)),
    },
    legend: {
      top: 0,
      right: 4,
      icon: 'roundRect',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { fontSize: 11, color: C.text },
    },
    grid: { left: 8, right: 8, top: 34, bottom: 4, containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: C.axis, fontSize: 10 },
    },
    yAxis: [
      {
        type: 'value',
        name: '入出庫',
        nameTextStyle: { color: C.axis, fontSize: 10 },
        splitLine: { lineStyle: { color: C.grid } },
        axisLabel: { color: C.axis, fontSize: 10 },
      },
      {
        type: 'value',
        name: '在庫',
        nameTextStyle: { color: C.axis, fontSize: 10 },
        splitLine: { show: false },
        axisLabel: { color: C.axis, fontSize: 10 },
      },
    ],
    series: [
      {
        name: '注文',
        type: 'bar',
        stack: 'in',
        barMaxWidth: 12,
        itemStyle: { color: C.order, borderRadius: [3, 3, 0, 0] },
        data: props.trend.map((d) => d.order_qty),
      },
      {
        name: '受入',
        type: 'bar',
        stack: 'out',
        barMaxWidth: 12,
        itemStyle: { color: C.recv },
        data: props.trend.map((d) => d.receiving_qty),
      },
      {
        name: '不良',
        type: 'bar',
        stack: 'out',
        barMaxWidth: 12,
        itemStyle: { color: C.defect, borderRadius: [3, 3, 0, 0] },
        data: props.trend.map((d) => d.defect_qty),
      },
      {
        name: '現在庫',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        showSymbol: props.trend.length <= 16,
        lineStyle: { width: 2.5, color: C.stock },
        itemStyle: { color: C.stock },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(139, 92, 246, 0.28)' },
            { offset: 1, color: 'rgba(139, 92, 246, 0.02)' },
          ]),
        },
        data: props.trend.map((d) => d.current_stock),
      },
    ],
  }
})

// ---------- 外注先別構成 ----------
const supplierStock = computed(() => {
  const map = new Map<string, number>()
  for (const r of props.rows) {
    const stock = Math.max(r.current_stock || 0, 0)
    if (stock <= 0) continue
    const name = r.supplier_name || r.supplier_cd
    map.set(name, (map.get(name) || 0) + stock)
  }
  return [...map.entries()].map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value)
})

const donutOption = computed<EChartsOption>(() => ({
  color: PALETTE,
  tooltip: {
    trigger: 'item',
    formatter: (p: any) => `${p.marker}${p.name}<br/><b>${formatNum(p.value)}</b>（${p.percent}%）`,
  },
  legend: {
    type: 'scroll',
    bottom: 0,
    icon: 'circle',
    itemWidth: 8,
    itemHeight: 8,
    textStyle: { fontSize: 11, color: C.text },
  },
  title: {
    text: formatNum(sums.value.stock),
    subtext: '現在庫合計',
    left: 'center',
    top: '33%',
    itemGap: 2,
    textStyle: { fontSize: 20, fontWeight: 800, color: '#5b21b6' },
    subtextStyle: { fontSize: 11, color: C.axis },
  },
  series: [
    {
      type: 'pie',
      radius: ['54%', '76%'],
      center: ['50%', '44%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { scale: true, scaleSize: 6 },
      data: supplierStock.value,
    },
  ],
}))

// ---------- TOP10 ----------
const topItems = computed(() =>
  [...props.rows]
    .filter((r) => (r.current_stock || 0) > 0)
    .sort((a, b) => b.current_stock - a.current_stock)
    .slice(0, 10),
)

function shortName(name: string, max = 14): string {
  return name.length > max ? `${name.slice(0, max)}…` : name
}

const topOption = computed<EChartsOption>(() => {
  const items = [...topItems.value].reverse()
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(139, 92, 246, 0.06)' } },
      formatter: (params: any) => {
        const item = items[params[0].dataIndex]
        if (!item) return ''
        return `${item.product_name}（${item.product_cd}）<br/>${item.supplier_name}<br/>現在庫 <b>${formatNum(item.current_stock)}</b>`
      },
    },
    grid: { left: 8, right: 52, top: 6, bottom: 4, containLabel: true },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: C.grid } },
      axisLabel: { color: C.axis, fontSize: 10 },
    },
    yAxis: {
      type: 'category',
      data: items.map((r) => shortName(r.product_name || r.product_cd)),
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: { color: '#334155', fontSize: 11 },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 14,
        data: items.map((r) => r.current_stock),
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#c4b5fd' },
            { offset: 1, color: '#7c3aed' },
          ]),
        },
        label: {
          show: true,
          position: 'right',
          color: '#5b21b6',
          fontSize: 11,
          fontWeight: 700,
          formatter: (p: any) => formatNum(p.value),
        },
      },
    ],
  }
})

// ---------- 外注先別フロー ----------
const supplierFlow = computed(() => {
  const map = new Map<string, { order: number; recv: number; defect: number }>()
  for (const r of props.rows) {
    const name = r.supplier_name || r.supplier_cd
    const it = map.get(name) || { order: 0, recv: 0, defect: 0 }
    it.order += r.month_order_qty || 0
    it.recv += r.month_receiving_qty || 0
    it.defect += r.month_defect_qty || 0
    map.set(name, it)
  }
  return [...map.entries()].map(([name, v]) => ({ name, ...v }))
})

const hasFlow = computed(() => supplierFlow.value.some((s) => s.order || s.recv || s.defect))

const flowOption = computed<EChartsOption>(() => {
  const list = supplierFlow.value
  const bar = (name: string, color: string, data: number[]) => ({
    name,
    type: 'bar' as const,
    barMaxWidth: 18,
    barGap: '15%',
    itemStyle: { color, borderRadius: [4, 4, 0, 0] },
    label: {
      show: true,
      position: 'top' as const,
      fontSize: 10,
      color: C.text,
      formatter: (p: any) => (p.value ? formatNum(p.value) : ''),
    },
    data,
  })
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(99, 102, 241, 0.06)' } },
      valueFormatter: (v) => formatNum(Number(v)),
    },
    legend: {
      top: 0,
      right: 4,
      icon: 'roundRect',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { fontSize: 11, color: C.text },
    },
    grid: { left: 8, right: 8, top: 34, bottom: 4, containLabel: true },
    xAxis: {
      type: 'category',
      data: list.map((s) => s.name),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#334155', fontSize: 11, interval: 0, overflow: 'truncate', width: 110 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: C.grid } },
      axisLabel: { color: C.axis, fontSize: 10 },
    },
    series: [
      bar('注文', C.order, list.map((s) => s.order)),
      bar('受入', C.recv, list.map((s) => s.recv)),
      bar('不良', C.defect, list.map((s) => s.defect)),
    ],
  }
})

// ---------- 不良率ランキング ----------
const defectRanking = computed(() => {
  const list = props.rows
    .map((r) => {
      const defect = r.month_defect_qty || 0
      const total = (r.month_receiving_qty || 0) + defect
      return {
        key: `${r.supplier_cd}:${r.product_cd}`,
        product_name: r.product_name || r.product_cd,
        supplier_name: r.supplier_name || r.supplier_cd,
        defect,
        total,
        rate: total > 0 ? defect / total : 0,
      }
    })
    .filter((r) => r.defect > 0)
    .sort((a, b) => b.rate - a.rate || b.defect - a.defect)
    .slice(0, 8)
  const max = list[0]?.rate || 1
  return list.map((r) => ({ ...r, barWidth: Math.max((r.rate / max) * 100, 4) }))
})

// ---------- 滞留アラート ----------
const staleCandidates = computed(() =>
  props.rows
    .filter((r) => (r.current_stock || 0) > 0)
    .map((r) => {
      const days = r.last_receiving_date ? daysBetween(r.last_receiving_date, props.asOf) : null
      const level = days == null || days >= 30 ? 'danger' : days >= STALE_DAYS ? 'warn' : 'ok'
      return {
        key: `${r.supplier_cd}:${r.product_cd}`,
        product_name: r.product_name || r.product_cd,
        supplier_name: r.supplier_name || r.supplier_cd,
        stock: r.current_stock,
        days,
        level,
        cover: coverDays(r.current_stock, (r.month_receiving_qty || 0) + (r.month_defect_qty || 0)),
      }
    }),
)

const staleCount = computed(
  () => staleCandidates.value.filter((r) => r.days == null || r.days >= STALE_DAYS).length,
)

const staleList = computed(() =>
  [...staleCandidates.value]
    .sort((a, b) => {
      const da = a.days ?? Number.MAX_SAFE_INTEGER
      const db = b.days ?? Number.MAX_SAFE_INTEGER
      return db - da || b.stock - a.stock
    })
    .slice(0, 8),
)

// ---------- ECharts ----------
function render(el: HTMLDivElement | null, option: EChartsOption) {
  if (!el) return
  const chart = echarts.getInstanceByDom(el) ?? echarts.init(el)
  chart.setOption(option, true)
}

function renderAll() {
  render(trendRef.value, trendOption.value)
  render(donutRef.value, donutOption.value)
  render(topRef.value, topOption.value)
  render(flowRef.value, flowOption.value)
}

function chartEls(): HTMLDivElement[] {
  return [trendRef.value, donutRef.value, topRef.value, flowRef.value].filter(
    (el): el is HTMLDivElement => !!el,
  )
}

let resizeObserver: ResizeObserver | null = null

onMounted(async () => {
  await nextTick()
  renderAll()
  resizeObserver = new ResizeObserver(() => {
    for (const el of chartEls()) echarts.getInstanceByDom(el)?.resize()
  })
  if (rootRef.value) resizeObserver.observe(rootRef.value)
})

watch([trendOption, donutOption, topOption, flowOption], renderAll, { flush: 'post' })

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  for (const el of chartEls()) echarts.getInstanceByDom(el)?.dispose()
})
</script>

<style scoped>
.analysis {
  margin-top: 12px;
}

/* ---------- 見出し ---------- */
.analysis-head {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-bottom: 10px;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid #e4dcfb;
  background:
    radial-gradient(circle at 92% -40%, rgba(167, 139, 250, 0.28), transparent 55%),
    linear-gradient(120deg, #faf7ff 0%, #f5f3ff 45%, #eef6ff 100%);
}

.analysis-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.analysis-icon {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 18px;
  color: #fff;
  background: linear-gradient(135deg, #a78bfa, #6d28d9);
  box-shadow: 0 6px 14px -6px rgba(109, 40, 217, 0.6);
}

.analysis-copy h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #4c1d95;
}

.analysis-copy p {
  margin: 1px 0 0;
  font-size: 11.5px;
  color: #7c6f9b;
}

.insights {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.insight {
  --i: #6d28d9;
  min-width: 112px;
  display: flex;
  flex-direction: column;
  padding: 5px 12px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--i) 22%, #fff);
  background: rgba(255, 255, 255, 0.78);
}

.insight__label {
  font-size: 10.5px;
  font-weight: 600;
  white-space: nowrap;
  color: #64748b;
}

.insight__value {
  font-size: 16px;
  font-weight: 800;
  line-height: 1.25;
  white-space: nowrap;
  color: var(--i);
  font-variant-numeric: tabular-nums;
}

.insight__value small {
  margin-left: 2px;
  font-size: 11px;
  font-weight: 600;
}

.insight--net {
  --i: #4338ca;
}

.insight--rate {
  --i: #be123c;
}

.insight--cover {
  --i: #0e7490;
}

.insight--stale {
  --i: #64748b;
}

.insight--stale.is-alert {
  --i: #b45309;
  background: #fffbeb;
}

/* ---------- カードグリッド ---------- */
.grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 10px;
}

.span-4 {
  grid-column: span 4;
}

.span-6 {
  grid-column: span 6;
}

.span-8 {
  grid-column: span 8;
}

.card {
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 10px 12px 12px;
  border-radius: 12px;
  border: 1px solid #e6edf3;
  background: #fff;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -22px rgba(76, 29, 149, 0.45);
  transition:
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.card:hover {
  border-color: #ddd6fe;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 14px 28px -20px rgba(76, 29, 149, 0.5);
}

.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  min-width: 0;
}

.card-icon {
  --c: #8b5cf6;
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  font-size: 13px;
  color: var(--c);
  background: color-mix(in srgb, var(--c) 14%, #fff);
}

.card-icon--violet {
  --c: #7c3aed;
}

.card-icon--cyan {
  --c: #0891b2;
}

.card-icon--purple {
  --c: #9333ea;
}

.card-icon--indigo {
  --c: #4f46e5;
}

.card-icon--rose {
  --c: #e11d48;
}

.card-icon--amber {
  --c: #d97706;
}

.card-title {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 800;
  color: #1e293b;
}

.card-sub {
  overflow: hidden;
  font-size: 11px;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: #94a3b8;
}

.chart-box {
  position: relative;
}

.chart {
  width: 100%;
}

.chart--lg {
  height: 280px;
}

.chart--md {
  height: 300px;
}

.chart-empty,
.list-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
}

.chart-empty {
  position: absolute;
  inset: 0;
  border-radius: 10px;
  background: repeating-linear-gradient(-45deg, #fafbfd 0 10px, #f6f8fb 10px 20px);
}

.list-empty {
  min-height: 120px;
  flex: 1;
  border-radius: 10px;
  background: #f8fafc;
}

.list-empty .el-icon {
  font-size: 16px;
  color: #34d399;
}

/* ---------- 不良率ランキング ---------- */
.rank-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  border-radius: 9px;
  transition: background-color 0.15s ease;
}

.rank-item:hover {
  background: #fff5f7;
}

.rank-no {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  font-size: 11.5px;
  font-weight: 800;
  color: #64748b;
  background: #f1f5f9;
}

.rank-no--1 {
  color: #fff;
  background: linear-gradient(135deg, #fb7185, #e11d48);
}

.rank-no--2 {
  color: #fff;
  background: linear-gradient(135deg, #fda4af, #f43f5e);
}

.rank-no--3 {
  color: #be123c;
  background: #ffe4e6;
}

.rank-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rank-name,
.stale-name {
  display: flex;
  align-items: baseline;
  gap: 6px;
  min-width: 0;
}

.rank-product {
  overflow: hidden;
  font-size: 12.5px;
  font-weight: 700;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: #1e293b;
}

.rank-supplier {
  flex-shrink: 0;
  font-size: 11px;
  color: #94a3b8;
}

.rank-bar {
  height: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: #fde8ec;
}

.rank-bar__fill {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #fda4af, #e11d48);
}

.rank-stat {
  flex-shrink: 0;
  min-width: 78px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.rank-rate {
  font-size: 14px;
  font-weight: 800;
  color: #be123c;
  font-variant-numeric: tabular-nums;
}

.rank-detail {
  font-size: 10.5px;
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

/* ---------- 滞留アラート ---------- */
.stale-table {
  display: flex;
  flex-direction: column;
}

.stale-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 76px 96px 84px;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-bottom: 1px dashed #eef2f6;
  font-size: 12px;
}

.stale-row:last-child {
  border-bottom: none;
}

.stale-row:not(.stale-row--head):hover {
  border-radius: 8px;
  background: #fffbeb;
}

.stale-row--head {
  padding-top: 2px;
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  border-bottom: 1px solid #eef2f6;
}

.t-right {
  text-align: right;
}

.t-center {
  text-align: center;
}

.stale-stock {
  font-weight: 800;
  color: #5b21b6;
  font-variant-numeric: tabular-nums;
}

.stale-cover {
  color: #0e7490;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.days-badge {
  display: inline-block;
  min-width: 56px;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.days-badge--ok {
  color: #047857;
  background: #d1fae5;
}

.days-badge--warn {
  color: #b45309;
  background: #fef3c7;
}

.days-badge--danger {
  color: #be123c;
  background: #ffe4e6;
}

/* ---------- レスポンシブ ---------- */
@media (max-width: 1280px) {
  .span-4,
  .span-6,
  .span-8 {
    grid-column: span 12;
  }
}
</style>
