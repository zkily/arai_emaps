<template>
  <div class="inventory-value-charts">
    <!-- 图表容器 -->
    <div class="charts-container">
      <div class="charts-grid">
        <!-- 项目别分布饼图 -->
        <div class="chart-card">
          <el-card class="chart-wrapper">
            <template #header>
              <div class="chart-header">
                <h3 class="chart-title">
                  <PieChart class="title-icon" />
                  項目別金額分布
                </h3>
                <div class="chart-actions">
                  <el-button
                    size="small"
                    @click="refreshChart('distribution')"
                    :loading="loading.distribution"
                  >
                    <Refresh class="btn-icon" />
                    更新
                  </el-button>
                </div>
              </div>
            </template>
            <div class="chart-content">
              <div
                ref="distributionChart"
                class="chart-container"
                v-loading="loading.distribution"
              ></div>
            </div>
          </el-card>
        </div>

        <!-- 期间别推移折线图 -->
        <div class="chart-card">
          <el-card class="chart-wrapper">
            <template #header>
              <div class="chart-header">
                <h3 class="chart-title">
                  <DataAnalysis class="title-icon" />
                  期間別金額推移
                </h3>
                <div class="chart-actions">
                  <el-select
                    v-model="trendPeriod"
                    size="small"
                    @change="loadTrendChart"
                    style="width: 100px; margin-right: 10px"
                  >
                    <el-option label="月別" value="monthly" />
                    <el-option label="週別" value="weekly" />
                    <el-option label="日別" value="daily" />
                  </el-select>
                  <el-button size="small" @click="refreshChart('trend')" :loading="loading.trend">
                    <Refresh class="btn-icon" />
                    更新
                  </el-button>
                </div>
              </div>
            </template>
            <div class="chart-content">
              <div ref="trendChart" class="chart-container" v-loading="loading.trend"></div>
            </div>
          </el-card>
        </div>

        <!-- 工程别比较柱状图 -->
        <div class="chart-card">
          <el-card class="chart-wrapper">
            <template #header>
              <div class="chart-header">
                <h3 class="chart-title">
                  <Histogram class="title-icon" />
                  工程別金額比較
                </h3>
                <div class="chart-actions">
                  <el-button
                    size="small"
                    @click="refreshChart('process')"
                    :loading="loading.process"
                  >
                    <Refresh class="btn-icon" />
                    更新
                  </el-button>
                </div>
              </div>
            </template>
            <div class="chart-content">
              <div ref="processChart" class="chart-container" v-loading="loading.process"></div>
            </div>
          </el-card>
        </div>

        <!-- 热力图 -->
        <div class="chart-card full-width">
          <el-card class="chart-wrapper">
            <template #header>
              <div class="chart-header">
                <h3 class="chart-title">
                  <Grid class="title-icon" />
                  月別工程別金額分布ヒートマップ
                </h3>
                <div class="chart-actions">
                  <el-date-picker
                    v-model="heatmapYear"
                    type="year"
                    placeholder="年を選択"
                    format="YYYY年"
                    value-format="YYYY"
                    size="small"
                    @change="loadHeatmapChart"
                    style="width: 120px; margin-right: 10px"
                  />
                  <el-button
                    size="small"
                    @click="refreshChart('heatmap')"
                    :loading="loading.heatmap"
                  >
                    <Refresh class="btn-icon" />
                    更新
                  </el-button>
                </div>
              </div>
            </template>
            <div class="chart-content">
              <div
                ref="heatmapChart"
                class="chart-container heatmap-container"
                v-loading="loading.heatmap"
              ></div>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <!-- 图表数据详情弹窗 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="detailDialogTitle"
      width="800px"
      class="chart-detail-dialog"
    >
      <div class="detail-content">
        <el-table :data="detailData" v-loading="detailLoading" class="detail-table">
          <el-table-column prop="name" label="項目" width="150" />
          <el-table-column prop="value" label="金額" align="right">
            <template #default="{ row }">
              <strong>¥{{ formatNumber(row.value) }}</strong>
            </template>
          </el-table-column>
          <el-table-column prop="percentage" label="割合" width="100" align="right">
            <template #default="{ row }"> {{ row.percentage }}% </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="120" align="right">
            <template #default="{ row }">
              {{ formatNumber(row.quantity, 3) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDetailDialog = false">閉じる</el-button>
          <el-button type="primary" @click="exportDetailData">
            <Download class="btn-icon" />
            データ出力
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { PieChart, DataAnalysis, Histogram, Grid, Refresh, Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { inventoryValueApi } from '@/api/inventoryValue'

// 类型定义
interface ChartInstance {
  setOption: (option: any) => void
  off: (event: string) => void
  on: (event: string, callback: (params: any) => void) => void
  resize: () => void
  dispose: () => void
}

interface QueryParams {
  startDate?: string
  endDate?: string
  itemType?: string
  processCode?: string
  period?: string
  year?: string
  type?: string
}

interface ChartDataItem {
  value: number
  name: string
}

// NOTE: 现阶段 inventoryValueApi はプレースホルダで型が確定しないため、
// 図表の厳密型インターフェースは省略しています（detailData を any[] で受ける）。

// Props
const props = defineProps({
  dateRange: {
    type: Array,
    default: () => [],
  },
  itemType: {
    type: String,
    default: 'all',
  },
  processCode: {
    type: String,
    default: 'all',
  },
})

// 响应式数据
const loading = reactive({
  distribution: false,
  trend: false,
  process: false,
  heatmap: false,
})

const trendPeriod = ref('monthly')
const heatmapYear = ref(new Date().getFullYear().toString())

// 图表实例
const distributionChart = ref()
const trendChart = ref()
const processChart = ref()
const heatmapChart = ref()

let distributionChartInstance: ChartInstance | null = null
let trendChartInstance: ChartInstance | null = null
let processChartInstance: ChartInstance | null = null
let heatmapChartInstance: ChartInstance | null = null

// 详情弹窗
const showDetailDialog = ref(false)
const detailDialogTitle = ref('')
const detailData = ref<any[]>([])
const detailLoading = ref(false)

// 方法
const formatNumber = (value: number | string, decimals = 0): string => {
  if (!value && value !== 0) return '0'
  return Number(value).toLocaleString('ja-JP', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

// 获取查询参数
const getQueryParams = (): QueryParams => {
  const params: QueryParams = {}
  if (props.dateRange && props.dateRange.length === 2) {
    params.startDate = props.dateRange[0] as string
    params.endDate = props.dateRange[1] as string
  }
  if (props.itemType && props.itemType !== 'all') {
    params.itemType = props.itemType
  }
  if (props.processCode && props.processCode !== 'all') {
    params.processCode = props.processCode
  }
  return params
}

// 加载项目别分布图
const loadDistributionChart = async () => {
  try {
    loading.distribution = true
    const params = getQueryParams()
    const response = await inventoryValueApi.getItemDistributionChart(params)
    const data = response.data

    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: ¥{c} ({d}%)',
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        textStyle: {
          color: '#333',
        },
      },
      series: [
        {
          name: '金額分布',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['60%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: false,
            position: 'center',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 20,
              fontWeight: 'bold',
            },
          },
          labelLine: {
            show: false,
          },
          data: data.map((item: ChartDataItem) => ({
            value: item.value,
            name: item.name,
            itemStyle: {
              color: getItemColor(item.name),
            },
          })),
        },
      ],
    }

    if (distributionChartInstance) {
      distributionChartInstance.setOption(option)
      // 添加点击事件
      distributionChartInstance.off('click')
      distributionChartInstance.on('click', (params) => {
        showChartDetail('項目別詳細', params.name)
      })
    }
  } catch (error) {
    console.error('分布图加载失败:', error)
    ElMessage.error('分布図の読み込みに失敗しました')
  } finally {
    loading.distribution = false
  }
}

// 加载趋势图
const loadTrendChart = async () => {
  try {
    loading.trend = true
    const params = {
      ...getQueryParams(),
      period: trendPeriod.value,
    }
    const response = await inventoryValueApi.getPeriodTrendChart(params)
    const data = response.data

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          label: {
            backgroundColor: '#6a7985',
          },
        },
      },
      legend: {
        data: ['材料', '部品', 'ステー', '合計'],
        textStyle: {
          color: '#333',
        },
      },
      toolbox: {
        feature: {
          saveAsImage: {},
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: [
        {
          type: 'category',
          boundaryGap: false,
          data: data.dates,
        },
      ],
      yAxis: [
        {
          type: 'value',
          axisLabel: {
            formatter: '¥{value}',
          },
        },
      ],
      series: [
        {
          name: '材料',
          type: 'line',
          stack: 'Total',
          areaStyle: {},
          emphasis: {
            focus: 'series',
          },
          data: data.material,
          itemStyle: {
            color: '#3b82f6',
          },
        },
        {
          name: '部品',
          type: 'line',
          stack: 'Total',
          areaStyle: {},
          emphasis: {
            focus: 'series',
          },
          data: data.component,
          itemStyle: {
            color: '#10b981',
          },
        },
        {
          name: 'ステー',
          type: 'line',
          stack: 'Total',
          areaStyle: {},
          emphasis: {
            focus: 'series',
          },
          data: data.stay,
          itemStyle: {
            color: '#f59e0b',
          },
        },
        {
          name: '合計',
          type: 'line',
          data: data.total,
          itemStyle: {
            color: '#667eea',
          },
          lineStyle: {
            width: 3,
          },
        },
      ],
    }

    if (trendChartInstance) {
      trendChartInstance.setOption(option)
    }
  } catch (error) {
    console.error('趋势图加载失败:', error)
    ElMessage.error('推移図の読み込みに失敗しました')
  } finally {
    loading.trend = false
  }
}

// 加载工程比较图
const loadProcessChart = async () => {
  try {
    loading.process = true
    const params = getQueryParams()
    const response = await inventoryValueApi.getProcessComparisonChart(params)
    const data = response.data

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      legend: {
        data: ['金額', '数量'],
        textStyle: {
          color: '#333',
        },
      },
      toolbox: {
        feature: {
          saveAsImage: {},
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
        data: data.processes,
        axisLabel: {
          interval: 0,
          rotate: 45,
        },
      },
      yAxis: [
        {
          type: 'value',
          name: '金額',
          position: 'left',
          axisLabel: {
            formatter: '¥{value}',
          },
        },
        {
          type: 'value',
          name: '数量',
          position: 'right',
          axisLabel: {
            formatter: '{value}',
          },
        },
      ],
      series: [
        {
          name: '金額',
          type: 'bar',
          yAxisIndex: 0,
          data: data.values,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#667eea' },
              { offset: 1, color: '#764ba2' },
            ]),
          },
        },
        {
          name: '数量',
          type: 'line',
          yAxisIndex: 1,
          data: data.quantities,
          itemStyle: {
            color: '#10b981',
          },
        },
      ],
    }

    if (processChartInstance) {
      processChartInstance.setOption(option)
      // 添加点击事件
      processChartInstance.off('click')
      processChartInstance.on('click', (params) => {
        showChartDetail('工程別詳細', params.name)
      })
    }
  } catch (error) {
    console.error('工程比较图加载失败:', error)
    ElMessage.error('工程比較図の読み込みに失敗しました')
  } finally {
    loading.process = false
  }
}

