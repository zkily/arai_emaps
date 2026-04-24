<template>
  <div class="sales-page-shell sales-home">
    <div class="sales-page-hero">
      <div class="sales-page-hero__mesh" aria-hidden="true" />
      <div class="sales-page-hero__content">
        <div class="sales-page-hero__icon">
          <el-icon :size="28"><Sell /></el-icon>
        </div>
        <div class="sales-page-hero__titles">
          <h1 class="sales-page-hero__title">{{ t('salesPages.salesHome.title') }}</h1>
          <p class="sales-page-hero__subtitle">{{ t('salesPages.salesHome.subtitle') }}</p>
        </div>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card" v-for="stat in statsCards" :key="stat.key">
        <div class="stat-icon" :style="{ background: stat.gradient }">
          <el-icon :size="20"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.label }}</span>
          <span v-if="stat.change" class="stat-change" :class="stat.changeType">
            <el-icon v-if="stat.changeType === 'up'"><Top /></el-icon>
            <el-icon v-else-if="stat.changeType === 'down'"><Bottom /></el-icon>
            {{ stat.change }}
          </span>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-header">
        <el-icon><Grid /></el-icon>
        <span>{{ t('dashboard.quickAccess') }}</span>
      </div>
      <div class="module-grid">
        <router-link
          v-for="module in salesModules"
          :key="module.path"
          :to="module.path"
          class="module-card"
        >
          <div class="module-icon" :style="{ background: module.gradient }">
            <el-icon :size="26"><component :is="module.icon" /></el-icon>
          </div>
          <div class="module-info">
            <h3 class="module-title">{{ module.title }}</h3>
            <p class="module-desc">{{ module.description }}</p>
          </div>
          <el-icon class="module-arrow"><ArrowRight /></el-icon>
        </router-link>
      </div>
    </div>

    <div class="section">
      <div class="two-col">
        <el-card class="panel-card" shadow="never">
          <div class="panel-head">
            <el-icon><Van /></el-icon>
            <span>{{ t('salesPages.salesHome.pendingShipTitle') }}</span>
            <el-badge
              v-if="pendingDeliveries.length > 0"
              :value="pendingDeliveries.length"
              type="warning"
            />
          </div>
          <el-table :data="pendingDeliveries" v-loading="loading" stripe size="small">
            <el-table-column prop="order_no" :label="t('salesPages.common.orderNo')" width="120" />
            <el-table-column prop="customer_name" :label="t('salesPages.common.customer')" min-width="120" />
            <el-table-column prop="expected_delivery_date" :label="t('salesPages.salesHome.colShipDue')" width="110" />
            <el-table-column :label="t('salesPages.common.actions')" width="88">
              <template #default="{ row }">
                <el-button size="small" type="success" link @click="deliverOrder(row)">
                  {{ t('salesPages.salesHome.ship') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card class="panel-card" shadow="never">
          <div class="panel-head">
            <el-icon><Money /></el-icon>
            <span>{{ t('salesPages.salesHome.unpaidTitle') }}</span>
            <el-badge v-if="unpaidOrders.length > 0" :value="unpaidOrders.length" type="danger" />
          </div>
          <el-table :data="unpaidOrders" v-loading="loading" stripe size="small">
            <el-table-column prop="order_no" :label="t('salesPages.common.orderNo')" width="120" />
            <el-table-column prop="customer_name" :label="t('salesPages.common.customer')" min-width="120" />
            <el-table-column prop="total_amount" :label="t('salesPages.salesHome.colAmount')" width="112" align="right">
              <template #default="{ row }">
                ¥{{ formatDecimal(row.total_amount ?? 0, locale as LocaleType, 0) }}
              </template>
            </el-table-column>
            <el-table-column :label="t('salesPages.common.actions')" width="88">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="viewOrder(row)">
                  {{ t('salesPages.common.detail') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </div>

    <div class="section">
      <div class="section-header">
        <el-icon><TrendCharts /></el-icon>
        <span>{{ t('salesPages.salesHome.chartTitle') }}</span>
      </div>
      <el-card class="chart-card" shadow="never">
        <el-empty :description="t('salesPages.salesHome.chartEmpty')">
          <el-button type="primary" @click="fetchChartData">{{ t('salesPages.salesHome.chartReload') }}</el-button>
        </el-empty>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  Sell,
  ArrowRight,
  Top,
  Bottom,
  Van,
  Money,
  TrendCharts,
  Document,
  List,
  Tickets,
  DataAnalysis,
  User,
  Grid,
} from '@element-plus/icons-vue'
import { getSalesStats, getSalesOrderList } from '@/api/erp/sales'
import type { SalesStats, SalesOrder } from '@/types/erp/sales'
import type { LocaleType } from '@/i18n'
import { formatInteger, formatDecimal } from '@/utils/formatInteger'

const router = useRouter()
const { t, locale } = useI18n()
const loading = ref(false)
const stats = ref<SalesStats | null>(null)
const pendingDeliveries = ref<SalesOrder[]>([])
const unpaidOrders = ref<SalesOrder[]>([])

function amountMomRate(s: SalesStats | null): number | null {
  if (!s?.last_month_amount) return null
  return ((s.this_month_amount - s.last_month_amount) / s.last_month_amount) * 100
}

const statsCards = computed(() => {
  const s = stats.value
  const ordersMom = s?.month_over_month_rate ?? 0
  const amtMom = amountMomRate(s)
  return [
    {
      key: 'total_orders',
      label: t('salesPages.salesHome.statOrders'),
      value: formatInteger(s?.this_month_orders ?? 0, locale.value as LocaleType),
      icon: markRaw(Document),
      gradient: 'linear-gradient(135deg, #409eff, #67c23a)',
      change: t('salesPages.salesHome.momLabel', { n: formatDecimal(ordersMom, locale.value as LocaleType, 1) }),
      changeType: ordersMom >= 0 ? 'up' : 'down',
    },
    {
      key: 'total_amount',
      label: t('salesPages.salesHome.statAmount'),
      value: `¥${formatDecimal(s?.this_month_amount ?? 0, locale.value as LocaleType, 0)}`,
      icon: markRaw(DataAnalysis),
      gradient: 'linear-gradient(135deg, #67c23a, #85ce61)',
      change:
        amtMom == null
          ? ''
          : t('salesPages.salesHome.momLabel', { n: formatDecimal(amtMom, locale.value as LocaleType, 1) }),
      changeType: amtMom == null ? '' : amtMom >= 0 ? 'up' : 'down',
    },
    {
      key: 'pending_orders',
      label: t('salesPages.salesHome.statPending'),
      value: formatInteger(s?.pending_orders ?? 0, locale.value as LocaleType),
      icon: markRaw(Van),
      gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)',
      change: '',
      changeType: '',
    },
    {
      key: 'avg_order',
      label: t('salesPages.salesHome.statAvg'),
      value: `¥${formatDecimal(s?.average_order_value ?? 0, locale.value as LocaleType, 0)}`,
      icon: markRaw(TrendCharts),
      gradient: 'linear-gradient(135deg, #9254de, #b37feb)',
      change: '',
      changeType: '',
    },
  ]
})

const salesModules = computed(() => [
  {
    path: '/erp/sales/quotation',
    title: t('salesPages.salesHome.modules.quotation.title'),
    description: t('salesPages.salesHome.modules.quotation.desc'),
    icon: markRaw(Document),
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)',
  },
  {
    path: '/erp/sales/orders',
    title: t('salesPages.salesHome.modules.orders.title'),
    description: t('salesPages.salesHome.modules.orders.desc'),
    icon: markRaw(List),
    gradient: 'linear-gradient(135deg, #409eff, #67c23a)',
  },
  {
    path: '/erp/order/monthly',
    title: t('salesPages.salesHome.modules.monthlyOrder.title'),
    description: t('salesPages.salesHome.modules.monthlyOrder.desc'),
    icon: markRaw(Tickets),
    gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)',
  },
  {
    path: '/erp/sales/forecast',
    title: t('salesPages.salesHome.modules.forecast.title'),
    description: t('salesPages.salesHome.modules.forecast.desc'),
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #a18cd1, #fbc2eb)',
  },
  {
    path: '/erp/sales/credit',
    title: t('salesPages.salesHome.modules.credit.title'),
    description: t('salesPages.salesHome.modules.credit.desc'),
    icon: markRaw(User),
    gradient: 'linear-gradient(135deg, #f56c6c, #f78989)',
  },
  {
    path: '/erp/sales/contract-pricing',
    title: t('salesPages.salesHome.modules.contractPricing.title'),
    description: t('salesPages.salesHome.modules.contractPricing.desc'),
    icon: markRaw(Tickets),
    gradient: 'linear-gradient(135deg, #9254de, #b37feb)',
  },
  {
    path: '/erp/sales/shipping',
    title: t('salesPages.salesHome.modules.shipping.title'),
    description: t('salesPages.salesHome.modules.shipping.desc'),
    icon: markRaw(Van),
    gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)',
  },
  {
    path: '/erp/sales/recording',
    title: t('salesPages.salesHome.modules.recording.title'),
    description: t('salesPages.salesHome.modules.recording.desc'),
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #67c23a, #85ce61)',
  },
  {
    path: '/erp/sales/invoice',
    title: t('salesPages.salesHome.modules.invoice.title'),
    description: t('salesPages.salesHome.modules.invoice.desc'),
    icon: markRaw(Document),
    gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)',
  },
  {
    path: '/erp/sales/return-correction',
    title: t('salesPages.salesHome.modules.returnCorrection.title'),
    description: t('salesPages.salesHome.modules.returnCorrection.desc'),
    icon: markRaw(TrendCharts),
    gradient: 'linear-gradient(135deg, #f56c6c, #f78989)',
  },
])

