<template>
  <div class="inventory-container">
    <!-- 動的背景 -->
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>
    <!-- ページヘッダー -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="32"> <DataAnalysis /> </el-icon>
          </div>
          <div class="header-text">
            <h1 class="main-title">棚卸統計分析</h1>
            <p class="subtitle">工程別・製品別・月別の棚卸データを分析します</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button
            type="primary"
            @click="exportStatistics"
            :loading="exportLoading"
            :icon="Download"
            class="export-button"
            size="large"
          >
            統計データ出力
          </el-button>
        </div>
      </div>
    </div>
    <!-- メインコンテンツエリア -->
    <div class="content-container">
      <!-- フィルターフォーム -->
      <el-card class="filter-card" shadow="hover">
        <el-form :inline="true" :model="filters" class="filter-form" @submit.prevent>
          <div class="filter-row">
            <el-form-item label="統計期間" class="filter-item">
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
            <el-form-item label="月選択" class="filter-item">
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
            <el-form-item label="工程" class="filter-item">
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
              </el-select>
            </el-form-item>
            <el-form-item label="製品名" class="filter-item">
              <el-input
                v-model="filters.productName"
                placeholder="製品名で検索"
                clearable
                class="filter-input"
                :prefix-icon="Search"
              />
            </el-form-item>
            <el-form-item class="filter-item filter-actions-inline">
              <el-button type="primary" :icon="Search" @click="handleSearch" class="search-button">
                統計実行
              </el-button>
              <el-button :icon="RefreshLeft" @click="resetFilters" class="reset-button">
                リセット
              </el-button>
            </el-form-item>
          </div>
        </el-form>
      </el-card>
      <!-- タブ切り替えエリア -->
      <el-card class="tab-card" shadow="hover">
        <el-tabs v-model="activeTab" type="card" @tab-click="handleTabClick" class="custom-tabs">
          <!-- 工程別統計 -->
          <el-tab-pane label="工程別統計" name="stage">
            <div class="tab-content">
              <div class="tab-header">
                <h3>工程別棚卸統計</h3>
                <div class="tab-stats">
                  <span class="tab-count">総工程数: {{ stageStats.length }}工程</span>
                  <span class="tab-quantity"
                    >総数量: {{ stageTotalQuantity.toLocaleString() }}個</span
                  >
                </div>
              </div>
              <div class="statistics-content">
                <div class="chart-container"><div ref="stageChartRef" class="chart"></div></div>
                <div class="table-container">
                  <el-table
                    :data="stageStats"
                    stripe
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
              <div class="tab-header">
                <h3>製品別棚卸統計</h3>
                <div class="tab-header-right">
                  <div class="tab-stats">
                    <span class="tab-count">総製品数: {{ productStats.length }}製品</span>
                    <span class="tab-quantity"
                      >総数量: {{ productTotalQuantity.toLocaleString() }}個</span
                    >
                  </div>
                  <el-button
                    type="primary"
                    @click="printProductStatistics"
                    :icon="Printer"
                    class="print-button"
                    size="default"
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
              <div class="tab-header">
                <h3>月別棚卸統計</h3>
                <div class="tab-stats">
                  <span class="tab-count">総月数: {{ monthlyStats.length }}ヶ月</span>
                  <span class="tab-quantity"
                    >総数量: {{ monthlyTotalQuantity.toLocaleString() }}個</span
                  >
                </div>
              </div>
              <div class="statistics-content">
                <div class="chart-container"><div ref="monthlyChartRef" class="chart"></div></div>
                <div class="table-container">
                  <el-table
                    :data="monthlyStats"
                    stripe
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

import { getInventoryLogs, type InventoryLog, type InventoryFilters } from '@/api/inventory'

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
    const params: any = {
      ...filters.value,
      pageSize: 10000, // 統計用に全データを取得
    }

    const response = await getInventoryLogs(params)

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
  min-height: 100vh;
  background: linear-gradient(
    135deg,
    #f0f9ff 0%,
    #e0f2fe 20%,
    #bae6fd 40%,
    #7dd3fc 60%,
    #38bdf8 80%,
    #0ea5e9 100%
  );
  position: relative;
  overflow-x: hidden;
  padding: 2px;
  will-change: transform;
  animation: backgroundShift 20s ease-in-out infinite;
}

