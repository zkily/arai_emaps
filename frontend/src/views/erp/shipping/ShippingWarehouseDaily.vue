<template>
  <div class="wh-page">
    <div class="wh-bg" aria-hidden="true">
      <div class="wh-bg__orb wh-bg__orb--1" />
      <div class="wh-bg__orb wh-bg__orb--2" />
      <div class="wh-bg__orb wh-bg__orb--3" />
      <div class="wh-bg__noise" />
    </div>

    <section class="wh-top-card glass animate-in">
      <div class="wh-top-card__head">
        <div class="wh-top-card__brand">
          <div class="wh-hero__icon-wrap">
            <div class="wh-hero__icon">
              <el-icon :size="22"><OfficeBuilding /></el-icon>
            </div>
            <div class="wh-hero__icon-glow" aria-hidden="true" />
          </div>
          <div class="wh-top-card__titles">
            <h1 class="wh-top-card__title">{{ t('menu.ERP_SHIPPING_WAREHOUSE_DAILY') }}</h1>
            <p class="wh-top-card__desc">{{ t('shipping.warehouseDaily.desc') }}</p>
          </div>
        </div>
        <div class="wh-top-card__actions">
          <el-button
            type="warning"
            class="wh-btn-sync wh-btn-sync--hero"
            size="small"
            :loading="syncLoading"
            @click="handleSyncFromOrderDaily"
          >
            <el-icon class="wh-btn-sync__icon"><Refresh /></el-icon>
            {{ t('shipping.warehouseDaily.syncFromOrderDaily') }}
          </el-button>
          <el-button
            type="success"
            class="wh-btn-gen wh-btn-gen--hero"
            size="small"
            :loading="genLoading"
            @click="handleGenerateData"
          >
            <el-icon class="wh-btn-gen__icon"><MagicStick /></el-icon>
            {{ t('shipping.warehouseDaily.generateData') }}
          </el-button>
          <el-button
            type="info"
            class="wh-btn-print wh-btn-print--hero"
            size="small"
            :disabled="loading || printShortageLoading || !queryDateRange || queryDateRange.length !== 2"
            :loading="printShortageLoading"
            @click="handleShortageIssuePrint"
          >
            <el-icon class="wh-btn-print__icon"><Printer /></el-icon>
            {{ t('shipping.warehouseDaily.shortageIssuePrint') }}
          </el-button>
        </div>
      </div>
      <div class="wh-top-card__filters">
        <el-form class="wh-form" size="small" :inline="true" @submit.prevent>
          <el-form-item :label="t('shipping.warehouseDaily.dateRange')" class="wh-form-item wh-form-item--compact">
            <div class="wh-range-with-nudges">
              <el-date-picker
                v-model="queryDateRange"
                type="daterange"
                value-format="YYYY-MM-DD"
                size="small"
                class="wh-daterange"
                :start-placeholder="t('shipping.warehouseDaily.rangeStart')"
                :end-placeholder="t('shipping.warehouseDaily.rangeEnd')"
                :editable="false"
                unlink-panels
              />
              <div class="wh-range-nudges" role="group" :aria-label="t('shipping.warehouseDaily.dateNudgeGroup')">
                <el-button text type="primary" size="small" class="wh-shortcut" @click="shiftDateRangeByDays(-1)">
                  {{ t('shipping.prevDay') }}
                </el-button>
                <el-button text type="primary" size="small" class="wh-shortcut" @click="setRangeToday">
                  {{ t('shipping.today') }}
                </el-button>
                <el-button text type="primary" size="small" class="wh-shortcut" @click="shiftDateRangeByDays(1)">
                  {{ t('shipping.nextDay') }}
                </el-button>
              </div>
            </div>
          </el-form-item>
          <el-form-item :label="t('shipping.warehouseDaily.product')" class="wh-form-item wh-form-item--compact">
            <el-select
              v-model="filterProductCd"
              class="wh-product-select"
              filterable
              clearable
              size="small"
              :placeholder="t('shipping.warehouseDaily.allProducts')"
              @clear="filterProductCd = ''"
            >
              <el-option :label="t('shipping.warehouseDaily.allProducts')" value="" />
              <el-option
                v-for="p in productOptions"
                :key="p.product_cd"
                :label="`${p.product_cd} — ${p.product_name}`"
                :value="p.product_cd"
              />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('shipping.warehouseDaily.productTypeFilter')" class="wh-form-item wh-form-item--compact">
            <el-switch
              v-model="massProductOnly"
              inline-prompt
              size="small"
              :active-text="t('shipping.warehouseDaily.massProductOnlySwitch')"
              :inactive-text="t('shipping.warehouseDaily.allTypesSwitch')"
            />
          </el-form-item>
        </el-form>
        <div class="wh-toolbar__end">
          <el-popover placement="bottom-end" :width="300" trigger="click">
            <template #reference>
              <el-button size="small" class="wh-btn-columns-pill">
                <el-icon class="wh-col-picker-icon"><Setting /></el-icon>
                {{ t('shipping.warehouseDaily.columnPicker') }}
              </el-button>
            </template>
            <div class="wh-col-picker">
              <p class="wh-col-picker__hint">{{ t('shipping.warehouseDaily.columnPickerHint') }}</p>
              <el-checkbox-group v-model="visibleColumnList" class="wh-col-picker__group">
                <el-checkbox
                  v-for="opt in columnPickerOptions"
                  :key="opt.key"
                  :label="opt.key"
                  class="wh-col-picker__item"
                >
                  {{ opt.label }}
                </el-checkbox>
              </el-checkbox-group>
            </div>
          </el-popover>
        </div>
      </div>
    </section>

    <section class="wh-table-section glass animate-in" style="animation-delay: 0.07s">
      <div class="wh-table-section__inner">
        <div ref="tableScrollRef" class="wh-table-scroll">
          <el-table
            v-loading="loading"
            :data="tableData"
            stripe
            border
            size="small"
            class="wh-table"
            empty-text=" "
            :height="tableBodyHeight"
            :default-sort="tableDefaultSort"
            @sort-change="onTableSortChange"
          >
          <el-table-column
            v-if="colVisible('destination_name')"
            prop="destination_name"
            :label="t('shipping.warehouseDaily.col_destination_name')"
            width="150"
            fixed="left"
            show-overflow-tooltip
          />
          <el-table-column
            v-if="colVisible('product_cd')"
            prop="product_cd"
            :label="t('shipping.warehouseDaily.col_product_cd')"
            width="80"
            fixed="left"
            show-overflow-tooltip
          />
          <el-table-column
            v-if="colVisible('product_name')"
            prop="product_name"
            :label="t('shipping.warehouseDaily.col_product_name')"
            width="120"
            show-overflow-tooltip
            sortable="custom"
          />
          <el-table-column
            v-if="colVisible('product_type')"
            prop="product_type"
            :label="t('shipping.warehouseDaily.col_product_type')"
            width="100"
            show-overflow-tooltip
          />
          <el-table-column
            v-if="colVisible('destination_cd')"
            prop="destination_cd"
            :label="t('shipping.warehouseDaily.col_destination_cd')"
            width="80"
            show-overflow-tooltip
          />
          <el-table-column
            v-if="colVisible('work_date')"
            prop="work_date"
            :label="t('shipping.warehouseDaily.col_work_date')"
            width="104"
            align="center"
          />
          <el-table-column
            v-if="colVisible('weekday')"
            prop="weekday"
            :label="t('shipping.warehouseDaily.col_weekday')"
            width="60"
            align="center"
          />
          <el-table-column
            v-if="colVisible('order_qty')"
            prop="order_qty"
            :label="t('shipping.warehouseDaily.col_order_qty')"
            width="96"
            align="right"
          >
            <template #default="{ row }">
              <span class="wh-num" :class="{ 'wh-num--negative': isQtyNegative(row.order_qty) }">{{ formatQty(row.order_qty) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="colVisible('forecast_qty')"
            prop="forecast_qty"
            :label="t('shipping.warehouseDaily.col_forecast_qty')"
            width="96"
            align="right"
          >
            <template #default="{ row }">
              <span class="wh-num" :class="{ 'wh-num--negative': isQtyNegative(row.forecast_qty) }">{{ formatQty(row.forecast_qty) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="colVisible('warehouse_carryover')"
            prop="warehouse_carryover"
            :label="t('shipping.warehouseDaily.col_warehouse_carryover')"
            width="100"
            align="right"
          >
            <template #default="{ row }">
              <span class="wh-num" :class="{ 'wh-num--negative': isQtyNegative(row.warehouse_carryover) }">{{ formatQty(row.warehouse_carryover) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="colVisible('warehouse_actual')"
            prop="warehouse_actual"
            :label="t('shipping.warehouseDaily.col_warehouse_actual')"
            width="100"
            align="right"
          >
            <template #default="{ row }">
              <span class="wh-num" :class="{ 'wh-num--negative': isQtyNegative(row.warehouse_actual) }">{{ formatQty(row.warehouse_actual) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="colVisible('warehouse_defect')"
            prop="warehouse_defect"
            :label="t('shipping.warehouseDaily.col_warehouse_defect')"
            width="100"
            align="right"
          >
            <template #default="{ row }">
              <span
                class="wh-num wh-num--warn"
                :class="{ 'wh-num--negative': isQtyNegative(row.warehouse_defect) }"
              >{{ formatQty(row.warehouse_defect) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="colVisible('warehouse_disposal')"
            prop="warehouse_disposal"
            :label="t('shipping.warehouseDaily.col_warehouse_disposal')"
            width="100"
            align="right"
          >
            <template #default="{ row }">
              <span
                class="wh-num wh-num--muted"
                :class="{ 'wh-num--negative': isQtyNegative(row.warehouse_disposal) }"
              >{{ formatQty(row.warehouse_disposal) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="colVisible('warehouse_hold')"
            prop="warehouse_hold"
            :label="t('shipping.warehouseDaily.col_warehouse_hold')"
            width="104"
            align="right"
          >
            <template #default="{ row }">
              <span class="wh-num" :class="{ 'wh-num--negative': isQtyNegative(row.warehouse_hold) }">{{ formatQty(row.warehouse_hold) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="colVisible('warehouse_stock')"
            prop="warehouse_stock"
            :label="t('shipping.warehouseDaily.col_warehouse_stock')"
            width="100"
            align="right"
            fixed="right"
          >
            <template #default="{ row }">
              <span
                class="wh-num wh-num--accent"
                :class="{ 'wh-num--negative': isQtyNegative(row.warehouse_stock) }"
              >{{ formatQty(row.warehouse_stock) }}</span>
            </template>
          </el-table-column>
        </el-table>
          <div v-if="!loading && tableData.length === 0" class="wh-empty">
            <el-empty :description="t('shipping.noDataTable')" :image-size="120" />
          </div>
        </div>

        <div class="wh-pagination-wrap">
          <el-pagination
            :current-page="currentPage"
            :page-size="pageSize"
            :total="totalCount"
            :disabled="loading"
            layout="total, prev, pager, next, jumper"
            background
            @current-change="onPageChange"
          />
        </div>
      </div>
    </section>

    <div ref="printContentRef" class="print-content-hidden">
      <div class="print-body">
        <div class="print-header">
          <div class="print-title-wrap">
            <span class="print-title-accent" />
            <h1 class="print-title">出荷不足数一覧</h1>
            <p class="print-subtitle">検査工程用</p>
          </div>
          <div class="print-header-row">
            <div class="print-period-block">
              <span class="print-period-dot" />
              <span class="print-period-label">対象期間</span>
              <span class="print-period-value">{{ printPeriodFormatted }}</span>
            </div>
            <div class="print-summary-box">
              <span class="print-summary-label">合計</span>
              <span class="print-summary-item"><em>箱数</em> {{ formatPrintNumber(printTotals.box_quantity) }}</span>
              <span class="print-summary-item"><em>本数</em> {{ formatPrintNumber(printTotals.units) }}</span>
            </div>
          </div>
        </div>

        <template v-for="(group, gIdx) in printDataGroupedByDate" :key="gIdx">
          <div class="print-date-section">
            <div class="print-date-heading">
              <span class="print-date-badge">{{ formatPrintDate(group.date) }}</span>
            </div>
            <div class="print-table-wrap">
              <table class="print-table">
                <thead>
                  <tr>
                    <th class="print-th">納入先名</th>
                    <th class="print-th">製品名</th>
                    <th class="print-th">製品種類</th>
                    <th class="print-th">箱種</th>
                    <th class="print-th print-th-num">検査済在庫</th>
                    <th class="print-th print-th-num">箱数</th>
                    <th class="print-th print-th-num">本数</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in group.rows" :key="`${gIdx}-${idx}`" class="print-tr">
                    <td class="print-td">{{ row.destination_name || '—' }}</td>
                    <td class="print-td">{{ row.product_name || '—' }}</td>
                    <td class="print-td">{{ row.product_type || '—' }}</td>
                    <td class="print-td">{{ row.box_type || '—' }}</td>
                    <td class="print-td print-td-num">{{ formatPrintInspectionInventory(row.inspection_inventory) }}</td>
                    <td class="print-td print-td-num">{{ row.box_quantity != null ? formatPrintNumber(row.box_quantity) : '—' }}</td>
                    <td class="print-td print-td-num">{{ formatPrintNumber(row.units) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { OfficeBuilding, MagicStick, Refresh, Setting, Printer } from '@element-plus/icons-vue'
import { getJSTToday } from '@/utils/dateFormat'
import request from '@/utils/request'
import { getWarehouseDailyShortagePrint } from '@/api/shipping/warehouseDailyStock'
import type { InventoryShortagePrintRow } from '@/api/database'

const { t } = useI18n()

interface ShippingWarehouseDailyRow {
  product_cd: string
  product_name: string
  product_type?: string
  destination_cd: string
  destination_name: string
  work_date: string
  weekday: string
  order_qty: number
  forecast_qty: number
  warehouse_carryover: number
  warehouse_actual: number
  warehouse_defect: number
  warehouse_disposal: number
  warehouse_hold: number
  warehouse_stock: number
}

const COLUMN_KEYS_ORDER = [
  'destination_name',
  'product_cd',
  'product_name',
  'product_type',
  'destination_cd',
  'work_date',
  'weekday',
  'order_qty',
  'forecast_qty',
  'warehouse_carryover',
  'warehouse_actual',
  'warehouse_defect',
  'warehouse_disposal',
  'warehouse_hold',
  'warehouse_stock',
] as const

const COLUMN_DEFAULT_VISIBLE = [
  'destination_name',
  'product_cd',
  'product_name',
  'product_type',
  'work_date',
  'weekday',
  'order_qty',
  'forecast_qty',
  'warehouse_actual',
  'warehouse_stock',
] as const

/** v4: 製品種類列を追加（products.product_type） */
const COLUMN_STORAGE_KEY = 'shippingWarehouseDaily.visibleColumns.v4'

function normalizeColumnKeys(selected: string[]): string[] {
  const order = COLUMN_KEYS_ORDER as readonly string[]
  const allowed = new Set(order)
  const unique = [...new Set(selected.filter((k) => allowed.has(k)))]
  return order.filter((k) => unique.includes(k))
}

function loadColumnKeysFromStorage(): string[] {
  if (typeof localStorage === 'undefined') return [...COLUMN_DEFAULT_VISIBLE]
  try {
    const raw = localStorage.getItem(COLUMN_STORAGE_KEY)
    if (!raw) return [...COLUMN_DEFAULT_VISIBLE]
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return [...COLUMN_DEFAULT_VISIBLE]
    const norm = normalizeColumnKeys(parsed as string[])
    if (norm.length === 0) return [...COLUMN_DEFAULT_VISIBLE]
    return norm
  } catch {
    return [...COLUMN_DEFAULT_VISIBLE]
  }
}

const visibleColumnList = ref<string[]>(loadColumnKeysFromStorage())

const columnPickerOptions = computed(() =>
  (COLUMN_KEYS_ORDER as readonly string[]).map((key) => ({
    key,
    label: t(`shipping.warehouseDaily.col_${key}`),
  })),
)

function colVisible(key: string): boolean {
  return visibleColumnList.value.includes(key)
}

watch(
  visibleColumnList,
  (val) => {
    const norm = normalizeColumnKeys(val)
    if (norm.length === 0) {
      ElMessage.warning(t('shipping.warehouseDaily.columnPickerNeedOne'))
      nextTick(() => {
        visibleColumnList.value = [...COLUMN_DEFAULT_VISIBLE]
      })
      return
    }
    const orderAligned = norm.length === val.length && norm.every((k, i) => val[i] === k)
    if (!orderAligned) {
      nextTick(() => {
        visibleColumnList.value = norm
      })
      return
    }
    try {
      localStorage.setItem(COLUMN_STORAGE_KEY, JSON.stringify(norm))
    } catch {
      /* ignore */
    }
  },
  { deep: true },
)

const PAGE_SIZE = 100

const _defaultDay = getJSTToday()
const queryDateRange = ref<string[] | null>([_defaultDay, _defaultDay])
const filterProductCd = ref<string>('')
/** true: products.product_type が「量産品」の行のみ（API で絞り込み） */
const massProductOnly = ref(false)
const productOptions = ref<{ product_cd: string; product_name: string }[]>([])
const tableData = ref<ShippingWarehouseDailyRow[]>([])
const currentPage = ref(1)
const totalCount = ref(0)
const pageSize = PAGE_SIZE
/** 製品名のみサーバー側で全件 ORDER BY（ページを跨いで一貫） */
const serverSortOrder = ref<'ascending' | 'descending'>('ascending')
const tableDefaultSort = computed(() => ({
  prop: 'product_name',
  order: serverSortOrder.value,
}))
const loading = ref(false)
const genLoading = ref(false)
const syncLoading = ref(false)
const printShortageLoading = ref(false)
const printContentRef = ref<HTMLElement | null>(null)
const printTableData = ref<InventoryShortagePrintRow[]>([])
const tableScrollRef = ref<HTMLElement | null>(null)
const tableBodyHeight = ref(320)
let tableResizeObserver: ResizeObserver | null = null

function formatQty(v: unknown): string {
  const n = Number(v)
  if (v === null || v === undefined || Number.isNaN(n)) return '—'
  if (n === 0) return ''
  return n.toLocaleString()
}

function isQtyNegative(v: unknown): boolean {
  const n = Number(v)
  if (v === null || v === undefined || Number.isNaN(n)) return false
  return n < 0
}

function addDaysToYmd(ymd: string, delta: number): string {
  const base = ymd || getJSTToday()
  const [y, m, d] = base.split('-').map(Number)
  const dt = new Date(Date.UTC(y, m - 1, d))
  dt.setUTCDate(dt.getUTCDate() + delta)
  const yy = dt.getUTCFullYear()
  const mm = String(dt.getUTCMonth() + 1).padStart(2, '0')
  const dd = String(dt.getUTCDate()).padStart(2, '0')
  return `${yy}-${mm}-${dd}`
}

function setRangeToday() {
  const t = getJSTToday()
  queryDateRange.value = [t, t]
}

/** 期間の開始・終了を同じ日数だけずらす（未選択時は当日1日を起点）。 */
function shiftDateRangeByDays(delta: number) {
  const r = queryDateRange.value
  let lo: string
  let hi: string
  if (!r || r.length !== 2 || !r[0] || !r[1]) {
    const t = getJSTToday()
    lo = hi = t
  } else {
    ;[lo, hi] = r[0] <= r[1] ? [r[0], r[1]] : [r[1], r[0]]
  }
  queryDateRange.value = [addDaysToYmd(lo, delta), addDaysToYmd(hi, delta)]
}

async function loadProductOptions() {
  try {
    const res: any = await request.get('/api/shipping/warehouse-daily/product-options')
    const raw = res?.data?.list ?? res?.list ?? []
    productOptions.value = Array.isArray(raw) ? raw : []
  } catch {
    productOptions.value = []
  }
}

async function fetchRows(resetPage = false) {
  const r = queryDateRange.value
  if (!r || r.length !== 2 || !r[0] || !r[1]) {
    tableData.value = []
    totalCount.value = 0
    return
  }
  if (resetPage) {
    currentPage.value = 1
  }
  const [df, dt] = r[0] <= r[1] ? [r[0], r[1]] : [r[1], r[0]]
  loading.value = true
  try {
    const params: Record<string, string | number | boolean> = {
      date_from: df,
      date_to: dt,
      page: currentPage.value,
      pageSize: PAGE_SIZE,
      sortOrder: serverSortOrder.value === 'descending' ? 'desc' : 'asc',
    }
    const pc = (filterProductCd.value || '').trim()
    if (pc) params.product_cd = pc
    if (massProductOnly.value) params.massProductOnly = true
    const res: any = await request.get('/api/shipping/warehouse-daily/rows', { params })
    const d = res?.data ?? {}
    const list = d.list ?? res?.list ?? []
    tableData.value = Array.isArray(list) ? list : []
    totalCount.value = Number(d.total ?? 0)
  } catch {
    tableData.value = []
    totalCount.value = 0
  } finally {
    loading.value = false
  }
}

function onPageChange(page: number) {
  currentPage.value = page
  void fetchRows(false)
}

function onTableSortChange(payload: { prop?: string; order?: string | null }) {
  if (payload.prop !== 'product_name') return
  if (!payload.order) {
    serverSortOrder.value = 'ascending'
  } else {
    serverSortOrder.value = payload.order === 'descending' ? 'descending' : 'ascending'
  }
  currentPage.value = 1
  void fetchRows(false)
}

function isPrintWeekday(dateStr: string): boolean {
  if (!dateStr || dateStr.length < 10) return false
  const d = new Date(`${dateStr}T00:00:00+09:00`)
  const day = d.getDay()
  return day >= 1 && day <= 5
}

function formatPrintNumber(val: number | null | undefined): string {
  if (val == null || (typeof val === 'number' && Number.isNaN(val))) return '-'
  return Number(val).toLocaleString()
}

/** 印刷「検査済在庫」：0・未設定は '—' */
function formatPrintInspectionInventory(val: number | null | undefined): string {
  if (val == null || (typeof val === 'number' && Number.isNaN(val))) return '—'
  if (Number(val) === 0) return '—'
  return Number(val).toLocaleString()
}

const printDataGroupedByDate = computed(() => {
  const list = printTableData.value
  if (!list.length) return []
  const map = new Map<string, InventoryShortagePrintRow[]>()
  for (const row of list) {
    const d = row.date || ''
    if (!map.has(d)) map.set(d, [])
    map.get(d)!.push(row)
  }
  const sorted = [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]))
  return sorted.map(([date, rows]) => ({ date, rows }))
})

const printPeriodFormatted = computed(() => {
  const list = printTableData.value
  const fmt = (s: string) => {
    if (!s || s.length < 10) return s
    const [y, m, d] = [s.slice(0, 4), s.slice(5, 7), s.slice(8, 10)]
    return `${y}年${m}月${d}日`
  }
  if (!list.length) return '—'
  const dates = [...new Set(list.map((row) => row.date).filter(Boolean))] as string[]
  if (dates.length === 0) return '—'
  dates.sort()
  return `${fmt(dates[0])} ～ ${fmt(dates[dates.length - 1])}（土日除く）`
})

const printTotals = computed(() => {
  const list = printTableData.value
  let boxSum = 0
  let unitsSum = 0
  for (const row of list) {
    if (row.box_quantity != null && typeof row.box_quantity === 'number') boxSum += row.box_quantity
    unitsSum += Number(row.units) || 0
  }
  return { box_quantity: boxSum, units: unitsSum }
})

function formatPrintDate(dateStr: string): string {
  if (!dateStr || dateStr.length < 10) return dateStr
  const y = dateStr.slice(0, 4)
  const m = dateStr.slice(5, 7)
  const d = dateStr.slice(8, 10)
  return `${y}年${m}月${d}日`
}

function executeShortagePrint(contentRef: HTMLElement | null) {
  if (!contentRef || !contentRef.innerHTML) {
    ElMessage.error('印刷内容の取得に失敗しました。')
    return
  }
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('ポップアップがブロックされました。ブラウザの設定を確認してください。')
    return
  }
  const printHtml = contentRef.innerHTML
  const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"], style'))
    .map((el) => el.outerHTML)
    .join('')
  printWindow.document.write(`
    <html>
      <head>
        <title>出荷不足数一覧</title>
        ${styles}
      </head>
      <body>
        <div class="print-container">${printHtml}</div>
      </body>
    </html>
  `)
  printWindow.document.close()
  printWindow.onload = () => {
    printWindow.focus()
    printWindow.print()
    printWindow.close()
  }
}

async function handleShortageIssuePrint() {
  const r = queryDateRange.value
  if (!r || r.length !== 2 || !r[0] || !r[1]) {
    ElMessage.warning(t('shipping.periodNotSelected'))
    return
  }
  const [startDate, endDate] = r[0] <= r[1] ? [r[0], r[1]] : [r[1], r[0]]
  printShortageLoading.value = true
  try {
    const res: any = await getWarehouseDailyShortagePrint({
      startDate,
      endDate,
      productCd: (filterProductCd.value || '').trim() || undefined,
    })
    const raw = res?.data ?? res
    const list = Array.isArray(raw) ? raw : raw?.data ?? []
    const weekdaysOnly = list.filter((row: InventoryShortagePrintRow) => isPrintWeekday(row.date || ''))
    printTableData.value = weekdaysOnly
    if (weekdaysOnly.length === 0) {
      ElMessage.warning(t('shipping.warehouseDaily.shortagePrintNoWeekdayData'))
      return
    }
    await nextTick()
    executeShortagePrint(printContentRef.value)
  } catch (e: any) {
    if (!e?.response) {
      ElMessage.error(t('shipping.warehouseDaily.shortagePrintNetworkError'))
    }
  } finally {
    printShortageLoading.value = false
  }
}

watch(
  [queryDateRange, filterProductCd, massProductOnly],
  () => {
    void fetchRows(true)
  },
  { deep: true, immediate: true },
)

async function handleSyncFromOrderDaily() {
  try {
    await ElMessageBox.confirm(
      t('shipping.warehouseDaily.syncFromOrderDailyConfirm'),
      t('shipping.warehouseDaily.syncFromOrderDaily'),
      {
        type: 'warning',
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        distinguishCancelAndClose: true,
      },
    )
  } catch {
    return
  }
  syncLoading.value = true
  try {
    const res: any = await request.post('/api/shipping/warehouse-daily/sync-from-order-daily', {}, { timeout: 120000 })
    const d = res?.data ?? {}
    ElMessage.success({
      message: t('shipping.warehouseDaily.syncFromOrderDailyDone', {
        o: d.order_daily_rows ?? d.rows_matched ?? 0,
        c: d.stock_carryover_rows ?? 0,
        a: d.stock_actual_rows ?? 0,
        de: d.stock_defect_rows ?? 0,
        di: d.stock_disposal_rows ?? 0,
        ho: d.stock_hold_rows ?? 0,
        w: d.warehouse_stock_roll_days ?? 0,
        sd: d.warehouse_stock_roll_start ?? '—',
      }),
      duration: 5000,
      showClose: true,
    })
    await fetchRows(true)
  } catch (e: any) {
    const msg =
      e?.response?.data?.detail ||
      e?.response?.data?.message ||
      t('shipping.warehouseDaily.syncFromOrderDailyFailed')
    ElMessage.error(typeof msg === 'string' ? msg : t('shipping.warehouseDaily.syncFromOrderDailyFailed'))
  } finally {
    syncLoading.value = false
  }
}

async function handleGenerateData() {
  try {
    await ElMessageBox.confirm(
      t('shipping.warehouseDaily.generateConfirm'),
      t('shipping.warehouseDaily.generateData'),
      {
        type: 'warning',
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        distinguishCancelAndClose: true,
      },
    )
  } catch {
    return
  }
  genLoading.value = true
  try {
    const res: any = await request.post(
      '/api/shipping/warehouse-daily/generate-data',
      {},
      { timeout: 300000 },
    )
    const n = res?.data?.inserted_or_updated ?? res?.inserted_or_updated ?? 0
    const samples: string[] = res?.data?.sample_lines ?? []
    ElMessage.success({
      message: t('shipping.warehouseDaily.generateDone').replace('{n}', String(n)),
      duration: 5000,
      showClose: true,
    })
    if (samples.length) {
      ElMessage.info({ message: samples.join(' / '), duration: 6000, showClose: true })
    }
    await fetchRows(true)
  } catch (e: any) {
    const msg =
      e?.response?.data?.detail ||
      e?.response?.data?.message ||
      t('shipping.warehouseDaily.generateFailed')
    ElMessage.error(typeof msg === 'string' ? msg : t('shipping.warehouseDaily.generateFailed'))
  } finally {
    genLoading.value = false
  }
}

function measureTableBodyHeight() {
  requestAnimationFrame(() => {
    nextTick(() => {
      const el = tableScrollRef.value
      if (!el) return
      const h = Math.floor(el.getBoundingClientRect().height)
      if (h >= 64) {
        tableBodyHeight.value = Math.max(120, h)
      }
    })
  })
}

onMounted(() => {
  void loadProductOptions()
  nextTick(() => {
    if (typeof ResizeObserver !== 'undefined' && tableScrollRef.value) {
      tableResizeObserver = new ResizeObserver(() => measureTableBodyHeight())
      tableResizeObserver.observe(tableScrollRef.value)
    }
    window.addEventListener('resize', measureTableBodyHeight)
    measureTableBodyHeight()
    requestAnimationFrame(() => measureTableBodyHeight())
  })
})

onUnmounted(() => {
  tableResizeObserver?.disconnect()
  tableResizeObserver = null
  window.removeEventListener('resize', measureTableBodyHeight)
})

watch(loading, (v) => {
  if (!v) measureTableBodyHeight()
})
</script>

<style scoped>
.wh-page {
  --wh-glass: rgba(255, 255, 255, 0.11);
  --wh-glass-border: rgba(255, 255, 255, 0.18);
  --wh-shadow: 0 8px 32px rgba(15, 23, 42, 0.14);
  --wh-text: #0f172a;
  --wh-text-soft: #64748b;
  --wh-accent: #6366f1;
  --wh-accent2: #3b82f6;
  --wh-surface: rgba(255, 255, 255, 0.98);
  position: relative;
  min-height: calc(100vh - 12px);
  padding: 10px 12px 14px;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* ---------- 背景 ---------- */
.wh-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: linear-gradient(155deg, #0f172a 0%, #1e293b 38%, #312e81 72%, #1d4ed8 100%);
}

.wh-bg__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(72px);
  opacity: 0.45;
  animation: whOrb 22s ease-in-out infinite;
}

.wh-bg__orb--1 {
  width: 420px;
  height: 420px;
  top: -140px;
  right: -80px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.55) 0%, transparent 70%);
}

.wh-bg__orb--2 {
  width: 360px;
  height: 360px;
  bottom: -100px;
  left: -60px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.45) 0%, transparent 72%);
  animation-delay: -8s;
}

.wh-bg__orb--3 {
  width: 260px;
  height: 260px;
  top: 42%;
  left: 28%;
  background: radial-gradient(circle, rgba(34, 211, 238, 0.22) 0%, transparent 70%);
  animation-delay: -14s;
}

@keyframes whOrb {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(16px, -20px) scale(1.06);
  }
}

.wh-bg__noise {
  position: absolute;
  inset: 0;
  opacity: 0.35;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E");
}

/* ---------- 玻璃卡片 ---------- */
.glass {
  position: relative;
  z-index: 1;
  background: var(--wh-glass);
  backdrop-filter: blur(20px) saturate(1.35);
  -webkit-backdrop-filter: blur(20px) saturate(1.35);
  border: 1px solid var(--wh-glass-border);
  border-radius: 14px;
  box-shadow: var(--wh-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

.animate-in {
  opacity: 0;
  transform: translateY(8px);
  animation: whFadeUp 0.42s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

@keyframes whFadeUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ---------- 顶部：标题 + 筛选（单卡片） ---------- */
.wh-hero__icon-wrap {
  position: relative;
  flex-shrink: 0;
}

.wh-hero__icon {
  position: relative;
  z-index: 1;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(140deg, #6366f1 0%, #4f46e5 45%, #2563eb 100%);
  box-shadow: 0 6px 18px rgba(79, 70, 229, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.wh-hero__icon-glow {
  position: absolute;
  inset: -4px;
  border-radius: 16px;
  background: linear-gradient(135deg, #a5b4fc, #38bdf8);
  opacity: 0.32;
  filter: blur(12px);
  z-index: 0;
}

.wh-top-card {
  padding: 0;
  margin-bottom: 0;
  overflow: hidden;
  flex-shrink: 0;
}

.wh-top-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px 14px;
  flex-wrap: wrap;
  padding: 12px 14px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.wh-top-card__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.wh-top-card__titles {
  min-width: 0;
}

.wh-top-card__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.18);
}

.wh-top-card__desc {
  margin: 4px 0 0;
  font-size: 0.75rem;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.72);
  max-width: 42rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.wh-top-card__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.wh-top-card__filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 12px;
  padding: 8px 12px 10px;
  background: rgba(0, 0, 0, 0.12);
}

.wh-toolbar__end {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.wh-btn-columns-pill {
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border-radius: 10px !important;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95) !important;
  background: rgba(255, 255, 255, 0.12) !important;
  border: 1px solid rgba(255, 255, 255, 0.22) !important;
  backdrop-filter: blur(8px);
  padding: 6px 12px !important;
}

.wh-btn-columns-pill:hover {
  background: rgba(255, 255, 255, 0.18) !important;
  border-color: rgba(255, 255, 255, 0.3) !important;
}

.wh-col-picker-icon {
  margin-right: 4px;
  vertical-align: middle;
}

.wh-col-picker__hint {
  margin: 0 0 10px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

.wh-col-picker__group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: min(52vh, 420px);
  overflow-y: auto;
}

.wh-col-picker__item {
  margin-right: 0;
  height: auto;
}

.wh-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 12px;
}

.wh-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.wh-form-item--compact :deep(.el-form-item__label) {
  padding-bottom: 0;
}

.wh-form :deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.82);
  font-weight: 600;
  font-size: 12px;
}

.wh-range-with-nudges {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
}

.wh-range-nudges {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0;
  padding: 2px 4px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.wh-daterange {
  width: 240px;
}

.wh-product-select {
  width: min(280px, 88vw);
}

.wh-form :deep(.el-switch) {
  --el-switch-on-color: #6366f1;
  --el-switch-off-color: rgba(148, 163, 184, 0.55);
}

.wh-form :deep(.el-input__wrapper),
.wh-form :deep(.el-date-editor .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.96);
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.wh-shortcut {
  font-weight: 600;
  padding: 4px 6px !important;
}

.wh-btn-gen--hero {
  flex-shrink: 0;
  border-radius: 10px;
  padding: 7px 14px !important;
  font-weight: 600;
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.32);
}

.wh-btn-gen__icon {
  margin-right: 4px;
  vertical-align: middle;
}

.wh-btn-sync--hero {
  border-radius: 10px;
  padding: 7px 14px !important;
  font-weight: 600;
  box-shadow: 0 4px 14px rgba(245, 158, 11, 0.32);
}

.wh-btn-sync__icon {
  margin-right: 4px;
  vertical-align: middle;
}

/* ---------- Table section ---------- */
.wh-table-section {
  padding: 0;
  overflow: hidden;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.wh-table-section__inner {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 8px 10px 6px;
  background: var(--wh-surface);
  border-radius: 12px;
  margin: 1px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
}

.wh-table-scroll {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.wh-pagination-wrap {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  flex-shrink: 0;
  padding: 6px 4px 2px;
  gap: 6px;
}

.wh-pagination-wrap :deep(.el-pagination) {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.wh-table {
  width: 100%;
  border-radius: 10px;
  overflow: hidden;
  --el-table-border-color: rgba(15, 23, 42, 0.06);
  --el-table-header-bg-color: #f1f5f9;
}

.wh-table :deep(.el-table__header-wrapper th) {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
  color: #475569;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 0.02em;
  text-transform: none;
}

.wh-table :deep(.el-table__row:hover > td) {
  background: rgba(99, 102, 241, 0.05) !important;
}

.wh-table :deep(.el-table__cell) {
  padding: 5px 0;
  font-size: 12px;
}

.wh-num {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: var(--wh-text);
}

.wh-num--accent {
  color: #2563eb;
}

.wh-num--warn {
  color: #c2410c;
}

.wh-num--muted {
  color: var(--wh-text-soft);
}

.wh-num--negative {
  color: #dc2626 !important;
}

.wh-empty {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.65) 0%, rgba(248, 250, 252, 0.92) 100%);
  border-radius: 12px;
}

.wh-empty :deep(.el-empty__description) {
  color: var(--wh-text-soft);
}

.wh-btn-print--hero {
  flex-shrink: 0;
  border-radius: 10px;
  padding: 7px 14px !important;
  font-weight: 600;
  box-shadow: 0 4px 14px rgba(100, 116, 139, 0.32);
}

.wh-btn-print__icon {
  margin-right: 4px;
  vertical-align: middle;
}

/* ---------- 不足数発行：印刷用（画面上は非表示、在庫不足画面と同様） ---------- */
.print-content-hidden {
  position: absolute;
  left: -9999px;
  top: 0;
  width: 820px;
  max-width: 100%;
  overflow: hidden;
  font-family: 'Helvetica Neue', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', sans-serif;
  color: #000;
  background: #fff;
  box-sizing: border-box;
}

.print-body {
  padding: 14px 20px 12px;
  font-size: 12px;
  min-height: 100%;
}

.print-header {
  text-align: center;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
  position: relative;
}

.print-header::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #6366f1, transparent);
  border-radius: 1px;
}

.print-title-wrap {
  position: relative;
  margin-bottom: 8px;
}

.print-title-accent {
  display: block;
  width: 24px;
  height: 3px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 2px;
  margin: 0 auto 8px;
}

.print-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 0.06em;
  color: #000;
  line-height: 1.25;
}

.print-subtitle {
  font-size: 10px;
  font-weight: 600;
  margin: 3px 0 0 0;
  letter-spacing: 0.1em;
  color: #000;
  text-transform: uppercase;
}

.print-header-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.print-period-block {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.print-period-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #6366f1;
  flex-shrink: 0;
}

.print-period-label {
  font-size: 10px;
  font-weight: 600;
  color: #000;
  letter-spacing: 0.06em;
}

.print-period-value {
  font-size: 12px;
  font-weight: 600;
  color: #000;
}

.print-date-section {
  margin-bottom: 12px;
  page-break-inside: avoid;
  break-inside: avoid;
}

.print-date-heading {
  margin: 0 0 6px 0;
}

.print-date-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  color: #4338ca;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border: 1px solid #c7d2fe;
  border-radius: 6px;
  letter-spacing: 0.02em;
}

.print-table-wrap {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.print-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.print-th {
  padding: 6px 10px;
  text-align: left;
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #fff;
  background: linear-gradient(180deg, #475569 0%, #334155 100%);
  border: none;
  border-bottom: 1px solid #334155;
}

.print-th-num {
  text-align: right;
  min-width: 64px;
}

.print-tr:nth-child(even) {
  background: #fafbfc;
}

.print-td {
  padding: 5px 10px;
  border: 1px solid #e2e8f0;
  border-top: none;
  color: #000;
}

.print-td-num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 500;
  color: #000;
}

.print-summary-box {
  display: inline-flex;
  align-items: center;
  gap: 16px;
  padding: 6px 14px;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.print-summary-label {
  font-size: 12px;
  font-weight: 700;
  color: #000;
  margin-right: 4px;
}

.print-summary-item {
  font-size: 11px;
  color: #000;
}

.print-summary-item em {
  font-style: normal;
  font-weight: 600;
  color: #000;
  margin-right: 4px;
}

@media print {
  .print-content-hidden {
    position: static;
    width: auto;
    max-width: none;
    overflow: visible;
    left: 0;
  }

  .print-body {
    padding: 12px 16px 10px;
  }

  .print-title {
    font-size: 20px;
  }

  .print-date-section {
    page-break-inside: avoid;
    break-inside: avoid;
  }

  .print-title-accent,
  .print-period-block,
  .print-date-badge,
  .print-summary-box {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .print-table-wrap {
    box-shadow: none;
  }
}

@media (max-width: 768px) {
  .wh-page {
    padding: 8px 8px 12px;
  }

  .wh-top-card__head {
    flex-direction: column;
    align-items: stretch;
  }

  .wh-top-card__actions {
    width: 100%;
    justify-content: stretch;
  }

  .wh-top-card__actions .el-button {
    flex: 1;
    justify-content: center;
  }

  .wh-top-card__filters {
    flex-direction: column;
    align-items: stretch;
  }

  .wh-toolbar__end {
    justify-content: stretch;
  }

  .wh-btn-columns-pill {
    width: 100%;
    justify-content: center;
  }

  .wh-daterange {
    width: 100%;
  }

  .wh-product-select {
    width: 100%;
  }
}
</style>
