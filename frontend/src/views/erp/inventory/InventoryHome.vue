<template>
  <div class="inventory-home">
    <div class="page-bg">
      <div class="bg-gradient"></div>
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
      <div class="bg-orb bg-orb-3"></div>
    </div>

    <div class="page-inner">
      <header class="top-bar glass animate-in" style="--delay: 0s">
        <div class="top-bar-info">
          <div class="brand-icon">
            <el-icon :size="26"><Box /></el-icon>
          </div>
          <div>
            <h1 class="page-title">在庫管理</h1>
            <p class="page-meta">{{ todayDateStr }} · 製品 / 材料 / 部品 当日サマリ</p>
          </div>
        </div>
        <nav class="quick-nav quick-nav--bar" aria-label="ショートカット">
          <router-link
            v-for="m in quickNavModules"
            :key="m.path"
            :to="m.path"
            class="quick-nav-item"
            :title="m.title"
          >
            <span class="quick-nav-icon" :style="{ background: m.gradient }">
              <el-icon :size="17"><component :is="m.icon" /></el-icon>
            </span>
            <span class="quick-nav-label">{{ m.title }}</span>
          </router-link>
        </nav>
      </header>

      <div class="stats-stack">
    <!-- 製品在庫：工程別（生産サマリ当日） -->
    <div class="stat-category animate-in" style="--delay: 0.02s">
      <div class="stat-category-head stat-category-head--product">
        <el-icon :size="20"><List /></el-icon>
        <span class="stat-category-title">製品在庫</span>
        <span class="stat-category-sub">工程別 · 当日集計</span>
      </div>
      <div class="stat-cards glass stat-cards--product" v-loading="loading">
        <div
          v-for="(item, i) in productStatCards"
          :key="item.key"
          class="stat-card"
          :style="{ '--i': i }"
        >
          <span class="stat-label">{{ item.label }}</span>
          <span class="stat-value" :class="item.sum < 0 ? 'num-negative' : ''">{{ formatNum(item.sum) }}</span>
        </div>
      </div>
    </div>

    <!-- 材料在庫：当日 material_stock 合計 -->
    <div class="stat-category animate-in" style="--delay: 0.06s">
      <div class="stat-category-head stat-category-head--material">
        <el-icon :size="20"><Grid /></el-icon>
        <span class="stat-category-title">材料在庫</span>
        <span class="stat-category-sub">当日分集計</span>
      </div>
      <div class="stat-cards glass stat-cards--material" v-loading="loading">
        <div
          v-for="(item, i) in materialStatCards"
          :key="item.key"
          class="stat-card"
          :style="{ '--i': i }"
        >
          <span class="stat-label">{{ item.label }}</span>
          <span class="stat-value" :class="item.sum < 0 ? 'num-negative' : ''">{{ formatNum(item.sum) }}</span>
        </div>
      </div>
    </div>

    <!-- 部品在庫：当日 part_stock 合計 -->
    <div class="stat-category animate-in" style="--delay: 0.1s">
      <div class="stat-category-head stat-category-head--part">
        <el-icon :size="20"><Files /></el-icon>
        <span class="stat-category-title">部品在庫</span>
        <span class="stat-category-sub">当日分集計</span>
      </div>
      <div class="stat-cards glass stat-cards--part" v-loading="loading">
        <div
          v-for="(item, i) in partStatCards"
          :key="item.key"
          class="stat-card"
          :style="{ '--i': i }"
        >
          <span class="stat-label">{{ item.label }}</span>
          <span class="stat-value" :class="item.sum < 0 ? 'num-negative' : ''">{{ formatNum(item.sum) }}</span>
        </div>
      </div>
    </div>
      </div>

    <!-- 在庫アラート -->
    <section class="alert-panel animate-in" style="--delay: 0.12s">
      <div class="alert-panel-head">
        <el-icon class="alert-head-icon"><Warning /></el-icon>
        <span class="alert-head-title">在庫アラート</span>
        <el-badge :value="alerts.length" type="danger" v-if="alerts.length > 0" />
      </div>
      <el-table :data="alerts" v-loading="loading" stripe size="small" class="alert-table">
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
    </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, markRaw } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Box, Warning,
  List, Document, Memo, Grid, Files
} from '@element-plus/icons-vue'
import { getStockAlerts } from '@/api/erp/inventory'
import type { StockAlert } from '@/types/erp/inventory'
import { getProductionSummarysList, type ProductionSummaryInventoryRow } from '@/api/database'
import { getMaterialStockList } from '@/api/material'
import { getPartStockList } from '@/api/part'

