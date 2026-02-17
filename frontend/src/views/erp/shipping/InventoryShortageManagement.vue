<template>
  <div class="inventory-shortage">
    <div class="overview-card glass-card">
      <!-- ページタイトル -->
      <div class="card-header glass-header">
        <div class="header-left">
          <div class="header-icon-container">
            <el-icon class="header-icon"><Box /></el-icon>
          </div>
          <h1 class="header-title">{{ t('shipping.inventoryShortageTitle') }}</h1>
        </div>
        <div class="header-right">
          <el-button
            :icon="TrendCharts"
            @click="openChartDialog"
            :disabled="chartButtonDisabled"
            class="header-btn header-btn-chart"
            size="small"
          >
            {{ t('shipping.chartTrend') }}
          </el-button>
          <el-button :icon="Printer" @click="handlePrint" :disabled="loading || !filters.dateRange || filters.dateRange.length !== 2" class="header-btn header-btn-print" size="small">
            {{ t('shipping.print') }}
          </el-button>
          <el-button :icon="Operation" @click="handleAllUpdate" :disabled="updatingAll" :loading="updatingAll" class="header-btn header-btn-update" size="small">
            {{ t('shipping.batchUpdate') }}
          </el-button>
        </div>
      </div>

      <!-- フィルター条件 -->
      <div class="filter-section glass-filter">
        <div class="filter-row">
          <div class="filter-item">
            <label class="filter-label">{{ t('shipping.period') }}</label>
            <el-date-picker
              v-model="filters.dateRange"
              type="daterange"
              :start-placeholder="t('shipping.startDate')"
              :end-placeholder="t('shipping.endDate')"
              value-format="YYYY-MM-DD"
              size="small"
              :editable="false"
              @change="handleDateChange"
              class="date-picker"
            />
            <div class="date-nav-buttons">
              <el-button size="small" @click="adjustDate(-1)" class="nav-btn nav-prev">{{ t('shipping.prevDay') }}</el-button>
              <el-button size="small" @click="goToToday" class="nav-btn today-btn">{{ t('shipping.today') }}</el-button>
              <el-button size="small" @click="adjustDate(1)" class="nav-btn nav-next">{{ t('shipping.nextDay') }}</el-button>
            </div>
          </div>

          <div class="filter-item">
            <label class="filter-label">{{ t('shipping.productSelect') }}</label>
            <el-select
              v-model="filters.productCd"
              :placeholder="t('shipping.productSelect')"
              clearable
              size="small"
              class="product-select"
              @change="handleProductChange"
            >
              <el-option
                v-for="p in productOptions"
                :key="p.product_cd"
                :label="p.product_name ? `${p.product_cd} - ${p.product_name}` : p.product_cd"
                :value="p.product_cd"
              />
            </el-select>
          </div>

          <div class="filter-item">
            <el-checkbox v-model="filters.warehouseNegativeOnly" size="small">
              {{ t('shipping.onlyNegative') }}
            </el-checkbox>
          </div>
        </div>
      </div>

      <!-- 統計情報：现在在库数统计・安全在库统计・负数合计 -->
      <div v-if="!loading && listData.length > 0" class="stats-section glass-stats">
        <div class="stats-grid">
          <div class="stat-card glass-stat current-inv">
            <div class="stat-icon">
              <el-icon><Box /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ totalCurrentInventory }}</div>
              <div class="stat-label">{{ t('shipping.currentStock') }}</div>
            </div>
          </div>
          <div class="stat-card glass-stat safety-inv">
            <div class="stat-icon">
              <el-icon><Lock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ totalSafetyStock }}</div>
              <div class="stat-label">{{ t('shipping.safetyStock') }}</div>
            </div>
          </div>
          <div class="stat-card glass-stat negative-inv">
            <div class="stat-icon">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value stat-value-negative">{{ totalNegativeWarehouse }}</div>
              <div class="stat-label">{{ t('shipping.shortage') }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- データテーブル -->
      <div class="table-section glass-table-wrap" v-loading="loading">
        <el-empty
          v-if="!loading && displayedData.length === 0"
          :description="t('shipping.noData')"
          :image-size="56"
          class="empty-state"
        />
        <div v-else>
          <div class="table-container">
            <el-table
              :data="paginatedData"
              stripe
              style="width: 100%"
              show-summary
              :summary-method="getSummaries"
              size="small"
              class="modern-table"
            >
            <el-table-column label="日付" prop="date" width="120" align="center" fixed />
            <el-table-column label="曜日" prop="day_of_week" width="80" align="center" />
            <el-table-column label="製品CD" prop="product_cd" width="90" show-overflow-tooltip />
            <el-table-column label="製品名" prop="product_name" width="140" show-overflow-tooltip />
            <el-table-column label="受注数" prop="order_quantity" width="100" align="right">
              <template #default="{ row }">
                <span :class="{ 'cell-negative': (Number(row.order_quantity) || 0) < 0 }">{{ row.order_quantity ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="内示数" prop="forecast_quantity" width="100" align="right">
              <template #default="{ row }">
                <span :class="{ 'cell-negative': (Number(row.forecast_quantity) || 0) < 0 }">{{ row.forecast_quantity ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="安全在庫" prop="safety_stock" width="100" align="right">
              <template #default="{ row }">
                <span :class="{ 'cell-negative': (Number(row.safety_stock) || 0) < 0 }">{{ row.safety_stock ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="倉庫在庫" prop="warehouse_inventory" width="100" align="right">
              <template #default="{ row }">
                <span :class="{ 'cell-negative': (Number(row.warehouse_inventory) || 0) < 0 }">{{ row.warehouse_inventory ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="外注倉庫在庫" prop="outsourced_warehouse_inventory" width="120" align="right">
              <template #default="{ row }">
                <span :class="{ 'cell-negative': (Number(row.outsourced_warehouse_inventory) || 0) < 0 }">{{ row.outsourced_warehouse_inventory ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="現在在庫合計" width="120" align="right">
              <template #default="{ row }">
                <span :class="{ 'cell-negative': ((Number(row.warehouse_inventory) || 0) + (Number(row.outsourced_warehouse_inventory) || 0)) < 0 }">
                  {{ (Number(row.warehouse_inventory) || 0) + (Number(row.outsourced_warehouse_inventory) || 0) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
          </div>
          <div class="pagination-wrap">
            <el-pagination
              v-model:current-page="pagination.page"
              :page-size="pagination.pageSize"
              :total="displayedData.length"
              layout="total, prev, pager, next"
              small
              background
            />
          </div>
        </div>
      </div>

      <!-- 印刷用の隠しコンテナ（在庫不足一覧・期間・日期分组・合計） -->
      <div ref="printContent" class="print-content-hidden">
        <div class="print-body">
          <div class="print-header">
            <div class="print-title-wrap">
              <span class="print-title-accent"></span>
              <h1 class="print-title">在庫不足一覧</h1>
              <p class="print-subtitle">検査工程用</p>
            </div>
            <div class="print-header-row">
              <div class="print-period-block">
                <span class="print-period-dot"></span>
                <span class="print-period-label">対象期間</span>
                <span class="print-period-value">{{ printPeriodFormatted }}</span>
              </div>
              <div class="print-summary-box">
                <span class="print-summary-label">合計</span>
                <span class="print-summary-item"><em>箱数</em> {{ printTotals.box_quantity }}</span>
                <span class="print-summary-item"><em>本数</em> {{ printTotals.units }}</span>
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
                      <td class="print-td print-td-num">{{ row.box_quantity != null ? row.box_quantity : '—' }}</td>
                      <td class="print-td print-td-num">{{ row.units }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </template>

        </div>
      </div>

      <!-- 全部一括更新確認ダイアログ -->
      <el-dialog
        v-model="showAllUpdateConfirmDialog"
        title="全部一括更新確認"
        width="520px"
        class="all-update-confirm-dialog"
        :close-on-click-modal="false"
      >
        <div class="generate-confirm-content">
          <div class="confirm-info">
            <h3 class="confirm-title">以下の順で一括更新します</h3>
            <div class="confirm-details">
              <ol class="all-update-steps-list">
                <li>受注データ更新</li>
                <li>実績データ更新</li>
                <li>不良データ更新</li>
                <li>廃棄データ更新</li>
                <li>保留データ更新</li>
                <li>計画データ更新</li>
                <li>在庫・推移・安全在庫更新</li>
              </ol>
              <div class="detail-row" style="margin-top: 10px;">
                <span class="detail-value">この処理には時間がかかる場合があります。</span>
              </div>
            </div>
          </div>
        </div>
        <template #footer>
          <div class="dialog-footer">
            <el-button @click="showAllUpdateConfirmDialog = false" class="cancel-btn">キャンセル</el-button>
            <el-button type="primary" @click="confirmAllUpdate" class="confirm-btn">一括更新開始</el-button>
          </div>
        </template>
      </el-dialog>

      <!-- 製品別推移グラフダイアログ -->
      <el-dialog
        v-model="showChartDialog"
        :title="chartDialogTitle"
        class="chart-dialog chart-dialog--fullscreen-top"
        destroy-on-close
        append-to-body
        @closed="disposeChart"
        @opened="onChartDialogOpened"
      >
        <div class="chart-dialog-body">
          <div class="chart-dialog-subtitle">{{ chartDialogSubtitle }}</div>
          <div ref="chartContainerRef" class="chart-container"></div>
        </div>
        <template #footer>
          <div class="chart-dialog-footer">
            <el-button :icon="Printer" @click="handlePrintChart" type="primary" size="default">印刷</el-button>
            <el-button @click="showChartDialog = false">閉じる</el-button>
          </div>
        </template>
      </el-dialog>

      <!-- 一括更新進度ダイアログ -->
      <el-dialog
        v-model="showProgressDialog"
        title="一括更新中"
        width="500px"
        :close-on-click-modal="false"
        :close-on-press-escape="false"
        :show-close="false"
        class="progress-dialog progress-dialog--styled"
      >
        <div class="progress-content">
          <div class="progress-info">
            <div class="progress-icon-wrap">
              <el-icon class="progress-icon"><Loading /></el-icon>
            </div>
            <span class="progress-text">{{ progressText }}</span>
          </div>
          <div class="progress-track">
            <div
              class="progress-fill"
              :class="{ 'progress-fill--success': progressStatus === 'success' }"
              :style="{ width: Math.min(100, Math.round(progressPercentage)) + '%' }"
            >
              <span class="progress-shine" />
            </div>
          </div>
          <div class="progress-details">
            <span class="detail-label">進捗</span>
            <span class="detail-value progress-percent">{{ Math.round(progressPercentage) }}%</span>
          </div>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getJSTToday as getJSTTodayUtil } from '@/utils/dateFormat'
import { Box, Lock, Warning, Printer, Operation, Loading, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import {
  getProductionSummarysList,
  getProductionSummarysProducts,
  getInventoryShortagePrint,
  acquireBatchUpdateLock,
  releaseBatchUpdateLock,
  updateProductionSummarysFromOrderDaily,
  updateProductionSummarysActual,
  updateProductionSummarysDefect,
  updateProductionSummarysScrap,
  updateProductionSummarysOnHold,
  updateProductionSummarysPlan,
  clearProductionSummarysCalculatedFields,
  updateProductionSummarysInventory,
  updateProductionSummarysTrend,
  updateProductionSummarysSafetyStock,
} from '@/api/database'
import type { ProductionSummaryProduct, InventoryShortagePrintRow } from '@/api/database'

interface SummaryRow {
  product_cd?: string
  product_name?: string
  date?: string
  day_of_week?: string
  order_quantity?: number
  forecast_quantity?: number
  safety_stock?: number
  warehouse_inventory?: number
  outsourced_warehouse_inventory?: number
}

const loading = ref(false)
const listData = ref<SummaryRow[]>([])
const productOptions = ref<ProductionSummaryProduct[]>([])
const printContent = ref<HTMLElement | null>(null)
/** 印刷用テーブルデータ（API で products / destinations ジョイン取得） */
const printTableData = ref<InventoryShortagePrintRow[]>([])

const showAllUpdateConfirmDialog = ref(false)
const showProgressDialog = ref(false)
const progressPercentage = ref(0)
const progressStatus = ref<'success' | 'exception' | 'warning' | ''>('')
const progressText = ref('')
const updatingAll = ref(false)

const showChartDialog = ref(false)
const chartContainerRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const chartButtonDisabled = computed(
  () =>
    loading.value ||
    !filters.dateRange ||
    filters.dateRange.length !== 2 ||
    !filters.productCd ||
    listData.value.length === 0
)

const chartDialogTitle = computed(() => {
  const name = productOptions.value.find((p) => p.product_cd === filters.productCd)?.product_name || filters.productCd
  return `在庫・受注推移（${filters.productCd} ${name ? `- ${name}` : ''}）`
})

const chartDialogSubtitle = computed(() => {
  if (!filters.dateRange || filters.dateRange.length !== 2) return ''
  return `${filters.dateRange[0]} ～ ${filters.dateRange[1]}`
})

/** グラフ用：選択製品・期間の listData を日付昇順 */
const chartDataForProduct = computed(() => {
  const pc = filters.productCd
  const [start, end] = filters.dateRange || ['', '']
  if (!pc || !start || !end) return []
  return listData.value
    .filter((row) => row.product_cd === pc && row.date && row.date >= start && row.date <= end)
    .sort((a, b) => (a.date || '').localeCompare(b.date || ''))
})

const { t } = useI18n()
const getJSTToday = getJSTTodayUtil

const today = getJSTToday()
const filters = reactive({
  dateRange: [today, today] as string[],
  productCd: '' as string,
  warehouseNegativeOnly: false,
})

// 表示用データ：倉庫在庫マイナスのみフィルタ対応、日付昇順 → 製品名昇順（デフォルト並び）
const displayedData = computed(() => {
  let data = listData.value
  if (filters.warehouseNegativeOnly) {
    data = data.filter((row) => (Number(row.warehouse_inventory) || 0) < 0)
  }
  return [...data].sort((a, b) => {
    const dateCompare = (a.date || '').localeCompare(b.date || '')
    if (dateCompare !== 0) return dateCompare
    const nameCompare = (a.product_name || '').localeCompare(b.product_name || '', 'ja')
    if (nameCompare !== 0) return nameCompare
    return (a.product_cd || '').localeCompare(b.product_cd || '', 'ja')
  })
})

const PAGE_SIZE = 50
const pagination = reactive({ page: 1, pageSize: PAGE_SIZE })

/** 当前页数据（统计卡片仍用 displayedData 全量） */
const paginatedData = computed(() => {
  const list = displayedData.value
  const start = (pagination.page - 1) * pagination.pageSize
  return list.slice(start, start + pagination.pageSize)
})

watch(
  () => displayedData.value.length,
  (len) => {
    const maxPage = Math.max(1, Math.ceil(len / pagination.pageSize))
    if (pagination.page > maxPage) pagination.page = maxPage
  }
)
watch(
  () => filters.warehouseNegativeOnly,
  () => {
    pagination.page = 1
  }
)

// 現在在庫合計（倉庫＋外注倉庫）表示データ（全件）
const totalCurrentInventory = computed(() => {
  return displayedData.value.reduce(
    (sum, row) =>
      sum + (Number(row.warehouse_inventory) || 0) + (Number(row.outsourced_warehouse_inventory) || 0),
    0
  )
})

// 安全在庫合計（表示データ）
const totalSafetyStock = computed(() => {
  return displayedData.value.reduce((sum, row) => sum + (Number(row.safety_stock) || 0), 0)
})

// 倉庫在庫・负数合計（表示データ内のマイナス分のみ合計）
const totalNegativeWarehouse = computed(() => {
  return displayedData.value.reduce((sum, row) => {
    const v = Number(row.warehouse_inventory) || 0
    return v < 0 ? sum + v : sum
  }, 0)
})

/** 印刷用：日付ごとにグループ化 [{ date, rows }] */
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

/** 印刷用：対象期間のフォーマット（年月日） */
const printPeriodFormatted = computed(() => {
  if (!filters.dateRange || filters.dateRange.length !== 2) return '—'
  const fmt = (s: string) => {
    if (!s || s.length < 10) return s
    const [y, m, d] = [s.slice(0, 4), s.slice(5, 7), s.slice(8, 10)]
    return `${y}年${m}月${d}日`
  }
  return `${fmt(filters.dateRange[0])} ～ ${fmt(filters.dateRange[1])}`
})

/** 印刷用：合計（箱数・本数） */
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

async function fetchProducts() {
  try {
    const res: any = await getProductionSummarysProducts()
    const body = res?.data ?? res
    const list = Array.isArray(body) ? body : body?.data ?? []
    productOptions.value = list
  } catch (e) {
    ElMessage.error('製品一覧の取得に失敗しました')
    productOptions.value = []
  }
}

async function fetchList() {
  if (!filters.dateRange || filters.dateRange.length !== 2) {
    ElMessage.warning('期間を選択してください')
    return
  }
  loading.value = true
  try {
    const res: any = await getProductionSummarysList({
      page: 1,
      limit: 50000,
      startDate: filters.dateRange[0],
      endDate: filters.dateRange[1],
      productCd: filters.productCd || undefined,
      sortBy: 'product_name',
      sortOrder: 'ASC',
    })
    const payload = res?.data ?? res
    const list = payload?.data?.list ?? payload?.list ?? []
    listData.value = Array.isArray(list) ? list : []
  } catch (e) {
    ElMessage.error('データの取得に失敗しました')
    listData.value = []
  } finally {
    loading.value = false
  }
}

function handleDateChange() {
  pagination.page = 1
  if (filters.dateRange && filters.dateRange.length === 2) fetchList()
}

function adjustDate(days: number) {
  if (!filters.dateRange || filters.dateRange.length !== 2) return
  const startDate = new Date(filters.dateRange[0] + 'T00:00:00+09:00')
  const endDate = new Date(filters.dateRange[1] + 'T00:00:00+09:00')
  startDate.setDate(startDate.getDate() + days)
  endDate.setDate(endDate.getDate() + days)
  const fmt = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  filters.dateRange = [fmt(startDate), fmt(endDate)]
  fetchList()
}

function goToToday() {
  const t = getJSTToday()
  filters.dateRange = [t, t]
  fetchList()
}

function handleProductChange() {
  pagination.page = 1
  fetchList()
}

function getSummaries(param: { columns: Array<{ property?: string }>; data: SummaryRow[] }): string[] {
  const { columns, data } = param
  const sums: string[] = []
  columns.forEach((col, i) => {
    if (i === 0) {
      sums[i] = '合計'
      return
    }
    const prop = col.property
    if (
      prop === 'order_quantity' ||
      prop === 'forecast_quantity' ||
      prop === 'safety_stock' ||
      prop === 'warehouse_inventory' ||
      prop === 'outsourced_warehouse_inventory'
    ) {
      const v = data.reduce((s, row) => s + (Number((row as any)[prop]) || 0), 0)
      sums[i] = String(v)
    } else if (i === 9) {
      // 現在在庫合計列（倉庫＋外注倉庫）
      const v = data.reduce(
        (s, row) =>
          s + (Number(row.warehouse_inventory) || 0) + (Number(row.outsourced_warehouse_inventory) || 0),
        0
      )
      sums[i] = String(v)
    } else {
      sums[i] = ''
    }
  })
  return sums
}

async function handlePrint() {
  if (!filters.dateRange || filters.dateRange.length !== 2) {
    ElMessage.warning('期間を選択してください')
    return
  }
  try {
    const res: any = await getInventoryShortagePrint({
      startDate: filters.dateRange[0],
      endDate: filters.dateRange[1],
      productCd: filters.productCd || undefined,
    })
    const data = res?.data ?? res
    const list = Array.isArray(data) ? data : data?.data ?? []
    printTableData.value = list
    if (list.length === 0) {
      ElMessage.warning('印刷対象の在庫不足データがありません')
      return
    }
    nextTick(() => {
      executeFrontendPrint(printContent.value)
    })
  } catch (e: any) {
    // レスポンスエラーは interceptor で既に表示済みのため、ネットワークエラー時のみ表示
    if (!e?.response) {
      ElMessage.error('印刷データの取得に失敗しました')
    }
  }
}

function executeFrontendPrint(contentRef: HTMLElement | null) {
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
        <title>在庫不足一覧</title>
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

function getFirstDayOfCurrentMonth(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  return `${y}-${m}-01`
}

function handleAllUpdate() {
  showAllUpdateConfirmDialog.value = true
}

// crypto.randomUUID が無い環境（古いブラウザ・非 HTTPS 等）用のフォールバック
function getRandomUUID(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  const buf = new Uint8Array(16)
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    crypto.getRandomValues(buf)
  } else {
    for (let i = 0; i < 16; i++) buf[i] = Math.floor(Math.random() * 256)
  }
  buf[6] = (buf[6]! & 0x0f) | 0x40
  buf[8] = (buf[8]! & 0x3f) | 0x80
  const hex = Array.from(buf, b => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

async function confirmAllUpdate() {
  showAllUpdateConfirmDialog.value = false
  const lockValue = getRandomUUID()
  try {
    await acquireBatchUpdateLock(lockValue)
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status
    if (status === 423) {
      ElMessage.warning('他の端末で一括更新が実行中のため、しばらく待ってから再度お試しください。')
      return
    }
    ElMessage.error('ロックの取得に失敗しました。')
    return
  }
  updatingAll.value = true
  showProgressDialog.value = true
  progressStatus.value = ''
  const results: { name: string; success: boolean }[] = []
  const stepNames = [
    '受注データ更新',
    '実績データ更新',
    '不良データ更新',
    '廃棄データ更新',
    '保留データ更新',
    '計画データ更新',
  ]
  const steps = [
    () => updateProductionSummarysFromOrderDaily({ updateMode: 'all' }),
    () => updateProductionSummarysActual(),
    () => updateProductionSummarysDefect(),
    () => updateProductionSummarysScrap(),
    () => updateProductionSummarysOnHold(),
    () => updateProductionSummarysPlan(),
  ]
  try {
    for (let i = 0; i < steps.length; i++) {
      progressPercentage.value = Math.round(((i + 1) / 7) * 90)
      progressText.value = `${stepNames[i]}を実行中... (${i + 1}/7)`
      try {
        await steps[i]()
        results.push({ name: stepNames[i], success: true })
      } catch (_e) {
        results.push({ name: stepNames[i], success: false })
      }
      await new Promise((r) => setTimeout(r, 300))
    }
    const startDate = getFirstDayOfCurrentMonth()
    try {
      await clearProductionSummarysCalculatedFields(startDate)
    } catch (_e) {
      /* ignore */
    }
    progressPercentage.value = 92
    progressText.value = '在庫・推移更新を実行中... (7/7)'
    try {
      await updateProductionSummarysInventory(startDate)
      results.push({ name: '在庫更新', success: true })
    } catch (_e) {
      results.push({ name: '在庫更新', success: false })
    }
    await new Promise((r) => setTimeout(r, 300))
    try {
      await updateProductionSummarysTrend(startDate)
      results.push({ name: '推移更新', success: true })
    } catch (_e) {
      results.push({ name: '推移更新', success: false })
    }
    await new Promise((r) => setTimeout(r, 300))
    progressText.value = '安全在庫を更新中... (8/8)'
    try {
      await updateProductionSummarysSafetyStock(startDate)
      results.push({ name: '安全在庫更新', success: true })
    } catch (_e) {
      results.push({ name: '安全在庫更新', success: false })
    }
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const successCount = results.filter((r) => r.success).length
    const failCount = results.filter((r) => !r.success).length
    const failedNames = results.filter((r) => !r.success).map((r) => r.name)
    progressText.value =
      failCount === 0
        ? '全部一括更新が完了しました！'
        : `全部一括更新が完了しました（成功 ${successCount} / 失敗 ${failCount}）\n失敗: ${failedNames.join('、')}`
    if (failCount === 0) {
      ElMessage.success('全部一括更新が完了しました')
    } else {
      ElMessage.warning(`一部失敗しました: ${failedNames.join('、')}`)
    }
    setTimeout(() => {
      showProgressDialog.value = false
      updatingAll.value = false
      setTimeout(() => fetchList(), 500)
    }, 1500)
  } finally {
    try {
      await releaseBatchUpdateLock(lockValue)
    } catch (_e) {
      /* 解放失敗は無視（ロックは有効期限で自動解放） */
    }
  }
}

function openChartDialog() {
  showChartDialog.value = true
}

function onChartDialogOpened() {
  nextTick(() => {
    initChart()
  })
}

function initChart() {
  const el = chartContainerRef.value
  if (!el) return
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  chartInstance = echarts.init(el, null, { renderer: 'canvas' })
  updateChart()
}

function formatChartLabel(value: number): string {
  if (typeof value === 'number' && value < 0) return `{negative|${value}}`
  return `${value}`
}

function updateChart() {
  if (!chartInstance) return
  const data = chartDataForProduct.value
  const dates = data.map((r) => r.date || '').filter(Boolean)
  const forecastQty = data.map((r) => Number(r.forecast_quantity) || 0)
  const warehouseInv = data.map((r) => Number(r.warehouse_inventory) || 0)

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#000', fontSize: 12 },
      padding: [10, 14],
      axisPointer: { type: 'cross', lineStyle: { color: '#94a3b8', type: 'dashed' } },
    },
    legend: {
      data: ['内示数', '倉庫在庫'],
      top: 8,
      right: 16,
      textStyle: { fontSize: 11, color: '#000' },
      itemWidth: 14,
      itemGap: 12,
    },
    grid: { left: 40, right: 40, top: 50, bottom: 72, containLabel: false },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        fontSize: 11,
        color: '#000',
        rotate: dates.length > 14 ? 35 : 0,
        margin: 28,
      },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 11, color: '#000' },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        name: '内示数',
        type: 'line',
        smooth: true,
        data: forecastQty,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2 },
        itemStyle: { color: '#8b5cf6' },
        label: {
          show: true,
          fontSize: 10,
          position: 'top',
          formatter: (params: any) => formatChartLabel(Number(params.value)),
          rich: { negative: { color: '#f56c6c' } },
        },
      },
      {
        name: '倉庫在庫',
        type: 'line',
        smooth: true,
        data: warehouseInv,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2 },
        itemStyle: { color: '#f59e0b' },
        label: {
          show: true,
          fontSize: 10,
          position: 'bottom',
          formatter: (params: any) => formatChartLabel(Number(params.value)),
          rich: { negative: { color: '#f56c6c' } },
        },
      },
    ],
  }
  chartInstance.setOption(option)
  chartInstance.resize()
}

function disposeChart() {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

function handlePrintChart() {
  if (!chartInstance) return
  const url = chartInstance.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff',
  })
  const title = chartDialogTitle.value
  const subtitle = chartDialogSubtitle.value
  const w = window.open('', '_blank')
  if (!w) {
    ElMessage.warning('ポップアップがブロックされています。印刷するにはブラウザの設定でポップアップを許可してください。')
    return
  }
  w.document.write(`
    <!DOCTYPE html><html><head><meta charset="utf-8"><title>${title}</title>
    <style>
      body{font-family:system-ui,sans-serif;margin:24px;text-align:center;background:#fff;}
      h1{font-size:18px;color:#000;margin:0 0 8px 0;}
      p{font-size:13px;color:#000;margin:0 0 20px 0;}
      img{max-width:100%;height:auto;box-shadow:0 2px 8px rgba(0,0,0,0.08);}
      @media print {
        @page { size: A4 landscape; margin: 12mm; }
        body { margin: 0; }
      }
    </style></head><body>
    <h1>${title}</h1><p>${subtitle}</p><img src="${url}" alt="推移グラフ" />
    </body></html>
  `)
  w.document.close()
  w.focus()
  setTimeout(() => {
    w.print()
    w.close()
  }, 300)
}

onMounted(() => {
  fetchProducts()
  fetchList()
})
</script>

<style scoped>
.inventory-shortage {
  padding: 6px;
  min-height: 100vh;
  background: linear-gradient(160deg, #eef2f8 0%, #e4e9f2 48%, #e8ecf4 100%);
}

.glass-card {
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.03), inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.glass-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 48px;
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.92) 0%, rgba(139, 92, 246, 0.9) 100%);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon-container {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.24);
  border: 1px solid rgba(255, 255, 255, 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.header-icon {
  color: #fff;
  font-size: 18px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin: 0;
  letter-spacing: 0.03em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.header-btn {
  border-radius: 6px;
  font-weight: 500;
  font-size: 12px;
  padding: 5px 12px;
  border: 1px solid transparent;
  color: #fff;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.header-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
}

/* 推移グラフ：青緑 */
.header-btn-chart {
  background: linear-gradient(135deg, rgba(20, 184, 166, 0.95) 0%, rgba(13, 148, 136, 0.9) 100%);
  border-color: rgba(255, 255, 255, 0.35);
}

.header-btn-chart:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(13, 148, 136, 0.95) 0%, rgba(15, 118, 110, 0.95) 100%);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 2px 6px rgba(20, 184, 166, 0.35);
}

/* 印刷：スレート灰 */
.header-btn-print {
  background: linear-gradient(135deg, rgba(71, 85, 105, 0.9) 0%, rgba(51, 65, 85, 0.9) 100%);
  border-color: rgba(255, 255, 255, 0.25);
}

.header-btn-print:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(51, 65, 85, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%);
  border-color: rgba(255, 255, 255, 0.4);
  box-shadow: 0 2px 6px rgba(51, 65, 85, 0.4);
}

/* 全部一括更新：オレンジ・メイン操作 */
.header-btn-update {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.95) 0%, rgba(217, 119, 6, 0.9) 100%);
  border-color: rgba(255, 255, 255, 0.4);
}

.header-btn-update:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(217, 119, 6, 0.95) 0%, rgba(180, 83, 9, 0.95) 100%);
  border-color: rgba(255, 255, 255, 0.55);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.4);
}

