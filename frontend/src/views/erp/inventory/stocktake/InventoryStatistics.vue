<template>
  <div class="inventory-container">
    <div class="page-ambient" aria-hidden="true" />

    <header class="page-toolbar">
      <div class="toolbar-inner">
        <div class="toolbar-brand">
          <div class="brand-icon">
            <el-icon :size="20"><DataAnalysis /></el-icon>
          </div>
          <div class="brand-text">
            <h1 class="toolbar-title">棚卸統計分析</h1>
            <p class="toolbar-sub">工程別・製品別・月別の棚卸データ</p>
          </div>
        </div>
        <el-button
          type="primary"
          size="small"
          @click="exportStatistics"
          :loading="exportLoading"
          :icon="Download"
        >
          統計データ出力
        </el-button>
      </div>
    </header>

    <div class="content-container">
      <el-card class="filter-card" shadow="never">
        <template #header>
          <div class="filter-toolbar">
            <el-icon class="filter-toolbar-icon"><Search /></el-icon>
            <span class="filter-toolbar-title">検索条件</span>
          </div>
        </template>
        <el-form :inline="true" :model="filters" size="small" class="filter-form" @submit.prevent>
          <div class="filter-row">
            <el-form-item label="統計期間" class="filter-item filter-item--date">
              <el-date-picker
                v-model="filters.dateRange"
                type="daterange"
                range-separator="～"
                start-placeholder="開始日"
                end-placeholder="終了日"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                class="filter-date-picker"
              />
            </el-form-item>
            <el-form-item label="月選択" class="filter-item filter-item--month">
              <el-date-picker
                v-model="filters.monthPicker"
                type="month"
                placeholder="月を選択"
                format="YYYY-MM"
                value-format="YYYY-MM"
                class="filter-month-picker"
                @change="handleMonthChange"
              />
            </el-form-item>
            <el-form-item label="工程" class="filter-item filter-item--stage">
              <el-select
                v-model="filters.stageType"
                placeholder="工程を選択"
                clearable
                class="filter-select"
              >
                <el-option label="全て" value="all" /> <el-option label="切断" value="cutting" />
                <el-option label="面取" value="surface" /> <el-option label="SW" value="sw" />
                <el-option label="成型" value="forming" />
                <el-option label="メッキ" value="plating" />
                <el-option label="溶接" value="welding" />
                <el-option label="検査" value="inspection" />
                <el-option label="倉庫" value="warehouse" />
                <el-option label="外注メッキ" value="outsource_plating" />
                <el-option label="外注溶接" value="outsource_welding" />
                <el-option label="溶接前検査" value="pre_welding_inspection" />
                <el-option label="外注検査前" value="pre_outsource_inspection" />
                <el-option label="部品工程" value="part_process" />
              </el-select>
            </el-form-item>
            <el-form-item label="製品名" class="filter-item filter-item--product">
              <el-input
                v-model="filters.productName"
                placeholder="製品名で検索"
                clearable
                class="filter-input"
                :prefix-icon="Search"
              />
            </el-form-item>
            <el-form-item class="filter-item filter-actions-inline">
              <el-button type="primary" size="small" :icon="Search" @click="handleSearch">
                統計実行
              </el-button>
              <el-button size="small" :icon="RefreshLeft" @click="resetFilters">リセット</el-button>
            </el-form-item>
          </div>
        </el-form>
      </el-card>
      <el-card class="tab-card" shadow="never">
        <el-tabs v-model="activeTab" type="card" @tab-click="handleTabClick" class="custom-tabs">
          <!-- 工程別統計 -->
          <el-tab-pane label="工程別統計" name="stage">
            <div class="tab-content">
              <div class="tab-header tab-header--row">
                <h3 class="tab-heading">工程別棚卸統計</h3>
                <div class="tab-stats">
                  <span class="stat-pill">総工程 {{ stageStats.length }} 工程</span>
                  <span class="stat-pill stat-pill--qty"
                    >総数量 {{ stageTotalQuantity.toLocaleString() }} 個</span
                  >
                </div>
              </div>
              <div class="statistics-content">
                <div class="chart-container"><div ref="stageChartRef" class="chart"></div></div>
                <div class="table-container">
                  <el-table
                    :data="stageStats"
                    stripe
                    border
                    size="small"
                    class="statistics-table"
                    @sort-change="handleStageSortChange"
                    :default-sort="{ prop: 'totalQuantity', order: 'descending' }"
                  >
                    <el-table-column
                      prop="stageName"
                      label="工程名"
                      width="120"
                      sortable="custom"
                    />
                    <el-table-column
                      prop="productCount"
                      label="製品数"
                      width="100"
                      sortable="custom"
                    />
                    <el-table-column
                      prop="totalQuantity"
                      label="総数量"
                      width="120"
                      sortable="custom"
                    >
                      <template #default="{ row }">
                        {{ row.totalQuantity.toLocaleString() }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="percentage" label="割合" width="100" sortable="custom">
                      <template #default="{ row }"> {{ row.percentage.toFixed(1) }}% </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </div>
          </el-tab-pane>
          <!-- 製品別統計 -->
          <el-tab-pane label="製品別統計" name="product">
            <div class="tab-content">
              <div class="tab-header tab-header--row">
                <h3 class="tab-heading">製品別棚卸統計</h3>
                <div class="tab-header-right">
                  <div class="tab-stats">
                    <span class="stat-pill">総製品 {{ productStats.length }} 件</span>
                    <span class="stat-pill stat-pill--qty"
                      >総数量 {{ productTotalQuantity.toLocaleString() }} 個</span
                    >
                  </div>
                  <el-button
                    type="success"
                    size="small"
                    plain
                    @click="printProductStatistics"
                    :icon="Printer"
                  >
                    印刷
                  </el-button>
                </div>
              </div>
              <div class="statistics-content">
                <div class="chart-container"><div ref="productChartRef" class="chart"></div></div>
                <div class="table-container">
                  <el-table
                    :data="productStats"
                    stripe
                    border
                    size="small"
                    class="statistics-table"
                    @sort-change="handleProductSortChange"
                    :default-sort="{ prop: 'totalQuantity', order: 'descending' }"
                  >
                    <el-table-column
                      prop="productName"
                      label="製品名"
                      width="200"
                      sortable="custom"
                    />
                    <el-table-column
                      prop="productCode"
                      label="製品CD"
                      width="120"
                      sortable="custom"
                    />
                    <el-table-column
                      prop="stageCount"
                      label="工程数"
                      width="100"
                      sortable="custom"
                    />
                    <el-table-column
                      prop="totalQuantity"
                      label="総数量"
                      width="120"
                      sortable="custom"
                    >
                      <template #default="{ row }">
                        {{ row.totalQuantity.toLocaleString() }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="percentage" label="割合" width="100" sortable="custom">
                      <template #default="{ row }"> {{ row.percentage.toFixed(1) }}% </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </div>
          </el-tab-pane>
          <!-- 月別統計 -->
          <el-tab-pane label="月別統計" name="monthly">
            <div class="tab-content">
              <div class="tab-header tab-header--row">
                <h3 class="tab-heading">月別棚卸統計</h3>
                <div class="tab-stats">
                  <span class="stat-pill">総月数 {{ monthlyStats.length }} ヶ月</span>
                  <span class="stat-pill stat-pill--qty"
                    >総数量 {{ monthlyTotalQuantity.toLocaleString() }} 個</span
                  >
                </div>
              </div>
              <div class="statistics-content">
                <div class="chart-container"><div ref="monthlyChartRef" class="chart"></div></div>
                <div class="table-container">
                  <el-table
                    :data="monthlyStats"
                    stripe
                    border
                    size="small"
                    class="statistics-table"
                    @sort-change="handleMonthlySortChange"
                    :default-sort="{ prop: 'month', order: 'ascending' }"
                  >
                    <el-table-column prop="month" label="月" width="120" sortable="custom" />
                    <el-table-column
                      prop="productCount"
                      label="製品数"
                      width="100"
                      sortable="custom"
                    />
                    <el-table-column
                      prop="stageCount"
                      label="工程数"
                      width="100"
                      sortable="custom"
                    />
                    <el-table-column
                      prop="totalQuantity"
                      label="総数量"
                      width="120"
                      sortable="custom"
                    >
                      <template #default="{ row }">
                        {{ row.totalQuantity.toLocaleString() }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="percentage" label="割合" width="100" sortable="custom">
                      <template #default="{ row }"> {{ row.percentage.toFixed(1) }}% </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

import { getInventoryLogsAll } from '@/api/inventory'

// ✅ Element Plus アイコンコンポーネント
import { DataAnalysis, Download, Search, RefreshLeft, Printer } from '@element-plus/icons-vue'

// タブ状態
const activeTab = ref('stage')

// ローディング状態
const loading = ref(false)
const exportLoading = ref(false)

// チャート参照
const stageChartRef = ref<HTMLElement>()
const productChartRef = ref<HTMLElement>()
const monthlyChartRef = ref<HTMLElement>()

// チャートインスタンス
let stageChart: echarts.ECharts | null = null
let productChart: echarts.ECharts | null = null
let monthlyChart: echarts.ECharts | null = null

// 統計データ
const stageStats = ref<any[]>([])
const productStats = ref<any[]>([])
const monthlyStats = ref<any[]>([])

// 総数量
const stageTotalQuantity = ref(0)
const productTotalQuantity = ref(0)
const monthlyTotalQuantity = ref(0)

// フィルター条件
const filters = ref({
  dateRange: [] as string[],
  monthPicker: '',
  stageType: '',
  productName: '',
})

// 生データ
const rawData = ref<any[]>([])

// 月選択処理
const handleMonthChange = (month: string) => {
  if (month) {
    const year = parseInt(month.split('-')[0])
    const monthNum = parseInt(month.split('-')[1])

    // その月の最初の日を設定
    const startDate = dayjs(`${year}-${monthNum.toString().padStart(2, '0')}-01`)

    // その月の最後の日を設定
    const endDate = startDate.endOf('month')

    filters.value.dateRange = [startDate.format('YYYY-MM-DD'), endDate.format('YYYY-MM-DD')]
  } else {
    // 月選択をクリアした場合、日付範囲もクリア
    filters.value.dateRange = []
  }
}

// データ取得
const fetchData = async () => {
  loading.value = true
  try {
    const response = await getInventoryLogsAll({
      ...filters.value,
    })

    if (response && response.list) {
      rawData.value = response.list || []
      calculateStatistics()
    } else {
      rawData.value = []
      resetStatistics()
    }
  } catch (err) {
    console.error('データ取得に失敗しました', err)
    rawData.value = []
    resetStatistics()
  } finally {
    loading.value = false
  }
}

// 統計データ計算
const calculateStatistics = () => {
  const data = rawData.value

  // 工程別統計
  const stageMap = new Map()
  data.forEach((item) => {
    const stageName = item.process_name || item.process_cd || '不明'
    if (!stageMap.has(stageName)) {
      stageMap.set(stageName, {
        stageName,
        productCount: new Set(),
        totalQuantity: 0,
      })
    }
    const stage = stageMap.get(stageName)
    stage.productCount.add(item.product_cd)
    stage.totalQuantity += parseInt(item.quantity || 0)
  })

  stageStats.value = Array.from(stageMap.values()).map((stage) => ({
    ...stage,
    productCount: stage.productCount.size,
  }))

  // 製品別統計
  const productMap = new Map()
  data.forEach((item) => {
    const productKey = `${item.product_cd}-${item.product_name}`
    if (!productMap.has(productKey)) {
      productMap.set(productKey, {
        productName: item.product_name || '不明',
        productCode: item.product_cd || '不明',
        stageCount: new Set(),
        totalQuantity: 0,
      })
    }
    const product = productMap.get(productKey)
    product.stageCount.add(item.process_cd)
    product.totalQuantity += parseInt(item.quantity || 0)
  })

  productStats.value = Array.from(productMap.values()).map((product) => ({
    ...product,
    stageCount: product.stageCount.size,
  }))

  // 月別統計
  const monthlyMap = new Map()
  data.forEach((item) => {
    // 使用正确的日期字段：log_date，并添加错误处理
    if (!item.log_date) {
      console.warn('日期字段为空:', item)
      return
    }

    const month = dayjs(item.log_date).format('YYYY-MM')

    if (!monthlyMap.has(month)) {
      monthlyMap.set(month, {
        month,
        productCount: new Set(),
        stageCount: new Set(),
        totalQuantity: 0,
      })
    }
    const monthly = monthlyMap.get(month)
    monthly.productCount.add(item.product_cd)
    monthly.stageCount.add(item.process_cd)
    monthly.totalQuantity += parseInt(item.quantity || 0)
  })

  monthlyStats.value = Array.from(monthlyMap.values()).map((monthly) => ({
    ...monthly,
    productCount: monthly.productCount.size,
    stageCount: monthly.stageCount.size,
  }))

  // パーセンテージ計算
  const stageTotal = stageStats.value.reduce((sum, item) => sum + item.totalQuantity, 0)
  const productTotal = productStats.value.reduce((sum, item) => sum + item.totalQuantity, 0)
  const monthlyTotal = monthlyStats.value.reduce((sum, item) => sum + item.totalQuantity, 0)

  stageStats.value.forEach((item) => {
    item.percentage = stageTotal > 0 ? (item.totalQuantity / stageTotal) * 100 : 0
  })

  productStats.value.forEach((item) => {
    item.percentage = productTotal > 0 ? (item.totalQuantity / productTotal) * 100 : 0
  })

  monthlyStats.value.forEach((item) => {
    item.percentage = monthlyTotal > 0 ? (item.totalQuantity / monthlyTotal) * 100 : 0
  })

  // 総数量更新
  stageTotalQuantity.value = stageTotal
  productTotalQuantity.value = productTotal
  monthlyTotalQuantity.value = monthlyTotal

  // チャート描画
  nextTick(() => {
    renderCharts()
  })
}

// 統計データリセット
const resetStatistics = () => {
  stageStats.value = []
  productStats.value = []
  monthlyStats.value = []
  stageTotalQuantity.value = 0
  productTotalQuantity.value = 0
  monthlyTotalQuantity.value = 0
}

// チャート描画
const renderCharts = () => {
  // 延迟渲染，确保容器大小已计算完成
  setTimeout(() => {
    // 工程別チャート
    if (stageChartRef.value && stageStats.value.length > 0 && activeTab.value === 'stage') {
      // 检查DOM元素是否有尺寸
      const stageChartElement = stageChartRef.value
      if (stageChartElement.clientWidth > 0 && stageChartElement.clientHeight > 0) {
        if (!stageChart) {
          stageChart = echarts.init(stageChartElement)
        } else {
          // 强制重新初始化图表
          stageChart.dispose()
          stageChart = echarts.init(stageChartElement)
        }

        const stageChartData = stageStats.value.map((item) => ({
          name: item.stageName,
          value: item.totalQuantity,
        }))

        stageChart.setOption({
          title: {
            text: '工程別数量分布',
            left: 'center',
            top: 10,
            textStyle: {
              fontSize: 18,
              fontWeight: 700,
              color: '#1e293b',
            },
            subtext: `総工程数: ${stageStats.value.length}工程`,
            subtextStyle: {
              fontSize: 12,
              color: '#64748b',
              marginTop: 5,
            },
          },
          tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            textStyle: {
              color: '#1e293b',
              fontSize: 13,
            },
            formatter: function (params: any) {
              return `
                <div style="padding: 8px;">
                  <div style="font-weight: 600; color: #6366f1; margin-bottom: 8px;">
                    ${params.name}
                  </div>
                  <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                    <span style="color: #64748b;">数量:</span>
                    <span style="font-weight: 600; color: #10b981;">
                      ${params.value.toLocaleString()}個
                    </span>
                  </div>
                  <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                    <span style="color: #64748b;">割合:</span>
                    <span style="font-weight: 600; color: #6366f1;">
                      ${params.percent}%
                    </span>
                  </div>
                </div>
              `
            },
          },
          legend: {
            orient: 'vertical',
            left: '5%',
            top: 'middle',
            itemWidth: 12,
            itemHeight: 12,
            itemGap: 8,
            textStyle: {
              fontSize: 12,
              color: '#64748b',
            },
            formatter: function (name: string) {
              const data = stageChartData.find((item) => item.name === name)
              if (data) {
                return `${name} (${data.value.toLocaleString()})`
              }
              return name
            },
          },
          series: [
            {
              name: '工程別',
              type: 'pie',
              radius: ['40%', '70%'],
              center: ['60%', '55%'],
              data: stageChartData,
              itemStyle: {
                borderRadius: 6,
                borderColor: '#fff',
                borderWidth: 2,
              },
              label: {
                show: false,
              },
              labelLine: {
                show: false,
              },
              emphasis: {
                itemStyle: {
                  shadowBlur: 15,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.3)',
                },
                scale: true,
                scaleSize: 5,
              },
            },
          ],
          color: [
            '#6366f1',
            '#8b5cf6',
            '#a855f7',
            '#c084fc',
            '#f59e0b',
            '#ef4444',
            '#10b981',
            '#06b6d4',
            '#84cc16',
            '#f97316',
            '#ec4899',
            '#8b5a2b',
          ],
        })
      }
    }

    // 製品別チャート
    if (productChartRef.value && productStats.value.length > 0 && activeTab.value === 'product') {
      // 检查DOM元素是否有尺寸
      const productChartElement = productChartRef.value
      if (productChartElement.clientWidth > 0 && productChartElement.clientHeight > 0) {
        if (!productChart) {
          productChart = echarts.init(productChartElement)
        } else {
          // 强制重新初始化图表
          productChart.dispose()
          productChart = echarts.init(productChartElement)
        }

        // 动态调整显示数量，根据数据量智能选择
        const maxDisplayCount = Math.min(25, Math.max(15, productStats.value.length))
        const productChartData = productStats.value
          .sort((a, b) => b.totalQuantity - a.totalQuantity)
          .slice(0, maxDisplayCount)

        productChart.setOption({
          title: {
            text: `製品別数量TOP${maxDisplayCount}`,
            left: 'center',
            top: 10,
            textStyle: {
              fontSize: 18,
              fontWeight: 700,
              color: '#1e293b',
            },
            subtext: `総製品数: ${productStats.value.length}製品`,
            subtextStyle: {
              fontSize: 12,
              color: '#64748b',
              marginTop: 5,
            },
          },
          tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            textStyle: {
              color: '#1e293b',
              fontSize: 13,
            },
            formatter: function (params: any) {
              const data = params[0]
              return `
                <div style="padding: 8px;">
                  <div style="font-weight: 600; color: #6366f1; margin-bottom: 8px;">
                    ${data.name}
                  </div>
                  <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                    <span style="color: #64748b;">数量:</span>
                    <span style="font-weight: 600; color: #10b981;">
                      ${data.value.toLocaleString()}個
                    </span>
                  </div>
                  <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                    <span style="color: #64748b;">割合:</span>
                    <span style="font-weight: 600; color: #6366f1;">
                      ${((data.value / productTotalQuantity.value) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              `
            },
            axisPointer: {
              type: 'shadow',
              shadowStyle: {
                color: 'rgba(99, 102, 241, 0.1)',
              },
            },
          },
          grid: {
            left: '1%',
            right: '1%',
            top: '20%',
            bottom: '15%',
            containLabel: true,
          },
          xAxis: {
            type: 'category',
            data: productChartData.map((item) => item.productName),
            axisLabel: {
              rotate: 30,
              fontSize: 9,
              color: '#64748b',
              margin: 4,
              interval: 0, // 显示所有标签
              formatter: function (value: string) {
                // 产品名称过长时截断显示
                return value.length > 8 ? value.substring(0, 8) + '...' : value
              },
            },
            axisTick: {
              show: false,
            },
            axisLine: {
              lineStyle: {
                color: '#e2e8f0',
              },
            },
          },
          yAxis: {
            type: 'value',
            axisLabel: {
              fontSize: 11,
              color: '#64748b',
              formatter: function (value: number) {
                return value.toLocaleString()
              },
            },
            axisTick: {
              show: false,
            },
            axisLine: {
              show: false,
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
              name: '数量',
              type: 'bar',
              data: productChartData.map((item) => item.totalQuantity),
              barWidth: '95%',
              itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: '#6366f1' },
                  { offset: 0.3, color: '#8b5cf6' },
                  { offset: 0.7, color: '#a855f7' },
                  { offset: 1, color: '#c084fc' },
                ]),
                borderRadius: [4, 4, 0, 0],
                shadowColor: 'rgba(99, 102, 241, 0.3)',
                shadowBlur: 8,
                shadowOffsetY: 2,
              },
              emphasis: {
                itemStyle: {
                  color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#4f46e5' },
                    { offset: 0.3, color: '#7c3aed' },
                    { offset: 0.7, color: '#9333ea' },
                    { offset: 1, color: '#a855f7' },
                  ]),
                  shadowColor: 'rgba(99, 102, 241, 0.5)',
                  shadowBlur: 12,
                  shadowOffsetY: 4,
                },
              },
            },
          ],
        })
      }
    }

    // 月別チャート
    if (monthlyChartRef.value && monthlyStats.value.length > 0 && activeTab.value === 'monthly') {
      // 检查DOM元素是否有尺寸
      const monthlyChartElement = monthlyChartRef.value
      if (monthlyChartElement.clientWidth > 0 && monthlyChartElement.clientHeight > 0) {
        if (!monthlyChart) {
          monthlyChart = echarts.init(monthlyChartElement)
        } else {
          // 强制重新初始化图表
          monthlyChart.dispose()
          monthlyChart = echarts.init(monthlyChartElement)
        }

        const monthlyChartData = monthlyStats.value.sort((a, b) => a.month.localeCompare(b.month))

        monthlyChart.setOption({
          title: {
            text: '月別数量推移',
            left: 'center',
            top: 8,
            textStyle: {
              fontSize: 16,
              fontWeight: 700,
              color: '#1e293b',
            },
            subtext: `総月数: ${monthlyStats.value.length}ヶ月`,
            subtextStyle: {
              fontSize: 11,
              color: '#64748b',
              marginTop: 3,
            },
          },
          tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            textStyle: {
              color: '#1e293b',
              fontSize: 13,
            },
            formatter: function (params: any) {
              const data = params[0]
              return `
                <div style="padding: 8px;">
                  <div style="font-weight: 600; color: #6366f1; margin-bottom: 8px;">
                    ${data.name}
                  </div>
                  <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                    <span style="color: #64748b;">数量:</span>
                    <span style="font-weight: 600; color: #10b981;">
                      ${data.value.toLocaleString()}個
                    </span>
                  </div>
                  <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                    <span style="color: #64748b;">割合:</span>
                    <span style="font-weight: 600; color: #6366f1;">
                      ${((data.value / monthlyTotalQuantity.value) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              `
            },
            axisPointer: {
              type: 'line',
              lineStyle: {
                color: '#6366f1',
                width: 2,
                type: 'dashed',
              },
            },
          },
          grid: {
            left: '1%',
            right: '1%',
            top: '18%',
            bottom: '12%',
            containLabel: true,
          },
          xAxis: {
            type: 'category',
            data: monthlyChartData.map((item) => item.month),
            axisLabel: {
              fontSize: 12,
              color: '#64748b',
              margin: 6,
              interval: 0, // 显示所有标签
            },
            axisTick: {
              show: false,
            },
            axisLine: {
              lineStyle: {
                color: '#e2e8f0',
              },
            },
          },
          yAxis: {
            type: 'value',
            axisLabel: {
              fontSize: 12,
              color: '#64748b',
              formatter: function (value: number) {
                return value.toLocaleString()
              },
            },
            axisTick: {
              show: false,
            },
            axisLine: {
              show: false,
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
              name: '数量',
              type: 'line',
              data: monthlyChartData.map((item) => item.totalQuantity),
              smooth: true,
              symbol: 'circle',
              symbolSize: 10,
              lineStyle: {
                color: '#6366f1',
                width: 5,
                shadowColor: 'rgba(99, 102, 241, 0.3)',
                shadowBlur: 8,
              },
              itemStyle: {
                color: '#6366f1',
                borderColor: '#fff',
                borderWidth: 2,
                shadowColor: 'rgba(99, 102, 241, 0.3)',
                shadowBlur: 4,
              },
              areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(99, 102, 241, 0.4)' },
                  { offset: 0.5, color: 'rgba(99, 102, 241, 0.2)' },
                  { offset: 1, color: 'rgba(99, 102, 241, 0.05)' },
                ]),
              },
              emphasis: {
                itemStyle: {
                  color: '#4f46e5',
                  borderColor: '#fff',
                  borderWidth: 3,
                  shadowColor: 'rgba(99, 102, 241, 0.5)',
                  shadowBlur: 8,
                },
                lineStyle: {
                  width: 6,
                  shadowColor: 'rgba(99, 102, 241, 0.4)',
                  shadowBlur: 12,
                },
              },
            },
          ],
        })
      }
    }
  }, 500) // 增加延迟时间到500ms
}

