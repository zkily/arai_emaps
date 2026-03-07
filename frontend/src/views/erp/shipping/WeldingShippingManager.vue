<template>
  <div class="welding-shipping-manager">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="icon-wrapper">
            <el-icon class="title-icon">
              <Box />
            </el-icon>
          </div>
          <div class="title-text">
            <h2 class="page-title">{{ t('shipping.weldingTitle') }}</h2>
            <p class="page-description">{{ t('shipping.weldingSubtitle') }}</p>
          </div>
        </div>
        <div class="header-decoration"></div>
      </div>
    </div>

    <!-- 条件设置区域 -->
    <el-card class="condition-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon">
              <Search />
            </el-icon>
            <span class="header-title">{{ t('shipping.weldingSearchCondition') }}</span>
          </div>
          <div class="header-badge">検索設定</div>
        </div>
      </template>

      <el-form :model="searchForm" :inline="true" class="search-form">
        <div class="form-row-inline">
          <el-form-item :label="t('shipping.weldingPeriod')" class="form-item-compact">
            <el-date-picker v-model="dateRange" type="daterange" range-separator="～" start-placeholder="開始日"
              end-placeholder="終了日" format="YYYY-MM-DD" value-format="YYYY-MM-DD" :shortcuts="dateShortcuts"
              @change="onDateRangeChange" class="date-picker" />
          </el-form-item>

          <el-form-item :label="t('shipping.weldingProduct')" class="form-item-compact">
            <el-select v-model="searchForm.selectedProducts" multiple collapse-tags collapse-tags-tooltip
              :placeholder="t('shipping.selectWeldingProduct')" class="product-select" :loading="productLoading">
              <el-option v-for="product in weldingProducts" :key="product.value" :label="product.label"
                :value="product.value" />
            </el-select>
          </el-form-item>

          <div class="form-actions-inline">
            <el-button type="primary" @click="handleSearch" :loading="tableLoading" :disabled="!searchForm.startDate ||
              !searchForm.endDate ||
              searchForm.selectedProducts.length === 0
              " class="search-btn">
              <el-icon>
                <Search />
              </el-icon>
              {{ t('shipping.searchExecute') }}
            </el-button>
            <el-button @click="handleReset" class="reset-btn">
              <el-icon>
                <Refresh />
              </el-icon>
              {{ t('shipping.reset') }}
            </el-button>
          </div>
        </div>
      </el-form>
    </el-card>

    <!-- 数据展示区域 -->
    <el-card v-if="tableData" class="data-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon">
              <Printer />
            </el-icon>
            <span class="header-title">{{ t('shipping.weldingSchedule') }}</span>
          </div>
          <div class="header-actions">
            <el-button type="success" @click="handleExport" :loading="exportLoading" class="export-btn">
              <el-icon>
                <Printer />
              </el-icon>
              {{ t('shipping.printExport') }}
            </el-button>
          </div>
        </div>
      </template>

      <!-- 统计信息 -->
      <div class="summary-section">
        <el-row :gutter="12" class="stats-row">
          <el-col :span="8">
            <div class="stat-card period-stat">
              <div class="stat-icon">
                <el-icon>
                  <Calendar />
                </el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">対象期間</div>
                <div class="stat-value">{{ periodText || '期間未選択' }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card products-stat">
              <div class="stat-icon">
                <el-icon>
                  <Box />
                </el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">対象製品数</div>
                <div class="stat-value">
                  {{ searchForm.selectedProducts.length }}<span class="stat-unit">種類</span>
                </div>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card records-stat">
              <div class="stat-icon">
                <el-icon>
                  <DataLine />
                </el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">総レコード数</div>
                <div class="stat-value">
                  {{ getTotalRecordCount() }}<span class="stat-unit">件</span>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 合并后的表格 -->
      <div class="table-section">
        <div class="table-header">
          <h3 class="table-title">出荷スケジュール詳細</h3>
        </div>
        <div class="table-container">
          <el-table v-if="tableData && Array.isArray(tableData.products) && tableData.products.length > 0" :data="pivotTableData" border stripe
            size="default" class="welding-table" :span-method="objectSpanMethod" empty-text="データがありません">
            <!-- 纳入先列 -->
            <el-table-column prop="destination" label="納入先" width="140" fixed="left" align="center">
              <template #default="{ row }">
                <div class="destination-cell">
                  <el-tag effect="light" type="primary" size="small">{{ row.destination }}</el-tag>
                </div>
              </template>
            </el-table-column>

            <!-- 製品名列 -->
            <el-table-column prop="productName" label="製品名" width="180" fixed="left">
              <template #default="{ row }">
                <div class="product-cell">
                  <div class="product-name">{{ row.productName }}</div>
                  <div class="product-code">{{ row.productCd }}</div>
                </div>
              </template>
            </el-table-column>

            <!-- 日期列 -->
            <el-table-column v-for="date in (tableData.dates || [])" :key="date" :label="formatDateHeader(date)" width="100"
              align="center">
              <template #header="">
                <div class="date-header">
                  <div class="date-month">{{ formatDateMonth(date) }}</div>
                  <div class="date-day">{{ formatDateDay(date) }}</div>
                  <div class="date-weekday">{{ formatDateWeekday(date) }}</div>
                </div>
              </template>
              <template #default="{ row }">
                <div class="data-cell">
                  <div v-if="row.data[date] && row.data[date].length > 0" class="data-content">
                    <div v-for="(item, index) in row.data[date]" :key="index" class="data-item">
                      <span class="box-count">{{ item.boxes }}</span>
                      <span class="box-unit">箱</span>
                    </div>
                  </div>
                  <div v-else class="empty-cell">
                    <span class="empty-dash">—</span>
                  </div>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>

    <!-- 空状态 -->
    <div v-else-if="!tableLoading" class="empty-state">
      <div class="empty-content">
        <el-icon class="empty-icon">
          <Search />
        </el-icon>
        <h3 class="empty-title">データがありません</h3>
        <p class="empty-description">検索条件を設定して「検索実行」ボタンをクリックしてください</p>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="tableLoading" class="loading-overlay">
      <el-icon class="loading-icon is-loading">
        <Loading />
      </el-icon>
      <p class="loading-text">データを読み込み中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { TableColumnCtx } from 'element-plus'
import { Search, Refresh, Printer, Calendar, Box, DataLine, Loading } from '@element-plus/icons-vue'
import {
  getWeldingProducts,
  getWeldingShippingData,
  exportWeldingShippingReport,
  type WeldingProduct,
  type WeldingShippingData,
  type WeldingShippingRecord,
} from '@/api/shipping/weldingShipping'

const { t } = useI18n()

// 当月期间（默认）：按 JST 计算，与页面其他日期显示一致
const getCurrentMonthRange = (): [string, string] => {
  const pad = (n: number) => String(n).padStart(2, '0')
  // 当前时刻在 JST 下的年月日
  const jst = new Date(Date.now() + 9 * 60 * 60 * 1000)
  const y = jst.getUTCFullYear()
  const m = jst.getUTCMonth()
  const startStr = `${y}-${pad(m + 1)}-01`
  const lastDay = new Date(Date.UTC(y, m + 1, 0)).getUTCDate()
  const endStr = `${y}-${pad(m + 1)}-${pad(lastDay)}`
  return [startStr, endStr]
}
const initialMonthRange = getCurrentMonthRange()

// 响应式数据
const productLoading = ref(false)
const tableLoading = ref(false)
const exportLoading = ref(false)
const weldingProducts = ref<WeldingProduct[]>([])
const tableData = ref<WeldingShippingData | null>(null)
const dateRange = ref<[string, string] | undefined>(initialMonthRange)

// 搜索表单（默认当月、対象製品在 loadWeldingProducts 后全选）
const searchForm = reactive({
  startDate: initialMonthRange[0],
  endDate: initialMonthRange[1],
  selectedProducts: [] as string[],
})

// 日期快捷选项
const dateShortcuts = [
  {
    text: '今月',
    value: () => {
      const now = new Date()
      const start = new Date(now.getFullYear(), now.getMonth(), 1)
      const end = new Date(now.getFullYear(), now.getMonth() + 1, 0)
      return [start, end]
    },
  },
  {
    text: '先月',
    value: () => {
      const now = new Date()
      const start = new Date(now.getFullYear(), now.getMonth() - 1, 1)
      const end = new Date(now.getFullYear(), now.getMonth(), 0)
      return [start, end]
    },
  },
  {
    text: '過去7日',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    },
  },
  {
    text: '過去30日',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start, end]
    },
  },
]

