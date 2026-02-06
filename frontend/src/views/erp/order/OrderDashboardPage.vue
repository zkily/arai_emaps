<!-- 文件位置：src/views/order/OrderDashboardPage.vue -->
<template>
  <div class="order-dashboard-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">📊</div>
          <div class="title-text">
            <h1 class="title">月別受注ダッシュボード</h1>
            <p class="subtitle">リアルタイムで受注状況を把握・分析</p>
          </div>
        </div>
        <div class="header-actions">
          <el-tag type="success" size="large" class="status-tag">
            <el-icon>
              <TrendCharts />
            </el-icon>
            データ分析中
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 筛选控制区域 -->
    <el-card class="filter-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon">
              <Filter />
            </el-icon>
            <span class="header-title">分析条件</span>
          </div>
          <div class="header-right">
            <el-badge :value="totalOrderCount" :hidden="totalOrderCount === 0" type="primary">
              <el-icon>
                <DataAnalysis />
              </el-icon>
            </el-badge>
          </div>
        </div>
      </template>

      <div class="filter-content">
        <div class="filter-row">
          <div class="filter-section filter-section-year">
            <div class="section-title">
              <el-icon>
                <Calendar />
              </el-icon>
              対象年度
            </div>
            <div class="year-selector">
              <el-select v-model="filters.year" placeholder="年を選択" size="default" class="year-select"
                @change="fetchData">
                <el-option v-for="year in yearOptions" :key="year" :label="`${year}年`" :value="year" />
              </el-select>
            </div>
          </div>

          <div class="filter-section filter-section-month">
            <div class="section-title">
              <el-icon>
                <Clock />
              </el-icon>
              対象月度
            </div>
            <div class="month-buttons">
              <el-button v-for="m in 12" :key="m" :type="filters.month === m ? 'primary' : 'default'"
                :class="['month-btn', { active: filters.month === m }]" @click="selectMonth(m)" size="default">
                {{ m }}月
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 总体统计卡片 -->
    <div class="stats-overview">
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="stat-card total-orders-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-info">
                <div class="stat-label">総受注件数</div>
                <div :class="['stat-value', isOrderCountZero ? 'danger' : 'primary']">
                  {{ formatNumber(totalOrderCount) }}
                  <span class="stat-unit">件</span>
                </div>
              </div>
              <div class="stat-trend">
                <el-icon v-if="!isOrderCountZero" class="trend-up">
                  <ArrowUp />
                </el-icon>
                <el-icon v-else class="trend-warning">
                  <Warning />
                </el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="stat-card total-forecast-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-info">
                <div class="stat-label">総内示本数</div>
                <div :class="['stat-value', isForecastUnitsZero ? 'danger' : 'success']">
                  {{ formatNumber(totalForecastUnits) }}
                  <span class="stat-unit">本</span>
                </div>
              </div>
              <div class="stat-trend">
                <el-icon v-if="!isForecastUnitsZero" class="trend-up">
                  <ArrowUp />
                </el-icon>
                <el-icon v-else class="trend-warning">
                  <Warning />
                </el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="stat-card avg-forecast-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-info">
                <div class="stat-label">総金額</div>
                <div class="stat-value info">
                  {{ formatNumber(totalAmount) }}
                  <span class="stat-unit">円</span>
                </div>
              </div>
              <div class="stat-trend">
                <el-icon class="trend-stable">
                  <Minus />
                </el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- Top5排行榜 -->
    <el-card class="ranking-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon">
              <Trophy />
            </el-icon>
            <span class="header-title">内示本数 Top5 納入先</span>
          </div>
          <div class="header-right">
            <el-tag type="warning" class="ranking-tag" size="small">ランキング</el-tag>
          </div>
        </div>
      </template>

      <div class="ranking-content">
        <div class="ranking-list">
          <div v-for="(item, index) in top5DestinationSummary" :key="index" class="ranking-item">
            <div class="rank-number">
              <div v-if="index === 0" class="rank-medal gold">
                <el-icon>
                  <Trophy />
                </el-icon>
                <span>1</span>
              </div>
              <div v-else-if="index === 1" class="rank-medal silver">
                <el-icon>
                  <Medal />
                </el-icon>
                <span>2</span>
              </div>
              <div v-else-if="index === 2" class="rank-medal bronze">
                <el-icon>
                  <Medal />
                </el-icon>
                <span>3</span>
              </div>
              <div v-else class="rank-number-normal">{{ index + 1 }}</div>
            </div>
            <div class="rank-info">
              <div class="destination-name">{{ item.destination_name }}</div>
              <div class="destination-code">{{ item.destination_cd }}</div>
            </div>
            <div class="rank-value">
              <div class="value-number">
                {{ formatNumber(Number(item.forecast_units_sum) || 0) }}
              </div>
              <div class="value-unit">本</div>
            </div>
            <div class="rank-progress">
              <el-progress :percentage="calculatePercentage(Number(item.forecast_units_sum) || 0)"
                :color="getRankColor(index)" :stroke-width="8" :show-text="false" />
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 金額 Top5排行榜 -->
    <el-card class="ranking-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon">
              <Money />
            </el-icon>
            <span class="header-title">金額 Top5 納入先</span>
          </div>
          <div class="header-right">
            <el-tag type="success" class="ranking-tag" size="small">ランキング</el-tag>
          </div>
        </div>
      </template>

      <div class="ranking-content">
        <div class="ranking-list">
          <div v-for="(item, index) in top5AmountRanking" :key="index" class="ranking-item">
            <div class="rank-number">
              <div v-if="index === 0" class="rank-medal gold">
                <el-icon>
                  <Trophy />
                </el-icon>
                <span>1</span>
              </div>
              <div v-else-if="index === 1" class="rank-medal silver">
                <el-icon>
                  <Medal />
                </el-icon>
                <span>2</span>
              </div>
              <div v-else-if="index === 2" class="rank-medal bronze">
                <el-icon>
                  <Medal />
                </el-icon>
                <span>3</span>
              </div>
              <div v-else class="rank-number-normal">{{ index + 1 }}</div>
            </div>
            <div class="rank-info">
              <div class="destination-name">{{ item.destination_name }}</div>
              <div class="destination-code">{{ item.destination_cd }}</div>
            </div>
            <div class="rank-value">
              <div class="value-number">
                {{ formatNumber(Number(item.total_amount) || 0) }}
              </div>
              <div class="value-unit">円</div>
            </div>
            <div class="rank-progress">
              <el-progress :percentage="calculateAmountPercentage(Number(item.total_amount) || 0)"
                :color="getRankColor(index)" :stroke-width="8" :show-text="false" />
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 预测差异排行 -->
    <el-card class="forecast-diff-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon">
              <DataLine />
            </el-icon>
            <span class="header-title">予測差異分析</span>
          </div>
        </div>
      </template>
      <forecast-diff-rank :year="filters.year" :month="filters.month || new Date().getMonth() + 1" />
    </el-card>

    <!-- 详细数据表格 -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon">
              <Grid />
            </el-icon>
            <span class="header-title">納入先別詳細データ</span>
            <el-tag class="data-count-tag">{{ formatNumber(totalOrderCount) }}件</el-tag>
          </div>
          <div class="header-right">
            <el-button type="success" :icon="Download" @click="exportData"> データ出力 </el-button>
          </div>
        </div>
      </template>

      <div class="table-container">
        <el-table :data="destinationSummary" border stripe v-loading="loading" class="data-table"
          :header-cell-style="{ backgroundColor: '#f8fafc', fontWeight: 'bold' }" :row-class-name="getRowClassName">
          <el-table-column label="No." type="index" width="60" align="center">
            <template #default="{ $index }">
              <div class="index-cell">{{ $index + 1 }}</div>
            </template>
          </el-table-column>

          <el-table-column prop="destination_name" label="納入先名" min-width="180">
            <template #default="{ row }">
              <div class="destination-cell">
                <div class="destination-name">{{ row.destination_name }}</div>
                <div class="destination-code">{{ row.destination_cd }}</div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="注文件数" width="100" align="center">
            <template #default="{ row }">
              <el-badge :value="row.order_count" type="primary" class="order-badge" />
            </template>
          </el-table-column>

          <el-table-column label="内示本数合計" width="130" align="center">
            <template #default="{ row }">
              <div class="forecast-cell">
                <span class="forecast-value">
                  {{ formatNumber(Number(row.forecast_units_sum) || 0) }}
                </span>
                <span class="forecast-unit">本</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="平均本数" width="100" align="center">
            <template #default="{ row }">
              <div class="average-cell">
                {{ calculateAverage(row.forecast_units_sum, row.order_count) }}
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 图表区域 -->
    <div class="charts-section">
      <el-row :gutter="16">
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <div class="header-left">
                  <el-icon class="header-icon">
                    <TrendCharts />
                  </el-icon>
                  <span class="header-title">月別受注推移</span>
                </div>
                <div class="header-right">
                  <el-tag type="info" size="small">トレンド分析</el-tag>
                </div>
              </div>
            </template>
            <div ref="monthlyChartRef" class="chart"></div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <div class="header-left">
                  <el-icon class="header-icon">
                    <Histogram />
                  </el-icon>
                  <span class="header-title">納入先別受注数</span>
                </div>
                <div class="header-right">
                  <el-tag type="warning" size="small">分布分析</el-tag>
                </div>
              </div>
            </template>
            <div ref="destinationChartRef" class="chart"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-card class="loading-card" shadow="hover">
        <div class="loading-content">
          <el-icon class="loading-icon">
            <Loading />
          </el-icon>
          <p>データを読み込み中...</p>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, onBeforeUnmount, computed } from 'vue'