.glass-filter {
  margin: 6px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.85);
  border: 1px solid rgba(226, 232, 240, 0.85);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
  justify-content: flex-start;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.filter-label {
  font-weight: 500;
  color: #000;
  font-size: 12px;
  white-space: nowrap;
}

.filter-item :deep(.el-checkbox) {
  margin-right: 0;
}
.filter-item :deep(.el-checkbox__label) {
  font-size: 12px;
  color: #000;
}

.date-picker {
  width: 180px;
}

.date-picker :deep(.el-input__wrapper) {
  border-radius: 6px;
  border: 1px solid rgba(203, 213, 225, 0.85);
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 10px;
  min-height: 32px;
  font-size: 12px;
}

.date-picker :deep(.el-input__inner) {
  font-size: 12px;
}

.date-nav-buttons {
  display: flex;
  gap: 3px;
  margin-left: 3px;
}

.nav-btn {
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11px;
  min-width: 28px;
  min-height: 28px;
  border: 1px solid rgba(203, 213, 225, 0.8);
  background: rgba(248, 250, 252, 0.95);
  color: #000;
}

.nav-btn:hover {
  background: rgba(226, 232, 240, 0.95);
  border-color: #94a3b8;
}

.product-select {
  width: 228px;
}

.product-select :deep(.el-input__wrapper) {
  border-radius: 6px;
  border: 1px solid rgba(203, 213, 225, 0.85);
  background: rgba(255, 255, 255, 0.9);
  min-height: 32px;
  font-size: 12px;
}

