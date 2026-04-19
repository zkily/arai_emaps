<template>
  <div class="order-daily-list">
    <div class="page-hero">
      <div class="page-hero-top">
        <div class="hero-title-block">
          <h1 class="toolbar-title">日受注管理</h1>
          <p v-if="lastFetchedText" class="hero-meta">更新: {{ lastFetchedText }}</p>
        </div>
        <div class="hero-actions">
          <el-button class="tb-btn tb-btn-refresh" :loading="loading" @click="refreshAll">
            <el-icon><Refresh /></el-icon>
            <span class="tb-label">更新</span>
          </el-button>
          <el-button class="tb-btn tb-btn-export" :disabled="!fullList.length" @click="exportCsv">
            <el-icon><Download /></el-icon>
            <span class="tb-label">CSV</span>
          </el-button>
          <el-button class="tb-btn tb-btn-create" @click="openDialog()">
            <el-icon><Plus /></el-icon>
            <span class="tb-label">新規登録</span>
          </el-button>
        </div>
      </div>
      <div class="date-quick-row">
        <span class="dq-label">期間</span>
        <el-button-group class="date-quick-btns">
          <el-button size="small" @click="applyQuickRange('today')">今日</el-button>
          <el-button size="small" @click="applyQuickRange('week')">今週</el-button>
          <el-button size="small" @click="applyQuickRange('month')">今月</el-button>
          <el-button size="small" @click="applyQuickRange('lastMonth')">先月</el-button>
        </el-button-group>
      </div>
      <div class="filter-inline">
        <div class="fi-group">
          <el-icon class="fi-icon"><Calendar /></el-icon>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="～"
            start-placeholder="開始日"
            end-placeholder="終了日"
            value-format="YYYY-MM-DD"
            clearable
            class="fi-date-range"
          />
        </div>
        <div class="fi-sep"></div>
        <div class="fi-group">
          <el-select v-model="filters.destination_cd" placeholder="納入先" clearable filterable class="fi-dest" popper-class="destination-select-popper">
            <el-option v-for="d in destinationOptions" :key="d.cd" :label="`${d.cd} | ${d.name}`" :value="d.cd" />
          </el-select>
        </div>
        <div class="fi-group">
          <el-select v-model="filters.keyword" placeholder="製品" clearable filterable class="fi-product">
            <el-option
              v-for="p in productOptions"
              :key="p.cd"
              :value="p.cd"
              :label="`${p.cd} | ${p.name} | ${p.destination_name || p.destination_cd || '-'}`"
            >
              <div class="product-option-row">
                <span class="product-option-cd">{{ p.cd }}</span>
                <span class="product-option-name">{{ p.name }}</span>
                <span class="product-option-dest">{{ p.destination_name || p.destination_cd || '－' }}</span>
              </div>
            </el-option>
          </el-select>
        </div>
      </div>
    </div>

    <div class="kpi-strip">
      <div class="kpi-card kpi-count">
        <span class="kpi-label">件数</span>
        <span class="kpi-value">{{ summaryStats.count }}</span>
      </div>
      <div class="kpi-card kpi-units">
        <span class="kpi-label">確定本数</span>
        <span class="kpi-value">{{ formatNum(summaryStats.confirmedUnits) }}</span>
      </div>
      <div class="kpi-card kpi-boxes">
        <span class="kpi-label">確定箱数</span>
        <span class="kpi-value">{{ formatNum(summaryStats.confirmedBoxes) }}</span>
      </div>
      <div class="kpi-card kpi-forecast">
        <span class="kpi-label">内示本数</span>
        <span class="kpi-value">{{ formatNum(summaryStats.forecastUnits) }}</span>
      </div>
    </div>

    <div class="table-section">
      <div class="table-section-head">
        <span class="table-section-title">受注一覧</span>
        <span class="table-section-hint">クリックで列ソート</span>
      </div>
      <el-table
        :data="list"
        v-loading="loading"
        stripe
        border
        size="small"
        class="data-table"
        :max-height="tableMaxHeight"
        :default-sort="{ prop: 'date', order: 'ascending' }"
      >
        <el-table-column prop="date" label="日付" width="110" sortable />
        <el-table-column prop="weekday" label="曜日" width="70" align="center" />
        <el-table-column prop="monthly_order_id" label="月受注ID" width="160" show-overflow-tooltip />
        <el-table-column prop="destination_cd" label="納入先CD" width="100" />
        <el-table-column prop="destination_name" label="納入先名" min-width="120" show-overflow-tooltip />
        <el-table-column prop="product_cd" label="製品CD" width="100" />
        <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
        <el-table-column prop="product_type" label="種別" width="90" />
        <el-table-column prop="forecast_units" label="内示本数" width="90" align="right" />
        <el-table-column prop="confirmed_boxes" label="確定箱数" width="90" align="right" />
        <el-table-column prop="confirmed_units" label="確定本数" width="90" align="right" />
        <el-table-column label="ステータス" width="108" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small" effect="light" class="status-tag">
              {{ row.status || '—' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="delivery_date" label="納入日" width="110" />
        <el-table-column label="操作" width="128" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" class="row-act-btn row-act-edit" link @click="openDialog(row)">編集</el-button>
            <el-button type="danger" size="small" class="row-act-btn row-act-del" link @click="handleDelete(row)">削除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <span class="page-range-text">{{ pageRangeText }}</span>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="pagination.total"
          layout="sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
          background
          class="pagination-el"
        />
      </div>
    </div>

    <el-dialog 
      v-model="dialogVisible" 
      width="540px" 
      destroy-on-close 
      @close="resetForm"
      class="daily-order-dialog compact-dialog"
      :show-close="false"
    >
      <template #header>
        <div class="dialog-header-custom">
          <div class="dialog-header-left">
            <span class="dialog-header-add-btn" title="新規追加">
              <el-icon><Plus /></el-icon>
            </span>
            <span class="dialog-header-title">{{ editId ? '日別受注編集' : '新規受注追加(試作品・補給品等)' }}</span>
          </div>
          <el-icon class="dialog-header-close" @click="dialogVisible = false"><Close /></el-icon>
        </div>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="modern-form compact-form" size="default">
        <!-- 日付情報セクション -->
        <div class="form-section compact-section">
          <div class="section-header compact-header">
            <el-icon class="section-icon"><Calendar /></el-icon>
            <span class="section-title">日付情報</span>
          </div>
          <div class="section-content compact-content">
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="出荷日" prop="date" required class="compact-item">
                  <el-date-picker 
                    v-model="form.date" 
                    type="date" 
                    placeholder="選択" 
                    value-format="YYYY-MM-DD" 
                    style="width: 100%" 
                    size="default"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="納入日" prop="delivery_date" required class="compact-item">
                  <el-date-picker 
                    v-model="form.delivery_date" 
                    type="date" 
                    placeholder="選択" 
                    value-format="YYYY-MM-DD" 
                    style="width: 100%" 
                    clearable 
                    size="default"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>

        <!-- 基本情報セクション -->
        <div class="form-section compact-section">
          <div class="section-header compact-header">
            <el-icon class="section-icon"><Document /></el-icon>
            <span class="section-title">基本情報</span>
          </div>
          <div class="section-content compact-content">
            <el-form-item label="納入先" prop="destination_cd" required class="compact-item">
              <el-select 
                v-model="form.destination_cd" 
                placeholder="納入先を選択" 
                filterable 
                style="width: 100%" 
                popper-class="destination-select-popper"
                @change="onDestinationChange"
                size="default"
              >
                <el-option 
                  v-for="d in destinationOptions" 
                  :key="d.cd" 
                  :label="`${d.cd} | ${d.name}`" 
                  :value="d.cd" 
                />
              </el-select>
            </el-form-item>
            <el-form-item label="製品" prop="product_cd" required class="compact-item">
              <el-select 
                v-model="form.product_cd" 
                placeholder="製品を選択" 
                filterable 
                style="width: 100%" 
                @change="onProductChange"
                size="default"
              >
                <el-option
                  v-for="p in productOptions"
                  :key="p.cd"
                  :value="p.cd"
                  :label="`${p.cd} | ${p.name}`"
                >
                  <div class="product-option-compact">
                    <span class="opt-cd">{{ p.cd }}</span>
                    <span class="opt-name">{{ p.name }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="製品タイプ" prop="product_type" class="compact-item">
              <el-select v-model="form.product_type" placeholder="製品タイプを選択" style="width: 100%" size="default">
                <el-option label="量産品" value="量産品" />
                <el-option label="試作品" value="試作品" />
                <el-option label="別注品" value="別注品" />
                <el-option label="補給品" value="補給品" />
                <el-option label="サンプル品" value="サンプル品" />
                <el-option label="代替品" value="代替品" />
                <el-option label="返却品" value="返却品" />
                <el-option label="その他" value="その他" />
              </el-select>
            </el-form-item>
          </div>
        </div>

        <!-- 数量情報セクション -->
        <div class="form-section compact-section">
          <div class="section-header compact-header">
            <el-icon class="section-icon"><Box /></el-icon>
            <span class="section-title">数量情報</span>
          </div>
          <div class="section-content compact-content">
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="入数" prop="unit_per_box" class="compact-item">
                  <el-input-number 
                    v-model="form.unit_per_box" 
                    :min="0" 
                    placeholder="入数を入力"
                    style="width: 100%" 
                    @change="calculateConfirmedUnits"
                    size="default"
                    :controls="false"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="箱数" prop="confirmed_boxes" class="compact-item">
                  <el-input-number 
                    v-model="form.confirmed_boxes" 
                    :min="0" 
                    placeholder="箱数を入力"
                    style="width: 100%" 
                    @change="calculateConfirmedUnits"
                    size="default"
                    :controls="false"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="確定本数" prop="confirmed_units" class="compact-item calculated-row">
              <el-input 
                :model-value="confirmedUnitsDisplay" 
                placeholder="自動計算" 
                readonly
                class="calculated-field"
                size="default"
              >
                <template #suffix>
                  <span class="unit-suffix"> (本)</span>
                </template>
              </el-input>
            </el-form-item>
            <div class="info-tip compact-tip">
              <el-icon><InfoFilled /></el-icon>
              <span>確定本数は入数×確定箱数で自動計算されます</span>
            </div>
          </div>
        </div>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer-compact">
          <el-button @click="dialogVisible = false" class="btn-cancel" size="default">
            <el-icon><Close /></el-icon>
            <span>キャンセル</span>
          </el-button>
          <el-button type="primary" :loading="saving" @click="submitForm" class="btn-save" size="default">
            <el-icon><Check /></el-icon>
            <span>保存</span>
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Calendar, Plus, Document, Box, InfoFilled, Close, Check, Refresh, Download } from '@element-plus/icons-vue'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import { getProductList } from '@/api/master/productMaster'
import {
  fetchOrderDailyList,
  updateOrderDaily,
  deleteOrderDaily,
  checkMonthlyOrderExists,
  addMonthlyOrder,
  addOrderDaily,
  type OrderDailyItem,
  type OrderDailyCreate,
  type OrderDailyFilters,
} from '@/api/erp/orderDaily'

// ========== 一覧用 ==========
const loading = ref(false)
const list = ref<OrderDailyItem[]>([])
const destinationOptions = ref<{ cd: string; name: string }[]>([])

interface ProductOption {
  cd: string
  name: string
  product_type?: string
  unit_per_box?: number
  product_alias?: string
  destination_cd?: string
  destination_name?: string
}
const productOptions = ref<ProductOption[]>([])
/** 全製品（納入先変更時にフィルタする元データ） */
const allProductOptions = ref<ProductOption[]>([])

const filters = reactive<OrderDailyFilters>({})

// ========== 日本時区ユーティリティ ==========
function getJapanDate(): Date {
  return new Date(new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' }))
}

const WEEKDAY_MAP = ['日', '月', '火', '水', '木', '金', '土']

function getTodayRange(): [string, string] {
  const d = getJapanDate()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return [`${y}-${m}-${day}`, `${y}-${m}-${day}`]
}
const dateRange = ref<[string, string] | null>(getTodayRange())

/** フィルタ後の全件（KPI・CSV 用） */
const fullList = ref<OrderDailyItem[]>([])
const lastFetchedAt = ref<Date | null>(null)

const lastFetchedText = computed(() => {
  if (!lastFetchedAt.value) return ''
  return lastFetchedAt.value.toLocaleString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
})

const summaryStats = computed(() => {
  const rows = fullList.value
  let confirmedUnits = 0
  let confirmedBoxes = 0
  let forecastUnits = 0
  for (const r of rows) {
    confirmedUnits += Number(r.confirmed_units) || 0
    confirmedBoxes += Number(r.confirmed_boxes) || 0
    forecastUnits += Number(r.forecast_units) || 0
  }
  return { count: rows.length, confirmedUnits, confirmedBoxes, forecastUnits }
})

function formatNum(n: number): string {
  return n.toLocaleString('ja-JP')
}

const pageRangeText = computed(() => {
  const total = pagination.total
  if (total === 0) return '表示 0件'
  const start = (pagination.page - 1) * pagination.pageSize + 1
  const end = Math.min(pagination.page * pagination.pageSize, total)
  return `表示 ${start}〜${end}件 / 全${total.toLocaleString('ja-JP')}件`
})

function formatYmdFromDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** 今日・今週・今月・先月（getJapanDate 基準） */
function applyQuickRange(kind: 'today' | 'week' | 'month' | 'lastMonth') {
  const d = getJapanDate()
  if (kind === 'today') {
    dateRange.value = getTodayRange()
    return
  }
  if (kind === 'week') {
    const w = d.getDay()
    const mondayOffset = w === 0 ? -6 : 1 - w
    const start = new Date(d.getFullYear(), d.getMonth(), d.getDate() + mondayOffset)
    const end = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 6)
    dateRange.value = [formatYmdFromDate(start), formatYmdFromDate(end)]
    return
  }
  if (kind === 'month') {
    const y = d.getFullYear()
    const m = d.getMonth()
    const start = new Date(y, m, 1)
    const end = new Date(y, m + 1, 0)
    dateRange.value = [formatYmdFromDate(start), formatYmdFromDate(end)]
    return
  }
  const y = d.getFullYear()
  const m = d.getMonth()
  const start = new Date(y, m - 1, 1)
  const end = new Date(y, m, 0)
  dateRange.value = [formatYmdFromDate(start), formatYmdFromDate(end)]
}

function statusTagType(status: string | null | undefined): 'success' | 'warning' | 'info' | 'danger' {
  const s = status || ''
  if (/取消|キャンセル|中止/.test(s)) return 'danger'
  if (/未出荷|保留|待ち/.test(s)) return 'warning'
  if (/出荷済|完了/.test(s)) return 'success'
  if (/出荷/.test(s)) return 'success'
  return 'info'
}

function escapeCsvCell(v: unknown): string {
  const s = v == null ? '' : String(v)
  if (/[",\r\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`
  return s
}

function exportCsv() {
  const rows = fullList.value
  if (!rows.length) {
    ElMessage.warning('出力するデータがありません')
    return
  }
  const headers = [
    '日付',
    '曜日',
    '月受注ID',
    '納入先CD',
    '納入先名',
    '製品CD',
    '製品名',
    '種別',
    '内示本数',
    '確定箱数',
    '確定本数',
    'ステータス',
    '納入日',
  ]
  const lines: string[] = [headers.map(escapeCsvCell).join(',')]
  for (const r of rows) {
    lines.push(
      [
        r.date,
        r.weekday ?? '',
        r.monthly_order_id ?? '',
        r.destination_cd,
        r.destination_name ?? '',
        r.product_cd,
        r.product_name ?? '',
        r.product_type ?? '',
        r.forecast_units,
        r.confirmed_boxes,
        r.confirmed_units,
        r.status ?? '',
        r.delivery_date ?? '',
      ]
        .map(escapeCsvCell)
        .join(',')
    )
  }
  const stamp = formatYmdFromDate(getJapanDate()).replace(/-/g, '')
  const blob = new Blob([`\ufeff${lines.join('\r\n')}`], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `order_daily_${stamp}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('CSVをダウンロードしました')
}

const tableMaxHeight = ref(480)
function updateTableMaxHeight() {
  /* ヘッダー・KPI・余白を差し引き、一覧を縦に最大化 */
  tableMaxHeight.value = Math.max(240, window.innerHeight - 296)
}

// ========== ページング ==========
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

// ========== typeSuffix 映射 ==========
const TYPE_SUFFIX_MAP: Record<string, string> = {
  '量産品': '0',
  '試作品': '1',
  '別注品': '2',
  '補給品': '3',
  'サンプル品': '4',
  '代替品': '5',
  '返却品': '6',
  'その他': '7',
}

function getTypeSuffix(productType: string): string {
  return TYPE_SUFFIX_MAP[productType] || '0'
}

// ========== データ読込 ==========
async function loadOptions() {
  try {
    const [d, pr] = await Promise.all([
      getDestinationOptions(),
      getProductList({ pageSize: 9999 }),
    ])
    destinationOptions.value = d.map((x) => ({ cd: x.cd, name: x.name }))
    const destMap: Record<string, string> = {}
    destinationOptions.value.forEach((x) => { destMap[x.cd] = x.name })
    const rawList = pr?.data?.list ?? pr?.list ?? []
    allProductOptions.value = rawList
      .map((p: any) => ({
        cd: p.product_cd,
        name: p.product_name || p.product_cd,
        product_type: p.product_type || '量産品',
        unit_per_box: p.unit_per_box ?? 0,
        product_alias: p.product_alias || '',
        destination_cd: p.destination_cd,
        destination_name: p.destination_cd ? (destMap[p.destination_cd] || p.destination_cd) : undefined,
      }))
      .sort((a: ProductOption, b: ProductOption) => (a.name || '').localeCompare(b.name || '', 'ja'))
    productOptions.value = [...allProductOptions.value]
  } catch {
    destinationOptions.value = []
    allProductOptions.value = []
    productOptions.value = []
  }
}

function applyPagination() {
  const allData = fullList.value
  pagination.total = allData.length
  const maxPage = Math.max(1, Math.ceil(allData.length / pagination.pageSize) || 1)
  if (pagination.page > maxPage) pagination.page = maxPage
  const start = (pagination.page - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  list.value = allData.slice(start, end)
}

async function loadList() {
  loading.value = true
  try {
    const params: OrderDailyFilters = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.destination_cd) params.destination_cd = filters.destination_cd
    const allData = await fetchOrderDailyList(params)
    fullList.value = allData
    lastFetchedAt.value = new Date()
    applyPagination()
  } catch {
    fullList.value = []
    list.value = []
    pagination.total = 0
    ElMessage.error('一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

async function refreshAll() {
  await loadOptions()
  await loadList()
}

function handlePageChange(page: number) {
  pagination.page = page
  applyPagination()
}

function handleSizeChange(size: number) {
  pagination.pageSize = size
  pagination.page = 1
  applyPagination()
}

watch(
  () => [dateRange.value, filters.keyword, filters.destination_cd],
  () => {
    pagination.page = 1
    loadList()
  },
  { deep: true }
)

// ========== ダイアログ ==========
const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const saving = ref(false)
const editId = ref<number | null>(null)

// 日付から分解した年・月・日
const formYear = ref('')
const formMonth = ref('')
const formDay = ref('')

const form = reactive<OrderDailyCreate & { destination_name?: string; product_name?: string }>({
  monthly_order_id: '',
  destination_cd: '',
  destination_name: '',
  date: '',
  weekday: '',
  product_cd: '',
  product_name: '',
  product_alias: '',
  product_type: '量産品',
  forecast_units: 0,
  confirmed_boxes: 0,
  confirmed_units: 0,
  unit_per_box: 0,
  status: '未出荷',
  remarks: '',
  delivery_date: '',
})

const rules: FormRules = {
  date: [{ required: true, message: '出荷日を入力してください', trigger: 'change' }],
  delivery_date: [{ required: true, message: '納入日を入力してください', trigger: 'change' }],
  destination_cd: [{ required: true, message: '納入先を選択してください', trigger: 'change' }],
  product_cd: [{ required: true, message: '製品を選択してください', trigger: 'change' }],
}

// ========== 日付変更時に year/month/day/weekday を自動設定 ==========
watch(() => form.date, (newDate) => {
  if (!newDate) {
    formYear.value = ''
    formMonth.value = ''
    formDay.value = ''
    form.weekday = ''
    return
  }
  const parts = newDate.split('-')
  formYear.value = parts[0] || ''
  formMonth.value = parts[1] || ''
  formDay.value = parts[2] || ''
  // 曜日を自動設定
  const d = new Date(newDate)
  if (!isNaN(d.getTime())) {
    form.weekday = WEEKDAY_MAP[d.getDay()] || ''
  }
  // 納入日が未設定なら出荷日と同じにする
  if (!form.delivery_date) {
    form.delivery_date = newDate
  }
})

// ========== 納入先変更 → 製品クリア＆製品リストをフィルタ ==========
function onDestinationChange(cd: string) {
  const d = destinationOptions.value.find((x) => x.cd === cd)
  if (d) form.destination_name = d.name

  // 製品をクリア
  form.product_cd = ''
  form.product_name = ''
  form.product_alias = ''
  form.product_type = '量産品'
  form.unit_per_box = 0
  form.confirmed_units = 0

  // 該当納入先の製品を優先表示（全製品も含む）
  if (cd) {
    const filtered = allProductOptions.value.filter((p) => p.destination_cd === cd)
    // 該当納入先の製品があればそれを優先、無ければ全製品
    productOptions.value = filtered.length > 0 ? filtered : [...allProductOptions.value]
  } else {
    productOptions.value = [...allProductOptions.value]
  }
}

// ========== 製品変更 → product_type, unit_per_box, product_name を帯出 ==========
function onProductChange(cd: string) {
  const p = productOptions.value.find((x) => x.cd === cd)
    || allProductOptions.value.find((x) => x.cd === cd)
  if (p) {
    form.product_name = p.name
    form.product_alias = p.product_alias || ''
    form.product_type = p.product_type || '量産品'
    form.unit_per_box = p.unit_per_box ?? 0
    // 本数を再計算
    calculateConfirmedUnits()
  }
}

// ========== 確定本数の自動計算 ==========
const confirmedUnitsDisplay = computed(() => {
  const units = (form.unit_per_box || 0) * (form.confirmed_boxes || 0)
  return units > 0 ? `${units}` : ''
})

function calculateConfirmedUnits() {
  form.confirmed_units = (form.unit_per_box || 0) * (form.confirmed_boxes || 0)
}

// ========== ダイアログ開閉 ==========
function openDialog(row?: OrderDailyItem) {
  editId.value = row?.id ?? null
  if (row) {
    form.monthly_order_id = row.monthly_order_id ?? ''
    form.destination_cd = row.destination_cd
    form.destination_name = row.destination_name ?? ''
    form.date = row.date
    form.weekday = row.weekday ?? ''
    form.product_cd = row.product_cd
    form.product_name = row.product_name ?? ''
    form.product_alias = row.product_alias ?? ''
    form.product_type = row.product_type ?? '量産品'
    form.forecast_units = row.forecast_units ?? 0
    form.confirmed_boxes = row.confirmed_boxes ?? 0
    form.confirmed_units = row.confirmed_units ?? 0
    form.unit_per_box = row.unit_per_box ?? 0
    form.status = row.status ?? '未出荷'
    form.remarks = row.remarks ?? ''
    form.delivery_date = row.delivery_date ?? ''
  } else {
    resetForm()
    const today = getJapanDate()
    form.date = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  }
  dialogVisible.value = true
}

function resetForm() {
  editId.value = null
  form.monthly_order_id = ''
  form.destination_cd = ''
  form.destination_name = ''
  form.date = ''
  form.weekday = ''
  form.product_cd = ''
  form.product_name = ''
  form.product_alias = ''
  form.product_type = '量産品'
  form.forecast_units = 0
  form.confirmed_boxes = 0
  form.confirmed_units = 0
  form.unit_per_box = 0
  form.status = '未出荷'
  form.remarks = ''
  form.delivery_date = ''
  formYear.value = ''
  formMonth.value = ''
  formDay.value = ''
  // 製品リストをリセット
  productOptions.value = [...allProductOptions.value]
}

// ========== 保存ロジック（handleSave） ==========
async function submitForm() {
  // ① Element Plus Form 校验
  try {
    await formRef.value?.validate()
  } catch (e: any) {
    const msg = (e && typeof e === 'object' && e.message) ? e.message : '入力内容を確認してください'
    ElMessage.warning(msg)
    return
  }

  // ② 年月日二次校验
  if (!formYear.value || !formMonth.value || !formDay.value) {
    ElMessage.warning('日付が正しく設定されていません')
    return
  }

  // ③ 納入日二次校验
  if (!form.delivery_date) {
    ElMessage.warning('納入日を入力してください')
    return
  }

  // ④ 箱数・入数校验
  if (!form.confirmed_boxes || !form.unit_per_box) {
    ElMessage.warning('確定箱数と入数を入力してください')
    return
  }

  saving.value = true
  try {
    // ---------- 編集モード ----------
    if (editId.value != null) {
      const payload: OrderDailyCreate = {
        monthly_order_id: form.monthly_order_id || undefined,
        destination_cd: form.destination_cd,
        destination_name: form.destination_name || undefined,
        date: form.date,
        weekday: form.weekday || undefined,
        product_cd: form.product_cd,
        product_name: form.product_name || undefined,
        product_alias: form.product_alias || undefined,
        product_type: form.product_type,
        forecast_units: form.forecast_units ?? 0,
        confirmed_boxes: form.confirmed_boxes ?? 0,
        confirmed_units: form.confirmed_units ?? 0,
        unit_per_box: form.unit_per_box ?? 0,
        status: form.status,
        remarks: form.remarks || undefined,
        delivery_date: form.delivery_date || undefined,
      }
      await updateOrderDaily(editId.value, payload)
      ElMessage.success('更新しました')
      dialogVisible.value = false
      loadList()
      return
    }

    // ---------- 新規追加モード ----------
    const year = formYear.value
    const month = formMonth.value.padStart(2, '0')
    const weekday = form.weekday || ''
    const confirmedUnits = Number(form.confirmed_units) || 0

    // ⑤ typeSuffix = product_type → 類型後綴
    const typeSuffix = getTypeSuffix(form.product_type || '量産品')

    // ⑥ monthlyOrderId = YYYYMM + destination_cd + product_cd + typeSuffix
    const monthlyOrderId = `${year}${month}${form.destination_cd}${form.product_cd}${typeSuffix}`

    // ⑦ 月次注文が存在するかチェック
    let monthlyExists = false
    try {
      const checkResult = await checkMonthlyOrderExists(monthlyOrderId)
      monthlyExists = checkResult.exists
    } catch {
      ElMessage.error('月次注文の確認に失敗しました')
      return
    }

    // ⑧ 月次注文が存在しない場合は自動作成
    if (!monthlyExists) {
      try {
        const monthlyResult = await addMonthlyOrder({
          order_id: monthlyOrderId,
          destination_cd: form.destination_cd,
          destination_name: form.destination_name || '',
          year: Number(year),
          month: Number(month),
          product_cd: form.product_cd,
          product_name: form.product_name || '',
          product_alias: form.product_alias || '',
          product_type: form.product_type || '量産品',
          forecast_units: confirmedUnits,
          forecast_total_units: confirmedUnits,
        })
        if (monthlyResult.ok) {
          ElMessage.success('月次注文が自動作成されました')
        } else {
          ElMessage.error('月次注文の作成に失敗しました')
          return
        }
      } catch {
        ElMessage.error('月次注文の作成に失敗しました')
        return
      }
    }

    // ⑨ 日次注文を作成
    const rawPostData: OrderDailyCreate = {
      monthly_order_id: monthlyOrderId,
      destination_cd: form.destination_cd,
      destination_name: form.destination_name || undefined,
      date: form.date,
      weekday: weekday || undefined,
      product_cd: form.product_cd,
      product_name: form.product_name || undefined,
      product_alias: form.product_alias || undefined,
      product_type: form.product_type,
      unit_per_box: Number(form.unit_per_box) || 0,
      confirmed_boxes: Number(form.confirmed_boxes) || 0,
      confirmed_units: confirmedUnits,
      forecast_units: confirmedUnits,
      delivery_date: form.delivery_date || undefined,
      status: '未出荷',
    }

    await addOrderDaily(rawPostData)
    ElMessage.success('追加成功しました')
    dialogVisible.value = false
    resetForm()
    loadList()
  } catch (e: any) {
    const errorMessage = (e instanceof Error) ? e.message : '日次注文の追加に失敗しました'
    ElMessage.error(errorMessage)
  } finally {
    saving.value = false
  }
}

// ========== 削除 ==========
async function handleDelete(row: OrderDailyItem) {
  try {
    await ElMessageBox.confirm(`日別受注 ID「${row.id}」を削除しますか？`, '確認', { type: 'warning' })
    await deleteOrderDaily(row.id)
    ElMessage.success('削除しました')
    loadList()
  } catch (e: unknown) {
    if ((e as string) !== 'cancel') ElMessage.error('削除に失敗しました')
  }
}

// ========== マウント ==========
onMounted(() => {
  updateTableMaxHeight()
  window.addEventListener('resize', updateTableMaxHeight)
  loadOptions()
  loadList()
})

onUnmounted(() => {
  window.removeEventListener('resize', updateTableMaxHeight)
})
</script>

<style scoped>
/* ======================================================
   Modern Glassmorphism UI — Daily Order List
   ====================================================== */

/* --- Base --- */
.order-daily-list {
  padding: 8px 10px 10px;
  min-height: calc(100vh - 20px);
  box-sizing: border-box;
  background-color: #f1f4fb;
  background-image:
    radial-gradient(ellipse 120% 80% at 0% -20%, rgba(99, 102, 241, 0.14), transparent 55%),
    radial-gradient(ellipse 100% 60% at 100% 0%, rgba(14, 165, 233, 0.1), transparent 50%),
    radial-gradient(ellipse 80% 50% at 50% 100%, rgba(16, 185, 129, 0.06), transparent 55%);
}

/* --- Hero: タイトル + 操作 + フィルタ一体 --- */
.page-hero {
  background: linear-gradient(145deg, #4f46e5 0%, #6366f1 38%, #7c3aed 72%, #6d28d9 100%);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 16px;
  padding: 8px 12px 10px;
  margin-bottom: 8px;
  box-shadow:
    0 8px 32px rgba(79, 70, 229, 0.28),
    0 2px 8px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.page-hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.hero-title-block {
  min-width: 0;
}

.toolbar-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.02em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}

.hero-meta {
  margin: 2px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.82);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.hero-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.date-quick-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.18);
}

.dq-label {
  font-size: 12px;
  color: rgba(255,255,255,0.85);
  font-weight: 500;
}

.date-quick-btns :deep(.el-button) {
  --el-button-bg-color: rgba(255, 255, 255, 0.14);
  --el-button-border-color: rgba(255, 255, 255, 0.32);
  --el-button-text-color: #fff;
  --el-button-hover-bg-color: rgba(255, 255, 255, 0.26);
  --el-button-hover-border-color: rgba(255, 255, 255, 0.48);
  --el-button-hover-text-color: #fff;
  border-radius: 8px;
  font-weight: 600;
}

.filter-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

/* --- ツールバー：役割別配色 --- */
.tb-btn {
  border-radius: 10px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    box-shadow 0.2s ease,
    filter 0.2s ease;
  position: relative;
  overflow: hidden;
  border: 1px solid transparent;
  color: #fff;
}

.tb-btn:hover {
  transform: translateY(-1px);
  filter: brightness(1.05);
}

.tb-btn:active {
  transform: translateY(0);
  filter: brightness(0.98);
}

/* 更新：シアン（同期・再取得） */
.tb-btn-refresh {
  background: linear-gradient(145deg, #0ea5e9 0%, #0284c7 100%);
  border-color: rgba(255, 255, 255, 0.35);
  box-shadow: 0 3px 12px rgba(14, 165, 233, 0.45);
}

.tb-btn-refresh:hover {
  box-shadow: 0 5px 18px rgba(14, 165, 233, 0.55);
}

/* CSV：アンバー（書き出し） */
.tb-btn-export {
  background: linear-gradient(145deg, #f59e0b 0%, #d97706 100%);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 3px 12px rgba(245, 158, 11, 0.42);
}

.tb-btn-export:hover:not(:disabled) {
  box-shadow: 0 5px 18px rgba(245, 158, 11, 0.52);
}

.tb-btn-export:disabled {
  opacity: 0.42;
  cursor: not-allowed;
  transform: none;
  filter: grayscale(0.15);
}

/* 新規登録：エメラルド（主アクション） */
.tb-btn-create {
  background: linear-gradient(145deg, #10b981 0%, #059669 100%);
  border-color: rgba(255, 255, 255, 0.35);
  box-shadow: 0 3px 14px rgba(16, 185, 129, 0.48);
}

.tb-btn-create:hover {
  box-shadow: 0 6px 22px rgba(16, 185, 129, 0.58);
}

/* --- KPI --- */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
  margin-bottom: 8px;
}

.kpi-card {
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 12px;
  padding: 6px 10px 8px;
  display: flex;
  flex-direction: column;
  gap: 1px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  border-left: 3px solid #cbd5e1;
}

.kpi-count {
  border-left-color: #64748b;
}

.kpi-units {
  border-left-color: #6366f1;
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.06) 0%, rgba(255, 255, 255, 0.92) 100%);
}

.kpi-boxes {
  border-left-color: #0d9488;
}

.kpi-forecast {
  border-left-color: #8b5cf6;
}

.kpi-label {
  font-size: 10px;
  color: #64748b;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.kpi-value {
  font-size: 17px;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  line-height: 1.15;
  letter-spacing: -0.02em;
}

.fi-group {
  display: flex;
  align-items: center;
  gap: 5px;
}

.fi-icon {
  font-size: 15px;
  color: #6366f1;
}

.fi-date-range {
  width: 280px;
}

.fi-dest {
  width: 195px;
  min-width: 150px;
}

.fi-product {
  width: 380px;
  min-width: 320px;
}

.fi-sep {
  width: 1px;
  height: 22px;
  background: rgba(0,0,0,0.08);
}

/* Product Option Styling */
.product-option-row {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 13px;
}

.product-option-cd {
  min-width: 90px;
  color: #606266;
}

.product-option-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-option-dest {
  min-width: 80px;
  color: #909399;
  font-size: 12px;
}

/* --- Table --- */
.table-section {
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(12px) saturate(160%);
  -webkit-backdrop-filter: blur(12px) saturate(160%);
  border-radius: 14px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow:
    0 4px 24px rgba(15, 23, 42, 0.06),
    0 1px 3px rgba(15, 23, 42, 0.04);
  padding: 0 8px 8px;
}

.table-section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  padding: 8px 4px 6px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 4px;
}

.table-section-title {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.table-section-hint {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
}

.data-table {
  width: 100%;
  --el-table-border-color: #e8ecf1;
  --el-table-header-bg-color: #f8fafc;
}

.data-table :deep(.el-table__header-wrapper th) {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
  color: #334155 !important;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 0.02em;
  border-bottom: 1px solid #e2e8f0 !important;
}

.data-table :deep(.el-table__body-wrapper td.el-table__cell) {
  color: #1e293b;
  font-size: 12px;
}

.data-table :deep(.el-table__row) {
  transition: background-color 0.15s ease;
}

.data-table :deep(.el-table__row:hover > td) {
  background: rgba(99, 102, 241, 0.06) !important;
}

.data-table :deep(.el-table__body tr.el-table__row--striped td) {
  background: #fafbfc;
}

.data-table :deep(.el-table__body tr.el-table__row--striped:hover > td) {
  background: rgba(99, 102, 241, 0.06) !important;
}

.row-act-btn {
  font-weight: 600;
  font-size: 12px;
}

.data-table :deep(.row-act-edit.el-button.is-link) {
  color: #4f46e5;
}

.data-table :deep(.row-act-edit.el-button.is-link:hover) {
  color: #4338ca;
}

.data-table :deep(.row-act-del.el-button.is-link) {
  color: #e11d48;
}

.data-table :deep(.row-act-del.el-button.is-link:hover) {
  color: #be123c;
}

.pagination-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
  padding: 4px 2px 0;
}

.page-range-text {
  font-size: 11px;
  color: #64748b;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.pagination-el {
  flex: 1;
  justify-content: flex-end;
  min-width: 0;
}

.pagination-container :deep(.pagination-el.el-pagination) {
  font-size: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
  --el-pagination-button-bg-color: #fff;
  --el-pagination-hover-color: #4f46e5;
}

.pagination-container :deep(.el-pagination.is-background .el-pager li.is-active) {
  background: linear-gradient(145deg, #6366f1 0%, #4f46e5 100%);
  color: #fff;
}

.pagination-container :deep(.el-pagination button),
.pagination-container :deep(.el-pagination .el-pager li) {
  min-width: 26px;
  height: 26px;
  line-height: 26px;
  font-weight: 600;
}

.status-tag {
  max-width: 100%;
}

.status-tag :deep(.el-tag__content) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 92px;
}

/* --- Modern Compact Dialog Styles --- */
.compact-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
}

/* カスタムヘッダー：紫背景・左に青＋・右に閉じる */
.daily-order-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}

.dialog-header-custom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 14px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.dialog-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dialog-header-add-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: rgba(59, 130, 246, 0.95);
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.dialog-header-add-btn:hover {
  background: rgba(37, 99, 235, 1);
}

.dialog-header-title {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.dialog-header-close {
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  transition: background 0.2s;
}

.dialog-header-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

.daily-order-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: #fff;
}

.compact-form {
  padding: 0;
}

.compact-section {
  background: #fff;
  margin: 10px;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  border: 1px solid #e8ecf1;
}

.compact-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #f5f7ff 0%, #eef1ff 100%);
  border-bottom: 1px solid #e0e6f7;
}

.section-icon {
  font-size: 16px;
  color: #667eea;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.compact-content {
  padding: 12px;
}

.compact-item {
  margin-bottom: 10px !important;
}

.compact-item:last-child {
  margin-bottom: 0 !important;
}

.compact-item :deep(.el-form-item__label) {
  font-size: 13px;
  padding-right: 8px;
  line-height: 32px;
}

.compact-item :deep(.el-input__inner),
.compact-item :deep(.el-input__wrapper) {
  font-size: 13px;
}

.product-option-compact {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 12px;
}

.opt-cd {
  min-width: 70px;
  color: #606266;
  font-weight: 500;
}

.opt-name {
  flex: 1;
  color: #303133;
}

/* 確定本数：浅绿背景・灰色文字・自動計算 (本) */
.calculated-row :deep(.el-input__wrapper) {
  min-height: 40px;
}

.calculated-field :deep(.el-input__wrapper) {
  background: #e8f5e9;
  border: 1px solid #a5d6a7;
  box-shadow: none;
}

.calculated-field :deep(.el-input__inner),
.calculated-field :deep(.el-input__wrapper) {
  color: #616161;
  font-size: 14px;
  text-align: left;
}

.calculated-field:not(.is-focus):deep(.el-input__wrapper) .el-input__inner::placeholder {
  color: #9e9e9e;
}

.unit-suffix {
  font-size: 13px;
  color: #616161;
  padding-right: 8px;
}

/* 説明：青い i アイコン・確定本数は入数×確定箱数で自動計算されます */
.compact-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #e3f2fd;
  border-radius: 8px;
  border-left: 4px solid #2196f3;
  margin-top: 12px;
  font-size: 12px;
  color: #1976d2;
}

.compact-tip .el-icon {
  font-size: 16px;
  color: #2196f3;
  flex-shrink: 0;
}

.dialog-footer-compact {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 14px 20px;
  background: #fff;
  border-top: 1px solid #e0e0e0;
}

.btn-cancel {
  background: #fff;
  border: 1px solid #9e9e9e;
  color: #424242;
  border-radius: 8px;
  padding: 8px 18px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-cancel:hover {
  background: #f5f5f5;
  border-color: #757575;
  color: #212121;
}

.btn-save {
  border-radius: 8px;
  padding: 8px 18px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-weight: 500;
  color: #fff;
}

.btn-save:hover {
  opacity: 0.92;
}

/* Responsive Design */
@media (max-width: 900px) {
  .kpi-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .order-daily-list {
    padding: 8px;
  }

  .page-hero {
    padding: 8px 10px 10px;
  }

  .page-hero-top {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-actions {
    justify-content: flex-end;
  }

  .toolbar-title {
    font-size: 15px;
  }

  .table-section-hint {
    display: none;
  }

  .filter-inline {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .fi-group {
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
  }

  .fi-date-range,
  .fi-dest,
  .fi-product {
    width: 100%;
  }

  .fi-sep {
    display: none;
  }

  .table-section {
    padding: 8px;
  }

  .data-table {
    font-size: 11px;
  }
}

@media (max-width: 600px) {
  .daily-order-dialog :deep(.el-dialog) {
    width: 95% !important;
    margin: 0 auto;
  }
  
  .compact-section {
    margin: 8px;
  }
  
  .compact-content {
    padding: 10px;
  }
  
  .compact-item :deep(.el-form-item__label) {
    font-size: 12px;
  }
  
  .dialog-footer-compact {
    padding: 10px 12px;
  }
  
  .btn-cancel span,
  .btn-save span {
    display: none;
  }
}

@media (max-width: 480px) {
  .kpi-strip {
    grid-template-columns: 1fr;
  }

  .date-quick-btns {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
  }

  .daily-order-dialog :deep(.el-dialog__title) {
    font-size: 14px;
  }
  
  .section-title {
    font-size: 12px;
  }
  
  .compact-form {
    font-size: 12px;
  }
}
</style>

