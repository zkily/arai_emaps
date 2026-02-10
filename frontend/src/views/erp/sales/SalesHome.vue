<template>
  <div class="sales-home">
    <!-- 动态背景 -->
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <!-- 页面头部 -->
    <div class="modern-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="32"><Sell /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">販売管理</h1>
            <div class="header-subtitle">Sales Management</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card modern-card" v-for="stat in statsCards" :key="stat.key">
        <div class="stat-icon" :style="{ background: stat.gradient }">
          <el-icon :size="24"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-change" :class="stat.changeType">
            <el-icon v-if="stat.changeType === 'up'"><Top /></el-icon>
            <el-icon v-else-if="stat.changeType === 'down'"><Bottom /></el-icon>
            {{ stat.change }}
          </div>
        </div>
      </div>
    </div>

    <!-- 功能入口 -->
    <div class="module-grid">
      <router-link
        v-for="module in modules"
        :key="module.path"
        :to="module.path"
        class="module-card modern-card"
      >
        <div class="module-icon" :style="{ background: module.gradient }">
          <el-icon :size="32"><component :is="module.icon" /></el-icon>
        </div>
        <div class="module-info">
          <h3 class="module-title">{{ module.title }}</h3>
          <p class="module-desc">{{ module.description }}</p>
        </div>
        <el-icon class="module-arrow"><ArrowRight /></el-icon>
      </router-link>
    </div>

    <!-- 待处理事项 -->
    <div class="pending-section">
      <div class="section-row">
        <!-- 待发货订单 -->
        <div class="section-card modern-card">
          <div class="section-header">
            <el-icon><Van /></el-icon>
            <span>出荷待ち</span>
            <el-badge :value="pendingDeliveries.length" type="warning" v-if="pendingDeliveries.length > 0" />
          </div>
          <el-table :data="pendingDeliveries" v-loading="loading" stripe size="small">
            <el-table-column prop="order_no" label="受注番号" width="120" />
            <el-table-column prop="customer_name" label="顧客" min-width="120" />
            <el-table-column prop="expected_delivery_date" label="出荷予定" width="100" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button size="small" type="success" link @click="deliverOrder(row)">出荷</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 未收款订单 -->
        <div class="section-card modern-card">
          <div class="section-header">
            <el-icon><Money /></el-icon>
            <span>入金待ち</span>
            <el-badge :value="unpaidOrders.length" type="danger" v-if="unpaidOrders.length > 0" />
          </div>
          <el-table :data="unpaidOrders" v-loading="loading" stripe size="small">
            <el-table-column prop="order_no" label="受注番号" width="120" />
            <el-table-column prop="customer_name" label="顧客" min-width="120" />
            <el-table-column prop="total_amount" label="金額" width="100" align="right">
              <template #default="{ row }">
                ¥{{ row.total_amount?.toLocaleString() }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="viewOrder(row)">詳細</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <!-- 销售趋势图 -->
    <div class="chart-section modern-card">
      <div class="section-header">
        <el-icon><TrendCharts /></el-icon>
        <span>売上推移</span>
      </div>
      <div class="chart-container" ref="chartContainer">
        <!-- 图表占位 -->
        <div class="chart-placeholder">
          <el-empty description="グラフデータを読み込み中...">
            <el-button type="primary" @click="fetchChartData">再読み込み</el-button>
          </el-empty>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Sell, ArrowRight, Top, Bottom, Van, Money, TrendCharts,
  Document, List, Tickets, DataAnalysis, User
} from '@element-plus/icons-vue'
import { getSalesStats, getSalesOrderList } from '@/api/erp/sales'
import type { SalesStats, SalesOrder } from '@/types/erp/sales'

const router = useRouter()
const loading = ref(false)
const stats = ref<SalesStats | null>(null)
const pendingDeliveries = ref<SalesOrder[]>([])
const unpaidOrders = ref<SalesOrder[]>([])
const chartContainer = ref<HTMLElement | null>(null)

// 统计卡片配置
const statsCards = computed(() => [
  {
    key: 'total_orders',
    label: '今月受注件数',
    value: stats.value?.this_month_orders?.toString() || '0',
    icon: markRaw(Document),
    gradient: 'linear-gradient(135deg, #409eff, #67c23a)',
    change: `${stats.value?.month_over_month_rate || 0}%`,
    changeType: (stats.value?.month_over_month_rate || 0) >= 0 ? 'up' : 'down'
  },
  {
    key: 'total_amount',
    label: '今月売上金額',
    value: `¥${(stats.value?.this_month_amount || 0).toLocaleString()}`,
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #67c23a, #85ce61)',
    change: '+12%',
    changeType: 'up'
  },
  {
    key: 'pending_orders',
    label: '出荷待ち',
    value: stats.value?.pending_orders?.toString() || '0',
    icon: markRaw(Van),
    gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)',
    change: '',
    changeType: ''
  },
  {
    key: 'avg_order',
    label: '平均受注額',
    value: `¥${(stats.value?.average_order_value || 0).toLocaleString()}`,
    icon: markRaw(TrendCharts),
    gradient: 'linear-gradient(135deg, #9254de, #b37feb)',
    change: '+5%',
    changeType: 'up'
  }
])