.product-select :deep(.el-input__inner) {
  font-size: 12px;
}

.glass-stats {
  margin: 6px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.85);
  border: 1px solid rgba(226, 232, 240, 0.85);
}

.stats-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  min-width: 120px;
}

.stat-card.current-inv {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.12) 100%);
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.stat-card.safety-inv {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(22, 163, 74, 0.12) 100%);
  border: 1px solid rgba(34, 197, 94, 0.25);
}

.stat-icon {
  font-size: 18px;
  color: #000;
}

.stat-card.current-inv .stat-icon {
  color: #2563eb;
}

.stat-card.safety-inv .stat-icon {
  color: #16a34a;
}

.stat-card.negative-inv {
  background: linear-gradient(135deg, rgba(245, 108, 108, 0.15) 0%, rgba(245, 108, 108, 0.1) 100%);
  border: 1px solid rgba(245, 108, 108, 0.3);
}

.stat-card.negative-inv .stat-icon {
  color: #f56c6c;
}

.stat-value-negative {
  color: #f56c6c;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #000;
}

.stat-label {
  font-size: 11px;
  color: #000;
}

.glass-table-wrap {
  margin: 6px;
  padding: 6px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(226, 232, 240, 0.75);
}

.empty-state {
  padding: 16px;
}

.empty-state :deep(.el-empty__description) {
  font-size: 12px;
  color: #000;
}