const loading = ref(false)
const summaryList = ref<ProductionSummaryInventoryRow[]>([])
const materialStockRows = ref<Record<string, unknown>[]>([])
const partStockRows = ref<Record<string, unknown>[]>([])
const alerts = ref<StockAlert[]>([])

/** 在庫一覧（InventoryList）と同一の工程フィールド */
const INVENTORY_FIELDS: { key: keyof ProductionSummaryInventoryRow; label: string }[] = [
  { key: 'cutting_inventory', label: '切断' },
  { key: 'chamfering_inventory', label: '面取' },
  { key: 'molding_inventory', label: '成型' },
  { key: 'plating_inventory', label: 'メッキ' },
  { key: 'welding_inventory', label: '溶接' },
  { key: 'inspection_inventory', label: '検査' },
  { key: 'warehouse_inventory', label: '倉庫' },
  { key: 'outsourced_warehouse_inventory', label: '外注倉庫' },
  { key: 'outsourced_plating_inventory', label: '外注メッキ' },
  { key: 'outsourced_welding_inventory', label: '外注溶接' },
  { key: 'pre_welding_inspection_inventory', label: '溶接前検査' },
  { key: 'pre_inspection_inventory', label: '支給前' },
  { key: 'pre_outsourcing_inventory', label: '検査前' }
]

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

const todayDateStr = computed(() => todayStr())

const productStatCards = computed(() => {
  const data = summaryList.value
  return INVENTORY_FIELDS.map(({ key, label }) => {
    const sum = data.reduce((acc, row) => acc + (Number(row[key]) || 0), 0)
    return { key, label, sum }
  })
})

function sumField(rows: Record<string, unknown>[], key: string): number {
  return rows.reduce((acc, row) => acc + (Number(row[key]) || 0), 0)
}

const MATERIAL_STAT_KEYS: { key: string; label: string }[] = [
  { key: 'current_stock', label: '現在在庫' },
  { key: 'safety_stock', label: '安全在庫' },
  { key: 'planned_usage', label: '使用数' },
  { key: 'order_quantity', label: '注文数' }
]

const PART_STAT_KEYS: { key: string; label: string }[] = [
  { key: 'current_stock', label: '現在在庫' },
  { key: 'planned_usage', label: '使用数' },
  { key: 'usage_plan_qty', label: '計画使用' },
  { key: 'order_quantity', label: '注文数' }
]

const materialStatCards = computed(() => {
  const rows = materialStockRows.value
  return MATERIAL_STAT_KEYS.map(({ key, label }) => ({
    key,
    label,
    sum: sumField(rows, key)
  }))
})

const partStatCards = computed(() => {
  const rows = partStockRows.value
  return PART_STAT_KEYS.map(({ key, label }) => ({
    key,
    label,
    sum: sumField(rows, key)
  }))
})

function formatNum(v: number | null | undefined): string {
  if (v == null) return '0'
  return Number(v).toLocaleString()
}

type QuickNavItem = {
  path: string
  title: string
  icon: ReturnType<typeof markRaw>
  gradient: string
}