import { fetchDashboardSummary } from '@/api/order/order'
import ForecastDiffRank from '@/views/erp/order/components/ForecastDiffRank.vue'
import * as echarts from 'echarts'
import type { DestinationSummaryItem, MonthlySummaryItem } from '@/types/order'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  Filter,
  DataAnalysis,
  Calendar,
  Clock,
  ArrowUp,
  Warning,
  Minus,
  Trophy,
  Medal,
  DataLine,
  Grid,
  Download,
  Histogram,
  Loading,
  Money,
} from '@element-plus/icons-vue'

// ECharts tooltip formatter 参数类型
interface TooltipFormatterParams {
  name: string
  value: number | string
  seriesName?: string
}

// 🌟 千分位フォーマット関数
const formatNumber = (num: number | undefined | null) => {
  if (num === undefined || num === null || isNaN(num)) return '0'
  return num.toLocaleString('en-US')
}

// 🎯 筛选条件
const filters = ref({
  year: new Date().getFullYear(),
  month: undefined as number | undefined,
})

const yearOptions = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - 3 + i)

// 📋 表格数据
const destinationSummary = ref<DestinationSummaryItem[]>([])
const loading = ref(false)

// 📈 ECharts实例
const monthlyChartRef = ref<HTMLDivElement>()
const destinationChartRef = ref<HTMLDivElement>()
let monthlyChart: echarts.ECharts | null = null
let destinationChart: echarts.ECharts | null = null