// 计算属性
const periodText = computed(() => {
  if (searchForm.startDate && searchForm.endDate) {
    return `${searchForm.startDate} ～ ${searchForm.endDate}`
  }
  return ''
})

interface PivotRow {
  destination: string
  productName: string
  productCd: string
  data: { [key: string]: WeldingShippingRecord[] }
}

const pivotTableData = computed<PivotRow[]>(() => {
  const currentData = tableData.value
  if (!currentData || !Array.isArray(currentData.destinations) || !Array.isArray(currentData.products) || !Array.isArray(currentData.dates)) {
    return []
  }

  const rows: PivotRow[] = []
  currentData.destinations.forEach((dest) => {
    currentData.products.forEach((product) => {
      const rowData: PivotRow = {
        destination: dest,
        productName: product.name,
        productCd: product.cd,
        data: {},
      }

      let hasData = false
      currentData.dates.forEach((date) => {
        const cellData = currentData.data[date]?.[dest]?.[product.cd]
        rowData.data[date] = cellData || []
        if (cellData && cellData.length > 0) {
          hasData = true
        }
      })

      if (hasData) {
        rows.push(rowData)
      }
    })
  })

  return rows
})

const destinationSpans = computed(() => {
  const spans: Record<number, number> = {}
  const data = pivotTableData.value
  if (data.length === 0) return spans

  let pos = 0
  while (pos < data.length) {
    const currentDest = data[pos].destination
    let count = 0
    for (let i = pos; i < data.length; i++) {
      if (data[i].destination === currentDest) {
        count++
      } else {
        break
      }
    }
    spans[pos] = count
    pos += count
  }
  return spans
})