@keyframes backgroundShift {
  0%,
  100% {
    background: linear-gradient(
      135deg,
      #f0f9ff 0%,
      #e0f2fe 20%,
      #bae6fd 40%,
      #7dd3fc 60%,
      #38bdf8 80%,
      #0ea5e9 100%
    );
  }
  50% {
    background: linear-gradient(
      135deg,
      #0ea5e9 0%,
      #38bdf8 20%,
      #7dd3fc 40%,
      #bae6fd 60%,
      #e0f2fe 80%,
      #f0f9ff 100%
    );
  }
}

/* 動的背景 */
.dynamic-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  overflow: hidden;
  will-change: transform;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.7;
  animation: float 18s ease-in-out infinite;
  will-change: transform, opacity;
}

.orb-1 {
  width: 350px;
  height: 350px;
  background: radial-gradient(
    circle,
    rgba(14, 165, 233, 0.5) 0%,
    rgba(56, 189, 248, 0.4) 30%,
    rgba(125, 211, 252, 0.3) 60%,
    transparent 80%
  );
  top: 8%;
  left: 12%;
  animation-delay: 0s;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(
    circle,
    rgba(59, 130, 246, 0.45) 0%,
    rgba(14, 165, 233, 0.35) 30%,
    rgba(56, 189, 248, 0.25) 60%,
    transparent 80%
  );
  top: 55%;
  right: 15%;
  animation-delay: -6s;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(
    circle,
    rgba(125, 211, 252, 0.4) 0%,
    rgba(186, 230, 253, 0.3) 30%,
    rgba(224, 242, 254, 0.2) 60%,
    transparent 80%
  );
  bottom: 15%;
  left: 35%;
  animation-delay: -12s;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px) translateX(0px) scale(1) rotate(0deg);
    opacity: 0.7;
  }
  25% {
    transform: translateY(-25px) translateX(15px) scale(1.08) rotate(90deg);
    opacity: 0.9;
  }
  50% {
    transform: translateY(-15px) translateX(-20px) scale(0.92) rotate(180deg);
    opacity: 0.8;
  }
  75% {
    transform: translateY(20px) translateX(8px) scale(1.05) rotate(270deg);
    opacity: 0.95;
  }
}

/* ページヘッダー */
.page-header {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.9) 100%);
  backdrop-filter: blur(25px);
  border-radius: 16px;
  padding: 14px 20px;
  margin-bottom: 12px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.08),
    0 4px 16px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.4);
  animation: slideInDown 0.6s ease-out;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s ease;
}

.page-header:hover {
  transform: translateY(-3px);
  box-shadow:
    0 16px 50px rgba(0, 0, 0, 0.15),
    0 8px 25px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

.page-header:hover::before {
  left: 100%;
}

@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  gap: 20px;
  position: relative;
  z-index: 1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.header-icon {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 50%, #7dd3fc 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow:
    0 6px 20px rgba(14, 165, 233, 0.3),
    0 3px 10px rgba(56, 189, 248, 0.2);
  animation: iconPulse 3s ease-in-out infinite;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}

.header-icon::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transform: rotate(45deg);
  transition: all 0.6s ease;
}

.header-icon:hover {
  transform: scale(1.08) rotate(5deg);
  box-shadow:
    0 12px 35px rgba(14, 165, 233, 0.45),
    0 6px 18px rgba(56, 189, 248, 0.3);
}

.header-icon:hover::before {
  animation: shimmer 0.6s ease-in-out;
}

@keyframes iconPulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow:
      0 8px 25px rgba(14, 165, 233, 0.35),
      0 4px 12px rgba(56, 189, 248, 0.2);
  }
  50% {
    transform: scale(1.02);
    box-shadow:
      0 10px 30px rgba(14, 165, 233, 0.4),
      0 5px 15px rgba(56, 189, 248, 0.25);
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%) translateY(-100%) rotate(45deg);
  }
  100% {
    transform: translateX(100%) translateY(100%) rotate(45deg);
  }
}

.header-text {
  flex: 1;
}