const viewOrder = (row: SalesOrder) => {
  router.push(`/erp/sales/orders/${row.id}`)
}

const deliverOrder = (row: SalesOrder) => {
  router.push(`/erp/sales/deliveries/new?order_id=${row.id}`)
}

const fetchChartData = () => {
  ElMessage.info(t('salesPages.salesHome.chartWip'))
}

const fetchData = async () => {
  loading.value = true
  try {
    const [statsRes, deliveriesRes, unpaidRes] = await Promise.all([
      getSalesStats(),
      getSalesOrderList({ status: 'approved', page_size: 5 }),
      getSalesOrderList({ payment_status: 'unpaid', page_size: 5 } as Record<string, unknown>),
    ])
    stats.value = statsRes as SalesStats
    const delBody = deliveriesRes as { items?: SalesOrder[] }
    const unBody = unpaidRes as { items?: SalesOrder[] }
    pendingDeliveries.value = delBody.items ?? []
    unpaidOrders.value = unBody.items ?? []
  } catch (error) {
    console.error(t('salesPages.salesHome.fetchFailed'), error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped src="@/views/erp/sales/sales-page-shell.scss"></style>

<style scoped>
.sales-home {
  padding-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: #fff;
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 17px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
}

.stat-change {
  font-size: 11px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}

.stat-change.up {
  color: #16a34a;
}
.stat-change.down {
  color: #dc2626;
}

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
}

.section-header .el-icon {
  color: #6366f1;
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.module-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #fff;
  border-radius: 12px;
  text-decoration: none;
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.module-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.12);
}

.module-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.module-info {
  flex: 1;
  min-width: 0;
}

.module-title {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.module-desc {
  margin: 0;
  font-size: 11px;
  color: #64748b;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.module-arrow {
  color: #cbd5e1;
  flex-shrink: 0;
}

.two-col {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.panel-card :deep(.el-card__body) {
  padding: 14px 16px 16px;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.chart-card :deep(.el-card__body) {
  padding: 24px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 1200px) {
  .stats-grid,
  .module-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid,
  .module-grid,
  .two-col {
    grid-template-columns: 1fr;
  }
}
</style>
