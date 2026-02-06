<template>
  <div class="order-history-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">📊</div>
          <div class="title-text">
            <h1 class="title">受注履歴比較</h1>
            <p class="description">
              異なる月に入力された受注データを比較して、予測の変化を確認できます
            </p>
          </div>
        </div>
        <div class="header-actions">
          <el-tag type="info" size="large" class="status-tag">
            <el-icon><TrendCharts /></el-icon>
            データ分析
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 筛选条件卡片 -->
    <el-card class="filter-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Filter /></el-icon>
            <span class="header-title">比較条件</span>
          </div>
          <div class="header-right">
            <el-badge
              :value="comparisonData.length"
              :hidden="comparisonData.length === 0"
              type="primary"
            >
              <el-icon><DataAnalysis /></el-icon>
            </el-badge>
          </div>
        </div>
      </template>

      <div class="filter-content">
        <div class="filter-section">
          <div class="section-title">
            <el-icon><Calendar /></el-icon>
            比較対象期間
          </div>
          <div class="filter-row">
            <div class="filter-group">
              <label class="filter-label">対象年月</label>
              <div class="date-selectors">
                <el-select
                  v-model="filters.year"
                  placeholder="年を選択"
                  class="year-select"
                  size="large"
                >
                  <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="y" />
                </el-select>
                <span class="date-separator">年</span>
                <el-select
                  v-model="filters.month"
                  placeholder="月を選択"
                  class="month-select"
                  size="large"
                >
                  <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
                </el-select>
                <span class="date-separator">月</span>
              </div>
            </div>
          </div>
        </div>

        <div class="filter-section">
          <div class="section-title">
            <el-icon><Document /></el-icon>
            入力月比較
          </div>
          <div class="filter-row">
            <div class="filter-group">
              <label class="filter-label">基準入力月</label>
              <el-select
                v-model="filters.baseRecord"
                placeholder="基準月を選択"
                class="record-select"
                size="large"
              >
                <el-option
                  v-for="record in recordOptions"
                  :key="`${record.year}-${record.month}`"
                  :label="`${record.year}年${record.month}月入力分`"
                  :value="`${record.year}-${record.month}`"
                />
              </el-select>
            </div>
            <div class="vs-indicator">
              <el-icon><ArrowRight /></el-icon>
              <span>VS</span>
              <el-icon><ArrowLeft /></el-icon>
            </div>
            <div class="filter-group">
              <label class="filter-label">比較入力月</label>
              <el-select
                v-model="filters.compareRecord"
                placeholder="比較月を選択"
                class="record-select"
                size="large"
              >
                <el-option
                  v-for="record in recordOptions"
                  :key="`${record.year}-${record.month}`"
                  :label="`${record.year}年${record.month}月入力分`"
                  :value="`${record.year}-${record.month}`"
                />
              </el-select>
            </div>
          </div>
        </div>

        <div class="action-section">
          <el-button
            type="primary"
            @click="fetchData"
            :loading="loading"
            size="large"
            class="primary-button"
          >
            <el-icon><Search /></el-icon>
            比較データ表示
          </el-button>
          <el-button
            v-if="isDevelopment"
            @click="createSnapshot"
            size="large"
            class="secondary-button"
          >
            <el-icon><Plus /></el-icon>
            履歴作成
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 结果统计卡片 -->
    <div v-if="comparisonData.length > 0" class="stats-cards">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card increase-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ increaseCount }}</div>
                <div class="stat-label">増加項目</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card decrease-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><Bottom /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ decreaseCount }}</div>
                <div class="stat-label">減少項目</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card total-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ comparisonData.length }}</div>
                <div class="stat-label">総項目数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card impact-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ significantChangeCount }}</div>
                <div class="stat-label">大幅変動</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 结果表格卡片 -->
    <el-card v-if="comparisonData.length > 0" class="result-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Grid /></el-icon>
            <span class="header-title">比較結果</span>
            <el-tag class="result-count-tag">{{ comparisonData.length }}件</el-tag>
          </div>
          <div class="header-right">
            <el-button @click="exportToExcel" class="export-button" type="success" :icon="Download">
              Excel出力
            </el-button>
          </div>
        </div>
      </template>

      <div class="table-container">
        <el-table
          :data="comparisonData"
          border
          stripe
          :summary-method="getSummaries"
          show-summary
          class="comparison-table"
          :header-cell-style="{ backgroundColor: '#f8fafc', fontWeight: 'bold' }"
          :row-class-name="getRowClassName"
        >
          <el-table-column label="納入先" prop="destination_cd" min-width="140" fixed="left">
            <template #default="{ row }">
              <div class="destination-cell">
                <div class="destination-code">{{ row.destination_cd }}</div>
                <div class="destination-name">{{ row.destination_name }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="製品情報" min-width="180">
            <template #default="{ row }">
              <div class="product-cell">
                <div class="product-code">
                  <el-tag size="small" type="info">{{ row.product_cd }}</el-tag>
                </div>
                <div class="product-name">{{ row.product_name }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column :label="baseRecordLabel" prop="base_forecast" width="140" align="right">
            <template #default="{ row }">
              <div class="number-cell base-value">
                {{ formatNumber(row.base_forecast) }}
              </div>
            </template>
          </el-table-column>
          <el-table-column
            :label="compareRecordLabel"
            prop="compare_forecast"
            width="140"
            align="right"
          >
            <template #default="{ row }">
              <div class="number-cell compare-value">
                {{ formatNumber(row.compare_forecast) }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="差異" prop="forecast_diff" width="120" align="right">
            <template #default="{ row }">
              <div class="diff-cell" :class="getDiffClass(row.forecast_diff)">
                <el-icon v-if="row.forecast_diff > 0"><ArrowUp /></el-icon>
                <el-icon v-else-if="row.forecast_diff < 0"><ArrowDown /></el-icon>
                <el-icon v-else><Minus /></el-icon>
                <span class="diff-value">
                  {{ row.forecast_diff > 0 ? '+' : '' }}{{ formatNumber(row.forecast_diff) }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="変動率" width="120" align="right">
            <template #default="{ row }">
              <div class="change-rate-cell" :class="getDiffClass(row.forecast_diff)">
                <el-progress
                  :percentage="
                    Math.min(
                      Math.abs(
                        parseFloat(calculateChangeRate(row.base_forecast, row.compare_forecast)),
                      ),
                      100,
                    )
                  "
                  :color="getProgressColor(row.forecast_diff)"
                  :stroke-width="6"
                  :show-text="false"
                  class="rate-progress"
                />
                <span class="rate-text">
                  {{ calculateChangeRate(row.base_forecast, row.compare_forecast) }}
                </span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-card v-else-if="!loading && searched" class="empty-card" shadow="hover">
      <el-empty description="比較データがありません" class="custom-empty">
        <template #image>
          <div class="empty-icon">
            <el-icon><DataAnalysis /></el-icon>
          </div>
        </template>
        <template #description>
          <div class="empty-description">
            <p>選択した条件での比較データが見つかりませんでした</p>
            <p class="empty-tip">異なる期間を選択してお試しください</p>
          </div>
        </template>
      </el-empty>
    </el-card>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-card class="loading-card" shadow="hover">
        <div class="loading-content">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <p>データを読み込み中...</p>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Download,
  Plus,
  Filter,
  Calendar,
  Document,
  ArrowRight,
  ArrowLeft,
  TrendCharts,
  Bottom,
  DataAnalysis,
  Warning,
  Grid,
  ArrowUp,
  ArrowDown,
  Minus,
  Loading,
} from '@element-plus/icons-vue'
import { fetchOrderHistoryComparison, createOrderHistorySnapshot } from '@/api/order/order'
import type { OrderHistoryComparisonItem } from '@/api/order/order'
import type { ApiResponse } from '@/types/global'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'

// 环境变量类型扩展
declare global {
  interface ImportMeta {
    env: Record<string, any>
  }
}

// 開発環境かどうか
const isDevelopment = import.meta.env.MODE === 'development'

// フィルター
const filters = ref({
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  baseRecord: '',
  compareRecord: '',
})

// 年選択肢
const yearOptions = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - 3 + i)

// 録入月選択肢（過去12ヶ月）
const recordOptions = computed(() => {
  const options = []
  const now = new Date()
  let year = now.getFullYear()
  let month = now.getMonth() + 1

  for (let i = 0; i < 12; i++) {
    options.push({ year, month })
    month--
    if (month < 1) {
      month = 12
      year--
    }
  }
  return options
})

// 初期値設定
if (recordOptions.value.length >= 2) {
  filters.value.baseRecord = `${recordOptions.value[0].year}-${recordOptions.value[0].month}`
  filters.value.compareRecord = `${recordOptions.value[1].year}-${recordOptions.value[1].month}`
}

// 状態管理
const loading = ref(false)
const searched = ref(false)
const comparisonData = ref<OrderHistoryComparisonItem[]>([])

// 统计计算
const increaseCount = computed(
  () => comparisonData.value.filter((item) => item.forecast_diff > 0).length,
)

const decreaseCount = computed(
  () => comparisonData.value.filter((item) => item.forecast_diff < 0).length,
)

const significantChangeCount = computed(
  () =>
    comparisonData.value.filter((item) => {
      const rate = Math.abs(
        parseFloat(calculateChangeRate(item.base_forecast, item.compare_forecast)),
      )
      return rate > 20 // 20%以上の変動を大幅変動とする
    }).length,
)

// ラベル計算
const baseRecordLabel = computed(() => {
  if (!filters.value.baseRecord) return '基準入力分'
  const [year, month] = filters.value.baseRecord.split('-')
  return `${year}年${month}月入力`
})

const compareRecordLabel = computed(() => {
  if (!filters.value.compareRecord) return '比較入力分'
  const [year, month] = filters.value.compareRecord.split('-')
  return `${year}年${month}月入力`
})

// 数値フォーマット
const formatNumber = (value: number) => {
  if (typeof value !== 'number') return ''
  return value.toLocaleString('ja-JP')
}

// 変動率計算
const calculateChangeRate = (base: number, compare: number) => {
  if (!base || base === 0) return '-'
  const rate = (((compare - base) / base) * 100).toFixed(1)
  return `${rate}%`
}

// 差異のクラス
const getDiffClass = (diff: number) => {
  if (diff > 0) return 'positive'
  if (diff < 0) return 'negative'
  return 'neutral'
}

// 行のクラス名
const getRowClassName = ({ row }: { row: OrderHistoryComparisonItem }) => {
  const rate = Math.abs(parseFloat(calculateChangeRate(row.base_forecast, row.compare_forecast)))
  if (rate > 50) return 'high-change-row'
  if (rate > 20) return 'medium-change-row'
  return ''
}

// プログレスバーの色
const getProgressColor = (diff: number) => {
  if (diff > 0) return '#67c23a'
  if (diff < 0) return '#f56c6c'
  return '#909399'
}

// データ取得
const fetchData = async () => {
  if (!filters.value.baseRecord || !filters.value.compareRecord) {
    ElMessage.warning('基準入力月と比較入力月を選択してください')
    return
  }

  loading.value = true
  searched.value = true

  try {
    const [baseYear, baseMonth] = filters.value.baseRecord.split('-').map(Number)
    const [compareYear, compareMonth] = filters.value.compareRecord.split('-').map(Number)

    const response = await fetchOrderHistoryComparison({
      year: filters.value.year,
      month: filters.value.month,
      baseRecordYear: baseYear,
      baseRecordMonth: baseMonth,
      compareRecordYear: compareYear,
      compareRecordMonth: compareMonth,
    })

    comparisonData.value = response.data || []

    if (comparisonData.value.length === 0) {
      ElMessage.info('比較できるデータがありません')
    } else {
      ElMessage.success(`${comparisonData.value.length}件のデータを取得しました`)
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('データの取得に失敗しました')
    comparisonData.value = []
  } finally {
    loading.value = false
  }
}

// 手動で履歴を作成（開発用）
const createSnapshot = async () => {
  try {
    const response = await createOrderHistorySnapshot()
    ElMessage.success(`${response.data?.count || 0}件の履歴を記録しました`)
  } catch (error) {
    console.error(error)
    ElMessage.error('履歴の作成に失敗しました')
  }
}

// サマリー計算
const getSummaries = ({
  columns,
  data,
}: {
  columns: any[]
  data: OrderHistoryComparisonItem[]
}) => {
  const sums: any[] = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合計'
      return
    }

    const values = data.map((item) => {
      const key = column.property as keyof OrderHistoryComparisonItem
      return item[key]
    })

    if (!values.every((value) => isNaN(Number(value)))) {
      const sum = values.reduce((prev: number, curr) => {
        const value = Number(curr)
        if (!isNaN(value)) {
          return prev + value
        } else {
          return prev
        }
      }, 0)

      if (
        column.property === 'base_forecast' ||
        column.property === 'compare_forecast' ||
        column.property === 'forecast_diff'
      ) {
        sums[index] = formatNumber(sum)
      } else {
        sums[index] = ''
      }
    } else {
      sums[index] = ''
    }
  })

  return sums
}

