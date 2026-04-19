<template>
  <div class="dashboard-home">
    <!-- Welcome Banner -->
    <div class="welcome-banner">
      <div class="welcome-banner__mesh" aria-hidden="true" />
      <div class="welcome-banner__shine" aria-hidden="true" />
      <div class="welcome-content">
        <div class="welcome-avatar-shell">
          <div class="welcome-avatar">
            <el-icon :size="26"><UserFilled /></el-icon>
          </div>
        </div>
        <div class="welcome-copy">
          <h1 class="welcome-title">
            {{ t('dashboard.welcomeBack', { name: userStore.user?.username || t('common.guest') }) }}
          </h1>
          <p class="welcome-tagline">
            <span class="welcome-tagline__dot" aria-hidden="true" />
            <span class="welcome-tagline__text">{{ t('dashboard.welcomeSub') }}</span>
          </p>
        </div>
      </div>
      <div class="welcome-datetime">
        <el-icon class="welcome-datetime__icon"><Clock /></el-icon>
        <span class="welcome-datetime__text">{{ currentDateTime }}</span>
      </div>
    </div>

    <!-- Stats Grid - More Compact -->
    <div class="stats-grid">
      <div 
        v-for="stat in statsCards" 
        :key="stat.key" 
        class="stat-card"
      >
        <div class="stat-icon" :style="{ background: stat.gradient }">
          <el-icon :size="20"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ t('dashboard.stats.' + stat.key) }}</span>
        </div>
      </div>
    </div>

    <!-- 日別受注数量（過去2週・今後1週） -->
    <div class="section chart-block">
      <div class="section-header chart-section-header">
        <el-icon><TrendCharts /></el-icon>
        <div class="chart-title-wrap">
          <span class="chart-main-title">{{ t('dashboard.dailyOrderChart.title') }}</span>
          <span class="chart-sub-title">{{ t('dashboard.dailyOrderChart.subtitle') }}</span>
        </div>
      </div>
      <div class="chart-card chart-card--daily">
        <el-empty
          v-if="!dailyOrderChartHasData"
          :description="t('dashboard.dailyOrderChart.empty')"
          class="chart-empty"
        />
        <div v-show="dailyOrderChartHasData" ref="dailyOrderChartEl" class="daily-order-chart" />
      </div>
    </div>

    <!-- Quick Access Grid -->
    <div class="section">
      <div class="section-header">
        <el-icon><Grid /></el-icon>
        <span>{{ t('dashboard.quickAccess') }}</span>
      </div>
      <div class="quick-grid">
        <router-link
          v-for="item in quickAccessItems"
          :key="item.path"
          :to="item.path"
          class="quick-card"
        >
          <div class="quick-icon" :style="{ background: item.bg }">
            <el-icon :size="22"><component :is="item.icon" /></el-icon>
          </div>
          <div class="quick-content">
            <span class="quick-title">{{ t('dashboard.quick.' + item.titleKey) }}</span>
            <span class="quick-desc">{{ t('dashboard.quick.' + item.descKey) }}</span>
          </div>
          <el-icon class="quick-arrow"><ArrowRight /></el-icon>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, markRaw, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/modules/auth/stores/user'
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import { getSalesStats, getDailyConfirmedSeries } from '@/api/erp/sales'
import type { DailyConfirmedSeries } from '@/api/erp/sales'
import { getInventoryStats } from '@/api/erp/inventory'
import { getActiveProductCount } from '@/api/master/productMaster'
import type { SalesStats } from '@/types/erp/sales'
import type { LocaleType } from '@/i18n'
import { formatInteger } from '@/utils/formatInteger'
import type { InventoryStats } from '@/types/erp/inventory'
import {
  UserFilled, Sell, Box, Document, Clock, List, Grid,
  TrendCharts, Tickets, ArrowRight, Calendar, Van, DataAnalysis, Operation, Tools,
} from '@element-plus/icons-vue'

const { t, locale } = useI18n()
const userStore = useUserStore()

const currentDateTime = ref(dayjs().format('YYYY/MM/DD HH:mm'))
let timer: number | null = null