// 初始化
onMounted(() => {
  loadWeldingProducts()
})

// 加载溶接产品列表（加载完成后默认全选対象製品，并用默认条件自动检索）
const loadWeldingProducts = async () => {
  try {
    productLoading.value = true
    const response = await getWeldingProducts()
    // request工具已经自动提取了data字段，所以直接使用response
    const list = (response as WeldingProduct[]) || []
    weldingProducts.value = list
    // 対象製品默认全选
    searchForm.selectedProducts = list.map((p) => p.value)
    // 用默认筛选条件（当月・全选）自动加载数据
    if (searchForm.startDate && searchForm.endDate && searchForm.selectedProducts.length > 0) {
      await handleSearch()
    }
  } catch (error) {
    console.error('溶接製品取得エラー:', error)
    ElMessage.error('溶接製品の取得に失敗しました')
  } finally {
    productLoading.value = false
  }
}

// 日期范围变化处理
const onDateRangeChange = (dates: [string, string] | null) => {
  if (dates) {
    searchForm.startDate = dates[0]
    searchForm.endDate = dates[1]
  } else {
    searchForm.startDate = ''
    searchForm.endDate = ''
  }
}

// 搜索处理
const handleSearch = async () => {
  if (!searchForm.startDate || !searchForm.endDate) {
    ElMessage.warning('期間を選択してください')
    return
  }

  if (searchForm.selectedProducts.length === 0) {
    ElMessage.warning('対象製品を選択してください')
    return
  }

  try {
    tableLoading.value = true
    const response = await getWeldingShippingData({
      start_date: searchForm.startDate,
      end_date: searchForm.endDate,
      products: searchForm.selectedProducts,
    })

    // request工具已经自动提取了data字段
    tableData.value = response
    ElMessage.success('データを取得しました')
  } catch (error) {
    console.error('データ取得エラー:', error)
    ElMessage.error('データの取得に失敗しました')
  } finally {
    tableLoading.value = false
  }
}

// 重置处理
const handleReset = () => {
  dateRange.value = undefined
  searchForm.startDate = ''
  searchForm.endDate = ''
  searchForm.selectedProducts = []
  tableData.value = null
}

// 导出处理
const handleExport = async () => {
  if (!tableData.value) {
    ElMessage.warning('エクスポートするデータがありません')
    return
  }

  try {
    exportLoading.value = true
    const response = await exportWeldingShippingReport({
      start_date: searchForm.startDate,
      end_date: searchForm.endDate,
      products: searchForm.selectedProducts,
      table_data: tableData.value,
    })

    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(response.html)
      printWindow.document.close()
      printWindow.onload = () => {
        printWindow.print()
        printWindow.close()
      }
    }
    ElMessage.success('印刷用レポートを生成しました')
  } catch (error) {
    console.error('エクスポートエラー:', error)
    ElMessage.error('レポートの生成に失敗しました')
  } finally {
    exportLoading.value = false
  }
}

