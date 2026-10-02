<template>
  <div class="sales-home">
    <div class="glass-header">
      <div class="header-fx" aria-hidden="true">
        <span class="fx-orb orb-a" />
        <span class="fx-orb orb-b" />
        <span class="fx-grid" />
      </div>
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon-wrap">
            <div class="header-icon">
              <el-icon size="28"><Sell /></el-icon>
            </div>
          </div>
          <div class="header-text">
            <h1 class="header-title">販売管理</h1>
            <div class="header-subtitle">Sales Management</div>
          </div>
        </div>
      </div>
    </div>

    <div class="stats-section">
      <div class="stats-grid" v-loading="loading">
        <div
          v-for="stat in statCards"
          :key="stat.key"
          class="stat-card"
          :style="{ '--sc': stat.color }"
        >
          <div class="stat-card-inner">
            <div class="stat-icon" :style="{ background: stat.gradient }">
              <el-icon :size="22"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">{{ stat.label }}</div>
              <div class="stat-value">{{ stat.value }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="modules-section">
      <h2 class="section-title">機能メニュー</h2>
      <div class="module-grid">
        <router-link
          v-for="mod in modules"
          :key="mod.path"
          :to="mod.path"
          class="module-card"
          :style="{ '--mc': mod.color }"
        >
          <div class="module-card-inner">
            <div class="module-icon" :style="{ background: mod.gradient }">
              <el-icon :size="24"><component :is="mod.icon" /></el-icon>
            </div>
            <div class="module-info">
              <h3 class="module-title">{{ mod.title }}</h3>
              <p class="module-desc">{{ mod.description }}</p>
            </div>
            <span class="module-arrow">
              <el-icon :size="18"><ArrowRight /></el-icon>
            </span>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, markRaw } from 'vue'
import {
  Sell,
  ArrowRight,
  Document,
  List,
  Calendar,
  Ticket,
  Money,
  CreditCard,
  PriceTag,
  TrendCharts,
  Van,
  Coin,
  RefreshLeft,
  DataAnalysis,
} from '@element-plus/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const stats = ref({
  monthly_order_count: 0,
  monthly_order_amount: 0,
  pending_delivery_count: 0,
  unpaid_amount: 0,
  completed_count: 0,
  monthly_confirmed_units: 0,
})

