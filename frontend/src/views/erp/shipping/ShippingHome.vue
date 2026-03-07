<template>
  <div class="shipping-home">
    <!-- 动态背景：多层光晕 + 网格 -->
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="gradient-orb orb-4"></div>
      <div class="gradient-orb orb-5"></div>
      <div class="noise-overlay"></div>
    </div>

    <!-- 玻璃头部 -->
    <div class="glass-header animate-in">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon-wrap">
            <div class="header-icon">
              <el-icon size="28"><Van /></el-icon>
            </div>
            <div class="header-icon-glow"></div>
          </div>
          <div class="header-text">
            <h1 class="header-title">出荷管理</h1>
            <div class="header-subtitle">Shipping Management</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计卡片：玻璃 + 入场动画 -->
    <div class="stats-section">
      <div class="stats-grid" v-loading="loading">
        <router-link
          v-for="(stat, index) in statCards"
          :key="stat.key"
          :to="stat.to"
          class="stat-card glass-card animate-in"
          :style="{ animationDelay: `${0.1 + index * 0.05}s` }"
        >
          <div class="stat-card-inner">
            <div class="stat-icon" :style="{ background: stat.gradient }">
              <el-icon :size="24"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">{{ stat.label }}</div>
              <div class="stat-value" :class="{ 'stat-value-negative': stat.negative }">{{ stat.value }}</div>
            </div>
          </div>
          <div class="stat-card-shine"></div>
        </router-link>
      </div>
    </div>

    <!-- 功能模块：玻璃卡片 + 交错入场 -->
    <div class="modules-section">
      <h2 class="section-title animate-in" style="animation-delay: 0.25s">機能メニュー</h2>
      <div class="module-grid">
        <router-link
          v-for="(module, index) in modules"
          :key="module.path"
          :to="module.path"
          class="module-card glass-card animate-in"
          :style="{ animationDelay: `${0.3 + index * 0.04}s` }"
        >
          <div class="module-card-inner">
            <div class="module-icon" :style="{ background: module.gradient }">
              <el-icon :size="28"><component :is="module.icon" /></el-icon>
            </div>
            <div class="module-info">
              <h3 class="module-title">{{ module.title }}</h3>
              <p class="module-desc">{{ module.description }}</p>
            </div>
            <span class="module-arrow">
              <el-icon :size="20"><ArrowRight /></el-icon>
            </span>
          </div>
          <div class="module-card-shine"></div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { markRaw, ref, onMounted, computed } from 'vue'
import {
  Van,
  ArrowRight,
  List,
  Document,
  Calendar,
  CircleCheck,
  Connection,
  Box,
  OfficeBuilding,
  Clock,
  Warning,
  DataAnalysis,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import { getJSTToday } from '@/utils/dateFormat'
import { getProductionSummarysList } from '@/api/database'

const loading = ref(false)

// ピッキング概览（与 PickingHome 一致）
interface TodayOverview {
  total_today: number
  pending_today: number
  completed_today: number
  today_completion_rate: number
}
const pickingOverview = ref<TodayOverview>({
  total_today: 0,
  pending_today: 0,
  completed_today: 0,
  today_completion_rate: 0,
})

// 倉庫在庫統計（与 InventoryShortageManagement 一致：本日の production_summarys 集計）
const inventoryStats = ref({
  totalCurrent: 0,
  negativeCount: 0,
})

function formatNumber(n: number): string {
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)}B`
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`
  return String(n)
}

