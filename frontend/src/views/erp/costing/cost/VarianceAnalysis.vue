<template>
  <div class="variance-analysis">
    <div class="page-hero">
      <div class="hero-text">
        <h2>原価差異分析</h2>
        <p>標準原価と実際原価の差異を7項目に分解し、材料・労務・間接ごとの改善ポイントを特定します。</p>
      </div>
      <div class="hero-nav">
        <router-link to="/erp/costing/standard" class="nav-chip">標準原価 設定</router-link>
        <router-link to="/erp/costing/actual" class="nav-chip accent">実際原価</router-link>
      </div>
    </div>

    <!-- フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" class="compact-form">
        <el-form-item label="対象期間">
          <el-select v-model="selectedPeriodId" placeholder="選択" filterable style="width: 200px" @change="onPeriodChange">
            <el-option v-for="p in periods" :key="p.id" :label="`${p.year_month}（${p.status}）`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="品番">
          <el-input v-model="keyword" clearable style="width: 160px" placeholder="部分一致" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData"><el-icon><DataAnalysis /></el-icon> 分析</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- サマリー 3 cards -->
    <div class="summary-row">
      <div class="big-card std">
        <div class="big-label">標準許容（合計）</div>
        <div class="big-value">¥{{ money(totalStd) }}</div>
      </div>
      <div class="big-card act">
        <div class="big-label">実際原価（合計）</div>
        <div class="big-value">¥{{ money(totalAct) }}</div>
      </div>
      <div class="big-card" :class="grandVariance <= 0 ? 'fav-bg' : 'unfav-bg'">
        <div class="big-label">原価差異（合計）</div>
        <div class="big-value">{{ signedMoney(grandVariance) }}</div>
        <div class="big-note">{{ grandVariance <= 0 ? '有利差異' : '不利差異' }}</div>
      </div>
    </div>

    <!-- 7-bar breakdown -->
    <el-card shadow="never" class="breakdown-card">
      <template #header>
        <span class="card-title">差異7項目ブレークダウン</span>
      </template>
      <div class="bar-list">
        <div v-for="b in barData" :key="b.key" class="bar-row">
          <div class="bar-label">
            <el-tag :type="b.group === 'material' ? 'success' : b.group === 'labor' ? 'primary' : 'warning'" size="small" effect="plain">
              {{ b.groupLabel }}
            </el-tag>
            <span>{{ b.label }}</span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" :class="b.value <= 0 ? 'fav' : 'unfav'" :style="{ width: barWidth(b.value) }" />
          </div>
          <div class="bar-amount" :class="b.value <= 0 ? 'fav' : 'unfav'">
            {{ signedMoney(b.value) }}
          </div>
        </div>
      </div>
    </el-card>

    <!-- 品目別テーブル -->
    <el-card shadow="never" class="table-card">
      <template #header><span class="card-title">品目別差異詳細</span></template>
      <el-table v-loading="loading" :data="filteredList" stripe border size="small" class="compact-table">
        <el-table-column prop="product_cd" label="品番" width="100" fixed />
        <el-table-column prop="product_name" label="品名" min-width="130" show-overflow-tooltip />
        <el-table-column label="材料価格" width="96" align="right" header-align="center">
          <template #default="{ row }"><span :class="vc(row.variance_material_price)">{{ signedMoney(row.variance_material_price) }}</span></template>
        </el-table-column>
        <el-table-column label="材料数量" width="96" align="right" header-align="center">
          <template #default="{ row }"><span :class="vc(row.variance_material_qty)">{{ signedMoney(row.variance_material_qty) }}</span></template>
        </el-table-column>
        <el-table-column label="賃率" width="90" align="right" header-align="center">
          <template #default="{ row }"><span :class="vc(row.variance_labor_rate)">{{ signedMoney(row.variance_labor_rate) }}</span></template>
        </el-table-column>
        <el-table-column label="時間" width="90" align="right" header-align="center">
          <template #default="{ row }"><span :class="vc(row.variance_labor_efficiency)">{{ signedMoney(row.variance_labor_efficiency) }}</span></template>
        </el-table-column>
        <el-table-column label="予算" width="90" align="right" header-align="center">
          <template #default="{ row }"><span :class="vc(row.variance_moh_budget)">{{ signedMoney(row.variance_moh_budget) }}</span></template>
        </el-table-column>
        <el-table-column label="稼働" width="90" align="right" header-align="center">
          <template #default="{ row }"><span :class="vc(row.variance_moh_capacity)">{{ signedMoney(row.variance_moh_capacity) }}</span></template>
        </el-table-column>
        <el-table-column label="能率" width="90" align="right" header-align="center">
          <template #default="{ row }"><span :class="vc(row.variance_moh_efficiency)">{{ signedMoney(row.variance_moh_efficiency) }}</span></template>
        </el-table-column>
        <el-table-column label="差異合計" width="110" align="right" header-align="center">
          <template #default="{ row }">
            <strong :class="vc(row.variance_grand_total)">{{ row.variance_grand_total != null ? signedMoney(row.variance_grand_total) : '—' }}</strong>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!filteredList.length && !loading" class="empty-hint">
        <el-empty :image-size="80" description="対象期間のデータがありません" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis } from '@element-plus/icons-vue'