// 加载热力图
const loadHeatmapChart = async () => {
  try {
    loading.heatmap = true
    const params = {
      ...getQueryParams(),
      year: heatmapYear.value,
    }
    const response = await inventoryValueApi.getHeatmapData(params)
    const data = response.data

    const months = [
      '1月',
      '2月',
      '3月',
      '4月',
      '5月',
      '6月',
      '7月',
      '8月',
      '9月',
      '10月',
      '11月',
      '12月',
    ]
    const processes = data.processes
    const heatmapData: [number, number, number][] = []

    data.data.forEach((item: number[], i: number) => {
      item.forEach((value: number, j: number) => {
        heatmapData.push([j, i, value || 0])
      })
    })

    const option = {
      tooltip: {
        position: 'top',
        formatter: function (params: any) {
          return `${months[params.data[0]]} ${processes[params.data[1]]}<br/>金額: ¥${formatNumber(params.data[2])}`
        },
      },
      grid: {
        height: '50%',
        top: '10%',
      },
      xAxis: {
        type: 'category',
        data: months,
        splitArea: {
          show: true,
        },
      },
      yAxis: {
        type: 'category',
        data: processes,
        splitArea: {
          show: true,
        },
      },
      visualMap: {
        min: 0,
        max: Math.max(...heatmapData.map((item) => item[2])),
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '15%',
        inRange: {
          color: [
            '#313695',
            '#4575b4',
            '#74add1',
            '#abd9e9',
            '#e0f3f8',
            '#ffffcc',
            '#fee090',
            '#fdae61',
            '#f46d43',
            '#d73027',
            '#a50026',
          ],
        },
      },
      series: [
        {
          name: '金額',
          type: 'heatmap',
          data: heatmapData,
          label: {
            show: true,
            formatter: function (params: any) {
              return params.data[2] > 0 ? formatNumber(params.data[2]) : ''
            },
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    }

    if (heatmapChartInstance) {
      heatmapChartInstance.setOption(option)
    }
  } catch (error) {
    console.error('热力图加载失败:', error)
    ElMessage.error('ヒートマップの読み込みに失敗しました')
  } finally {
    loading.heatmap = false
  }
}

// 获取项目颜色
const getItemColor = (itemName: string): string => {
  const colorMap: Record<string, string> = {
    材料: '#3b82f6',
    部品: '#10b981',
    ステー: '#f59e0b',
  }
  return colorMap[itemName] || '#667eea'
}

// 刷新图表
const refreshChart = (chartType: string): void => {
  switch (chartType) {
    case 'distribution':
      loadDistributionChart()
      break
    case 'trend':
      loadTrendChart()
      break
    case 'process':
      loadProcessChart()
      break
    case 'heatmap':
      loadHeatmapChart()
      break
  }
}

// 显示图表详情
const showChartDetail = async (title: string, name: string): Promise<void> => {
  try {
    detailLoading.value = true
    detailDialogTitle.value = `${title} - ${name}`

    // 根据图表类型获取详细数据
    const params = {
      ...getQueryParams(),
      type: name,
    }
    const response = await inventoryValueApi.getValueAnalysis(params)
    detailData.value = response.data

    showDetailDialog.value = true
  } catch (error) {
    console.error('详情数据加载失败:', error)
    ElMessage.error('詳細データの読み込みに失敗しました')
  } finally {
    detailLoading.value = false
  }
}

// 导出详情数据
const exportDetailData = () => {
  // 实现数据导出逻辑
  ElMessage.success('データ出力機能は開発中です')
}

// 初始化图表
const initCharts = () => {
  nextTick(() => {
    if (distributionChart.value) {
      distributionChartInstance = echarts.init(distributionChart.value)
    }
    if (trendChart.value) {
      trendChartInstance = echarts.init(trendChart.value)
    }
    if (processChart.value) {
      processChartInstance = echarts.init(processChart.value)
    }
    if (heatmapChart.value) {
      heatmapChartInstance = echarts.init(heatmapChart.value)
    }

    // 加载所有图表数据
    loadDistributionChart()
    loadTrendChart()
    loadProcessChart()
    loadHeatmapChart()

    // 监听窗口大小变化
    window.addEventListener('resize', handleResize)
  })
}

// 处理窗口大小变化
const handleResize = () => {
  if (distributionChartInstance) distributionChartInstance.resize()
  if (trendChartInstance) trendChartInstance.resize()
  if (processChartInstance) processChartInstance.resize()
  if (heatmapChartInstance) heatmapChartInstance.resize()
}

// 销毁图表
const destroyCharts = () => {
  if (distributionChartInstance) {
    distributionChartInstance.dispose()
    distributionChartInstance = null
  }
  if (trendChartInstance) {
    trendChartInstance.dispose()
    trendChartInstance = null
  }
  if (processChartInstance) {
    processChartInstance.dispose()
    processChartInstance = null
  }
  if (heatmapChartInstance) {
    heatmapChartInstance.dispose()
    heatmapChartInstance = null
  }
  window.removeEventListener('resize', handleResize)
}

// 监听props变化
watch(
  () => [props.dateRange, props.itemType, props.processCode],
  () => {
    if (distributionChartInstance) loadDistributionChart()
    if (trendChartInstance) loadTrendChart()
    if (processChartInstance) loadProcessChart()
    if (heatmapChartInstance) loadHeatmapChart()
  },
  { deep: true },
)

// 生命周期
onMounted(() => {
  initCharts()
})

onUnmounted(() => {
  destroyCharts()
})

// 暴露方法给父组件
defineExpose({
  refreshAllCharts: () => {
    loadDistributionChart()
    loadTrendChart()
    loadProcessChart()
    loadHeatmapChart()
  },
})
</script>

<style scoped>
.inventory-value-charts {
  width: 100%;
  padding: 0;
}

.charts-container {
  padding: 24px 0;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.chart-card {
  min-height: 420px;
  transition: all 0.3s ease;
  animation: fadeInScale 0.6s ease-out;
  animation-fill-mode: both;
}

.chart-card:nth-child(1) {
  animation-delay: 0.1s;
}
.chart-card:nth-child(2) {
  animation-delay: 0.2s;
}
.chart-card:nth-child(3) {
  animation-delay: 0.3s;
}
.chart-card:nth-child(4) {
  animation-delay: 0.4s;
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.chart-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.chart-card.full-width {
  grid-column: 1 / -1;
  min-height: 520px;
}

.chart-wrapper {
  height: 100%;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chart-wrapper :deep(.el-card__header) {
  background: rgba(248, 250, 252, 0.8);
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  padding: 20px 25px;
  backdrop-filter: blur(10px);
}

.chart-wrapper :deep(.el-card__body) {
  padding: 0;
  height: calc(100% - 80px);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-title {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 20px;
  color: #667eea;
}

.chart-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chart-content {
  height: 100%;
  padding: 24px;
  position: relative;
}

.chart-container {
  width: 100%;
  height: 320px;
}

.heatmap-container {
  height: 420px;
}

.btn-icon {
  font-size: 14px;
}

/* Element Plus 组件样式覆盖 */
:deep(.el-button) {
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
}

:deep(.el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

:deep(.el-button--default) {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #e5e7eb;
  color: #374151;
  backdrop-filter: blur(10px);
}

:deep(.el-button--default:hover) {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-1px);
}

:deep(.el-loading-mask) {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
}

/* 详情弹窗样式 */
.chart-detail-dialog :deep(.el-dialog) {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
}

.chart-detail-dialog :deep(.el-dialog__header) {
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px 25px;
}

.chart-detail-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
}

.chart-detail-dialog :deep(.el-dialog__body) {
  padding: 25px;
}

.detail-content {
  color: white;
}

.detail-table {
  background: transparent;
}

.detail-table :deep(.el-table__header-wrapper) {
  background: rgba(255, 255, 255, 0.05);
}

.detail-table :deep(.el-table__header th) {
  background: transparent;
  color: white;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.detail-table :deep(.el-table__body tr) {
  background: rgba(255, 255, 255, 0.02);
}

.detail-table :deep(.el-table__body tr:hover) {
  background: rgba(255, 255, 255, 0.08);
}

.detail-table :deep(.el-table__body td) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.9);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px 25px;
  background: rgba(255, 255, 255, 0.02);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }

  .chart-card.full-width {
    grid-column: 1;
  }
}

@media (max-width: 768px) {
  .charts-container {
    padding: 15px 0;
  }

  .charts-grid {
    gap: 15px;
  }

  .chart-card {
    min-height: 350px;
  }

  .chart-container {
    height: 250px;
  }

  .heatmap-container {
    height: 350px;
  }

  .chart-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }

  .chart-actions {
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 480px) {
  .chart-content {
    padding: 15px;
  }

  .chart-container {
    height: 200px;
  }

  .heatmap-container {
    height: 300px;
  }
}
</style>