// 機能モジュール配置 - 見積・引合
const quotationModules = [
  {
    path: '/erp/sales/quotation',
    title: '見積管理',
    description: '見積作成・過去参照・原価積算・PDF出力',
    icon: markRaw(Document),
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)'
  }
]

// 機能モジュール配置 - 受注管理
const orderModules = [
  {
    path: '/erp/sales/orders',
    title: '受注一覧',
    description: '受注データ登録・与信チェック・在庫引当・納期回答(ATP)',
    icon: markRaw(List),
    gradient: 'linear-gradient(135deg, #409eff, #67c23a)'
  },
  {
    path: '/erp/order/monthly',
    title: 'EDI取込',
    description: '月受注画面の「EDI取込」ボタンから顧客フォーマット(CSV/XML)取込',
    icon: markRaw(Tickets),
    gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)'
  },
  {
    path: '/erp/sales/forecast',
    title: '内示・フォーキャスト',
    description: '確定前の需要予測をAPSへ連携',
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #a18cd1, #fbc2eb)'
  },
  {
    path: '/erp/sales/credit',
    title: '与信管理',
    description: '受注時の限度額チェック・アラート',
    icon: markRaw(User),
    gradient: 'linear-gradient(135deg, #f56c6c, #f78989)'
  },
  {
    path: '/erp/sales/contract-pricing',
    title: '契約単価管理',
    description: '期間別・数量別ボリュームディスカウント',
    icon: markRaw(Tickets),
    gradient: 'linear-gradient(135deg, #9254de, #b37feb)'
  }
]

// 機能モジュール配置 - 出荷管理
const shippingModules = [
  {
    path: '/erp/sales/shipping',
    title: '出荷指示',
    description: '出荷指図書・ピッキングリスト・分納管理',
    icon: markRaw(Van),
    gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)'
  }
]

// 機能モジュール配置 - 売上・請求管理
const billingModules = [
  {
    path: '/erp/sales/recording',
    title: '売上計上',
    description: '出荷基準/検収基準の切替',
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #67c23a, #85ce61)'
  },
  {
    path: '/erp/sales/invoice',
    title: '請求書発行',
    description: 'インボイス対応・電子請求書送信',
    icon: markRaw(Document),
    gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)'
  },
  {
    path: '/erp/sales/return-correction',
    title: '赤黒訂正処理',
    description: '返品・値引き時の伝票修正',
    icon: markRaw(TrendCharts),
    gradient: 'linear-gradient(135deg, #f56c6c, #f78989)'
  }
]

// 全機能モジュール(互換性のため)
const modules = [...quotationModules, ...orderModules, ...shippingModules, ...billingModules]

// 查看订单
const viewOrder = (row: SalesOrder) => {
  router.push(`/erp/sales/orders/${row.id}`)
}

// 发货
const deliverOrder = (row: SalesOrder) => {
  router.push(`/erp/sales/deliveries/new?order_id=${row.id}`)
}

// 加载图表数据
const fetchChartData = () => {
  ElMessage.info('グラフ機能は開発中です')
}

// 加载数据
const fetchData = async () => {
  loading.value = true
  try {
    const [statsRes, deliveriesRes, unpaidRes] = await Promise.all([
      getSalesStats(),
      getSalesOrderList({ status: 'approved', page_size: 5 }),
      getSalesOrderList({ payment_status: 'unpaid', page_size: 5 } as any)
    ])
    stats.value = statsRes.data || statsRes
    pendingDeliveries.value = (deliveriesRes.data?.items || deliveriesRes.items || []) as SalesOrder[]
    unpaidOrders.value = (unpaidRes.data?.items || unpaidRes.items || []) as SalesOrder[]
  } catch (error) {
    console.error('データ取得に失敗しました', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.sales-home {
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

.dynamic-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(45deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  animation: float 20s ease-in-out infinite;
}

.orb-1 { width: 300px; height: 300px; top: -150px; right: -150px; }
.orb-2 { width: 200px; height: 200px; bottom: -100px; left: -100px; animation-delay: -10s; }
.orb-3 { width: 250px; height: 250px; top: 50%; left: 50%; transform: translate(-50%, -50%); animation-delay: -15s; }

@keyframes float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  33% { transform: translateY(-30px) rotate(120deg); }
  66% { transform: translateY(30px) rotate(240deg); }
}

.modern-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #67c23a, #85ce61);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.header-title {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0;
}

.header-subtitle {
  font-size: 14px;
  color: #8492a6;
}

.modern-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.modern-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #8492a6;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
}

.stat-change {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
}

.stat-change.up { color: #67c23a; }
.stat-change.down { color: #f56c6c; }

/* 功能模块 */
.module-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.module-card {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  text-decoration: none;
  cursor: pointer;
}

.module-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.module-info {
  flex: 1;
}

.module-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 4px 0;
}

.module-desc {
  font-size: 13px;
  color: #8492a6;
  margin: 0;
}

.module-arrow {
  color: #c0c4cc;
  font-size: 20px;
}

/* 待处理区域 */
.pending-section {
  margin-bottom: 24px;
}

.section-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.section-card {
  padding: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

/* 图表区域 */
.chart-section {
  padding: 24px;
}

.chart-container {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  text-align: center;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid, .module-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .section-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid, .module-grid {
    grid-template-columns: 1fr;
  }
}
</style>