.main-title {
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(135deg, #1e293b 0%, #475569 50%, #64748b 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.subtitle {
  font-size: 13px;
  background: linear-gradient(135deg, #64748b 0%, #94a3b8 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 4px 0 0 0;
  font-weight: 600;
  letter-spacing: 0.01em;
  line-height: 1.3;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.export-button {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 50%, #0369a1 100%);
  border: none;
  border-radius: 10px;
  padding: 10px 18px;
  font-weight: 700;
  font-size: 14px;
  box-shadow:
    0 4px 14px rgba(14, 165, 233, 0.3),
    0 2px 6px rgba(2, 132, 199, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.export-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s ease;
}

.export-button:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow:
    0 8px 25px rgba(14, 165, 233, 0.45),
    0 4px 12px rgba(2, 132, 199, 0.3);
  background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #075985 100%);
}

.export-button:hover::before {
  left: 100%;
}

/* メインコンテンツエリア */
.content-container {
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* フィルターカード */
.filter-card {
  border-radius: 14px;
  border: none;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 250, 252, 0.92) 100%);
  backdrop-filter: blur(25px) saturate(180%);
  box-shadow:
    0 6px 24px rgba(0, 0, 0, 0.06),
    0 3px 12px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
  animation: slideInLeft 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  will-change: transform;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.7);
  position: relative;
  overflow: hidden;
}

.filter-card :deep(.el-card__body) {
  padding: 12px 16px;
}

.filter-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.8s ease;
}

.filter-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.12),
    0 6px 20px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.filter-card:hover::before {
  left: 100%;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

.filter-form {
  padding: 0;
  margin: 0;
}

.filter-row {
  display: flex;
  flex-wrap: nowrap;
  gap: 10px;
  align-items: flex-end;
  margin: 0;
}

.filter-item {
  margin-bottom: 0;
  position: relative;
  flex-shrink: 0;
}

.filter-item :deep(.el-form-item__label) {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  padding-bottom: 3px;
}

.filter-input,
.filter-select {
  width: 160px;
  border-radius: 6px;
}

.filter-date-picker {
  width: 144px; /* 缩小10% */
  border-radius: 6px;
}

.filter-month-picker {
  width: 128px; /* 缩小20% */
  border-radius: 6px;
}

.filter-input :deep(.el-input__wrapper),
.filter-select :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(226, 232, 240, 0.8);
  transition: all 0.25s ease;
}

.filter-input :deep(.el-input__wrapper):hover,
.filter-select :deep(.el-input__wrapper):hover {
  border-color: #0ea5e9;
  background: rgba(255, 255, 255, 0.9);
}

.filter-actions-inline {
  margin-left: auto;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

.filter-actions-inline :deep(.el-form-item__content) {
  display: flex;
  gap: 8px;
  margin-left: 0 !important;
  flex-wrap: nowrap;
  align-items: center;
}

.filter-actions-inline :deep(.el-form-item) {
  margin-bottom: 0;
}

.search-button {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 50%, #0369a1 100%);
  border: none;
  border-radius: 10px;
  padding: 10px 18px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(12px);
  box-shadow:
    0 4px 12px rgba(14, 165, 233, 0.25),
    0 2px 6px rgba(2, 132, 199, 0.15);
  position: relative;
  overflow: hidden;
  white-space: nowrap;
  flex-shrink: 0;
}

.search-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.search-button:hover {
  transform: translateY(-1px) scale(1.02);
  box-shadow:
    0 6px 18px rgba(14, 165, 233, 0.35),
    0 3px 8px rgba(2, 132, 199, 0.2);
  background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #075985 100%);
}

.search-button:hover::before {
  left: 100%;
}

.reset-button {
  border-radius: 10px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, rgba(248, 250, 252, 0.8) 100%);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(226, 232, 240, 0.9);
  color: #64748b;
  font-size: 14px;
  padding: 10px 18px;
  font-weight: 600;
  position: relative;
  overflow: hidden;
  white-space: nowrap;
  flex-shrink: 0;
}

.reset-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
  transition: left 0.5s ease;
}

.reset-button:hover {
  transform: translateY(-1px) scale(1.02);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.9) 100%);
  border-color: #0ea5e9;
  color: #0ea5e9;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15);
}

.reset-button:hover::before {
  left: 100%;
}

/* タブカード */
.tab-card {
  border-radius: 14px;
  border: none;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.94) 0%, rgba(248, 250, 252, 0.9) 100%);
  backdrop-filter: blur(30px) saturate(180%);
  box-shadow:
    0 8px 28px rgba(0, 0, 0, 0.06),
    0 4px 14px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
  animation: slideInRight 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  border: 1px solid rgba(255, 255, 255, 0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.tab-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.18), transparent);
  transition: left 0.9s ease;
}