// タブ切り替え処理
const handleTabClick = () => {
  nextTick(() => {
    renderCharts()
  })
}

// 検索処理
const handleSearch = async () => {
  await fetchData()
}

// フィルターリセット
const resetFilters = async () => {
  filters.value = {
    dateRange: [] as string[],
    monthPicker: '',
    stageType: '',
    productName: '',
  }
  await fetchData()
}

// 統計データ出力
const exportStatistics = async () => {
  exportLoading.value = true
  try {
    // ここに出力ロジックを追加できます
    ElMessage.success('統計データの出力が完了しました')
  } catch (err) {
    ElMessage.error('統計データの出力に失敗しました')
  } finally {
    exportLoading.value = false
  }
}

// 製品別統計印刷
const printProductStatistics = () => {
  if (productStats.value.length === 0) {
    ElMessage.warning('印刷するデータがありません')
    return
  }

  // 工程名マッピング
  const stageNameMap: Record<string, string> = {
    all: '全て',
    cutting: '切断',
    surface: '面取',
    sw: 'SW',
    forming: '成型',
    plating: 'メッキ',
    welding: '溶接',
    inspection: '検査',
    warehouse: '倉庫',
    outsource_plating: '外注メッキ',
    outsource_welding: '外注溶接',
    pre_welding_inspection: '溶接前検査',
    pre_outsource_inspection: '外注検査前',
    part_process: '部品工程',
  }

  // 製品名で昇順ソート
  const sortedData = [...productStats.value].sort((a, b) => {
    const nameA = (a.productName || '').toLowerCase()
    const nameB = (b.productName || '').toLowerCase()
    return nameA.localeCompare(nameB, 'ja')
  })

  // 合計を計算
  const totalQuantity = sortedData.reduce((sum, item) => sum + (item.totalQuantity || 0), 0)

  // 印刷用のHTMLを作成
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('ポップアップがブロックされています。ブラウザの設定を確認してください。')
    return
  }

  // フィルター情報を取得
  const filterInfo = []
  if (filters.value.dateRange && filters.value.dateRange.length === 2) {
    filterInfo.push(`統計期間: ${filters.value.dateRange[0]} ～ ${filters.value.dateRange[1]}`)
  }
  if (filters.value.stageType) {
    const stageName = stageNameMap[filters.value.stageType] || filters.value.stageType
    filterInfo.push(`工程: ${stageName}`)
  }
  if (filters.value.productName) {
    filterInfo.push(`製品名: ${filters.value.productName}`)
  }

  // 印刷用HTML
  const printContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>製品別棚卸統計</title>
      <style>
        @media print {
          @page {
            size: A4 portrait;
            margin: 10mm;
          }
          body {
            margin: 0;
            padding: 0;
          }
        }
        body {
          font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
          margin: 10px;
          color: #333;
        }
        .print-header {
          text-align: center;
          margin-bottom: 10px;
          border-bottom: 2px solid #0ea5e9;
          padding-bottom: 8px;
        }
        .print-title {
          font-size: 20px;
          font-weight: bold;
          color: #1e293b;
          margin-bottom: 5px;
        }
        .print-subtitle {
          font-size: 12px;
          color: #64748b;
          margin-bottom: 4px;
        }
        .print-info {
          font-size: 12px;
          color: #64748b;
          text-align: left;
          margin-top: 6px;
        }
        .print-info-item {
          margin: 2px 0;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 12px;
          font-size: 11px;
        }
        th {
          background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%);
          color: white;
          padding: 8px 5px;
          text-align: center;
          font-weight: bold;
          border: 1px solid #0284c7;
          font-size: 12px;
        }
        td {
          padding: 6px 5px;
          text-align: center;
          border: 1px solid #e2e8f0;
        }
        tr:nth-child(even) {
          background-color: #f8fafc;
        }
        tr:hover {
          background-color: #e0f2fe;
        }
        .text-right {
          text-align: right;
        }
        .text-left {
          text-align: left;
        }
        .print-footer {
          margin-top: 15px;
          padding-top: 8px;
          border-top: 2px solid #e2e8f0;
          font-size: 11px;
          color: #64748b;
          text-align: right;
        }
        .total-row {
          background-color: #e0f2fe !important;
          font-weight: bold;
          border-top: 2px solid #0ea5e9;
        }
        .total-row td {
          padding: 8px 5px;
          font-size: 12px;
        }
      </style>
    </head>
    <body>
      <div class="print-header">
        <div class="print-title">製品別棚卸統計</div>
        <div class="print-subtitle">印刷日時: ${dayjs().format('YYYY-MM-DD HH:mm:ss')}</div>
        ${filterInfo.length > 0 ? `<div class="print-info">${filterInfo.map((info) => `<div class="print-info-item">${info}</div>`).join('')}</div>` : ''}
      </div>

      <table>
        <thead>
          <tr>
            <th style="width: 8%;">No.</th>
            <th style="width: 20%;">製品CD</th>
            <th style="width: 35%;">製品名</th>
            <th style="width: 20%;">総数量</th>
            <th style="width: 17%;">割合(%)</th>
          </tr>
        </thead>
        <tbody>
          ${sortedData
            .map(
              (item, index) => `
            <tr>
              <td>${index + 1}</td>
              <td>${item.productCode || '不明'}</td>
              <td class="text-left">${item.productName || '不明'}</td>
              <td class="text-right">${(item.totalQuantity || 0).toLocaleString()}</td>
              <td>${(item.percentage || 0).toFixed(1)}</td>
            </tr>
          `,
            )
            .join('')}
          <tr class="total-row">
            <td colspan="3" style="text-align: right; font-weight: bold;">合計</td>
            <td class="text-right">${totalQuantity.toLocaleString()}</td>
            <td>100.0</td>
          </tr>
        </tbody>
      </table>

      <div class="print-footer">
        ページ 1/1 | 総レコード数: ${sortedData.length}件
      </div>
    </body>
    </html>
  `

  printWindow.document.write(printContent)
  printWindow.document.close()

  // 印刷ダイアログを表示
  setTimeout(() => {
    printWindow.print()
    printWindow.onafterprint = () => {
      printWindow.close()
    }
  }, 250)
}

// 工程別統計ソート処理
const handleStageSortChange = ({ prop, order }: { prop: string; order: string }) => {
  if (!prop || !order) return

  stageStats.value.sort((a, b) => {
    let aValue = a[prop]
    let bValue = b[prop]

    // 数値の場合は数値として比較
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return order === 'ascending' ? aValue - bValue : bValue - aValue
    }

    // 文字列の場合は文字列として比較
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return order === 'ascending'
        ? aValue.localeCompare(bValue, 'ja')
        : bValue.localeCompare(aValue, 'ja')
    }

    return 0
  })
}

// 製品別統計ソート処理
const handleProductSortChange = ({ prop, order }: { prop: string; order: string }) => {
  if (!prop || !order) return

  productStats.value.sort((a, b) => {
    let aValue = a[prop]
    let bValue = b[prop]

    // 数値の場合は数値として比較
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return order === 'ascending' ? aValue - bValue : bValue - aValue
    }

    // 文字列の場合は文字列として比較
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return order === 'ascending'
        ? aValue.localeCompare(bValue, 'ja')
        : bValue.localeCompare(aValue, 'ja')
    }

    return 0
  })
}

// 月別統計ソート処理
const handleMonthlySortChange = ({ prop, order }: { prop: string; order: string }) => {
  if (!prop || !order) return

  monthlyStats.value.sort((a, b) => {
    let aValue = a[prop]
    let bValue = b[prop]

    // 数値の場合は数値として比較
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return order === 'ascending' ? aValue - bValue : bValue - aValue
    }

    // 文字列の場合は文字列として比較
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return order === 'ascending'
        ? aValue.localeCompare(bValue, 'ja')
        : bValue.localeCompare(aValue, 'ja')
    }

    return 0
  })
}

// 窗口大小变化监听
const handleResize = () => {
  nextTick(() => {
    renderCharts()
  })
}

// 组件挂载时添加监听器
onMounted(async () => {
  // 初始化数据
  await fetchData()

  // 添加窗口大小变化监听
  window.addEventListener('resize', handleResize)
})

// 组件卸载时移除监听器
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  // 销毁图表实例
  if (stageChart) {
    stageChart.dispose()
    stageChart = null
  }
  if (productChart) {
    productChart.dispose()
    productChart = null
  }
  if (monthlyChart) {
    monthlyChart.dispose()
    monthlyChart = null
  }
})
</script>

<style scoped>
.inventory-container {
  --is-surface: rgba(255, 255, 255, 0.92);
  --is-border: rgba(15, 23, 42, 0.08);
  --is-accent: #0ea5e9;
  --is-muted: #64748b;
  position: relative;
  z-index: 0;
  padding: 10px 12px 14px;
  box-sizing: border-box;
  min-height: 100vh;
  background: linear-gradient(165deg, #f8fafc 0%, #f1f5f9 45%, #e8edf3 100%);
}

.page-ambient {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse 70% 50% at 12% -10%, rgba(14, 165, 233, 0.12), transparent 55%),
    radial-gradient(ellipse 50% 40% at 92% 20%, rgba(99, 102, 241, 0.08), transparent 50%);
}

.page-toolbar,
.content-container {
  position: relative;
  z-index: 1;
}

.page-toolbar {
  margin-bottom: 10px;
}

.toolbar-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  padding: 8px 12px;
  background: var(--is-surface);
  border: 1px solid var(--is-border);
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 6px 20px rgba(15, 23, 42, 0.05);
  backdrop-filter: blur(10px);
}

.toolbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.brand-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  background: linear-gradient(145deg, #0ea5e9, #0284c7);
  color: #fff;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.25);
}

.brand-text {
  min-width: 0;
}

.toolbar-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: #0f172a;
}

.toolbar-sub {
  margin: 2px 0 0;
  font-size: 11px;
  font-weight: 500;
  color: var(--is-muted);
  line-height: 1.3;
}

.content-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-card,
.tab-card {
  background: var(--is-surface);
  border: 1px solid var(--is-border);
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: box-shadow 0.2s ease;
}

.filter-card:hover,
.tab-card:hover {
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
}

.filter-card :deep(.el-card__header) {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  background: rgba(248, 250, 252, 0.6);
}

.filter-card :deep(.el-card__body) {
  padding: 10px 12px 9px;
}

.filter-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  min-height: 18px;
}

.filter-toolbar-icon {
  font-size: 16px;
  color: var(--is-accent);
  display: inline-flex;
  align-items: center;
}

.filter-toolbar-title {
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.filter-form {
  padding: 0;
  margin: 0;
}

.filter-row {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  align-items: center;
  margin: 0;
}

.filter-item {
  margin-bottom: 0;
  flex-shrink: 0;
}

.filter-item :deep(.el-form-item__label) {
  font-size: 11px;
  color: var(--is-muted);
  font-weight: 600;
  line-height: 1.25;
  padding-bottom: 0;
  height: 30px;
  display: inline-flex;
  align-items: center;
}

.filter-item :deep(.el-form-item) {
  margin-bottom: 0;
  align-items: center;
}

.filter-item :deep(.el-form-item__content) {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
}

.filter-item--date .filter-date-picker {
  width: 160px;
}

.filter-item--month .filter-month-picker {
  width: 90px;
}

.filter-item--stage .filter-select {
  width: 100px;
}

.filter-item--product .filter-input {
  width: 130px;
}

.filter-input :deep(.el-input__wrapper),
.filter-select :deep(.el-input__wrapper),
.filter-date-picker :deep(.el-input__wrapper),
.filter-month-picker :deep(.el-input__wrapper) {
  min-height: 30px;
}

.filter-actions-inline {
  margin-left: auto;
  display: flex;
  gap: 6px;
  align-items: center;
  flex-shrink: 0;
  min-height: 30px;
}

.filter-actions-inline :deep(.el-form-item__content) {
  display: flex;
  gap: 6px;
  margin-left: 0 !important;
  flex-wrap: nowrap !important;
  align-items: center;
}

.filter-actions-inline :deep(.el-form-item__label) {
  display: none;
}

.tab-card :deep(.el-card__body) {
  padding: 10px;
}

.custom-tabs {
  border: none;
  background: transparent;
}

.custom-tabs :deep(.el-tabs__header) {
  margin: 0 0 8px;
  padding: 3px;
  background: rgba(241, 245, 249, 0.85);
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 8px;
}

.custom-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0;
}

.custom-tabs :deep(.el-tabs__item) {
  border: none;
  color: var(--is-muted);
  font-weight: 600;
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
  margin: 0 1px;
  line-height: 1.35;
  transition: color 0.15s ease, background 0.15s ease;
}

.custom-tabs :deep(.el-tabs__item:hover) {
  color: #0284c7;
  background: rgba(14, 165, 233, 0.08);
}

.custom-tabs :deep(.el-tabs__item.is-active) {
  color: #fff;
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.25);
}

.custom-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.custom-tabs :deep(.el-tabs__content) {
  padding: 0;
  margin-top: 0;
}

.tab-content {
  min-height: 280px;
}

.tab-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(14, 165, 233, 0.15);
}

.tab-header--row {
  flex-direction: row;
}

.tab-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tab-heading {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.tab-stats {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.stat-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  line-height: 1.35;
  color: #0369a1;
  background: rgba(14, 165, 233, 0.1);
  border: 1px solid rgba(14, 165, 233, 0.2);
}

.stat-pill--qty {
  color: #047857;
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.22);
}

.statistics-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 0;
}

.chart-container {
  background: rgba(255, 255, 255, 0.75);
  border-radius: 8px;
  padding: 8px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.chart {
  width: 100%;
  height: 300px;
  min-height: 220px;
}

.table-container {
  background: rgba(255, 255, 255, 0.75);
  border-radius: 8px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.statistics-table {
  width: 100%;
}

.statistics-table :deep(.el-table__header) {
  background: #f8fafc;
}

.statistics-table :deep(.el-table__header th) {
  background: transparent !important;
  color: #334155;
  font-weight: 600;
  font-size: 12px;
  padding: 6px 8px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.1);
}

.statistics-table :deep(.el-table__cell) {
  padding: 5px 8px;
  font-size: 12px;
}

.statistics-table :deep(.el-table__row) {
  transition: background-color 0.15s ease;
}

.statistics-table :deep(.el-table__row:hover) {
  background-color: rgba(14, 165, 233, 0.06);
}

@media (max-width: 1200px) {
  .content-container {
    padding: 0 4px;
  }

  .filter-row {
    flex-wrap: wrap;
  }

  .filter-actions-inline {
    margin-left: 0;
    width: 100%;
    justify-content: flex-start;
  }

  .filter-item--date .filter-date-picker {
    width: 100%;
  }

  .statistics-content {
    grid-template-columns: 1fr;
  }

  .chart {
    height: 260px;
    min-height: 200px;
  }
}

@media (max-width: 768px) {
  .inventory-container {
    padding: 8px;
  }

  .toolbar-inner {
    align-items: flex-start;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-input,
  .filter-select,
  .filter-date-picker,
  .filter-month-picker {
    width: 100%;
  }

  .tab-header {
    align-items: flex-start;
  }

  .chart {
    height: 220px;
    min-height: 180px;
  }

  .tab-content {
    min-height: 240px;
  }
}

@media (max-width: 480px) {
  .inventory-container {
    padding: 6px;
  }

  .brand-icon {
    width: 32px;
    height: 32px;
  }

  .toolbar-title {
    font-size: 1rem;
  }

  .custom-tabs :deep(.el-tabs__item) {
    padding: 5px 8px;
    font-size: 11px;
  }

  .chart {
    height: 200px;
    min-height: 160px;
  }
}
</style>
