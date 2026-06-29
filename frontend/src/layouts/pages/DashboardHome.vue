<template>
  <div class="dashboard-home">
    <el-alert
      v-if="showMenuAccessWarning"
      type="warning"
      :closable="false"
      show-icon
      class="menu-access-alert"
      title="メニュー権限が未設定です"
      description="管理者にロールとメニュー権限の割り当てを依頼してください。現在はダッシュボードのみ利用できます。"
    />

    <!-- Welcome Banner -->
    <div class="welcome-banner">
      <div class="welcome-banner__mesh" aria-hidden="true" />
      <div class="welcome-banner__shine" aria-hidden="true" />
      <div class="welcome-banner__row">
        <div class="welcome-content">
          <div class="welcome-avatar-wrap">
            <div
              class="welcome-avatar"
              :style="{ background: avatarGradient }"
              aria-hidden="true"
            >
              {{ avatarLetter }}
            </div>
          </div>
          <div class="welcome-copy">
            <p class="welcome-greeting">{{ t('dashboard.welcomeGreeting') }}</p>
            <h1 class="welcome-title">
              <span class="welcome-name">{{ displayName }}</span>
              <span v-if="welcomeSuffix" class="welcome-suffix">{{ welcomeSuffix }}</span>
            </h1>
            <div class="welcome-chips">
              <span class="welcome-chip welcome-chip--role">{{ roleDisplay }}</span>
              <span v-if="departmentName" class="welcome-chip welcome-chip--dept">{{ departmentName }}</span>
            </div>
          </div>
        </div>
        <p class="welcome-tagline welcome-tagline--right">
          <span class="welcome-tagline__dot" aria-hidden="true" />
          <span class="welcome-tagline__text">{{ t('dashboard.welcomeSub') }}</span>
        </p>
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
          <el-icon :size="16"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ t('dashboard.stats.' + stat.key) }}</span>
        </div>
      </div>
    </div>

    <!-- 日別受注数量（過去2週・今後1週） -->
    <div class="section chart-block">
      <div class="glass-card chart-card--daily">
        <div class="glass-card__accent glass-card__accent--chart" aria-hidden="true" />
        <div class="chart-card-header">
          <div class="chart-card-header__left">
            <div class="chart-card-header__icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="chart-title-wrap">
              <span class="chart-main-title">{{ t('dashboard.dailyOrderChart.title') }}</span>
              <span class="chart-sub-title">{{ t('dashboard.dailyOrderChart.subtitle') }}</span>
            </div>
          </div>
          <span class="chart-unit">{{ t('dashboard.dailyOrderChart.unitLabel') }}</span>
        </div>
        <div v-if="dailyOrderChartHasData" class="chart-legend">
          <span class="chart-legend-chip">
            <span class="chart-legend-chip__bar chart-legend-chip__bar--past" />
            {{ t('dashboard.dailyOrderChart.legendPast') }}
          </span>
          <span class="chart-legend-chip">
            <span class="chart-legend-chip__bar chart-legend-chip__bar--today" />
            {{ t('dashboard.dailyOrderChart.legendToday') }}
          </span>
          <span class="chart-legend-chip">
            <span class="chart-legend-chip__bar chart-legend-chip__bar--future" />
            {{ t('dashboard.dailyOrderChart.legendFuture') }}
          </span>
        </div>
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
      <div class="glass-card quick-access-card">
        <div class="glass-card__accent glass-card__accent--quick" aria-hidden="true" />
        <div class="section-header section-header--in-card">
          <div class="section-header__icon">
            <el-icon><Grid /></el-icon>
          </div>
          <span>{{ t('dashboard.quickAccess') }}</span>
        </div>
        <div class="quick-grid">
        <router-link
          v-for="item in visibleQuickAccessItems"
          :key="item.path"
          :to="item.path"
          class="quick-card"
          :style="{ '--quick-accent': item.bg }"
        >
          <div class="quick-icon" :style="{ background: item.bg }">
            <el-icon :size="16"><component :is="item.icon" /></el-icon>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, markRaw, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/modules/auth/stores/user'
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import {
  getSalesStats,
  getDailyConfirmedSeries,
  type DailyConfirmedSeries,
  type SalesStats,
} from '@/api/erp/sales'
import { getInventoryStats } from '@/api/erp/inventory'
import { getActiveProductCount } from '@/api/master/productMaster'
import type { LocaleType } from '@/i18n'
import { formatInteger } from '@/utils/formatInteger'
import { canAccessPath, isAdminUser } from '@/utils/menuPermissions'
import { avatarGradientFor, avatarLetterFor } from '@/utils/avatarGradient'
import { displayUserRoleName } from '@/utils/userRoleDisplay'
import type { InventoryStats } from '@/types/erp/inventory'
import {
  Sell, Box, Document, List, Grid,
  TrendCharts, Tickets, ArrowRight, Calendar, Van, DataAnalysis, Operation, Tools,
} from '@element-plus/icons-vue'

