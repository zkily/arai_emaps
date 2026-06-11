<template>
  <div class="forecast-page">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="noise-overlay"></div>
    </div>

    <!-- Header -->
    <div class="glass-header animate-in">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="26"><TrendCharts /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">内示・フォーキャスト</h1>
            <span class="header-subtitle">Demand Forecast · order_monthly</span>
          </div>
        </div>
        <div class="header-badges">
          <span class="badge badge-total">件数 <b>{{ total }}</b></span>
          <span class="badge badge-achieved">達成 <b>{{ achievedCount }}</b></span>
          <span class="badge badge-rate">達成率 <b>{{ achievementRate }}%</b></span>
        </div>
      </div>
    </div>

    <!-- KPI -->
    <div class="kpi-row animate-in" style="animation-delay: 0.06s">
      <div class="kpi-card kpi-card--forecast">
        <div class="kpi-icon"><el-icon><DataLine /></el-icon></div>
        <div class="kpi-body">
          <span class="kpi-label">内示合計</span>
          <span class="kpi-value">{{ totalForecast.toLocaleString() }}</span>
        </div>
      </div>
      <div class="kpi-card kpi-card--confirmed">
        <div class="kpi-icon"><el-icon><CircleCheck /></el-icon></div>
        <div class="kpi-body">
          <span class="kpi-label">確定合計</span>
          <span class="kpi-value">{{ totalConfirmed.toLocaleString() }}</span>
        </div>
      </div>
      <div class="kpi-card kpi-card--rate">
        <div class="kpi-icon"><el-icon><Odometer /></el-icon></div>
        <div class="kpi-body">
          <span class="kpi-label">達成率</span>
          <span class="kpi-value">{{ achievementRate }}<small>%</small></span>
        </div>
      </div>
    </div>

    <!-- Filter -->
    <div class="filter-panel glass-card animate-in" style="animation-delay: 0.1s">
      <div class="filter-panel__head">
        <div class="filter-panel__title">
          <el-icon class="filter-panel__title-icon"><Filter /></el-icon>
          <span>検索条件</span>
        </div>
        <span v-if="activeFilterHint" class="filter-panel__hint">{{ activeFilterHint }}</span>
      </div>
      <div class="filter-panel__body">
        <div class="filter-group">
          <label class="filter-label"><el-icon><Calendar /></el-icon>対象月</label>
          <div class="filter-month-nav">
            <el-button class="nav-btn" :icon="ArrowLeft" circle size="small" @click="goPrevMonth" />
            <el-date-picker
              v-model="filters.month"
              type="month"
              placeholder="すべて"
              format="YYYY/MM"
              value-format="YYYY-MM"
              clearable
              class="filter-month-picker"
            />
            <el-button class="nav-btn" :icon="ArrowRight" circle size="small" @click="goNextMonth" />
            <el-button class="now-btn" size="small" @click="goCurrentMonth">今月</el-button>
          </div>
        </div>

        <div class="filter-divider" aria-hidden="true"></div>

        <div class="filter-group filter-group--grow">
          <label class="filter-label"><el-icon><Location /></el-icon>納入先</label>
          <el-select
            v-model="filters.destination_cd"
            placeholder="納入先を選択"
            clearable
            filterable
            class="filter-control filter-dest"
            popper-class="destination-select-popper"
          >
            <el-option v-for="d in destinationOptions" :key="d.cd" :label="`${d.cd} | ${d.name}`" :value="d.cd" />
          </el-select>
        </div>

        <div class="filter-group filter-group--grow">
          <label class="filter-label"><el-icon><Box /></el-icon>製品</label>
          <el-input
            v-model="filters.keyword"
            placeholder="製品CD・製品名"
            clearable
            class="filter-control"
            @keyup.enter="handleSearch"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>

        <div class="filter-actions">
          <el-button class="gradient-btn" :icon="Search" :loading="loading" @click="handleSearch">検索</el-button>
          <el-button class="ghost-btn" :icon="Refresh" @click="resetFilters">リセット</el-button>
          <el-button class="gradient-btn create-btn" :icon="Plus" @click="openCreate">新規登録</el-button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="table-panel glass-card animate-in" style="animation-delay: 0.14s">
      <div class="table-surface">
        <el-table
          v-loading="loading"
          :data="dataList"
          size="default"
          stripe
          class="forecast-table"
          :header-cell-style="headerStyle"
          :cell-style="cellStyle"
          empty-text="内示データがありません"
        >
          <el-table-column prop="destination_cd" label="納入先CD" width="100">
            <template #default="{ row }"><span class="code-text">{{ row.destination_cd || '—' }}</span></template>
          </el-table-column>
          <el-table-column prop="destination_name" label="納入先名" min-width="130" show-overflow-tooltip>
            <template #default="{ row }"><span class="text-cell">{{ row.destination_name }}</span></template>
          </el-table-column>
          <el-table-column prop="forecast_month" label="対象月" width="92" align="center">
            <template #default="{ row }"><span class="month-badge">{{ row.forecast_month }}</span></template>
          </el-table-column>
          <el-table-column prop="product_cd" label="製品CD" width="100">
            <template #default="{ row }"><span class="code-text">{{ row.product_cd }}</span></template>
          </el-table-column>
          <el-table-column prop="product_name" label="製品名" min-width="130" show-overflow-tooltip>
            <template #default="{ row }"><span class="text-cell text-cell--strong">{{ row.product_name }}</span></template>
          </el-table-column>
          <el-table-column prop="product_type" label="種別" width="80" align="center">
            <template #default="{ row }">
              <span class="type-tag">{{ row.product_type || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="forecast_units" label="内示本数" width="96" align="right">
            <template #default="{ row }"><span class="num-cell">{{ (row.forecast_units || 0).toLocaleString() }}</span></template>
          </el-table-column>
          <el-table-column prop="forecast_total_units" label="確定本数" width="96" align="right">
            <template #default="{ row }"><span class="num-cell num-cell--ok">{{ (row.forecast_total_units || 0).toLocaleString() }}</span></template>
          </el-table-column>
          <el-table-column prop="forecast_diff" label="内示差異" width="92" align="right">
            <template #default="{ row }">
              <span :class="['num-cell', row.forecast_diff >= 0 ? 'num-cell--ok' : 'num-cell--ng']">
                {{ (row.forecast_diff ?? 0).toLocaleString() }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="達成率" width="136" align="center">
            <template #default="{ row }">
              <div class="progress-wrap">
                <el-progress :percentage="getRate(row)" :stroke-width="8" :color="getProgressColor(getRate(row))" :show-text="false" />
                <span class="progress-text" :class="getRateClass(row)">{{ getRate(row) }}%</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="92" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-icons">
              <el-tooltip content="編集" placement="top" :show-after="300">
                <button type="button" class="act-btn act-btn--edit" @click="openEdit(row)">
                  <el-icon><Edit /></el-icon>
                </button>
              </el-tooltip>
              <el-tooltip content="削除" placement="top" :show-after="300">
                <button type="button" class="act-btn act-btn--delete" @click="handleDelete(row)">
                  <el-icon><Delete /></el-icon>
                </button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <div class="empty-state">
            <el-icon size="44"><Document /></el-icon>
            <p>条件に一致する内示データがありません</p>
            <el-button class="ghost-btn" size="small" @click="resetFilters">条件をクリア</el-button>
          </div>
        </template>
        </el-table>
      </div>
      <div v-if="total > pageSize" class="pagination-wrap">
        <el-pagination
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          size="small"
          background
          @current-change="onPageChange"
        />
      </div>
    </div>

    <!-- Form Dialog -->
    <el-dialog
      v-model="showForm"
      :title="editId ? '内示編集' : '内示登録'"
      width="500px"
      class="forecast-dialog"
      :close-on-click-modal="false"
      align-center
    >
      <el-form :model="form" label-width="96px" size="default" class="forecast-form">
        <el-form-item label="納入先" required>
          <el-select
            v-model="form.destination_cd"
            placeholder="納入先を選択"
            filterable
            clearable
            style="width:100%"
            @change="onDestinationChange"
          >
            <el-option v-for="d in destinationOptions" :key="d.cd" :label="`${d.cd} | ${d.name}`" :value="d.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="対象月" required>
          <el-date-picker v-model="form.forecast_month" type="month" format="YYYY-MM" value-format="YYYY-MM" style="width:100%" />
        </el-form-item>
        <el-form-item label="製品CD" required><el-input v-model="form.product_cd" /></el-form-item>
        <el-form-item label="製品名"><el-input v-model="form.product_name" /></el-form-item>
        <el-form-item label="種別">
          <el-select v-model="form.product_type" style="width:100%">
            <el-option label="量産品" value="量産品" />
            <el-option label="試作品" value="試作品" />
            <el-option label="別注品" value="別注品" />
          </el-select>
        </el-form-item>
        <el-form-item label="内示本数" required>
          <el-input-number v-model="form.forecast_units" :min="0" controls-position="right" style="width:100%" />
        </el-form-item>
        <p v-if="editId" class="form-hint">確定本数は日別受注から自動集計されます。</p>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">キャンセル</el-button>
        <el-button type="primary" class="gradient-btn" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  TrendCharts,
  Search,
  Document,
  Plus,
  Edit,
  Delete,
  Refresh,
  Calendar,
  Location,
  Box,
  Filter,
  ArrowLeft,
  ArrowRight,
  DataLine,
  CircleCheck,
  Odometer,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchOrderMonthlyList,
  createOrderMonthly,
  updateOrderMonthly,
  deleteOrderMonthly,
  type OrderMonthlyItem,
} from '@/api/erp/orderMonthly'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import { useSalesOperationPermission } from '@/composables/useSalesOperationPermission'
import { guardSalesOperation } from '@/utils/salesOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = useSalesOperationPermission()


const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editId = ref<number | null>(null)
const allData = ref<OrderMonthlyItem[]>([])
const dataList = ref<(OrderMonthlyItem & { forecast_month?: string })[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const destinationOptions = ref<{ cd: string; name: string }[]>([])
const filters = ref({ keyword: '', month: '', destination_cd: '' })

const emptyForm = () => ({
  destination_cd: '',
  destination_name: '',
  forecast_month: '',
  product_cd: '',
  product_name: '',
  product_type: '量産品',
  forecast_units: 0,
})
const form = ref(emptyForm())

const totalForecast = computed(() => allData.value.reduce((s, i) => s + (i.forecast_units || 0), 0))
const totalConfirmed = computed(() => allData.value.reduce((s, i) => s + (i.forecast_total_units || 0), 0))
const achievementRate = computed(() =>
  totalForecast.value > 0 ? Math.round(totalConfirmed.value / totalForecast.value * 100) : 0,
)
const achievedCount = computed(() =>
  allData.value.filter((i) => (i.forecast_units || 0) > 0 && (i.forecast_total_units || 0) >= (i.forecast_units || 0)).length,
)

const activeFilterHint = computed(() => {
  const parts: string[] = []
  if (filters.value.month) parts.push(filters.value.month.replace('-', '年') + '月')
  if (filters.value.destination_cd) {
    const d = destinationOptions.value.find((x) => x.cd === filters.value.destination_cd)
    parts.push(d ? d.name : filters.value.destination_cd)
  }
  if (filters.value.keyword) parts.push(`製品: ${filters.value.keyword}`)
  return parts.length ? parts.join(' · ') : ''
})

const headerStyle = () => ({
  background: 'linear-gradient(135deg, #0e7490 0%, #0891b2 100%)',
  color: '#fff',
  fontWeight: '700',
  fontSize: '13px',
  padding: '10px 0',
  borderBottom: 'none',
})
const cellStyle = () => ({
  padding: '10px 8px',
  fontSize: '13px',
  color: '#1e293b',
  background: 'transparent',
})

function getRateClass(row: OrderMonthlyItem) {
  const rate = getRate(row)
  if (rate >= 80) return 'progress-text--high'
  if (rate >= 50) return 'progress-text--mid'
  return 'progress-text--low'
}

function getRate(row: OrderMonthlyItem) {
  const forecast = row.forecast_units || 0
  if (forecast <= 0) return 0
  return Math.min(100, Math.round((row.forecast_total_units || 0) / forecast * 100))
}
function getProgressColor(rate: number) {
  return rate >= 80 ? '#10b981' : rate >= 50 ? '#f59e0b' : '#ef4444'
}

function applyPagination() {
  if (!guardSalesOperation(canEdit)) return

  total.value = allData.value.length
  const start = (page.value - 1) * pageSize.value
  dataList.value = allData.value.slice(start, start + pageSize.value).map(mapMonthlyRow)
}

function mapMonthlyRow(row: OrderMonthlyItem): OrderMonthlyItem & { forecast_month: string } {
  return {
    ...row,
    forecast_month: `${row.year}-${String(row.month).padStart(2, '0')}`,
  }
}

function shiftMonth(ym: string, delta: number): string {
  const [y, m] = ym.split('-').map(Number)
  const d = new Date(y, m - 1 + delta, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function goCurrentMonth() {
  const now = new Date()
  filters.value.month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  handleSearch()
}

function goPrevMonth() {
  filters.value.month = filters.value.month
    ? shiftMonth(filters.value.month, -1)
    : shiftMonth(`${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`, -1)
  handleSearch()
}

function goNextMonth() {
  filters.value.month = filters.value.month
    ? shiftMonth(filters.value.month, 1)
    : shiftMonth(`${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`, 1)
  handleSearch()
}

function onDestinationChange(cd: string) {
  const d = destinationOptions.value.find((x) => x.cd === cd)
  form.value.destination_name = d?.name ?? ''
}

async function loadDestinationOptions() {
  if (!guardSalesOperation(canCreate)) return

  try {
    const res = await getDestinationOptions()
    const list = (res as { data?: { cd: string; name: string }[] })?.data ?? res
    destinationOptions.value = Array.isArray(list) ? list : []
  } catch {
    destinationOptions.value = []
  }
}

function buildFetchParams() {
  const params: Record<string, string | number> = {}
  if (filters.value.destination_cd) params.destination_cd = filters.value.destination_cd
  if (filters.value.keyword) params.keyword = filters.value.keyword
  if (filters.value.month) {
    const [y, m] = filters.value.month.split('-')
    if (y) params.year = Number(y)
    if (m) params.month = Number(m)
  }
  return params
}

async function fetchData() {
  loading.value = true
  try {
    const list = await fetchOrderMonthlyList(buildFetchParams())
    allData.value = list || []
    applyPagination()
  } catch {
    allData.value = []
    applyPagination()
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  if (!guardSalesOperation(canEdit)) return

  page.value = 1
  fetchData()
}

function resetFilters() {
  filters.value = { keyword: '', month: '', destination_cd: '' }
  page.value = 1
  fetchData()
}

function onPageChange(p: number) {
  page.value = p
  applyPagination()
}

function openEdit(row: OrderMonthlyItem & { forecast_month?: string }) {
  if (!guardSalesOperation(canEdit)) return

  editId.value = row.id
  form.value = {
    ...emptyForm(),
    destination_cd: row.destination_cd,
    destination_name: row.destination_name,
    forecast_month: row.forecast_month || `${row.year}-${String(row.month).padStart(2, '0')}`,
    product_cd: row.product_cd,
    product_name: row.product_name,
    product_type: row.product_type || '量産品',
    forecast_units: row.forecast_units || 0,
  }
  showForm.value = true
}

function openCreate() {
  if (!guardSalesOperation(canCreate)) return

  editId.value = null
  form.value = emptyForm()
  if (filters.value.month) form.value.forecast_month = filters.value.month
  if (filters.value.destination_cd) {
    form.value.destination_cd = filters.value.destination_cd
    onDestinationChange(filters.value.destination_cd)
  }
  showForm.value = true
}

function parseYearMonth(ym: string) {
  const [y, m] = ym.split('-')
  return { year: Number(y), month: Number(m) }
}

async function handleSave() {
  if (!guardSalesOperation(canEdit)) return

  if (!form.value.destination_cd || !form.value.product_cd || !form.value.forecast_month) {
    ElMessage.warning('納入先、製品CD、対象月は必須です')
    return
  }
  const { year, month } = parseYearMonth(form.value.forecast_month)
  if (!year || !month) {
    ElMessage.warning('対象月の形式が正しくありません')
    return
  }
  saving.value = true
  try {
    const payload = {
      destination_cd: form.value.destination_cd,
      destination_name: form.value.destination_name || form.value.destination_cd,
      year,
      month,
      product_cd: form.value.product_cd,
      product_name: form.value.product_name || form.value.product_cd,
      product_type: form.value.product_type || '量産品',
      forecast_units: form.value.forecast_units || 0,
    }
    if (editId.value) {
      await updateOrderMonthly(editId.value, payload)
    } else {
      await createOrderMonthly(payload)
    }
    ElMessage.success('保存しました')
    showForm.value = false
    fetchData()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    ElMessage.error(err?.response?.data?.detail || err?.message || '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: OrderMonthlyItem) {
  if (!guardSalesOperation(canDelete)) return

  try {
    await ElMessageBox.confirm(
      `「${row.destination_name} / ${row.product_cd}」の内示を削除します。紐づく日別受注も削除されます。`,
      '削除確認',
      { type: 'warning', confirmButtonText: '削除', cancelButtonText: 'キャンセル' },
    )
    await deleteOrderMonthly(row.id)
    ElMessage.success('削除しました')
    fetchData()
  } catch {
    /* cancelled */
  }
}

onMounted(() => {
  loadDestinationOptions()
  goCurrentMonth()
})
</script>

<style scoped>
.forecast-page {
  position: relative;
  min-height: 100vh;
  padding: 16px;
  overflow: hidden;
}

/* Background */
.dynamic-background {
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(135deg, #0f172a 0%, #134e4a 35%, #1e1b4b 70%, #0f172a 100%);
}
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.38;
  animation: float 22s ease-in-out infinite;
}
.orb-1 { width: 380px; height: 380px; top: -90px; left: -70px; background: radial-gradient(circle, #06b6d4, transparent); }
.orb-2 { width: 320px; height: 320px; top: 35%; right: -70px; background: radial-gradient(circle, #14b8a6, transparent); animation-delay: -8s; }
.orb-3 { width: 280px; height: 280px; bottom: -40px; left: 28%; background: radial-gradient(circle, #6366f1, transparent); animation-delay: -15s; }
.noise-overlay {
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
}
@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(18px, -22px) scale(1.04); }
}

.glass-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  margin-bottom: 12px;
}

/* Header */
.glass-header {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 14px 20px;
  margin-bottom: 12px;
}
.header-content { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-icon {
  width: 46px; height: 46px;
  background: linear-gradient(135deg, #06b6d4, #0d9488);
  border-radius: 13px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  box-shadow: 0 8px 24px rgba(6, 182, 212, 0.35);
}
.header-title { font-size: 1.35rem; font-weight: 700; color: #fff; margin: 0; line-height: 1.2; }
.header-subtitle { font-size: 0.72rem; color: rgba(255, 255, 255, 0.45); letter-spacing: 0.04em; }
.header-badges { display: flex; gap: 8px; flex-wrap: wrap; }
.badge {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px;
  padding: 4px 12px;
}
.badge b { color: #fff; font-weight: 700; margin-left: 2px; }
.badge-achieved { background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.3); }
.badge-rate { background: rgba(6, 182, 212, 0.15); border-color: rgba(6, 182, 212, 0.3); }

/* KPI */
.kpi-row {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 12px;
}
.kpi-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(14px);
}
.kpi-icon {
  width: 40px; height: 40px;
  border-radius: 11px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; color: #fff; flex-shrink: 0;
}
.kpi-card--forecast .kpi-icon { background: linear-gradient(135deg, #0891b2, #06b6d4); }
.kpi-card--confirmed .kpi-icon { background: linear-gradient(135deg, #059669, #10b981); }
.kpi-card--rate .kpi-icon { background: linear-gradient(135deg, #7c3aed, #6366f1); }
.kpi-label { display: block; font-size: 11px; color: rgba(255, 255, 255, 0.5); margin-bottom: 2px; }
.kpi-value { font-size: 1.35rem; font-weight: 700; color: #fff; line-height: 1.1; }
.kpi-value small { font-size: 0.85rem; font-weight: 600; opacity: 0.8; }

/* Filter panel */
.filter-panel { padding: 0; overflow: hidden; }
.filter-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 16px;
  background: linear-gradient(90deg, rgba(6, 182, 212, 0.12), rgba(99, 102, 241, 0.08));
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.filter-panel__title {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; font-weight: 600; color: rgba(255, 255, 255, 0.9);
}
.filter-panel__title-icon { color: #22d3ee; }
.filter-panel__hint { font-size: 11px; color: rgba(255, 255, 255, 0.45); max-width: 50%; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.filter-panel__body {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 14px 16px;
  padding: 14px 16px;
}
.filter-group { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.filter-group--grow { flex: 1; min-width: 160px; }
.filter-label {
  display: flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 600; color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.03em;
}
.filter-label .el-icon { font-size: 13px; color: #67e8f9; }
.filter-divider {
  width: 1px; align-self: stretch; min-height: 52px;
  background: linear-gradient(180deg, transparent, rgba(255,255,255,.12), transparent);
  margin: 0 2px;
}
.filter-month-nav { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.filter-month-picker { width: 130px !important; }
.nav-btn {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  color: rgba(255, 255, 255, 0.85) !important;
}
.nav-btn:hover { background: rgba(6, 182, 212, 0.2) !important; border-color: rgba(6, 182, 212, 0.4) !important; }
.now-btn {
  background: rgba(6, 182, 212, 0.15) !important;
  border: 1px solid rgba(6, 182, 212, 0.35) !important;
  color: #67e8f9 !important;
  font-size: 12px;
}
.filter-control { width: 100%; }
.filter-dest { min-width: 200px; }
.filter-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  flex-wrap: wrap;
}
.gradient-btn {
  background: linear-gradient(135deg, #06b6d4, #0891b2) !important;
  border: none !important;
  color: #fff !important;
  font-weight: 600;
  box-shadow: 0 4px 14px rgba(6, 182, 212, 0.3);
}
.gradient-btn:hover { filter: brightness(1.08); }
.create-btn { background: linear-gradient(135deg, #6366f1, #4f46e5) !important; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3); }
.ghost-btn {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.16) !important;
  color: rgba(255, 255, 255, 0.85) !important;
}
.ghost-btn:hover { background: rgba(255, 255, 255, 0.1) !important; }

/* Table — light surface for readability */
.table-panel { padding: 0; overflow: hidden; }
.table-surface {
  background: #f8fafc;
  border-radius: 0 0 13px 13px;
  overflow: hidden;
}

.text-cell { color: #334155; font-size: 13px; }
.text-cell--strong { color: #0f172a; font-weight: 600; }

.code-text {
  font-family: Consolas, 'Courier New', monospace;
  font-weight: 700;
  font-size: 13px;
  color: #0369a1;
  letter-spacing: 0.02em;
}
.month-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  background: #ede9fe;
  color: #5b21b6;
  border: 1px solid #ddd6fe;
}
.type-tag {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  background: #e2e8f0;
  color: #475569;
}
.num-cell {
  font-variant-numeric: tabular-nums;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}
.num-cell--ok { color: #047857; }
.num-cell--ng { color: #b91c1c; }

.progress-wrap { display: flex; align-items: center; gap: 8px; padding: 0 4px; }
.progress-wrap :deep(.el-progress-bar__outer) { background: #e2e8f0; border-radius: 999px; }
.progress-wrap :deep(.el-progress-bar__inner) { border-radius: 999px; }
.progress-text {
  font-size: 12px;
  font-weight: 700;
  min-width: 36px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.progress-text--high { color: #047857; }
.progress-text--mid { color: #b45309; }
.progress-text--low { color: #b91c1c; }

:deep(.forecast-table) {
  --el-table-bg-color: #ffffff;
  --el-table-tr-bg-color: #ffffff;
  --el-table-text-color: #1e293b;
  --el-table-header-text-color: #ffffff;
  --el-table-border-color: #e2e8f0;
  --el-table-row-hover-bg-color: #ecfeff;
  --el-fill-color-lighter: #f1f5f9;
  background: #ffffff !important;
}
:deep(.forecast-table .el-table__inner-wrapper::before),
:deep(.forecast-table .el-table__border-left-patch) {
  display: none;
}
:deep(.forecast-table th.el-table__cell) {
  border-bottom: none !important;
}
:deep(.forecast-table td.el-table__cell) {
  border-bottom: 1px solid #e2e8f0;
}
:deep(.forecast-table .el-table__row--striped td.el-table__cell) {
  background: #f8fafc !important;
}
:deep(.forecast-table .el-table__body tr:hover > td.el-table__cell) {
  background: #ecfeff !important;
}
:deep(.forecast-table .el-table__empty-block) {
  background: #f8fafc;
}
:deep(.forecast-table .cell) {
  line-height: 1.45;
}

/* Icon actions — visible on light rows */
.action-icons { display: flex; align-items: center; justify-content: center; gap: 6px; }
.act-btn {
  width: 30px; height: 30px;
  display: inline-flex; align-items: center; justify-content: center;
  border-radius: 8px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.18s ease;
  font-size: 15px;
  background: transparent;
  padding: 0;
}
.act-btn--edit {
  color: #0369a1;
  background: #e0f2fe;
  border-color: #7dd3fc;
}
.act-btn--edit:hover {
  background: #bae6fd;
  border-color: #38bdf8;
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(14, 165, 233, 0.25);
}
.act-btn--delete {
  color: #b91c1c;
  background: #fee2e2;
  border-color: #fca5a5;
}
.act-btn--delete:hover {
  background: #fecaca;
  border-color: #f87171;
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(239, 68, 68, 0.2);
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: 12px;
  background: #f1f5f9;
  border-top: 1px solid #e2e8f0;
}
.empty-state { padding: 40px 16px; text-align: center; color: #64748b; background: #f8fafc; }
.empty-state p { margin: 10px 0 14px; font-size: 14px; color: #475569; }
.form-hint { margin: 0; font-size: 12px; color: #64748b; padding-left: 96px; }

:deep(.pagination-wrap .el-pagination.is-background .el-pager li) {
  background: #fff;
  color: #475569;
  border: 1px solid #e2e8f0;
}
:deep(.pagination-wrap .el-pagination.is-background .el-pager li.is-active) {
  background: linear-gradient(135deg, #0891b2, #0e7490) !important;
  color: #fff !important;
  border-color: transparent;
}
:deep(.pagination-wrap .el-pagination.is-background .btn-prev),
:deep(.pagination-wrap .el-pagination.is-background .btn-next) {
  background: #fff;
  color: #475569;
}

:deep(.filter-control .el-input__wrapper),
:deep(.filter-month-picker .el-input__wrapper),
:deep(.filter-dest .el-select__wrapper) {
  background: rgba(15, 23, 42, 0.45) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.12) inset !important;
}
:deep(.filter-control .el-input__inner),
:deep(.filter-dest .el-select__selected-item) { color: rgba(255, 255, 255, 0.9); }

.animate-in { animation: slideIn 0.45s ease forwards; opacity: 0; transform: translateY(10px); }
@keyframes slideIn { to { opacity: 1; transform: translateY(0); } }

@media (max-width: 900px) {
  .kpi-row { grid-template-columns: 1fr; }
  .filter-panel__body { flex-direction: column; align-items: stretch; }
  .filter-divider { width: 100%; height: 1px; min-height: 0; margin: 0; }
  .filter-actions { margin-left: 0; width: 100%; justify-content: flex-end; }
  .filter-month-picker { width: 100% !important; flex: 1; }
}
</style>

<style>
/* Dialog (teleport) */
.forecast-dialog.el-dialog {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 14px;
  border: 1px solid #e2e8f0;
}
.forecast-dialog .el-dialog__title { font-weight: 700; color: #0f172a; }
</style>