// 格式化日期相关方法 - 使用日本时区
const formatDateHeader = (date: string) => {
  const d = new Date(date + 'T00:00:00+09:00') // 确保使用JST时区
  return `${d.getMonth() + 1}/${d.getDate()}`
}

const formatDateMonth = (date: string) => {
  const d = new Date(date + 'T00:00:00+09:00') // 确保使用JST时区
  return `${d.getMonth() + 1}月`
}

const formatDateDay = (date: string) => {
  const d = new Date(date + 'T00:00:00+09:00') // 确保使用JST时区
  return `${d.getDate()}日`
}

const formatDateWeekday = (date: string) => {
  const d = new Date(date + 'T00:00:00+09:00') // 确保使用JST时区
  const weekdays = ['日', '月', '火', '水', '木', '金', '土']
  return `(${weekdays[d.getDay()]})`
}

// 合并单元格方法
const objectSpanMethod = ({
  rowIndex,
  columnIndex,
}: {
  row: PivotRow
  column: TableColumnCtx<PivotRow>
  rowIndex: number
  columnIndex: number
}) => {
  if (columnIndex === 0) {
    const rowspan = destinationSpans.value[rowIndex]
    if (rowspan) {
      return {
        rowspan,
        colspan: 1,
      }
    }
    return {
      rowspan: 0,
      colspan: 0,
    }
  }
}

// 获取总记录数
const getTotalRecordCount = () => {
  const data = tableData.value
  if (!data || !Array.isArray(data.dates) || !Array.isArray(data.destinations) || !Array.isArray(data.products)) {
    return 0
  }

  let count = 0
  const dataMap = data.data || {}
  data.dates.forEach((date) => {
    data.destinations.forEach((dest) => {
      data.products.forEach((product) => {
        const records = dataMap[date]?.[dest]?.[product.cd]
        count += records?.length ?? 0
      })
    })
  })

  return count
}
</script>

<style scoped>
.welding-shipping-manager {
  padding: 12px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
  position: relative;
}

/* 页面标题样式 */
.page-header {
  margin-bottom: 12px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  position: relative;
  animation: slideInDown 0.8s ease-out;
}

.header-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px 20px;
  color: white;
  position: relative;
  overflow: hidden;
}

.header-decoration {
  position: absolute;
  top: -50%;
  right: -10%;
  width: 200px;
  height: 200px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  transform: rotate(45deg);
  animation: float 6s ease-in-out infinite;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 2;
}

.icon-wrapper {
  background: rgba(255, 255, 255, 0.2);
  padding: 8px;
  border-radius: 10px;
  backdrop-filter: blur(10px);
  animation: pulse 2s ease-in-out infinite;
}

.title-icon {
  font-size: 24px;
  color: white;
}

.page-title {
  margin: 0 0 4px 0;
  font-size: 22px;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.page-description {
  margin: 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.3;
}

/* 卡片样式 */
.condition-card,
.data-card {
  margin-bottom: 12px;
  border-radius: 10px;
  border: none;
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
  animation: fadeInUp 0.6s ease-out;
}

.condition-card:hover,
.data-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 16px;
  color: #667eea;
}

.header-title {
  font-weight: 600;
  font-size: 14px;
  color: #2d3748;
}

.header-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 500;
}

/* 表单样式 */
.search-form {
  padding: 0;
}

.form-row-inline {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.form-item-compact {
  margin-bottom: 0;
  flex: 0 0 auto;
}

.form-item-compact :deep(.el-form-item__label) {
  margin-right: 8px;
  padding: 0;
  width: auto;
  font-size: 13px;
}

.date-picker {
  width: 280px;
  border-radius: 6px;
}

.product-select {
  width: 300px;
  border-radius: 6px;
}

.form-actions-inline {
  display: flex;
  gap: 8px;
  margin-left: auto;
  flex-shrink: 0;
}

.search-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.25);
  transition: all 0.3s ease;
}

.search-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
}

.reset-btn {
  background: white;
  border: 1px solid #e2e8f0;
  color: #718096;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  font-size: 13px;
  transition: all 0.3s ease;
}

.reset-btn:hover {
  border-color: #cbd5e0;
  color: #4a5568;
  transform: translateY(-1px);
}

.export-btn {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(72, 187, 120, 0.25);
  transition: all 0.3s ease;
}

.export-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(72, 187, 120, 0.35);
}

/* 统计卡片样式 */
.summary-section {
  margin-bottom: 12px;
}