import {
  fetchCostPeriods,
  fetchPeriodProducts,
  type CostAccountingPeriod,
  type CostPeriodProductLine,
} from '@/api/erp/standardCost'

const loading = ref(false)
const periods = ref<CostAccountingPeriod[]>([])
const selectedPeriodId = ref<number | undefined>()
const allLines = ref<CostPeriodProductLine[]>([])
const keyword = ref('')

const filteredList = computed(() => {
  if (!keyword.value) return allLines.value
  const k = keyword.value.toLowerCase()
  return allLines.value.filter(
    (r) => r.product_cd.toLowerCase().includes(k) || (r.product_name ?? '').toLowerCase().includes(k),
  )
})

function n(v: number | null | undefined) { return Number(v ?? 0) }
function money(v: number | null | undefined) {
  const x = n(v)
  return Number.isFinite(x) ? x.toLocaleString('ja-JP', { maximumFractionDigits: 0 }) : '0'
}
function signedMoney(v: number | null | undefined) {
  const x = n(v)
  return `${x >= 0 ? '+' : ''}¥${money(Math.abs(x))}`
}
function vc(v: number | null | undefined) { return n(v) <= 0 ? 'fav' : 'unfav' }

const totalStd = computed(() =>
  filteredList.value.reduce((s, r) => s + n(r.standard_material_allowed) + n(r.standard_labor_allowed) + n(r.standard_overhead_allowed), 0),
)
const totalAct = computed(() =>
  filteredList.value.reduce((s, r) => s + n(r.actual_material_cost) + n(r.actual_labor_cost) + n(r.actual_overhead_cost), 0),
)
const grandVariance = computed(() => totalAct.value - totalStd.value)

interface BarItem { key: string; label: string; group: string; groupLabel: string; value: number }
const barData = computed<BarItem[]>(() => {
  const sum = (field: keyof CostPeriodProductLine) => filteredList.value.reduce((s, r) => s + n(r[field] as number | null | undefined), 0)
  return [
    { key: 'mp', label: '価格差異', group: 'material', groupLabel: '材料', value: sum('variance_material_price') },
    { key: 'mq', label: '数量差異', group: 'material', groupLabel: '材料', value: sum('variance_material_qty') },
    { key: 'lr', label: '賃率差異', group: 'labor', groupLabel: '労務', value: sum('variance_labor_rate') },
    { key: 'le', label: '時間差異', group: 'labor', groupLabel: '労務', value: sum('variance_labor_efficiency') },
    { key: 'ob', label: '予算差異', group: 'oh', groupLabel: '間接', value: sum('variance_moh_budget') },
    { key: 'oc', label: '操業度差異', group: 'oh', groupLabel: '間接', value: sum('variance_moh_capacity') },
    { key: 'oe', label: '能率差異', group: 'oh', groupLabel: '間接', value: sum('variance_moh_efficiency') },
  ]
})
const maxBar = computed(() => Math.max(...barData.value.map((b) => Math.abs(b.value)), 1))
function barWidth(v: number) { return `${(Math.abs(v) / maxBar.value) * 100}%` }