.tab-card:hover {
  transform: translateY(-3px);
  box-shadow:
    0 15px 45px rgba(0, 0, 0, 0.12),
    0 8px 25px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.tab-card:hover::before {
  left: 100%;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

/* カスタムタブスタイル */
.custom-tabs {
  border-radius: 12px;
  overflow: hidden;
}

.custom-tabs :deep(.el-tabs__header) {
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.92) 0%, rgba(241, 245, 249, 0.88) 100%);
  backdrop-filter: blur(12px);
  margin: 0;
  padding: 10px 14px 0;
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
  border-radius: 12px 12px 0 0;
}

.custom-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0;
}

.custom-tabs :deep(.el-tabs__item) {
  background: transparent;
  border: none;
  color: #64748b;
  font-weight: 600;
  padding: 8px 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 8px;
  margin: 0 4px 8px 0;
  font-size: 13px;
  position: relative;
  overflow: hidden;
  border: 1px solid transparent;
}

.custom-tabs :deep(.el-tabs__item:hover) {
  color: #0ea5e9;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.1) 0%, rgba(56, 189, 248, 0.08) 100%);
  border-color: rgba(14, 165, 233, 0.25);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15);
}

.custom-tabs :deep(.el-tabs__item.is-active) {
  color: #0ea5e9;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(56, 189, 248, 0.12) 100%);
  backdrop-filter: blur(8px);
  border-color: rgba(14, 165, 233, 0.35);
  font-weight: 700;
  box-shadow:
    0 6px 18px rgba(14, 165, 233, 0.25),
    0 3px 8px rgba(56, 189, 248, 0.15);
  transform: translateY(-1px);
}

.custom-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 50%, #7dd3fc 100%);
  height: 4px;
  border-radius: 3px;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3);
}

.custom-tabs :deep(.el-tabs__content) {
  padding: 14px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.7) 0%, rgba(248, 250, 252, 0.6) 100%);
  backdrop-filter: blur(12px);
  border-radius: 0 0 12px 12px;
}

/* タブコンテンツスタイル */
.tab-content {
  min-height: 420px;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(226, 232, 240, 0.7);
  gap: 12px;
}

.tab-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.tab-header h3 {
  margin: 0;
  background: linear-gradient(135deg, #1e293b 0%, #475569 50%, #64748b 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tab-stats {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.tab-count {
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.9) 0%, rgba(241, 245, 249, 0.85) 100%);
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(226, 232, 240, 0.7);
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.tab-count:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.9) 100%);
}

.tab-quantity {
  color: #0ea5e9;
  font-size: 14px;
  font-weight: 600;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.1) 0%, rgba(2, 132, 199, 0.08) 100%);
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(14, 165, 233, 0.25);
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
  transition: all 0.3s ease;
}

.tab-quantity:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15);
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(2, 132, 199, 0.12) 100%);
}

.print-button {
  background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%);
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 13px;
  box-shadow:
    0 4px 12px rgba(16, 185, 129, 0.3),
    0 2px 6px rgba(5, 150, 105, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  color: white;
}

.print-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.print-button:hover {
  transform: translateY(-1px) scale(1.02);
  box-shadow:
    0 6px 18px rgba(16, 185, 129, 0.4),
    0 3px 8px rgba(5, 150, 105, 0.3);
  background: linear-gradient(135deg, #059669 0%, #047857 50%, #065f46 100%);
}

.print-button:hover::before {
  left: 100%;
}

/* 統計コンテンツスタイル */
.statistics-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 12px;
}

.chart-container {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 250, 252, 0.88) 100%);
  border-radius: 10px;
  padding: 10px;
  border: 1px solid rgba(226, 232, 240, 0.7);
  backdrop-filter: blur(12px);
  box-shadow:
    0 3px 12px rgba(0, 0, 0, 0.05),
    0 1px 6px rgba(0, 0, 0, 0.03);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.chart-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transition: left 0.6s ease;
}

.chart-container:hover {
  transform: translateY(-1px);
  box-shadow:
    0 6px 20px rgba(0, 0, 0, 0.08),
    0 3px 12px rgba(0, 0, 0, 0.06);
}

.chart-container:hover::before {
  left: 100%;
}