.table-container {
  overflow-x: auto;
  border-radius: 6px;
}

.modern-table {
  border-radius: 6px;
  overflow: hidden;
}

.modern-table :deep(.el-table__header th),
.modern-table :deep(.el-table__body td) {
  padding: 4px 8px;
  font-size: 12px;
}
.modern-table :deep(.el-table__footer-wrapper td) {
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 600;
}
.modern-table :deep(.el-table .el-table__row) {
  --el-table-row-hover-bg-color: rgba(99, 102, 241, 0.04);
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 10px 0 4px;
  flex-wrap: wrap;
  gap: 6px;
}

.pagination-wrap :deep(.el-pagination) {
  font-weight: 500;
  font-size: 11px;
}

.pagination-wrap :deep(.el-pagination__total) {
  font-size: 11px;
  color: #000;
}

.pagination-wrap :deep(.el-pagination .el-pager li) {
  min-width: 26px;
  height: 26px;
  line-height: 26px;
  font-size: 11px;
}

.pagination-wrap :deep(.el-pagination .btn-prev),
.pagination-wrap :deep(.el-pagination .btn-next) {
  min-width: 26px;
  height: 26px;
  line-height: 26px;
  font-size: 11px;
}

.cell-negative {
  color: #f56c6c;
  font-weight: 500;
}

