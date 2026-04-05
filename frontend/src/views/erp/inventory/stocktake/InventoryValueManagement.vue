<template>
  <div class="inventory-value-management">
    <!-- ページヘッダー -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <Operation class="icon" />
          </div>
          <div class="header-text">
            <h1 class="page-title">棚卸金額管理</h1>
            <p class="page-description">在庫金額の計算・分析・レポート管理</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button size="small" @click="goToBom">BOM管理</el-button>
          <el-button size="small" @click="goToUnitPrice">原価管理</el-button>
          <el-button type="warning" size="small" :loading="calculating" @click="runCalculation">
            計算実行
          </el-button>
        </div>
      </div>
    </div>

    <!-- エラー・警告パネル -->
    <div v-if="errors.length > 0" class="alert-panel">
      <el-alert type="warning" :closable="false" show-icon>
        <template #title>
          <span>未定価・設定不備が {{ errors.length }} 件あります</span>
        </template>
        <div class="error-list">
          <div v-for="(err, idx) in errors.slice(0, 5)" :key="idx" class="error-item">
            <el-tag :type="errorTagType(err.error_code)" size="small">{{ errorLabel(err.error_code) }}</el-tag>
            <span class="error-detail">{{ err.product_cd }} / {{ err.process_cd || '—' }}: {{ err.error_message }}</span>
          </div>
          <div v-if="errors.length > 5" class="error-more">
            ...他 {{ errors.length - 5 }} 件
          </div>
        </div>
      </el-alert>
    </div>

    <!-- 期间筛选条件 -->
    <div class="filter-container">
      <div class="filter-row">
        <div class="filter-item">
          <label class="filter-label">期間選択</label>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            size="small"
            range-separator="～"
            start-placeholder="開始日"
            end-placeholder="終了日"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateChange"
            class="date-picker"
          />
        </div>
        <div class="filter-item">
          <label class="filter-label">工程選択</label>
          <el-select
            v-model="selectedProcess"
            placeholder="工程を選択"
            size="small"
            @change="handleProcessChange"
            class="process-select"
          >
            <el-option label="全部" value="all" />
            <el-option
              v-for="process in processList"
              :key="process.process_cd"
              :label="process.process_name"
              :value="process.process_cd"
            />
          </el-select>
        </div>
        <div class="filter-actions">
          <el-button type="primary" size="small" @click="searchData" :loading="loading" class="search-btn">
            <Search class="btn-icon" />
            検索
          </el-button>
          <el-button size="small" @click="clearFilters" class="clear-btn">
            <RefreshLeft class="btn-icon" />
            クリア
          </el-button>
        </div>
      </div>
    </div>

    <!-- 金额统计卡片（合計は API の total_amount、内訳は材料・部品・その他） -->
    <div class="stats-container">
      <div class="stats-grid">
        <div class="stat-card total-card">
          <div class="stat-header">
            <div class="stat-badge total">合計</div>
          </div>
          <div class="stat-icon">
            <Money class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value">
              ¥{{ formatNumber(statistics.total?.total_amount || 0) }}
            </div>
            <div class="stat-label">棚卸金額合計</div>
          </div>
        </div>
        <div class="stat-card material-card">
          <div class="stat-header">
            <div class="stat-badge material">材料</div>
          </div>
          <div class="stat-icon">
            <Box class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value">
              ¥{{ formatNumber(statistics.total?.material_amount || 0) }}
            </div>
            <div class="stat-label">材料金額</div>
          </div>
        </div>
        <div class="stat-card component-card">
          <div class="stat-header">
            <div class="stat-badge component">部品</div>
          </div>
          <div class="stat-icon">
            <Setting class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value">
              ¥{{ formatNumber(statistics.total?.component_amount || 0) }}
            </div>
            <div class="stat-label">部品金額</div>
          </div>
        </div>
        <div class="stat-card stay-card">
          <div class="stat-header">
            <div class="stat-badge stay">ステー</div>
          </div>
          <div class="stat-icon">
            <Tools class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value">¥{{ formatNumber(statistics.total?.stay_amount || 0) }}</div>
            <div class="stat-label">ステー金額</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 标签页切换 -->
    <div class="content-tabs">
      <el-card class="tabs-card" shadow="never">
        <el-tabs v-model="activeTab" class="main-tabs">
          <el-tab-pane label="材料" name="material">
            <InventoryValueTable
              ref="materialTableRef"
              :date-range="dateRange"
              item-type="材料"
              :process-code="selectedProcess"
            />
          </el-tab-pane>

          <el-tab-pane label="部品" name="component">
            <InventoryValueTable
              ref="componentTableRef"
              :date-range="dateRange"
              item-type="部品"
              :process-code="selectedProcess"
            />
          </el-tab-pane>

          <el-tab-pane label="ステー" name="stay">
            <InventoryValueTable
              ref="stayTableRef"
              :date-range="dateRange"
              item-type="ステー"
              :process-code="selectedProcess"
            />
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Operation, Search, RefreshLeft, Box, Setting, Tools, Money } from '@element-plus/icons-vue'
import { inventoryValueApi, type InventoryValueParams } from '@/api/inventoryValue'
import InventoryValueTable from './components/InventoryValueTable.vue'