async function fetchPickingOverview() {
  try {
    const response = (await request.get('/api/shipping/picking/new-progress')) as any
    let data = response?.data ?? response
    if (response?.success === false || !data) return
    const excludeKeywords = ['加工', 'アーチ', '料金']
    const today = getJSTToday()
    if (Array.isArray(data.palletList)) {
      const list = data.palletList.filter((item: any) => {
        const name = item.product_name || item.productName || ''
        return !excludeKeywords.some((k: string) => name.includes(k))
      })
      const todayItems = list.filter((item: any) => {
        const d = item.shipping_date || item.date || ''
        return d === today || d.startsWith(today)
      })
      const pendingStatuses = ['pending', '進行中', 'in_progress']
      const completedStatuses = ['completed', '完了', 'finished']
      pickingOverview.value = {
        total_today: todayItems.length,
        pending_today: todayItems.filter((i: any) => pendingStatuses.includes(i.status)).length,
        completed_today: todayItems.filter((i: any) => completedStatuses.includes(i.status)).length,
        today_completion_rate:
          todayItems.length > 0
            ? Math.round(
                (todayItems.filter((i: any) => completedStatuses.includes(i.status)).length / todayItems.length) * 100,
              )
            : 0,
      }
      return
    }
    const ov = data.todayOverview
    if (ov && (ov.total_today > 0 || ov.pending_today > 0 || ov.completed_today > 0)) {
      pickingOverview.value = {
        total_today: ov.total_today ?? 0,
        pending_today: ov.pending_today ?? 0,
        completed_today: ov.completed_today ?? 0,
        today_completion_rate: ov.today_completion_rate ?? 0,
      }
    }
  } catch (_) {
    // ignore
  }
}

async function fetchInventoryStats() {
  const today = getJSTToday()
  try {
    const res: any = await getProductionSummarysList({
      page: 1,
      limit: 50000,
      startDate: today,
      endDate: today,
      sortBy: 'product_name',
      sortOrder: 'ASC',
    })
    const payload = res?.data ?? res
    const list = payload?.data?.list ?? payload?.list ?? []
    const rows = Array.isArray(list) ? list : []
    const totalCurrent = rows.reduce(
      (sum: number, row: any) =>
        sum + (Number(row.warehouse_inventory) || 0) + (Number(row.outsourced_warehouse_inventory) || 0),
      0,
    )
    const negativeCount = rows.reduce((sum: number, row: any) => {
      const v = Number(row.warehouse_inventory) || 0
      return v < 0 ? sum + v : sum
    }, 0)
    inventoryStats.value = { totalCurrent, negativeCount }
  } catch (_) {
    // ignore
  }
}

async function fetchStats() {
  loading.value = true
  try {
    await Promise.all([fetchPickingOverview(), fetchInventoryStats()])
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStats()
})

// 统计卡片配置（用于模板 + 玻璃样式）
const statCards = computed(() => [
  {
    key: 'pallets',
    to: '/erp/shipping/picking',
    label: '本日パレット数',
    value: String(pickingOverview.value.total_today),
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)',
    icon: markRaw(Calendar),
    negative: false,
  },
  {
    key: 'pending',
    to: '/erp/shipping/picking',
    label: '未ピッキング',
    value: String(pickingOverview.value.pending_today),
    gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)',
    icon: markRaw(Clock),
    negative: false,
  },
  {
    key: 'completed',
    to: '/erp/shipping/picking',
    label: '本日完了',
    value: String(pickingOverview.value.completed_today),
    gradient: 'linear-gradient(135deg, #67c23a, #85ce61)',
    icon: markRaw(CircleCheck),
    negative: false,
  },
  {
    key: 'inventory',
    to: '/erp/shipping/inventory-shortage',
    label: '現在在庫数',
    value: formatNumber(inventoryStats.value.totalCurrent),
    gradient: 'linear-gradient(135deg, #409eff, #66b1ff)',
    icon: markRaw(Box),
    negative: false,
  },
  {
    key: 'shortage',
    to: '/erp/shipping/inventory-shortage',
    label: '倉庫不足（マイナス）',
    value: formatNumber(inventoryStats.value.negativeCount),
    gradient: 'linear-gradient(135deg, #f56c6c, #f78989)',
    icon: markRaw(Warning),
    negative: true,
  },
])