// Excel出力
const exportToExcel = () => {
  if (comparisonData.value.length === 0) {
    ElMessage.warning('出力するデータがありません')
    return
  }

  const exportData = comparisonData.value.map((item) => ({
    納入先CD: item.destination_cd,
    納入先名: item.destination_name,
    製品CD: item.product_cd,
    製品名: item.product_name,
    [baseRecordLabel.value]: item.base_forecast,
    [compareRecordLabel.value]: item.compare_forecast,
    差異: item.forecast_diff,
    変動率: calculateChangeRate(item.base_forecast, item.compare_forecast),
  }))

  const ws = XLSX.utils.json_to_sheet(exportData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '受注履歴比較')
  const buf = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  saveAs(
    new Blob([buf], { type: 'application/octet-stream' }),
    `受注履歴比較_${filters.value.year}_${filters.value.month}.xlsx`,
  )

  ElMessage.success('Excelファイルをダウンロードしました')
}
</script>

<style scoped>
.order-history-page {
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  position: relative;
}

.order-history-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  pointer-events: none;
}

/* 页面头部 */
.page-header {
  margin-bottom: 32px;
  position: relative;
  z-index: 1;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 32px;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.title-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.title-icon {
  font-size: 48px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #2c3e50, #4a5568);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px 0;
}

.description {
  color: #64748b;
  font-size: 16px;
  margin: 0;
  line-height: 1.5;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-tag {
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: white;
}

/* 筛选卡片 */
.filter-card {
  margin-bottom: 24px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  overflow: hidden;
  position: relative;
  z-index: 1;
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
  gap: 12px;
}

.header-icon {
  font-size: 20px;
  color: #667eea;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.result-count-tag {
  margin-left: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: white;
}

.filter-content {
  padding: 24px 0;
}

.filter-section {
  margin-bottom: 32px;
}

.filter-section:last-child {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e5e7eb;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  font-weight: 500;
  color: #4b5563;
}

.date-selectors {
  display: flex;
  align-items: center;
  gap: 8px;
}

.year-select {
  width: 120px;
}

.month-select {
  width: 100px;
}

.date-separator {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.record-select {
  width: 200px;
}

.vs-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #667eea;
  font-weight: 600;
  padding: 0 16px;
}

.action-section {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.primary-button {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.primary-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.secondary-button {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #667eea;
  color: #667eea;
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.secondary-button:hover {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
}

/* 统计卡片 */
.stats-cards {
  margin-bottom: 24px;
  position: relative;
  z-index: 1;
}

.stat-card {
  border-radius: 16px;
  border: none;
  overflow: hidden;
  transition: all 0.3s ease;
  height: 120px;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
}

.increase-card {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.decrease-card {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

.total-card {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.impact-card {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 24px;
  height: 100%;
}

.stat-icon {
  font-size: 32px;
  margin-right: 16px;
  opacity: 0.9;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  font-weight: 500;
}

/* 结果表格 */
.result-card {
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.table-container {
  overflow-x: auto;
}

.comparison-table {
  border-radius: 12px;
  overflow: hidden;
}

.destination-cell {
  padding: 8px 0;
}

.destination-code {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.destination-name {
  color: #6b7280;
  font-size: 12px;
  margin-top: 2px;
}

.product-cell {
  padding: 8px 0;
}

.product-code {
  margin-bottom: 4px;
}

.product-name {
  color: #374151;
  font-size: 13px;
  line-height: 1.3;
}

.number-cell {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  font-size: 14px;
}

.base-value {
  color: #3b82f6;
}

.compare-value {
  color: #8b5cf6;
}

.diff-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.diff-value {
  font-size: 14px;
}

.change-rate-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.rate-progress {
  width: 60px;
}

.rate-text {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  font-size: 13px;
}

.positive {
  color: #10b981;
}

.negative {
  color: #ef4444;
}

.neutral {
  color: #6b7280;
}

/* 表格行样式 */
:deep(.high-change-row) {
  background-color: rgba(239, 68, 68, 0.05);
}

:deep(.medium-change-row) {
  background-color: rgba(245, 158, 11, 0.05);
}

/* 空状态 */
.empty-card {
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  position: relative;
  z-index: 1;
}

.custom-empty {
  padding: 60px 40px;
}

.empty-icon {
  font-size: 64px;
  color: #d1d5db;
  margin-bottom: 24px;
}

.empty-description {
  text-align: center;
}

.empty-description p {
  margin: 8px 0;
  color: #6b7280;
}

.empty-tip {
  font-size: 14px;
  color: #9ca3af;
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: none;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 60px;
}

.loading-icon {
  font-size: 32px;
  color: #667eea;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-content p {
  color: #374151;
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

/* 导出按钮 */
.export-button {
  background: linear-gradient(135deg, #10b981, #059669);
  border: none;
  color: white;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.export-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .order-history-page {
    padding: 16px;
  }

  .header-content {
    flex-direction: column;
    gap: 20px;
    padding: 24px;
  }

  .title {
    font-size: 24px;
  }

  .title-icon {
    font-size: 36px;
  }

  .filter-row {
    flex-direction: column;
    gap: 16px;
  }

  .filter-group {
    width: 100%;
  }

  .record-select,
  .year-select,
  .month-select {
    width: 100%;
  }

  .vs-indicator {
    flex-direction: row;
    padding: 8px 0;
  }

  .action-section {
    flex-direction: column;
  }

  .primary-button,
  .secondary-button {
    width: 100%;
  }

  .stats-cards .el-col {
    margin-bottom: 16px;
  }
}

@media (max-width: 480px) {
  .title-section {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }

  .comparison-table {
    font-size: 12px;
  }

  .stat-content {
    padding: 16px;
  }

  .stat-icon {
    font-size: 24px;
  }

  .stat-value {
    font-size: 20px;
  }
}
</style>