.stats-row {
  margin: 0;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f1f5f9;
  transition: all 0.3s ease;
  height: 64px;
  animation: slideInRight 0.6s ease-out;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.period-stat {
  border-left: 4px solid #667eea;
  animation-delay: 0.1s;
}

.products-stat {
  border-left: 4px solid #ed8936;
  animation-delay: 0.2s;
}

.records-stat {
  border-left: 4px solid #38a169;
  animation-delay: 0.3s;
}

.stat-icon {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.stat-card:hover .stat-icon {
  transform: scale(1.05);
}

.stat-icon .el-icon {
  font-size: 18px;
  color: #4a5568;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-label {
  color: #718096;
  font-size: 11px;
  margin-bottom: 2px;
  font-weight: 500;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #2d3748;
  line-height: 1.2;
}

.stat-unit {
  font-size: 12px;
  color: #718096;
  margin-left: 2px;
  font-weight: 500;
}

/* 表格样式 */
.table-section {
  border-radius: 10px;
  overflow: hidden;
  background: white;
  animation: fadeInUp 0.8s ease-out;
}

.table-header {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 10px 16px;
  border-bottom: 1px solid #e2e8f0;
}

.table-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
}

.table-container {
  overflow-x: auto;
}

.welding-table {
  width: 100%;
  border-radius: 0;
}

.welding-table :deep(.el-table__header-wrapper) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.welding-table :deep(.el-table__header th) {
  background: transparent !important;
  color: white !important;
  font-weight: 600;
  border-color: rgba(255, 255, 255, 0.2);
  font-size: 13px;
  text-align: center;
  padding: 8px 0;
}

.destination-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 6px;
}

.product-cell {
  padding: 8px;
}

.product-name {
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 2px;
  font-size: 13px;
}

.product-code {
  font-size: 11px;
  color: #718096;
  background: #f7fafc;
  padding: 1px 6px;
  border-radius: 3px;
  display: inline-block;
}

.date-header {
  text-align: center;
  line-height: 1.2;
  color: #2d3748 !important;
}

.date-month {
  font-size: 11px;
  font-weight: 600;
}

.date-day {
  font-size: 14px;
  font-weight: 700;
  margin: 1px 0;
}

.date-weekday {
  font-size: 10px;
  opacity: 0.8;
}

.data-cell {
  padding: 6px;
  min-height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.data-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
  align-items: center;
}

.data-item {
  background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
  border: 1px solid #90cdf4;
  border-radius: 6px;
  padding: 4px 8px;
  display: flex;
  align-items: center;
  gap: 3px;
  min-width: 50px;
  justify-content: center;
  transition: all 0.2s ease;
  animation: fadeIn 0.5s ease-out;
}

.data-item:hover {
  transform: scale(1.08);
  box-shadow: 0 3px 12px rgba(66, 153, 225, 0.4);
}

.box-count {
  font-weight: 700;
  font-size: 12px;
  color: #2b6cb0;
}

.box-unit {
  font-size: 10px;
  color: #2b6cb0;
}

.empty-cell {
  color: #cbd5e0;
  font-size: 14px;
}

.empty-dash {
  opacity: 0.5;
}

/* 空状态样式 */
.empty-state {
  background: white;
  border-radius: 12px;
  padding: 60px 30px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  animation: fadeInUp 0.6s ease-out;
}

.empty-content {
  max-width: 350px;
  margin: 0 auto;
}

.empty-icon {
  font-size: 48px;
  color: #e2e8f0;
  margin-bottom: 12px;
  animation: bounce 2s ease-in-out infinite;
}

.empty-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #4a5568;
}

.empty-description {
  margin: 0;
  color: #718096;
  font-size: 14px;
  line-height: 1.4;
}

/* 加载状态样式 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
  animation: fadeIn 0.3s ease-out;
}

.loading-icon {
  font-size: 40px;
  color: #667eea;
  margin-bottom: 12px;
  animation: spin 1s linear infinite;
}

.loading-text {
  font-size: 14px;
  color: #4a5568;
  margin: 0;
  font-weight: 500;
}

/* 动画定义 */
@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes float {

  0%,
  100% {
    transform: translateY(0px) rotate(45deg);
  }

  50% {
    transform: translateY(-10px) rotate(45deg);
  }
}

@keyframes pulse {

  0%,
  100% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.05);
  }
}