onUnmounted(() => {
  if (timer) clearInterval(timer)
  disposeDailyOrderChart()
})

interface StatsCard {
  key: 'sales' | 'orders' | 'inventory' | 'products'
  value: string
  icon: object
  gradient: string
}

const statsCards = ref<StatsCard[]>([
  { key: 'sales', value: '¥0', icon: markRaw(TrendCharts), gradient: 'linear-gradient(135deg, #667eea, #764ba2)' },
  { key: 'orders', value: '0', icon: markRaw(Document), gradient: 'linear-gradient(135deg, #f43f5e, #e11d48)' },
  { key: 'inventory', value: '0', icon: markRaw(Box), gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)' },
  { key: 'products', value: '0', icon: markRaw(Sell), gradient: 'linear-gradient(135deg, #10b981, #059669)' },
])

const quickAccessItems = ref([
  { path: '/erp/order/monthly', titleKey: 'monthlyOrder', descKey: 'monthlyOrderDesc', icon: markRaw(Calendar), bg: 'linear-gradient(135deg, #667eea, #764ba2)' },
  { path: '/erp/order/daily', titleKey: 'dailyOrder', descKey: 'dailyOrderDesc', icon: markRaw(Document), bg: 'linear-gradient(135deg, #0ea5e9, #0284c7)' },
  { path: '/erp/shipping/list', titleKey: 'shippingList', descKey: 'shippingListDesc', icon: markRaw(List), bg: 'linear-gradient(135deg, #f43f5e, #e11d48)' },
  { path: '/erp/shipping/report', titleKey: 'shippingReport', descKey: 'shippingReportDesc', icon: markRaw(Van), bg: 'linear-gradient(135deg, #fb7185, #db2777)' },
  { path: '/erp/production/data-management', titleKey: 'productionData', descKey: 'productionDataDesc', icon: markRaw(DataAnalysis), bg: 'linear-gradient(135deg, #10b981, #059669)' },
  { path: '/erp/production/plan-schedules', titleKey: 'scheduling', descKey: 'schedulingDesc', icon: markRaw(Operation), bg: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' },
  { path: '/aps/planning-list', titleKey: 'formingPlanList', descKey: 'formingPlanListDesc', icon: markRaw(Tickets), bg: 'linear-gradient(135deg, #a855f7, #9333ea)' },
  { path: '/aps/welding-planning-list', titleKey: 'weldingPlanList', descKey: 'weldingPlanListDesc', icon: markRaw(Tickets), bg: 'linear-gradient(135deg, #7c3aed, #6d28d9)' },
  { path: '/erp/production/instruction/cutting', titleKey: 'cuttingInstruction', descKey: 'cuttingInstructionDesc', icon: markRaw(Tools), bg: 'linear-gradient(135deg, #f59e0b, #d97706)' },
  { path: '/erp/production/instruction/forming', titleKey: 'formingInstruction', descKey: 'formingInstructionDesc', icon: markRaw(Box), bg: 'linear-gradient(135deg, #06b6d4, #0891b2)' },
  { path: '/erp/production/instruction/welding', titleKey: 'weldingInstruction', descKey: 'weldingInstructionDesc', icon: markRaw(Grid), bg: 'linear-gradient(135deg, #6366f1, #4f46e5)' },
])

const dailyOrderRaw = ref<DailyConfirmedSeries | null>(null)
const dailyOrderChartEl = ref<HTMLDivElement | null>(null)
let dailyOrderChart: echarts.ECharts | null = null

const dailyOrderChartHasData = computed(
  () => (dailyOrderRaw.value?.items?.length ?? 0) > 0,
)

function onDailyOrderChartResize() {
  dailyOrderChart?.resize()
}

function disposeDailyOrderChart() {
  window.removeEventListener('resize', onDailyOrderChartResize)
  if (dailyOrderChart) {
    dailyOrderChart.dispose()
    dailyOrderChart = null
  }
}

function updateDailyOrderChart() {
  const el = dailyOrderChartEl.value
  const raw = dailyOrderRaw.value
  if (!el || !raw?.items?.length) {
    disposeDailyOrderChart()
    return
  }
  if (!dailyOrderChart) {
    dailyOrderChart = echarts.init(el)
    window.addEventListener('resize', onDailyOrderChartResize)
  }

  const asOf = raw.as_of_date
  const cats = raw.items.map((it) => dayjs(it.date).format('MM/DD'))
  const todayIdx = raw.items.findIndex((it) => it.date === asOf)

  const radiusBar: [number, number, number, number] = [7, 7, 0, 0]
  const barData = raw.items.map((it) => {
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

  dailyOrderChart.setOption(
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
          const row = raw.items[idx]
          if (!row) return ''
          const name = dayjs(row.date).format('YYYY-MM-DD')
          const v = row.confirmed_units
          const num = formatInteger(v, locale.value as LocaleType)
          return `<div style="font-weight:600;margin-bottom:4px">${name}</div><span style="opacity:.9">${t('dashboard.dailyOrderChart.tooltip', { n: num })}</span>`
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
    true,
  )
  requestAnimationFrame(() => dailyOrderChart?.resize())
}

const toObjectData = <T>(res: unknown): T => {
  if (res && typeof res === 'object' && 'data' in (res as Record<string, unknown>)) {
    return ((res as { data?: T }).data ?? ({} as T))
  }
  return (res as T) ?? ({} as T)
}

const loadDashboardData = async () => {
  try {
    const [salesRes, inventoryRes, activeProductsRes, dailySeriesRes] = await Promise.all([
      getSalesStats(),
      getInventoryStats(),
      getActiveProductCount(),
      getDailyConfirmedSeries().catch(() => null),
    ])

    dailyOrderRaw.value = dailySeriesRes ? toObjectData<DailyConfirmedSeries>(dailySeriesRes) : null
    await nextTick()
    updateDailyOrderChart()

    const sales = toObjectData<SalesStats>(salesRes)
    const inventory = toObjectData<InventoryStats>(inventoryRes)
    const activeProducts = toObjectData<{ active_count?: number }>(activeProductsRes)

    statsCards.value = [
      {
        key: 'sales',
        value: `¥${(sales?.this_month_amount ?? 0).toLocaleString()}`,
        icon: markRaw(TrendCharts),
        gradient: 'linear-gradient(135deg, #667eea, #764ba2)',
      },
      {
        key: 'orders',
        value: formatInteger(sales?.this_month_orders ?? 0, locale.value as LocaleType),
        icon: markRaw(Document),
        gradient: 'linear-gradient(135deg, #f43f5e, #e11d48)',
      },
      {
        key: 'inventory',
        value: formatInteger(inventory?.summary_stock_qty_today ?? 0, locale.value as LocaleType),
        icon: markRaw(Box),
        gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)',
      },
      {
        key: 'products',
        value: formatInteger(activeProducts?.active_count ?? 0, locale.value as LocaleType),
        icon: markRaw(Sell),
        gradient: 'linear-gradient(135deg, #10b981, #059669)',
      },
    ]
  } catch (error) {
    console.error('dashboard 数据加载失败', error)
  }
}

onMounted(() => {
  timer = window.setInterval(() => {
    currentDateTime.value = dayjs().format('YYYY/MM/DD HH:mm')
  }, 60000)
  loadDashboardData()
})
</script>

<style scoped>
.dashboard-home {
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
  min-height: 100vh;
}

/* Welcome Banner — modern glass + mesh */
.welcome-banner {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  overflow: hidden;
  border-radius: 18px;
  padding: 22px 26px;
  margin-bottom: 16px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(
    125deg,
    #4f46e5 0%,
    #6366f1 28%,
    #7c3aed 58%,
    #5b21b6 100%
  );
  box-shadow:
    0 4px 6px -1px rgba(79, 70, 229, 0.12),
    0 20px 40px -12px rgba(79, 70, 229, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.welcome-banner__mesh {
  pointer-events: none;
  position: absolute;
  inset: 0;
  opacity: 0.55;
  background:
    radial-gradient(ellipse 90% 70% at 10% 20%, rgba(255, 255, 255, 0.35) 0%, transparent 55%),
    radial-gradient(ellipse 70% 60% at 88% 75%, rgba(167, 139, 250, 0.45) 0%, transparent 50%),
    radial-gradient(circle at 50% 100%, rgba(15, 23, 42, 0.15) 0%, transparent 45%);
}

.welcome-banner__shine {
  pointer-events: none;
  position: absolute;
  top: -40%;
  right: -15%;
  width: 55%;
  height: 140%;
  background: linear-gradient(
    115deg,
    transparent 0%,
    rgba(255, 255, 255, 0.07) 40%,
    rgba(255, 255, 255, 0.14) 50%,
    rgba(255, 255, 255, 0.05) 60%,
    transparent 100%
  );
  transform: rotate(-12deg);
}

.welcome-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
}

.welcome-avatar-shell {
  flex-shrink: 0;
  padding: 3px;
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.55), rgba(255, 255, 255, 0.08));
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.2);
}