const router = useRouter()

interface ProcessItem {
  process_cd: string
  process_name: string
}

interface StatisticsData {
  total: {
    total_amount: number
    material_amount: number
    component_amount: number
    stay_amount: number
  }
  byType: any[]
  byProcess: any[]
}

interface CalcError {
  product_cd: string
  process_cd: string | null
  item_type: string | null
  error_code: string
  error_message: string
}

const loading = ref(false)
const calculating = ref(false)
const activeTab = ref('material')

const materialTableRef = ref()
const componentTableRef = ref()
const stayTableRef = ref()

const dateRange = ref<string[]>([])
const selectedProcess = ref('all')
const processList = ref<ProcessItem[]>([])
const errors = ref<CalcError[]>([])

const statistics = ref<StatisticsData>({
  total: {
    total_amount: 0,
    material_amount: 0,
    component_amount: 0,
    stay_amount: 0,
  },
  byType: [],
  byProcess: [],
})

const currentDateRange = computed(() => {
  if (dateRange.value && dateRange.value.length === 2) {
    return {
      startDate: dateRange.value[0],
      endDate: dateRange.value[1],
    }
  }
  return { startDate: '', endDate: '' }
})

const formatNumber = (value: number | string | undefined, decimals = 0): string => {
  if (!value && value !== 0) return '0'
  return Number(value).toLocaleString('ja-JP', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

const errorTagType = (code: string) => {
  if (code === 'NO_ROUTE') return 'danger'
  if (code === 'NO_STEP') return 'warning'
  return 'info'
}

const errorLabel = (code: string) => {
  const map: Record<string, string> = {
    NO_ROUTE: 'ルート未設定',
    NO_STEP: 'ステップ不明',
    NO_PRICE: '単価未設定',
  }
  return map[code] || code
}

const loadStatistics = async () => {
  try {
    const params: InventoryValueParams = {
      ...currentDateRange.value,
      processCode: selectedProcess.value === 'all' ? undefined : selectedProcess.value,
    }
    const response = await inventoryValueApi.getInventoryValueSummary(params)
    const raw = response.data as Partial<StatisticsData> | undefined
    if (raw?.total) {
      statistics.value = {
        total: {
          total_amount: Number(raw.total.total_amount) || 0,
          material_amount: Number(raw.total.material_amount) || 0,
          component_amount: Number(raw.total.component_amount) || 0,
          stay_amount: Number(raw.total.stay_amount) || 0,
        },
        byType: raw.byType ?? [],
        byProcess: raw.byProcess ?? [],
      }
    } else {
      statistics.value = {
        total: {
          total_amount: 0,
          material_amount: 0,
          component_amount: 0,
          stay_amount: 0,
        },
        byType: [],
        byProcess: [],
      }
    }
  } catch (error) {
    console.error('統計データ取得失敗:', error)
  }
}

const loadErrors = async () => {
  try {
    const response = await inventoryValueApi.getErrors()
    errors.value = ((response as any)?.data ?? []) as CalcError[]
  } catch {
    errors.value = []
  }
}

const loadProcessList = async () => {
  try {
    const response = await inventoryValueApi.getProcessList()
    if (response.data) {
      processList.value = response.data as unknown as ProcessItem[]
    }
  } catch (error) {
    console.error('工程リスト取得失敗:', error)
  }
}

const runCalculation = async () => {
  if (!dateRange.value || dateRange.value.length < 2) {
    ElMessage.warning('期間を選択してください')
    return
  }
  calculating.value = true
  try {
    const res = await inventoryValueApi.calculateValue({
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      process_cd: selectedProcess.value === 'all' ? undefined : selectedProcess.value,
    })
    if (res?.success) {
      const d = res.data as {
        total_rows?: number
        error_rows?: number
        total_amount?: number
      }
      ElMessage.success(
        `計算完了: ${d?.total_rows ?? 0}件処理 / エラー${d?.error_rows ?? 0}件 / 合計 ¥${formatNumber(d?.total_amount ?? 0)}`,
      )
      await loadStatistics()
      await loadErrors()
      refreshCurrentTable()
    } else {
      ElMessage.error((res as { message?: string })?.message || '計算に失敗しました')
    }
  } catch {
    ElMessage.error('計算実行中にエラーが発生しました')
  } finally {
    calculating.value = false
  }
}

const handleDateChange = () => { searchData() }
const handleProcessChange = () => { searchData() }

const searchData = () => {
  loadStatistics()
  loadErrors()
  refreshCurrentTable()
}

const clearFilters = () => {
  dateRange.value = []
  selectedProcess.value = 'all'
  searchData()
}

const refreshCurrentTable = () => {
  switch (activeTab.value) {
    case 'material':
      materialTableRef.value?.refreshTable()
      break
    case 'component':
      componentTableRef.value?.refreshTable()
      break
    case 'stay':
      stayTableRef.value?.refreshTable()
      break
  }
}

const goToBom = () => { router.push('/master/bom/product-bom') }
const goToUnitPrice = () => { router.push('/master/bom/product-unit-price') }

onMounted(() => {
  const now = new Date()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  dateRange.value = [firstDay.toISOString().split('T')[0], lastDay.toISOString().split('T')[0]]
  loadProcessList()
  searchData()
})
</script>

<style scoped>
.inventory-value-management {
  --ivm-surface: rgba(255, 255, 255, 0.92);
  --ivm-border: rgba(15, 23, 42, 0.08);
  --ivm-accent: #0ea5e9;
  --ivm-muted: #64748b;
  min-height: 100vh;
  background: linear-gradient(165deg, #f8fafc 0%, #f1f5f9 45%, #e8edf3 100%);
  padding: 10px 12px 14px;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.page-header {
  margin-bottom: 10px;
  padding: 8px 12px;
  background: var(--ivm-surface);
  border-radius: 10px;
  border: 1px solid var(--ivm-border);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 6px 20px rgba(15, 23, 42, 0.05);
  backdrop-filter: blur(10px);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(145deg, #0ea5e9, #0284c7);
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.25);
  flex-shrink: 0;
}

.header-icon .icon {
  font-size: 18px;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.page-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  line-height: 1.25;
  letter-spacing: -0.02em;
}

.page-description {
  font-size: 11px;
  color: var(--ivm-muted);
  margin: 0;
  line-height: 1.3;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.alert-panel {
  margin-bottom: 8px;
}

.error-list {
  margin-top: 6px;
}

.error-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 0;
  font-size: 12px;
}

.error-detail {
  color: #475569;
}

.error-more {
  font-size: 12px;
  color: #94a3b8;
  padding-top: 4px;
}

.filter-container {
  margin-bottom: 8px;
  padding: 10px 12px;
  background: var(--ivm-surface);
  border-radius: 10px;
  border: 1px solid var(--ivm-border);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.filter-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin: 0;
}

.filter-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--ivm-muted);
  margin-bottom: 0;
  line-height: 1.2;
}

.date-picker,
.process-select {
  width: 180px;
}

.date-picker :deep(.el-input__wrapper),
.process-select :deep(.el-input__wrapper) {
  border-radius: 6px;
  min-height: 30px;
}

.filter-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-left: auto;
}

.search-btn,
.clear-btn {
  border-radius: 6px;
  font-weight: 600;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.search-btn {
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.25);
}

.clear-btn {
  color: #475569;
}

.btn-icon {
  font-size: 14px;
}

.stats-container {
  margin-bottom: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.stat-card {
  background: var(--ivm-surface);
  border: 1px solid var(--ivm-border);
  border-radius: 10px;
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.stat-header {
  align-self: flex-start;
}

.stat-badge {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
}

.stat-badge.material {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
}

.stat-badge.component {
  background: linear-gradient(135deg, #22c55e, #16a34a);
}

.stat-badge.stay {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.stat-badge.total {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
}

.total-card .stat-icon {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
}

.stat-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.material-card .stat-icon {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
}

.component-card .stat-icon {
  background: linear-gradient(135deg, #22c55e, #16a34a);
}

.stay-card .stat-icon {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.stat-icon .icon {
  font-size: 16px;
  color: #fff;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 2px;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #475569;
  font-weight: 600;
}

.content-tabs {
  background: var(--ivm-surface);
  border-radius: 10px;
  border: 1px solid var(--ivm-border);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

.tabs-card {
  background: transparent;
  border: none;
  box-shadow: none;
}

.tabs-card :deep(.el-card__body) {
  padding: 0;
}

.main-tabs :deep(.el-tabs__header) {
  background: rgba(241, 245, 249, 0.85);
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  margin: 0;
  padding: 3px;
  border-radius: 8px;
}

.main-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0;
}

.main-tabs :deep(.el-tabs__item) {
  color: var(--ivm-muted);
  font-weight: 600;
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
  margin: 0 1px;
  line-height: 1.35;
  border: none;
  transition: color 0.15s ease, background 0.15s ease;
}

.main-tabs :deep(.el-tabs__item:hover) {
  color: #0284c7;
  background: rgba(14, 165, 233, 0.08);
}

.main-tabs :deep(.el-tabs__item.is-active) {
  color: #fff;
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.25);
}

.main-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.main-tabs :deep(.el-tabs__content) {
  padding: 0;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .inventory-value-management {
    padding: 8px;
  }

  .header-content {
    gap: 10px;
  }

  .filter-row {
    gap: 6px;
  }

  .date-picker,
  .process-select {
    width: 100%;
  }

  .filter-actions {
    margin-left: 0;
    width: 100%;
    justify-content: flex-start;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .page-title {
    font-size: 1rem;
  }

  .stat-value {
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .inventory-value-management {
    padding: 6px;
  }

  .header-icon {
    width: 32px;
    height: 32px;
  }

  .stat-card {
    padding: 8px;
  }

  .stat-value {
    font-size: 15px;
  }
}
</style>
