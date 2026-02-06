<template>
  <div class="dashboard-home">
    <!-- Compact Welcome Banner -->
    <div class="welcome-banner">
      <div class="welcome-content">
        <div class="welcome-avatar">
          <el-icon :size="24"><UserFilled /></el-icon>
        </div>
        <div class="welcome-text">
          <h1>{{ t('dashboard.welcomeBack', { name: userStore.user?.username || t('common.guest') }) }}</h1>
          <p>{{ t('dashboard.welcomeSub') }}</p>
        </div>
      </div>
      <div class="welcome-datetime">
        <el-icon><Clock /></el-icon>
        <span>{{ currentDateTime }}</span>
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
        <div class="stat-trend" :class="stat.trend > 0 ? 'up' : 'down'" v-if="stat.trend !== undefined && stat.trend !== null">
          <el-icon :size="12"><component :is="stat.trend > 0 ? Top : Bottom" /></el-icon>
          <span>{{ Math.abs(stat.trend) }}%</span>
        </div>
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

    <!-- Two Column Content -->
    <div class="content-grid">
      <!-- Recent Activity -->
      <div class="content-card">
        <div class="card-header">
          <div class="card-title">
            <el-icon><Clock /></el-icon>
            <span>{{ t('dashboard.recentActivity') }}</span>
          </div>
          <el-tag size="small" type="info">{{ t('dashboard.itemsCount', { n: recentActivities.length }) }}</el-tag>
        </div>
        <div class="card-body">
          <div class="activity-list">
            <div 
              v-for="activity in recentActivities" 
              :key="activity.id" 
              class="activity-item"
            >
              <div class="activity-dot" :class="activity.type"></div>
              <div class="activity-content">
                <span class="activity-text">{{ t('dashboard.activity.' + activity.contentKey, activity.contentParams) }}</span>
                <span class="activity-time">{{ t('dashboard.time.' + activity.timeKey, activity.timeParams) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tasks -->
      <div class="content-card">
        <div class="card-header">
          <div class="card-title">
            <el-icon><List /></el-icon>
            <span>{{ t('dashboard.tasks') }}</span>
          </div>
          <el-tag size="small" :type="pendingCount > 0 ? 'warning' : 'success'">
            {{ t('dashboard.pendingCount', { n: pendingCount }) }}
          </el-tag>
        </div>
        <div class="card-body">
          <div class="todo-list">
            <div 
              v-for="todo in todoItems" 
              :key="todo.id" 
              class="todo-item"
              :class="{ completed: todo.completed }"
            >
              <el-checkbox v-model="todo.completed" />
              <span class="todo-text">{{ t('dashboard.todo.' + todo.titleKey, todo.params || {}) }}</span>
              <span class="todo-priority" :class="todo.priority">
                {{ t('dashboard.' + todo.priority) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, markRaw, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/modules/auth/stores/user'
import dayjs from 'dayjs'
import {
  UserFilled, Sell, ShoppingCart, Box, Coin, Document, Clock, List, Grid,
  Top, Bottom, DataAnalysis, TrendCharts, User, Tickets, ArrowRight
} from '@element-plus/icons-vue'

const { t } = useI18n()
const userStore = useUserStore()

// Current datetime
const currentDateTime = ref(dayjs().format('YYYY/MM/DD HH:mm'))
let timer: number | null = null

onMounted(() => {
  timer = window.setInterval(() => {
    currentDateTime.value = dayjs().format('YYYY/MM/DD HH:mm')
  }, 60000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

// Stats cards
const statsCards = ref([
  { key: 'sales', value: '¥12,580,000', icon: markRaw(TrendCharts), gradient: 'linear-gradient(135deg, #667eea, #764ba2)', trend: 12.5 },
  { key: 'orders', value: '156件', icon: markRaw(Document), gradient: 'linear-gradient(135deg, #f43f5e, #e11d48)', trend: 8.2 },
  { key: 'inventory', value: '2,847', icon: markRaw(Box), gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)', trend: -2.3 },
  { key: 'suppliers', value: '89社', icon: markRaw(User), gradient: 'linear-gradient(135deg, #10b981, #059669)', trend: 5.0 },
])

// Quick access items (titleKey/descKey for i18n)
const quickAccessItems = ref([
  { path: '/erp/sales', titleKey: 'sales', descKey: 'salesDesc', icon: markRaw(Sell), bg: 'linear-gradient(135deg, #667eea, #764ba2)' },
  { path: '/erp/purchase', titleKey: 'purchase', descKey: 'purchaseDesc', icon: markRaw(ShoppingCart), bg: 'linear-gradient(135deg, #f43f5e, #e11d48)' },
  { path: '/erp/inventory', titleKey: 'inventory', descKey: 'inventoryDesc', icon: markRaw(Box), bg: 'linear-gradient(135deg, #06b6d4, #0891b2)' },
  { path: '/erp/costing', titleKey: 'costing', descKey: 'costingDesc', icon: markRaw(Coin), bg: 'linear-gradient(135deg, #10b981, #059669)' },
  { path: '/erp/order', titleKey: 'order', descKey: 'orderDesc', icon: markRaw(DataAnalysis), bg: 'linear-gradient(135deg, #f59e0b, #d97706)' },
  { path: '/aps/planning', titleKey: 'planning', descKey: 'planningDesc', icon: markRaw(Tickets), bg: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' },
])

// Recent activities (contentKey/contentParams, timeKey/timeParams for i18n)
type TimelineType = 'primary' | 'success' | 'warning' | 'danger' | 'info'
const recentActivities = ref<{
  id: number
  contentKey: string
  contentParams: Record<string, string>
  timeKey: string
  timeParams: Record<string, number>
  type: TimelineType
}[]>([
  { id: 1, contentKey: 'orderRegistered', contentParams: { code: 'SO-2026020001' }, timeKey: 'minutesAgo', timeParams: { n: 10 }, type: 'primary' },
  { id: 2, contentKey: 'shippingDone', contentParams: { code: 'SH-2026020015' }, timeKey: 'minutesAgo', timeParams: { n: 30 }, type: 'success' },
  { id: 3, contentKey: 'orderApproved', contentParams: { code: 'PO-2026020008' }, timeKey: 'hoursAgo', timeParams: { n: 1 }, type: 'warning' },
  { id: 4, contentKey: 'stockAlert', contentParams: { code: 'A001' }, timeKey: 'hoursAgo', timeParams: { n: 2 }, type: 'danger' },
  { id: 5, contentKey: 'invoiceDone', contentParams: {}, timeKey: 'hoursAgo', timeParams: { n: 3 }, type: 'info' },
])

// Todo items (titleKey/params for i18n)
const todoItems = ref([
  { id: 1, titleKey: 'arrivalCheck', params: { n: 3 }, completed: false, priority: 'high' },
  { id: 2, titleKey: 'quoteReply', params: {}, completed: false, priority: 'medium' },
  { id: 3, titleKey: 'stocktakePrep', params: {}, completed: true, priority: 'low' },
  { id: 4, titleKey: 'supplierRegister', params: {}, completed: false, priority: 'medium' },
])

const pendingCount = computed(() => todoItems.value.filter(t => !t.completed).length)
</script>

<style scoped>
.dashboard-home {
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
  min-height: 100vh;
}

/* Welcome Banner - Compact */
.welcome-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 16px 24px;
  margin-bottom: 12px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.25);
}

.welcome-content {
  display: flex;
  align-items: center;
  gap: 14px;
}

.welcome-avatar {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  backdrop-filter: blur(10px);
}

.welcome-text h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.welcome-text p {
  margin: 2px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
}

.welcome-datetime {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  padding: 8px 14px;
  border-radius: 8px;
  color: white;
  font-size: 13px;
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

.stat-trend {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 6px;
  border-radius: 4px;
}

.stat-trend.up {
  color: #16a34a;
  background: #dcfce7;
}

.stat-trend.down {
  color: #dc2626;
  background: #fee2e2;
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

/* Content Grid - Two Columns */
.content-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.content-card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  background: #f8fafc;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.card-title .el-icon {
  color: #667eea;
}

.card-body {
  padding: 12px 16px;
  max-height: 240px;
  overflow-y: auto;
}

/* Activity List */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
}

.activity-dot.primary { background: #667eea; }
.activity-dot.success { background: #10b981; }
.activity-dot.warning { background: #f59e0b; }
.activity-dot.danger { background: #ef4444; }
.activity-dot.info { background: #64748b; }

.activity-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.activity-text {
  font-size: 12px;
  color: #1e293b;
  line-height: 1.4;
}

.activity-time {
  font-size: 10px;
  color: #94a3b8;
}

/* Todo List */
.todo-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: 6px;
  transition: all 0.2s;
}

.todo-item:hover {
  background: #f1f5f9;
}

.todo-item.completed {
  opacity: 0.6;
}

.todo-item.completed .todo-text {
  text-decoration: line-through;
  color: #94a3b8;
}

.todo-text {
  flex: 1;
  font-size: 12px;
  color: #1e293b;
}

.todo-priority {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.todo-priority.high { background: #fee2e2; color: #dc2626; }
.todo-priority.medium { background: #fef3c7; color: #d97706; }
.todo-priority.low { background: #f1f5f9; color: #64748b; }

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
    gap: 12px;
    text-align: center;
  }
  
  .welcome-content {
    flex-direction: column;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .quick-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>