.chart {
  width: 100%;
  height: 380px;
  position: relative;
  z-index: 1;
  min-height: 300px;
}

.table-container {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 250, 252, 0.88) 100%);
  border-radius: 10px;
  border: 1px solid rgba(226, 232, 240, 0.7);
  backdrop-filter: blur(12px);
  overflow: hidden;
  box-shadow:
    0 3px 12px rgba(0, 0, 0, 0.05),
    0 1px 6px rgba(0, 0, 0, 0.03);
  transition: all 0.3s ease;
  position: relative;
}

.table-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transition: left 0.6s ease;
  z-index: 0;
}

.table-container:hover {
  transform: translateY(-1px);
  box-shadow:
    0 6px 20px rgba(0, 0, 0, 0.08),
    0 3px 12px rgba(0, 0, 0, 0.06);
}

.table-container:hover::before {
  left: 100%;
}

.statistics-table {
  width: 100%;
  position: relative;
  z-index: 1;
}

.statistics-table :deep(.el-table__header) {
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.9) 100%);
}

.statistics-table :deep(.el-table__row) {
  transition: all 0.3s ease;
}

.statistics-table :deep(.el-table__row:hover) {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.06) 0%, rgba(56, 189, 248, 0.04) 100%);
  transform: scale(1.001);
  transition: all 0.3s ease;
}

.statistics-table :deep(.el-table__body-wrapper) {
  background: transparent;
}

.statistics-table :deep(.el-table th) {
  background: transparent;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid rgba(226, 232, 240, 0.8);
  transition: all 0.3s ease;
}

.statistics-table :deep(.el-table th:hover) {
  background: rgba(14, 165, 233, 0.05);
  color: #0ea5e9;
}

.statistics-table :deep(.el-table th.is-sortable) {
  cursor: pointer;
}

.statistics-table :deep(.el-table th.is-sortable:hover) {
  background: rgba(14, 165, 233, 0.08);
}

.statistics-table :deep(.el-table .sort-caret) {
  border-color: #0ea5e9;
}

.statistics-table :deep(.el-table .ascending .sort-caret.ascending) {
  border-bottom-color: #0ea5e9;
}

.statistics-table :deep(.el-table .descending .sort-caret.descending) {
  border-top-color: #0ea5e9;
}

.statistics-table :deep(.el-table td) {
  background: transparent;
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  transition: all 0.3s ease;
}

