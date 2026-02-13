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
      <template #header>
        <div class="search-header">
          <el-icon><Search /></el-icon>
          <span>検索条件</span>
        </div>
      </template>
      <el-form
        :model="searchForm"
        label-width="80px"
        class="search-form"
        @keyup.enter.prevent="handleSearch"
      >
        <el-row :gutter="16" class="search-row">
          <el-col :span="6">
            <el-form-item label="キーワード">
              <el-input
                v-model="searchForm.keyword"
                placeholder="製品名・品番で検索"
                clearable
                size="default"
                class="keyword-input"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
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
          <el-col :span="6">
            <div class="search-actions">
              <el-button type="primary" :icon="Search" @click="handleSearch" class="search-btn"
                >検索</el-button
              >
              <el-button :icon="Refresh" @click="handleReset" class="reset-btn">リセット</el-button>
            </div>
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
              印刷
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
          height="520"
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
          <el-table-column prop="process_cd" label="工程" width="90" align="center">
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

          <el-table-column label="数量" width="110" align="center">
            <template #default="{ row }">
              <span class="quantity">{{ Number(row.quantity || 0).toLocaleString() }}</span>
              <small v-if="row.unit" class="unit">{{ row.unit }}</small>
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
          <div ref="dailyTrendChartRef" class="chart-container" style="height: 250px"></div>
        </div>
        <div class="chart-item">
          <div class="chart-item-header">
            <span class="chart-item-title">工程別生産量</span>
          </div>
          <div ref="processChartRef" class="chart-container" style="height: 250px"></div>
        </div>
        <div class="chart-item">
          <div class="chart-item-header">
            <span class="chart-item-title">取引タイプ分布</span>
          </div>
          <div ref="typeChartRef" class="chart-container" style="height: 250px"></div>
        </div>
        <div class="chart-item">
          <div class="chart-item-header">
            <span class="chart-item-title">製品生産量TOP10</span>
          </div>
          <div ref="productChartRef" class="chart-container" style="height: 250px"></div>
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
import { ref, reactive, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Search,
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
  keyword: '',
  date_from: '',
  date_to: '',
  process_cd: '',
  transaction_type: '実績',
})

const createOffsetDate = (offset: number) => {
  const date = new Date()
  date.setDate(date.getDate() + offset)
  return date
}

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