// 🔢 统计计算
// 総受注件数
const totalOrderCount = computed(() => {
  return destinationSummary.value.reduce((sum, item) => sum + (item.order_count || 0), 0)
})

// 総内示本数
const totalForecastUnits = computed(() => {
  return destinationSummary.value.reduce((sum, item) => {
    const units = Number(item.forecast_units_sum) || 0
    return sum + units
  }, 0)
})

// 総金額
const totalAmount = computed(() => {
  return destinationSummary.value.reduce((sum, item) => {
    const amount = Number(item.total_amount) || 0
    return sum + amount
  }, 0)
})

// 🚨 異常検出
const isOrderCountZero = computed(() => {
  return totalOrderCount.value === 0
})

const isForecastUnitsZero = computed(() => {
  return totalForecastUnits.value === 0
})

// 🏆 Top5用computed
const top5DestinationSummary = computed(() => {
  const sorted = [...destinationSummary.value].sort(
    (a, b) => (Number(b.forecast_units_sum) || 0) - (Number(a.forecast_units_sum) || 0),
  )
  return sorted.slice(0, 5)
})

// 🏆 金額Top5用computed
const top5AmountRanking = computed(() => {
  const sorted = [...destinationSummary.value].sort(
    (a, b) => (Number(b.total_amount) || 0) - (Number(a.total_amount) || 0),
  )
  return sorted.slice(0, 5)
})

// 计算百分比
const calculatePercentage = (value: number) => {
  if (totalForecastUnits.value === 0) return 0
  return Math.round((value / totalForecastUnits.value) * 100)
}

// 计算金额百分比
const calculateAmountPercentage = (value: number) => {
  if (totalAmount.value === 0) return 0
  return Math.round((value / totalAmount.value) * 100)
}

// 获取排名颜色
const getRankColor = (index: number) => {
  const colors = ['#ffd700', '#c0c0c0', '#cd7f32', '#4dabf7', '#69db7c']
  return colors[index] || '#95a5a6'
}

