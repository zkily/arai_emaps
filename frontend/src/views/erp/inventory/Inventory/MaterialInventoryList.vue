<template>
  <div class="inventory-list-page miq-modern pb-std">
    <header class="page-header glass page-toolbar pb-hero pb-hero--page">
      <div class="page-toolbar-glow" aria-hidden="true" />
      <div class="page-header-fx pb-bubbles" aria-hidden="true" />
      <div class="header-left">
        <div class="header-icon header-icon--material">
          <el-icon size="24"><Grid /></el-icon>
        </div>
        <div class="header-text">
          <div class="header-title-row">
            <h1 class="header-title pb-hero-title">材料在庫照会</h1>
            <span class="header-meta">{{ totalCount }} 件</span>
          </div>
          <p class="header-desc pb-hero-desc">期間・材料・仕入先で在庫推移を照会</p>
        </div>
      </div>
      <div class="header-actions toolbar-actions">
        <el-button class="tb-btn tb-btn-teal" @click="exportCsv">
          <el-icon><Download /></el-icon>
          <span class="tb-label">CSV</span>
        </el-button>
      </div>
    </header>

    <div class="stat-cards glass">
      <div
        v-for="(item, i) in statCards"
        :key="item.key"
        :class="['stat-card', `stat-card--${item.key}`]"
        :style="{ '--i': i }"
      >
        <span class="stat-label">{{ item.label }}</span>
        <span class="stat-value" :class="item.sum < 0 ? 'num-negative' : ''">{{ formatNum(item.sum) }}</span>
      </div>
    </div>

    <div class="filter-bar glass">
      <div class="toolbar-group">
        <span class="toolbar-label">期間</span>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="～"
          start-placeholder="開始日"
          end-placeholder="終了日"
          value-format="YYYY-MM-DD"
          size="small"
          class="date-range-picker"
          @change="onDateChange"
        />
        <div class="date-quick">
          <el-button
            size="small"
            class="date-quick-btn"
            :class="{ 'date-quick-btn--active': isPrevDay }"
            @click="setQuickDate('prev')"
          >
            前日
          </el-button>
          <el-button
            size="small"
            class="date-quick-btn"
            :class="{ 'date-quick-btn--active': isToday }"
            @click="setQuickDate('today')"
          >
            今日
          </el-button>
          <el-button
            size="small"
            class="date-quick-btn"
            :class="{ 'date-quick-btn--active': isNextDay }"
            @click="setQuickDate('next')"
          >
            翌日
          </el-button>
        </div>
      </div>
      <div class="toolbar-group">
        <span class="toolbar-label">材料</span>
        <el-select
          v-model="filters.materialCd"
          placeholder="全て"
          clearable
          filterable
          size="small"
          class="product-select"
          @change="onFilterChange"
        >
          <el-option
            v-for="m in materialOptions"
            :key="m.material_cd"
            :label="m.material_name || m.material_cd"
            :value="m.material_cd"
          />
        </el-select>
      </div>
      <div class="toolbar-group">
        <span class="toolbar-label">仕入先</span>
        <el-select
          v-model="filters.suppliers"
          placeholder="全て"
          clearable
          filterable
          multiple
          collapse-tags
          collapse-tags-tooltip
          size="small"
          class="supplier-select"
          @change="onFilterChange"
        >
          <el-option v-for="s in supplierOptions" :key="s" :label="s" :value="s" />
        </el-select>
      </div>
    </div>

    <div class="table-section glass">
      <el-table
        :data="list"
        v-loading="loading"
        stripe
        border
        size="small"
        class="data-table"
        height="100%"
      >
        <el-table-column prop="material_cd" label="材料CD" width="100" fixed />
        <el-table-column prop="material_name" label="材料名" width="140" show-overflow-tooltip />
        <el-table-column prop="date" label="日付" width="105" align="center" />
        <el-table-column label="曜日" width="56" align="center">
          <template #default="{ row }">
            {{ weekdayJa(row.date) }}
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="仕入先" width="120" show-overflow-tooltip />
        <el-table-column prop="standard_spec" label="規格" width="100" show-overflow-tooltip />
        <el-table-column prop="current_stock" label="現在在庫" width="92" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.current_stock)">{{ formatNum(row.current_stock) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="safety_stock" label="安全在庫" width="88" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.safety_stock)">{{ formatNum(row.safety_stock) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="max_stock" label="最大在庫" width="88" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.max_stock)">{{ formatNum(row.max_stock) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="planned_usage" label="使用数" width="80" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.planned_usage)">{{ formatNum(row.planned_usage) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="adjustment_quantity" label="調整数" width="80" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.adjustment_quantity)">{{ formatNum(row.adjustment_quantity) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="order_quantity" label="注文数" width="80" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.order_quantity)">{{ formatNum(row.order_quantity) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="単位" width="64" align="center" />
        <el-table-column prop="unit_price" label="単価" width="88" align="right">
          <template #default="{ row }">
            {{ formatPrice(row.unit_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="remarks" label="備考" min-width="100" show-overflow-tooltip />
      </el-table>

      <div class="table-footer">
        <div class="footer-pills">
          <span class="footer-pill footer-pill--count">件数 {{ totalCount.toLocaleString() }}</span>
          <span
            v-for="item in statCards"
            :key="`ft-${item.key}`"
            :class="['footer-pill', `footer-pill--${item.key}`]"
          >
            {{ item.label }} {{ formatNum(item.sum) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Grid, Download } from '@element-plus/icons-vue'
import { getMaterialStockList, getMaterialStockSupplierNames } from '@/api/material'
import { getMaterialList } from '@/api/master/materialMaster'
import type { Material } from '@/types/master'
import { useInventoryOperationPermission } from '@/composables/useInventoryOperationPermission'
import { guardInventoryOperation } from '@/utils/inventoryOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = useInventoryOperationPermission()

export interface MaterialStockInquiryRow {
  id?: number
  material_cd: string
  material_name: string
  date: string
  supplier_name?: string | null
  standard_spec?: string | null
  current_stock?: number | null
  safety_stock?: number | null
  max_stock?: number | null
  planned_usage?: number | null
  adjustment_quantity?: number | null
  order_quantity?: number | null
  unit?: string | null
  unit_price?: number | null
  remarks?: string | null
}

const loading = ref(false)
const list = ref<MaterialStockInquiryRow[]>([])
const materialOptions = ref<Pick<Material, 'material_cd' | 'material_name'>[]>([])
const supplierOptions = ref<string[]>([])
const dateRange = ref<[string, string] | null>(null)

const filters = reactive({
  materialCd: '',
  suppliers: [] as string[],
})

const totalCount = ref(0)

const STAT_FIELDS: { key: keyof MaterialStockInquiryRow; label: string }[] = [
  { key: 'current_stock', label: '現在在庫' },
  { key: 'safety_stock', label: '安全在庫' },
  { key: 'planned_usage', label: '使用数' },
  { key: 'order_quantity', label: '注文数' },
]

const statCards = computed(() => {
  const data = list.value
  return STAT_FIELDS.map(({ key, label }) => {
    const sum = data.reduce((acc, row) => acc + (Number(row[key]) || 0), 0)
    return { key: String(key), label, sum }
  })
})

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function initDate() {
  if (!dateRange.value || !dateRange.value[0]) {
    const t = todayStr()
    dateRange.value = [t, t]
  }
}

function weekdayJa(isoDate: string | null | undefined): string {
  if (!isoDate) return ''
  const d = new Date(isoDate.slice(0, 10) + 'T12:00:00')
  const w = ['日', '月', '火', '水', '木', '金', '土']
  return w[d.getDay()] ?? ''
}

function setQuickDate(which: 'prev' | 'today' | 'next') {
  const base = dateRange.value?.[0] || todayStr()
  const d = new Date(base)
  if (which === 'prev') d.setDate(d.getDate() - 1)
  else if (which === 'next') d.setDate(d.getDate() + 1)
  const s = d.toISOString().slice(0, 10)
  dateRange.value = [s, s]
  doFetch()
}

const isToday = computed(() => {
  const r = dateRange.value
  if (!r || r[0] !== r[1]) return false
  return r[0] === todayStr()
})
const isPrevDay = computed(() => {
  const r = dateRange.value
  if (!r || r[0] !== r[1]) return false
  const d = new Date(todayStr())
  d.setDate(d.getDate() - 1)
  return r[0] === d.toISOString().slice(0, 10)
})
const isNextDay = computed(() => {
  const r = dateRange.value
  if (!r || r[0] !== r[1]) return false
  const d = new Date(todayStr())
  d.setDate(d.getDate() + 1)
  return r[0] === d.toISOString().slice(0, 10)
})

function onDateChange() {
  doFetch()
}

function onFilterChange() {
  doFetch()
}

function formatNum(v: number | null | undefined): string {
  if (v == null) return '0'
  return Number(v).toLocaleString()
}

function formatPrice(v: number | null | undefined): string {
  if (v == null) return ''
  const n = Number(v)
  if (Number.isNaN(n)) return ''
  return n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function numClass(v: number | null | undefined): string {
  if (v == null) return ''
  const n = Number(v)
  if (n < 0) return 'num-negative'
  if (n === 0) return 'num-zero'
  return 'num-positive'
}

function doFetch() {
  const t = todayStr()
  const start = dateRange.value?.[0] ?? t
  const end = dateRange.value?.[1] ?? t
  if (!start || !end) return

  loading.value = true
  const params: Record<string, unknown> = {
    page: 1,
    pageSize: 10000,
    start_date: start,
    end_date: end,
  }
  if (filters.materialCd) params.material_cd = filters.materialCd
  if (filters.suppliers.length > 0) params.suppliers = filters.suppliers.join(',')

  getMaterialStockList(params)
    .then((res) => {
      const listData = res?.data?.list ?? []
      list.value = listData as MaterialStockInquiryRow[]
      totalCount.value = Number(res?.data?.total ?? listData.length)
    })
    .catch((e) => {
      console.error(e)
      ElMessage.error('データの取得に失敗しました')
      list.value = []
      totalCount.value = 0
    })
    .finally(() => {
      loading.value = false
    })
}

async function fetchMaterials() {
  try {
    const res = await getMaterialList({ page: 1, pageSize: 8000, status: 1 })
    const raw = res?.data?.list ?? (res as { list?: Material[] })?.list ?? []
    materialOptions.value = (raw as Material[]).map((m) => ({
      material_cd: m.material_cd,
      material_name: m.material_name,
    }))
  } catch (e) {
    console.error(e)
    materialOptions.value = []
  }
}

async function fetchSuppliers() {
  try {
    const res = await getMaterialStockSupplierNames()
    supplierOptions.value = res?.data ?? []
  } catch (e) {
    console.error(e)
    supplierOptions.value = []
  }
}

function exportCsv() {
  if (!guardInventoryOperation(canExport)) return

  const headers = [
    '材料CD',
    '材料名',
    '日付',
    '曜日',
    '仕入先',
    '規格',
    '現在在庫',
    '安全在庫',
    '最大在庫',
    '使用数',
    '調整数',
    '注文数',
    '単位',
    '単価',
    '備考',
  ]
  const rows = list.value
  if (!rows.length) {
    ElMessage.warning('エクスポートするデータがありません')
    return
  }
  const escape = (v: unknown) => {
    const s = v == null ? '' : String(v)
    if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`
    return s
  }
  const lines = [headers.map(escape).join(',')]
  for (const row of rows) {
    lines.push(
      [
        row.material_cd,
        row.material_name,
        row.date,
        weekdayJa(row.date),
        row.supplier_name ?? '',
        row.standard_spec ?? '',
        row.current_stock ?? '',
        row.safety_stock ?? '',
        row.max_stock ?? '',
        row.planned_usage ?? '',
        row.adjustment_quantity ?? '',
        row.order_quantity ?? '',
        row.unit ?? '',
        row.unit_price ?? '',
        row.remarks ?? '',
      ]
        .map(escape)
        .join(',')
    )
  }
  const blob = new Blob(['\uFEFF' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const [s, e] = dateRange.value || ['', '']
  a.download = `material_stock_${s || 'start'}_${e || 'end'}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('CSVをダウンロードしました')
}

onMounted(() => {
  initDate()
  fetchMaterials()
  fetchSuppliers()
  doFetch()
})
</script>

<style scoped>
.inventory-list-page {
  --miq-app-chrome: 84px;
  --miq-gap: 10px;
  position: relative;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: var(--miq-gap);
  padding: 12px;
  height: calc(100vh - var(--miq-app-chrome));
  height: calc(100dvh - var(--miq-app-chrome));
  max-height: calc(100vh - var(--miq-app-chrome));
  max-height: calc(100dvh - var(--miq-app-chrome));
  min-height: 0;
  overflow: hidden;
}

.miq-modern {
  --hero-shadow:
    0 18px 36px -18px rgba(91, 33, 182, 0.55),
    0 4px 12px -6px rgba(168, 85, 247, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  --card-shadow: 0 1px 0 rgba(255, 255, 255, 0.95) inset, 0 10px 28px rgba(15, 23, 42, 0.06);
  background:
    radial-gradient(1100px 380px at 0% 0%, rgba(124, 58, 237, 0.1), transparent 60%),
    radial-gradient(900px 380px at 100% 0%, rgba(217, 70, 239, 0.08), transparent 60%),
    linear-gradient(160deg, #faf5ff 0%, #f8fafc 45%, #fdf4ff 100%);
}

.glass {
  position: relative;
  z-index: 1;
  background: #fff;
  border: 1px solid #e9d5ff;
  border-radius: 14px;
  box-shadow: var(--card-shadow);
}

/* ---------- タイトル条（紫→マゼンタ・他頁と分色） ---------- */
.page-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px 16px;
  overflow: hidden;
  isolation: isolate;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(125deg, #5b21b6 0%, #7c3aed 34%, #a855f7 66%, #d946ef 100%);
  box-shadow: var(--hero-shadow);
}

.page-toolbar-glow {
  position: absolute;
  inset: -40% -20% auto -10%;
  height: 120%;
  z-index: 0;
  background: radial-gradient(ellipse 80% 55% at 18% 0%, rgba(255, 255, 255, 0.22), transparent 55%);
  pointer-events: none;
}

.page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.header-left,
.header-actions {
  position: relative;
  z-index: 1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.header-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.42);
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(91, 33, 182, 0.3);
}

.header-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  min-width: 0;
}

.header-title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 10px;
}

.header-title {
  margin: 0;
  font-weight: 800;
  color: #fff;
  letter-spacing: 0.02em;
}

.header-desc {
  margin: 0;
  color: rgba(255, 255, 255, 0.88);
}

.header-meta {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  font-variant-numeric: tabular-nums;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.35);
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tb-btn {
  --k-rgb: 13 148 136;
  --k-fg: #0f766e;
  --k-bd: #5eead4;
  --k-tint: #ccfbf1;
  --k-tint-h: #99f6e4;
  --k-ico: #14b8a6;
  height: 32px !important;
  padding: 0 15px 0 12px !important;
  border-radius: 999px !important;
  font-weight: 700 !important;
  letter-spacing: 0.03em;
  color: var(--k-fg) !important;
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 40%, var(--k-tint) 100%) !important;
  border: 1px solid var(--k-bd) !important;
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgb(var(--k-rgb) / 0.12),
    0 2px 6px -1px rgba(91, 33, 182, 0.35) !important;
}
.tb-btn :deep(.el-icon) {
  color: var(--k-ico);
}
.tb-btn:hover {
  color: rgb(var(--k-rgb)) !important;
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 30%, var(--k-tint-h) 100%) !important;
  transform: translateY(-1px);
}

/* ---------- 合計カード ---------- */
.stat-cards {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
  gap: 8px;
  padding: 10px 12px;
}

.stat-card {
  --sc: #7c3aed;
  --sc-rgb: 124, 58, 237;
  --sc-ink: #6d28d9;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 11px 14px 9px;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(var(--sc-rgb), 0.09) 0%, #fff 72%);
  border: 1px solid rgba(var(--sc-rgb), 0.25);
  box-shadow: 0 3px 0 rgba(var(--sc-rgb), 0.28), 0 10px 18px -12px rgba(var(--sc-rgb), 0.5);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--sc) 0%, rgba(var(--sc-rgb), 0.3) 100%);
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 0 rgba(var(--sc-rgb), 0.35), 0 14px 22px -12px rgba(var(--sc-rgb), 0.55);
}
.stat-card--current_stock {
  --sc: #7c3aed;
  --sc-rgb: 124, 58, 237;
  --sc-ink: #6d28d9;
}
.stat-card--safety_stock {
  --sc: #0284c7;
  --sc-rgb: 2, 132, 199;
  --sc-ink: #0369a1;
}
.stat-card--planned_usage {
  --sc: #e11d48;
  --sc-rgb: 225, 29, 72;
  --sc-ink: #be123c;
}
.stat-card--order_quantity {
  --sc: #059669;
  --sc-rgb: 5, 150, 105;
  --sc-ink: #047857;
}

.stat-label {
  margin-bottom: 3px;
  font-size: 11px;
  font-weight: 700;
  color: var(--sc-ink);
}
.stat-value {
  font-size: 18px;
  font-weight: 800;
  line-height: 1.2;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}
.stat-card .stat-value.num-negative {
  color: #dc2626;
}

/* ---------- 筛选条 ---------- */
.filter-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 18px;
  padding: 10px 14px 10px 18px;
}
.filter-bar::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  bottom: 10px;
  width: 4px;
  border-radius: 99px;
  background: linear-gradient(180deg, #a78bfa, #a855f7, #d946ef);
}

.toolbar-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 10px;
}

.toolbar-label {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #6b21a8;
  background: #f3e8ff;
  box-shadow: inset 0 0 0 1px #e9d5ff;
}

.filter-bar :deep(.el-date-editor),
.filter-bar :deep(.el-select) {
  --el-fill-color-blank: #f8fafc;
  --el-border-color: #e2e8f0;
  --el-text-color-regular: #1e293b;
}
.filter-bar :deep(.el-input__wrapper),
.filter-bar :deep(.el-select__wrapper) {
  border: none;
  border-radius: 9px;
  background-color: #f8fafc;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}
.filter-bar :deep(.el-input__wrapper:hover),
.filter-bar :deep(.el-select__wrapper:hover) {
  background-color: #fff;
  box-shadow: 0 0 0 1px #c4b5fd inset;
}
.filter-bar :deep(.el-input__wrapper.is-focus),
.filter-bar :deep(.el-select__wrapper.is-focused) {
  background-color: #fff;
  box-shadow:
    0 0 0 1px #7c3aed inset,
    0 0 0 3px rgba(124, 58, 237, 0.15);
}

.date-range-picker {
  width: 240px;
}
.product-select {
  width: 200px;
}
.supplier-select {
  min-width: 200px;
  max-width: 280px;
}

.date-quick {
  display: flex;
  gap: 2px;
  padding: 2px;
  border-radius: 9px;
  background: #faf5ff;
  box-shadow: inset 0 0 0 1px #e9d5ff;
}
.date-quick-btn {
  min-width: 52px !important;
  height: 24px;
  border-radius: 7px !important;
  color: #6b21a8 !important;
  background: transparent !important;
  border: 1px solid transparent !important;
  box-shadow: none !important;
  font-weight: 600 !important;
}
.date-quick-btn + .date-quick-btn {
  margin-left: 0;
}
.date-quick-btn:hover {
  color: #5b21b6 !important;
  background: #f3e8ff !important;
}
.date-quick-btn--active,
.date-quick-btn--active:hover {
  color: #fff !important;
  background: linear-gradient(180deg, #a855f7 0%, #7c3aed 100%) !important;
  box-shadow: 0 2px 0 #5b21b6, 0 6px 12px -6px rgba(124, 58, 237, 0.7) !important;
}

/* ---------- テーブル（flex 填满） ---------- */
.table-section {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 10px 12px;
}

.table-section :deep(.el-table) {
  flex: 1 1 auto;
  height: 100% !important;
}
.table-section :deep(.el-table__inner-wrapper) {
  height: 100%;
}
.table-section :deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
}

.data-table {
  font-size: 12px;
  border-radius: 12px;
  overflow: hidden;
  background: #fff !important;
}
.data-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #faf5ff 0%, #f3e8ff 100%) !important;
  color: #6b21a8 !important;
  font-weight: 700;
  font-size: 12px;
  border-bottom: 2px solid #d8b4fe !important;
}
.data-table :deep(.el-table__body td) {
  padding: 6px 10px;
  color: #1e293b !important;
  font-variant-numeric: tabular-nums;
}
.data-table :deep(.el-table__body tr:hover > td) {
  background: #faf5ff !important;
}
.data-table :deep(.el-table__body tr:hover > td:first-child) {
  box-shadow: inset 3px 0 0 #7c3aed;
}

.table-footer {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f3e8ff;
}

.footer-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.footer-pill {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  background: #f8fafc;
  color: #475569;
  border: 1px solid #e2e8f0;
}
.footer-pill--count {
  background: #f3e8ff;
  color: #6b21a8;
  border-color: #e9d5ff;
}
.footer-pill--current_stock {
  background: #ede9fe;
  color: #5b21b6;
  border-color: #ddd6fe;
}
.footer-pill--safety_stock {
  background: #e0f2fe;
  color: #0369a1;
  border-color: #bae6fd;
}
.footer-pill--planned_usage {
  background: #ffe4e6;
  color: #be123c;
  border-color: #fecdd3;
}
.footer-pill--order_quantity {
  background: #d1fae5;
  color: #047857;
  border-color: #a7f3d0;
}

.num-positive {
  color: #1e293b;
}
.num-zero {
  color: #64748b;
}
.num-negative {
  color: #dc2626;
  font-weight: 600;
}

@media (max-width: 768px) {
  .inventory-list-page {
    padding: 8px;
    --miq-gap: 8px;
  }
  .header-actions {
    width: 100%;
  }
  .date-range-picker,
  .product-select,
  .supplier-select {
    width: 100%;
    max-width: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .stat-card:hover,
  .tb-btn:hover {
    transform: none;
  }
}
</style>