const loadChartData = async () => {
  try {
    const params = {
      page: 1,
      limit: 10000, // 大きな値を設定して全データを取得
      process_cd: searchForm.process_cd || undefined,
      transaction_type: searchForm.transaction_type || undefined,
      keyword: searchForm.keyword || undefined,
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
      keyword: searchForm.keyword || undefined,
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

const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    date_from: '',
    date_to: '',
    process_cd: activeProcessTab.value === 'ALL' ? '' : activeProcessTab.value,
    transaction_type: '実績',
  })
  // ソート状態をリセット
  sortState.prop = ''
  sortState.order = ''
  setDefaultDateRange()
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

const formatDateTime = (value: string) => {
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
    if (searchForm.keyword && searchForm.keyword.trim()) {
      filterInfo.push('キーワード: ' + searchForm.keyword.trim())
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
      keyword: searchForm.keyword || undefined,
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

    if (searchForm.keyword && searchForm.keyword.trim()) {
      filterInfo.push('キーワード: ' + searchForm.keyword.trim())
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
    groupedData.forEach((rows, processKey) => {
      rows.sort((a, b) => {
        const timeA = new Date(a.transaction_time).getTime()
        const timeB = new Date(b.transaction_time).getTime()
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
        htmlParts.push('<td>' + formatDateTime(row.transaction_time) + '</td>')
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

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  dailyTrendChart?.dispose()
  processChart?.dispose()
  typeChart?.dispose()
  productChart?.dispose()
})
</script>

<style scoped lang="scss">
.production-actual-management {
  padding: 10px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  min-height: 100vh;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding: 12px 24px;
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border-radius: 12px;
    border: 1px solid rgba(226, 232, 240, 0.8);
    box-shadow:
      0 2px 8px rgba(0, 0, 0, 0.04),
      0 1px 2px rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;

    &:hover {
      box-shadow:
        0 4px 12px rgba(0, 0, 0, 0.08),
        0 2px 4px rgba(0, 0, 0, 0.08);
    }

    .page-title {
      display: flex;
      align-items: center;
      gap: 16px;

      .title-icon {
        width: 48px;
        height: 48px;
        border-radius: 14px;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 24px;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        transition: transform 0.2s ease;

        &:hover {
          transform: scale(1.05);
        }
      }

      h1 {
        margin: 0;
        font-size: 22px;
        font-weight: 700;
        color: #1e293b;
        letter-spacing: -0.02em;
      }

      p {
        margin: 4px 0 0 0;
        color: #64748b;
        font-size: 14px;
        font-weight: 400;
      }
    }

    .action-btn {
      border-radius: 8px;
      font-weight: 500;
      transition: all 0.2s ease;

      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }
    }
  }

  .search-card {
    margin-bottom: 10px;
    border-radius: 10px;
    border: 1px solid rgba(226, 232, 240, 0.8);
    box-shadow:
      0 2px 8px rgba(0, 0, 0, 0.04),
      0 1px 2px rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;

    &:hover {
      box-shadow:
        0 4px 12px rgba(0, 0, 0, 0.08),
        0 2px 4px rgba(0, 0, 0, 0.08);
    }

    :deep(.el-card__header) {
      padding: 10px 16px;
      border-bottom: 1px solid #f1f5f9;
    }

    :deep(.el-card__body) {
      padding: 12px 16px 10px;
    }

    .search-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 700;
      color: #1e293b;
      font-size: 14px;

      .el-icon {
        color: #3b82f6;
        font-size: 16px;
      }
    }

    .search-form {
      padding: 4px 0 0;

      .search-row {
        align-items: center;
      }

      :deep(.el-form-item) {
        margin-bottom: 0;
      }

      :deep(.el-form-item__label) {
        font-weight: 600;
        color: #475569;
        font-size: 13px;
        padding-bottom: 0;
        line-height: 32px;
      }

      :deep(.el-form-item__content) {
        line-height: 32px;
      }

      .keyword-input {
        :deep(.el-input__wrapper) {
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
          transition: all 0.2s ease;

          &:hover {
            box-shadow: 0 2px 6px rgba(59, 130, 246, 0.15);
          }

          &.is-focus {
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
          }
        }
      }
    }

    .search-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      padding-top: 0;
      align-items: center;

      .search-btn {
        min-width: 90px;
        border-radius: 8px;
        font-weight: 600;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        border: none;
        box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);
        transition: all 0.2s ease;

        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
          background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        }

        &:active {
          transform: translateY(0);
        }
      }

      .reset-btn {
        min-width: 90px;
        border-radius: 8px;
        font-weight: 500;
        color: #64748b;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;

        &:hover {
          background: #f1f5f9;
          border-color: #cbd5e1;
          color: #475569;
          transform: translateY(-1px);
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
        }

        &:active {
          transform: translateY(0);
        }
      }
    }

    .date-input-group {
      display: flex;
      align-items: center;
      gap: 8px;

      .date-picker {
        flex: 1;
        min-width: 0;

        :deep(.el-input__wrapper) {
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
          transition: all 0.2s ease;

          &:hover {
            box-shadow: 0 2px 6px rgba(59, 130, 246, 0.15);
          }

          &.is-focus {
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
          }
        }
      }

      .quick-buttons {
        display: flex;
        flex-direction: row;
        gap: 4px;
        flex-shrink: 0;

        .date-btn {
          font-size: 12px;
          padding: 6px 12px;
          min-width: 50px;
          border-radius: 6px;
          font-weight: 500;
          transition: all 0.2s ease;
          border: 1px solid transparent;

          &.yesterday {
            color: #64748b;
            background: #f8fafc;

            &:hover {
              background: #e2e8f0;
              color: #475569;
              border-color: #cbd5e1;
            }
          }

          &.today {
            color: #fff;
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            border-color: #2563eb;
            box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);

            &:hover {
              background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
              box-shadow: 0 3px 8px rgba(59, 130, 246, 0.4);
              transform: translateY(-1px);
            }
          }

          &.tomorrow {
            color: #64748b;
            background: #f8fafc;

            &:hover {
              background: #e2e8f0;
              color: #475569;
              border-color: #cbd5e1;
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
    border-radius: 12px;
    border: 1px solid rgba(226, 232, 240, 0.8);
    box-shadow:
      0 2px 8px rgba(0, 0, 0, 0.04),
      0 1px 2px rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;

    &:hover {
      box-shadow:
        0 4px 12px rgba(0, 0, 0, 0.08),
        0 2px 4px rgba(0, 0, 0, 0.08);
    }

    .process-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;

      .title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 700;
        color: #1e293b;
        font-size: 15px;

        .el-icon {
          color: #3b82f6;
          font-size: 18px;
        }
      }

      .type-summary-inline {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        flex: 1;

        .inline-label {
          font-size: 12px;
          font-weight: 700;
          color: #475569;
        }

        .type-chip {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          border-radius: 20px;
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          border: 1px solid rgba(226, 232, 240, 0.8);
          font-size: 12px;
          color: #334155;
          transition: all 0.2s ease;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
            border-color: #cbd5e1;
          }

          .type-name {
            font-weight: 700;
            color: #1e293b;
          }

          .type-values {
            display: flex;
            align-items: center;
            gap: 4px;
            color: #64748b;
            font-weight: 500;

            .divider {
              color: #cbd5e1;
              margin: 0 2px;
            }
          }
        }
      }

      .record-hint {
        font-size: 13px;
        color: #64748b;
        font-weight: 600;
        padding: 4px 12px;
        background: #f1f5f9;
        border-radius: 12px;
      }
    }

    .process-tabs {
      margin-bottom: 16px;

      :deep(.el-tabs__item) {
        font-weight: 600;
        color: #64748b;
        transition: all 0.2s ease;

        &.is-active {
          color: #3b82f6;
          font-weight: 700;
        }

        &:hover {
          color: #3b82f6;
        }
      }
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 0;

      .stat-card {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 12px;
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 12px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);

        &:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
          border-color: rgba(59, 130, 246, 0.3);
        }

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          transition: all 0.3s ease;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

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
            background: linear-gradient(135deg, #06b6d4 0%, #0ea5e9 100%);
          }
          &.neutral {
            background: linear-gradient(135deg, #64748b 0%, #475569 100%);
          }

          &:hover {
            transform: scale(1.1) rotate(5deg);
          }
        }

        .stat-label {
          font-size: 13px;
          color: #64748b;
          font-weight: 600;
          margin-bottom: 4px;
        }

        .stat-value {
          font-size: 24px;
          font-weight: 700;
          color: #1e293b;
          display: flex;
          align-items: baseline;
          gap: 4px;
          letter-spacing: -0.02em;

          small {
            font-size: 14px;
            font-weight: 500;
            color: #64748b;
          }
        }
      }
    }
  }

  .chart-card {
    margin-bottom: 10px;
    border-radius: 12px;
    border: 1px solid rgba(226, 232, 240, 0.8);
    box-shadow:
      0 2px 8px rgba(0, 0, 0, 0.04),
      0 1px 2px rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;

    &:hover {
      box-shadow:
        0 4px 12px rgba(0, 0, 0, 0.08),
        0 2px 4px rgba(0, 0, 0, 0.08);
    }

    :deep(.el-card__header) {
      padding: 12px 20px;
      border-bottom: 1px solid #f1f5f9;
      background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    }

    :deep(.el-card__body) {
      padding: 16px;
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
        color: #1e293b;
        font-size: 15px;
        font-family: '游ゴシック', 'Yu Gothic', 'YuGothic', 'Meiryo', 'メイリオ', sans-serif;

        .el-icon {
          color: #3b82f6;
          font-size: 18px;
        }
      }

      .print-btn {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        border: none;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
        transition: all 0.3s ease;

        &:hover {
          background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
          box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
          transform: translateY(-1px);
        }

        &:active {
          transform: translateY(0);
          box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
        }
      }
    }

    .charts-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;

      .chart-item {
        background: #ffffff;
        border: 1px solid rgba(226, 232, 240, 0.6);
        border-radius: 10px;
        padding: 12px;
        transition: all 0.3s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

        &:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
          border-color: rgba(59, 130, 246, 0.3);
        }

        .chart-item-header {
          margin-bottom: 12px;
          padding-bottom: 10px;
          border-bottom: 2px solid #f1f5f9;
          position: relative;

          &::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 40px;
            height: 2px;
            background: linear-gradient(90deg, #3b82f6, #60a5fa);
            border-radius: 2px;
          }

          .chart-item-title {
            font-weight: 700;
            color: #1e293b;
            font-size: 13px;
            letter-spacing: 0.3px;
            font-family: '游ゴシック', 'Yu Gothic', 'YuGothic', 'Meiryo', 'メイリオ', sans-serif;
          }
        }

        .chart-container {
          width: 100%;
          min-height: 250px;
        }
      }
    }
  }

  .table-card {
    margin-bottom: 10px;
    border-radius: 12px;
    border: 1px solid rgba(226, 232, 240, 0.8);
    box-shadow:
      0 2px 8px rgba(0, 0, 0, 0.04),
      0 1px 2px rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;

    &:hover {
      box-shadow:
        0 4px 12px rgba(0, 0, 0, 0.08),
        0 2px 4px rgba(0, 0, 0, 0.08);
    }

    :deep(.el-card__body) {
      padding: 10px 20px 6px;
    }

    .table-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .table-title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 700;
        color: #1e293b;
        font-size: 15px;

        .el-icon {
          color: #3b82f6;
          font-size: 18px;
        }
      }

      .table-header-right {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .el-tag {
        border-radius: 12px;
        font-weight: 600;
        padding: 4px 12px;
      }

      .print-table-btn {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        border: none;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
        transition: all 0.3s ease;

        &:hover {
          background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
          box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
          transform: translateY(-1px);
        }

        &:active {
          transform: translateY(0);
          box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
        }
      }
    }

    .data-table {
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid rgba(226, 232, 240, 0.8);
      box-shadow:
        0 4px 16px rgba(0, 0, 0, 0.1),
        0 2px 4px rgba(0, 0, 0, 0.04);
      font-family: '游ゴシック', 'Yu Gothic', 'YuGothic', 'Meiryo', 'メイリオ', sans-serif;

      :deep(.el-table__header-wrapper) {
        border-radius: 12px 12px 0 0;
        overflow: hidden;
      }

      :deep(.el-table__header) {
        th {
          background: linear-gradient(135deg, #ffffff 0%, #f8fafc 50%, #f1f5f9 100%);
          padding: 4px 8px;
          font-weight: 700;
          color: #01173b;
          border-bottom: 2px solid #e2e8f0;
          border-right: 1px solid rgba(226, 232, 240, 0.6);
          position: relative;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-size: 11px;
          line-height: 1.4;

          &:last-child {
            border-right: none;
          }

          &::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, #3b82f6 50%, transparent 100%);
            opacity: 0.3;
          }
        }
      }

      :deep(.el-table__body-wrapper) {
        border-radius: 0 0 12px 12px;
      }

      :deep(.el-table__row) {
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border-bottom: 1px solid rgba(241, 245, 249, 0.6);

        &:nth-child(even) {
          background: rgba(248, 250, 252, 0.3);
        }

        &:last-child {
          border-bottom: none;
        }

        &:hover {
          background: linear-gradient(135deg, #f0f4ff 0%, #e0e7ff 100%) !important;
          transform: translateX(2px);
          box-shadow:
            inset 4px 0 0 #3b82f6,
            0 2px 12px rgba(59, 130, 246, 0.15);
          z-index: 1;
          position: relative;
        }

        td {
          padding: 4px 8px;
          font-size: 12px;
          color: #050505;
          border-right: 1px solid rgba(241, 245, 249, 0.6);
          transition: all 0.2s ease;
          line-height: 1.5;

          &:last-child {
            border-right: none;
          }
        }
      }

      :deep(.el-table--striped) {
        .el-table__body {
          tr.el-table__row--striped {
            background: rgba(248, 250, 252, 0.5);
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
          font-weight: 600;
          color: #051bda;
          font-size: 12px;
          letter-spacing: 0.2px;
          line-height: 1.3;
        }

        small {
          font-size: 10px;
          color: #64748b;
        }
      }

      .target-cd {
        // font-weight: 700;
        color: #252b35;
        font-size: 12px;
        letter-spacing: 0.3px;
        font-family: '游ゴシック体', monospace;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 1px 4px;
        border-radius: 3px;
        display: inline-block;
        line-height: 1.3;
      }

      .target-name {
        color: #080808;
        font-size: 12px;
        font-weight: 700;
        line-height: 1.4;
      }

      .quantity {
        font-weight: 700;
        color: #1e293b;
        font-size: 13px;
        letter-spacing: 0.3px;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        padding: 2px 6px;
        border-radius: 4px;
        display: inline-block;
        border: 1px solid rgba(59, 130, 246, 0.2);
        line-height: 1.3;
      }

      .unit {
        color: #64748b;
        font-size: 10px;
        margin-left: 3px;
        font-weight: 500;
      }

      :deep(.el-tag) {
        border-radius: 4px;
        font-weight: 600;
        font-size: 11px;
        padding: 2px 8px;
        border: none;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
        transition: all 0.2s ease;
        line-height: 1.3;

        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12);
        }
      }

      .machine-name {
        color: #860292;
        font-size: 12px;
        font-weight: 400;
        line-height: 1.4;
      }

      .action-buttons {
        display: flex;
        gap: 4px;
        align-items: center;
        justify-content: center;

        .el-button {
          padding: 3px 8px;
          font-size: 11px;
          border-radius: 4px;
          font-weight: 400;
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
          line-height: 1.3;

          &.el-button--primary {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            border: none;
            color: #fff;

            &:hover {
              background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
              transform: translateY(-2px);
              box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
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
              transform: translateY(-2px);
              box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
            }

            &:active {
              transform: translateY(0);
            }
          }
        }
      }
    }

    .pagination-wrapper {
      margin-top: 16px;
      display: flex;
      justify-content: center;
      padding: 8px 0;

      :deep(.el-pagination) {
        .el-pager li,
        .btn-prev,
        .btn-next {
          border-radius: 8px;
          transition: all 0.2s ease;

          &:hover {
            background: #3b82f6;
            color: #fff;
          }

          &.is-active {
            background: #3b82f6;
            color: #fff;
            font-weight: 700;
          }
        }
      }
    }

    .table-skeleton {
      padding: 20px 0;
    }

    .table-empty {
      padding: 48px 0;
    }
  }

  // 編集ダイアログスタイル
  :deep(.edit-dialog) {
    .el-dialog {
      border-radius: 10px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
      border: 1px solid rgba(226, 232, 240, 0.8);
    }

    .el-dialog__header {
      padding: 10px 16px;
      border-bottom: 1px solid #f1f5f9;
      background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
      border-radius: 10px 10px 0 0;

      .el-dialog__title {
        font-weight: 700;
        font-size: 15px;
        color: #1e293b;
        font-family: '游ゴシック', 'Yu Gothic', 'YuGothic', 'Meiryo', 'メイリオ', sans-serif;
      }
    }

    .el-dialog__body {
      padding: 12px 16px;
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
        color: #475569;
        font-size: 12px;
        padding-bottom: 3px;
        padding-top: 0;
        line-height: 1.4;
        margin-bottom: 0;
        font-family: '游ゴシック', 'Yu Gothic', 'YuGothic', 'Meiryo', 'メイリオ', sans-serif;
      }

      :deep(.el-form-item__content) {
        line-height: 1.4;
      }

      .readonly-field {
        :deep(.el-input__wrapper) {
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          border: 1px solid #e2e8f0;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
          cursor: not-allowed;
          padding: 5px 10px;
          min-height: 30px;
          border-radius: 6px;
          transition: all 0.2s ease;

          .el-input__inner {
            color: #475569;
            font-size: 12px;
            padding: 0;
            line-height: 1.4;
            font-family: '游ゴシック', 'Yu Gothic', 'YuGothic', 'Meiryo', 'メイリオ', sans-serif;
            font-weight: 500;
          }
        }

        :deep(.el-input.is-disabled) {
          .el-input__wrapper {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          }
        }
      }

      .editable-field {
        :deep(.el-input-number) {
          width: 100%;

          .el-input__wrapper {
            border-radius: 6px;
            border: 2px solid #3b82f6;
            box-shadow: 0 2px 4px rgba(59, 130, 246, 0.15);
            transition: all 0.2s ease;
            background: #ffffff;
            padding: 5px 10px;
            min-height: 32px;

            &:hover {
              border-color: #2563eb;
              box-shadow: 0 3px 8px rgba(59, 130, 246, 0.25);
            }

            &.is-focus {
              border-color: #2563eb;
              box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
            }

            .el-input__inner {
              font-size: 14px;
              font-weight: 700;
              color: #1e293b;
              text-align: left;
              padding: 0;
              line-height: 1.4;
              font-family: '游ゴシック', 'Yu Gothic', 'YuGothic', 'Meiryo', 'メイリオ', sans-serif;
            }
          }

          .el-input-number__increase,
          .el-input-number__decrease {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-left: 1px solid #e2e8f0;
            color: #64748b;
            transition: all 0.2s ease;
            width: 24px;

            &:hover {
              background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
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
      padding: 10px 16px;
      border-top: 1px solid #f1f5f9;
      background: #fafbfc;
      border-radius: 0 0 10px 10px;

      .el-button {
        min-width: 80px;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s ease;
        font-family: '游ゴシック', 'Yu Gothic', 'YuGothic', 'Meiryo', 'メイリオ', sans-serif;
        font-size: 12px;

        &.save-btn {
          background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
          border: none;
          box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);
          color: #fff;

          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
          }

          &:active {
            transform: translateY(0);
          }
        }

        &:not(.save-btn) {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          color: #64748b;

          &:hover {
            background: #f8fafc;
            border-color: #cbd5e1;
            color: #475569;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
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