.welcome-avatar {
  width: 54px;
  height: 54px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #eef2ff;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0.06) 100%);
  backdrop-filter: blur(12px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.welcome-copy {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.welcome-title {
  margin: 0;
  font-size: clamp(1.15rem, 2.5vw, 1.45rem);
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.03em;
  color: #ffffff;
  text-shadow: 0 2px 16px rgba(15, 23, 42, 0.25);
}

.welcome-tagline {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  max-width: 100%;
  width: fit-content;
  padding: 8px 16px 8px 12px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 500;
  letter-spacing: 0.04em;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(15, 23, 42, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(14px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.welcome-tagline__dot {
  flex-shrink: 0;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a5f3fc, #34d399);
  box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.25);
}

.welcome-tagline__text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.welcome-datetime {
  position: relative;
  z-index: 1;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: #f8fafc;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(14px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.welcome-datetime__icon {
  font-size: 16px;
  opacity: 0.95;
}

.welcome-datetime__text {
  font-variant-numeric: tabular-nums;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: white;
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
}

.chart-block {
  margin-bottom: 16px;
}

.chart-section-header {
  align-items: flex-start;
}

.chart-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chart-main-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: 0.02em;
}

.chart-sub-title {
  font-size: 11px;
  color: #64748b;
  font-weight: 400;
}

.chart-card {
  background: white;
  border-radius: 10px;
  padding: 12px 8px 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  min-height: 300px;
  position: relative;
}

.chart-card--daily {
  border-radius: 14px;
  padding: 18px 16px 14px;
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 48%, #f1f5f9 100%);
  border: 1px solid rgba(148, 163, 184, 0.22);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 12px 32px -8px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.85);
  overflow: hidden;
}

.chart-card--daily::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 3px;
  border-radius: 14px 14px 0 0;
  background: linear-gradient(90deg, #6366f1, #8b5cf6 40%, #10b981 100%);
  opacity: 0.85;
  pointer-events: none;
}

.chart-section-header .el-icon {
  margin-top: 2px;
  padding: 8px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(139, 92, 246, 0.1));
  color: #6366f1;
}

.daily-order-chart {
  width: 100%;
  height: 292px;
}

.chart-empty {
  padding: 48px 16px;
}

/* Section */
.section {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 10px;
  padding-left: 2px;
}

.section-header .el-icon {
  color: #667eea;
}

/* Quick Access Grid */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: white;
  border-radius: 10px;
  padding: 12px 14px;
  text-decoration: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

.quick-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
}

.quick-card:hover .quick-arrow {
  transform: translateX(3px);
  color: #667eea;
}

.quick-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.quick-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.quick-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.quick-desc {
  font-size: 10px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-arrow {
  color: #cbd5e1;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

/* Responsive */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .quick-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard-home {
    padding: 12px;
  }
  
  .welcome-banner {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
    padding: 20px 18px;
    text-align: center;
  }

  .welcome-content {
    flex-direction: column;
    align-items: center;
  }

  .welcome-tagline {
    justify-content: center;
    width: 100%;
    max-width: 100%;
  }

  .welcome-tagline__text {
    white-space: normal;
    text-align: center;
    line-height: 1.45;
  }

  .welcome-datetime {
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .quick-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