@keyframes bounce {

  0%,
  20%,
  50%,
  80%,
  100% {
    transform: translateY(0);
  }

  40% {
    transform: translateY(-10px);
  }

  60% {
    transform: translateY(-5px);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .form-row-inline {
    flex-direction: column;
    align-items: stretch;
  }

  .form-item-compact {
    width: 100%;
  }

  .date-picker,
  .product-select {
    width: 100%;
  }

  .form-actions-inline {
    margin-left: 0;
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 768px) {
  .welding-shipping-manager {
    padding: 12px;
  }

  .header-content {
    padding: 20px;
  }

  .title-section {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }

  .page-title {
    font-size: 22px;
  }

  .form-actions {
    justify-content: center;
    flex-wrap: wrap;
  }

  .stats-row {
    flex-direction: column;
    gap: 12px;
  }

  .stat-card {
    margin-bottom: 12px;
    height: auto;
    padding: 12px;
  }

  .table-container {
    font-size: 11px;
  }

  .product-cell {
    padding: 6px;
  }

  .product-name {
    font-size: 11px;
  }

  .date-header {
    font-size: 10px;
  }

  .data-item {
    padding: 3px 6px;
    min-width: 40px;
  }

  .box-count {
    font-size: 11px;
  }

  .box-unit {
    font-size: 9px;
  }
}

@media (max-width: 480px) {
  .header-content {
    padding: 16px;
  }

  .page-title {
    font-size: 18px;
  }

  .page-description {
    font-size: 12px;
  }

  .stat-card {
    padding: 12px;
    height: auto;
  }

  .stat-value {
    font-size: 18px;
  }

  .empty-state {
    padding: 40px 16px;
  }

  .empty-icon {
    font-size: 36px;
  }

  .empty-title {
    font-size: 16px;
  }

  .empty-description {
    font-size: 12px;
  }
}

/* 打印样式 */
@media print {
  .welding-shipping-manager {
    background: white !important;
    padding: 0 !important;
  }

  .page-header {
    box-shadow: none !important;
    margin-bottom: 16px;
  }

  .header-content {
    background: white !important;
    color: black !important;
    padding: 16px !important;
  }

  .condition-card {
    display: none;
  }

  .header-actions,
  .export-btn {
    display: none;
  }

  .summary-section {
    margin-bottom: 16px;
  }

  .stat-card {
    box-shadow: none !important;
    border: 1px solid #e2e8f0 !important;
  }

  .welding-table {
    font-size: 10px;
  }

  .data-item {
    background: #f7fafc !important;
    border: 1px solid #e2e8f0 !important;
  }
}

/* 自定义滚动条 */
.table-container::-webkit-scrollbar {
  height: 6px;
}

.table-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.table-container::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px;
}

.table-container::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6b4190 100%);
}

/* Element Plus 组件样式覆盖 */
.welding-shipping-manager :deep(.el-card__header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e2e8f0;
}

.welding-shipping-manager :deep(.el-card__body) {
  padding: 16px;
}

.welding-shipping-manager :deep(.el-form-item__label) {
  font-weight: 600;
  color: #4a5568;
}

.welding-shipping-manager :deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.welding-shipping-manager :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.welding-shipping-manager :deep(.el-input__wrapper):hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.welding-shipping-manager :deep(.el-select) {
  border-radius: 8px;
}

.welding-shipping-manager :deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
}

.welding-shipping-manager :deep(.el-table) {
  border-radius: 0;
}

.welding-shipping-manager :deep(.el-table__body-wrapper) {
  border-radius: 0 0 10px 10px;
}

.welding-shipping-manager :deep(.el-table td) {
  border-color: #f1f5f9;
  padding: 6px 0;
}

.welding-shipping-manager :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #fafbfc;
}

.welding-shipping-manager :deep(.el-table__body tr:hover > td) {
  background-color: #f8fafc !important;
}

/* 工具提示样式 */
.welding-shipping-manager :deep(.el-tooltip__popper) {
  border-radius: 8px;
  font-size: 12px;
}

/* 日期选择器样式 */
.welding-shipping-manager :deep(.el-date-editor) {
  border-radius: 8px;
}

.welding-shipping-manager :deep(.el-picker-panel) {
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
}

/* 选择器下拉样式 */
.welding-shipping-manager :deep(.el-select-dropdown) {
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
  border: none;
}

.welding-shipping-manager :deep(.el-select-dropdown__item) {
  border-radius: 6px;
  margin: 2px 8px;
  transition: all 0.2s ease;
}

.welding-shipping-manager :deep(.el-select-dropdown__item:hover) {
  background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
  color: #2b6cb0;
}
</style>