const { t, locale } = useI18n()
const userStore = useUserStore()

const displayName = computed(() => {
  const user = userStore.user
  const full = user?.full_name?.trim()
  if (full) return full
  return user?.username || t('common.guest')
})

const avatarLetter = computed(() => avatarLetterFor(displayName.value))
const avatarGradient = computed(() => avatarGradientFor(displayName.value))
const roleDisplay = computed(() => displayUserRoleName(userStore.user, t))
const departmentName = computed(() => userStore.user?.department_name?.trim() || '')
const welcomeSuffix = computed(() => t('dashboard.welcomeSuffix'))

const showMenuAccessWarning = computed(() => {
  const user = userStore.user
  return !!user && !isAdminUser(user) && (user.menu_codes?.length ?? 0) === 0
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
  { path: '/mes/productionInstruction/cutting', titleKey: 'cuttingInstruction', descKey: 'cuttingInstructionDesc', icon: markRaw(Tools), bg: 'linear-gradient(135deg, #f59e0b, #d97706)' },
  { path: '/mes/productionInstruction/forming', titleKey: 'formingInstruction', descKey: 'formingInstructionDesc', icon: markRaw(Box), bg: 'linear-gradient(135deg, #06b6d4, #0891b2)' },
  { path: '/mes/productionInstruction/welding', titleKey: 'weldingInstruction', descKey: 'weldingInstructionDesc', icon: markRaw(Grid), bg: 'linear-gradient(135deg, #6366f1, #4f46e5)' },
])

const visibleQuickAccessItems = computed(() =>
  quickAccessItems.value.filter((item) => canAccessPath(userStore.user, item.path)),
)

const dailyOrderRaw = ref<DailyConfirmedSeries | null>(null)
const dailyOrderChartEl = ref<HTMLDivElement | null>(null)
let dailyOrderChart: echarts.ECharts | null = null

const dailyOrderChartHasData = computed(
  () => (dailyOrderRaw.value?.items?.length ?? 0) > 0,
)

onUnmounted(() => {
  disposeDailyOrderChart()
})

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
          fontSize: 11,
          rotate: 38,
          color: '#64748b',
          margin: 10,
          fontWeight: 500,
        },
      },
      yAxis: {
        type: 'value',
        name: '',
        nameGap: 8,
        nameTextStyle: { fontSize: 11, color: '#94a3b8', fontWeight: 500 },
        axisLabel: { fontSize: 11, color: '#94a3b8' },
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
            fontSize: 10,
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
            label: { fontSize: 11, fontWeight: 600, color: '#475569' },
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
        value: `¥${(sales?.monthly_order_amount ?? 0).toLocaleString()}`,
        icon: markRaw(TrendCharts),
        gradient: 'linear-gradient(135deg, #667eea, #764ba2)',
      },
      {
        key: 'orders',
        value: formatInteger(sales?.monthly_confirmed_units ?? 0, locale.value as LocaleType),
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
  loadDashboardData()
})
</script>

