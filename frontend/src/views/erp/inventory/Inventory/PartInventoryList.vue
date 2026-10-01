<template>
  <div class="inventory-list-page piq-modern">
    <div class="page-header glass animate-in">
      <div class="page-header-fx" aria-hidden="true"><span class="fx-orb orb-a" /><span class="fx-orb orb-b" /><span class="fx-grid" /></div>
      <div class="header-left">
        <div class="header-icon header-icon--part">
          <el-icon size="24"><Files /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="header-title">部品在庫照会</h1>
          <span class="header-meta">{{ totalCount }} 件</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button size="small" class="btn-glass" @click="exportCsv">
          <el-icon><Download /></el-icon>CSV
        </el-button>
      </div>
    </div>

    <div class="stat-cards glass animate-in" style="--delay: 0.05s">
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

    <div class="toolbar glass animate-in" style="--delay: 0.1s">
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
        <span class="toolbar-label">部品</span>
        <el-select
          v-model="filters.partCd"
          placeholder="全て"
          clearable
          filterable
          size="small"
          class="product-select"
          @change="onFilterChange"
        >
          <el-option
            v-for="p in partOptions"
            :key="p.part_cd"
            :label="p.part_name || p.part_cd"
            :value="p.part_cd"
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

    <div class="table-wrap glass animate-in" style="--delay: 0.15s">
      <el-table
        :data="list"
        v-loading="loading"
        stripe
        size="small"
        class="data-table"
        show-summary
        :summary-method="getSummaries"
        :height="tableHeight"
      >
        <el-table-column prop="part_cd" label="部品CD" width="100" fixed />
        <el-table-column prop="part_name" label="部品名" width="140" show-overflow-tooltip />
        <el-table-column prop="date" label="日付" width="105" align="center" />
        <el-table-column label="曜日" width="56" align="center">
          <template #default="{ row }">
            {{ weekdayJa(row.date) }}
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="仕入先" width="120" show-overflow-tooltip />
        <el-table-column prop="standard_spec" label="規格" width="100" show-overflow-tooltip />
        <el-table-column prop="initial_stock" label="初期在庫" width="88" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.initial_stock)">{{ formatNum(row.initial_stock) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="current_stock" label="現在在庫" width="92" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.current_stock)">{{ formatNum(row.current_stock) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="planned_usage" label="使用数" width="80" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.planned_usage)">{{ formatNum(row.planned_usage) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="manual_usage" label="使用数調整" width="92" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.manual_usage)">{{ formatNum(row.manual_usage) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="usage_plan_qty" label="計画使用" width="88" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.usage_plan_qty)">{{ formatNum(row.usage_plan_qty) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="stock_trend" label="推移" width="72" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.stock_trend)">{{ formatNum(row.stock_trend) }}</span>
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
        <el-table-column prop="order_bundle_quantity" label="注文本数" width="88" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.order_bundle_quantity)">{{ formatNum(row.order_bundle_quantity) }}</span>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Files, Download } from '@element-plus/icons-vue'
import { getPartStockList, getPartStockSupplierNames } from '@/api/part'
import { getPartList } from '@/api/master/partMaster'
import { useInventoryOperationPermission } from '@/composables/useInventoryOperationPermission'
import { guardInventoryOperation } from '@/utils/inventoryOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = useInventoryOperationPermission()


export interface PartStockInquiryRow {
  id?: number
  part_cd: string
  part_name: string
  date: string
  supplier_name?: string | null
  standard_spec?: string | null
  initial_stock?: number | null
  current_stock?: number | null
  planned_usage?: number | null
  manual_usage?: number | null
  usage_plan_qty?: number | null
  stock_trend?: number | null
  adjustment_quantity?: number | null
  order_quantity?: number | null
  order_bundle_quantity?: number | null
  unit?: string | null
  unit_price?: number | null
  remarks?: string | null
}

const loading = ref(false)
const list = ref<PartStockInquiryRow[]>([])
const partOptions = ref<{ part_cd: string; part_name: string }[]>([])
const supplierOptions = ref<string[]>([])
const dateRange = ref<[string, string] | null>(null)

const filters = reactive({
  partCd: '',
  suppliers: [] as string[]
})

const totalCount = ref(0)

const STAT_FIELDS: { key: keyof PartStockInquiryRow; label: string }[] = [
  { key: 'current_stock', label: '現在在庫' },
  { key: 'planned_usage', label: '使用数' },
  { key: 'manual_usage', label: '使用数調整' },
  { key: 'usage_plan_qty', label: '計画使用' },
  { key: 'order_quantity', label: '注文数' }
]

const statCards = computed(() => {
  const data = list.value
  return STAT_FIELDS.map(({ key, label }) => {
    const sum = data.reduce((acc, row) => acc + (Number(row[key]) || 0), 0)
    return { key: String(key), label, sum }
  })
})

const SUMMARY_NUM_KEYS = new Set([
  'initial_stock',
  'current_stock',
  'planned_usage',
  'manual_usage',
  'usage_plan_qty',
  'stock_trend',
  'adjustment_quantity',
  'order_quantity',
  'order_bundle_quantity'
])

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

const tableHeight = computed(() => 'calc(100vh - 260px)')

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

function getSummaries(param: { columns: { property?: string }[]; data: PartStockInquiryRow[] }) {
  const { columns, data } = param
  const sums: string[] = []
  columns.forEach((col, index) => {
    if (index === 0) {
      sums.push('合計')
      return
    }
    const prop = col.property
    if (prop && SUMMARY_NUM_KEYS.has(prop)) {
      const total = data.reduce(
        (acc, row) => acc + (Number((row as unknown as Record<string, unknown>)[prop]) || 0),
        0
      )
      sums.push(total.toLocaleString())
    } else {
      sums.push('')
    }
  })
  return sums
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
    end_date: end
  }
  if (filters.partCd) params.part_cd = filters.partCd
  if (filters.suppliers.length > 0) params.suppliers = filters.suppliers.join(',')

  getPartStockList(params)
    .then((res) => {
      const listData = res?.data?.list ?? []
      list.value = listData as PartStockInquiryRow[]
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

async function fetchParts() {
  try {
    const res = await getPartList({ page: 1, pageSize: 8000, status: 1 })
    const raw = res?.data?.list ?? []
    partOptions.value = raw.map((p) => ({
      part_cd: p.part_cd,
      part_name: p.part_name
    }))
  } catch (e) {
    console.error(e)
    partOptions.value = []
  }
}

async function fetchSuppliers() {
  try {
    const res = await getPartStockSupplierNames()
    supplierOptions.value = res?.data ?? []
  } catch (e) {
    console.error(e)
    supplierOptions.value = []
  }
}

function exportCsv() {
  if (!guardInventoryOperation(canExport)) return

  const headers = [
    '部品CD',
    '部品名',
    '日付',
    '曜日',
    '仕入先',
    '規格',
    '初期在庫',
    '現在在庫',
    '使用数',
    '使用数調整',
    '計画使用',
    '推移',
    '調整数',
    '注文数',
    '注文本数',
    '単位',
    '単価',
    '備考'
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
        row.part_cd,
        row.part_name,
        row.date,
        weekdayJa(row.date),
        row.supplier_name ?? '',
        row.standard_spec ?? '',
        row.initial_stock ?? '',
        row.current_stock ?? '',
        row.planned_usage ?? '',
        row.manual_usage ?? '',
        row.usage_plan_qty ?? '',
        row.stock_trend ?? '',
        row.adjustment_quantity ?? '',
        row.order_quantity ?? '',
        row.order_bundle_quantity ?? '',
        row.unit ?? '',
        row.unit_price ?? '',
        row.remarks ?? ''
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
  a.download = `part_stock_${s || 'start'}_${e || 'end'}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('CSVをダウンロードしました')
}

onMounted(() => {
  initDate()
  fetchParts()
  fetchSuppliers()
  doFetch()
})
</script>

<style scoped>
.inventory-list-page {
  position: relative;
  padding: 14px 18px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.glass {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1);
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

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-radius: 16px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.page-header:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.header-icon--part {
  background: linear-gradient(145deg, #ea580c 0%, #f97316 48%, #fb923c 100%);
  box-shadow:
    0 4px 16px rgba(234, 88, 12, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.header-icon--part:hover {
  transform: scale(1.05);
  box-shadow:
    0 8px 24px rgba(234, 88, 12, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.28);
}

.header-title {
  font-size: 20px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0;
  letter-spacing: -0.02em;
}

.header-meta {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin-left: 10px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.btn-glass {
  border-radius: 10px !important;
  background: linear-gradient(
    145deg,
    rgba(255, 255, 255, 0.14) 0%,
    rgba(251, 146, 60, 0.18) 100%
  ) !important;
  border: 1px solid rgba(253, 186, 116, 0.45) !important;
  color: #fff7ed !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em;
  box-shadow:
    0 2px 12px rgba(234, 88, 12, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease, background 0.2s ease !important;
}

.btn-glass:hover {
  background: linear-gradient(
    145deg,
    rgba(255, 255, 255, 0.2) 0%,
    rgba(251, 146, 60, 0.28) 100%
  ) !important;
  border-color: rgba(254, 215, 170, 0.65) !important;
  transform: translateY(-1px);
  box-shadow:
    0 6px 20px rgba(234, 88, 12, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
}

.stat-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 16px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 74px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.25s ease;
  animation: cardIn 0.4s ease-out backwards;
  animation-delay: calc(var(--delay, 0s) + 0.02s * var(--i, 0));
}

.stat-card:hover {
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

.stat-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 4px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.stat-value {
  font-size: 15px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  transition: color 0.2s ease;
}

.stat-card .stat-value.num-negative {
  color: #f87171;
  text-shadow: 0 0 20px rgba(248, 113, 113, 0.3);
}

.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 18px;
  padding: 12px 16px;
  border-radius: 16px;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.65);
  white-space: nowrap;
  font-weight: 500;
}

.toolbar :deep(.el-date-editor),
.toolbar :deep(.el-select) {
  --el-fill-color-blank: rgba(255, 255, 255, 0.08);
  --el-border-color: rgba(255, 255, 255, 0.15);
  --el-text-color-regular: rgba(255, 255, 255, 0.9);
}

.toolbar :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: none;
  transition: all 0.2s ease;
}

.toolbar :deep(.el-input__wrapper:hover),
.toolbar :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
}

.date-range-picker {
  width: 240px;
}

.date-quick {
  display: flex;
  gap: 8px;
}

.date-quick-btn {
  min-width: 58px !important;
  border-radius: 999px !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em;
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  color: rgba(255, 255, 255, 0.72) !important;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease !important;
}

.date-quick-btn:hover {
  background: rgba(255, 255, 255, 0.11) !important;
  border-color: rgba(255, 255, 255, 0.22) !important;
  color: #fff !important;
  transform: translateY(-1px);
}

.date-quick-btn--active {
  background: linear-gradient(145deg, rgba(234, 88, 12, 0.55), rgba(251, 146, 60, 0.45)) !important;
  border-color: rgba(255, 255, 255, 0.32) !important;
  color: #fff !important;
  box-shadow:
    0 4px 16px rgba(234, 88, 12, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
}

.date-quick-btn--active:hover {
  background: linear-gradient(145deg, rgba(234, 88, 12, 0.68), rgba(251, 146, 60, 0.52)) !important;
}

.product-select {
  width: 200px;
}

.supplier-select {
  min-width: 200px;
  max-width: 280px;
}

.table-wrap {
  flex: 1;
  min-height: 0;
  padding: 14px 16px;
  border-radius: 16px;
  transition: box-shadow 0.2s ease;
}

.table-wrap:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.data-table {
  font-size: 12px;
  border-radius: 12px;
  overflow: hidden;
  background: #ffffff !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.data-table :deep(.el-table__inner-wrapper) {
  background: #ffffff;
}

.data-table :deep(.el-table__header-wrapper) {
  background: #ffffff;
}

.data-table :deep(.el-table__header th) {
  background: #f1f5f9 !important;
  color: #334155 !important;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 10px;
  border-color: #e2e8f0 !important;
}

.data-table :deep(.el-table__body-wrapper) {
  background: #ffffff;
}

.data-table :deep(.el-table__body tr) {
  transition: background 0.15s ease;
}

.data-table :deep(.el-table__body tr:hover > td) {
  background: #f8fafc !important;
}

.data-table :deep(.el-table__body td) {
  padding: 6px 10px;
  border-color: #e2e8f0 !important;
  background: #ffffff !important;
  color: #1e293b !important;
}

.data-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #fafbfc !important;
  color: #1e293b !important;
}

.data-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped:hover > td) {
  background: #f1f5f9 !important;
}

.data-table :deep(.el-table__footer-wrapper) {
  background: #ffffff;
}

.data-table :deep(.el-table__footer td) {
  background: #f1f5f9 !important;
  font-weight: 600;
  padding: 8px 10px;
  font-size: 12px;
  color: #1e293b !important;
  border-color: #e2e8f0 !important;
}

.data-table :deep(.el-table__empty-block) {
  background: #ffffff !important;
}

.num-positive { color: #1e293b; }
.num-zero { color: #64748b; }
.num-negative { color: #dc2626; font-weight: 600; }

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（部品在庫照会 / オレンジ系）
 * ============================================================ */
.piq-modern {
  --hero-shadow:
    0 18px 36px -18px rgba(154, 52, 18, 0.6),
    0 4px 12px -6px rgba(234, 88, 12, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  --card-shadow:
    0 10px 24px -18px rgba(194, 65, 12, 0.45),
    0 1px 2px rgba(15, 23, 42, 0.04);
  background: linear-gradient(160deg, #fff7ed 0%, #fffbf5 42%, #f8fafc 100%);
}

/* ルート遷移中に backdrop-filter があると背景が描画されないことがあるため不透明カードにする */
.piq-modern .glass {
  background: #fff;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
  border: 1px solid #fde4cf;
  box-shadow: var(--card-shadow);
}

/* ---------- ヘッダー ---------- */
.piq-modern .page-header {
  overflow: hidden;
  isolation: isolate;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(125deg, #7c2d12 0%, #c2410c 34%, #ea580c 66%, #fb923c 100%);
  box-shadow: var(--hero-shadow);
}
.piq-modern .page-header:hover {
  transform: none;
  box-shadow: var(--hero-shadow);
}
.piq-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
}
.piq-modern .fx-orb {
  position: absolute;
  border-radius: 50%;
}
.piq-modern .orb-a {
  width: 220px;
  height: 220px;
  top: -110px;
  right: 12%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0) 70%);
}
.piq-modern .orb-b {
  width: 180px;
  height: 180px;
  bottom: -110px;
  left: 24%;
  background: radial-gradient(circle, rgba(253, 230, 138, 0.42) 0%, rgba(253, 230, 138, 0) 70%);
}
.piq-modern .fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 22px 22px;
  -webkit-mask-image: radial-gradient(ellipse at 18% 50%, #000 0%, transparent 70%);
  mask-image: radial-gradient(ellipse at 18% 50%, #000 0%, transparent 70%);
}
.piq-modern .header-icon--part {
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.42), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.45);
  box-shadow:
    0 3px 0 rgba(124, 45, 18, 0.5),
    0 10px 18px -8px rgba(67, 20, 7, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  transform: perspective(300px) rotateX(8deg) rotateY(-10deg);
}
.piq-modern .header-icon--part:hover {
  transform: perspective(300px) rotateX(0deg) rotateY(0deg) translateY(-1px);
  box-shadow:
    0 4px 0 rgba(124, 45, 18, 0.5),
    0 12px 20px -8px rgba(67, 20, 7, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}
.piq-modern .header-text {
  display: flex;
  align-items: center;
  gap: 10px;
}
.piq-modern .header-title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #fff;
  text-shadow: 0 2px 6px rgba(67, 20, 7, 0.3);
}
.piq-modern .header-meta {
  display: inline-flex;
  align-items: center;
  height: 22px;
  margin-left: 0;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  font-variant-numeric: tabular-nums;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 2px 0 rgba(124, 45, 18, 0.35);
}

/* CSV：白のキーキャップ */
.piq-modern .btn-glass {
  height: 30px;
  padding: 0 14px !important;
  border-radius: 9px !important;
  color: #c2410c !important;
  font-weight: 700 !important;
  background: linear-gradient(180deg, #ffffff 0%, #fff7ed 100%) !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  box-shadow:
    0 3px 0 #9a3412,
    0 10px 18px -8px rgba(67, 20, 7, 0.55) !important;
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease !important;
}
.piq-modern .btn-glass:hover {
  transform: translateY(-2px);
  background: #fff !important;
  border-color: #fff !important;
  box-shadow:
    0 5px 0 #9a3412,
    0 14px 22px -8px rgba(67, 20, 7, 0.6) !important;
}
.piq-modern .btn-glass:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 #9a3412 !important;
}

/* ---------- 集計カード（色分け・キーキャップ） ---------- */
.piq-modern .stat-cards {
  gap: 10px;
  padding: 12px 14px;
}
.piq-modern .stat-card {
  --sc: #ea580c;
  --sc-rgb: 234, 88, 12;
  --sc-ink: #c2410c;
  position: relative;
  overflow: hidden;
  flex: 1 1 120px;
  align-items: flex-start;
  min-width: 120px;
  padding: 11px 14px 9px;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(var(--sc-rgb), 0.09) 0%, #fff 72%);
  border: 1px solid rgba(var(--sc-rgb), 0.25);
  box-shadow:
    0 3px 0 rgba(var(--sc-rgb), 0.35),
    0 10px 18px -12px rgba(var(--sc-rgb), 0.6);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    border-color 0.15s ease;
}
.piq-modern .stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--sc) 0%, rgba(var(--sc-rgb), 0.3) 100%);
}
.piq-modern .stat-card:hover {
  transform: translateY(-2px);
  background: linear-gradient(180deg, rgba(var(--sc-rgb), 0.12) 0%, #fff 72%);
  border-color: rgba(var(--sc-rgb), 0.45);
  box-shadow:
    0 5px 0 rgba(var(--sc-rgb), 0.4),
    0 14px 22px -12px rgba(var(--sc-rgb), 0.65);
}
.piq-modern .stat-label {
  margin-bottom: 3px;
  font-size: 11px;
  font-weight: 700;
  color: var(--sc-ink);
  text-transform: none;
}
.piq-modern .stat-value {
  font-size: 18px;
  font-weight: 800;
  line-height: 1.2;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}
.piq-modern .stat-card .stat-value.num-negative {
  color: #dc2626;
  text-shadow: none;
}
.piq-modern .stat-card--current_stock {
  --sc: #ea580c;
  --sc-rgb: 234, 88, 12;
  --sc-ink: #c2410c;
}
.piq-modern .stat-card--planned_usage {
  --sc: #e11d48;
  --sc-rgb: 225, 29, 72;
  --sc-ink: #be123c;
}
.piq-modern .stat-card--manual_usage {
  --sc: #7c3aed;
  --sc-rgb: 124, 58, 237;
  --sc-ink: #6d28d9;
}
.piq-modern .stat-card--usage_plan_qty {
  --sc: #0284c7;
  --sc-rgb: 2, 132, 199;
  --sc-ink: #0369a1;
}
.piq-modern .stat-card--order_quantity {
  --sc: #059669;
  --sc-rgb: 5, 150, 105;
  --sc-ink: #047857;
}

/* ---------- ツールバー ---------- */
.piq-modern .toolbar {
  gap: 14px 18px;
  padding: 10px 14px;
}
.piq-modern .toolbar-label {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #9a3412;
  background: #ffedd5;
  box-shadow: inset 0 0 0 1px #fed7aa;
}
.piq-modern .toolbar :deep(.el-date-editor),
.piq-modern .toolbar :deep(.el-select) {
  --el-fill-color-blank: #f8fafc;
  --el-border-color: #e2e8f0;
  --el-text-color-regular: #1e293b;
}
.piq-modern .toolbar :deep(.el-input__wrapper),
.piq-modern .toolbar :deep(.el-select__wrapper) {
  border: none;
  border-radius: 8px;
  background-color: #f8fafc;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition:
    box-shadow 0.15s ease,
    background-color 0.15s ease;
}
.piq-modern .toolbar :deep(.el-input__wrapper:hover),
.piq-modern .toolbar :deep(.el-select__wrapper:hover) {
  background-color: #fff;
  box-shadow: 0 0 0 1px #fdba74 inset;
}
.piq-modern .toolbar :deep(.el-input__wrapper.is-focus),
.piq-modern .toolbar :deep(.el-input__wrapper.is-active),
.piq-modern .toolbar :deep(.el-select__wrapper.is-focused) {
  background-color: #fff;
  box-shadow:
    0 0 0 1px #ea580c inset,
    0 0 0 3px rgba(234, 88, 12, 0.15);
}

/* 前日・今日・翌日：セグメント */
.piq-modern .date-quick {
  gap: 2px;
  padding: 2px;
  border-radius: 9px;
  background: #fff7ed;
  box-shadow: inset 0 0 0 1px #fed7aa;
}
.piq-modern .date-quick-btn {
  min-width: 52px !important;
  height: 24px;
  border-radius: 7px !important;
  color: #9a3412 !important;
  background: transparent !important;
  border: 1px solid transparent !important;
  box-shadow: none !important;
}
.piq-modern .date-quick-btn + .date-quick-btn {
  margin-left: 0;
}
.piq-modern .date-quick-btn:hover {
  transform: none;
  color: #7c2d12 !important;
  background: #ffedd5 !important;
  border-color: transparent !important;
}
.piq-modern .date-quick-btn--active,
.piq-modern .date-quick-btn--active:hover {
  color: #fff !important;
  background: linear-gradient(180deg, #fb923c 0%, #ea580c 100%) !important;
  box-shadow:
    0 2px 0 #9a3412,
    0 6px 12px -6px rgba(234, 88, 12, 0.7) !important;
}

/* ---------- テーブル ---------- */
.piq-modern .table-wrap {
  padding: 10px 12px;
}
.piq-modern .table-wrap:hover {
  box-shadow: var(--card-shadow);
}
.piq-modern .data-table {
  border-radius: 10px;
  box-shadow: 0 0 0 1px #f1e4d8;
}
.piq-modern .data-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #fff7ed 0%, #ffedd5 100%) !important;
  color: #9a3412 !important;
  font-weight: 700;
  box-shadow: inset 0 -2px 0 #fdba74;
}
.piq-modern .data-table :deep(.el-table__body tr:hover > td) {
  background: #fff7ed !important;
}
.piq-modern .data-table :deep(.el-table__body tr:hover > td:first-child) {
  box-shadow: inset 3px 0 0 #ea580c;
}
.piq-modern .data-table :deep(.el-table__body td .cell) {
  font-variant-numeric: tabular-nums;
}
.piq-modern .data-table :deep(.el-table__footer td) {
  background: linear-gradient(180deg, #fff7ed 0%, #ffedd5 100%) !important;
  color: #7c2d12 !important;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  border-top: 2px solid #fdba74 !important;
}

@media (prefers-reduced-motion: reduce) {
  .piq-modern .animate-in,
  .piq-modern .stat-card {
    animation: none;
    opacity: 1;
  }
  .piq-modern .stat-card:hover,
  .piq-modern .btn-glass:hover {
    transform: none;
  }
}
</style>