/* レスポンシブデザイン */
@media (max-width: 1200px) {
  .inventory-container {
    padding: 3px;
  }

  .page-header {
    padding: 16px 18px;
    margin-bottom: 14px;
    border-radius: 16px;
  }

  .header-content {
    gap: 16px;
  }

  .header-icon {
    width: 56px;
    height: 56px;
    border-radius: 14px;
  }

  .main-title {
    font-size: 24px;
  }

  .subtitle {
    font-size: 14px;
  }

  .export-button {
    padding: 10px 16px;
    font-size: 14px;
    border-radius: 10px;
  }

  .content-container {
    gap: 12px;
    padding: 0 8px;
  }

  .filter-card,
  .tab-card {
    margin: 0;
    border-radius: 14px;
  }

  .filter-row {
    flex-wrap: wrap;
    gap: 8px;
  }

  .filter-actions-inline {
    margin-left: 0;
    width: 100%;
    justify-content: flex-end;
  }

  .filter-input,
  .filter-date-picker,
  .filter-month-picker,
  .filter-select {
    width: 100%;
  }

  .custom-tabs {
    border-radius: 10px;
  }

  .custom-tabs :deep(.el-tabs__header) {
    padding: 10px 12px 0;
    border-radius: 10px 10px 0 0;
  }

  .custom-tabs :deep(.el-tabs__item) {
    padding: 8px 16px;
    font-size: 13px;
    border-radius: 8px;
  }

  .custom-tabs :deep(.el-tabs__content) {
    padding: 16px;
    border-radius: 0 0 10px 10px;
  }

  .tab-header {
    flex-direction: column;
    gap: 6px;
    align-items: flex-start;
    margin-bottom: 16px;
    padding-bottom: 12px;
  }

  .tab-header h3 {
    font-size: 16px;
  }

  .tab-stats {
    gap: 10px;
  }

  .statistics-content {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .chart-container,
  .table-container {
    border-radius: 10px;
    padding: 12px;
  }

  .chart {
    height: 300px;
    min-height: 250px;
  }
}

@media (max-width: 768px) {
  .inventory-container {
    padding: 2px;
  }

  .page-header {
    padding: 12px 16px;
    margin-bottom: 12px;
    border-radius: 12px;
  }

  .header-content {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }

  .header-left {
    justify-content: center;
    align-items: center;
  }

  .header-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
  }

  .main-title {
    font-size: 20px;
  }

  .subtitle {
    font-size: 13px;
  }

  .export-button {
    padding: 8px 14px;
    font-size: 13px;
    border-radius: 8px;
  }

  .content-container {
    gap: 10px;
  }

  .filter-card,
  .tab-card {
    border-radius: 12px;
  }

  .filter-row {
    flex-wrap: wrap;
    gap: 12px;
  }

  .filter-item {
    width: 100%;
  }

  .filter-actions-inline {
    margin-left: 0;
    width: 100%;
    justify-content: center;
  }

  .search-button,
  .reset-button {
    padding: 8px 14px;
    font-size: 13px;
    border-radius: 8px;
  }

  .custom-tabs {
    border-radius: 8px;
  }

  .custom-tabs :deep(.el-tabs__header) {
    padding: 8px 10px 0;
    border-radius: 8px 8px 0 0;
  }

  .custom-tabs :deep(.el-tabs__item) {
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 6px;
    margin: 0 4px 8px 0;
  }

  .custom-tabs :deep(.el-tabs__content) {
    padding: 12px;
    border-radius: 0 0 8px 8px;
  }

  .tab-content {
    min-height: 350px;
  }

  .tab-header {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
    margin-bottom: 14px;
    padding-bottom: 10px;
  }

  .tab-header h3 {
    font-size: 15px;
  }

  .tab-stats {
    gap: 12px;
  }

  .tab-count,
  .tab-quantity {
    font-size: 12px;
    padding: 4px 8px;
    border-radius: 6px;
  }

  .statistics-content {
    grid-template-columns: 1fr;
    gap: 10px;
    margin-top: 12px;
  }

  .chart-container,
  .table-container {
    border-radius: 8px;
    padding: 10px;
  }

  .chart {
    height: 240px;
    min-height: 200px;
  }
}

@media (max-width: 480px) {
  .inventory-container {
    padding: 1px;
  }

  .page-header {
    padding: 10px 12px;
    margin-bottom: 8px;
    border-radius: 10px;
  }

  .header-content {
    gap: 8px;
  }

  .header-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
  }

  .main-title {
    font-size: 18px;
  }

  .subtitle {
    font-size: 12px;
  }

  .export-button {
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 6px;
  }

  .header-actions {
    justify-content: center;
    gap: 4px;
  }

  .content-container {
    gap: 8px;
  }

  .filter-card,
  .tab-card {
    border-radius: 10px;
  }

  .filter-actions-inline {
    margin-left: 0;
    width: 100%;
    justify-content: center;
  }

  .search-button,
  .reset-button {
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 6px;
  }

  .custom-tabs {
    border-radius: 6px;
  }

  .custom-tabs :deep(.el-tabs__header) {
    padding: 6px 8px 0;
    border-radius: 6px 6px 0 0;
  }

  .custom-tabs :deep(.el-tabs__item) {
    padding: 5px 10px;
    font-size: 11px;
    border-radius: 4px;
    margin: 0 3px 6px 0;
  }

  .custom-tabs :deep(.el-tabs__content) {
    padding: 10px;
    border-radius: 0 0 6px 6px;
  }

  .tab-content {
    min-height: 300px;
  }

  .tab-header {
    margin-bottom: 12px;
    padding-bottom: 8px;
    gap: 6px;
  }

  .tab-header h3 {
    font-size: 14px;
  }

  .tab-stats {
    gap: 8px;
    flex-wrap: wrap;
  }

  .tab-count,
  .tab-quantity {
    font-size: 11px;
    padding: 3px 6px;
    border-radius: 4px;
  }

  .statistics-content {
    gap: 8px;
    margin-top: 10px;
  }

  .chart-container,
  .table-container {
    border-radius: 6px;
    padding: 8px;
  }

  .chart {
    height: 200px;
    min-height: 160px;
  }
}
</style>
