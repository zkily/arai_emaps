<template>
  <div class="system-home">
    <!-- Modern Gradient Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon :size="28"><Setting /></el-icon>
        </div>
        <div class="header-text">
          <h1>システム管理</h1>
          <p class="subtitle">ユーザー・組織・権限・システム設定</p>
        </div>
      </div>
    </div>

    <!-- Stats Row -->
    <div class="stats-row">
      <div class="stat-card" v-for="stat in statsCards" :key="stat.key">
        <div class="stat-icon" :style="{ background: stat.gradient }">
          <el-icon :size="20"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
      </div>
    </div>

    <!-- User & Organization Section -->
    <div class="section">
      <div class="section-header">
        <el-icon><User /></el-icon>
        <span>ユーザー・組織管理</span>
      </div>
      <div class="module-grid-3">
        <router-link 
          v-for="module in userModules" 
          :key="module.path" 
          :to="module.path" 
          class="module-card"
        >
          <div class="module-icon" :style="{ background: module.gradient }">
            <el-icon :size="24"><component :is="module.icon" /></el-icon>
          </div>
          <div class="module-content">
            <h3 class="module-title">{{ module.title }}</h3>
            <p class="module-desc">{{ module.description }}</p>
          </div>
          <div class="module-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </router-link>
      </div>
    </div>

    <!-- System Settings Section -->
    <div class="section">
      <div class="section-header">
        <el-icon><Setting /></el-icon>
        <span>システム設定</span>
      </div>
      <div class="module-grid-3">
        <router-link 
          v-for="module in settingModules" 
          :key="module.path" 
          :to="module.path" 
          class="module-card"
        >
          <div class="module-icon" :style="{ background: module.gradient }">
            <el-icon :size="24"><component :is="module.icon" /></el-icon>
          </div>
          <div class="module-content">
            <h3 class="module-title">{{ module.title }}</h3>
            <p class="module-desc">{{ module.description }}</p>
          </div>
          <div class="module-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw, onMounted } from 'vue'
import {
  Setting, ArrowRight, User, OfficeBuilding, Key, Document,
  Connection, Bell, Tickets, DataBoard, UserFilled, Lock
} from '@element-plus/icons-vue'
import * as systemApi from '@/api/system'
import type { PaginatedUserResponse } from '@/api/system'

// 今日の日付 YYYY-MM-DD
function todayStr(): string {
  const d = new Date()
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0')
}

// Stats data
const statsCards = ref([
  { key: 'users', label: '登録ユーザー', value: '—', gradient: 'linear-gradient(135deg, #667eea, #764ba2)', icon: markRaw(UserFilled) },
  { key: 'online', label: '現在の利用者', value: '—', gradient: 'linear-gradient(135deg, #10b981, #059669)', icon: markRaw(User) },
  { key: 'roles', label: 'ロール数', value: '—', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)', icon: markRaw(Key) },
  { key: 'logs', label: '今日のログ', value: '—', gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)', icon: markRaw(Tickets) },
])

async function loadStats() {
  try {
    const today = todayStr()
    const [usersRes, onlineRes, rolesRes, logsRes] = await Promise.all([
      systemApi.getUsers({ page: 1, page_size: 1 }),
      systemApi.getOnlineCount(),
      systemApi.getRoles(),
      systemApi.getOperationLogs({ start_date: today, end_date: today, page: 1, page_size: 1 }),
    ])
    const totalUsers = (usersRes as unknown as PaginatedUserResponse).total ?? 0
    const onlineCount = (onlineRes as { online_count?: number })?.online_count ?? 0
    const roles = Array.isArray(rolesRes) ? rolesRes : (rolesRes as { data?: unknown[] })?.data ?? []
    const roleCount = roles.length
    const logsTotal = (logsRes as { total?: number })?.total ?? 0

    statsCards.value[0].value = totalUsers.toLocaleString()
    statsCards.value[1].value = String(onlineCount)
    statsCards.value[2].value = String(roleCount)
    statsCards.value[3].value = logsTotal.toLocaleString()
  } catch {
    statsCards.value[0].value = '—'
    statsCards.value[1].value = '—'
    statsCards.value[2].value = '—'
    statsCards.value[3].value = '—'
  }
}

onMounted(loadStats)

// User & Organization modules
const userModules = ref([
  {
    path: '/system/users',
    title: 'ユーザー管理',
    description: 'ユーザー登録・権限・2FA設定',
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)',
    icon: markRaw(User)
  },
  {
    path: '/system/organization',
    title: '組織・部門管理',
    description: '会社・拠点・部門階層構造',
    gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
    icon: markRaw(OfficeBuilding)
  },
  {
    path: '/system/roles',
    title: '権限・ロール管理',
    description: 'RBAC・メニュー・操作権限',
    gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)',
    icon: markRaw(Lock)
  },
])

// System settings modules
const settingModules = ref([
  {
    path: '/system/numbering',
    title: '採番ルール管理',
    description: '伝票番号の自動採番設定',
    gradient: 'linear-gradient(135deg, #10b981, #059669)',
    icon: markRaw(Document)
  },
  {
    path: '/system/workflow',
    title: 'ワークフロー設定',
    description: '承認ルート・代理承認',
    gradient: 'linear-gradient(135deg, #f43f5e, #e11d48)',
    icon: markRaw(Connection)
  },
  {
    path: '/system/notification',
    title: '通知センター',
    description: 'メール・LINE・Slack連携',
    gradient: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
    icon: markRaw(Bell)
  },
  {
    path: '/system/logs',
    title: 'システムログ',
    description: '操作・エラー・APIログ',
    gradient: 'linear-gradient(135deg, #64748b, #475569)',
    icon: markRaw(Tickets)
  },
  {
    path: '/system/data',
    title: 'データ管理',
    description: 'インポート・エクスポート',
    gradient: 'linear-gradient(135deg, #ec4899, #db2777)',
    icon: markRaw(DataBoard)
  },
])
</script>

<style scoped>
/* Base Layout */
.system-home {
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
  min-height: 100vh;
}

/* Modern Gradient Header */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 16px 24px;
  margin-bottom: 12px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.25);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
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

.header-text h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: white;
  letter-spacing: -0.5px;
}

.header-text .subtitle {
  margin: 2px 0 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

/* Stats Row */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: white;
  border-radius: 10px;
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
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
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

/* Module Grid - 3 columns */
.module-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.module-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  text-decoration: none;
  transition: all 0.25s ease;
  cursor: pointer;
}

.module-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
}

.module-card:hover .module-arrow {
  transform: translateX(4px);
  color: #667eea;
}

.module-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.module-content {
  flex: 1;
  min-width: 0;
}

.module-title {
  margin: 0 0 3px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.module-desc {
  margin: 0;
  font-size: 11px;
  color: #64748b;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.module-arrow {
  color: #cbd5e1;
  transition: all 0.25s ease;
  flex-shrink: 0;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .module-grid-3 {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .system-home {
    padding: 12px;
  }
  
  .page-header {
    padding: 14px 16px;
  }
  
  .header-text h1 {
    font-size: 18px;
  }
  
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  
  .stat-card {
    padding: 12px;
  }
  
  .stat-value {
    font-size: 18px;
  }
  
  .module-grid-3 {
    grid-template-columns: 1fr;
  }
  
  .module-card {
    padding: 12px 14px;
  }
}

@media (max-width: 480px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
  
  .stat-card {
    flex-direction: row;
  }
}
</style>
