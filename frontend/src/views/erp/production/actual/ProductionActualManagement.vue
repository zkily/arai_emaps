<template>
  <div class="production-actual-management">
    <div class="page-header">
      <div class="page-title">
        <div class="title-icon">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="title-content">
          <h1>生産実績管理</h1>
          <p>工程別に在庫取引ログ（実績）を横断分析します</p>
        </div>
      </div>
      <div class="page-actions">
        <el-button :icon="Refresh" class="action-btn" @click="handleRefresh">再取得</el-button>
      </div>
    </div>

    <el-card class="search-card" shadow="hover">
      <el-form
        :model="searchForm"
        label-width="80px"
        class="search-form"
      >
        <el-row :gutter="12" class="search-row">
          <el-col :span="6">
            <el-form-item label="製品名">
              <el-select
                v-model="searchForm.target_name"
                placeholder="製品名を選択"
                clearable
                filterable
                class="filter-select"
              >
                <el-option
                  v-for="item in productOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="設備">
              <el-select
                v-model="searchForm.machine_name"
                placeholder="設備名を選択"
                clearable
                filterable
                class="filter-select"
              >
                <el-option
                  v-for="item in machineOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="生産日">
              <div class="date-input-group">
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  unlink-panels
                  range-separator="～"
                  start-placeholder="開始日"
                  end-placeholder="終了日"
                  format="YYYY/MM/DD"
                  value-format="YYYY-MM-DD"
                  :shortcuts="dateShortcuts"
                  @change="handleDateRangeChange"
                  class="date-picker"
                />
                <div class="quick-buttons">
                  <el-button size="small" class="date-btn yesterday" @click="shiftDay(-1)"
                    >前日</el-button
                  >
                  <el-button size="small" class="date-btn today" @click="setToday">今日</el-button>
                  <el-button size="small" class="date-btn tomorrow" @click="shiftDay(1)"
                    >翌日</el-button
                  >
                </div>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card class="process-card" shadow="hover">
      <template #header>
        <div class="process-card-header">
          <div class="title">
            <el-icon><Histogram /></el-icon>
            <span>工程別フィルタ</span>
          </div>
          <div v-if="typeSummary.length" class="type-summary-inline">
            <span class="inline-label">取引タイプ内訳</span>
            <div v-for="item in typeSummary" :key="item.transaction_type" class="type-chip">
              <span class="type-name">{{ item.transaction_type }}</span>
              <span class="type-values">
                {{ Number(item.record_count || 0).toLocaleString() }}件
                <span class="divider">/</span>
                {{ Number(item.total_quantity || 0).toLocaleString() }}
              </span>
            </div>
          </div>
          <span class="record-hint">対象件数: {{ stats.total_records.toLocaleString() }} 件</span>
        </div>
      </template>

      <el-tabs
        v-model="activeProcessTab"
        type="card"
        class="process-tabs"
        @tab-change="handleProcessTabChange"
      >
        <el-tab-pane
          v-for="tab in processTabs"
          :key="tab.process_cd"
          :name="tab.process_cd"
          :label="tab.process_name"
        />
      </el-tabs>

      <transition-group name="fade-slide" tag="div" class="stats-grid">
        <div v-for="card in statCards" :key="card.key" class="stat-card">
          <div class="stat-icon" :class="card.type">
            <component :is="card.icon" />
          </div>
          <div>
            <div class="stat-label">{{ card.label }}</div>
            <div class="stat-value">
              {{ card.value }}
              <small v-if="card.unit">{{ card.unit }}</small>
            </div>
          </div>
        </div>
      </transition-group>
    </el-card>

    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="table-header">
          <div class="table-title">
            <el-icon><List /></el-icon>
            <span>取引ログ一覧</span>
          </div>
          <div class="table-header-right">
            <el-tag type="info" size="small"> {{ pagination.total }} 件 </el-tag>
            <el-button
              type="primary"
              size="small"
              :icon="Printer"
              @click="handlePrintTable"
              class="print-table-btn"
            >
              取引ログ印刷
            </el-button>
            <el-button
              type="primary"
              size="small"
              :icon="Printer"
              @click="handlePrintMatrixTable"
              class="print-table-btn"
            >
              日別マトリクス印刷
            </el-button>
          </div>
        </div>
      </template>

      <el-skeleton v-if="loading" animated :rows="6" class="table-skeleton" />
      <template v-else>
        <el-table
          v-if="tableData.length"
          :data="tableData"
          stripe
          border
          max-height="520"
          class="data-table"
          @sort-change="handleSortChange"
        >
          <el-table-column
            prop="transaction_time"
            label="取引日時"
            width="150"
            align="center"
            sortable
            :sort-orders="['ascending', 'descending']"
          >
            <template #default="{ row }">
              {{ formatDateTime(row.transaction_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="process_cd" label="工程" width="120" align="center">
            <template #default="{ row }">
              <div class="process-info">
                <div class="process-name">{{ row.process_name || '-' }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="transaction_type" label="タイプ" width="90" align="center">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ row.transaction_type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="stock_type" label="区分" width="80" align="center" />
          <el-table-column prop="target_cd" label="製品CD" width="90" align="center">
            <template #default="{ row }">
              <span class="target-cd">{{ row.target_cd || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="target_name"
            label="製品名"
            min-width="130"
            sortable
            :sort-orders="['ascending', 'descending']"
          >
            <template #default="{ row }">
              <span class="target-name">{{ row.target_name || '-' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="数量" width="110" align="right">
            <template #default="{ row }">
              <span
                class="quantity"
                :class="{ 'is-negative': Number(row.quantity || 0) < 0 }"
              >
                {{ Number(row.quantity || 0).toLocaleString() }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="location_cd" label="保管場所" width="120" align="center" />
          <el-table-column
            prop="machine_name"
            label="設備名"
            width="150"
            align="center"
            sortable
            :sort-orders="['ascending', 'descending']"
          >
            <template #default="{ row }">
              <span class="machine-name">{{ row.machine_name || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="primary" size="small" text :icon="Edit" @click="handleEdit(row)">
                  編集
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  text
                  :icon="Delete"
                  @click="handleDelete(row)"
                >
                  削除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="該当データがありません" class="table-empty" />
      </template>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.limit"
          :page-sizes="[20, 50, 100, 200]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 分析チャートエリア -->
    <el-card class="chart-card" shadow="hover">
      <template #header>
        <div class="chart-header">
          <div class="chart-title">
            <el-icon><TrendCharts /></el-icon>
            <span>生産実績分析チャート</span>
          </div>
          <el-button
            type="primary"
            size="small"
            :icon="Printer"
            @click="handlePrintCharts"
            class="print-btn"
          >
            印刷
          </el-button>
        </div>
      </template>
      <div class="charts-grid">
        <div class="chart-item">
          <div class="chart-item-header">
            <span class="chart-item-title">日別生産量推移</span>
          </div>
          <div ref="dailyTrendChartRef" class="chart-container" style="height: 220px"></div>
        </div>
        <div class="chart-item">
          <div class="chart-item-header">
            <span class="chart-item-title">工程別生産量</span>
          </div>
          <div ref="processChartRef" class="chart-container" style="height: 220px"></div>
        </div>
        <div class="chart-item">
          <div class="chart-item-header">
            <span class="chart-item-title">取引タイプ分布</span>
          </div>
          <div ref="typeChartRef" class="chart-container" style="height: 220px"></div>
        </div>
        <div class="chart-item">
          <div class="chart-item-header">
            <span class="chart-item-title">製品生産量TOP10</span>
          </div>
          <div ref="productChartRef" class="chart-container" style="height: 220px"></div>
        </div>
      </div>
    </el-card>

    <!-- 編集ダイアログ -->
    <el-dialog
      v-model="editDialogVisible"
      title="取引ログ編集"
      width="480px"
      :close-on-click-modal="false"
      class="edit-dialog"
    >
      <div class="edit-dialog-content">
        <el-form ref="editFormRef" :model="editForm" :rules="editFormRules" label-width="90px">
          <div class="form-grid">
            <el-form-item label="取引日時" class="readonly-field">
              <el-input :model-value="formatDateTime(editForm.transaction_time)" disabled />
            </el-form-item>
            <el-form-item label="取引タイプ" class="readonly-field">
              <el-input :model-value="editForm.transaction_type" disabled>
                <template #prefix>
                  <el-tag size="small" type="info" style="border: none; background: transparent">
                    {{ editForm.transaction_type }}
                  </el-tag>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item label="区分" class="readonly-field">
              <el-input :model-value="editForm.stock_type || '-'" disabled />
            </el-form-item>
            <el-form-item label="製品コード" class="readonly-field">
              <el-input :model-value="editForm.target_cd" disabled />
            </el-form-item>
            <el-form-item label="製品名" class="readonly-field">
              <el-input :model-value="editForm.target_name || '-'" disabled />
            </el-form-item>
            <el-form-item label="数量" prop="quantity" class="editable-field">
              <el-input-number
                v-model="editForm.quantity"
                :min="0"
                :precision="0"
                :step="1"
                placeholder="数量を入力"
                style="width: 100%"
                controls-position="right"
              />
            </el-form-item>
            <el-form-item label="設備名" class="readonly-field">
              <el-input :model-value="editForm.machine_name || '-'" disabled />
            </el-form-item>
          </div>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editDialogVisible = false" size="small">キャンセル</el-button>
          <el-button type="primary" @click="handleSaveEdit" size="small" class="save-btn">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'ProductionActualManagement' })
import { ref, reactive, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Refresh,
  TrendCharts,
  Histogram,
  DataLine,
  CollectionTag,
  List,
  Edit,
  Delete,
  Printer,
} from '@element-plus/icons-vue'
import { fetchProcesses } from '@/api/master/processMaster'
import {
  getStockActualLogs,
  updateStockTransactionLog,
  deleteStockTransactionLog,
  type StockActualLogRecord,
  type StockActualStats,
  type StockActualTypeSummary,
} from '@/api/productionActualStockLogs'
import * as echarts from 'echarts'

const loading = ref(false)
const tableData = ref<StockActualLogRecord[]>([])
const processList = ref<any[]>([])
const activeProcessTab = ref('ALL')
const dateRange = ref<string[] | undefined>(undefined)
const stats = ref<StockActualStats>({
  total_records: 0,
  total_quantity: 0,
  avg_quantity: 0,
  product_count: 0,
  active_days: 0,
})
const typeSummary = ref<StockActualTypeSummary[]>([])

const pagination = reactive({
  page: 1,
  limit: 50,
  total: 0,
})

// ソート状態
const sortState = reactive({
  prop: '',
  order: '' as '' | 'ascending' | 'descending',
})

// 編集ダイアログ関連
const editDialogVisible = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive({
  id: 0,
  transaction_time: '',
  transaction_type: '',
  stock_type: '',
  target_cd: '',
  target_name: '',
  quantity: 0,
  location_cd: '',
  machine_cd: '',
  machine_name: '',
  related_doc_no: '',
})

const editFormRules: FormRules = {
  quantity: [
    { required: true, message: '数量を入力してください', trigger: 'blur' },
    { type: 'number', min: 0, message: '数量は0以上である必要があります', trigger: 'blur' },
  ],
}

// チャート関連
const dailyTrendChartRef = ref<HTMLDivElement>()
const processChartRef = ref<HTMLDivElement>()
const typeChartRef = ref<HTMLDivElement>()
const productChartRef = ref<HTMLDivElement>()

let dailyTrendChart: echarts.ECharts | null = null
let processChart: echarts.ECharts | null = null
let typeChart: echarts.ECharts | null = null
let productChart: echarts.ECharts | null = null

const searchForm = reactive({
  target_name: '',
  machine_name: '',
  date_from: '',
  date_to: '',
  process_cd: '',
  transaction_type: '実績',
})

let autoSearchTimer: ReturnType<typeof setTimeout> | null = null

const dateShortcuts = [
  {
    text: '過去7日',
    value: () => {
      const japanNow = getJapanDate()
      const end = new Date(japanNow)
      const start = new Date(japanNow)
      start.setDate(start.getDate() - 6)
      return [start, end]
    },
  },
  {
    text: '過去30日',
    value: () => {
      const japanNow = getJapanDate()
      const end = new Date(japanNow)
      const start = new Date(japanNow)
      start.setDate(start.getDate() - 29)
      return [start, end]
    },
  },
]

const allowedProcessesOrder = [
  '切断',
  '面取',
  '成型',
  'メッキ',
  '外注メッキ',
  '溶接',
  '外注溶接',
  '検査',
  '溶接前検査',
  '倉庫',
]

const processTabs = computed(() => {
  const availableMap = new Map<string, any>()
  processList.value
    .filter((p) => p.process_cd)
    .forEach((p: any) => {
      const key = p.process_name || p.process_cd
      availableMap.set(key, p)
    })

  const orderedTabs = allowedProcessesOrder
    .map((name) => {
      const process = availableMap.get(name)
      if (!process) return null
      return {
        process_cd: process.process_cd,
        process_name: process.process_name || process.process_cd,
      }
    })
    .filter((tab): tab is { process_cd: string; process_name: string } => Boolean(tab))

  return [{ process_cd: 'ALL', process_name: '全工程' }, ...orderedTabs]
})

const formatNumber = (value: number | undefined, fraction = 0) => {
  const num = Number(value || 0)
  return num.toLocaleString(undefined, {
    minimumFractionDigits: fraction,
    maximumFractionDigits: fraction,
  })
}

const statCards = computed(() => {
  const s = stats.value
  return [
    {
      key: 'records',
      label: '総レコード',
      value: formatNumber(s.total_records),
      unit: '件',
      icon: CollectionTag,
      type: 'primary',
    },
    {
      key: 'quantity',
      label: '数量合計',
      value: formatNumber(s.total_quantity),
      unit: '本',
      icon: DataLine,
      type: 'success',
    },
    {
      key: 'avg',
      label: '平均数量/件',
      value: formatNumber(s.avg_quantity, 1),
      unit: '本/件',
      icon: Histogram,
      type: 'warning',
    },
    {
      key: 'products',
      label: '対象製品数',
      value: formatNumber(s.product_count),
      unit: '品目',
      icon: TrendCharts,
      type: 'info',
    },
    {
      key: 'days',
      label: '稼働日数',
      value: formatNumber(s.active_days),
      unit: '日',
      icon: List,
      type: 'neutral',
    },
  ]
})

// 日本时区日期格式化工具函数
const getJapanDate = (date?: Date) => {
  if (!date) return new Date()
  // 日本時区のオフセット（UTC+9）を適用
  const utc = date.getTime() + date.getTimezoneOffset() * 60000
  const japanTime = new Date(utc + 9 * 3600000)
  return japanTime
}

const formatDateString = (date?: Date) => {
  if (!date) {
    const now = new Date()
    const japanDate = getJapanDate(now)
    const year = japanDate.getFullYear()
    const month = `${japanDate.getMonth() + 1}`.padStart(2, '0')
    const day = `${japanDate.getDate()}`.padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  // 文字列の場合は直接解析
  if (typeof date === 'string') {
    const d = new Date(date)
    const japanDate = getJapanDate(d)
    const year = japanDate.getFullYear()
    const month = `${japanDate.getMonth() + 1}`.padStart(2, '0')
    const day = `${japanDate.getDate()}`.padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const japanDate = getJapanDate(date)
  const year = japanDate.getFullYear()
  const month = `${japanDate.getMonth() + 1}`.padStart(2, '0')
  const day = `${japanDate.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

const updateSingleDate = (value: string) => {
  dateRange.value = [value, value]
  searchForm.date_from = value
  searchForm.date_to = value
}

const setDefaultDateRange = () => {
  const today = formatDateString(new Date())
  updateSingleDate(today)
}

setDefaultDateRange()

const shiftDay = (delta: number) => {
  const base = searchForm.date_from || formatDateString()
  const baseDate = getJapanDate(new Date(`${base}T00:00:00+09:00`))
  baseDate.setDate(baseDate.getDate() + delta)
  updateSingleDate(formatDateString(baseDate))
}

const setToday = () => {
  updateSingleDate(formatDateString())
}

const loadProcesses = async () => {
  try {
    const response = await fetchProcesses({ page: 1, pageSize: 500 })
    processList.value = response.list || []
  } catch (error) {
    console.error('工程データ取得失敗:', error)
    ElMessage.error('工程マスタの取得に失敗しました')
  }
}

// チャート初期化関数
const initCharts = () => {
  nextTick(() => {
    setTimeout(() => {
      if (dailyTrendChartRef.value && !dailyTrendChart) {
        dailyTrendChart = echarts.init(dailyTrendChartRef.value)
      }
      if (processChartRef.value && !processChart) {
        processChart = echarts.init(processChartRef.value)
      }
      if (typeChartRef.value && !typeChart) {
        typeChart = echarts.init(typeChartRef.value)
      }
      if (productChartRef.value && !productChart) {
        productChart = echarts.init(productChartRef.value)
      }
      // データが読み込まれている場合のみ更新
      if (chartData.value.length > 0 || typeSummary.value.length > 0) {
        updateCharts()
      }
    }, 300)
  })
}

// チャート用データ取得
const chartData = ref<StockActualLogRecord[]>([])

const productOptions = computed(() => {
  const names = new Set<string>()
  ;[...chartData.value, ...tableData.value].forEach((item) => {
    const name = String(item.target_name || '').trim()
    if (name) names.add(name)
  })
  return Array.from(names)
    .sort((a, b) => a.localeCompare(b, 'ja'))
    .map((name) => ({ label: name, value: name }))
})

const machineOptions = computed(() => {
  const names = new Set<string>()
  ;[...chartData.value, ...tableData.value].forEach((item) => {
    const name = String(item.machine_name || '').trim()
    if (name) names.add(name)
  })
  return Array.from(names)
    .sort((a, b) => a.localeCompare(b, 'ja'))
    .map((name) => ({ label: name, value: name }))
})

const loadChartData = async () => {
  try {
    const params = {
      page: 1,
      limit: 500, // チャート用（API 上限 500 で確実に通す。バックエンドを le=10000 にした場合は 5000 等に変更可）
      process_cd: searchForm.process_cd || undefined,
      transaction_type: searchForm.transaction_type || undefined,
      target_name: searchForm.target_name || undefined,
      machine_name: searchForm.machine_name || undefined,
      date_from: searchForm.date_from || undefined,
      date_to: searchForm.date_to || undefined,
    }
    const response = await getStockActualLogs(params)
    if (response?.success && response.data) {
      chartData.value = response.data.list || []
      // データ読み込み後、チャートを更新
      nextTick(() => {
        updateCharts()
      })
    } else {
      chartData.value = []
      // データがない場合もチャートを更新（空データ表示）
      nextTick(() => {
        updateCharts()
      })
    }
  } catch (error: any) {
    console.error('チャートデータ取得失敗:', error)
    chartData.value = []

    // 如果是token错误，不显示额外的错误消息（request.ts已经处理了）
    if (error.isTokenError || error.response?.status === 403) {
      // Token错误或权限错误，request.ts已经显示了错误消息
      return
    }
    nextTick(() => {
      updateCharts()
    })
  }
}

// チャート更新関数
const updateCharts = () => {
  // チャートが初期化されていない場合は初期化を試みる
  if (!dailyTrendChart && dailyTrendChartRef.value) {
    dailyTrendChart = echarts.init(dailyTrendChartRef.value)
  }
  if (!processChart && processChartRef.value) {
    processChart = echarts.init(processChartRef.value)
  }
  if (!typeChart && typeChartRef.value) {
    typeChart = echarts.init(typeChartRef.value)
  }
  if (!productChart && productChartRef.value) {
    productChart = echarts.init(productChartRef.value)
  }

  // 日別生産量推移チャート - 全データを使用
  if (dailyTrendChart) {
    if (chartData.value.length === 0) {
      dailyTrendChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: '10%', right: '10%', top: '15%', bottom: '15%' },
        xAxis: { type: 'category', data: [] },
        yAxis: { type: 'value' },
        series: [{ name: '生産量', type: 'line', data: [] }],
      })
    } else {
      const dailyData = new Map<string, number>()

      // データから日付別に数量を集計
      chartData.value.forEach((item) => {
        // transaction_timeから日付部分（YYYY-MM-DD）を直接抽出
        // transaction_timeは文字列型なので、直接文字列から抽出
        let dateStr = ''
        const timeStr = String(item.transaction_time || '')

        // YYYY-MM-DD HH:mm:ss または YYYY-MM-DDTHH:mm:ss 形式から日付部分を抽出
        const match = timeStr.match(/^(\d{4}-\d{2}-\d{2})/)
        if (match) {
          dateStr = match[1]
        } else if (timeStr) {
          // フォールバック: 文字列をDateに変換してから日付部分を抽出
          try {
            const date = new Date(timeStr)
            if (!isNaN(date.getTime())) {
              // 日付を取得（ローカル時区）
              const year = date.getFullYear()
              const month = `${date.getMonth() + 1}`.padStart(2, '0')
              const day = `${date.getDate()}`.padStart(2, '0')
              dateStr = `${year}-${month}-${day}`
            }
          } catch (e) {
            console.warn('日付解析エラー:', timeStr, e)
          }
        }

        if (dateStr) {
          const quantity = Number(item.quantity) || 0
          dailyData.set(dateStr, (dailyData.get(dateStr) || 0) + quantity)
        }
      })

      // 筛选日期范围内的所有日期を生成（YYYY-MM-DD形式で直接生成）
      let dates: string[] = []
      if (searchForm.date_from && searchForm.date_to) {
        // 日付文字列を直接解析（YYYY-MM-DD形式）
        const startParts = searchForm.date_from.split('-')
        const endParts = searchForm.date_to.split('-')

        if (startParts.length === 3 && endParts.length === 3) {
          const startYear = parseInt(startParts[0], 10)
          const startMonth = parseInt(startParts[1], 10) - 1 // 月は0ベース
          const startDay = parseInt(startParts[2], 10)

          const endYear = parseInt(endParts[0], 10)
          const endMonth = parseInt(endParts[1], 10) - 1
          const endDay = parseInt(endParts[2], 10)

          const startDate = new Date(startYear, startMonth, startDay, 0, 0, 0, 0)
          const endDate = new Date(endYear, endMonth, endDay, 23, 59, 59, 999)
          const currentDate = new Date(startDate)

          // 日付を文字列として比較するためのヘルパー関数
          const formatDateForCompare = (date: Date) => {
            const year = date.getFullYear()
            const month = `${date.getMonth() + 1}`.padStart(2, '0')
            const day = `${date.getDate()}`.padStart(2, '0')
            return `${year}-${month}-${day}`
          }

          const endDateStr = formatDateForCompare(endDate)
          let loopCount = 0
          const maxDays = 365 // 安全のための最大ループ回数

          while (loopCount < maxDays) {
            const dateStr = formatDateForCompare(currentDate)
            dates.push(dateStr)

            // 終了日付に達したら終了
            if (dateStr >= endDateStr) {
              break
            }

            currentDate.setDate(currentDate.getDate() + 1)
            loopCount++
          }
        }
      } else {
        // 日付範囲がない場合は、データから日付を取得してソート
        dates = Array.from(dailyData.keys()).sort()
      }

      const quantities = dates.map((date) => dailyData.get(date) || 0)

      // デバッグ用ログ（開発時のみ）
      if (process.env.NODE_ENV === 'development') {
        const dateRangeDays = dates.length
        const dataDates = Array.from(dailyData.keys()).sort()
        const missingDates = dates.filter((date) => !dailyData.has(date))
        const extraDates = dataDates.filter((date) => !dates.includes(date))

        console.log('日別生産量推移データ:', {
          dateRange: {
            from: searchForm.date_from,
            to: searchForm.date_to,
            days: dateRangeDays,
          },
          dates: {
            total: dates.length,
            first: dates[0],
            last: dates[dates.length - 1],
            all: dates,
          },
          quantities: {
            total: quantities.length,
            sum: quantities.reduce((a, b) => a + b, 0),
            max: Math.max(...quantities, 0),
            all: quantities,
          },
          dailyData: {
            total: dailyData.size,
            entries: Array.from(dailyData.entries()),
          },
          chartDataCount: chartData.value.length,
          dataDates: {
            total: dataDates.length,
            first: dataDates[0],
            last: dataDates[dataDates.length - 1],
          },
          issues: {
            missingDates: missingDates.length > 0 ? missingDates : 'なし',
            extraDates: extraDates.length > 0 ? extraDates : 'なし',
          },
          sampleData: chartData.value.slice(0, 10).map((item) => {
            let extractedDate = ''
            if (typeof item.transaction_time === 'string') {
              const match = item.transaction_time.match(/^(\d{4}-\d{2}-\d{2})/)
              extractedDate = match ? match[1] : 'N/A'
            }
            return {
              transaction_time: item.transaction_time,
              extractedDate,
              quantity: item.quantity,
            }
          }),
        })
      }

      const maxValue = Math.max(...quantities, 1)
      dailyTrendChart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'line',
            lineStyle: {
              color: '#3b82f6',
              width: 2,
              type: 'dashed',
            },
            label: {
              backgroundColor: '#3b82f6',
              color: '#fff',
            },
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: {
            color: '#1f2937',
            fontSize: 12,
          },
          padding: [8, 12],
          formatter: (params: any) => {
            const param = params[0]
            return `
              <div style="font-weight: 600; margin-bottom: 4px;">${param.axisValue}</div>
              <div style="display: flex; align-items: center;">
                <span style="display: inline-block; width: 10px; height: 10px; background: #3b82f6; border-radius: 50%; margin-right: 6px;"></span>
                <span style="font-weight: 600;">${param.seriesName}: ${param.value.toLocaleString()} 本</span>
              </div>
            `
          },
        },
        grid: {
          left: '12%',
          right: '8%',
          top: '18%',
          bottom: '20%',
          containLabel: false,
        },
        xAxis: {
          type: 'category',
          data: dates,
          axisLabel: {
            fontSize: 11,
            rotate: 45,
            color: '#6b7280',
            margin: 12,
            formatter: (value: string) => {
              // YYYY-MM-DD を MM-DD に変換
              if (value && value.includes('-')) {
                const parts = value.split('-')
                if (parts.length === 3) {
                  return `${parts[1]}-${parts[2]}`
                }
              }
              return value
            },
          },
          axisLine: {
            lineStyle: {
              color: '#e5e7eb',
              width: 1,
            },
          },
          axisTick: {
            show: false,
          },
          splitLine: {
            show: false,
          },
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            fontSize: 11,
            color: '#6b7280',
            formatter: (value: number) => {
              if (value >= 1000) {
                return (value / 1000).toFixed(1) + 'K'
              }
              return value.toString()
            },
          },
          axisLine: {
            show: false,
          },
          axisTick: {
            show: false,
          },
          splitLine: {
            lineStyle: {
              color: '#f3f4f6',
              width: 1,
              type: 'dashed',
            },
          },
        },
        series: [
          {
            name: '生産量',
            type: 'line',
            data: quantities,
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            showSymbol: quantities.length <= 30,
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(59, 130, 246, 0.4)' },
                { offset: 0.5, color: 'rgba(59, 130, 246, 0.15)' },
                { offset: 1, color: 'rgba(59, 130, 246, 0.02)' },
              ]),
            },
            lineStyle: {
              color: '#3b82f6',
              width: 3,
              shadowColor: 'rgba(59, 130, 246, 0.3)',
              shadowBlur: 8,
            },
            itemStyle: {
              color: '#3b82f6',
              borderColor: '#fff',
              borderWidth: 2,
              shadowColor: 'rgba(59, 130, 246, 0.5)',
              shadowBlur: 4,
            },
            label: {
              show: maxValue > 0 && quantities.length <= 15,
              position: 'top',
              fontSize: 10,
              color: '#3b82f6',
              fontWeight: 600,
              formatter: (params: any) => params.value.toLocaleString(),
            },
            emphasis: {
              focus: 'series',
              itemStyle: {
                shadowBlur: 10,
                shadowColor: 'rgba(59, 130, 246, 0.8)',
              },
            },
          },
        ],
      })
    }
  }

  // 工程別生産量チャート - 全データを使用
  if (processChart) {
    if (chartData.value.length === 0) {
      processChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: '15%', right: '10%', top: '15%', bottom: '15%' },
        xAxis: { type: 'value' },
        yAxis: { type: 'category', data: [] },
        series: [{ name: '生産量', type: 'bar', data: [] }],
      })
    } else {
      const processData = new Map<string, number>()
      chartData.value.forEach((item) => {
        const processName = item.process_name || '不明'
        processData.set(processName, (processData.get(processName) || 0) + Number(item.quantity))
      })
      const processNames = Array.from(processData.keys())
      const processQuantities = processNames.map((name) => processData.get(name) || 0)

      const maxProcessValue = Math.max(...processQuantities, 1)
      const colors = [
        ['#3b82f6', '#60a5fa'],
        ['#8b5cf6', '#a78bfa'],
        ['#ec4899', '#f472b6'],
        ['#f59e0b', '#fbbf24'],
        ['#10b981', '#34d399'],
        ['#06b6d4', '#22d3ee'],
        ['#ef4444', '#f87171'],
        ['#6366f1', '#818cf8'],
      ]

      processChart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow',
            shadowStyle: {
              color: 'rgba(59, 130, 246, 0.1)',
            },
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: {
            color: '#1f2937',
            fontSize: 12,
          },
          padding: [8, 12],
          formatter: (params: any) => {
            const param = params[0]
            return `
              <div style="font-weight: 600; margin-bottom: 4px;">${param.name}</div>
              <div style="display: flex; align-items: center;">
                <span style="display: inline-block; width: 10px; height: 10px; background: linear-gradient(90deg, ${colors[0][0]}, ${colors[0][1]}); border-radius: 2px; margin-right: 6px;"></span>
                <span style="font-weight: 600;">${param.seriesName}: ${param.value.toLocaleString()} 本</span>
              </div>
            `
          },
        },
        grid: {
          left: '18%',
          right: '8%',
          top: '12%',
          bottom: '12%',
          containLabel: false,
        },
        xAxis: {
          type: 'value',
          axisLabel: {
            fontSize: 11,
            color: '#6b7280',
            formatter: (value: number) => {
              if (value >= 1000) {
                return (value / 1000).toFixed(1) + 'K'
              }
              return value.toString()
            },
          },
          axisLine: {
            show: false,
          },
          axisTick: {
            show: false,
          },
          splitLine: {
            lineStyle: {
              color: '#f3f4f6',
              width: 1,
              type: 'dashed',
            },
          },
        },
        yAxis: {
          type: 'category',
          data: processNames,
          axisLabel: {
            fontSize: 11,
            color: '#374151',
            fontWeight: 500,
          },
          axisLine: {
            lineStyle: {
              color: '#e5e7eb',
              width: 1,
            },
          },
          axisTick: {
            show: false,
          },
        },
        series: [
          {
            name: '生産量',
            type: 'bar',
            data: processQuantities,
            barWidth: '60%',
            barGap: '20%',
            itemStyle: {
              color: (params: any) => {
                const index = params.dataIndex % colors.length
                return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                  { offset: 0, color: colors[index][0] },
                  { offset: 1, color: colors[index][1] },
                ])
              },
              borderRadius: [0, 6, 6, 0],
              shadowColor: 'rgba(0, 0, 0, 0.1)',
              shadowBlur: 4,
              shadowOffsetY: 2,
            },
            label: {
              show: true,
              position: 'right',
              fontSize: 10,
              color: '#374151',
              fontWeight: 600,
              formatter: (params: any) => {
                const percentage =
                  maxProcessValue > 0 ? ((params.value / maxProcessValue) * 100).toFixed(0) : 0
                return `${params.value.toLocaleString()} (${percentage}%)`
              },
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 8,
                shadowColor: 'rgba(59, 130, 246, 0.4)',
              },
            },
          },
        ],
      })
    }
  }

  // 取引タイプ分布チャート
  if (typeChart) {
    if (typeSummary.value.length === 0) {
      typeChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { orient: 'vertical', left: 'left', top: 'middle' },
        series: [{ name: '取引タイプ', type: 'pie', radius: ['40%', '70%'], data: [] }],
      })
    } else {
      const totalQuantity = typeSummary.value.reduce((sum, item) => sum + item.total_quantity, 0)
      const pieColors = [
        '#3b82f6',
        '#8b5cf6',
        '#ec4899',
        '#f59e0b',
        '#10b981',
        '#06b6d4',
        '#ef4444',
        '#6366f1',
        '#14b8a6',
        '#f97316',
      ]

      typeChart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: {
            color: '#1f2937',
            fontSize: 12,
          },
          padding: [10, 14],
          formatter: (params: any) => {
            const percentage =
              totalQuantity > 0 ? ((params.value / totalQuantity) * 100).toFixed(1) : 0
            return `
              <div style="font-weight: 600; margin-bottom: 6px; font-size: 13px;">${params.name}</div>
              <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="display: inline-block; width: 12px; height: 12px; background: ${params.color}; border-radius: 3px; margin-right: 8px;"></span>
                <span style="font-weight: 600; color: #1f2937;">数量: ${params.value.toLocaleString()} 本</span>
              </div>
              <div style="color: #6b7280; font-size: 11px;">占比: ${percentage}%</div>
            `
          },
        },
        legend: {
          orient: 'vertical',
          left: '5%',
          top: 'center',
          itemWidth: 12,
          itemHeight: 12,
          itemGap: 10,
          textStyle: {
            fontSize: 11,
            color: '#374151',
            fontWeight: 500,
          },
          formatter: (name: string) => {
            const item = typeSummary.value.find((i) => i.transaction_type === name)
            if (item) {
              const percentage =
                totalQuantity > 0 ? ((item.total_quantity / totalQuantity) * 100).toFixed(1) : 0
              return `${name} (${percentage}%)`
            }
            return name
          },
        },
        series: [
          {
            name: '取引タイプ',
            type: 'pie',
            radius: ['45%', '75%'],
            center: ['65%', '50%'],
            avoidLabelOverlap: true,
            itemStyle: {
              borderRadius: 6,
              borderColor: '#fff',
              borderWidth: 3,
              shadowColor: 'rgba(0, 0, 0, 0.1)',
              shadowBlur: 6,
              shadowOffsetY: 2,
            },
            label: {
              show: true,
              position: 'outside',
              fontSize: 11,
              color: '#374151',
              fontWeight: 500,
              formatter: (params: any) => {
                const percentage =
                  totalQuantity > 0 ? ((params.value / totalQuantity) * 100).toFixed(1) : 0
                return `${params.name}\n${percentage}%`
              },
              rich: {
                name: {
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#1f2937',
                },
                percent: {
                  fontSize: 10,
                  color: '#6b7280',
                },
              },
            },
            labelLine: {
              show: true,
              length: 15,
              length2: 10,
              lineStyle: {
                color: '#d1d5db',
                width: 1,
              },
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 12,
                shadowOffsetX: 0,
                shadowOffsetY: 0,
                shadowColor: 'rgba(0, 0, 0, 0.2)',
              },
              label: {
                fontSize: 12,
                fontWeight: 700,
              },
              scale: true,
              scaleSize: 5,
            },
            data: typeSummary.value.map((item, index) => ({
              value: item.total_quantity,
              name: item.transaction_type,
              itemStyle: {
                color: pieColors[index % pieColors.length],
              },
            })),
          },
        ],
      })
    }
  }

  // 製品生産量TOP10チャート - 全データを使用
  if (productChart) {
    if (chartData.value.length === 0) {
      productChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: '20%', right: '10%', top: '15%', bottom: '15%' },
        xAxis: { type: 'value' },
        yAxis: { type: 'category', data: [] },
        series: [{ name: '生産量', type: 'bar', data: [] }],
      })
    } else {
      const productData = new Map<string, number>()
      chartData.value.forEach((item) => {
        const productName = item.target_name || item.target_cd || '不明'
        productData.set(productName, (productData.get(productName) || 0) + Number(item.quantity))
      })
      const sortedProducts = Array.from(productData.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
      const productNames = sortedProducts.map(([name]) =>
        name.length > 15 ? name.substring(0, 15) + '...' : name,
      )
      const productQuantities = sortedProducts.map(([, qty]) => qty)

      const maxProductValue = Math.max(...productQuantities, 1)
      const top10Colors = [
        ['#10b981', '#34d399'],
        ['#3b82f6', '#60a5fa'],
        ['#8b5cf6', '#a78bfa'],
        ['#ec4899', '#f472b6'],
        ['#f59e0b', '#fbbf24'],
        ['#06b6d4', '#22d3ee'],
        ['#ef4444', '#f87171'],
        ['#6366f1', '#818cf8'],
        ['#14b8a6', '#5eead4'],
        ['#f97316', '#fb923c'],
      ]

      productChart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow',
            shadowStyle: {
              color: 'rgba(16, 185, 129, 0.1)',
            },
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: {
            color: '#1f2937',
            fontSize: 12,
          },
          padding: [8, 12],
          formatter: (params: any) => {
            const param = params[0]
            const rank = sortedProducts.findIndex((p) => p[1] === param.value) + 1
            return `
              <div style="display: flex; align-items: center; margin-bottom: 6px;">
                <span style="display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: linear-gradient(135deg, #10b981, #34d399); color: #fff; border-radius: 50%; font-weight: 700; font-size: 11px; margin-right: 8px;">${rank}</span>
                <span style="font-weight: 600; font-size: 13px;">${param.name}</span>
              </div>
              <div style="display: flex; align-items: center;">
                <span style="display: inline-block; width: 10px; height: 10px; background: linear-gradient(90deg, #10b981, #34d399); border-radius: 2px; margin-right: 6px;"></span>
                <span style="font-weight: 600;">${param.seriesName}: ${param.value.toLocaleString()} 本</span>
              </div>
            `
          },
        },
        grid: {
          left: '22%',
          right: '8%',
          top: '12%',
          bottom: '12%',
          containLabel: false,
        },
        xAxis: {
          type: 'value',
          axisLabel: {
            fontSize: 11,
            color: '#6b7280',
            formatter: (value: number) => {
              if (value >= 1000) {
                return (value / 1000).toFixed(1) + 'K'
              }
              return value.toString()
            },
          },
          axisLine: {
            show: false,
          },
          axisTick: {
            show: false,
          },
          splitLine: {
            lineStyle: {
              color: '#f3f4f6',
              width: 1,
              type: 'dashed',
            },
          },
        },
        yAxis: {
          type: 'category',
          data: productNames,
          axisLabel: {
            fontSize: 11,
            color: '#374151',
            fontWeight: 500,
          },
          axisLine: {
            lineStyle: {
              color: '#e5e7eb',
              width: 1,
            },
          },
          axisTick: {
            show: false,
          },
        },
        series: [
          {
            name: '生産量',
            type: 'bar',
            data: productQuantities,
            barWidth: '55%',
            itemStyle: {
              color: (params: any) => {
                const rank = params.dataIndex + 1
                if (rank === 1) {
                  return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: '#ef4444' },
                    { offset: 1, color: '#f87171' },
                  ])
                }
                if (rank === 2) {
                  return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: '#f59e0b' },
                    { offset: 1, color: '#fbbf24' },
                  ])
                }
                if (rank === 3) {
                  return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: '#10b981' },
                    { offset: 1, color: '#34d399' },
                  ])
                }
                const index = params.dataIndex % top10Colors.length
                return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                  { offset: 0, color: top10Colors[index][0] },
                  { offset: 1, color: top10Colors[index][1] },
                ])
              },
              borderRadius: [0, 6, 6, 0],
              shadowColor: 'rgba(0, 0, 0, 0.1)',
              shadowBlur: 4,
              shadowOffsetY: 2,
            },
            label: {
              show: true,
              position: 'right',
              fontSize: 10,
              color: '#374151',
              fontWeight: 600,
              formatter: (params: any) => {
                const percentage =
                  maxProductValue > 0 ? ((params.value / maxProductValue) * 100).toFixed(0) : 0
                return `${params.value.toLocaleString()} (${percentage}%)`
              },
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 8,
                shadowColor: 'rgba(16, 185, 129, 0.4)',
              },
            },
          },
        ],
      })
    }
  }
}

const loadData = async () => {
  try {
    loading.value = true
    const params: any = {
      page: pagination.page,
      limit: pagination.limit,
      process_cd: searchForm.process_cd || undefined,
      transaction_type: searchForm.transaction_type || undefined,
      target_name: searchForm.target_name || undefined,
      machine_name: searchForm.machine_name || undefined,
      date_from: searchForm.date_from || undefined,
      date_to: searchForm.date_to || undefined,
    }

    // ソートパラメータを追加
    if (sortState.prop && sortState.order) {
      params.sort_by = sortState.prop
      params.sort_order = sortState.order === 'ascending' ? 'ASC' : 'DESC'
    }
    const response = await getStockActualLogs(params)
    const apiMessage = response && 'message' in response ? (response as any).message : ''
    if (response?.success && response.data) {
      tableData.value = response.data.list || []
      stats.value = response.data.stats
      typeSummary.value = response.data.typeSummary || []
      pagination.total = response.data.pagination?.total || 0
    } else {
      tableData.value = []
      pagination.total = 0
      ElMessage.warning(apiMessage || 'データ取得に失敗しました')
    }
    // チャート用データ取得（全データ）
    await loadChartData()
    // チャート更新
    updateCharts()
  } catch (error: any) {
    console.error('stock_transaction_logs取得失敗:', error)
    tableData.value = []
    pagination.total = 0

    // 如果是token错误，不显示额外的错误消息（request.ts已经处理了）
    if (error.isTokenError || error.response?.status === 403) {
      // Token错误或权限错误，request.ts已经显示了错误消息
      return
    }

    // 其他错误显示通用错误消息
    const errorMsg = error.response?.data?.message || error.message || 'データの取得に失敗しました'
    if (!error.isSilentError) {
      ElMessage.error(errorMsg)
    }
  } finally {
    loading.value = false
  }
}

const handleDateRangeChange = (value: string[] | null) => {
  if (value && value.length === 2) {
    searchForm.date_from = value[0]
    searchForm.date_to = value[1]
  } else {
    searchForm.date_from = ''
    searchForm.date_to = ''
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  sortState.prop = prop || ''
  sortState.order = (order || '') as '' | 'ascending' | 'descending'
  pagination.page = 1 // ソート時は最初のページに戻る
  loadData()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadData()
}

const handlePageSizeChange = (size: number) => {
  pagination.limit = size
  pagination.page = 1
  loadData()
}

const handleProcessTabChange = (name: string | number) => {
  const processCode = String(name)
  activeProcessTab.value = processCode
  searchForm.process_cd = processCode === 'ALL' ? '' : processCode
  pagination.page = 1
  loadData()
}

const handleRefresh = () => {
  loadData()
}

// 編集処理
const handleEdit = (row: StockActualLogRecord) => {
  editForm.id = row.id
  editForm.transaction_time = row.transaction_time || ''
  editForm.transaction_type = row.transaction_type || ''
  editForm.stock_type = row.stock_type || ''
  editForm.target_cd = row.target_cd || ''
  editForm.target_name = row.target_name || ''
  editForm.quantity = Number(row.quantity) || 0
  editForm.location_cd = row.location_cd || ''
  editForm.machine_cd = row.machine_cd || ''
  editForm.machine_name = row.machine_name || ''
  editForm.related_doc_no = row.related_doc_no || ''
  editDialogVisible.value = true
}

// 保存編集
const handleSaveEdit = async () => {
  if (!editFormRef.value) return
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const response = await updateStockTransactionLog(editForm.id, {
          transaction_time: editForm.transaction_time,
          transaction_type: editForm.transaction_type,
          stock_type: editForm.stock_type,
          target_cd: editForm.target_cd,
          quantity: editForm.quantity,
          location_cd: editForm.location_cd,
          machine_cd: editForm.machine_cd,
          related_doc_no: editForm.related_doc_no,
        })
        if (response?.success) {
          ElMessage.success('更新に成功しました')
          editDialogVisible.value = false
          loadData()
        } else {
          ElMessage.error('更新に失敗しました')
        }
      } catch (error) {
        console.error('更新失敗:', error)
        ElMessage.error('更新に失敗しました')
      }
    }
  })
}

// 削除処理
const handleDelete = async (row: StockActualLogRecord) => {
  try {
    await ElMessageBox.confirm(`取引ログ（ID: ${row.id}）を削除しますか？`, '削除確認', {
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })
    const response = await deleteStockTransactionLog(row.id)
    if (response?.success) {
      ElMessage.success('削除に成功しました')
      loadData()
    } else {
      ElMessage.error('削除に失敗しました')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('削除失敗:', error)
      ElMessage.error('削除に失敗しました')
    }
  }
}

const formatDateTime = (value: string | undefined) => {
  if (!value) return '-'
  const date = new Date(value)
  return date.toLocaleString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

/** 印刷用 HTML エスケープ */
const escapeHtmlText = (raw: string) =>
  raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')

/** 取引日時から日付キー（YYYY-MM-DD）を取得 */
const transactionDateKey = (row: StockActualLogRecord): string => {
  const t = row.transaction_time
  if (!t) return ''
  const s = String(t)
  const m = s.match(/^(\d{4}-\d{2}-\d{2})/)
  if (m) return m[1]
  return formatDateString(new Date(s))
}

/** YYYY-MM-DD を表示用 M/D に短縮 */
const formatShortDateHeader = (ymd: string) => {
  const p = ymd.split('-')
  if (p.length !== 3) return ymd
  return `${Number(p[1])}/${Number(p[2])}`
}

// ウィンドウリサイズ処理
const handleResize = () => {
  dailyTrendChart?.resize()
  processChart?.resize()
  typeChart?.resize()
  productChart?.resize()
}

// チャート印刷処理
const handlePrintCharts = async () => {
  try {
    // すべてのチャートが初期化されているか確認
    if (!dailyTrendChart || !processChart || !typeChart || !productChart) {
      ElMessage.warning('チャートがまだ読み込まれていません。しばらくお待ちください。')
      return
    }

    // チャートを画像に変換
    const dailyTrendImage = dailyTrendChart.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff',
    })
    const processImage = processChart.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff',
    })
    const typeImage = typeChart.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff',
    })
    const productImage = productChart.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff',
    })

    // 印刷用HTMLを作成
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('ポップアップがブロックされています。ブラウザの設定を確認してください。')
      return
    }

    const dateRange =
      searchForm.date_from && searchForm.date_to
        ? `${searchForm.date_from} ～ ${searchForm.date_to}`
        : '全期間'

    // フィルタ情報を構築
    const filterInfo: string[] = []

    // 工程フィルタ
    if (searchForm.process_cd) {
      const process = processList.value.find((p) => p.process_cd === searchForm.process_cd)
      if (process && process.process_name) {
        filterInfo.push('工程: ' + process.process_name)
      } else if (searchForm.process_cd) {
        filterInfo.push('工程: ' + searchForm.process_cd)
      }
    } else if (activeProcessTab.value === 'ALL') {
      filterInfo.push('工程: 全工程')
    }

    // 取引タイプフィルタ
    if (
      searchForm.transaction_type &&
      searchForm.transaction_type !== 'ALL' &&
      searchForm.transaction_type !== '実績'
    ) {
      filterInfo.push('取引タイプ: ' + searchForm.transaction_type)
    }

    // キーワードフィルタ
    if (searchForm.target_name) {
      filterInfo.push('製品名: ' + searchForm.target_name)
    }
    if (searchForm.machine_name) {
      filterInfo.push('設備: ' + searchForm.machine_name)
    }

    const filterText = filterInfo.length > 0 ? filterInfo.join(' | ') : ''

    // HTML文字列を構築（Vueテンプレートパーサーを回避するため、文字列連結を使用）
    const htmlParts: string[] = []
    htmlParts.push('<!DOCTYPE html>')
    htmlParts.push('<html>')
    htmlParts.push('<head>')
    htmlParts.push('<meta charset="UTF-8">')
    htmlParts.push('<title>生産実績分析チャート</title>')
    htmlParts.push('<style>')
    htmlParts.push('@page { size: A4 landscape; margin: 15mm; }')
    htmlParts.push('* { margin: 0; padding: 0; box-sizing: border-box; }')
    htmlParts.push(
      'body { font-family: "游ゴシック", "Yu Gothic", "YuGothic", "Meiryo", "メイリオ", sans-serif; padding: 20px; background: #fff; }',
    )
    htmlParts.push(
      '.print-header { text-align: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #3b82f6; }',
    )
    htmlParts.push(
      '.print-title { font-size: 24px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }',
    )
    htmlParts.push('.print-date { font-size: 14px; color: #6b7280; margin-bottom: 4px; }')
    htmlParts.push('.print-filters { font-size: 13px; color: #475569; margin-top: 4px; }')
    htmlParts.push(
      '.charts-container { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 20px; }',
    )
    htmlParts.push(
      '.chart-print-item { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px; page-break-inside: avoid; }',
    )
    htmlParts.push(
      '.chart-print-title { font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #f1f5f9; }',
    )
    htmlParts.push('.chart-print-image { width: 100%; height: auto; display: block; }')
    htmlParts.push(
      '@media print { body { padding: 0; } .charts-container { gap: 15px; } .chart-print-item { break-inside: avoid; } }',
    )
    htmlParts.push('</style>')
    htmlParts.push('</head>')
    htmlParts.push('<body>')
    htmlParts.push('<div class="print-header">')
    htmlParts.push('<div class="print-title">生産実績分析チャート</div>')
    htmlParts.push('<div class="print-date">期間: ' + dateRange + '</div>')
    if (filterText) {
      htmlParts.push('<div class="print-filters">' + filterText + '</div>')
    }
    htmlParts.push('</div>')
    htmlParts.push('<div class="charts-container">')
    htmlParts.push('<div class="chart-print-item">')
    htmlParts.push('<div class="chart-print-title">日別生産量推移</div>')
    htmlParts.push(
      '<img src="' + dailyTrendImage + '" alt="日別生産量推移" class="chart-print-image" />',
    )
    htmlParts.push('</div>')
    htmlParts.push('<div class="chart-print-item">')
    htmlParts.push('<div class="chart-print-title">工程別生産量</div>')
    htmlParts.push(
      '<img src="' + processImage + '" alt="工程別生産量" class="chart-print-image" />',
    )
    htmlParts.push('</div>')
    htmlParts.push('<div class="chart-print-item">')
    htmlParts.push('<div class="chart-print-title">取引タイプ分布</div>')
    htmlParts.push('<img src="' + typeImage + '" alt="取引タイプ分布" class="chart-print-image" />')
    htmlParts.push('</div>')
    htmlParts.push('<div class="chart-print-item">')
    htmlParts.push('<div class="chart-print-title">製品生産量TOP10</div>')
    htmlParts.push(
      '<img src="' + productImage + '" alt="製品生産量TOP10" class="chart-print-image" />',
    )
    htmlParts.push('</div>')
    htmlParts.push('</div>')
    htmlParts.push('<script>')
    htmlParts.push('window.onload = function() {')
    htmlParts.push('setTimeout(function() {')
    htmlParts.push('window.print();')
    htmlParts.push('window.onafterprint = function() { window.close(); };')
    htmlParts.push('}, 500);')
    htmlParts.push('};')
    htmlParts.push('<' + '/script>')
    htmlParts.push('<' + '/body>')
    htmlParts.push('<' + '/html>')

    printWindow.document.write(htmlParts.join('\n'))
    printWindow.document.close()
  } catch (error) {
    console.error('印刷エラー:', error)
    ElMessage.error('印刷に失敗しました')
  }
}

// テーブル印刷処理
const handlePrintTable = async () => {
  try {
    if (tableData.value.length === 0) {
      ElMessage.warning('印刷するデータがありません')
      return
    }

    // すべてのフィルタ済みデータを取得（工程でグループ化、取引日時で昇順ソート）
    const params: any = {
      page: 1,
      limit: 10000, // 大きな値を設定して全データを取得
      process_cd: searchForm.process_cd || undefined,
      transaction_type: searchForm.transaction_type || undefined,
      target_name: searchForm.target_name || undefined,
      machine_name: searchForm.machine_name || undefined,
      date_from: searchForm.date_from || undefined,
      date_to: searchForm.date_to || undefined,
      sort_by: 'transaction_time', // 取引日時でソート
      sort_order: 'ASC', // 昇順
    }

    ElMessage.info('データを取得中...')
    const response = await getStockActualLogs(params)

    if (!response?.success || !response.data) {
      ElMessage.error('データの取得に失敗しました')
      return
    }

    const allData = response.data.list || []

    if (allData.length === 0) {
      ElMessage.warning('印刷するデータがありません')
      return
    }

    // 印刷用HTMLを作成
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('ポップアップがブロックされています。ブラウザの設定を確認してください。')
      return
    }

    const dateRange =
      searchForm.date_from && searchForm.date_to
        ? `${searchForm.date_from} ～ ${searchForm.date_to}`
        : '全期間'

    // フィルタ情報を構築
    const filterInfo: string[] = []

    if (searchForm.process_cd) {
      const process = processList.value.find((p) => p.process_cd === searchForm.process_cd)
      if (process && process.process_name) {
        filterInfo.push('工程: ' + process.process_name)
      } else if (searchForm.process_cd) {
        filterInfo.push('工程: ' + searchForm.process_cd)
      }
    } else if (activeProcessTab.value === 'ALL') {
      filterInfo.push('工程: 全工程')
    }

    if (
      searchForm.transaction_type &&
      searchForm.transaction_type !== 'ALL' &&
      searchForm.transaction_type !== '実績'
    ) {
      filterInfo.push('取引タイプ: ' + searchForm.transaction_type)
    }

    if (searchForm.target_name) {
      filterInfo.push('製品名: ' + searchForm.target_name)
    }
    if (searchForm.machine_name) {
      filterInfo.push('設備: ' + searchForm.machine_name)
    }

    const filterText = filterInfo.length > 0 ? filterInfo.join(' | ') : ''

    // HTML文字列を構築
    const htmlParts: string[] = []
    htmlParts.push('<!DOCTYPE html>')
    htmlParts.push('<html>')
    htmlParts.push('<head>')
    htmlParts.push('<meta charset="UTF-8">')
    htmlParts.push('<title>取引ログ一覧</title>')
    htmlParts.push('<style>')
    htmlParts.push('@page { size: A4 portrait; margin: 10mm; }')
    htmlParts.push('* { margin: 0; padding: 0; box-sizing: border-box; }')
    htmlParts.push(
      'body { font-family: "游ゴシック", "Yu Gothic", "YuGothic", "Meiryo", "メイリオ", sans-serif; padding: 15px; background: #fff; }',
    )
    htmlParts.push(
      '.print-header { text-align: center; margin-bottom: 15px; padding-bottom: 12px; border-bottom: 2px solid #3b82f6; }',
    )
    htmlParts.push(
      '.print-title { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 6px; }',
    )
    htmlParts.push('.print-info { font-size: 12px; color: #6b7280; margin-bottom: 3px; }')
    htmlParts.push('.print-filters { font-size: 12px; color: #475569; margin-top: 3px; }')
    htmlParts.push(
      '.print-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 11px; }',
    )
    htmlParts.push(
      '.print-table th { background: #f3f4f6; border: 1px solid #d1d5db; padding: 8px 6px; text-align: center; font-weight: 600; color: #1e293b; }',
    )
    htmlParts.push(
      '.print-table td { border: 1px solid #d1d5db; padding: 6px 4px; text-align: center; color: #374151; }',
    )
    htmlParts.push('.print-table tr:nth-child(even) { background: #f9fafb; }')
    htmlParts.push(
      '.print-table .group-header { background: #e0e7ff; font-weight: 700; color: #1e293b; }',
    )
    htmlParts.push(
      '.print-table .group-total { background: #fef3c7; font-weight: 700; color: #1e293b; }',
    )
    htmlParts.push(
      '@media print { body { padding: 0; } .print-table { font-size: 10px; } .print-table th, .print-table td { padding: 5px 3px; } }',
    )
    htmlParts.push('</style>')
    htmlParts.push('</head>')
    htmlParts.push('<body>')
    htmlParts.push('<div class="print-header">')
    htmlParts.push('<div class="print-title">取引ログ一覧</div>')

    // 一行にまとめて表示
    const infoParts: string[] = []
    infoParts.push('期間: ' + dateRange)
    if (filterText) {
      infoParts.push(filterText)
    }
    infoParts.push('件数: ' + allData.length + ' 件')

    htmlParts.push('<div class="print-info">' + infoParts.join('  |  ') + '</div>')
    htmlParts.push('</div>')
    htmlParts.push('<table class="print-table">')
    htmlParts.push('<thead>')
    htmlParts.push('<tr>')
    htmlParts.push('<th style="width: 120px;">取引日時</th>')
    htmlParts.push('<th style="width: 80px;">工程</th>')
    htmlParts.push('<th style="width: 80px;">タイプ</th>')
    htmlParts.push('<th style="width: 70px;">区分</th>')
    htmlParts.push('<th style="width: 90px;">製品CD</th>')
    htmlParts.push('<th style="min-width: 130px;">製品名</th>')
    htmlParts.push('<th style="width: 90px;">数量</th>')
    htmlParts.push('<th style="width: 100px;">保管場所</th>')
    htmlParts.push('<th style="width: 130px;">設備名</th>')
    htmlParts.push('</tr>')
    htmlParts.push('</thead>')
    htmlParts.push('<tbody>')

    // 工程でグループ化
    const groupedData = new Map<string, StockActualLogRecord[]>()
    allData.forEach((row: StockActualLogRecord) => {
      const processKey = row.process_name || row.process_cd || 'その他'
      if (!groupedData.has(processKey)) {
        groupedData.set(processKey, [])
      }
      groupedData.get(processKey)!.push(row)
    })

    // 各グループ内で取引日時で昇順ソート
    groupedData.forEach((rows) => {
      rows.sort((a, b) => {
        const timeA = new Date(a.transaction_time ?? '').getTime()
        const timeB = new Date(b.transaction_time ?? '').getTime()
        return timeA - timeB
      })
    })

    // 工程名でソート（全工程を最後に）
    const sortedProcesses = Array.from(groupedData.keys()).sort((a, b) => {
      if (a === '全工程' || a === 'その他') return 1
      if (b === '全工程' || b === 'その他') return -1
      return a.localeCompare(b, 'ja')
    })

    // 各工程グループを出力
    sortedProcesses.forEach((processName) => {
      const rows = groupedData.get(processName) || []
      if (rows.length === 0) return

      // 工程ヘッダー行
      htmlParts.push('<tr class="group-header">')
      htmlParts.push('<td colspan="9" style="text-align: left; padding-left: 10px;">')
      htmlParts.push('【' + processName + '】')
      htmlParts.push('</td>')
      htmlParts.push('</tr>')

      // データ行
      let groupTotal = 0
      rows.forEach((row: StockActualLogRecord) => {
        const quantity = Number(row.quantity || 0)
        groupTotal += quantity

        htmlParts.push('<tr>')
        htmlParts.push('<td>' + formatDateTime(row.transaction_time ?? '') + '</td>')
        htmlParts.push('<td>' + (row.process_name || '-') + '</td>')
        htmlParts.push('<td>' + (row.transaction_type || '-') + '</td>')
        htmlParts.push('<td>' + (row.stock_type || '-') + '</td>')
        htmlParts.push('<td>' + (row.target_cd || '-') + '</td>')
        htmlParts.push('<td>' + (row.target_name || '-') + '</td>')
        htmlParts.push(
          '<td>' + quantity.toLocaleString() + (row.unit ? ' ' + row.unit : '') + '</td>',
        )
        htmlParts.push('<td>' + (row.location_cd || '-') + '</td>')
        htmlParts.push('<td>' + (row.machine_name || '-') + '</td>')
        htmlParts.push('</tr>')
      })

      // 合計行
      htmlParts.push('<tr class="group-total">')
      htmlParts.push(
        '<td colspan="6" style="text-align: right; padding-right: 15px; font-weight: 700;">',
      )
      htmlParts.push(processName + ' 合計:')
      htmlParts.push('</td>')
      htmlParts.push(
        '<td style="font-weight: 700; font-size: 12px;">' + groupTotal.toLocaleString() + '</td>',
      )
      htmlParts.push('<td colspan="2" style="font-weight: 700;">件数: ' + rows.length + ' 件</td>')
      htmlParts.push('</tr>')
    })

    htmlParts.push('</tbody>')
    htmlParts.push('</table>')
    htmlParts.push('<script>')
    htmlParts.push('window.onload = function() {')
    htmlParts.push('setTimeout(function() {')
    htmlParts.push('window.print();')
    htmlParts.push('window.onafterprint = function() { window.close(); };')
    htmlParts.push('}, 500);')
    htmlParts.push('};')
    htmlParts.push('<' + '/script>')
    htmlParts.push('<' + '/body>')
    htmlParts.push('<' + '/html>')

    printWindow.document.write(htmlParts.join('\n'))
    printWindow.document.close()
    ElMessage.success('印刷準備が完了しました')
  } catch (error) {
    console.error('テーブル印刷エラー:', error)
    ElMessage.error('印刷に失敗しました')
  }
}

/** 取引ログ一覧を「工程・設備・製品 × 日付」の二次元表で印刷（A3 横） */
const handlePrintMatrixTable = async () => {
  try {
    if (tableData.value.length === 0) {
      ElMessage.warning('印刷するデータがありません')
      return
    }

    const params: any = {
      page: 1,
      limit: 10000,
      process_cd: searchForm.process_cd || undefined,
      transaction_type: searchForm.transaction_type || undefined,
      target_name: searchForm.target_name || undefined,
      machine_name: searchForm.machine_name || undefined,
      date_from: searchForm.date_from || undefined,
      date_to: searchForm.date_to || undefined,
      sort_by: 'transaction_time',
      sort_order: 'ASC',
    }

    ElMessage.info('データを取得中...')
    const response = await getStockActualLogs(params)

    if (!response?.success || !response.data) {
      ElMessage.error('データの取得に失敗しました')
      return
    }

    const allData = response.data.list || []
    if (allData.length === 0) {
      ElMessage.warning('印刷するデータがありません')
      return
    }

    /** この工程では設備名が空の行をマトリクス印刷から除外する */
    const SKIP_EMPTY_MACHINE_PROCESS_NAMES = new Set(['切断', '面取', '成型', '溶接', 'メッキ'])

    const resolveProcessDisplayForPrint = (row: StockActualLogRecord): string => {
      const n = String(row.process_name || '').trim()
      if (n) return n
      const cd = String(row.process_cd || '').trim()
      if (cd) {
        const p = processList.value.find((x) => String(x.process_cd) === cd)
        if (p?.process_name) return String(p.process_name).trim()
        return cd
      }
      return '-'
    }

    const isEmptyMachineLabel = (machine: string): boolean => {
      const m = machine.trim()
      if (!m) return true
      if (m === '-') return true
      if (m === '－') return true
      if (m === '—') return true
      return false
    }

    type MatrixAgg = {
      process: string
      machine: string
      product: string
      byDate: Map<string, number>
    }

    const dateSet = new Set<string>()
    const rowMap = new Map<string, MatrixAgg>()

    for (const row of allData) {
      const dk = transactionDateKey(row)
      if (!dk) continue

      const process = resolveProcessDisplayForPrint(row)
      const machine = String(row.machine_name || '-').trim() || '-'
      if (SKIP_EMPTY_MACHINE_PROCESS_NAMES.has(process) && isEmptyMachineLabel(machine)) {
        continue
      }
      const product = String(row.target_name || '-').trim() || '-'
      const rowKey = [process, machine, product].join('\u0001')

      dateSet.add(dk)
      const qty = Number(row.quantity || 0)

      let agg = rowMap.get(rowKey)
      if (!agg) {
        agg = { process, machine, product, byDate: new Map() }
        rowMap.set(rowKey, agg)
      }
      agg.byDate.set(dk, (agg.byDate.get(dk) || 0) + qty)
    }

    if (rowMap.size === 0) {
      ElMessage.warning(
        'マトリクス印刷の対象データがありません（切断・面取・成型・溶接・メッキで設備名が空の行は除いています）',
      )
      return
    }

    const sortedDates = Array.from(dateSet).sort()
    if (sortedDates.length === 0) {
      ElMessage.warning('日付が取得できたデータがありません')
      return
    }

    const matrixRows = Array.from(rowMap.values()).sort((a, b) => {
      const c1 = a.process.localeCompare(b.process, 'ja')
      if (c1 !== 0) return c1
      const c2 = a.machine.localeCompare(b.machine, 'ja')
      if (c2 !== 0) return c2
      return a.product.localeCompare(b.product, 'ja')
    })

    /** 工程 → 設備名 → 行データ（印刷時の階層表示用） */
    const byProcess = new Map<string, Map<string, MatrixAgg[]>>()
    for (const r of matrixRows) {
      if (!byProcess.has(r.process)) {
        byProcess.set(r.process, new Map())
      }
      const byMachine = byProcess.get(r.process)!
      if (!byMachine.has(r.machine)) {
        byMachine.set(r.machine, [])
      }
      byMachine.get(r.machine)!.push(r)
    }
    const sortedProcessKeys = Array.from(byProcess.keys()).sort((a, b) => a.localeCompare(b, 'ja'))

    const colTotals = new Map<string, number>()
    for (const d of sortedDates) colTotals.set(d, 0)
    for (const r of matrixRows) {
      for (const d of sortedDates) {
        const v = r.byDate.get(d) || 0
        colTotals.set(d, (colTotals.get(d) || 0) + v)
      }
    }

    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('ポップアップがブロックされています。ブラウザの設定を確認してください。')
      return
    }

    const dateRangeLabel =
      searchForm.date_from && searchForm.date_to
        ? `${searchForm.date_from} ～ ${searchForm.date_to}`
        : '全期間'

    const filterInfo: string[] = []
    if (
      searchForm.transaction_type &&
      searchForm.transaction_type !== 'ALL' &&
      searchForm.transaction_type !== '実績'
    ) {
      filterInfo.push('取引タイプ: ' + searchForm.transaction_type)
    }
    if (searchForm.target_name) {
      filterInfo.push('製品名: ' + searchForm.target_name)
    }
    if (searchForm.machine_name) {
      filterInfo.push('設備: ' + searchForm.machine_name)
    }
    const filterText = filterInfo.length > 0 ? filterInfo.join(' | ') : ''

    const fmtQty = (n: number) => {
      if (n === 0) return ''
      const s = n.toLocaleString('ja-JP', { maximumFractionDigits: 2 })
      return s
    }

    const htmlParts: string[] = []
    htmlParts.push('<!DOCTYPE html>')
    htmlParts.push('<html>')
    htmlParts.push('<head>')
    htmlParts.push('<meta charset="UTF-8">')
    htmlParts.push('<title>取引ログ一覧（日別集計）</title>')
    htmlParts.push('<style>')
    htmlParts.push('@page { size: A3 landscape; margin: 8mm; }')
    htmlParts.push('* { margin: 0; padding: 0; box-sizing: border-box; }')
    htmlParts.push(
      'body { font-family: "游ゴシック", "Yu Gothic", "YuGothic", "Meiryo", "メイリオ", sans-serif; padding: 10px; background: #fff; color: #111827; }',
    )
    htmlParts.push(
      '.print-header { margin-bottom: 10px; padding-bottom: 8px; border-bottom: 2px solid #2563eb; }',
    )
    htmlParts.push(
      '.print-header-row { display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 10px 16px; }',
    )
    htmlParts.push(
      '.print-title { font-size: 18px; font-weight: 700; color: #0f172a; margin: 0; text-align: left; flex: 1; min-width: 12em; }',
    )
    htmlParts.push(
      '.print-period { font-size: 12px; color: #475569; font-weight: 600; text-align: right; white-space: nowrap; flex-shrink: 0; }',
    )
    htmlParts.push('.print-filters { font-size: 11px; color: #475569; margin-top: 6px; text-align: left; }')
    htmlParts.push('.matrix-wrap { width: 100%; overflow: visible; }')
    htmlParts.push(
      '.matrix-table tbody.matrix-machine-tbody { break-inside: avoid; page-break-inside: avoid; }',
    )
    htmlParts.push(
      '.matrix-table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 10px; margin-top: 8px; line-height: 1.44; }',
    )
    htmlParts.push(
      '.matrix-table th, .matrix-table td { border: 1px solid #94a3b8; padding: 2.4px 3.6px; vertical-align: middle; word-wrap: break-word; overflow-wrap: anywhere; }',
    )
    htmlParts.push(
      '.matrix-table th { background: #e2e8f0; font-weight: 700; color: #0f172a; text-align: center; }',
    )
    htmlParts.push('.matrix-table .sticky-col { background: #f1f5f9; text-align: left; font-weight: 600; }')
    htmlParts.push(
      '.matrix-table .matrix-product-name { width: 150px; max-width: 150px; min-width: 150px; box-sizing: border-box; text-align: left; font-weight: 600; padding-left: 18px; padding-right: 6px; }',
    )
    htmlParts.push('.matrix-table .num { text-align: right; font-variant-numeric: tabular-nums; }')
    htmlParts.push('.matrix-table .date-th { font-size: 9px; line-height: 1.26; padding: 4.8px 1.2px; }')
    htmlParts.push(
      '.matrix-table .total-row th, .matrix-table .total-row td { background: #fef9c3; font-weight: 700; }',
    )
    htmlParts.push(
      '.matrix-table .row-total { background: #ecfdf5; font-weight: 700; text-align: right; }',
    )
    htmlParts.push(
      '.matrix-table .matrix-group-process td { background: #bfdbfe; font-weight: 700; font-size: 11px; text-align: left; padding: 6px 9.6px; border-color: #60a5fa; }',
    )
    htmlParts.push(
      '.matrix-table .matrix-group-machine td { background: #e0e7ff; font-weight: 700; font-size: 10px; text-align: left; padding: 4.8px 9.6px 4.8px 26.4px; border-color: #818cf8; }',
    )
    htmlParts.push(
      '.matrix-table .matrix-subtotal-machine td, .matrix-table .matrix-subtotal-machine th { background: #c7d2fe; font-weight: 700; border-color: #64748b; }',
    )
    htmlParts.push(
      '.matrix-table .matrix-subtotal-label { text-align: right !important; padding-right: 8px !important; font-size: 9px; color: #1e293b; }',
    )
    htmlParts.push(
      '@media print { body { padding: 0; } .matrix-table { font-size: 9px; line-height: 1.44; } .matrix-table th, .matrix-table td { padding: 1.2px 2.4px; } .matrix-table .matrix-product-name { width: 150px !important; max-width: 150px !important; min-width: 150px !important; padding-left: 14px !important; padding-right: 4px !important; } .matrix-table tbody.matrix-machine-tbody { break-inside: avoid !important; page-break-inside: avoid !important; } .matrix-table .date-th { font-size: 8px; padding: 3.6px 1.2px; } .matrix-table .matrix-group-process td { font-size: 10px; padding: 4.8px 8px; } .matrix-table .matrix-group-machine td { font-size: 9px; padding: 3.6px 8px 3.6px 26px; } .matrix-table .matrix-subtotal-label { font-size: 8px !important; } }',
    )
    htmlParts.push('</style>')
    htmlParts.push('</head>')
    htmlParts.push('<body>')
    htmlParts.push('<div class="print-header">')
    htmlParts.push('<div class="print-header-row">')
    htmlParts.push('<div class="print-title">取引ログ一覧表（日別数量集計）</div>')
    htmlParts.push(
      '<div class="print-period">期間: ' + escapeHtmlText(dateRangeLabel) + '</div>',
    )
    htmlParts.push('</div>')
    if (filterText) {
      htmlParts.push('<div class="print-filters">' + escapeHtmlText(filterText) + '</div>')
    }
    htmlParts.push('</div>')
    htmlParts.push('<div class="matrix-wrap">')
    htmlParts.push('<table class="matrix-table">')
    htmlParts.push('<thead><tr>')
    htmlParts.push('<th style="width:150px;min-width:150px;max-width:150px;" class="matrix-product-name">製品名</th>')
    for (const d of sortedDates) {
      htmlParts.push(
        '<th class="date-th num" title="' +
          escapeHtmlText(d) +
          '">' +
          escapeHtmlText(formatShortDateHeader(d)) +
          '</th>',
      )
    }
    htmlParts.push('<th style="width: 4%;" class="num">行計</th>')
    htmlParts.push('</tr></thead>')

    const matrixColSpan = 1 + sortedDates.length + 1

    for (const proc of sortedProcessKeys) {
      htmlParts.push('<tbody>')
      htmlParts.push('<tr class="matrix-group-process">')
      htmlParts.push(
        '<td colspan="' +
          matrixColSpan +
          '">【工程】' +
          escapeHtmlText(proc) +
          '</td>',
      )
      htmlParts.push('</tr>')
      htmlParts.push('</tbody>')

      const byMachine = byProcess.get(proc)!
      const sortedMachines = Array.from(byMachine.keys()).sort((a, b) => a.localeCompare(b, 'ja'))
      for (const mach of sortedMachines) {
        htmlParts.push('<tbody class="matrix-machine-tbody">')
        htmlParts.push('<tr class="matrix-group-machine">')
        htmlParts.push(
          '<td colspan="' +
            matrixColSpan +
            '">【設備名】' +
            escapeHtmlText(mach) +
            '</td>',
        )
        htmlParts.push('</tr>')

        const prodRows = byMachine.get(mach)!
        prodRows.sort((a, b) => a.product.localeCompare(b.product, 'ja'))
        for (const r of prodRows) {
          let rowSum = 0
          htmlParts.push('<tr>')
          htmlParts.push(
            '<td class="sticky-col matrix-product-name">' + escapeHtmlText(r.product) + '</td>',
          )
          for (const d of sortedDates) {
            const v = r.byDate.get(d) || 0
            rowSum += v
            htmlParts.push('<td class="num">' + escapeHtmlText(fmtQty(v)) + '</td>')
          }
          htmlParts.push('<td class="num row-total">' + escapeHtmlText(fmtQty(rowSum) || '0') + '</td>')
          htmlParts.push('</tr>')
        }

        const machineDateTotals = new Map<string, number>()
        for (const d of sortedDates) {
          machineDateTotals.set(d, 0)
        }
        let machineGrand = 0
        for (const r of prodRows) {
          let rowSum = 0
          for (const d of sortedDates) {
            const v = r.byDate.get(d) || 0
            machineDateTotals.set(d, (machineDateTotals.get(d) || 0) + v)
            rowSum += v
          }
          machineGrand += rowSum
        }
        htmlParts.push('<tr class="matrix-subtotal-machine">')
        htmlParts.push(
          '<th scope="row" class="sticky-col matrix-product-name matrix-subtotal-label">設備計</th>',
        )
        for (const d of sortedDates) {
          const sv = machineDateTotals.get(d) || 0
          htmlParts.push('<td class="num">' + escapeHtmlText(fmtQty(sv)) + '</td>')
        }
        htmlParts.push(
          '<td class="num row-total">' +
            escapeHtmlText(machineGrand === 0 ? '0' : machineGrand.toLocaleString('ja-JP')) +
            '</td>',
        )
        htmlParts.push('</tr>')

        htmlParts.push('</tbody>')
      }
    }

    htmlParts.push('<tbody>')
    htmlParts.push('<tr class="total-row">')
    htmlParts.push('<th style="text-align:right;padding-right:8px;">総計</th>')
    let grand = 0
    for (const d of sortedDates) {
      const t = colTotals.get(d) || 0
      grand += t
      htmlParts.push('<td class="num">' + escapeHtmlText(fmtQty(t) || '0') + '</td>')
    }
    htmlParts.push('<td class="num">' + escapeHtmlText(grand.toLocaleString('ja-JP')) + '</td>')
    htmlParts.push('</tr>')
    htmlParts.push('</tbody>')
    htmlParts.push('</table></div>')
    htmlParts.push('<script>')
    htmlParts.push('window.onload = function() {')
    htmlParts.push('setTimeout(function() {')
    htmlParts.push('window.print();')
    htmlParts.push('window.onafterprint = function() { window.close(); };')
    htmlParts.push('}, 500);')
    htmlParts.push('};')
    htmlParts.push('<' + '/script>')
    htmlParts.push('<' + '/body>')
    htmlParts.push('<' + '/html>')

    printWindow.document.write(htmlParts.join('\n'))
    printWindow.document.close()
    ElMessage.success('印刷準備が完了しました')
  } catch (error) {
    console.error('マトリクス印刷エラー:', error)
    ElMessage.error('印刷に失敗しました')
  }
}

onMounted(async () => {
  if (!searchForm.date_from || !searchForm.date_to) {
    setDefaultDateRange()
  }
  await loadProcesses()
  searchForm.process_cd = ''
  // チャート初期化（DOMがレンダリングされる前に初期化）
  initCharts()
  await loadData()
  window.addEventListener('resize', handleResize)
})

watch(
  () => [
    searchForm.target_name,
    searchForm.machine_name,
    searchForm.date_from,
    searchForm.date_to,
  ],
  () => {
    if (autoSearchTimer) {
      clearTimeout(autoSearchTimer)
    }
    autoSearchTimer = setTimeout(() => {
      handleSearch()
    }, 350)
  },
)

onUnmounted(() => {
  if (autoSearchTimer) {
    clearTimeout(autoSearchTimer)
    autoSearchTimer = null
  }
  window.removeEventListener('resize', handleResize)
  dailyTrendChart?.dispose()
  processChart?.dispose()
  typeChart?.dispose()
  productChart?.dispose()
})
</script>

<style scoped lang="scss">
$font-stack:
  'Inter',
  'Noto Sans JP',
  '游ゴシック',
  'Yu Gothic',
  'YuGothic',
  'Hiragino Sans',
  'Meiryo',
  'メイリオ',
  'Microsoft YaHei',
  'PingFang SC',
  sans-serif;
$font-num:
  'Inter',
  'SF Pro Display',
  -apple-system,
  BlinkMacSystemFont,
  'Segoe UI',
  'Noto Sans JP',
  '游ゴシック',
  'Yu Gothic',
  sans-serif;

$primary: #3b82f6;
$primary-strong: #2563eb;
$primary-darker: #1d4ed8;
$accent: #6366f1;

$text-strong: #0f172a;
$text-base: #1e293b;
$text-soft: #475569;
$text-muted: #64748b;
$text-subtle: #94a3b8;

$border: #e2e8f0;
$border-soft: #eef2f7;

$surface: #ffffff;
$surface-1: #f8fafc;
$surface-2: #f1f5f9;

$radius-card: 12px;
$radius-input: 8px;
$radius-chip: 999px;

$gradient-primary: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
$gradient-primary-strong: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
$gradient-surface: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);

$shadow-card:
  0 1px 2px rgba(15, 23, 42, 0.04),
  0 10px 24px rgba(15, 23, 42, 0.06);
$shadow-card-hover:
  0 2px 4px rgba(15, 23, 42, 0.06),
  0 18px 32px rgba(15, 23, 42, 0.1);
$shadow-inset-top: inset 0 1px 0 rgba(255, 255, 255, 0.8);

.production-actual-management {
  padding: 10px 12px 14px;
  min-height: 100vh;
  position: relative;
  font-family: $font-stack;
  font-feature-settings: 'palt' 1;
  color: $text-base;
  background:
    radial-gradient(circle at 4% 0%, rgba(59, 130, 246, 0.14), transparent 34%),
    radial-gradient(circle at 98% 8%, rgba(99, 102, 241, 0.12), transparent 32%),
    linear-gradient(145deg, #f5f8fd 0%, #eef2f9 48%, #e6ecf5 100%);

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.4) 0%, transparent 160px);
    z-index: 0;
  }

  > * {
    position: relative;
    z-index: 1;
  }

  :deep(button),
  :deep(input),
  :deep(.el-input__inner),
  :deep(.el-tag),
  :deep(.el-table) {
    font-family: inherit;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding: 12px 18px;
    border-radius: $radius-card;
    border: 1px solid rgba(226, 232, 240, 0.7);
    background:
      linear-gradient(
        135deg,
        rgba(255, 255, 255, 0.95) 0%,
        rgba(248, 250, 252, 0.95) 100%
      );
    backdrop-filter: blur(8px);
    box-shadow: $shadow-card, $shadow-inset-top;
    position: relative;
    overflow: hidden;
    transition:
      transform 0.2s ease,
      box-shadow 0.25s ease;

    &::before {
      content: '';
      position: absolute;
      inset: 0 0 auto 0;
      height: 3px;
      background: linear-gradient(90deg, $primary 0%, $accent 50%, $primary 100%);
      opacity: 0.75;
    }

    &:hover {
      transform: translateY(-1px);
      box-shadow: $shadow-card-hover, $shadow-inset-top;
    }

    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;

      .title-icon {
        width: 40px;
        height: 40px;
        border-radius: 11px;
        background: $gradient-primary;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 20px;
        box-shadow:
          0 10px 18px rgba(59, 130, 246, 0.35),
          inset 0 1px 0 rgba(255, 255, 255, 0.5);
        transition: transform 0.25s ease;

        &:hover {
          transform: translateY(-1px) scale(1.04);
        }
      }

      h1 {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
        color: $text-strong;
        letter-spacing: -0.01em;
        line-height: 1.2;
      }

      p {
        margin: 2px 0 0;
        color: $text-muted;
        font-size: 12px;
        font-weight: 400;
        letter-spacing: 0.2px;
      }
    }

    .action-btn {
      border-radius: 8px;
      font-weight: 600;
      font-size: 12px;
      height: 30px;
      padding: 0 14px;
      background: #fff;
      border: 1px solid $border;
      color: $text-soft;
      transition: all 0.2s ease;

      &:hover {
        transform: translateY(-1px);
        color: $primary-strong;
        border-color: rgba(59, 130, 246, 0.5);
        box-shadow: 0 6px 14px rgba(59, 130, 246, 0.15);
      }
    }
  }

  .search-card {
    margin-bottom: 10px;
    border-radius: $radius-card;
    border: 1px solid rgba(226, 232, 240, 0.7);
    background: $gradient-surface;
    box-shadow: $shadow-card, $shadow-inset-top;
    transition:
      transform 0.2s ease,
      box-shadow 0.25s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: $shadow-card-hover, $shadow-inset-top;
    }

    :deep(.el-card__body) {
      padding: 10px 14px;
    }

    .search-form {
      .search-row {
        align-items: center;
        flex-wrap: nowrap;
      }

      :deep(.el-form-item) {
        margin-bottom: 0;
      }

      :deep(.el-form-item__label) {
        font-weight: 600;
        color: $text-soft;
        font-size: 12px;
        padding-bottom: 0;
        line-height: 32px;
      }

      :deep(.el-form-item__content) {
        line-height: 32px;
      }

      :deep(.el-input__wrapper) {
        border-radius: $radius-input;
        box-shadow: 0 0 0 1px rgba(203, 213, 225, 0.6) inset;
        background: #fff;
        transition: all 0.2s ease;

        &:hover {
          box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.45) inset;
        }

        &.is-focus {
          box-shadow:
            0 0 0 1px $primary inset,
            0 0 0 3px rgba(59, 130, 246, 0.15);
        }
      }

      :deep(.el-input__inner) {
        font-size: 13px;
        color: $text-strong;
      }

      .filter-select {
        width: 100%;
      }
    }

    .date-input-group {
      display: flex;
      align-items: center;
      gap: 8px;

      .date-picker {
        flex: 1;
        min-width: 0;
      }

      .quick-buttons {
        display: inline-flex;
        flex-shrink: 0;
        padding: 2px;
        border-radius: $radius-input;
        background: $surface-2;
        border: 1px solid $border-soft;
        box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
        gap: 0;

        .date-btn {
          font-size: 12px;
          font-weight: 600;
          padding: 4px 10px;
          min-width: 46px;
          height: 26px;
          border-radius: 6px;
          border: 1px solid transparent;
          background: transparent;
          color: $text-muted;
          transition: all 0.2s ease;
          margin: 0 1px;

          &:hover {
            color: $text-base;
            background: rgba(255, 255, 255, 0.9);
            box-shadow:
              0 1px 2px rgba(15, 23, 42, 0.04),
              0 2px 6px rgba(15, 23, 42, 0.06);
          }

          &.today {
            color: #fff;
            background: $gradient-primary;
            border-color: transparent;
            box-shadow:
              0 4px 10px rgba(59, 130, 246, 0.35),
              inset 0 1px 0 rgba(255, 255, 255, 0.35);

            &:hover {
              background: $gradient-primary-strong;
              box-shadow:
                0 6px 14px rgba(59, 130, 246, 0.45),
                inset 0 1px 0 rgba(255, 255, 255, 0.35);
              transform: translateY(-1px);
            }
          }

          &:active {
            transform: translateY(0);
          }
        }
      }
    }
  }

  .process-card {
    margin-bottom: 10px;
    border-radius: $radius-card;
    border: 1px solid rgba(226, 232, 240, 0.7);
    background: $gradient-surface;
    box-shadow: $shadow-card, $shadow-inset-top;
    transition:
      transform 0.2s ease,
      box-shadow 0.25s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: $shadow-card-hover, $shadow-inset-top;
    }

    :deep(.el-card__header) {
      padding: 10px 14px;
      border-bottom: 1px solid $border-soft;
      background: linear-gradient(
        180deg,
        rgba(255, 255, 255, 0.9) 0%,
        rgba(248, 250, 252, 0.6) 100%
      );
    }

    :deep(.el-card__body) {
      padding: 10px 14px 12px;
    }

    .process-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;

      .title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
        color: $text-strong;
        font-size: 13px;
        letter-spacing: 0.2px;

        .el-icon {
          color: $primary;
          font-size: 16px;
        }
      }

      .type-summary-inline {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        flex: 1;

        .inline-label {
          font-size: 11px;
          font-weight: 700;
          color: $text-soft;
          text-transform: uppercase;
          letter-spacing: 0.6px;
        }

        .type-chip {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 3px 10px 3px 4px;
          border-radius: $radius-chip;
          background: #fff;
          border: 1px solid $border-soft;
          font-size: 12px;
          color: $text-soft;
          transition: all 0.2s ease;
          box-shadow:
            0 1px 2px rgba(15, 23, 42, 0.04),
            inset 0 1px 0 rgba(255, 255, 255, 0.7);

          &:hover {
            transform: translateY(-1px);
            border-color: rgba(59, 130, 246, 0.35);
            box-shadow:
              0 4px 10px rgba(59, 130, 246, 0.12),
              inset 0 1px 0 rgba(255, 255, 255, 0.7);
          }

          .type-name {
            font-weight: 700;
            color: $text-strong;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: $radius-chip;
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            color: $primary-darker;
            letter-spacing: 0.3px;
          }

          .type-values {
            display: flex;
            align-items: center;
            gap: 4px;
            color: $text-muted;
            font-weight: 600;
            font-family: $font-num;
            font-variant-numeric: tabular-nums;
            font-size: 12px;

            .divider {
              color: $text-subtle;
              margin: 0 1px;
            }
          }
        }
      }

      .record-hint {
        font-size: 12px;
        color: $text-soft;
        font-weight: 600;
        padding: 4px 10px;
        background: linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%);
        border: 1px solid rgba(59, 130, 246, 0.15);
        border-radius: $radius-chip;
        font-variant-numeric: tabular-nums;
      }
    }

    .process-tabs {
      margin-bottom: 10px;

      :deep(.el-tabs__header) {
        margin: 0 0 10px;
      }

      :deep(.el-tabs__nav) {
        border: none !important;
        padding: 3px;
        background: $surface-2;
        border-radius: 10px;
        box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.05);
      }

      :deep(.el-tabs__nav-wrap::after) {
        display: none;
      }

      :deep(.el-tabs__item) {
        font-weight: 600;
        color: $text-muted;
        font-size: 12px;
        padding: 0 14px !important;
        height: 28px;
        line-height: 28px;
        border: none !important;
        border-radius: 8px;
        margin: 0 2px;
        transition: all 0.2s ease;

        &:hover {
          color: $text-base;
          background: rgba(255, 255, 255, 0.6);
        }

        &.is-active {
          color: #fff;
          background: $gradient-primary;
          box-shadow:
            0 4px 10px rgba(59, 130, 246, 0.35),
            inset 0 1px 0 rgba(255, 255, 255, 0.35);
        }
      }
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 10px;

      .stat-card {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        border: 1px solid rgba(226, 232, 240, 0.7);
        border-radius: 10px;
        background: linear-gradient(
          180deg,
          rgba(255, 255, 255, 0.95) 0%,
          rgba(248, 250, 252, 0.9) 100%
        );
        position: relative;
        overflow: hidden;
        transition:
          transform 0.25s cubic-bezier(0.4, 0, 0.2, 1),
          box-shadow 0.25s ease,
          border-color 0.25s ease;
        box-shadow:
          0 1px 2px rgba(15, 23, 42, 0.04),
          0 6px 14px rgba(15, 23, 42, 0.05),
          $shadow-inset-top;

        &::before {
          content: '';
          position: absolute;
          inset: 0 0 auto 0;
          height: 3px;
          opacity: 0.9;
        }

        &:hover {
          transform: translateY(-3px);
          box-shadow:
            0 2px 4px rgba(15, 23, 42, 0.06),
            0 16px 28px rgba(15, 23, 42, 0.1),
            $shadow-inset-top;
          border-color: rgba(59, 130, 246, 0.3);
        }

        .stat-icon {
          width: 38px;
          height: 38px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          font-size: 18px;
          flex-shrink: 0;
          transition: transform 0.3s ease;
          box-shadow:
            0 6px 12px rgba(15, 23, 42, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);

          &.primary {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
          }
          &.success {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          }
          &.warning {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
          }
          &.info {
            background: linear-gradient(135deg, #06b6d4 0%, #0284c7 100%);
          }
          &.neutral {
            background: linear-gradient(135deg, #64748b 0%, #475569 100%);
          }

          &:hover {
            transform: scale(1.06) rotate(-3deg);
          }
        }

        &:has(.stat-icon.primary)::before {
          background: linear-gradient(90deg, #3b82f6, #60a5fa);
        }
        &:has(.stat-icon.success)::before {
          background: linear-gradient(90deg, #10b981, #34d399);
        }
        &:has(.stat-icon.warning)::before {
          background: linear-gradient(90deg, #f59e0b, #fbbf24);
        }
        &:has(.stat-icon.info)::before {
          background: linear-gradient(90deg, #06b6d4, #38bdf8);
        }
        &:has(.stat-icon.neutral)::before {
          background: linear-gradient(90deg, #64748b, #94a3b8);
        }

        .stat-label {
          font-size: 11px;
          color: $text-muted;
          font-weight: 600;
          margin-bottom: 2px;
          letter-spacing: 0.3px;
          text-transform: uppercase;
        }

        .stat-value {
          font-size: 20px;
          font-weight: 700;
          color: $text-strong;
          display: flex;
          align-items: baseline;
          gap: 3px;
          letter-spacing: -0.02em;
          line-height: 1.1;
          font-family: $font-num;
          font-variant-numeric: tabular-nums;

          small {
            font-size: 11px;
            font-weight: 600;
            color: $text-muted;
            font-family: $font-stack;
            letter-spacing: 0.3px;
          }
        }
      }
    }
  }

  .chart-card {
    margin-bottom: 10px;
    border-radius: $radius-card;
    border: 1px solid rgba(226, 232, 240, 0.7);
    background: $gradient-surface;
    box-shadow: $shadow-card, $shadow-inset-top;
    transition:
      transform 0.2s ease,
      box-shadow 0.25s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: $shadow-card-hover, $shadow-inset-top;
    }

    :deep(.el-card__header) {
      padding: 10px 14px;
      border-bottom: 1px solid $border-soft;
      background: linear-gradient(
        180deg,
        rgba(255, 255, 255, 0.9) 0%,
        rgba(248, 250, 252, 0.6) 100%
      );
    }

    :deep(.el-card__body) {
      padding: 10px 12px 12px;
    }

    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .chart-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
        color: $text-strong;
        font-size: 13px;
        letter-spacing: 0.2px;

        .el-icon {
          color: $primary;
          font-size: 16px;
        }
      }

      .print-btn {
        background: $gradient-primary;
        border: none;
        color: #fff;
        font-weight: 600;
        height: 26px;
        padding: 0 12px;
        border-radius: 7px;
        box-shadow:
          0 4px 10px rgba(59, 130, 246, 0.3),
          inset 0 1px 0 rgba(255, 255, 255, 0.3);
        transition: all 0.2s ease;

        &:hover {
          background: $gradient-primary-strong;
          box-shadow:
            0 6px 14px rgba(59, 130, 246, 0.42),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
          transform: translateY(-1px);
        }

        &:active {
          transform: translateY(0);
        }
      }
    }

    .charts-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;

      .chart-item {
        background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
        border: 1px solid rgba(226, 232, 240, 0.7);
        border-radius: 10px;
        padding: 10px 12px;
        position: relative;
        overflow: hidden;
        transition:
          transform 0.25s ease,
          box-shadow 0.25s ease,
          border-color 0.25s ease;
        box-shadow:
          0 1px 2px rgba(15, 23, 42, 0.03),
          0 4px 12px rgba(15, 23, 42, 0.04),
          $shadow-inset-top;

        &:hover {
          transform: translateY(-2px);
          box-shadow:
            0 2px 4px rgba(15, 23, 42, 0.05),
            0 10px 22px rgba(15, 23, 42, 0.08),
            $shadow-inset-top;
          border-color: rgba(59, 130, 246, 0.3);
        }

        .chart-item-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          padding-bottom: 7px;
          border-bottom: 1px solid $border-soft;
          position: relative;

          &::before {
            content: '';
            width: 3px;
            height: 14px;
            border-radius: 2px;
            background: $gradient-primary;
            box-shadow: 0 2px 6px rgba(59, 130, 246, 0.35);
          }

          &::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            width: 48px;
            height: 2px;
            background: linear-gradient(90deg, $primary, transparent);
            border-radius: 2px;
          }

          .chart-item-title {
            font-weight: 700;
            color: $text-strong;
            font-size: 12px;
            letter-spacing: 0.3px;
          }
        }

        .chart-container {
          width: 100%;
          min-height: 220px;
        }
      }
    }
  }

  .table-card {
    margin-bottom: 10px;
    border-radius: $radius-card;
    border: 1px solid rgba(226, 232, 240, 0.7);
    background: $gradient-surface;
    box-shadow: $shadow-card, $shadow-inset-top;
    transition:
      transform 0.2s ease,
      box-shadow 0.25s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: $shadow-card-hover, $shadow-inset-top;
    }

    :deep(.el-card__header) {
      padding: 10px 14px;
      border-bottom: 1px solid $border-soft;
      background: linear-gradient(
        180deg,
        rgba(255, 255, 255, 0.9) 0%,
        rgba(248, 250, 252, 0.6) 100%
      );
    }

    :deep(.el-card__body) {
      padding: 8px 12px 8px;
    }

    .table-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .table-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
        color: $text-strong;
        font-size: 13px;
        letter-spacing: 0.2px;

        .el-icon {
          color: $primary;
          font-size: 16px;
        }
      }

      .table-header-right {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .el-tag {
        border-radius: $radius-chip;
        font-weight: 700;
        font-size: 11px;
        padding: 2px 10px;
        height: 22px;
        line-height: 20px;
        border: 1px solid rgba(59, 130, 246, 0.2);
        background: linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%);
        color: $primary-darker;
        font-variant-numeric: tabular-nums;
      }

      .print-table-btn {
        background: $gradient-primary;
        border: none;
        color: #fff;
        font-weight: 600;
        height: 26px;
        padding: 0 12px;
        border-radius: 7px;
        box-shadow:
          0 4px 10px rgba(59, 130, 246, 0.3),
          inset 0 1px 0 rgba(255, 255, 255, 0.3);
        transition: all 0.2s ease;

        &:hover {
          background: $gradient-primary-strong;
          box-shadow:
            0 6px 14px rgba(59, 130, 246, 0.42),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
          transform: translateY(-1px);
        }

        &:active {
          transform: translateY(0);
        }
      }
    }

    .data-table {
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid $border;
      box-shadow:
        0 2px 4px rgba(15, 23, 42, 0.04),
        0 8px 18px rgba(15, 23, 42, 0.06),
        $shadow-inset-top;
      font-family: $font-stack;

      :deep(.el-table__header-wrapper) {
        border-radius: 10px 10px 0 0;
        overflow: hidden;
      }

      :deep(.el-table__header) {
        th {
          background: linear-gradient(
            180deg,
            #f8fafc 0%,
            #eef2f7 100%
          );
          padding: 6px 8px;
          font-weight: 700;
          color: $text-strong;
          border-bottom: 1px solid $border;
          border-right: 1px solid rgba(226, 232, 240, 0.5);
          position: relative;
          letter-spacing: 0.3px;
          font-size: 11px;
          line-height: 1.4;

          &:last-child {
            border-right: none;
          }

          .cell {
            font-family: $font-stack;
          }

          &::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(
              90deg,
              transparent 0%,
              rgba(59, 130, 246, 0.6) 50%,
              transparent 100%
            );
            opacity: 0.5;
          }
        }
      }

      :deep(.el-table__body-wrapper) {
        border-radius: 0 0 10px 10px;
      }

      :deep(.el-table__row) {
        transition:
          background-color 0.2s ease,
          box-shadow 0.2s ease;
        border-bottom: 1px solid rgba(241, 245, 249, 0.7);

        &:nth-child(even) {
          background: rgba(248, 250, 252, 0.45);
        }

        &:last-child {
          border-bottom: none;
        }

        &:hover {
          background: linear-gradient(
            90deg,
            rgba(239, 246, 255, 0.9) 0%,
            rgba(224, 231, 255, 0.6) 100%
          ) !important;
          box-shadow:
            inset 3px 0 0 $primary,
            0 1px 0 rgba(59, 130, 246, 0.08);
        }

        td {
          padding: 5px 8px;
          font-size: 12px;
          color: $text-base;
          border-right: 1px solid rgba(241, 245, 249, 0.6);
          transition: all 0.2s ease;
          line-height: 1.4;
          font-family: $font-stack;

          &:last-child {
            border-right: none;
          }

          .cell {
            font-family: inherit;
          }
        }
      }

      :deep(.el-table--striped) {
        .el-table__body {
          tr.el-table__row--striped {
            background: rgba(248, 250, 252, 0.55);
          }
        }
      }

      .process-info {
        display: flex;
        flex-direction: column;
        gap: 1px;
        align-items: center;
        justify-content: center;

        .process-name {
          font-weight: 700;
          color: $primary-darker;
          font-size: 12px;
          letter-spacing: 0.2px;
          line-height: 1.3;
          padding: 1px 8px;
          border-radius: $radius-chip;
          background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
          border: 1px solid rgba(59, 130, 246, 0.2);
        }

        small {
          font-size: 10px;
          color: $text-muted;
        }
      }

      .target-cd {
        color: $text-base;
        font-size: 12px;
        letter-spacing: 0.3px;
        font-family: $font-num;
        font-variant-numeric: tabular-nums;
        font-weight: 600;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid $border-soft;
        padding: 1px 6px;
        border-radius: 4px;
        display: inline-block;
        line-height: 1.4;
      }

      .target-name {
        color: $text-strong;
        font-size: 12px;
        font-weight: 600;
        line-height: 1.4;
      }

      .quantity {
        font-weight: 500;
        color: $text-base;
        font-size: 12px;
        letter-spacing: 0;
        font-family: $font-num;
        font-variant-numeric: tabular-nums;
        background: transparent;
        padding: 0;
        border-radius: 0;
        display: inline;
        border: none;
        line-height: 1.4;

        &.is-negative {
          color: #dc2626;
          font-weight: 700;
        }
      }

      :deep(.el-tag) {
        border-radius: $radius-chip;
        font-weight: 600;
        font-size: 11px;
        padding: 0 10px;
        height: 20px;
        line-height: 18px;
        border: 1px solid $border-soft;
        background: #fff;
        color: $text-soft;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        transition: all 0.2s ease;

        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 3px 6px rgba(15, 23, 42, 0.1);
        }
      }

      .machine-name {
        color: $text-soft;
        font-size: 12px;
        font-weight: 500;
        line-height: 1.4;
      }

      .action-buttons {
        display: flex;
        gap: 4px;
        align-items: center;
        justify-content: center;

        .el-button {
          padding: 0 10px;
          font-size: 11px;
          height: 24px;
          border-radius: 6px;
          font-weight: 600;
          transition: all 0.2s ease;
          box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
          line-height: 1;

          &.el-button--primary {
            background: $gradient-primary;
            border: none;
            color: #fff;

            &:hover {
              background: $gradient-primary-strong;
              transform: translateY(-1px);
              box-shadow: 0 6px 12px rgba(59, 130, 246, 0.35);
            }

            &:active {
              transform: translateY(0);
            }
          }

          &.el-button--danger {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            border: none;
            color: #fff;

            &:hover {
              background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
              transform: translateY(-1px);
              box-shadow: 0 6px 12px rgba(239, 68, 68, 0.35);
            }

            &:active {
              transform: translateY(0);
            }
          }
        }
      }
    }

    .pagination-wrapper {
      margin-top: 10px;
      display: flex;
      justify-content: center;
      padding: 4px 0 2px;

      :deep(.el-pagination) {
        font-family: $font-stack;

        .el-pagination__total,
        .el-pagination__jump {
          font-size: 12px;
          color: $text-soft;
          font-weight: 500;
        }

        .el-pagination__sizes {
          .el-input__wrapper {
            border-radius: 6px;
            box-shadow: 0 0 0 1px $border inset;
          }
        }

        .btn-prev,
        .btn-next {
          border-radius: 6px;
          background: #fff;
          border: 1px solid $border;
          color: $text-soft;
          min-width: 26px;
          height: 26px;
          transition: all 0.2s ease;

          &:hover {
            color: #fff;
            background: $gradient-primary;
            border-color: transparent;
            box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3);
          }
        }

        .el-pager li {
          border-radius: 6px;
          margin: 0 2px;
          min-width: 26px;
          height: 26px;
          line-height: 26px;
          font-weight: 600;
          font-size: 12px;
          color: $text-soft;
          background: #fff;
          border: 1px solid $border;
          transition: all 0.2s ease;

          &:hover {
            color: $primary;
            border-color: rgba(59, 130, 246, 0.4);
          }

          &.is-active {
            color: #fff;
            background: $gradient-primary;
            border-color: transparent;
            box-shadow:
              0 4px 10px rgba(59, 130, 246, 0.35),
              inset 0 1px 0 rgba(255, 255, 255, 0.35);
          }
        }
      }
    }

    .table-skeleton {
      padding: 14px 0;
    }

    .table-empty {
      padding: 36px 0;
    }
  }

  :deep(.edit-dialog) {
    .el-dialog {
      border-radius: 14px;
      box-shadow:
        0 20px 50px rgba(15, 23, 42, 0.18),
        0 8px 16px rgba(15, 23, 42, 0.08);
      border: 1px solid rgba(226, 232, 240, 0.7);
      overflow: hidden;
      font-family: $font-stack;
    }

    .el-dialog__header {
      padding: 12px 18px;
      border-bottom: 1px solid $border-soft;
      background: linear-gradient(
        180deg,
        rgba(255, 255, 255, 0.95) 0%,
        rgba(248, 250, 252, 0.95) 100%
      );
      position: relative;
      margin: 0;

      &::before {
        content: '';
        position: absolute;
        inset: 0 0 auto 0;
        height: 3px;
        background: linear-gradient(90deg, $primary 0%, $accent 100%);
      }

      .el-dialog__title {
        font-weight: 700;
        font-size: 14px;
        color: $text-strong;
        letter-spacing: 0.2px;
        font-family: $font-stack;
      }
    }

    .el-dialog__body {
      padding: 14px 18px;
      background: #ffffff;
    }

    .edit-dialog-content {
      .form-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 8px;
      }

      :deep(.el-form-item) {
        margin-bottom: 0;
      }

      :deep(.el-form-item__label) {
        font-weight: 600;
        color: $text-soft;
        font-size: 12px;
        padding-bottom: 3px;
        padding-top: 0;
        line-height: 1.4;
        margin-bottom: 0;
        letter-spacing: 0.2px;
        font-family: $font-stack;
      }

      :deep(.el-form-item__content) {
        line-height: 1.4;
      }

      .readonly-field {
        :deep(.el-input__wrapper) {
          background: $surface-1;
          border: 1px solid $border-soft;
          box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
          cursor: not-allowed;
          padding: 4px 10px;
          min-height: 30px;
          border-radius: 7px;
          transition: all 0.2s ease;

          .el-input__inner {
            color: $text-base;
            font-size: 12px;
            padding: 0;
            line-height: 1.4;
            font-weight: 600;
            font-family: $font-stack;
          }
        }

        :deep(.el-input.is-disabled) {
          .el-input__wrapper {
            background: $surface-1;
          }
        }
      }

      .editable-field {
        :deep(.el-input-number) {
          width: 100%;

          .el-input__wrapper {
            border-radius: 8px;
            border: 1px solid rgba(59, 130, 246, 0.5);
            box-shadow:
              0 0 0 3px rgba(59, 130, 246, 0.08),
              0 2px 6px rgba(59, 130, 246, 0.08);
            transition: all 0.2s ease;
            background: #ffffff;
            padding: 4px 10px;
            min-height: 34px;

            &:hover {
              border-color: $primary-strong;
              box-shadow:
                0 0 0 3px rgba(59, 130, 246, 0.14),
                0 4px 10px rgba(59, 130, 246, 0.15);
            }

            &.is-focus {
              border-color: $primary-strong;
              box-shadow:
                0 0 0 3px rgba(59, 130, 246, 0.2),
                0 4px 12px rgba(59, 130, 246, 0.2);
            }

            .el-input__inner {
              font-size: 14px;
              font-weight: 700;
              color: $text-strong;
              text-align: left;
              padding: 0;
              line-height: 1.4;
              font-family: $font-num;
              font-variant-numeric: tabular-nums;
            }
          }

          .el-input-number__increase,
          .el-input-number__decrease {
            background: $surface-1;
            border-left: 1px solid $border-soft;
            color: $text-muted;
            transition: all 0.2s ease;
            width: 24px;

            &:hover {
              background: $gradient-primary;
              color: #fff;
            }
          }
        }
      }
    }

    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      padding: 10px 18px 12px;
      border-top: 1px solid $border-soft;
      background: $surface-1;

      .el-button {
        min-width: 84px;
        height: 30px;
        border-radius: 7px;
        font-weight: 600;
        font-size: 12px;
        transition: all 0.2s ease;
        font-family: $font-stack;

        &.save-btn {
          background: $gradient-primary;
          border: none;
          color: #fff;
          box-shadow:
            0 4px 10px rgba(59, 130, 246, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);

          &:hover {
            transform: translateY(-1px);
            background: $gradient-primary-strong;
            box-shadow:
              0 6px 14px rgba(59, 130, 246, 0.4),
              inset 0 1px 0 rgba(255, 255, 255, 0.3);
          }

          &:active {
            transform: translateY(0);
          }
        }

        &:not(.save-btn) {
          background: #fff;
          border: 1px solid $border;
          color: $text-soft;

          &:hover {
            background: $surface-1;
            border-color: #cbd5e1;
            color: $text-base;
            transform: translateY(-1px);
            box-shadow: 0 3px 6px rgba(15, 23, 42, 0.06);
          }
        }
      }
    }
  }
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
