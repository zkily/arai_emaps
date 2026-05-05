<template>
  <div class="sales-home">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="noise-overlay"></div>
    </div>

    <div class="glass-header animate-in">
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
          v-for="(stat, index) in statCards"
          :key="stat.key"
          class="stat-card glass-card animate-in"
          :style="{ animationDelay: `${0.1 + index * 0.05}s` }"
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
      <h2 class="section-title animate-in" style="animation-delay: 0.25s">機能メニュー</h2>
      <div class="module-grid">
        <router-link
          v-for="(mod, index) in modules"
          :key="mod.path"
          :to="mod.path"
          class="module-card glass-card animate-in"
          :style="{ animationDelay: `${0.3 + index * 0.04}s` }"
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
  { key: 'orders', label: '今月受注', value: '0件', gradient: 'linear-gradient(135deg, #3b82f6, #1d4ed8)', icon: markRaw(Document) },
  { key: 'amount', label: '今月売上', value: '¥0', gradient: 'linear-gradient(135deg, #10b981, #059669)', icon: markRaw(Money) },
  { key: 'units', label: '確定本数', value: '0本', gradient: 'linear-gradient(135deg, #8b5cf6, #6d28d9)', icon: markRaw(TrendCharts) },
  { key: 'pending', label: '出荷待ち', value: '0件', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)', icon: markRaw(Van) },
  { key: 'completed', label: '今月完了', value: '0件', gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)', icon: markRaw(Ticket) },
  { key: 'unpaid', label: '未回収', value: '¥0', gradient: 'linear-gradient(135deg, #ef4444, #dc2626)', icon: markRaw(CreditCard) },
])

const modules = [
  { path: '/erp/sales/quotation', title: '見積管理', description: '見積書の作成・送付・受注変換', icon: markRaw(Document), gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)' },
  { path: '/erp/sales/orders', title: '受注一覧', description: '受注データの一覧管理・承認', icon: markRaw(List), gradient: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' },
  { path: '/erp/sales/forecast', title: '内示・フォーキャスト', description: '需要予測・内示データ管理', icon: markRaw(TrendCharts), gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)' },
  { path: '/erp/sales/credit', title: '与信管理', description: '顧客与信限度額・リスク管理', icon: markRaw(CreditCard), gradient: 'linear-gradient(135deg, #f59e0b, #d97706)' },
  { path: '/erp/sales/contract-pricing', title: '契約単価管理', description: '顧客別契約単価・割引管理', icon: markRaw(PriceTag), gradient: 'linear-gradient(135deg, #10b981, #059669)' },
  { path: '/erp/sales/shipping', title: '出荷指示', description: '出荷指示の作成・確定管理', icon: markRaw(Van), gradient: 'linear-gradient(135deg, #ec4899, #db2777)' },
  { path: '/erp/sales/recording', title: '売上計上', description: '月次売上計上・集計管理', icon: markRaw(Coin), gradient: 'linear-gradient(135deg, #14b8a6, #0d9488)' },
  { path: '/erp/sales/invoice', title: '請求書発行', description: '請求書作成・発行・入金管理', icon: markRaw(Money), gradient: 'linear-gradient(135deg, #6366f1, #4f46e5)' },
  { path: '/erp/sales/return-correction', title: '赤黒訂正処理', description: '売上訂正・赤伝票処理', icon: markRaw(RefreshLeft), gradient: 'linear-gradient(135deg, #f97316, #ea580c)' },
  { path: '/erp/sales/returns', title: '返品管理(RMA)', description: '返品受付・検品・返金処理', icon: markRaw(DataAnalysis), gradient: 'linear-gradient(135deg, #ef4444, #dc2626)' },
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
.sales-home {
  position: relative;
  min-height: 100vh;
  padding: 16px;
  overflow: hidden;
}

.dynamic-background {
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
}
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}
.orb-1 { width: 400px; height: 400px; top: -100px; left: -100px; background: radial-gradient(circle, #3b82f6, transparent); }
.orb-2 { width: 350px; height: 350px; top: 40%; right: -80px; background: radial-gradient(circle, #8b5cf6, transparent); animation-delay: -7s; }
.orb-3 { width: 300px; height: 300px; bottom: -50px; left: 30%; background: radial-gradient(circle, #06b6d4, transparent); animation-delay: -14s; }
.noise-overlay {
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.glass-header {
  position: relative;
  z-index: 1;
  background: rgba(255,255,255,0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 16px;
  padding: 16px 24px;
  margin-bottom: 16px;
}
.header-content { display: flex; align-items: center; gap: 16px; }
.header-left { display: flex; align-items: center; gap: 14px; }
.header-icon {
  width: 48px; height: 48px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  box-shadow: 0 4px 20px rgba(59,130,246,0.4);
}
.header-title { font-size: 1.5rem; font-weight: 700; color: #fff; margin: 0; }
.header-subtitle { font-size: 0.8rem; color: rgba(255,255,255,0.6); margin-top: 2px; }

.stats-section { position: relative; z-index: 1; margin-bottom: 16px; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.stat-card {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 14px;
  padding: 14px 16px;
  transition: all 0.3s ease;
}
.stat-card:hover { transform: translateY(-3px); border-color: rgba(255,255,255,0.2); background: rgba(255,255,255,0.1); }
.stat-card-inner { display: flex; align-items: center; gap: 12px; }
.stat-icon {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; color: #fff;
  flex-shrink: 0;
}
.stat-label { font-size: 0.72rem; color: rgba(255,255,255,0.6); margin-bottom: 2px; }
.stat-value { font-size: 1.1rem; font-weight: 700; color: #fff; }

.modules-section { position: relative; z-index: 1; }
.section-title { font-size: 1.1rem; font-weight: 600; color: rgba(255,255,255,0.9); margin: 0 0 12px 4px; }
.module-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; }
.module-card {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 14px;
  padding: 14px 16px;
  text-decoration: none;
  transition: all 0.3s ease;
  cursor: pointer;
}
.module-card:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.25); background: rgba(255,255,255,0.1); }
.module-card-inner { display: flex; align-items: center; gap: 12px; }
.module-icon {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; color: #fff;
  flex-shrink: 0;
}
.module-info { flex: 1; min-width: 0; }
.module-title { font-size: 0.9rem; font-weight: 600; color: #fff; margin: 0 0 3px; }
.module-desc { font-size: 0.72rem; color: rgba(255,255,255,0.55); margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.module-arrow { color: rgba(255,255,255,0.3); transition: color 0.3s; }
.module-card:hover .module-arrow { color: rgba(255,255,255,0.7); }

.animate-in {
  animation: slideIn 0.5s ease forwards;
  opacity: 0;
  transform: translateY(12px);
}
@keyframes slideIn {
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .sales-home { padding: 10px; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .module-grid { grid-template-columns: 1fr; }
}
</style>