/** 照会・業務へのショートカット（一覧・小アイコン） */
const quickNavModules: QuickNavItem[] = [
  {
    path: '/erp/inventory/list',
    title: '製品在庫照会',
    icon: markRaw(List),
    gradient: 'linear-gradient(135deg, #409eff, #67c23a)'
  },
  {
    path: '/erp/inventory/material-list',
    title: '材料在庫照会',
    icon: markRaw(Grid),
    gradient: 'linear-gradient(135deg, #14b8a6, #3b82f6)'
  },
  {
    path: '/erp/inventory/part-list',
    title: '部品在庫照会',
    icon: markRaw(Files),
    gradient: 'linear-gradient(135deg, #f97316, #ea580c)'
  },
  {
    path: '/erp/inventory/stock-entry',
    title: '在庫登録管理',
    icon: markRaw(Document),
    gradient: 'linear-gradient(135deg, #67c23a, #85ce61)'
  },
  {
    path: '/erp/inventory/stocktake',
    title: '棚卸管理',
    icon: markRaw(Memo),
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)'
  }
]

// 获取预警类型样式（el-tag 的 type）
type AlertTagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'
const getAlertType = (type: string): AlertTagType => {
  const typeMap: Record<string, AlertTagType> = {
    low_stock: 'warning',
    overstock: 'info',
    expiring: 'danger',
    expired: 'danger'
  }
  return typeMap[type] ?? 'info'
}

// 处理预警
const handleAlert = (row: StockAlert) => {
  ElMessage.info(`アラート ID: ${row.id} の対応画面へ遷移します`)
}

async function fetchTodayProductionSummary() {
  const d = todayStr()
  const res = await getProductionSummarysList({
    page: 1,
    limit: 50000,
    startDate: d,
    endDate: d,
    sortBy: 'product_name',
    sortOrder: 'ASC'
  })
  const data = res?.data ?? res
  const listData = data?.list ?? data?.data?.list ?? []
  summaryList.value = listData as ProductionSummaryInventoryRow[]
}

async function fetchTodayMaterialStock() {
  const d = todayStr()
  const res = await getMaterialStockList({
    page: 1,
    pageSize: 10000,
    start_date: d,
    end_date: d
  })
  const list = res?.data?.list ?? []
  materialStockRows.value = Array.isArray(list) ? (list as Record<string, unknown>[]) : []
}

async function fetchTodayPartStock() {
  const d = todayStr()
  const res = await getPartStockList({
    page: 1,
    pageSize: 10000,
    start_date: d,
    end_date: d
  })
  const list = res?.data?.list ?? []
  partStockRows.value = Array.isArray(list) ? (list as Record<string, unknown>[]) : []
}

// 加载数据
const fetchData = async () => {
  loading.value = true
  try {
    const [, , , alertsRes] = await Promise.all([
      fetchTodayProductionSummary(),
      fetchTodayMaterialStock(),
      fetchTodayPartStock(),
      getStockAlerts({ status: 'active', page_size: 10 })
    ])
    alerts.value = (alertsRes.data?.items ?? []) as StockAlert[]
  } catch (error) {
    console.error('データ取得に失敗しました', error)
    summaryList.value = []
    materialStockRows.value = []
    partStockRows.value = []
    alerts.value = []
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
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  padding: 0;
  color: rgba(255, 255, 255, 0.92);
}

.page-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 120% 80% at 10% -10%, rgba(59, 130, 246, 0.35), transparent 50%),
    radial-gradient(ellipse 90% 70% at 100% 20%, rgba(139, 92, 246, 0.28), transparent 45%),
    radial-gradient(ellipse 80% 60% at 50% 100%, rgba(16, 185, 129, 0.12), transparent 50%),
    linear-gradient(165deg, #0f172a 0%, #1e293b 42%, #0f172a 100%);
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(48px);
  opacity: 0.45;
  animation: orbFloat 22s ease-in-out infinite;
}

.bg-orb-1 {
  width: min(420px, 55vw);
  height: min(420px, 55vw);
  top: -12%;
  right: -8%;
  background: radial-gradient(circle, rgba(96, 165, 250, 0.55), transparent 68%);
}

.bg-orb-2 {
  width: min(320px, 45vw);
  height: min(320px, 45vw);
  bottom: -10%;
  left: -6%;
  background: radial-gradient(circle, rgba(167, 139, 250, 0.45), transparent 70%);
  animation-delay: -9s;
}