/* 全部一括更新確認ダイアログ */
.all-update-confirm-dialog .generate-confirm-content {
  padding: 8px 0;
}
.confirm-title {
  font-size: 14px;
  margin: 0 0 12px 0;
  color: #000;
}
.all-update-steps-list {
  margin: 0;
  padding-left: 20px;
  color: #000;
  font-size: 13px;
  line-height: 1.8;
}
.detail-value {
  font-size: 12px;
  color: #000;
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 一括更新進度ダイアログ（精美・アニメーション） */
.progress-dialog--styled .el-dialog__body {
  padding: 20px 24px 24px;
}
.progress-content {
  padding: 4px 0;
}
.progress-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.progress-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
  animation: progress-icon-pulse 1.5s ease-in-out infinite;
}
.progress-icon {
  font-size: 20px;
  color: #6366f1;
  animation: progress-icon-spin 0.9s linear infinite;
}
.progress-text {
  font-size: 14px;
  color: #000;
  font-weight: 500;
  transition: opacity 0.25s ease;
}
.progress-track {
  height: 14px;
  border-radius: 999px;
  background: #f1f5f9;
  overflow: hidden;
  margin-bottom: 12px;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.04);
}
.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  background-size: 200% 100%;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
}
.progress-fill--success {
  background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
}
.progress-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.35) 50%,
    transparent 100%
  );
  animation: progress-shine 1.8s ease-in-out infinite;
}
.progress-details {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #000;
}
.progress-details .detail-label {
  font-weight: 500;
}
.progress-details .detail-value {
  font-weight: 700;
  color: #6366f1;
  font-variant-numeric: tabular-nums;
  transition: transform 0.2s ease, color 0.3s ease;
}
.progress-details .detail-value.progress-percent {
  min-width: 2.5em;
  text-align: right;
}
/* 完了時は進捗数値を緑に */
.progress-dialog--styled .progress-content:has(.progress-fill--success) .detail-value {
  color: #059669;
}
@keyframes progress-icon-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes progress-icon-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.9; }
}
@keyframes progress-shine {
  0% { left: -100%; }
  60%, 100% { left: 100%; }
}