const modules = [
  {
    path: '/erp/shipping/list',
    title: '出荷構成表管理',
    description: '出荷構成表の作成・編集・一覧',
    icon: markRaw(List),
    gradient: 'linear-gradient(135deg, #409eff, #66b1ff)',
  },
  {
    path: '/erp/shipping/report',
    title: '出荷報告書管理',
    description: '出荷報告書の作成・印刷・履歴',
    icon: markRaw(Document),
    gradient: 'linear-gradient(135deg, #67c23a, #85ce61)',
  },
  {
    path: '/erp/shipping/overview',
    title: '出荷予定表発行',
    description: '出荷予定表の発行・印刷',
    icon: markRaw(Calendar),
    gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)',
  },
  {
    path: '/erp/shipping/confirm',
    title: '出荷確認リスト',
    description: '出荷確認リストの照会・印刷',
    icon: markRaw(CircleCheck),
    gradient: 'linear-gradient(135deg, #909399, #b1b3b8)',
  },
  {
    path: '/erp/shipping/welding',
    title: '溶接出荷管理',
    description: '溶接工程の出荷指示・進捗',
    icon: markRaw(Connection),
    gradient: 'linear-gradient(135deg, #f56c6c, #f78989)',
  },
  {
    path: '/erp/shipping/picking',
    title: 'ピッキング管理',
    description: 'ピッキングリスト・履歴・進捗',
    icon: markRaw(Box),
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)',
  },
  {
    path: '/erp/shipping/inventory-shortage',
    title: '倉庫在庫管理',
    description: '在庫不足・倉庫在庫の管理',
    icon: markRaw(OfficeBuilding),
    gradient: 'linear-gradient(135deg, #9254de, #b37feb)',
  },
  {
    path: '/erp/shipping/inventory-kpi',
    title: '在庫KPI・アラート',
    description: '在庫回転率・平均在庫日数・欠品/過剰アラート・発注点',
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #2563eb, #3b82f6)',
  },
  {
    path: '/erp/shipping/abc-analysis',
    title: 'ABC分析',
    description: '出荷データによる品目・納入先の重要度分析',
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #13c2c2, #36cfc9)',
  },
]
</script>

<style scoped>
/* ---------- 变量 ---------- */
.shipping-home {
  --glass-bg: rgba(255, 255, 255, 0.12);
  --glass-border: rgba(255, 255, 255, 0.25);
  --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --blur-strong: 24px;
  --blur-soft: 12px;
}

/* ---------- 页面容器 ---------- */
.shipping-home {
  padding: 24px;
  min-height: 100vh;
  background: linear-gradient(160deg, #0f172a 0%, #1e3a5f 35%, #2563eb 70%, #3b82f6 100%);
  position: relative;
  overflow-x: hidden;
}

/* ---------- 动态背景：光晕 + 噪点 ---------- */
.dynamic-background {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.5;
  animation: orbFloat 18s ease-in-out infinite;
}

.orb-1 {
  width: 420px;
  height: 420px;
  top: -120px;
  right: -80px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.4) 0%, transparent 70%);
  animation-delay: 0s;
}
.orb-2 {
  width: 320px;
  height: 320px;
  bottom: -80px;
  left: -60px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.35) 0%, transparent 70%);
  animation-delay: -6s;
}
.orb-3 {
  width: 280px;
  height: 280px;
  top: calc(50% - 140px);
  left: calc(50% - 140px);
  background: radial-gradient(circle, rgba(34, 211, 238, 0.2) 0%, transparent 70%);
  animation-delay: -12s;
}
.orb-4 {
  width: 200px;
  height: 200px;
  top: 20%;
  left: 15%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.08) 0%, transparent 70%);
  animation-delay: -3s;
}
.orb-5 {
  width: 180px;
  height: 180px;
  bottom: 25%;
  right: 20%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.06) 0%, transparent 70%);
  animation-delay: -9s;
}

