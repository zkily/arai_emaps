<template>
  <div class="system-home-container">
    <!-- ページヘッダー -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Setting />
            </el-icon>
            システムホーム
          </h1>
          <p class="subtitle">システム設定・ユーザー管理・権限管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card" v-for="stat in statsCards" :key="stat.key">
            <div class="stat-number">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ユーザー・組織管理セクション -->
    <div class="section-container">
      <div class="section-title">
        <el-icon class="section-icon"><User /></el-icon>
        <span>ユーザー・組織管理</span>
      </div>
      <div class="system-grid">
        <div
          v-for="module in userModules"
          :key="module.path"
          class="system-card"
          :style="{ '--card-color': module.color, '--card-gradient': module.gradient }"
          @click="navigateTo(module.path)"
        >
          <div class="card-icon-wrapper">
            <el-icon class="card-icon" :size="32">
              <component :is="module.icon" />
            </el-icon>
          </div>
          <div class="card-content">
            <h3 class="card-title">{{ module.title }}</h3>
            <p class="card-description">{{ module.description }}</p>
          </div>
          <div class="card-arrow">
            <el-icon :size="20">
              <ArrowRight />
            </el-icon>
          </div>
          <div class="card-decoration"></div>
        </div>
      </div>
    </div>

    <!-- システム設定セクション -->
    <div class="section-container">
      <div class="section-title">
        <el-icon class="section-icon"><Setting /></el-icon>
        <span>システム設定</span>
      </div>
      <div class="system-grid">
        <div
          v-for="module in settingModules"
          :key="module.path"
          class="system-card"
          :style="{ '--card-color': module.color, '--card-gradient': module.gradient }"
          @click="navigateTo(module.path)"
        >
          <div class="card-icon-wrapper">
            <el-icon class="card-icon" :size="32">
              <component :is="module.icon" />
            </el-icon>
          </div>
          <div class="card-content">
            <h3 class="card-title">{{ module.title }}</h3>
            <p class="card-description">{{ module.description }}</p>
          </div>
          <div class="card-arrow">
            <el-icon :size="20">
              <ArrowRight />
            </el-icon>
          </div>
          <div class="card-decoration"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Setting,
  ArrowRight,
  User,
  OfficeBuilding,
  Key,
  Document,
  Connection,
  Bell,
  Tickets,
  DataBoard,
  UserFilled,
  Lock,
} from '@element-plus/icons-vue'
import * as systemApi from '@/api/system'
import type { PaginatedUserResponse } from '@/api/system'

const router = useRouter()

// 今日の日付 YYYY-MM-DD
function todayStr(): string {
  const d = new Date()
  return (
    d.getFullYear() +
    '-' +
    String(d.getMonth() + 1).padStart(2, '0') +
    '-' +
    String(d.getDate()).padStart(2, '0')
  )
}

// Stats data
const statsCards = ref([
  { key: 'users', label: '登録ユーザー', value: '—' },
  { key: 'online', label: '現在の利用者', value: '—' },
  { key: 'roles', label: 'ロール数', value: '—' },
  { key: 'logs', label: '今日のログ', value: '—' },
])

async function loadStats() {
  try {
    const today = todayStr()
    const [usersRes, onlineRes, rolesRes, logsRes] = await Promise.all([
      systemApi.getUsers({ page: 1, page_size: 1 }),
      systemApi.getOnlineCount(),
      systemApi.getRoles(),
      systemApi.getOperationLogs({
        start_date: today,
        end_date: today,
        page: 1,
        page_size: 1,
      }),
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

interface SystemModule {
  path: string
  title: string
  description: string
  color: string
  gradient: string
  icon: any
}

// User & Organization modules
const userModules: SystemModule[] = [
  {
    path: '/system/users',
    title: 'ユーザー管理',
    description: 'ユーザー登録・権限・2FA設定',
    color: '#667eea',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    icon: markRaw(User),
  },
  {
    path: '/system/organization',
    title: '組織・部門管理',
    description: '会社・拠点・部門階層構造',
    color: '#f59e0b',
    gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    icon: markRaw(OfficeBuilding),
  },
  {
    path: '/system/roles',
    title: '権限・ロール管理',
    description: 'RBAC・メニュー・操作権限',
    color: '#06b6d4',
    gradient: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
    icon: markRaw(Lock),
  },
]

// System settings modules
const settingModules: SystemModule[] = [
  {
    path: '/system/numbering',
    title: '採番ルール管理',
    description: '伝票番号の自動採番設定',
    color: '#10b981',
    gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    icon: markRaw(Document),
  },
  {
    path: '/system/workflow',
    title: 'ワークフロー設定',
    description: '承認ルート・代理承認',
    color: '#f43f5e',
    gradient: 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)',
    icon: markRaw(Connection),
  },
  {
    path: '/system/notification',
    title: '通知センター',
    description: 'メール・LINE・Slack連携',
    color: '#8b5cf6',
    gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
    icon: markRaw(Bell),
  },
  {
    path: '/system/logs',
    title: 'システムログ',
    description: '操作・エラー・APIログ',
    color: '#64748b',
    gradient: 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
    icon: markRaw(Tickets),
  },
  {
    path: '/system/data',
    title: 'データ管理',
    description: 'インポート・エクスポート',
    color: '#ec4899',
    gradient: 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
    icon: markRaw(DataBoard),
  },
]

const navigateTo = (path: string) => {
  router.push(path)
}
</script>

<style scoped>
.system-home-container {
  padding: 16px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

/* ページヘッダー */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px 32px;
  margin-bottom: 24px;
  box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.main-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.title-icon {
  font-size: 36px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
}

.subtitle {
  margin: 4px 0 0 48px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 12px;
  padding: 12px 24px;
  text-align: center;
  min-width: 100px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.25);
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 2px;
}

/* セクションコンテナ */
.section-container {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-left: 4px;
}

.section-icon {
  font-size: 20px;
  color: #667eea;
}

/* システムカードグリッド */
.system-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.system-card {
  position: relative;
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.system-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.system-card:hover .card-decoration {
  opacity: 1;
  transform: translateX(0);
}

.system-card:hover .card-arrow {
  transform: translateX(4px);
  opacity: 1;
}

.system-card:hover .card-icon-wrapper {
  transform: scale(1.1) rotate(5deg);
}

.card-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: var(--card-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.card-icon {
  color: #fff;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-description {
  font-size: 13px;
  color: #909399;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-arrow {
  color: #c0c4cc;
  transition: all 0.3s ease;
  opacity: 0.5;
}

.card-decoration {
  position: absolute;
  top: 0;
  right: 0;
  width: 100px;
  height: 100%;
  background: var(--card-gradient);
  opacity: 0.08;
  transform: translateX(20px) skewX(-15deg);
  transition: all 0.3s ease;
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
  .system-home-container {
    padding: 12px;
  }

  .page-header {
    padding: 20px;
    border-radius: 12px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .main-title {
    font-size: 22px;
    justify-content: center;
  }

  .subtitle {
    margin-left: 0;
  }

  .header-stats {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .system-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .system-card {
    padding: 16px;
    border-radius: 12px;
  }

  .card-icon-wrapper {
    width: 48px;
    height: 48px;
    border-radius: 12px;
  }
}

@media (max-width: 480px) {
  .header-stats {
    grid-template-columns: 1fr;
  }
}
</style>