/* ========== 推移グラフダイアログ（最上层・画面 70%） ========== */
.chart-dialog.chart-dialog--fullscreen-top :deep(.el-dialog) {
  width: 70vw !important;
  max-width: 70vw;
  margin-top: 3vh !important;
  margin-bottom: 0;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
}
.chart-dialog.chart-dialog--fullscreen-top :deep(.el-dialog__body) {
  padding: 16px 20px 20px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.chart-dialog-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.chart-dialog-subtitle {
  font-size: 13px;
  color: #000;
  margin-bottom: 12px;
  font-weight: 500;
  flex-shrink: 0;
}
.chart-dialog.chart-dialog--fullscreen-top .chart-container {
  flex: 1;
  min-height: 280px;
  height: 100%;
}
.chart-container {
  width: 100%;
  border-radius: 10px;
  background: linear-gradient(180deg, #fafbfc 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.02);
}
.chart-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* ========== 响应式布局 ========== */
@media (max-width: 992px) {
  .inventory-shortage {
    padding: 5px;
  }

  .filter-row {
    gap: 6px 8px;
  }

  .product-select {
    width: 100%;
    max-width: 240px;
  }
}

@media (max-width: 768px) {
  .inventory-shortage {
    padding: 4px;
  }

  .glass-card {
    border-radius: 10px;
  }

  .glass-header {
    min-height: 44px;
    padding: 6px 10px;
  }

  .header-icon-container {
    width: 28px;
    height: 28px;
  }

  .header-icon {
    font-size: 16px;
  }

  .header-title {
    font-size: 15px;
  }

  .glass-filter {
    margin: 5px;
    padding: 6px 8px;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
  }

  .filter-item {
    flex-wrap: wrap;
  }

  .filter-item .date-picker {
    width: 100%;
    min-width: 0;
  }

  .filter-item .product-select {
    width: 100%;
    min-width: 0;
  }

  .date-nav-buttons {
    margin-left: 0;
    margin-top: 3px;
  }

  .glass-stats {
    margin: 5px;
    padding: 6px 8px;
  }

  .stats-grid {
    gap: 6px;
  }

  .stat-card {
    min-width: 0;
    flex: 1 1 100px;
    padding: 6px 10px;
  }

  .stat-value {
    font-size: 15px;
  }

  .stat-label {
    font-size: 10px;
  }

  .stat-icon {
    font-size: 16px;
  }

  .glass-table-wrap {
    margin: 5px;
    padding: 5px;
  }

  .table-container {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    margin: 0 -2px;
  }

  .modern-table {
    min-width: 780px;
  }

  .modern-table :deep(.el-table__header th),
  .modern-table :deep(.el-table__body td) {
    padding: 3px 6px;
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .inventory-shortage {
    padding: 3px;
  }

  .glass-header {
    min-height: 42px;
    padding: 5px 8px;
  }

  .header-title {
    font-size: 14px;
  }

  .filter-label {
    font-size: 11px;
  }

  .header-btn {
    font-size: 11px;
    padding: 4px 8px;
  }

  .stats-grid {
    flex-direction: column;
    gap: 4px;
  }

  .stat-card {
    flex: none;
    width: 100%;
    padding: 6px 10px;
  }
}

/* ========== 印刷用：精致样式（画面上は非表示） ========== */
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

/* ----- ヘッダー ----- */
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

/* ----- 日付セクション（1日分を1ページに収める分頁制御） ----- */
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

.print-tr {
  transition: background 0.15s ease;
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

.print-tr:first-child .print-td {
  border-top: none;
}

.print-td-num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 500;
  color: #000;
}

/* ----- 合計（対象期間と同行） ----- */
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

/* ----- フッター ----- */
.print-footer {
  margin-top: 12px;
  padding-top: 8px;
  text-align: center;
  border-top: 1px solid #f1f5f9;
}

.print-footer-text {
  font-size: 9px;
  color: #000;
  letter-spacing: 0.03em;
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

  /* 1日分のデータを1ページに収める（分頁時はブロックごと次ページへ） */
  .print-date-section {
    page-break-inside: avoid;
    break-inside: avoid;
  }

  .print-title-accent {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

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
</style>

<!-- 推移グラフ append-to-body 時も効くよう unscoped -->
<style>
.chart-dialog.chart-dialog--fullscreen-top.el-dialog {
  width: 70vw !important;
  max-width: 70vw;
  margin-top: 3vh !important;
  margin-bottom: 0;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
}
.chart-dialog.chart-dialog--fullscreen-top .el-dialog__body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.chart-dialog.chart-dialog--fullscreen-top .chart-container {
  flex: 1;
  min-height: 280px;
  height: 100%;
}
</style>
