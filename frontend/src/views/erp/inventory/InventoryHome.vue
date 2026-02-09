<template>
  <div class="inventory-home">
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
            <el-icon size="32"><Box /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">在庫管理</h1>
            <div class="header-subtitle">Inventory Management</div>
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

    <!-- 库存预警 -->
    <div class="alert-section modern-card">
      <div class="section-header">
        <el-icon><Warning /></el-icon>
        <span>在庫アラート</span>
        <el-badge :value="alerts.length" type="danger" v-if="alerts.length > 0" />
      </div>
      <el-table :data="alerts" v-loading="loading" stripe class="modern-table">
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" />
        <el-table-column prop="warehouse_name" label="倉庫" width="120" />
        <el-table-column prop="alert_type_name" label="アラート種別" width="120">
          <template #default="{ row }">
            <el-tag :type="getAlertType(row.alert_type)">{{ row.alert_type_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_quantity" label="現在数量" width="100" align="right" />
        <el-table-column prop="threshold_quantity" label="しきい値" width="100" align="right" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleAlert(row)">対応</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, markRaw } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Box, ArrowRight, Warning, Top, Bottom,
  List, Tickets, Setting, DataAnalysis, Document
} from '@element-plus/icons-vue'
import { getInventoryStats, getStockAlerts } from '@/api/erp/inventory'
import type { InventoryStats, StockAlert } from '@/types/erp/inventory'

const loading = ref(false)
const stats = ref<InventoryStats | null>(null)
const alerts = ref<StockAlert[]>([])

// 统计卡片配置
const statsCards = computed(() => [
  {
    key: 'total_items',
    label: '在庫品目数',
    value: stats.value?.total_items?.toLocaleString() || '0',
    icon: markRaw(Box),
    gradient: 'linear-gradient(135deg, #409eff, #67c23a)',
    change: '+12%',
    changeType: 'up'
  },
  {
    key: 'total_value',
    label: '在庫総額',
    value: `¥${(stats.value?.total_value || 0).toLocaleString()}`,
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #67c23a, #85ce61)',
    change: '+8%',
    changeType: 'up'
  },
  {
    key: 'low_stock',
    label: '在庫不足',
    value: stats.value?.low_stock_count?.toString() || '0',
    icon: markRaw(Warning),
    gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)',
    change: '-3',
    changeType: 'down'
  },
  {
    key: 'expiring',
    label: '期限切迫',
    value: stats.value?.expiring_soon_count?.toString() || '0',
    icon: markRaw(Document),
    gradient: 'linear-gradient(135deg, #f56c6c, #ff7875)',
    change: '+2',
    changeType: 'up'
  }
])

// 機能モジュール - 在庫・ロケーション管理
const locationModules = [
  {
    path: '/erp/inventory/list',
    title: '在庫照会',
    description: 'リアルタイム在庫照会・有効在庫照会',
    icon: markRaw(List),
    gradient: 'linear-gradient(135deg, #409eff, #67c23a)'
  },
  {
    path: '/erp/inventory/location',
    title: 'ロケーション管理',
    description: 'マルチ倉庫・ロケーション管理',
    icon: markRaw(Setting),
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)'
  }
]

// 機能モジュール - 入出庫・移動管理
const transactionModules = [
  {
    path: '/erp/inventory/transactions',
    title: '入出庫履歴',
    description: '入出庫の履歴を管理',
    icon: markRaw(Tickets),
    gradient: 'linear-gradient(135deg, #67c23a, #85ce61)'
  },
  {
    path: '/erp/inventory/movement',
    title: '入出庫移動',
    description: '倉庫間移動・セット品組立/分解',
    icon: markRaw(Box),
    gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)'
  },
  {
    path: '/erp/inventory/lot-trace',
    title: 'ロット・トレーサビリティ',
    description: '正展開（製品→材料）・逆展開（材料→製品）',
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #a18cd1, #fbc2eb)'
  }
]

// 機能モジュール - 棚卸管理
const stocktakingModules = [
  {
    path: '/erp/inventory/stocktaking',
    title: '棚卸管理',
    description: '一斉棚卸/循環棚卸・棚卸票発行・差異修正',
    icon: markRaw(Setting),
    gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)'
  },
  {
    path: '/erp/inventory/dead-stock',
    title: '滞留在庫アラート',
    description: 'デッドストック(Dead Stock)リストアップ',
    icon: markRaw(Warning),
    gradient: 'linear-gradient(135deg, #f56c6c, #f78989)'
  },
  {
    path: '/erp/inventory/abc-analysis',
    title: 'ABC分析',
    description: '出荷頻度・金額ランク付け・ロケ最適化',
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #9254de, #b37feb)'
  }
]

// 全機能モジュール
const modules = [...locationModules, ...transactionModules, ...stocktakingModules]

// 获取预警类型样式
const getAlertType = (type: string) => {
  const typeMap: Record<string, string> = {
    low_stock: 'warning',
    overstock: 'info',
    expiring: 'danger',
    expired: 'danger'
  }
  return typeMap[type] || 'info'
}

// 处理预警
const handleAlert = (row: StockAlert) => {
  ElMessage.info(`アラート ID: ${row.id} の対応画面へ遷移します`)
}

// 加载数据
const fetchData = async () => {
  loading.value = true
  try {
    const [statsRes, alertsRes] = await Promise.all([
      getInventoryStats(),
      getStockAlerts({ status: 'active', page_size: 10 })
    ])
    stats.value = statsRes.data || statsRes
    alerts.value = (alertsRes.data?.items || alertsRes.items || []) as StockAlert[]
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
.inventory-home {
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

/* 预警区域 */
.alert-section {
  padding: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.modern-table {
  border-radius: 8px;
  overflow: hidden;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid, .module-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid, .module-grid {
    grid-template-columns: 1fr;
  }
}
</style>
