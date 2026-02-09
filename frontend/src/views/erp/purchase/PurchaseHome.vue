<template>
  <div class="purchase-home">
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
            <el-icon size="32"><ShoppingCart /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">購買管理</h1>
            <div class="header-subtitle">Purchase Management</div>
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
        <!-- 待审批订单 -->
        <div class="section-card modern-card">
          <div class="section-header">
            <el-icon><Clock /></el-icon>
            <span>承認待ち発注</span>
            <el-badge :value="pendingOrders.length" type="warning" v-if="pendingOrders.length > 0" />
          </div>
          <el-table :data="pendingOrders" v-loading="loading" stripe size="small">
            <el-table-column prop="order_no" label="発注番号" width="120" />
            <el-table-column prop="supplier_name" label="仕入先" min-width="120" />
            <el-table-column prop="total_amount" label="金額" width="100" align="right">
              <template #default="{ row }">
                ¥{{ row.total_amount?.toLocaleString() }}
              </template>
            </el-table-column>
            <el-table-column prop="order_date" label="発注日" width="100" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="viewOrder(row)">詳細</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 待收货订单 -->
        <div class="section-card modern-card">
          <div class="section-header">
            <el-icon><Van /></el-icon>
            <span>入荷待ち</span>
            <el-badge :value="pendingReceipts.length" type="info" v-if="pendingReceipts.length > 0" />
          </div>
          <el-table :data="pendingReceipts" v-loading="loading" stripe size="small">
            <el-table-column prop="order_no" label="発注番号" width="120" />
            <el-table-column prop="supplier_name" label="仕入先" min-width="120" />
            <el-table-column prop="expected_delivery_date" label="入荷予定" width="100" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button size="small" type="success" link @click="receiveOrder(row)">入荷</el-button>
              </template>
            </el-table-column>
          </el-table>
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
  ShoppingCart, ArrowRight, Top, Bottom, Clock, Van,
  Document, List, Tickets, DataAnalysis, User
} from '@element-plus/icons-vue'
import { getPurchaseStats, getPurchaseOrderList } from '@/api/erp/purchase'
import type { PurchaseStats, PurchaseOrder } from '@/types/erp/purchase'

const router = useRouter()
const loading = ref(false)
const stats = ref<PurchaseStats | null>(null)
const pendingOrders = ref<PurchaseOrder[]>([])
const pendingReceipts = ref<PurchaseOrder[]>([])

// 统计卡片配置
const statsCards = computed(() => [
  {
    key: 'total_orders',
    label: '今月発注件数',
    value: stats.value?.this_month_orders?.toString() || '0',
    icon: markRaw(Document),
    gradient: 'linear-gradient(135deg, #409eff, #67c23a)',
    change: `${stats.value?.month_over_month_rate || 0}%`,
    changeType: (stats.value?.month_over_month_rate || 0) >= 0 ? 'up' : 'down'
  },
  {
    key: 'total_amount',
    label: '今月発注金額',
    value: `¥${(stats.value?.this_month_amount || 0).toLocaleString()}`,
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #67c23a, #85ce61)',
    change: '+8%',
    changeType: 'up'
  },
  {
    key: 'pending_orders',
    label: '承認待ち',
    value: stats.value?.pending_orders?.toString() || '0',
    icon: markRaw(Clock),
    gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)',
    change: '',
    changeType: ''
  },
  {
    key: 'completed_orders',
    label: '完了件数',
    value: stats.value?.completed_orders?.toString() || '0',
    icon: markRaw(Tickets),
    gradient: 'linear-gradient(135deg, #909399, #b1b3b8)',
    change: '',
    changeType: ''
  }
])

// 機能モジュール - 発注プロセス
const orderModules = [
  {
    path: '/erp/purchase/orders',
    title: '発注一覧',
    description: '発注登録・PDF自動送信・分納・承認WF',
    icon: markRaw(List),
    gradient: 'linear-gradient(135deg, #409eff, #67c23a)'
  },
  {
    path: '/erp/purchase/rfq',
    title: '見積依頼(RFQ)',
    description: 'サプライヤー相見積もり・比較表作成',
    icon: markRaw(Document),
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)'
  }
]

// 機能モジュール - 外注加工管理
const subcontractModules = [
  {
    path: '/erp/purchase/subcontract-order',
    title: '外注加工指示',
    description: '外注加工指示書発行・加工費単価管理',
    icon: markRaw(Tickets),
    gradient: 'linear-gradient(135deg, #f093fb, #f5576c)'
  },
  {
    path: '/erp/purchase/material-supply',
    title: '有償/無償支給管理',
    description: '自社材料を外注先に送る処理',
    icon: markRaw(Van),
    gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)'
  },
  {
    path: '/erp/purchase/subcontract-inventory',
    title: '外注先在庫管理',
    description: '外注先にある自社資産の把握',
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #a18cd1, #fbc2eb)'
  }
]

// 機能モジュール - 受入・検収管理
const receivingModules = [
  {
    path: '/erp/purchase/arrival',
    title: '入荷予定管理',
    description: '納期遅延アラート・督促メール送信',
    icon: markRaw(Clock),
    gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)'
  },
  {
    path: '/erp/purchase/receipt',
    title: '受入登録',
    description: '現品票(QR)発行・良品/不良振分',
    icon: markRaw(Van),
    gradient: 'linear-gradient(135deg, #67c23a, #85ce61)'
  },
  {
    path: '/erp/purchase/inspection',
    title: '受入検査',
    description: '良品/不良/保留判定・ロット番号付与',
    icon: markRaw(Document),
    gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)'
  }
]

// 機能モジュール - 債務管理
const payableModules = [
  {
    path: '/erp/purchase/invoice-matching',
    title: '請求書照合',
    description: '発注・受入・請求3点照合',
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #f56c6c, #f78989)'
  },
  {
    path: '/erp/purchase/payment-schedule',
    title: '支払予定表',
    description: '支払予定管理・資金繰り計画',
    icon: markRaw(Clock),
    gradient: 'linear-gradient(135deg, #fa709a, #fee140)'
  },
  {
    path: '/erp/purchase/bank-transfer',
    title: 'FBデータ作成',
    description: '全銀フォーマット出力・銀行振込',
    icon: markRaw(User),
    gradient: 'linear-gradient(135deg, #9254de, #b37feb)'
  }
]

// 全機能モジュール
const modules = [...orderModules, ...subcontractModules, ...receivingModules, ...payableModules]

// 查看订单
const viewOrder = (row: PurchaseOrder) => {
  router.push(`/erp/purchase/orders/${row.id}`)
}

// 收货
const receiveOrder = (row: PurchaseOrder) => {
  router.push(`/erp/purchase/receipts/new?order_id=${row.id}`)
}

// 加载数据
const fetchData = async () => {
  loading.value = true
  try {
    const [statsRes, pendingRes, receiptsRes] = await Promise.all([
      getPurchaseStats(),
      getPurchaseOrderList({ status: 'pending', page_size: 5 }),
      getPurchaseOrderList({ status: 'approved', page_size: 5 })
    ])
    stats.value = statsRes.data || statsRes
    pendingOrders.value = (pendingRes.data?.items || pendingRes.items || []) as PurchaseOrder[]
    pendingReceipts.value = (receiptsRes.data?.items || receiptsRes.items || []) as PurchaseOrder[]
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
.purchase-home {
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
  background: linear-gradient(135deg, #409eff, #67c23a);
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
  margin-top: 24px;
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