// 计算平均值
const calculateAverage = (total: string | number, count: number) => {
  const totalNum = Number(total) || 0
  if (count === 0) return '0'
  return formatNumber(Math.round(totalNum / count))
}

// 获取行类名
const getRowClassName = ({ row }: { row: DestinationSummaryItem }) => {
  const units = Number(row.forecast_units_sum) || 0
  if (units > totalForecastUnits.value * 0.2) return 'high-value-row'
  if (units > totalForecastUnits.value * 0.1) return 'medium-value-row'
  return ''
}

// 📥 取得ダッシュボードデータ
const fetchData = async () => {
  loading.value = true
  try {
    const res = await fetchDashboardSummary({
      year: filters.value.year,
      month: filters.value.month,
    })
    const { destinationSummary: destinationSummaryData, monthlySummary } = res.data.data

    destinationSummary.value = destinationSummaryData
    await nextTick()

    if (Array.isArray(monthlySummary)) {
      renderMonthlyChart(monthlySummary)
    }
    if (Array.isArray(destinationSummaryData)) {
      renderDestinationChart(destinationSummaryData)
    }

    ElMessage.success(`${destinationSummaryData.length}件のデータを取得しました`)
  } catch (error) {
    console.error('ダッシュボードデータ取得失敗', error)
    ElMessage.error('データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// 📈 月別受注推移グラフ
const renderMonthlyChart = (data: MonthlySummaryItem[]) => {
  if (!monthlyChartRef.value) return
  if (!monthlyChart) monthlyChart = echarts.init(monthlyChartRef.value)

  monthlyChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e1e8ed',
      borderWidth: 1,
      textStyle: {
        color: '#333',
      },
      formatter: (params: TooltipFormatterParams[]) => {
        return params
          .map((item) => `${item.name}<br/>内示本数: ${Number(item.value).toLocaleString()} 本`)
          .join('<br/>')
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map((d) => `${d.month}月`),
      axisLine: {
        lineStyle: { color: '#e1e8ed' },
      },
      axisLabel: {
        color: '#64748b',
        fontSize: 12,
      },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#64748b',
        fontSize: 12,
      },
      splitLine: {
        lineStyle: {
          color: '#f1f5f9',
          type: 'dashed',
        },
      },
    },
    series: [
      {
        data: data.map((d) => Number(d.forecast_units_sum) || 0),
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: {
          color: '#667eea',
        },
        lineStyle: {
          color: '#667eea',
          width: 3,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
            { offset: 1, color: 'rgba(102, 126, 234, 0.05)' },
          ]),
        },
      },
    ],
  })
}

// 📉 納入先別受注数グラフ
const renderDestinationChart = (data: DestinationSummaryItem[]) => {
  if (!destinationChartRef.value) return
  if (!destinationChart) destinationChart = echarts.init(destinationChartRef.value)

  destinationChart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e1e8ed',
      borderWidth: 1,
      textStyle: {
        color: '#333',
      },
      formatter: (params: TooltipFormatterParams) => {
        return `${params.name}<br/>内示本数: ${Number(params.value).toLocaleString()} 本`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.destination_name),
      axisLabel: {
        interval: 0,
        rotate: 45,
        color: '#64748b',
        fontSize: 11,
      },
      axisLine: {
        lineStyle: { color: '#e1e8ed' },
      },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#64748b',
        fontSize: 12,
      },
      splitLine: {
        lineStyle: {
          color: '#f1f5f9',
          type: 'dashed',
        },
      },
    },
    series: [
      {
        data: data.map((d) => d.forecast_units_sum),
        type: 'bar',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#10b981' },
            { offset: 1, color: '#34d399' },
          ]),
          borderRadius: [6, 6, 0, 0],
        },
        barWidth: '50%',
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#059669' },
              { offset: 1, color: '#10b981' },
            ]),
          },
        },
      },
    ],
  })
}

// 月份按钮点击时
const selectMonth = (month: number) => {
  filters.value.month = month
  fetchData()
}

// 导出数据
const exportData = () => {
  ElMessage.info('データ出力機能は開発中です')
}

// ✨ resize時にチャートリサイズ
const handleResize = () => {
  monthlyChart?.resize()
  destinationChart?.resize()
}

onMounted(() => {
  fetchData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  monthlyChart?.dispose()
  destinationChart?.dispose()
})
</script>

<style scoped>
.order-dashboard-page {
  padding: 16px;
  background: #f5f7fa;
  min-height: 100vh;
  position: relative;
}