async function loadPeriods() {
  try {
    periods.value = await fetchCostPeriods()
    if (periods.value.length && !selectedPeriodId.value) {
      selectedPeriodId.value = periods.value[0].id
      await loadData()
    }
  } catch { periods.value = [] }
}

async function loadData() {
  if (!selectedPeriodId.value) { allLines.value = []; return }
  loading.value = true
  try {
    allLines.value = await fetchPeriodProducts(selectedPeriodId.value)
  } catch {
    allLines.value = []
    ElMessage.error('差異データの取得に失敗しました')
  } finally { loading.value = false }
}

function onPeriodChange() { loadData() }

onMounted(() => loadPeriods())
</script>

<style scoped>
.variance-analysis { padding: 16px 20px; }

.page-hero {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 24px; margin-bottom: 14px; border-radius: 12px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: #fff;
}
.hero-text h2 { margin: 0 0 4px; font-size: 20px; font-weight: 700; }
.hero-text p { margin: 0; font-size: 13px; opacity: .85; }
.hero-nav { display: flex; gap: 8px; flex-shrink: 0; }
.nav-chip {
  padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;
  background: rgba(255,255,255,.2); color: #fff; text-decoration: none; transition: background .2s;
}
.nav-chip:hover { background: rgba(255,255,255,.35); }
.nav-chip.accent { background: rgba(255,255,255,.92); color: #0288d1; }
.nav-chip.accent:hover { background: #fff; }

.filter-card { margin-bottom: 12px; }
.filter-card :deep(.el-card__body) { padding: 12px 16px; }
.compact-form :deep(.el-form-item) { margin-bottom: 0; }

.summary-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 14px; }
.big-card {
  text-align: center; padding: 16px; border-radius: 10px;
  border: 1px solid #ebeef5; background: #fff;
}
.big-card.std { border-left: 4px solid #409eff; }
.big-card.act { border-left: 4px solid #e6a23c; }
.big-card.fav-bg { border-left: 4px solid #67c23a; background: #f0f9eb; }
.big-card.unfav-bg { border-left: 4px solid #f56c6c; background: #fef0f0; }
.big-label { font-size: 12px; color: #909399; margin-bottom: 4px; }
.big-value { font-size: 24px; font-weight: 700; color: #303133; }
.big-card.fav-bg .big-value { color: #67c23a; }
.big-card.unfav-bg .big-value { color: #f56c6c; }
.big-note { font-size: 11px; color: #909399; margin-top: 2px; }

.breakdown-card { margin-bottom: 14px; }
.breakdown-card :deep(.el-card__body) { padding: 14px 18px; }
.breakdown-card :deep(.el-card__header) { padding: 12px 18px; }
.card-title { font-weight: 600; font-size: 14px; }
.bar-list { display: flex; flex-direction: column; gap: 10px; }
.bar-row { display: grid; grid-template-columns: 160px 1fr 110px; gap: 10px; align-items: center; }
.bar-label { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.bar-track { height: 22px; background: #f5f7fa; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width .4s ease; min-width: 2px; }
.bar-fill.fav { background: linear-gradient(90deg, #67c23a, #95d475); }
.bar-fill.unfav { background: linear-gradient(90deg, #f56c6c, #fab6b6); }
.bar-amount { text-align: right; font-weight: 700; font-size: 13px; }

.table-card :deep(.el-card__body) { padding: 12px; }
.table-card :deep(.el-card__header) { padding: 12px 16px; }
.compact-table :deep(th .cell) { font-size: 12px; white-space: nowrap; }
.fav { color: #67c23a; font-weight: 600; }
.unfav { color: #f56c6c; font-weight: 600; }
.empty-hint { padding: 16px 0; }
</style>