.bg-orb-3 {
  width: min(260px, 38vw);
  height: min(260px, 38vw);
  top: 42%;
  left: 28%;
  background: radial-gradient(circle, rgba(45, 212, 191, 0.22), transparent 72%);
  animation-delay: -14s;
}

@keyframes orbFloat {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  40% {
    transform: translate(12px, -18px) scale(1.04);
  }
  70% {
    transform: translate(-10px, 10px) scale(0.98);
  }
}

.page-inner {
  position: relative;
  z-index: 1;
  max-width: 1440px;
  margin: 0 auto;
  padding: 10px 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.top-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 14px;
  padding: 10px 14px;
  border-radius: 14px;
}

.top-bar-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  background: linear-gradient(135deg, #3b82f6, #22c55e);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.page-title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.page-meta {
  margin: 2px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 统计卡片（与 InventoryList.vue の stat-cards 同様） */
.glass {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.animate-in {
  animation: fadeInUp 0.5s ease-out forwards;
  opacity: 0;
  animation-delay: var(--delay, 0s);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stats-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-category {
  margin-bottom: 0;
}

.stat-category-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  padding: 0 2px;
}

.stat-category-head .stat-category-title {
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
}

.stat-category-sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.68);
  font-weight: 500;
  margin-left: 2px;
}

.stat-category-head--product .el-icon {
  color: #a7f3d0;
}
.stat-category-head--material .el-icon {
  color: #67e8f9;
}
.stat-category-head--part .el-icon {
  color: #fed7aa;
}

.stat-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 14px;
}

.stat-cards--product {
  border-left: 3px solid rgba(96, 165, 250, 0.85);
}

.stat-cards--material {
  border-left: 3px solid rgba(45, 212, 191, 0.65);
}

.stat-cards--part {
  border-left: 3px solid rgba(251, 146, 60, 0.75);
}

.stat-cards .stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 70px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 11px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.25s ease;
  animation: cardIn 0.4s ease-out backwards;
  animation-delay: calc(var(--delay, 0s) + 0.02s * var(--i, 0));
}

.stat-cards .stat-card:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.18);
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

@keyframes cardIn {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.stat-cards .stat-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.52);
  margin-bottom: 3px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.stat-cards .stat-value {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  transition: color 0.2s ease;
}

.stat-cards .stat-value.num-negative {
  color: #f87171;
  text-shadow: 0 0 20px rgba(248, 113, 113, 0.3);
}

/* 機能ショートカット（ヘッダー内） */
.quick-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
}

.quick-nav--bar {
  justify-content: flex-end;
  flex: 1;
  min-width: min(100%, 280px);
}

.quick-nav-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px 4px 4px;
  border-radius: 999px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  transition: background 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease;
}

.quick-nav-item:hover {
  background: rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.quick-nav-icon {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.quick-nav-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

/* 在庫アラート */
.alert-panel {
  padding: 10px 12px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.97);
  color: #1e293b;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.35);
}

.alert-panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.alert-head-icon {
  color: #f59e0b;
}

.alert-table {
  border-radius: 10px;
  overflow: hidden;
}

.alert-table :deep(.el-table) {
  --el-table-border-color: rgba(15, 23, 42, 0.06);
  --el-table-header-bg-color: rgba(241, 245, 249, 0.95);
  font-size: 12px;
}

.alert-table :deep(.el-table th.el-table__cell) {
  font-weight: 600;
  color: #475569;
}

@media (max-width: 900px) {
  .top-bar {
    align-items: flex-start;
  }

  .quick-nav--bar {
    justify-content: flex-start;
    width: 100%;
  }

  .page-meta {
    white-space: normal;
  }
}

@media (max-width: 768px) {
  .page-inner {
    padding: 8px 10px 14px;
    gap: 8px;
  }

  .quick-nav-label {
    font-size: 10px;
  }

  .page-title {
    font-size: 1.2rem;
  }
}
</style>
