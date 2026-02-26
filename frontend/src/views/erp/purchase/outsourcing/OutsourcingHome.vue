<template>
  <div class="dashboard-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <DataBoard class="title-icon" />
            外注ダッシュボード
          </h1>
          <span class="subtitle">外注管理の全体状況</span>
        </div>
        <el-button @click="fetchAllData" :loading="loading">
          <Refresh class="btn-icon" />
          更新
        </el-button>
      </div>
    </div>

    <!-- 統計カード -->
    <div class="stats-grid">
      <div class="stat-card today-orders">
        <div class="stat-icon">
          <List />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.todayOrders }}</div>
          <div class="stat-label">本日の注文</div>
        </div>
        <div class="stat-detail">
          <span>メッキ: {{ dashboardData?.todayOrders?.plating_orders || 0 }}</span>
          <span>溶接: {{ dashboardData?.todayOrders?.welding_orders || 0 }}</span>
        </div>
      </div>

      <div class="stat-card pending-orders">
        <div class="stat-icon">
          <Clock />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.pendingOrders }}</div>
          <div class="stat-label">未完了注文</div>
        </div>
        <div class="stat-detail">
          <span>メッキ: {{ dashboardData?.pendingOrders?.plating_pending || 0 }}</span>
          <span>溶接: {{ dashboardData?.pendingOrders?.welding_pending || 0 }}</span>
        </div>
      </div>

      <div class="stat-card today-receivings">
        <div class="stat-icon">
          <CircleCheck />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.todayReceivings }}</div>
          <div class="stat-label">本日の受入</div>
        </div>
        <div class="stat-detail">
          <span>メッキ: {{ dashboardData?.todayReceivings?.plating_receivings || 0 }}</span>
          <span>溶接: {{ dashboardData?.todayReceivings?.welding_receivings || 0 }}</span>
        </div>
      </div>

      <div class="stat-card stock-alerts" :class="{ 'has-alert': stats.stockAlerts > 0 }">
        <div class="stat-icon">
          <Warning />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.stockAlerts }}</div>
          <div class="stat-label">在庫警告</div>
        </div>
        <div class="stat-detail">
          <span>メッキ: {{ dashboardData?.stockAlerts?.plating_alerts || 0 }}</span>
          <span>溶接: {{ dashboardData?.stockAlerts?.welding_alerts || 0 }}</span>
          <span>材料: {{ dashboardData?.stockAlerts?.material_alerts || 0 }}</span>
        </div>
      </div>

      <div class="stat-card overdue-orders" :class="{ 'has-alert': stats.overdueOrders > 0 }">
        <div class="stat-icon">
          <WarningFilled />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.overdueOrders }}</div>
          <div class="stat-label">納期遅延</div>
        </div>
        <div class="stat-detail">
          <span>メッキ: {{ dashboardData?.overdueOrders?.plating_overdue || 0 }}</span>
          <span>溶接: {{ dashboardData?.overdueOrders?.welding_overdue || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- メインコンテンツ -->
    <div class="main-content">
      <!-- 直近の納期一覧 -->
      <div class="content-card deliveries-card">
        <div class="card-header">
          <h3 class="card-title">
            <Calendar class="card-icon" />
            直近の納期一覧（7日以内）
          </h3>
        </div>
        <div class="card-body">
          <el-table :data="upcomingDeliveries" stripe size="small" max-height="300" empty-text="データがありません">
            <el-table-column prop="type" label="種別" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.type === 'plating' ? 'warning' : 'danger'" size="small">
                  {{ row.type === 'plating' ? 'メッキ' : '溶接' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="order_no" label="注文番号" width="130" />
            <el-table-column prop="product_cd" label="品番" width="120" />
            <el-table-column prop="supplier_name" label="外注先" min-width="140" show-overflow-tooltip />
            <el-table-column prop="quantity" label="数量" width="80" align="right" />
            <el-table-column label="残数" width="80" align="right">
              <template #default="{ row }">
                {{ row.quantity - row.received_qty }}
              </template>
            </el-table-column>
            <el-table-column prop="delivery_date" label="納期" width="110" />
            <el-table-column prop="days_remaining" label="残日数" width="80" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="row.days_remaining <= 1 ? 'danger' : row.days_remaining <= 3 ? 'warning' : 'success'"
                  size="small"
                >
                  {{ row.days_remaining }}日
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 外注先別サマリー -->
      <div class="content-card suppliers-card">
        <div class="card-header">
          <h3 class="card-title">
            <OfficeBuilding class="card-icon" />
            外注先別サマリー
          </h3>
        </div>
        <div class="card-body">
          <el-table :data="supplierSummary" stripe size="small" max-height="300" empty-text="データがありません">
            <el-table-column prop="supplier_cd" label="コード" width="100" />
            <el-table-column prop="supplier_name" label="外注先名" min-width="150" show-overflow-tooltip />
            <el-table-column prop="supplier_type" label="種別" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="getTypeTagColor(row.supplier_type) as 'success' | 'primary' | 'warning' | 'info' | 'danger'" size="small">
                  {{ getTypeLabel(row.supplier_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="メッキ注文" width="90" align="center">
              <template #default="{ row }">
                <span :class="{ 'has-value': row.plating_order_count > 0 }">
                  {{ row.plating_order_count || 0 }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="溶接注文" width="90" align="center">
              <template #default="{ row }">
                <span :class="{ 'has-value': row.welding_order_count > 0 }">
                  {{ row.welding_order_count || 0 }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="支給材料在庫" width="110" align="right">
              <template #default="{ row }">
                {{ row.supplied_material_stock?.toLocaleString() || 0 }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <!-- クイックアクセス -->
    <div class="quick-access">
      <h3 class="section-title">クイックアクセス</h3>
      <div class="quick-buttons">
        <router-link to="/erp/purchase/outsourcing/plating-order" class="quick-btn plating">
          <Star class="quick-icon" />
          <span>メッキ注文</span>
        </router-link>
        <router-link to="/erp/purchase/outsourcing/welding-order" class="quick-btn welding">
          <TrendCharts class="quick-icon" />
          <span>溶接注文</span>
        </router-link>
        <router-link to="/erp/purchase/outsourcing/plating-receiving" class="quick-btn receiving">
          <CircleCheck class="quick-icon" />
          <span>メッキ受入</span>
        </router-link>
        <router-link to="/erp/purchase/outsourcing/welding-receiving" class="quick-btn receiving">
          <CircleCheck class="quick-icon" />
          <span>溶接受入</span>
        </router-link>
        <router-link to="/erp/purchase/outsourcing/material-issue" class="quick-btn issue">
          <Delete class="quick-icon" />
          <span>材料支給</span>
        </router-link>
        <router-link to="/erp/purchase/outsourcing/stock" class="quick-btn stock">
          <Box class="quick-icon" />
          <span>在庫管理</span>
        </router-link>
        <router-link to="/erp/purchase/outsourcing/suppliers" class="quick-btn suppliers">
          <OfficeBuilding class="quick-icon" />
          <span>外注先マスタ</span>
        </router-link>
        <router-link to="/erp/purchase/outsourcing/process-products" class="quick-btn process-products">
          <DataBoard class="quick-icon" />
          <span>外注工程製品</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataBoard,
  Refresh,
  List,
  Clock,
  CircleCheck,
  Warning,
  WarningFilled,
  Calendar,
  OfficeBuilding,
  Star,
  TrendCharts,
  Delete,
  Box,
} from '@element-plus/icons-vue'
import {
  getOutsourcingDashboard,
  getUpcomingDeliveries,
  getSupplierSummary,
} from '@/api/outsourcing'

// 状态
const loading = ref(false)
const dashboardData = ref<any>(null)
const upcomingDeliveries = ref<any[]>([])
const supplierSummary = ref<any[]>([])

// 计算属性
const stats = computed(() => ({
  todayOrders: (dashboardData.value?.todayOrders?.plating_orders || 0) +
               (dashboardData.value?.todayOrders?.welding_orders || 0),
  pendingOrders: (dashboardData.value?.pendingOrders?.plating_pending || 0) +
                 (dashboardData.value?.pendingOrders?.welding_pending || 0),
  todayReceivings: (dashboardData.value?.todayReceivings?.plating_receivings || 0) +
                   (dashboardData.value?.todayReceivings?.welding_receivings || 0),
  stockAlerts: (dashboardData.value?.stockAlerts?.plating_alerts || 0) +
               (dashboardData.value?.stockAlerts?.welding_alerts || 0) +
               (dashboardData.value?.stockAlerts?.material_alerts || 0),
  overdueOrders: (dashboardData.value?.overdueOrders?.plating_overdue || 0) +
                 (dashboardData.value?.overdueOrders?.welding_overdue || 0),
}))

// 方法（request 拦截器已返回 response.data，故 res 即为 body: { success, data }）
const fetchAllData = async () => {
  loading.value = true
  try {
    const [dashboardRes, deliveriesRes, summaryRes] = await Promise.all([
      getOutsourcingDashboard(),
      getUpcomingDeliveries(7),
      getSupplierSummary(),
    ]) as Array<{ success?: boolean; data?: unknown }>

    if (dashboardRes?.success && dashboardRes.data) {
      dashboardData.value = dashboardRes.data as Record<string, unknown>
    }
    if (deliveriesRes?.success) {
      upcomingDeliveries.value = Array.isArray(deliveriesRes.data) ? deliveriesRes.data : []
    }
    if (summaryRes?.success) {
      supplierSummary.value = Array.isArray(summaryRes.data) ? summaryRes.data : []
    }
  } catch (error) {
    console.error('データ取得エラー:', error)
    ElMessage.error('データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    plating: 'メッキ',
    welding: '溶接',
    both: '両方',
  }
  return labels[type] || type
}

const getTypeTagColor = (type: string) => {
  const colors: Record<string, string> = {
    plating: 'warning',
    welding: 'danger',
    both: 'primary',
  }
  return colors[type] || 'info'
}

onMounted(() => {
  fetchAllData()
})
</script>

<style scoped lang="scss">
.dashboard-page {
  padding: 20px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  min-height: calc(100vh - 60px);
}

.page-header {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .title-section {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .page-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.6rem;
    font-weight: 700;
    color: #fff;
    margin: 0;

    .title-icon {
      width: 32px;
      height: 32px;
      color: #4facfe;
    }
  }

  .subtitle {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.9rem;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;

    svg {
      width: 24px;
      height: 24px;
      color: #fff;
    }
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: #fff;
    line-height: 1;
  }

  .stat-label {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.9rem;
    margin-top: 4px;
  }

  .stat-detail {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.6);

    span {
      background: rgba(255, 255, 255, 0.1);
      padding: 2px 8px;
      border-radius: 4px;
    }
  }

  &.today-orders .stat-icon { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
  &.pending-orders .stat-icon { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
  &.today-receivings .stat-icon { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
  &.stock-alerts .stat-icon { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
  &.overdue-orders .stat-icon { background: linear-gradient(135deg, #ff0844 0%, #ffb199 100%); }

  &.has-alert {
    border-color: rgba(255, 99, 71, 0.5);
    animation: pulse 2s infinite;
  }
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 99, 71, 0.4); }
  50% { box-shadow: 0 0 20px 10px rgba(255, 99, 71, 0.2); }
}

.main-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.content-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);

  .card-header {
    padding: 16px 20px;
    border-bottom: 1px solid #eee;
    background: #f8f9fa;
  }

  .card-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1rem;
    font-weight: 600;
    color: #1a1a2e;
    margin: 0;

    .card-icon {
      width: 20px;
      height: 20px;
      color: #667eea;
    }
  }

  .card-body {
    padding: 16px;
  }
}

.quick-access {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);

  .section-title {
    color: #fff;
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0 0 16px 0;
  }

  .quick-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .quick-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 20px;
    border-radius: 12px;
    color: #fff;
    text-decoration: none;
    font-weight: 500;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }

    .quick-icon {
      width: 20px;
      height: 20px;
    }

    &.plating { background: linear-gradient(135deg, #f5af19 0%, #f12711 100%); }
    &.welding { background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%); }
    &.receiving { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
    &.issue { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    &.stock { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    &.suppliers { background: linear-gradient(135deg, #5c6bc0 0%, #3949ab 100%); }
    &.process-products { background: linear-gradient(135deg, #26a69a 0%, #00897b 100%); }
  }
}

.btn-icon {
  width: 16px;
  height: 16px;
  margin-right: 4px;
}

.has-value {
  font-weight: 600;
  color: #409eff;
}
</style>