/* 页面头部 */
.page-header {
  margin-bottom: 16px;
  position: relative;
  z-index: 1;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
  padding: 20px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-icon {
  font-size: 36px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 4px 0;
}

.subtitle {
  color: #6b7280;
  font-size: 14px;
  margin: 0;
  line-height: 1.4;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-tag {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 8px;
  background: #10b981;
  border: none;
  color: white;
}

/* 筛选卡片 */
.filter-card {
  margin-bottom: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
  background: #ffffff;
  position: relative;
  z-index: 1;
}

.filter-card :deep(.el-card__body) {
  padding: 12px 20px;
}

.filter-card :deep(.el-card__header) {
  padding: 12px 20px;
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
  font-size: 18px;
  color: #667eea;
}

.header-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.filter-content {
  padding: 12px 0;
}

.filter-row {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.filter-section {
  margin-bottom: 0;
}

.filter-section-year {
  flex: 2;
}

.filter-section-month {
  flex: 8;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #e5e7eb;
}

.year-selector {
  display: flex;
  justify-content: flex-start;
}

.year-select {
  width: 100%;
  max-width: 200px;
}

.month-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-start;
}

.month-btn {
  min-width: 65px;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s ease;
  border: 1px solid #d1d5db;
  padding: 6px 12px;
}

.month-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.month-btn.active {
  background: #667eea;
  border-color: #667eea;
  color: white;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

/* 统计概览 */
.stats-overview {
  margin-bottom: 16px;
  position: relative;
  z-index: 1;
}

.stats-overview :deep(.el-row) {
  margin: 0 -8px;
}

.stats-overview :deep(.el-col) {
  padding: 0 8px;
}

.stat-card {
  border-radius: 12px;
  border: none;
  overflow: hidden;
  transition: all 0.2s ease;
  height: 110px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.total-orders-card {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.total-forecast-card {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.avg-forecast-card {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;
}

.stat-content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 14px 16px;
  height: 100%;
  position: relative;
}

.stat-info {
  flex: 1;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
  font-weight: 500;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1;
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 6px;
}

.stat-value.primary {
  color: white;
}

.stat-value.success {
  color: white;
}

.stat-value.danger {
  color: #fecaca;
}

.stat-value.info {
  color: white;
}

.stat-unit {
  font-size: 14px;
  font-weight: 500;
  opacity: 0.8;
}

.stat-trend {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 16px;
}

.trend-up {
  color: rgba(255, 255, 255, 0.8);
}

.trend-warning {
  color: #fbbf24;
}

.trend-stable {
  color: rgba(255, 255, 255, 0.6);
}

/* 排行榜卡片 */
.ranking-card {
  margin-bottom: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
  background: #ffffff;
  position: relative;
  z-index: 1;
}

.ranking-card :deep(.el-card__body) {
  padding: 12px 16px;
}

.ranking-card :deep(.el-card__header) {
  padding: 12px 16px;
}

.ranking-tag {
  background: #f59e0b;
  border: none;
  color: white;
  font-size: 11px;
}

.ranking-content {
  padding: 0;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ranking-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 6px;
  transition: all 0.2s ease;
  border: 1px solid #e5e7eb;
}

.ranking-item:hover {
  background: #f3f4f6;
  transform: translateX(2px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.rank-number {
  width: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.rank-medal {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  font-weight: bold;
}

.rank-medal.gold {
  color: #fbbf24;
}

.rank-medal.silver {
  color: #9ca3af;
}

.rank-medal.bronze {
  color: #d97706;
}

.rank-number-normal {
  font-size: 16px;
  font-weight: bold;
  color: #64748b;
}

.rank-info {
  flex: 1;
  margin-left: 12px;
}

.destination-name {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 1px;
}

.destination-code {
  font-size: 10px;
  color: #64748b;
}

.rank-value {
  text-align: right;
  margin-right: 12px;
}

.value-number {
  font-size: 14px;
  font-weight: bold;
  color: #059669;
}

.value-unit {
  font-size: 10px;
  color: #64748b;
}

.rank-progress {
  width: 90px;
}

/* 其他卡片 */
.forecast-diff-card,
.table-card,
.chart-card {
  margin-bottom: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
  background: #ffffff;
  position: relative;
  z-index: 1;
}

.table-card :deep(.el-card__body) {
  padding: 12px 16px;
}

.table-card :deep(.el-card__header) {
  padding: 12px 16px;
}

.data-count-tag {
  margin-left: 10px;
  background: #667eea;
  border: none;
  color: white;
  font-size: 11px;
}

/* 表格样式 */
.table-container {
  overflow-x: auto;
}

.data-table {
  border-radius: 8px;
  overflow: hidden;
}

/* 表格单元格padding优化 */
.data-table :deep(.el-table__header-wrapper) {
  font-size: 13px;
}

.data-table :deep(.el-table__header th) {
  padding: 8px 0;
  font-size: 13px;
  font-weight: 600;
}

.data-table :deep(.el-table__body td) {
  padding: 6px 0;
}

.data-table :deep(.el-table__row) {
  height: auto;
}

.index-cell {
  font-weight: 600;
  color: #64748b;
  font-size: 12px;
}

.destination-cell {
  padding: 4px 0;
}

.destination-cell .destination-name {
  font-weight: 600;
  color: #374151;
  font-size: 12px;
  line-height: 1.3;
}

.destination-cell .destination-code {
  color: #6b7280;
  font-size: 10px;
  margin-top: 1px;
  line-height: 1.2;
}

.order-badge {
  font-size: 11px;
}

.forecast-cell {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 3px;
}

.forecast-value {
  font-size: 13px;
  font-weight: bold;
  color: #059669;
}

.forecast-unit {
  font-size: 10px;
  color: #64748b;
}

.average-cell {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #3b82f6;
  font-size: 12px;
}

/* 表格行样式 */
:deep(.high-value-row) {
  background-color: rgba(16, 185, 129, 0.05);
}

:deep(.medium-value-row) {
  background-color: rgba(59, 130, 246, 0.05);
}

/* 图表区域 */
.charts-section {
  position: relative;
  z-index: 1;
}

.charts-section :deep(.el-row) {
  margin: 0 -8px;
}

.charts-section :deep(.el-col) {
  padding: 0 8px;
}

.chart {
  width: 100%;
  height: 320px;
  min-height: 280px;
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
  background: #ffffff;
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 48px;
}

.loading-icon {
  font-size: 28px;
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
  font-size: 14px;
  font-weight: 500;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .charts-section .el-col {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .order-dashboard-page {
    padding: 12px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }

  .title {
    font-size: 20px;
  }

  .title-icon {
    font-size: 28px;
  }

  .filter-content {
    padding: 10px 0;
  }

  .filter-row {
    flex-direction: column;
    gap: 12px;
  }

  .section-title {
    margin-bottom: 6px;
    padding-bottom: 3px;
  }

  .year-select {
    width: 180px;
  }

  .month-buttons {
    gap: 5px;
  }

  .month-btn {
    min-width: 60px;
    font-size: 12px;
    padding: 5px 10px;
  }

  .stats-overview .el-col {
    margin-bottom: 12px;
  }

  .stat-card {
    height: 110px;
  }

  .stat-content {
    padding: 10px;
  }

  .stat-value {
    font-size: 20px;
  }

  .stat-label {
    font-size: 11px;
    margin-bottom: 4px;
  }

  .stat-unit {
    font-size: 12px;
  }

  .ranking-item {
    padding: 8px 10px;
  }

  .ranking-list {
    gap: 5px;
  }

  .rank-number {
    width: 35px;
  }

  .rank-info {
    margin-left: 8px;
  }

  .rank-value {
    margin-right: 8px;
  }

  .rank-progress {
    width: 60px;
  }

  .destination-name {
    font-size: 12px;
  }

  .destination-code {
    font-size: 9px;
  }

  .value-number {
    font-size: 13px;
  }

  .chart {
    height: 280px;
  }
}

@media (max-width: 480px) {
  .title-section {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }

  .month-buttons {
    justify-content: center;
  }

  .ranking-item {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }

  .rank-info {
    margin-left: 0;
  }

  .rank-value {
    margin-right: 0;
  }

  .rank-progress {
    width: 100%;
  }

  .data-table {
    font-size: 12px;
  }

  .data-table :deep(.el-table__header th) {
    padding: 6px 0;
    font-size: 12px;
  }

  .data-table :deep(.el-table__body td) {
    padding: 4px 0;
  }

  .destination-cell {
    padding: 3px 0;
  }

  .destination-cell .destination-name {
    font-size: 11px;
  }

  .destination-cell .destination-code {
    font-size: 9px;
  }

  .forecast-value {
    font-size: 12px;
  }

  .average-cell {
    font-size: 11px;
  }
}
</style>