@keyframes orbFloat {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.5; }
  25% { transform: translate(20px, -25px) scale(1.05); opacity: 0.6; }
  50% { transform: translate(-15px, 15px) scale(0.98); opacity: 0.45; }
  75% { transform: translate(10px, 20px) scale(1.02); opacity: 0.55; }
}

.noise-overlay {
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
  pointer-events: none;
}

/* ---------- 入场动画 ---------- */
.animate-in {
  opacity: 0;
  transform: translateY(20px);
  animation: fadeInUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ---------- 玻璃头部 ---------- */
.glass-header {
  position: relative;
  z-index: 1;
  margin-bottom: 28px;
  padding: 28px 32px;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--blur-strong));
  -webkit-backdrop-filter: blur(var(--blur-strong));
  border-radius: 20px;
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon-wrap {
  position: relative;
}

.header-icon {
  position: relative;
  z-index: 1;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.4);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.header-icon-glow {
  position: absolute;
  inset: -4px;
  border-radius: 20px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  filter: blur(12px);
  opacity: 0.4;
}

.glass-header:hover .header-icon {
  transform: scale(1.05);
  box-shadow: 0 12px 32px rgba(37, 99, 235, 0.5);
}

.header-title {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 4px 0;
  letter-spacing: -0.02em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.header-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
  letter-spacing: 0.05em;
}

/* ---------- 玻璃卡片通用 ---------- */
.glass-card {
  position: relative;
  overflow: hidden;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--blur-soft));
  -webkit-backdrop-filter: blur(var(--blur-soft));
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  box-shadow: var(--glass-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.08);
  text-decoration: none;
  color: inherit;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.35s ease,
    border-color 0.35s ease;
}

.glass-card:hover {
  transform: translateY(-6px) scale(1.01);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.35);
}

/* ---------- 统计区域 ---------- */
.stats-section {
  position: relative;
  z-index: 1;
  margin-bottom: 32px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 18px;
  min-height: 88px;
}

.stat-card {
  display: block;
}

.stat-card-inner {
  position: relative;
  z-index: 1;
  padding: 20px 22px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-card-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(
    105deg,
    transparent,
    rgba(255, 255, 255, 0.08),
    transparent
  );
  transition: left 0.6s ease;
}

.stat-card:hover .stat-card-shine {
  left: 100%;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
  transition: transform 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.08);
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 4px;
  font-weight: 500;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.02em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.stat-value-negative {
  color: #fca5a5;
}

/* ---------- 功能模块区域 ---------- */
.modules-section {
  position: relative;
  z-index: 1;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  margin: 0 0 20px 0;
  letter-spacing: 0.02em;
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.module-card {
  display: block;
}

.module-card-inner {
  position: relative;
  z-index: 1;
  padding: 24px 26px;
  display: flex;
  align-items: center;
  gap: 18px;
}

.module-card-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 50%;
  height: 100%;
  background: linear-gradient(
    105deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
  transition: left 0.5s ease;
}

.module-card:hover .module-card-shine {
  left: 100%;
}

.module-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
  transition: transform 0.3s ease;
}

.module-card:hover .module-icon {
  transform: scale(1.06);
}

.module-info {
  flex: 1;
  min-width: 0;
}

.module-title {
  font-size: 17px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 6px 0;
  letter-spacing: -0.01em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.module-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
  line-height: 1.4;
}

.module-arrow {
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  transition: transform 0.3s ease, color 0.3s ease;
}

.module-card:hover .module-arrow {
  transform: translateX(6px);
  color: #fff;
}

/* ---------- 响应式 ---------- */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .module-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .shipping-home {
    padding: 16px;
  }
  .glass-header {
    padding: 20px 24px;
  }
  .header-title {
    font-size: 22px;
  }
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .stat-card-inner {
    padding: 16px 18px;
  }
  .stat-value {
    font-size: 20px;
  }
  .section-title {
    margin-bottom: 14px;
  }
  .module-grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }
  .module-card-inner {
    padding: 20px 22px;
  }
}
</style>