const statCards = ref([
  { key: 'orders', label: '今月受注', value: '0件', gradient: 'linear-gradient(135deg, #3b82f6, #1d4ed8)', color: '#3b82f6', icon: markRaw(Document) },
  { key: 'amount', label: '今月売上', value: '¥0', gradient: 'linear-gradient(135deg, #10b981, #059669)', color: '#10b981', icon: markRaw(Money) },
  { key: 'units', label: '確定本数', value: '0本', gradient: 'linear-gradient(135deg, #8b5cf6, #6d28d9)', color: '#8b5cf6', icon: markRaw(TrendCharts) },
  { key: 'pending', label: '出荷待ち', value: '0件', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#f59e0b', icon: markRaw(Van) },
  { key: 'completed', label: '今月完了', value: '0件', gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)', color: '#06b6d4', icon: markRaw(Ticket) },
  { key: 'unpaid', label: '未回収', value: '¥0', gradient: 'linear-gradient(135deg, #ef4444, #dc2626)', color: '#ef4444', icon: markRaw(CreditCard) },
])

const modules = [
  { path: '/erp/sales/quotation', title: '見積管理', description: '見積書の作成・送付・受注変換', icon: markRaw(Document), gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)', color: '#3b82f6' },
  { path: '/erp/sales/orders', title: '受注一覧', description: '受注データの一覧管理・承認', icon: markRaw(List), gradient: 'linear-gradient(135deg, #8b5cf6, #7c3aed)', color: '#8b5cf6' },
  { path: '/erp/sales/forecast', title: '内示・フォーキャスト', description: '需要予測・内示データ管理', icon: markRaw(TrendCharts), gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)', color: '#06b6d4' },
  { path: '/erp/sales/credit', title: '与信管理', description: '顧客与信限度額・リスク管理', icon: markRaw(CreditCard), gradient: 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#f59e0b' },
  { path: '/erp/sales/contract-pricing', title: '契約単価管理', description: '顧客別契約単価・割引管理', icon: markRaw(PriceTag), gradient: 'linear-gradient(135deg, #10b981, #059669)', color: '#10b981' },
  { path: '/erp/sales/shipping', title: '出荷指示', description: '出荷指示の作成・確定管理', icon: markRaw(Van), gradient: 'linear-gradient(135deg, #ec4899, #db2777)', color: '#ec4899' },
  { path: '/erp/sales/recording', title: '売上計上', description: '月次売上計上・集計管理', icon: markRaw(Coin), gradient: 'linear-gradient(135deg, #14b8a6, #0d9488)', color: '#14b8a6' },
  { path: '/erp/sales/invoice', title: '請求書発行', description: '請求書作成・発行・入金管理', icon: markRaw(Money), gradient: 'linear-gradient(135deg, #6366f1, #4f46e5)', color: '#6366f1' },
  { path: '/erp/sales/return-correction', title: '赤黒訂正処理', description: '売上訂正・赤伝票処理', icon: markRaw(RefreshLeft), gradient: 'linear-gradient(135deg, #f97316, #ea580c)', color: '#f97316' },
  { path: '/erp/sales/returns', title: '返品管理(RMA)', description: '返品受付・検品・返金処理', icon: markRaw(DataAnalysis), gradient: 'linear-gradient(135deg, #ef4444, #dc2626)', color: '#ef4444' },
]

function formatCurrency(n: number): string {
  if (n >= 1e8) return `¥${(n / 1e8).toFixed(1)}億`
  if (n >= 1e4) return `¥${(n / 1e4).toFixed(0)}万`
  return `¥${n.toLocaleString()}`
}

async function fetchStats() {
  loading.value = true
  try {
    const res: any = await request.get('/api/erp/sales/orders/stats')
    const data = res?.data ?? res
    if (data) {
      stats.value = data
      statCards.value[0].value = `${data.monthly_order_count || 0}件`
      statCards.value[1].value = formatCurrency(data.monthly_order_amount || 0)
      statCards.value[2].value = `${(data.monthly_confirmed_units || 0).toLocaleString()}本`
      statCards.value[3].value = `${data.pending_delivery_count || 0}件`
      statCards.value[4].value = `${data.completed_count || 0}件`
      statCards.value[5].value = formatCurrency(data.unpaid_amount || 0)
    }
  } catch (e) {
    console.error('Failed to fetch sales stats', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
</script>

<style scoped>
/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（販売管理 / インディゴ・ブルー系）
 * ============================================================ */
.sales-home {
  min-height: 100%;
  padding: 14px 16px 18px;
  background: linear-gradient(160deg, #eef2ff 0%, #eff6ff 45%, #f8fafc 100%);
}

/* ---------- ヘッダー ---------- */
.glass-header {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  margin-bottom: 14px;
  padding: 16px 22px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(125deg, #1e1b4b 0%, #3730a3 34%, #2563eb 68%, #0ea5e9 100%);
  box-shadow:
    0 18px 36px -18px rgba(55, 48, 163, 0.6),
    0 4px 12px -6px rgba(37, 99, 235, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
.header-fx {
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
}
.fx-orb {
  position: absolute;
  border-radius: 50%;
}
.orb-a {
  width: 260px;
  height: 260px;
  top: -130px;
  right: 26%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 70%);
}
.orb-b {
  width: 220px;
  height: 220px;
  bottom: -140px;
  left: 18%;
  background: radial-gradient(circle, rgba(165, 180, 252, 0.45) 0%, rgba(165, 180, 252, 0) 70%);
}
.fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 22px 22px;
  -webkit-mask-image: radial-gradient(ellipse at 15% 50%, #000 0%, transparent 70%);
  mask-image: radial-gradient(ellipse at 15% 50%, #000 0%, transparent 70%);
}
.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.42), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.45);
  box-shadow:
    0 3px 0 rgba(30, 27, 75, 0.55),
    0 10px 18px -8px rgba(30, 27, 75, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  transform: perspective(300px) rotateX(8deg) rotateY(-10deg);
}
.header-title {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #fff;
  text-shadow: 0 2px 6px rgba(30, 27, 75, 0.3);
}
.header-subtitle {
  margin-top: 4px;
  display: inline-block;
  padding: 1px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #fff;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.35);
}

/* ---------- 統計カード：白キーキャップ（色は stat.color） ---------- */
.stats-section {
  margin-bottom: 18px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.stat-card {
  --sc-edge: color-mix(in srgb, var(--sc) 72%, #000);
  padding: 12px 14px;
  border-radius: 13px;
  background: #fff;
  border: 1px solid color-mix(in srgb, var(--sc) 28%, #fff);
  box-shadow:
    0 3px 0 var(--sc-edge),
    0 12px 20px -14px rgba(15, 23, 42, 0.45);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 5px 0 var(--sc-edge),
    0 16px 24px -14px rgba(15, 23, 42, 0.5);
}
.stat-card-inner {
  display: flex;
  align-items: center;
  gap: 12px;
}
.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 11px;
  color: #fff;
  box-shadow: 0 2px 0 var(--sc-edge);
}
.stat-label {
  margin-bottom: 2px;
  font-size: 11px;
  font-weight: 700;
  color: var(--sc-edge);
}
.stat-value {
  font-size: 19px;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

/* ---------- 機能メニュー：色分けキーキャップ（色は mod.color） ---------- */
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px 2px;
  font-size: 15px;
  font-weight: 800;
  color: #312e81;
}
.section-title::before {
  content: '';
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: linear-gradient(180deg, #6366f1, #2563eb);
}
.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.module-card {
  --mc-edge: color-mix(in srgb, var(--mc) 72%, #000);
  position: relative;
  overflow: hidden;
  padding: 14px 16px 14px 18px;
  border-radius: 13px;
  text-decoration: none;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow:
    0 3px 0 #cbd5e1,
    0 12px 20px -14px rgba(15, 23, 42, 0.4);
  cursor: pointer;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    border-color 0.15s ease;
}
.module-card::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 4px;
  background: var(--mc);
}
.module-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--mc) 35%, #fff);
  box-shadow:
    0 5px 0 var(--mc-edge),
    0 16px 24px -14px rgba(15, 23, 42, 0.45);
}
.module-card:active {
  transform: translateY(1px);
  box-shadow: 0 1px 0 var(--mc-edge);
}
.module-card-inner {
  display: flex;
  align-items: center;
  gap: 12px;
}
.module-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  color: #fff;
  box-shadow: 0 2px 0 var(--mc-edge);
}
.module-info {
  flex: 1;
  min-width: 0;
}
.module-title {
  margin: 0 0 3px;
  font-size: 14px;
  font-weight: 800;
  color: #0f172a;
}
.module-desc {
  margin: 0;
  overflow: hidden;
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.module-arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  color: var(--mc);
  background: color-mix(in srgb, var(--mc) 10%, #fff);
  transition:
    transform 0.15s ease,
    color 0.15s ease,
    background-color 0.15s ease;
}
.module-card:hover .module-arrow {
  color: #fff;
  background: var(--mc);
  transform: translateX(2px);
}

@media (max-width: 768px) {
  .sales-home {
    padding: 10px;
  }
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .module-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .stat-card,
  .module-card,
  .module-arrow {
    transition: none;
  }
  .stat-card:hover,
  .module-card:hover,
  .module-card:active,
  .module-card:hover .module-arrow {
    transform: none;
  }
}
</style>
