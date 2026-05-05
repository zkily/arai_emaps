<template>
  <div class="actual-costing">
    <div class="page-hero">
      <div class="hero-text">
        <h2>実際原価計算</h2>
        <p>月次品目別の実績材料費・労務費・間接費を集計。標準原価との対比ベースで原価管理を実現します。</p>
      </div>
      <div class="hero-nav">
        <router-link to="/erp/costing/standard" class="nav-chip">標準原価 設定</router-link>
        <router-link to="/erp/costing/variance" class="nav-chip accent">差異分析</router-link>
      </div>
    </div>

    <!-- フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" class="compact-form">
        <el-form-item label="対象期間">
          <el-select
            v-model="selectedPeriodId"
            placeholder="会計期間を選択"
            filterable
            style="width: 200px"
            @change="onPeriodChange"
          >
            <el-option
              v-for="p in periods"
              :key="p.id"
              :label="`${p.year_month}（${p.status}）`"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="品番">
          <el-input v-model="keyword" clearable style="width: 160px" placeholder="絞り込み" @keyup.enter="applyFilter" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="applyFilter"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- サマリー -->
    <div class="stat-row">
      <div class="stat-card mat">
        <div class="stat-icon"><el-icon :size="22"><Box /></el-icon></div>
        <div class="stat-body">
          <div class="stat-label">実際材料費</div>
          <div class="stat-value">¥{{ money(totalActualMaterial) }}</div>
        </div>
      </div>
      <div class="stat-card lab">
        <div class="stat-icon"><el-icon :size="22"><Timer /></el-icon></div>
        <div class="stat-body">
          <div class="stat-label">実際労務費</div>
          <div class="stat-value">¥{{ money(totalActualLabor) }}</div>
        </div>
      </div>
      <div class="stat-card oh">
        <div class="stat-icon"><el-icon :size="22"><Setting /></el-icon></div>
        <div class="stat-body">
          <div class="stat-label">実際間接費</div>
          <div class="stat-value">¥{{ money(totalActualOverhead) }}</div>
        </div>
      </div>
      <div class="stat-card total">
        <div class="stat-icon"><el-icon :size="22"><TrendCharts /></el-icon></div>
        <div class="stat-body">
          <div class="stat-label">実際原価合計</div>
          <div class="stat-value">¥{{ money(totalActual) }}</div>
        </div>
      </div>
      <div class="stat-card items">
        <div class="stat-icon"><el-icon :size="22"><Document /></el-icon></div>
        <div class="stat-body">
          <div class="stat-label">品目数</div>
          <div class="stat-value">{{ filteredList.length }}</div>
        </div>
      </div>
    </div>

    <!-- テーブル -->
    <el-card shadow="never" class="table-card">
      <el-table v-loading="loading" :data="filteredList" stripe border size="small" class="compact-table">
        <el-table-column prop="product_cd" label="品番" width="110" fixed />
        <el-table-column prop="product_name" label="品名" min-width="140" show-overflow-tooltip />
        <el-table-column label="完成数" width="80" align="right">
          <template #default="{ row }">{{ fmt(row.finished_good_qty) }}</template>
        </el-table-column>
        <el-table-column label="仕掛約当" width="86" align="right">
          <template #default="{ row }">{{ fmt(row.wip_equivalent_qty) }}</template>
        </el-table-column>
        <el-table-column label="実際材料費" width="110" align="right" header-align="center">
          <template #default="{ row }">
            <span v-if="row.actual_material_cost != null">¥{{ money(row.actual_material_cost) }}</span>
            <span v-else class="dim">未入力</span>
          </template>
        </el-table-column>
        <el-table-column label="実際労務費" width="110" align="right" header-align="center">
          <template #default="{ row }">
            <span v-if="row.actual_labor_cost != null">¥{{ money(row.actual_labor_cost) }}</span>
            <span v-else class="dim">未入力</span>
          </template>
        </el-table-column>
        <el-table-column label="実際間接費" width="110" align="right" header-align="center">
          <template #default="{ row }">
            <span v-if="row.actual_overhead_cost != null">¥{{ money(row.actual_overhead_cost) }}</span>
            <span v-else class="dim">未入力</span>
          </template>
        </el-table-column>
        <el-table-column label="実際合計" width="120" align="right" header-align="center">
          <template #default="{ row }">
            <strong class="accent-text">¥{{ money(actualTotal(row)) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="標準合計" width="120" align="right" header-align="center">
          <template #default="{ row }">
            <span>¥{{ money(stdTotal(row)) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="差異" width="110" align="right" header-align="center">
          <template #default="{ row }">
            <template v-if="row.variance_grand_total != null">
              <span :class="row.variance_grand_total <= 0 ? 'fav' : 'unfav'">
                {{ signedMoney(row.variance_grand_total) }}
              </span>
            </template>
            <span v-else class="dim">—</span>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!filteredList.length && !loading" class="empty-hint">
        <el-empty :image-size="80" description="データがありません。標準原価画面の「月次実績・差異」タブで品目と実績を入力してください。" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Box, Timer, Setting, TrendCharts, Document } from '@element-plus/icons-vue'
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

function n(v: number | null | undefined): number { return Number(v ?? 0) }
function money(v: number | null | undefined) {
  const x = n(v)
  return Number.isFinite(x) ? x.toLocaleString('ja-JP', { maximumFractionDigits: 0 }) : '0'
}
function fmt(v: number | null | undefined) {
  const x = n(v)
  return Number.isFinite(x) ? x.toLocaleString('ja-JP', { maximumFractionDigits: 2 }) : '0'
}
function signedMoney(v: number) {
  const x = n(v)
  return `${x >= 0 ? '+' : ''}¥${money(Math.abs(x))}`
}
function actualTotal(r: CostPeriodProductLine) { return n(r.actual_material_cost) + n(r.actual_labor_cost) + n(r.actual_overhead_cost) }
function stdTotal(r: CostPeriodProductLine) { return n(r.standard_material_allowed) + n(r.standard_labor_allowed) + n(r.standard_overhead_allowed) }

const totalActualMaterial = computed(() => filteredList.value.reduce((s, r) => s + n(r.actual_material_cost), 0))
const totalActualLabor = computed(() => filteredList.value.reduce((s, r) => s + n(r.actual_labor_cost), 0))
const totalActualOverhead = computed(() => filteredList.value.reduce((s, r) => s + n(r.actual_overhead_cost), 0))
const totalActual = computed(() => totalActualMaterial.value + totalActualLabor.value + totalActualOverhead.value)

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
    ElMessage.error('実績データの取得に失敗しました')
  } finally { loading.value = false }
}

function onPeriodChange() { loadData() }
function applyFilter() { /* computed handles it */ }

onMounted(() => loadPeriods())
</script>

<style scoped>
.actual-costing { padding: 16px 20px; }

.page-hero {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 24px; margin-bottom: 14px; border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
.nav-chip.accent { background: rgba(255,255,255,.92); color: #764ba2; }
.nav-chip.accent:hover { background: #fff; }

.filter-card { margin-bottom: 12px; }
.filter-card :deep(.el-card__body) { padding: 12px 16px; }
.compact-form :deep(.el-form-item) { margin-bottom: 0; }

.stat-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 14px; }
.stat-card {
  display: flex; align-items: center; gap: 12px; padding: 14px 16px;
  border-radius: 10px; border: 1px solid #ebeef5; background: #fff;
}
.stat-icon {
  width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.stat-card.mat .stat-icon  { background: #e8f5e9; color: #43a047; }
.stat-card.lab .stat-icon  { background: #e3f2fd; color: #1e88e5; }
.stat-card.oh .stat-icon   { background: #fff3e0; color: #ef6c00; }
.stat-card.total .stat-icon { background: #ede7f6; color: #5e35b1; }
.stat-card.items .stat-icon { background: #fce4ec; color: #c62828; }
.stat-label { font-size: 11px; color: #909399; }
.stat-value { font-size: 18px; font-weight: 700; color: #303133; }

.table-card :deep(.el-card__body) { padding: 12px; }
.compact-table :deep(th .cell) { font-size: 12px; }
.accent-text { color: #5e35b1; }
.dim { color: #c0c4cc; font-size: 12px; }
.fav { color: #67c23a; font-weight: 600; }
.unfav { color: #f56c6c; font-weight: 600; }
.empty-hint { padding: 20px 0; }

@media (max-width: 1200px) { .stat-row { grid-template-columns: repeat(3, 1fr); } }
</style>