<style scoped>
.menu-access-alert {
  margin-bottom: 12px;
}

.dashboard-home {
  position: relative;
  padding: 16px;
  min-height: 100vh;
  background: linear-gradient(180deg, #eef2ff 0%, #f5f3ff 48%, #ecfeff 100%);
  overflow: hidden;
}

.dashboard-home::before,
.dashboard-home::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(0.5px);
}

.dashboard-home::before {
  width: 280px;
  height: 280px;
  top: -40px;
  left: -60px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.18) 0%, transparent 70%);
}

.dashboard-home::after {
  width: 220px;
  height: 220px;
  top: 120px;
  right: -40px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.14) 0%, transparent 70%);
}

.dashboard-home > * {
  position: relative;
  z-index: 1;
}

/* Welcome Banner */
.welcome-banner {
  position: relative;
  overflow: hidden;
  border-radius: 18px;
  padding: 14px 16px;
  margin-bottom: 12px;
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
  animation: welcome-shine-sweep 3.6s ease-in-out infinite;
}

@keyframes welcome-shine-sweep {
  0% { transform: rotate(-12deg) translateX(-30%); }
  100% { transform: rotate(-12deg) translateX(30%); }
}

.welcome-banner__row {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.welcome-content {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.welcome-avatar-wrap {
  flex-shrink: 0;
  animation: welcome-avatar-float 2.8s ease-in-out infinite;
}

@keyframes welcome-avatar-float {
  0%, 100% { transform: translateY(-3px); }
  50% { transform: translateY(3px); }
}

.welcome-avatar {
  width: 50px;
  height: 50px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
  font-weight: 800;
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow:
    0 6px 16px rgba(15, 23, 42, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.28);
  text-shadow: 0 2px 6px rgba(15, 23, 42, 0.35);
}

.welcome-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.welcome-greeting {
  margin: 0;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.04em;
  color: rgba(255, 255, 255, 0.82);
}

.welcome-title {
  margin: 0;
  display: flex;
  align-items: baseline;
  gap: 2px;
  min-width: 0;
  line-height: 1.2;
}

.welcome-name {
  font-size: clamp(1.05rem, 2.2vw, 1.25rem);
  font-weight: 800;
  letter-spacing: 0.02em;
  background: linear-gradient(
    90deg,
    #f8fafc 0%,
    #e0e7ff 25%,
    #ffffff 50%,
    #c7d2fe 75%,
    #f8fafc 100%
  );
  background-size: 220% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: welcome-name-shimmer 2.8s linear infinite;
  text-shadow: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
  filter: drop-shadow(0 2px 10px rgba(15, 23, 42, 0.25));
}

@keyframes welcome-name-shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

.welcome-suffix {
  flex-shrink: 0;
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.welcome-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.welcome-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: 0.03em;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.welcome-chip--role {
  color: #fff;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.28);
}

.welcome-chip--dept {
  color: rgba(255, 255, 255, 0.88);
  background: rgba(15, 23, 42, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.14);
}

.welcome-tagline {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
  max-width: min(42%, 280px);
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: rgba(255, 255, 255, 0.94);
  background: rgba(31, 41, 55, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.welcome-tagline--right {
  align-self: center;
}

.welcome-tagline__dot {
  flex-shrink: 0;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: radial-gradient(circle, #6ee7b7 0%, #34d399 100%);
  box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.28);
  animation: welcome-dot-pulse 1.4s ease-in-out infinite;
}

@keyframes welcome-dot-pulse {
  0%, 100% { transform: scale(0.88); opacity: 0.85; }
  50% { transform: scale(1); opacity: 1; }
}

.welcome-tagline__text {
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.35;
}

/* Glass card shared */
.glass-card {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.78) 0%, rgba(255, 255, 255, 0.58) 100%);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    0 6px 20px rgba(99, 102, 241, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

.glass-card__accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  pointer-events: none;
}

.glass-card__accent--chart {
  background: linear-gradient(90deg, #6366f1, #8b5cf6 40%, #10b981 100%);
}

.glass-card__accent--quick {
  background: linear-gradient(90deg, #6366f1, #8b5cf6 40%, #06b6d4 100%);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 12px;
  padding: 10px 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.78) 0%, rgba(255, 255, 255, 0.58) 100%);
  border: 1px solid rgba(255, 255, 255, 0.92);
  box-shadow:
    0 5px 16px rgba(99, 102, 241, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 8px 22px rgba(99, 102, 241, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

.stat-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.12);
}

.stat-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.stat-value {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat-label {
  font-size: 9.5px;
  color: #64748b;
  line-height: 1.25;
}

.chart-block {
  margin-bottom: 12px;
}

.chart-card--daily {
  padding: 0 0 10px;
}

.chart-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px 6px;
}

.chart-card-header__left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.chart-card-header__icon {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6366f1;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.14), rgba(139, 92, 246, 0.1));
  border: 1px solid #e2e8f0;
}

.chart-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.chart-main-title {
  font-size: 13px;
  font-weight: 700;
  color: #000;
  letter-spacing: 0.02em;
}

.chart-sub-title {
  font-size: 10px;
  color: #64748b;
  font-weight: 400;
  line-height: 1.2;
}

.chart-unit {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 500;
  color: #94a3b8;
  padding-top: 2px;
}

.chart-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 18px;
  padding: 4px 14px 8px;
}

.chart-legend-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10.5px;
  font-weight: 600;
}

.chart-legend-chip__bar {
  width: 14px;
  height: 8px;
  border-radius: 4px;
}

.chart-legend-chip__bar--past {
  background: linear-gradient(90deg, #818cf8, #4338ca);
  color: #4338ca;
}

.chart-legend-chip:nth-child(1) {
  color: #4338ca;
}

.chart-legend-chip__bar--today {
  background: linear-gradient(90deg, #34d399, #047857);
}

.chart-legend-chip:nth-child(2) {
  color: #047857;
}

.chart-legend-chip__bar--future {
  background: linear-gradient(90deg, #cbd5e1, #94a3b8);
}

.chart-legend-chip:nth-child(3) {
  color: #64748b;
}

.daily-order-chart {
  width: 100%;
  height: 236px;
  padding: 0 8px;
}

.chart-empty {
  padding: 48px 16px;
}

/* Section */
.section {
  margin-bottom: 12px;
}

.quick-access-card {
  padding: 0 0 12px;
}

.section-header--in-card {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #000;
  margin-bottom: 8px;
  padding: 12px 14px 0;
}

.section-header__icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6366f1;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.14), rgba(6, 182, 212, 0.1));
  border: 1px solid #e2e8f0;
}

/* Quick Access Grid */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
  padding: 0 10px;
}

.quick-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 78px;
  border-radius: 12px;
  padding: 8px 6px;
  text-decoration: none;
  text-align: center;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.82) 0%, rgba(255, 255, 255, 0.65) 100%);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  overflow: hidden;
}

.quick-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--quick-accent, linear-gradient(90deg, #6366f1, #8b5cf6));
  opacity: 0.9;
}

.quick-card:hover {
  transform: translateY(-2px) scale(0.99);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.14);
}

.quick-card:hover .quick-arrow {
  transform: translateX(2px);
  opacity: 1;
}

.quick-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 3px 8px rgba(15, 23, 42, 0.12);
}

.quick-content {
  width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.quick-title {
  font-size: 10px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.quick-desc {
  font-size: 8px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-arrow {
  position: absolute;
  right: 5px;
  bottom: 4px;
  color: rgba(99, 102, 241, 0.55);
  opacity: 0.8;
  transition: all 0.15s ease;
  flex-shrink: 0;
  font-size: 10px;
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

  .welcome-banner__row {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .welcome-content {
    align-items: flex-start;
  }

  .welcome-tagline--right {
    align-self: flex-end;
    max-width: 100%;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .quick-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
