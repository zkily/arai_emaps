<template>
  <div class="material-forecast-container">
    <!-- ページヘッダー -->
    <div class="page-header">
      <div class="header-left">
        <div class="title-section">
          <div class="title-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="title-text">
            <h1 class="main-title">材料内示管理</h1>
            <p class="subtitle">Material Forecast Management</p>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button class="action-btn refresh-btn" @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          データ更新
        </el-button>
        <el-button class="action-btn print-btn" @click="handlePrint">
          <el-icon><Printer /></el-icon>
          印刷
        </el-button>
      </div>
    </div>

    <!-- 統計カード -->
    <div class="stats-container">
      <div class="stats-grid">
        <div class="stat-card primary">
          <div class="stat-icon">
            <el-icon><Box /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_products || 0 }}</div>
            <div class="stat-label">製品種類数</div>
          </div>
        </div>

        <div class="stat-card info">
          <div class="stat-icon">
            <el-icon><Goods /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_materials || 0 }}</div>
            <div class="stat-label">材料種類数</div>
          </div>
        </div>

        <div class="stat-card warning">
          <div class="stat-icon">
            <el-icon><OfficeBuilding /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_suppliers || 0 }}</div>
            <div class="stat-label">仕入先数</div>
          </div>
        </div>

        <div class="stat-card success">
          <div class="stat-icon">
            <el-icon><DataLine /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              {{ formatNumber(stats.total_forecast_units || 0) }}<span class="unit">本</span>
            </div>
            <div class="stat-label">内示数量合計</div>
          </div>
        </div>

        <div class="stat-card amount">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              {{ formatNumber(stats.total_material_required || 0) }}
            </div>
            <div class="stat-label">材料必要数合計</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 検索・フィルター -->
    <div class="search-section">
      <div class="search-container">
        <div class="search-row">
          <div class="search-group">
            <label class="search-label">年</label>
            <el-select
              v-model="searchForm.year"
              placeholder="選択"
              clearable
              @change="handleSearch"
              class="search-select"
            >
              <el-option
                v-for="period in availableYears"
                :key="period"
                :label="period + '年'"
                :value="period"
              />
            </el-select>
          </div>

          <div class="search-group">
            <label class="search-label">月</label>
            <div class="month-control-wrapper">
              <el-select
                v-model="searchForm.month"
                placeholder="選択"
                clearable
                @change="handleSearch"
                class="search-select"
              >
                <el-option v-for="m in 12" :key="m" :label="m + '月'" :value="m" />
              </el-select>
              <div class="month-navigation">
                <el-button
                  class="month-nav-btn prev-btn"
                  @click="handlePrevMonth"
                  :disabled="!canGoPrevMonth"
                >
                  <el-icon><ArrowLeft /></el-icon>
                </el-button>
                <el-button class="month-nav-btn current-btn" @click="handleCurrentMonth">
                  今月
                </el-button>
                <el-button
                  class="month-nav-btn next-btn"
                  @click="handleNextMonth"
                  :disabled="!canGoNextMonth"
                >
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </div>
          </div>

          <div class="search-group">
            <label class="search-label">仕入先</label>
            <el-select
              v-model="searchForm.supplier_cd"
              placeholder="全て"
              clearable
              @change="handleSearch"
              class="search-select supplier-select"
            >
              <el-option
                v-for="supplier in suppliers"
                :key="supplier.supplier_cd"
                :label="supplier.supplier_name"
                :value="supplier.supplier_cd"
              />
            </el-select>
          </div>

          <div class="search-group keyword-group">
            <label class="search-label">キーワード</label>
            <el-input
              v-model="searchForm.keyword"
              placeholder="製品名・材料名・仕入先名"
              clearable
              @input="handleKeywordSearch"
              class="search-input"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="search-group reset-group">
            <el-button @click="handleReset" class="reset-btn" plain>
              <el-icon><RefreshLeft /></el-icon>
              リセット
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- タブ切り替え -->
    <div class="tab-section">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="custom-tabs">
        <el-tab-pane label="製品別一覧" name="detail">
          <template #label>
            <span class="tab-label">
              <el-icon><Document /></el-icon>
              製品別一覧
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="材料別集計" name="summary">
          <template #label>
            <span class="tab-label">
              <el-icon><DataAnalysis /></el-icon>
              材料別集計
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- データテーブル -->
    <div class="table-section">
      <!-- 製品別一覧 -->
      <el-table
        v-if="activeTab === 'detail'"
        :data="tableData"
        v-loading="loading"
        stripe
        border
        class="data-table detail-table"
        :header-cell-style="headerCellStyle"
        :row-class-name="tableRowClassName"
        show-summary
        :summary-method="getDetailSummary"
        height="650"
      >
        <el-table-column prop="year" label="年" width="80" align="center" />
        <el-table-column prop="month" label="月" width="80" align="center" />
        <el-table-column prop="supplier_name" label="仕入先" width="130" sortable>
          <template #default="{ row }">
            <span class="supplier-cell">{{ row.supplier_name || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="material_name" label="材料名" width="150" sortable>
          <template #default="{ row }">
            <span>{{ row.material_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="製品名" width="160" sortable>
          <template #default="{ row }">
            <span class="product-name">{{ row.product_name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="forecast_units" label="内示数量" width="100" align="right">
          <template #default="{ row }">
            <span class="number-cell">{{ formatNumber(row.forecast_units) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="lot_size" label="ロットサイズ" width="130" align="right">
          <template #default="{ row }">
            <span class="number-cell">{{ row.lot_size || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="material_required" label="材料必要数" width="120" align="right">
          <template #default="{ row }">
            <span
              class="number-cell highlight"
              :class="{ 'no-data': row.material_required === null }"
            >
              {{ row.material_required !== null ? row.material_required : '-' }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 材料別集計 -->
      <el-table
        v-else
        :data="summaryData"
        v-loading="loading"
        stripe
        border
        class="data-table summary-table"
        :header-cell-style="headerCellStyle"
        :row-class-name="tableRowClassName"
        height="650"
      >
        <el-table-column prop="supplier_name" label="仕入先" width="150" sortable>
          <template #default="{ row }">
            <span class="supplier-cell">{{ row.supplier_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="material_name" label="材料名" width="160" sortable>
          <template #default="{ row }">
            <div class="material-cell">
              <span class="material-name">{{ row.material_name || '-' }}</span>
              <!-- <span class="material-cd">{{ row.material_cd }}</span> -->
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="product_count" label="製品数" width="90" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.product_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_forecast_units" label="内示数量合計" width="140" align="right">
          <template #default="{ row }">
            <span class="number-cell">{{ formatNumber(row.total_forecast_units) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="avg_lot_size" label="平均ロットサイズ" width="150" align="right">
          <template #default="{ row }">
            <span class="number-cell">{{
              row.avg_lot_size ? Math.round(row.avg_lot_size) : '-'
            }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="total_material_required"
          label="材料必要数合計"
          width="150"
          align="right"
        >
          <template #default="{ row }">
            <span class="number-cell highlight-total">
              {{ row.total_material_required !== null ? row.total_material_required : '-' }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  Refresh,
  Box,
  Goods,
  OfficeBuilding,
  DataLine,
  Search,
  RefreshLeft,
  Document,
  DataAnalysis,
  Printer,
  ArrowLeft,
  ArrowRight,
} from '@element-plus/icons-vue'
import {
  getForecastSummary,
  getForecastMonthly,
  getForecastBySupplier,
  getSupplierList,
} from '@/api/material'

// 响应式数据
const loading = ref(false)
const activeTab = ref('detail')
const tableData = ref<any[]>([])
const summaryData = ref<any[]>([])
const suppliers = ref<any[]>([])
const periods = ref<any[]>([])

const stats = ref({
  total_products: 0,
  total_materials: 0,
  total_suppliers: 0,
  total_forecast_units: 0,
  total_material_required: 0,
})

const searchForm = reactive({
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  supplier_cd: '',
  keyword: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 15,
  total: 0,
})

// 计算可用年份
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let i = currentYear - 2; i <= currentYear + 2; i++) {
    years.push(i)
  }
  return years
})

// 月份导航相关计算属性
const canGoPrevMonth = computed(() => {
  if (!searchForm.year || !searchForm.month) return false
  const currentYear = new Date().getFullYear()
  const currentMonth = new Date().getMonth() + 1
  if (searchForm.year < currentYear - 2) return false
  if (searchForm.year === currentYear - 2 && searchForm.month <= 1) return false
  return true
})

const canGoNextMonth = computed(() => {
  if (!searchForm.year || !searchForm.month) return false
  const currentYear = new Date().getFullYear()
  const currentMonth = new Date().getMonth() + 1
  if (searchForm.year > currentYear + 2) return false
  if (searchForm.year === currentYear + 2 && searchForm.month >= 12) return false
  return true
})

// 月份导航方法
const handlePrevMonth = () => {
  if (!searchForm.year || !searchForm.month) return
  if (searchForm.month === 1) {
    searchForm.month = 12
    searchForm.year = searchForm.year - 1
  } else {
    searchForm.month = searchForm.month - 1
  }
  handleSearch()
}

const handleNextMonth = () => {
  if (!searchForm.year || !searchForm.month) return
  if (searchForm.month === 12) {
    searchForm.month = 1
    searchForm.year = searchForm.year + 1
  } else {
    searchForm.month = searchForm.month + 1
  }
  handleSearch()
}

const handleCurrentMonth = () => {
  const now = new Date()
  searchForm.year = now.getFullYear()
  searchForm.month = now.getMonth() + 1
  handleSearch()
}

// 表格样式
const headerCellStyle = {
  backgroundColor: '#f5f7fa',
  color: '#303133',
  fontWeight: '600',
  fontSize: '13px',
}

const tableRowClassName = ({ rowIndex }: { rowIndex: number }) => {
  return rowIndex % 2 === 0 ? 'even-row' : 'odd-row'
}

// 格式化数字
const formatNumber = (num: number | null) => {
  if (num === null || num === undefined) return '-'
  return num.toLocaleString()
}

// 计算製品別一覧合计
const getDetailSummary = (param: { columns: any[]; data: any[] }) => {
  const { columns, data } = param
  const sums: string[] = []

  // 判断是否只有年月筛选条件（可以使用stats数据）
  const hasOnlyYearMonthFilter =
    searchForm.year && searchForm.month && !searchForm.supplier_cd && !searchForm.keyword

  columns.forEach((column, index) => {
    if (index === 0) {
      // 年列
      sums[index] = '合计'
    } else if (index === 1) {
      // 月列
      sums[index] = ''
    } else if (column.property === 'forecast_units') {
      // 内示数量合计 - 现在显示全部数据，所以计算全部数据的合计
      let sum = 0
      if (hasOnlyYearMonthFilter && stats.value.total_forecast_units) {
        // 使用统计数据（所有数据的合计）
        sum = stats.value.total_forecast_units
      } else {
        // 计算全部数据合计
        const values = tableData.value.map((item) => Number(item[column.property]))
        sum = values.reduce((prev, curr) => {
          const value = Number(curr)
          if (!isNaN(value)) {
            return prev + curr
          } else {
            return prev
          }
        }, 0)
      }
      sums[index] = formatNumber(sum)
    } else if (column.property === 'material_required') {
      // 材料必要数合计 - 现在显示全部数据，所以计算全部数据的合计
      let sum = 0
      if (hasOnlyYearMonthFilter && stats.value.total_material_required) {
        // 使用统计数据（所有数据的合计）
        sum = stats.value.total_material_required
      } else {
        // 计算全部数据合计
        const values = tableData.value.map((item) => {
          const value = item[column.property]
          return value !== null && value !== undefined ? Number(value) : 0
        })
        sum = values.reduce((prev, curr) => {
          if (!isNaN(curr)) {
            return prev + curr
          } else {
            return prev
          }
        }, 0)
      }
      sums[index] = sum > 0 ? sum.toFixed(1) : '-'
    } else {
      sums[index] = ''
    }
  })

  return sums
}

// 防抖搜索
let searchTimer: ReturnType<typeof setTimeout> | null = null
const handleKeywordSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    handleSearch()
  }, 300)
}

// 获取数据
const fetchDetailData = async () => {
  try {
    loading.value = true
    const params: any = {
      page: 1,
      pageSize: 10000, // 获取所有数据
    }
    if (searchForm.year) params.year = searchForm.year
    if (searchForm.month) params.month = searchForm.month
    if (searchForm.supplier_cd) params.supplier_cd = searchForm.supplier_cd
    if (searchForm.keyword) params.keyword = searchForm.keyword

    const res = await getForecastMonthly({
      target_year: Number(searchForm.year) || new Date().getFullYear(),
      target_month: Number(searchForm.month) || new Date().getMonth() + 1,
      page: params.page,
      pageSize: params.pageSize,
    })
    const data = (res as any)?.data
    if (data?.list) {
      tableData.value = data.list
      pagination.total = data.total ?? 0
    }
  } catch (err) {
    console.error('获取详情数据失败:', err)
    ElMessage.error('データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const fetchSummaryData = async () => {
  try {
    loading.value = true
    const params: any = {
      page: 1,
      pageSize: 10000, // 获取所有数据
    }
    if (searchForm.year) params.year = searchForm.year
    if (searchForm.month) params.month = searchForm.month
    if (searchForm.supplier_cd) params.supplier_cd = searchForm.supplier_cd
    if (searchForm.keyword) params.keyword = searchForm.keyword

    const res = await getForecastBySupplier({
      target_year: Number(searchForm.year) || new Date().getFullYear(),
      target_month: Number(searchForm.month) || new Date().getMonth() + 1,
    })
    const data = (res as any)?.data
    if (Array.isArray(data)) {
      summaryData.value = data
      pagination.total = data.length
    } else if (data?.list) {
      summaryData.value = data.list
      pagination.total = data.total ?? 0
    }
  } catch (err) {
    console.error('获取集计数据失败:', err)
    ElMessage.error('データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getForecastSummary({
      target_year: searchForm.year ? Number(searchForm.year) : undefined,
      target_month: searchForm.month ? Number(searchForm.month) : undefined,
    })
    const d = (res as any)?.data
    if (d) {
      stats.value = {
        total_products: d.material_count ?? 0,
        total_materials: d.material_count ?? 0,
        total_suppliers: d.supplier_count ?? 0,
        total_forecast_units: d.total_planned_usage ?? 0,
        total_material_required: d.total_order_amount ?? 0,
      }
    }
  } catch (err) {
    console.error('获取统计数据失败:', err)
  }
}

const fetchSuppliers = async () => {
  try {
    const res = await getSupplierList()
    suppliers.value = (res as any)?.data ?? []
  } catch (err) {
    console.error('获取仕入先列表失败:', err)
  }
}

// 事件处理
const handleSearch = () => {
  pagination.page = 1
  fetchData()
  fetchStats()
}

const handleReset = () => {
  searchForm.year = new Date().getFullYear()
  searchForm.month = new Date().getMonth() + 1
  searchForm.supplier_cd = ''
  searchForm.keyword = ''
  pagination.page = 1
  fetchData()
  fetchStats()
}

const handleTabChange = () => {
  pagination.page = 1
  fetchData()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchData()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  fetchData()
}

const refreshData = () => {
  fetchData()
  fetchStats()
  ElMessage.success('データを更新しました')
}

// 打印功能
const handlePrint = async () => {
  try {
    // 检查是否有年月筛选条件
    if (!searchForm.year || !searchForm.month) {
      ElMessage.warning('印刷するには年月を選択してください')
      return
    }

    ElMessage.info('データを取得中...')

    // 获取所有数据（只按年月筛选，不分页）
    let allPrintData: any[] = []
    if (activeTab.value === 'detail') {
      const res = await getForecastMonthly({
        target_year: Number(searchForm.year),
        target_month: Number(searchForm.month),
        page: 1,
        pageSize: 10000,
      })
      const data = (res as any)?.data
      if (data?.list) allPrintData = data.list
    } else {
      const res = await getForecastBySupplier({
        target_year: Number(searchForm.year),
        target_month: Number(searchForm.month),
      })
      const data = (res as any)?.data
      if (Array.isArray(data)) allPrintData = data
      else if (data?.list) allPrintData = data.list
    }

    if (allPrintData.length === 0) {
      ElMessage.warning('印刷するデータがありません')
      return
    }

    ElMessage.info('印刷プレビューを生成中...')

    const statsRes = await getForecastSummary({
      target_year: Number(searchForm.year),
      target_month: Number(searchForm.month),
    })
    const printStatsData = (statsRes as any)?.data
    const printStats = printStatsData
      ? {
          total_products: printStatsData.material_count ?? 0,
          total_materials: printStatsData.material_count ?? 0,
          total_suppliers: printStatsData.supplier_count ?? 0,
          total_forecast_units: printStatsData.total_planned_usage ?? 0,
          total_material_required: printStatsData.total_order_amount ?? 0,
        }
      : stats.value

    const printContent = generatePrintHtml(allPrintData, printStats)
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html>
        <head>
          <title>材料内示管理 - ${activeTab.value === 'detail' ? '製品別一覧' : '材料別集計'}</title>
          <meta charset="UTF-8">
          <style>
            body {
              font-family: 'Meiryo', 'Yu Gothic', sans-serif;
              margin: 0.3cm;
              font-size: 9pt;
              line-height: 1.2;
              background-color: #ffffff;
              color: #000000;
            }
            .print-header {
              text-align: center;
              margin-bottom: 4mm;
              border-bottom: 1px solid #667eea;
              padding-bottom: 2mm;
            }
            .print-title {
              font-size: 14pt;
              font-weight: bold;
              color: #2c3e50;
              margin-bottom: 1mm;
            }
            .print-subtitle {
              font-size: 10pt;
              color: #7f8c8d;
              margin-bottom: 2mm;
            }
            .print-info {
              display: flex;
              justify-content: space-between;
              font-size: 8pt;
              color: #606266;
              margin-bottom: 2mm;
            }
            .print-stats {
              display: grid;
              grid-template-columns: repeat(5, 1fr);
              gap: 2mm;
              margin-bottom: 3mm;
              padding: 2mm;
              background: #f5f7fa;
              border-radius: 2px;
            }
            .print-stat-item {
              text-align: center;
            }
            .print-stat-label {
              font-size: 7pt;
              color: #7f8c8d;
              margin-bottom: 1mm;
            }
            .print-stat-value {
              font-size: 9pt;
              font-weight: bold;
              color: #2c3e50;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin: 2mm 0;
              font-size: 8pt;
              table-layout: fixed;
            }
            th, td {
              border: 1px solid #dee2e6;
              padding: 1.5mm 1.5mm;
              text-align: left;
              line-height: 1.2;
            }
            /* 製品別一覧表格（4列） */
            .detail-table th:nth-child(1),
            .detail-table td:nth-child(1) {
              width: 40%;
            }
            .detail-table th:nth-child(2),
            .detail-table td:nth-child(2),
            .detail-table th:nth-child(3),
            .detail-table td:nth-child(3),
            .detail-table th:nth-child(4),
            .detail-table td:nth-child(4) {
              width: 20%;
            }
            /* 材料別集計表格（6列） */
            .summary-table th:nth-child(1),
            .summary-table td:nth-child(1),
            .summary-table th:nth-child(2),
            .summary-table td:nth-child(2) {
              width: 20%;
            }
            .summary-table th:nth-child(3),
            .summary-table td:nth-child(3),
            .summary-table th:nth-child(4),
            .summary-table td:nth-child(4),
            .summary-table th:nth-child(5),
            .summary-table td:nth-child(5),
            .summary-table th:nth-child(6),
            .summary-table td:nth-child(6) {
              width: 13.33%;
            }
            .summary-row {
              background: #e8f4f8 !important;
              font-weight: bold;
            }
            .summary-row td {
              background: #e8f4f8 !important;
            }
            th {
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white;
              font-weight: bold;
              text-align: center;
              font-size: 8pt;
              padding: 2mm 1.5mm;
            }
            td {
              background: #ffffff;
            }
            tr:nth-child(even) td {
              background: #f8f9fa;
            }
            .text-center {
              text-align: center;
            }
            .text-right {
              text-align: right;
            }
            .print-footer {
              margin-top: 4mm;
              padding-top: 2mm;
              border-top: 1px solid #dee2e6;
              font-size: 7pt;
              color: #909399;
              text-align: right;
            }
            .supplier-group {
              margin-bottom: 5mm;
            }
            .supplier-group-title {
              background: #ffffff;
              color: #000000;
              padding: 2mm 3mm;
              font-weight: bold;
              font-size: 9pt;
              margin-bottom: 2mm;
              border: 1px solid #000000;
              border-radius: 2px;
            }
            .material-group {
              margin-bottom: 3mm;
              margin-left: 3mm;
              page-break-inside: avoid;
              break-inside: avoid;
            }
            .material-group-title {
              background: #ffffff;
              color: #000000;
              padding: 1.5mm 2.5mm;
              font-weight: bold;
              font-size: 8pt;
              margin-bottom: 1.5mm;
              border: 1px solid #000000;
              border-radius: 2px;
            }
            @page {
              size: A4 portrait;
              margin: 1.2cm 1.2cm;
            }
            @media print {
              body {
                margin: 0;
              }
              .material-group {
                page-break-inside: avoid;
                break-inside: avoid;
              }
            }
          </style>
        </head>
        <body>${printContent}</body>
        </html>
      `)
      printWindow.document.close()

      // 监听打印对话框关闭，自动关闭预览窗口
      const mediaQueryList = printWindow.matchMedia('print')
      const handlePrintChange = (mql: MediaQueryList | MediaQueryListEvent) => {
        if (!mql.matches) {
          // 打印对话框已关闭，关闭预览窗口
          setTimeout(() => {
            printWindow.close()
          }, 100)
          mediaQueryList.removeListener(handlePrintChange as any)
        }
      }

      // 兼容不同浏览器的API
      if (mediaQueryList.addEventListener) {
        mediaQueryList.addEventListener('change', handlePrintChange)
      } else if (mediaQueryList.addListener) {
        mediaQueryList.addListener(handlePrintChange)
      }

      // 备用方案：使用 onafterprint 事件（如果支持）
      printWindow.onafterprint = () => {
        setTimeout(() => {
          printWindow.close()
        }, 100)
      }

      // 等待内容加载完成后打印
      setTimeout(() => {
        printWindow.print()
      }, 250)
    }
  } catch (error) {
    console.error('打印失败:', error)
    ElMessage.error('印刷に失敗しました')
  }
}

// 生成打印HTML内容
const generatePrintHtml = (data: any[], printStats?: any) => {
  const currentDate = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

  const isDetail = activeTab.value === 'detail'
  const title = isDetail ? '材料内示管理 - 製品別一覧' : '材料内示管理 - 材料別集計'

  // 使用传入的统计数据，如果没有则使用默认的
  const displayStats = printStats || stats.value

  // 生成统计信息
  const statsHtml = `
    <div class="print-stats">
      <div class="print-stat-item">
        <div class="print-stat-label">製品種類数</div>
        <div class="print-stat-value">${displayStats.total_products || 0}</div>
      </div>
      <div class="print-stat-item">
        <div class="print-stat-label">材料種類数</div>
        <div class="print-stat-value">${displayStats.total_materials || 0}</div>
      </div>
      <div class="print-stat-item">
        <div class="print-stat-label">仕入先数</div>
        <div class="print-stat-value">${displayStats.total_suppliers || 0}</div>
      </div>
      <div class="print-stat-item">
        <div class="print-stat-label">内示数量合計</div>
        <div class="print-stat-value">${formatNumber(displayStats.total_forecast_units || 0)}</div>
      </div>
      <div class="print-stat-item">
        <div class="print-stat-label">材料必要数合計</div>
        <div class="print-stat-value">${formatNumber(displayStats.total_material_required || 0)}</div>
      </div>
    </div>
  `

  // 按仕入先分组数据
  const groupedData: Record<string, any[]> = {}
  data.forEach((row) => {
    const supplierName = row.supplier_name || '未分類'
    if (!groupedData[supplierName]) {
      groupedData[supplierName] = []
    }
    groupedData[supplierName].push(row)
  })

  // 生成表格（按仕入先分组，再按材料名分组）
  let tableHtml = ''
  if (isDetail) {
    // 製品別一覧表格（按仕入先分组，再按材料名分组，移除製品CD字段和年月字段）
    tableHtml = Object.keys(groupedData)
      .sort()
      .map((supplierName) => {
        const groupData = groupedData[supplierName]

        // 在仕入先分组内，再按材料名分组
        const materialGrouped: Record<string, any[]> = {}
        groupData.forEach((row) => {
          const materialName = row.material_name || '未分類'
          if (!materialGrouped[materialName]) {
            materialGrouped[materialName] = []
          }
          materialGrouped[materialName].push(row)
        })

        // 计算仕入先分组的总合计
        let supplierTotalForecast = 0
        let supplierTotalRequired = 0

        const materialGroupsHtml = Object.keys(materialGrouped)
          .sort((a, b) => {
            // 材料名升序排序
            if (a < b) return -1
            if (a > b) return 1
            return 0
          })
          .map((materialName) => {
            const materialData = materialGrouped[materialName]

            // 计算材料分组的合计
            const materialTotalForecast = materialData.reduce(
              (sum, row) => sum + (row.forecast_units || 0),
              0,
            )
            const materialTotalRequired = materialData.reduce((sum, row) => {
              return sum + (row.material_required !== null ? parseFloat(row.material_required) : 0)
            }, 0)

            // 累加到仕入先合计
            supplierTotalForecast += materialTotalForecast
            supplierTotalRequired += materialTotalRequired

            return `
              <div class="material-group">
                <div class="material-group-title">材料名: ${materialName}</div>
                <table class="detail-table">
                  <thead>
                    <tr>
                      <th>製品名</th>
                      <th class="text-right">内示数量</th>
                      <th class="text-right">ロットサイズ</th>
                      <th class="text-right">材料必要数</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${materialData
                      .map(
                        (row) => `
                      <tr>
                        <td>${row.product_name || '-'}</td>
                        <td class="text-right">${formatNumber(row.forecast_units)}</td>
                        <td class="text-right">${row.lot_size || '-'}</td>
                        <td class="text-right">${row.material_required !== null ? row.material_required : '-'}</td>
                      </tr>
                    `,
                      )
                      .join('')}
                    <tr class="summary-row">
                      <td><strong>小計</strong></td>
                      <td class="text-right"><strong>${formatNumber(materialTotalForecast)}</strong></td>
                      <td class="text-right">-</td>
                      <td class="text-right"><strong>${materialTotalRequired.toFixed(1)}</strong></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            `
          })
          .join('')

        // 添加仕入先分组合计
        const supplierSummaryHtml = `
          <table class="detail-table" style="margin-top: 2mm;">
            <tbody>
              <tr class="summary-row">
                <td><strong>仕入先合計</strong></td>
                <td class="text-right"><strong>${formatNumber(supplierTotalForecast)}</strong></td>
                <td class="text-right">-</td>
                <td class="text-right"><strong>${supplierTotalRequired.toFixed(1)}</strong></td>
              </tr>
            </tbody>
          </table>
        `

        return `
          <div class="supplier-group">
            <div class="supplier-group-title">仕入先: ${supplierName}</div>
            ${materialGroupsHtml}
            ${supplierSummaryHtml}
          </div>
        `
      })
      .join('')
  } else {
    // 材料別集計表格（按仕入先分组）
    tableHtml = Object.keys(groupedData)
      .sort()
      .map((supplierName) => {
        const groupData = groupedData[supplierName]

        // 计算仕入先分组合计
        const supplierTotalForecast = groupData.reduce(
          (sum, row) => sum + (row.total_forecast_units || 0),
          0,
        )
        const supplierTotalRequired = groupData.reduce((sum, row) => {
          return (
            sum +
            (row.total_material_required !== null ? parseFloat(row.total_material_required) : 0)
          )
        }, 0)

        return `
          <div class="supplier-group">
            <div class="supplier-group-title">仕入先: ${supplierName}</div>
            <table class="summary-table">
              <thead>
                <tr>
                  <th>材料名</th>
                  <th>材料CD</th>
                  <th class="text-center">製品数</th>
                  <th class="text-right">内示数量合計</th>
                  <th class="text-right">平均ロットサイズ</th>
                  <th class="text-right">材料必要数合計</th>
                </tr>
              </thead>
              <tbody>
                ${groupData
                  .map(
                    (row) => `
                  <tr>
                    <td>${row.material_name || '-'}</td>
                    <td>${row.material_cd || '-'}</td>
                    <td class="text-center">${row.product_count || 0}</td>
                    <td class="text-right">${formatNumber(row.total_forecast_units)}</td>
                    <td class="text-right">${row.avg_lot_size ? Math.round(row.avg_lot_size) : '-'}</td>
                    <td class="text-right">${row.total_material_required !== null ? row.total_material_required : '-'}</td>
                  </tr>
                `,
                  )
                  .join('')}
                <tr class="summary-row">
                  <td colspan="3"><strong>仕入先合計</strong></td>
                  <td class="text-right"><strong>${formatNumber(supplierTotalForecast)}</strong></td>
                  <td class="text-right">-</td>
                  <td class="text-right"><strong>${supplierTotalRequired.toFixed(1)}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        `
      })
      .join('')
  }

  // 筛选条件信息（打印时只显示年月）
  const filterInfo = []
  if (searchForm.year) filterInfo.push(`${searchForm.year}年`)
  if (searchForm.month) filterInfo.push(`${searchForm.month}月`)

  return `
    <div class="print-header">
      <div class="print-title">${title}</div>
      <div class="print-subtitle">Material Forecast Management</div>
      <div class="print-info">
        <div>印刷日時: ${currentDate}</div>
        <div>${filterInfo.length > 0 ? `条件: ${filterInfo.join(' / ')} (全仕入先)` : '条件: 全て'}</div>
      </div>
    </div>
    ${statsHtml}
    ${tableHtml}
    <div class="print-footer">
      総件数: ${data.length}件 | ページ: 1
    </div>
  `
}

const fetchData = () => {
  if (activeTab.value === 'detail') {
    fetchDetailData()
  } else {
    fetchSummaryData()
  }
}

// 初始化
onMounted(() => {
  fetchSuppliers()
  fetchData()
  fetchStats()
})
</script>

<style scoped>
.material-forecast-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 12px;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(10px);
}

.header-left {
  display: flex;
  align-items: center;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  box-shadow: 0 3px 10px rgba(102, 126, 234, 0.35);
  flex-shrink: 0;
}

.main-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
  letter-spacing: -0.02em;
}

.subtitle {
  font-size: 0.8rem;
  color: #718096;
  margin: 2px 0 0 0;
  font-weight: 400;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.2s ease;
  border: none;
  white-space: nowrap;
}

.refresh-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: white;
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.print-btn {
  background: linear-gradient(135deg, #ff8c00, #ffa500);
  border: none;
  color: white;
}

.print-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.4);
}

/* 统计卡片 */
.stats-container {
  margin-bottom: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.2s ease;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border-color: rgba(102, 126, 234, 0.2);
}

.stat-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
  flex-shrink: 0;
}

.stat-card.primary .stat-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.stat-card.info .stat-icon {
  background: linear-gradient(135deg, #00b8d9, #43e97b);
}

.stat-card.warning .stat-icon {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.stat-card.success .stat-icon {
  background: linear-gradient(135deg, #11998e, #38ef7d);
}

.stat-card.amount .stat-icon {
  background: linear-gradient(135deg, #ff8c00, #ffa500);
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 1.3rem;
  font-weight: 700;
  color: #1a202c;
  line-height: 1.2;
  letter-spacing: -0.01em;
}

.stat-value .unit {
  font-size: 0.75rem;
  color: #718096;
  margin-left: 3px;
  font-weight: 500;
}

.stat-label {
  font-size: 0.75rem;
  color: #718096;
  margin-top: 2px;
  font-weight: 500;
}

/* 搜索区域 */
.search-section {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.search-row {
  display: grid;
  grid-template-columns: auto auto auto 1fr auto;
  gap: 12px;
  align-items: end;
}

.search-group {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.search-label {
  font-size: 0.8rem;
  color: #4a5568;
  font-weight: 600;
  white-space: nowrap;
  min-width: 32px;
}

.search-select {
  width: 110px;
}

.supplier-select {
  width: 160px;
}

.keyword-group {
  min-width: 0;
}

.search-input {
  width: 100%;
  min-width: 200px;
}

.reset-group {
  flex-shrink: 0;
}

.reset-btn {
  padding: 8px 16px;
  font-size: 0.875rem;
  height: 32px;
}

/* 月份导航按钮组 */
.month-control-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.month-navigation {
  display: flex;
  align-items: center;
  gap: 4px;
}

.month-nav-btn {
  padding: 0;
  border-radius: 6px;
  border: 1px solid #dcdfe6;
  background: #ffffff;
  color: #606266;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 32px;
}

.month-nav-btn.prev-btn,
.month-nav-btn.next-btn {
  width: 32px;
  padding: 0;
}

.month-nav-btn.current-btn {
  padding: 0 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: #ffffff;
  font-weight: 500;
  font-size: 0.875rem;
}

.month-nav-btn:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.month-nav-btn.current-btn:hover {
  background: linear-gradient(135deg, #5568d3 0%, #653a8f 100%);
  color: #ffffff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.month-nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 标签页 */
.tab-section {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 10px 10px 0 0;
  padding: 0 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
  border-bottom: none;
}

.custom-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}

.custom-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.custom-tabs :deep(.el-tabs__item) {
  padding: 0 20px;
  height: 44px;
  line-height: 44px;
  font-size: 0.875rem;
  font-weight: 500;
}

.custom-tabs :deep(.el-tabs__item.is-active) {
  color: #667eea;
  font-weight: 600;
}

.custom-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(90deg, #667eea, #764ba2);
  height: 2.5px;
  border-radius: 2px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
}

/* 表格区域 */
.table-section {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 0 0 10px 10px;
  padding: 0 12px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
  border-top: none;
}

.data-table {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.data-table :deep(.el-table__header-wrapper) {
  border-radius: 8px 8px 0 0;
}

.data-table :deep(.el-table__header th) {
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%) !important;
  font-weight: 700;
  font-size: 0.75rem;
  padding: 8px 6px;
  color: #2d3748;
  border-bottom: 2px solid #e2e8f0;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  line-height: 1.3;
}

.data-table :deep(.even-row) {
  background: #fafbfc;
}

.data-table :deep(.odd-row) {
  background: #ffffff;
}

.data-table :deep(.el-table__row:hover > td) {
  background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%) !important;
  transition: background 0.2s ease;
}

.data-table :deep(.el-table__body td) {
  padding: 6px 6px;
  font-size: 0.75rem;
  border-bottom: 1px solid #f1f5f9;
  transition: all 0.2s ease;
  line-height: 1.4;
}

.data-table :deep(.el-table__body tr:last-child td) {
  border-bottom: none;
}

/* 合计行样式 */
.data-table :deep(.el-table__footer-wrapper) {
  border-top: 3px solid #667eea;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
}

.data-table :deep(.el-table__footer) {
  background: linear-gradient(135deg, #f0f4ff 0%, #e6edff 100%);
}

.data-table :deep(.el-table__footer td) {
  background: linear-gradient(135deg, #f0f4ff 0%, #e6edff 100%) !important;
  font-weight: 700;
  font-size: 0.8rem;
  color: #2d3748;
  padding: 10px 6px;
  border-top: 3px solid #667eea;
  border-bottom: none;
  line-height: 1.4;
}

.data-table :deep(.el-table__footer td:first-child) {
  font-weight: 700;
  color: #667eea;
  font-size: 0.85rem;
}

.data-table :deep(.el-table__footer td[class*='is-right']) {
  color: #667eea;
  font-size: 0.85rem;
  font-weight: 800;
}

/* 表格滚动条样式 */
.data-table :deep(.el-table__body-wrapper) {
  overflow-y: auto;
}

/* 确保表格有固定高度并显示滚动条 */
.detail-table,
.summary-table {
  height: 650px;
}

.detail-table :deep(.el-table__inner-wrapper),
.summary-table :deep(.el-table__inner-wrapper) {
  height: 100%;
}

.data-table :deep(.el-scrollbar__bar) {
  opacity: 0.6;
}

.data-table :deep(.el-scrollbar__thumb) {
  background-color: rgba(102, 126, 234, 0.3);
  border-radius: 4px;
}

.data-table :deep(.el-scrollbar__thumb:hover) {
  background-color: rgba(102, 126, 234, 0.5);
}

/* 减少行高 */
.data-table :deep(.el-table__row) {
  height: auto;
}

.data-table :deep(.el-table__row td) {
  padding-top: 6px;
  padding-bottom: 6px;
}

.supplier-cell {
  font-weight: 600;
  color: #667eea;
}

.product-cell,
.material-cell {
  display: flex;
  flex-direction: column;
}

.product-name,
.material-name {
  font-weight: 500;
  color: #303133;
}

.product-cd,
.material-cd {
  font-size: 0.7rem;
  color: #a0aec0;
  margin-top: 2px;
}

.number-cell {
  font-family: 'Roboto Mono', 'Consolas', monospace;
  font-weight: 500;
  font-size: 0.85rem;
}

.number-cell.highlight {
  color: #667eea;
  font-weight: 600;
}

.number-cell.highlight-total {
  color: #e6a23c;
  font-weight: 700;
  font-size: 1.05em;
}

.number-cell.no-data {
  color: #c0c4cc;
}

/* 分页 */
.pagination-container {
  display: flex;
  justify-content: center;
  padding: 8px 0 0;
  margin-top: 4px;
}

/* 响应式 */
@media (max-width: 1400px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .search-row {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .keyword-group {
    grid-column: 1 / -1;
  }

  .reset-group {
    grid-column: 1 / -1;
    justify-self: start;
  }

  .search-select,
  .supplier-select,
  .search-input {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .header-actions {
    width: 100%;
    justify-content: center;
  }
}
</style>
