<template>
  <div class="picking-progress-container">
    <!-- 页面标题区域 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <el-icon class="title-icon"><DataBoard /></el-icon>
            ピッキング進捗管理
          </h1>
          <p class="page-subtitle">リアルタイムでピッキング作業の進捗状況を監視・管理</p>
        </div>
        <div class="header-actions">
          <el-button
            @click="refreshData"
            :loading="loading.refresh"
            type="primary"
            size="default"
            class="refresh-btn"
          >
            <el-icon><Refresh /></el-icon>
            データ更新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 当日概要统计 -->
    <div class="overview-section">
      <div class="section-title">
        <h2>今日のピッキング作業概要</h2>
        <div class="title-line"></div>
      </div>
      <el-row :gutter="10" class="overview-cards">
        <el-col :span="7">
          <div class="stat-card total-card">
            <div class="card-background">
              <div class="background-pattern"></div>
            </div>
            <div class="card-content">
              <div class="stat-icon">
                <el-icon><DataBoard /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ detailOverviewStats.total }}</div>
                <div class="stat-label">総ピッキングパレット数</div>
                <div class="stat-trend">今日の全体</div>
              </div>
            </div>
          </div>
        </el-col>

        <el-col :span="7">
          <div class="stat-card pending-card">
            <div class="card-background">
              <div class="background-pattern"></div>
            </div>
            <div class="card-content">
              <div class="stat-icon">
                <el-icon><Clock /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ detailOverviewStats.pending }}</div>
                <div class="stat-label">未ピッキング</div>
                <div class="stat-trend">ピッキング待ち</div>
              </div>
            </div>
          </div>
        </el-col>

        <el-col :span="7">
          <div class="stat-card completed-card">
            <div class="card-background">
              <div class="background-pattern"></div>
            </div>
            <div class="card-content">
              <div class="stat-icon">
                <el-icon><Check /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ detailOverviewStats.completed }}</div>
                <div class="stat-label">完了済み</div>
                <div class="stat-trend">ピッキング済</div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 图表分析区域 -->
    <div class="analytics-section">
      <div class="analytics-grid">
        <!-- 进度圆环图卡片 -->
        <div class="chart-card progress-card">
          <div class="card-header">
            <div class="header-content">
              <div class="header-icon">
                <el-icon><DataBoard /></el-icon>
              </div>
              <div class="header-text">
                <h3 class="card-title">今日の進捗状況</h3>
                <p class="card-subtitle">リアルタイム完成率</p>
              </div>
            </div>
            <div class="completion-badge" :class="getCompletionBadgeClass(todayCompletionRate)">
              <span class="badge-icon">🎯</span>
              {{ todayCompletionRate }}%
            </div>
          </div>

          <div class="card-body">
            <div class="progress-display">
              <div class="progress-circle-wrapper">
                <el-progress
                  type="circle"
                  :percentage="todayCompletionRate"
                  :width="160"
                  :stroke-width="10"
                  :status="getProgressStatus(todayCompletionRate)"
                  :color="getProgressGradient(todayCompletionRate)"
                  stroke-linecap="round"
                >
                  <template #default="{ percentage }">
                    <div class="progress-center">
                      <div class="percentage-large">{{ percentage }}%</div>
                      <div class="progress-label-small">完成率</div>
                    </div>
                  </template>
                </el-progress>
              </div>

              <div class="progress-stats">
                <div class="stat-row">
                  <div class="stat-item completed-stat">
                    <div class="stat-icon">
                      <el-icon><CircleCheck /></el-icon>
                    </div>
                    <div class="stat-content">
                      <div class="stat-number">{{ detailOverviewStats.completed }}</div>
                      <div class="stat-text">完了済み</div>
                    </div>
                  </div>

                  <div class="stat-item pending-stat">
                    <div class="stat-icon">
                      <el-icon><Clock /></el-icon>
                    </div>
                    <div class="stat-content">
                      <div class="stat-number">{{ detailOverviewStats.pending }}</div>
                      <div class="stat-text">作業中</div>
                    </div>
                  </div>
                </div>

                <div class="total-stat">
                  <div class="total-label">総作業数</div>
                  <div class="total-number">{{ detailOverviewStats.total }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 進捗推移トレンド: 图标 TrendCharts / 标题・副标题 / 右侧三色图例 past #67c23a, today #e6a23c, future #909399 -->
        <div class="chart-card trend-card">
          <div class="card-header">
            <div class="header-content">
              <div class="header-icon">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="header-text">
                <h3 class="card-title">進捗推移トレンド</h3>
                <p class="card-subtitle">過去7日〜未来3日の推移</p>
              </div>
            </div>
            <div class="trend-controls">
              <div class="legend-item">
                <div class="legend-dot past"></div>
                <span>過去</span>
              </div>
              <div class="legend-item">
                <div class="legend-dot today"></div>
                <span>今日</span>
              </div>
              <div class="legend-item">
                <div class="legend-dot future"></div>
                <span>予定</span>
              </div>
            </div>
          </div>

          <div class="card-body">
            <div class="trend-chart-wrapper">
              <div ref="chartContainer" class="chart-container"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详细列表区域 -->
    <div class="data-section">
      <div class="data-panel">
        <div class="panel-header">
          <div class="header-left">
            <h3 class="panel-title">ピッキングリスト詳細</h3>
            <div class="data-count">
              <span class="count-text">全 {{ filteredDetailPalletList.length }} 件</span>
            </div>
          </div>

          <!-- 详细筛选区域 -->
          <div class="detail-filters">
            <div class="filter-row">
              <div class="filter-item">
                <label class="filter-label">期間:</label>
                <div class="date-filter-group">
                  <el-date-picker
                    v-model="detailFilters.dateRange"
                    type="daterange"
                    range-separator="〜"
                    start-placeholder="開始日"
                    end-placeholder="終了日"
                    value-format="YYYY-MM-DD"
                    size="small"
                    style="width: 240px"
                  />
                  <div class="date-quick-buttons-detail">
                    <el-button size="small" @click="setDetailDateRange(-1)">前日</el-button>
                    <el-button size="small" type="primary" @click="setDetailDateRange(0)"
                      >今日</el-button
                    >
                    <el-button size="small" @click="setDetailDateRange(1)">翌日</el-button>
                  </div>
                </div>
              </div>

              <div class="filter-item">
                <label class="filter-label">状態:</label>
                <el-select
                  v-model="statusFilter"
                  placeholder="全ての状態"
                  clearable
                  size="small"
                  style="width: 140px"
                >
                  <el-option label="全ての状態" value="" />
                  <el-option label="未ピッキング" value="pending" />
                  <el-option label="ピッキング済" value="completed" />
                </el-select>
              </div>

              <div class="filter-actions">
                <el-button size="small" @click="resetDetailFilters">
                  <el-icon><Refresh /></el-icon>
                  リセット
                </el-button>
                <el-button size="small" type="success" @click="printDetailData">
                  <el-icon><DataBoard /></el-icon>
                  印刷
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="table-container detail-table-wrap" v-loading="loading.data">
          <el-table
            :data="paginatedDetailData"
            stripe
            :row-class-name="getRowClass"
            @sort-change="handleSortChange"
            class="data-table detail-table"
          >
            <el-table-column prop="shipping_no_p" label="出荷番号" width="160" sortable="custom">
              <template #default="{ row }">
                <div class="shipping-no">
                  <el-tag size="small" type="info" effect="plain">{{ row.shipping_no_p }}</el-tag>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="shipping_date" label="出荷日" min-width="110" sortable="custom">
              <template #default="{ row }">
                <div class="date-cell">
                  <el-icon class="date-icon"><Calendar /></el-icon>
                  {{ formatDate(row.shipping_date) }}
                </div>
              </template>
            </el-table-column>

            <el-table-column
              prop="product_name"
              label="製品名"
              min-width="200"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <div class="product-cell">
                  <div class="product-name">{{ row.product_name }}</div>
                </div>
              </template>
            </el-table-column>

            <el-table-column
              prop="confirmed_boxes"
              label="箱数"
              width="88"
              align="center"
            >
              <template #default="{ row }">
                <span class="boxes-cell">{{ row.confirmed_boxes ?? '-' }}</span>
              </template>
            </el-table-column>

            <el-table-column
              prop="destination_name"
              label="納入先"
              min-width="180"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <div class="destination-cell">
                  <el-icon class="location-icon"><Location /></el-icon>
                  {{ row.destination_name }}
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="status" label="状態" min-width="140">
              <template #default="{ row }">
                <el-tag
                  :type="getStatusTagType(row.status)"
                  size="default"
                  :effect="row.status === 'completed' ? 'dark' : 'light'"
                  class="status-tag"
                >
                  <el-icon class="status-icon">
                    <component :is="getStatusIcon(row.status)" />
                  </el-icon>
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="picker_name" label="作業者" width="120" align="left">
              <template #default="{ row }">
                <div class="picker-cell">
                  <div v-if="row.picker_full_name || row.picker_name" class="picker-assigned">
                    <span class="picker-name">{{ row.picker_full_name || row.picker_name }}</span>
                  </div>
                  <div v-else class="picker-unassigned">
                    <span class="no-picker">未割当</span>
                  </div>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页组件 -->
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="filteredDetailPalletList.length"
              layout="total, sizes, prev, pager, next, jumper"
              class="pagination"
              :background="true"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataBoard,
  Clock,
  Check,
  Refresh,
  Calendar,
  Location,
  User,
  QuestionFilled,
  CircleCheck,
  Warning,
  CircleClose,
  TrendCharts,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import * as echarts from 'echarts'

/** new-progress API 响应体（request 拦截器已返回 response.data） */
interface NewProgressResponse {
  palletList?: unknown[]
  progressStats?: unknown
  todayOverview?: {
    total_today?: number
    pending_today?: number
    completed_today?: number
    today_completion_rate?: number
  }
}

interface PalletItem {
  shipping_no_p: string
  shipping_date: string
  product_name: string
  confirmed_boxes?: number
  destination_name: string
  status: string
  picker_id: string
  picker_name: string
  picker_full_name?: string
}

interface ProgressStat {
  shipping_date: string
  total_count: number
  pending_count: number
  completed_count: number
  completion_rate: number
}

interface TodayOverview {
  total_today: number
  pending_today: number
  completed_today: number
  today_completion_rate: number
}

const emit = defineEmits(['refresh'])

// 响应式数据
const loading = ref({
  refresh: false,
  data: false,
})

const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

// 获取日本标准时间(JST)的今天日期
const getJSTToday = () => {
  const now = new Date()
  const jstOffset = 9 * 60 // JST是UTC+9
  const jstTime = new Date(now.getTime() + jstOffset * 60 * 1000)
  return jstTime.toISOString().slice(0, 10)
}

// 详细列表筛选器
const today = getJSTToday()
const detailFilters = ref({
  dateRange: [today, today] as [string, string],
  status: '',
})

const palletList = ref<PalletItem[]>([])
const progressStats = ref<ProgressStat[]>([])
const todayOverview = ref<TodayOverview>({
  total_today: 0,
  pending_today: 0,
  completed_today: 0,
  today_completion_rate: 0,
})

const chartContainer = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
let initRetryCount = 0
const MAX_INIT_RETRIES = 5
let resizeObserver: ResizeObserver | null = null
let mutationObserver: MutationObserver | null = null

// ピッキングリスト詳細の筛选结果に基づく概要统计（概要カード・進捗円環に表示）
const detailOverviewStats = computed(() => {
  const list = filteredDetailPalletList.value
  const total = list.length
  const completed = list.filter((i) => i.status === 'completed').length
  const pending = list.filter(
    (i) => i.status === 'pending' || i.status === 'picking',
  ).length
  const completionRate = total > 0 ? Math.round((completed / total) * 1000) / 10 : 0
  return { total, completed, pending, completionRate }
})

// 计算属性（概要区域は detailOverviewStats を使用）
const todayCompletionRate = computed(() => {
  return detailOverviewStats.value.completionRate
})

const filteredPalletList = computed(() => {
  if (!statusFilter.value) return palletList.value
  return palletList.value.filter((item) => item.status === statusFilter.value)
})

// 製品名に「加工」「アーチ」「料金」を含む行を除外する
const excludeProductNameKeywords = (name: string) => {
  const n = (name || '').trim()
  return n.includes('加工') || n.includes('アーチ') || n.includes('料金')
}

// 详细列表的过滤逻辑
const filteredDetailPalletList = computed(() => {
  let filtered = palletList.value

  // 製品名に「加工」「アーチ」「料金」を含むデータを除外
  filtered = filtered.filter((item) => !excludeProductNameKeywords(item.product_name))

  // 按日期范围过滤
  if (detailFilters.value.dateRange && detailFilters.value.dateRange.length === 2) {
    const [startDate, endDate] = detailFilters.value.dateRange
    if (startDate && endDate) {
      filtered = filtered.filter((item) => {
        const shippingDate = item.shipping_date
        return shippingDate >= startDate && shippingDate <= endDate
      })
    }
  }

  // 按状态过滤（使用原有的statusFilter或新的detailFilters.status）
  const filterStatus = detailFilters.value.status || statusFilter.value
  if (filterStatus) {
    filtered = filtered.filter((item) => item.status === filterStatus)
  }

  return filtered
})

const _paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredPalletList.value.slice(start, end)
})

const paginatedDetailData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredDetailPalletList.value.slice(start, end)
})

// 生成测试数据
const generateTestData = () => {
  const testData = []
  const today = new Date()

  for (let i = -7; i <= 3; i++) {
    const date = new Date(today)
    date.setDate(today.getDate() + i)
    testData.push({
      shipping_date: date.toISOString().split('T')[0],
      total_count: Math.floor(Math.random() * 50) + 20,
      pending_count: Math.floor(Math.random() * 20),
      completed_count: Math.floor(Math.random() * 30) + 10,
      completion_rate: Math.floor(Math.random() * 40) + 60,
    })
  }

  return testData
}

// 進捗推移トレンド 数据: GET /api/shipping/picking/new-progress → progressStats（无数据时 generateTestData 兜底）→ nextTick 后 updateChart / initChart+updateChart
// 方法
const fetchProgressData = async () => {
  loading.value.data = true
  try {
    const range = detailFilters.value.dateRange
    const params: Record<string, string> = {}
    if (range && range.length === 2 && range[0] && range[1]) {
      params.start_date = range[0]
      params.end_date = range[1]
    }
    const response = (await request.get('/api/shipping/picking/new-progress', {
      params,
    })) as NewProgressResponse

    if (!response || typeof response !== 'object') {
      ElMessage.error('データの取得に失敗しました')
      return
    }

    // palletList: API は配列を返す
    palletList.value = Array.isArray(response.palletList) ? (response.palletList as PalletItem[]) : []

    // todayOverview: API は todayOverview オブジェクトを返す
    const ov = response.todayOverview
    todayOverview.value = {
      total_today: ov?.total_today ?? 0,
      pending_today: ov?.pending_today ?? 0,
      completed_today: ov?.completed_today ?? 0,
      today_completion_rate: ov?.today_completion_rate ?? 0,
    }

    // 進捗推移トレンド: 后端返回过去7日～未来3日、按日出荷分组、排除加工・アーチ・料金 的 progressStats 配列
    // 直接使用后端 completion_rate；无数据时用 generateTestData() 兜底
    if (Array.isArray(response.progressStats) && response.progressStats.length > 0) {
      progressStats.value = response.progressStats as ProgressStat[]
    } else {
      progressStats.value = generateTestData() as ProgressStat[]
    }

    await nextTick()
    if (chartInstance) {
      updateChart()
    } else {
      await initChart()
      if (chartInstance) updateChart()
    }

    ElMessage.success(`データを取得しました (${palletList.value.length}件)`)
  } catch (error: any) {
    console.error('数据获取失败:', error)
    if (!error?.response) {
      ElMessage.error(error?.message || 'データの取得に失敗しました')
    }
  } finally {
    loading.value.data = false
  }
}

const refreshData = async () => {
  loading.value.refresh = true
  try {
    await fetchProgressData()
    ElMessage.success('データを更新しました')
    emit('refresh')
  } finally {
    loading.value.refresh = false
  }
}

const initChart = async () => {
  if (!chartContainer.value) {
    console.error('Chart container not found')
    return
  }

  // 等待DOM更新
  await nextTick()

  // 强制设置容器尺寸
  chartContainer.value.style.width = '100%'
  chartContainer.value.style.height = '340px'
  chartContainer.value.style.minHeight = '340px'
  chartContainer.value.style.minWidth = '400px'
  chartContainer.value.style.display = 'block'

  // 再次等待DOM更新
  await nextTick()

  // 检查容器尺寸
  const containerRect = chartContainer.value.getBoundingClientRect()

  if (containerRect.width === 0 || containerRect.height === 0) {
    // 使用ResizeObserver监听容器尺寸变化
    if (!resizeObserver) {
      resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          const { width, height } = entry.contentRect
          if (width > 0 && height > 0) {
            resizeObserver?.disconnect()
            resizeObserver = null
            initRetryCount = 0
            initChart().then(() => updateChart())
          }
        }
      })
      resizeObserver.observe(chartContainer.value)
    }

    // 使用MutationObserver监听DOM变化
    if (!mutationObserver) {
      mutationObserver = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
          if (mutation.type === 'childList' || mutation.type === 'attributes') {
            const containerRect = chartContainer.value?.getBoundingClientRect()
            if (containerRect && containerRect.width > 0 && containerRect.height > 0) {
              mutationObserver?.disconnect()
              mutationObserver = null
              initRetryCount = 0
              initChart().then(() => updateChart())
            }
          }
        }
      })
      mutationObserver.observe(chartContainer.value, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class'],
      })
    }

    if (initRetryCount < MAX_INIT_RETRIES) {
      initRetryCount++
      return
    } else {
      console.error('Failed to initialize chart after maximum retries. Container size is still 0.')
      resizeObserver?.disconnect()
      resizeObserver = null
      mutationObserver?.disconnect()
      mutationObserver = null
      return
    }
  }

  try {
    // 销毁已存在的图表实例
    if (chartInstance) {
      chartInstance.dispose()
      chartInstance = null
    }

    // 确保容器有明确的尺寸
    chartContainer.value.style.width = '100%'
    chartContainer.value.style.height = '100%'

    chartInstance = echarts.init(chartContainer.value, null, {
      renderer: 'canvas',
      useDirtyRect: false,
      width: Math.max(containerRect.width, 400),
      height: Math.max(containerRect.height, 300),
    })

    const option = {
      backgroundColor: 'transparent',
      title: {
        show: false,
      },
      tooltip: {
        trigger: 'axis',
        confine: true,
        axisPointer: {
          type: 'cross',
          crossStyle: {
            color: '#3b82f6',
            width: 1,
            opacity: 0.8,
          },
          lineStyle: {
            color: '#3b82f6',
            width: 1,
            opacity: 0.6,
            type: 'dashed',
          },
        },
        backgroundColor: 'rgba(255, 255, 255, 0.98)',
        borderColor: '#e2e8f0',
        borderWidth: 1,
        textStyle: {
          color: '#1e293b',
          fontSize: 13,
          fontWeight: '500',
        },
        formatter: (params: any) => {
          if (!params || !params[0]) return ''

          const data = params[0]
          const dateStr = data.axisValueLabel

          // 判断是否为今天或未来
          const date = new Date(dateStr)
          const today = new Date()
          today.setHours(0, 0, 0, 0)
          const dataDate = new Date(date)
          dataDate.setHours(0, 0, 0, 0)

          let label = `${date.getMonth() + 1}月${date.getDate()}日`
          let statusIcon = '📊'
          let statusColor = '#3b82f6'

          if (dataDate.getTime() === today.getTime()) {
            label += ' (今日)'
            statusIcon = '🎯'
            statusColor = '#f59e0b'
          } else if (dataDate.getTime() > today.getTime()) {
            label += ' (予定)'
            statusIcon = '📅'
            statusColor = '#6b7280'
          } else {
            statusIcon = '✅'
            statusColor = '#10b981'
          }

          return `
            <div style="padding: 12px 0; min-width: 180px;">
              <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 18px; margin-right: 8px;">${statusIcon}</span>
                <span style="font-weight: 700; color: ${statusColor}; font-size: 15px;">${label}</span>
              </div>
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="color: #64748b; font-size: 13px;">完成率</span>
                <div style="display: flex; align-items: center;">
                  <div style="width: 10px; height: 10px; background: ${statusColor}; border-radius: 50%; margin-right: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></div>
                  <span style="font-size: 16px; font-weight: 800; color: ${statusColor};">${data.value}%</span>
                </div>
              </div>
            </div>
          `
        },
        borderRadius: 16,
        shadowColor: 'rgba(0, 0, 0, 0.15)',
        shadowBlur: 20,
        shadowOffsetY: 8,
        padding: [16, 20],
      },
      grid: {
        left: '8%',
        right: '8%',
        bottom: '15%',
        top: '10%',
        containLabel: true,
        backgroundColor: 'transparent',
      },
      xAxis: {
        type: 'category',
        data: [],
        axisLabel: {
          fontSize: 12,
          color: '#64748b',
          interval: 0,
          margin: 15,
          fontWeight: '600',
          formatter: (value: string) => {
            const date = new Date(value)
            const today = new Date()
            today.setHours(0, 0, 0, 0)
            const dataDate = new Date(date)
            dataDate.setHours(0, 0, 0, 0)

            let dateStr = `${date.getMonth() + 1}/${date.getDate()}`
            if (dataDate.getTime() === today.getTime()) {
              dateStr += '\n今日'
            }
            return dateStr
          },
        },
        axisLine: {
          lineStyle: {
            color: '#e2e8f0',
            width: 2,
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
        min: 0,
        max: 100,
        interval: 25,
        axisLabel: {
          formatter: '{value}%',
          fontSize: 12,
          color: '#64748b',
          margin: 20,
          fontWeight: '600',
        },
        axisLine: {
          show: false,
        },
        axisTick: {
          show: false,
        },
        splitLine: {
          lineStyle: {
            color: '#f1f5f9',
            type: 'solid',
            width: 1,
          },
        },
      },
      series: [
        {
          name: '完成率',
          type: 'line',
          data: [],
          smooth: 0.3,
          smoothMonotone: 'x',
          symbolSize: 8,
          symbol: 'circle',
          showSymbol: true,
          lineStyle: {
            width: 4,
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 1,
              y2: 0,
              colorStops: [
                { offset: 0, color: '#3b82f6' },
                { offset: 0.3, color: '#06b6d4' },
                { offset: 0.6, color: '#10b981' },
                { offset: 1, color: '#f59e0b' },
              ],
            },
            shadowColor: 'rgba(59, 130, 246, 0.4)',
            shadowBlur: 12,
            shadowOffsetY: 4,
          },
          itemStyle: {
            color: '#ffffff',
            borderColor: '#3b82f6',
            borderWidth: 3,
            shadowColor: 'rgba(59, 130, 246, 0.5)',
            shadowBlur: 10,
            shadowOffsetY: 3,
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
                { offset: 0.3, color: 'rgba(6, 182, 212, 0.25)' },
                { offset: 0.6, color: 'rgba(16, 185, 129, 0.2)' },
                { offset: 1, color: 'rgba(245, 158, 11, 0.1)' },
              ],
            },
            shadowColor: 'rgba(59, 130, 246, 0.2)',
            shadowBlur: 20,
            shadowOffsetY: 10,
          },
          emphasis: {
            focus: 'series',
            scale: 1.2,
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(59, 130, 246, 0.8)',
              borderWidth: 6,
            },
            lineStyle: {
              width: 5,
              shadowBlur: 20,
              shadowColor: 'rgba(59, 130, 246, 0.6)',
            },
          },
          markPoint: {
            symbol: 'pin',
            symbolSize: [40, 50],
            data: [],
            itemStyle: {
              color: '#f59e0b',
              borderColor: '#ffffff',
              borderWidth: 3,
              shadowColor: 'rgba(245, 158, 11, 0.5)',
              shadowBlur: 15,
            },
            label: {
              show: true,
              position: 'top',
              distance: 20,
              color: '#f59e0b',
              fontWeight: 'bold',
              fontSize: 13,
            },
          },
        },
      ],
      animationDuration: 2500,
      animationEasing: 'cubicInOut' as const,
      animationDelay: (idx: number) => idx * 150,
      animationDurationUpdate: 1000,
      animationEasingUpdate: 'cubicInOut' as const,
    }

    chartInstance.setOption(option)
  } catch (error) {
    console.error('Error initializing chart:', error)
  }
}

const updateChart = () => {
  if (!chartInstance) return

  if (!progressStats.value || progressStats.value.length === 0) {
    console.warn('No progress data available')
    // 显示空数据状态
    chartInstance.setOption({
      xAxis: { data: [] },
      series: [{ data: [] }],
    })
    return
  }

  try {
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    const dates = progressStats.value.map((stat) => stat.shipping_date)
    const rates = progressStats.value.map((stat, _index) => {
      const statDate = new Date(stat.shipping_date)
      statDate.setHours(0, 0, 0, 0)

      const isToday = statDate.getTime() === today.getTime()
      const isFuture = statDate.getTime() > today.getTime()
      const isPast = statDate.getTime() < today.getTime()

      let itemColor = '#3b82f6'
      let shadowColor = 'rgba(59, 130, 246, 0.5)'

      if (isToday) {
        itemColor = '#f59e0b'
        shadowColor = 'rgba(245, 158, 11, 0.7)'
      } else if (isFuture) {
        itemColor = '#909399'
        shadowColor = 'rgba(144, 147, 153, 0.4)'
      } else if (isPast) {
        if (stat.completion_rate >= 90) {
          itemColor = '#10b981'
          shadowColor = 'rgba(16, 185, 129, 0.5)'
        } else if (stat.completion_rate >= 70) {
          itemColor = '#06b6d4'
          shadowColor = 'rgba(6, 182, 212, 0.5)'
        } else if (stat.completion_rate >= 50) {
          itemColor = '#f59e0b'
          shadowColor = 'rgba(245, 158, 11, 0.5)'
        } else {
          itemColor = '#ef4444'
          shadowColor = 'rgba(239, 68, 68, 0.5)'
        }
      }

      return {
        value: stat.completion_rate,
        symbol: isToday ? 'diamond' : 'circle',
        symbolSize: isToday ? 12 : isFuture ? 6 : 8,
        itemStyle: {
          color: '#ffffff',
          borderColor: itemColor,
          borderWidth: isToday ? 4 : 3,
          shadowColor: shadowColor,
          shadowBlur: isToday ? 15 : 10,
          shadowOffsetY: isToday ? 4 : 2,
        },
        emphasis: {
          scale: isToday ? 1.5 : 1.3,
          itemStyle: {
            shadowBlur: 25,
            shadowColor: shadowColor,
            borderWidth: 6,
          },
        },
      }
    })

    // 找到今天的数据点用于标记
    const todayMarkPoint = progressStats.value.findIndex((stat) => {
      const statDate = new Date(stat.shipping_date)
      statDate.setHours(0, 0, 0, 0)
      return statDate.getTime() === today.getTime()
    })

    const markPointData =
      todayMarkPoint >= 0
        ? [
            {
              name: '今日',
              coord: [todayMarkPoint, progressStats.value[todayMarkPoint].completion_rate],
              value: `${progressStats.value[todayMarkPoint].completion_rate}%`,
              itemStyle: {
                color: '#f59e0b',
                borderColor: '#ffffff',
                borderWidth: 3,
                shadowColor: 'rgba(245, 158, 11, 0.6)',
                shadowBlur: 15,
              },
            },
          ]
        : []

    chartInstance.setOption(
      {
        xAxis: {
          data: dates,
        },
        series: [
          {
            data: rates,
            label: {
              show: true,
              position: 'top',
              formatter: (params: { data?: { value?: number }; value?: unknown }) => {
                const v = params.data?.value ?? (typeof params.value === 'number' ? params.value : null)
                return v != null ? `${v}%` : ''
              },
              fontSize: 11,
              color: '#374151',
              fontWeight: 500,
            },
            markPoint: {
              data: markPointData,
            },
          },
        ],
      },
      { notMerge: false },
    )

    console.log('Chart updated with data:', { dates: dates.length, rates: rates.length })
  } catch (error) {
    console.error('Error updating chart:', error)
  }
}

const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  console.log('排序变化:', prop, order)
  // 这里可以实现自定义排序逻辑
}

// 样式辅助函数
const getRowClass = ({ row }: { row: PalletItem }) => {
  return `status-${row.status}`
}

const getStatusTagType = (
  status: string,
): 'success' | 'warning' | 'danger' | 'info' | 'primary' => {
  const typeMap: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
    pending: 'warning',
    completed: 'success',
    cancelled: 'danger',
    shortage: 'danger',
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string): string => {
  const textMap: Record<string, string> = {
    pending: '未ピッキング',
    completed: 'ピッキング済',
    cancelled: 'キャンセル',
    shortage: '在庫欠品',
  }
  return textMap[status] || status
}

const getProgressStatus = (percentage: number) => {
  if (percentage === 100) return 'success'
  if (percentage >= 80) return ''
  if (percentage >= 50) return 'warning'
  return 'exception'
}

const formatDate = (dateStr: string): string => {
  if (!dateStr) return '-'
  // 使用日本标准时间格式化日期
  const date = new Date(dateStr + 'T00:00:00+09:00') // 确保使用JST时区
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const getCompletionBadgeClass = (percentage: number): string => {
  if (percentage >= 90) return 'badge-excellent'
  if (percentage >= 70) return 'badge-good'
  if (percentage >= 50) return 'badge-normal'
  return 'badge-low'
}

const _getProgressColor = (percentage: number): string => {
  if (percentage >= 80) return '#67C23A'
  if (percentage >= 50) return '#E6A23C'
  return '#F56C6C'
}

const getProgressGradient = (percentage: number) => {
  if (percentage >= 90) {
    return [
      { color: '#10b981', percentage: 0 },
      { color: '#059669', percentage: 100 },
    ]
  } else if (percentage >= 70) {
    return [
      { color: '#3b82f6', percentage: 0 },
      { color: '#1d4ed8', percentage: 100 },
    ]
  } else if (percentage >= 50) {
    return [
      { color: '#f59e0b', percentage: 0 },
      { color: '#d97706', percentage: 100 },
    ]
  } else {
    return [
      { color: '#ef4444', percentage: 0 },
      { color: '#dc2626', percentage: 100 },
    ]
  }
}

const getStatusIcon = (status: string) => {
  const iconMap: Record<string, any> = {
    pending: Clock,
    completed: CircleCheck,
    cancelled: CircleClose,
    shortage: Warning,
  }
  return iconMap[status] || Clock
}

// 详细列表筛选相关方法
const resetDetailFilters = () => {
  const today = getJSTToday()
  detailFilters.value.dateRange = [today, today]
  detailFilters.value.status = ''
  statusFilter.value = ''
}

const setDetailDateRange = (dayOffset: number) => {
  if (dayOffset === 0) {
    // 设置为今天
    const today = getJSTToday()
    detailFilters.value.dateRange = [today, today]
  } else {
    // 基于当前选择的日期进行增减
    const currentDate = detailFilters.value.dateRange[0]
      ? new Date(detailFilters.value.dateRange[0])
      : new Date()
    currentDate.setDate(currentDate.getDate() + dayOffset)
    const dateStr = currentDate.toISOString().slice(0, 10)
    detailFilters.value.dateRange = [dateStr, dateStr]
  }
}

const printDetailData = () => {
  // 创建打印样式
  const printStyles = `
    <style>
      @media print {
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; font-size: 12px; }
        .print-container { padding: 20px; }
        .print-header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }
        .print-title { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
        .print-date { font-size: 12px; color: #666; }
        .print-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .print-table th, .print-table td { border: 1px solid #333; padding: 8px; text-align: left; }
        .print-table th { background-color: #f5f5f5; font-weight: bold; }
        .print-table td { font-size: 11px; }
        .status-completed { color: #67C23A; font-weight: bold; }
        .status-pending { color: #E6A23C; font-weight: bold; }
        .no-picker { color: #999; font-style: italic; }
        @page { margin: 1cm; }
      }
    </style>
  `

  // 创建打印内容
  const printContent = `
    ${printStyles}
    <div class="print-container">
      <div class="print-header">
        <div class="print-title">ピッキングリスト詳細</div>
        <div class="print-date">印刷日時: ${new Date().toLocaleString('ja-JP')}</div>
        <div class="print-date">期間: ${detailFilters.value.dateRange[0]} 〜 ${detailFilters.value.dateRange[1]}</div>
        <div class="print-date">状態: ${detailFilters.value.status || statusFilter.value || '全ての状態'}</div>
        <div class="print-date">総件数: ${filteredDetailPalletList.value.length}件</div>
      </div>

      <table class="print-table">
        <thead>
          <tr>
            <th>出荷番号</th>
            <th>出荷日</th>
            <th>製品名</th>
            <th>箱数</th>
            <th>納入先</th>
            <th>状態</th>
            <th>作業者</th>
          </tr>
        </thead>
        <tbody>
          ${filteredDetailPalletList.value
            .map(
              (item) => `
            <tr>
              <td>${item.shipping_no_p}</td>
              <td>${formatDate(item.shipping_date)}</td>
              <td>${item.product_name}</td>
              <td>${item.confirmed_boxes ?? '-'}</td>
              <td>${item.destination_name}</td>
              <td class="status-${item.status}">${getStatusText(item.status)}</td>
              <td>${item.picker_full_name || item.picker_name || '<span class="no-picker">未割当</span>'}</td>
            </tr>
          `,
            )
            .join('')}
        </tbody>
      </table>
    </div>
  `

  // 打开新窗口并打印
  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.write(printContent)
    printWindow.document.close()
    printWindow.focus()

    // 等待内容加载完成后打印
    setTimeout(() => {
      printWindow.print()
      printWindow.close()
    }, 500)
  } else {
    console.error('无法打开打印窗口，可能被浏览器阻止')
  }
}

// 期間変更時にピッキングリスト詳細用データを再取得
watch(
  () => detailFilters.value.dateRange,
  (range) => {
    if (range && range.length === 2 && range[0] && range[1]) {
      fetchProgressData()
    }
  },
  { deep: true },
)

// 响应式调整图表大小
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(async () => {
  await fetchProgressData()

  await nextTick()
  if (chartContainer.value) {
    chartContainer.value.style.display = 'none'
    await nextTick()
    chartContainer.value.style.display = 'block'
    await nextTick()

    requestAnimationFrame(async () => {
      await initChart()
      if (chartInstance) updateChart()
    })

    setTimeout(async () => {
      if (!chartInstance) {
        await initChart()
        if (chartInstance) updateChart()
      }
    }, 500)
  }

  // 添加窗口大小变化监听
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (mutationObserver) {
    mutationObserver.disconnect()
    mutationObserver = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
/* 整体容器 - 紧凑 */
.picking-progress-container {
  min-height: 100vh;
  background: linear-gradient(145deg, #f1f5f9 0%, #e2e8f0 100%);
  padding: 10px 12px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* 页面标题 - 紧凑 */
.page-header {
  background: linear-gradient(135deg, #fff 0%, #f8fafc 100%);
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section { flex: 1; }

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 22px;
  color: #6366f1;
}

.page-subtitle {
  font-size: 12px;
  color: #64748b;
  margin: 0;
  font-weight: 400;
}

.header-actions { display: flex; gap: 8px; }

.refresh-btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 13px;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
  transition: all 0.2s ease;
}

.refresh-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(99, 102, 241, 0.25);
}

/* 概要统计 - 紧凑 */
.overview-section {
  margin-bottom: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  gap: 10px;
}

.section-title h2 {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin: 0;
}

.title-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, #6366f1 0%, transparent 100%);
  border-radius: 1px;
}

.overview-cards {
  display: flex;
  gap: 10px;
}

.stat-card {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.25s ease;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
}

.total-card {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
}

.pending-card {
  background: linear-gradient(135deg, #ec4899 0%, #f43f5e 100%);
  color: white;
}

.completed-card {
  background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%);
  color: white;
}

.card-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.08;
}

.background-pattern {
  width: 100%;
  height: 100%;
  background-image:
    radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
}

.card-content {
  position: relative;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 1;
}

.stat-icon {
  font-size: 28px;
  opacity: 0.95;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
}

.stat-info { flex: 1; }

.stat-value {
  font-size: 22px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 4px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.stat-label {
  font-size: 12px;
  font-weight: 600;
  opacity: 0.95;
  margin-bottom: 2px;
}

.stat-trend {
  font-size: 11px;
  opacity: 0.85;
  font-weight: 500;
}

/* 图表分析 - 紧凑 */
.analytics-section {
  margin-bottom: 12px;
}

.analytics-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 12px;
  align-items: stretch;
}

.chart-card {
  background: linear-gradient(135deg, #fff 0%, #f8fafc 100%);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(226, 232, 240, 0.9);
  transition: all 0.25s ease;
  position: relative;
}

.chart-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
  z-index: 1;
}

.chart-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.card-header {
  padding: 10px 14px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: linear-gradient(135deg, #fff 0%, #fafbff 100%);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.header-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.header-text { flex: 1; }

.card-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 2px 0;
  line-height: 1.3;
}

.card-subtitle {
  font-size: 11px;
  color: #64748b;
  margin: 0;
  font-weight: 500;
}

.completion-badge {
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

.badge-icon { font-size: 12px; }

.badge-excellent {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.badge-good {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
}

.badge-normal {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.badge-low {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.trend-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot.past {
  background: #67c23a;
}

.legend-dot.today {
  background: #e6a23c;
}

.legend-dot.future {
  background: #909399;
}

.card-body {
  padding: 12px 14px;
}

.progress-card .card-body {
  padding: 14px 14px;
}

.progress-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.progress-circle-wrapper {
  position: relative;
}

.progress-center {
  text-align: center;
}

.percentage-large {
  font-size: 20px;
  font-weight: 800;
  color: #1e293b;
  line-height: 1;
}

.progress-label-small {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
  font-weight: 600;
}

.progress-stats {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-row {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 10px;
  flex: 1;
  transition: all 0.2s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
}

.completed-stat {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.pending-stat {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.05) 100%);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.stat-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.completed-stat .stat-icon {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.pending-stat .stat-icon {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 20px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 2px;
}

.completed-stat .stat-number {
  color: #059669;
}

.pending-stat .stat-number {
  color: #d97706;
}

.stat-text {
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
}

.total-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 16px;
  border: 1px solid #cbd5e1;
}

.total-label {
  font-size: 14px;
  color: #475569;
  font-weight: 600;
}

.total-number {
  font-size: 24px;
  font-weight: 800;
  color: #1e293b;
}

/* 進捗推移トレンド: 卡片・图表容器样式（渐变白底、圆角20/16、细边框、阴影、blur） */
.trend-card .card-body {
  padding: 20px 28px 28px 28px;
}

.trend-chart-wrapper {
  height: 380px;
  position: relative;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    rgba(248, 250, 252, 0.98) 50%,
    rgba(241, 245, 249, 0.95) 100%
  );
  border-radius: 20px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  backdrop-filter: blur(10px);
  padding: 20px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 4px 6px rgba(0, 0, 0, 0.07),
    0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chart-container {
  width: 100%;
  height: 100%;
  min-height: 340px;
  min-width: 400px;
  position: relative;
  z-index: 2;
  border-radius: 16px;
  background: transparent;
  display: block;
  overflow: hidden;
}

/* 确保图表容器可见 */
.chart-container > div {
  width: 100% !important;
  height: 100% !important;
  min-height: 340px !important;
  min-width: 400px !important;
}

.chart-container canvas {
  border-radius: 16px;
  display: block !important;
}

/* 数据列表 - 紧凑 */
.data-section {
  margin-bottom: 12px;
}

.data-panel {
  background: linear-gradient(135deg, #fff 0%, #f8fafc 100%);
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.data-panel .panel-header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f1f5f9;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.data-count {
  padding: 4px 10px;
  background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
  border-radius: 10px;
  border: 1px solid #0ea5e9;
}

.count-text {
  font-size: 12px;
  color: #0369a1;
  font-weight: 600;
}

.header-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.detail-filters {
  background: #f8fafc;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-label {
  font-size: 12px;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
}

.date-filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-quick-buttons-detail {
  display: flex;
  gap: 4px;
}

.date-quick-buttons-detail .el-button {
  min-width: 40px;
  padding: 5px 10px;
  font-size: 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.date-quick-buttons-detail .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.filter-actions {
  display: flex;
  gap: 6px;
  margin-left: auto;
}

.filter-actions .el-button {
  padding: 5px 12px;
  font-size: 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.filter-actions .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.filter-controls {
  display: flex;
  gap: 12px;
}

.status-filter {
  min-width: 160px;
}

.table-container {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.data-table {
  border-radius: 16px;
  overflow: hidden;
}

/* ピッキングリスト詳細テーブル - 日本简约风 */
.detail-table-wrap {
  background: #fafafa;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
  box-shadow: none;
}

.detail-table-wrap :deep(.el-table) {
  --el-table-border-color: #eee;
  --el-table-header-bg-color: #f5f5f5;
  font-size: 13px;
  letter-spacing: 0.02em;
}

.detail-table-wrap :deep(.el-table__header-wrapper) th {
  background: #f5f5f5 !important;
  color: #333;
  font-weight: 600;
  font-size: 12px;
  letter-spacing: 0.04em;
  padding: 14px 12px;
  border-bottom: 1px solid #e8e8e8;
}

.detail-table-wrap :deep(.el-table__body-wrapper) td {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  color: #444;
}

.detail-table-wrap :deep(.el-table__row:hover) td {
  background: #f9f9f9 !important;
}

.detail-table-wrap :deep(.el-table__row) td {
  background: #fff;
}

.detail-table-wrap :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #fafafa;
}

.detail-table-wrap :deep(.el-table--striped .el-table__body tr.el-table__row--striped:hover td) {
  background: #f5f5f5 !important;
}

.boxes-cell {
  font-variant-numeric: tabular-nums;
  color: #555;
  font-weight: 500;
}

.detail-table-wrap .picker-cell .picker-name {
  font-weight: 500;
  color: #333;
}

.detail-table-wrap .no-picker {
  color: #999;
  font-style: normal;
  font-size: 12px;
}

/* 表格单元格样式 */
.shipping-no {
  display: flex;
  align-items: center;
}

.date-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #374151;
}

.date-icon {
  color: #6b7280;
  font-size: 14px;
}

.product-cell {
  padding: 4px 0;
}

.product-name {
  font-weight: 500;
  color: #374151;
  line-height: 1.4;
}

.destination-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #374151;
}

.location-icon {
  color: #6b7280;
  font-size: 14px;
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  border-radius: 20px;
  padding: 6px 12px;
}

.status-icon {
  font-size: 14px;
}

.picker-cell {
  display: flex;
  align-items: center;
}

.picker-assigned {
  display: flex;
  align-items: center;
  gap: 8px;
}

.picker-avatar {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
}

.picker-name {
  color: #3b82f6;
  font-weight: 600;
}

.picker-unassigned {
  display: flex;
  align-items: center;
  gap: 8px;
}

.unassigned-icon {
  color: #9ca3af;
  font-size: 16px;
}

.no-picker {
  color: #9ca3af;
  font-style: italic;
  font-weight: 500;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  padding: 20px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.pagination {
  background: white;
  border-radius: 12px;
  padding: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 行状态样式 */
:deep(.status-pending) {
  background-color: rgba(251, 191, 36, 0.05);
}

:deep(.status-completed) {
  background-color: rgba(16, 185, 129, 0.05);
}

:deep(.status-cancelled) {
  background-color: rgba(239, 68, 68, 0.05);
}

:deep(.status-shortage) {
  background-color: rgba(239, 68, 68, 0.05);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .overview-cards {
    flex-direction: column;
  }

  .analytics-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .progress-card .card-body {
    padding: 24px 20px;
  }

  .stat-row {
    flex-direction: column;
    gap: 12px;
  }
}

@media (max-width: 768px) {
  .picking-progress-container {
    padding: 16px;
  }

  .page-header {
    padding: 20px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .page-title {
    font-size: 24px;
  }

  .chart-panel {
    padding: 20px;
  }

  /* 详细筛选区域移动端样式 */
  .filter-row {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .filter-item {
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
  }

  .date-filter-group {
    flex-direction: column;
    gap: 8px;
  }

  .filter-actions {
    margin-left: 0;
    justify-content: center;
  }
}

/* ========== Modern compact tab polish ========== */
.picking-progress-container {
  min-height: auto;
  padding: 0;
  background: transparent;
}

.page-header {
  margin-bottom: 8px;
  padding: 9px 12px;
  border-radius: 14px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.07);
}

.page-title {
  font-size: 15px;
  margin-bottom: 2px;
}

.title-icon {
  font-size: 18px;
}

.page-subtitle {
  font-size: 11px;
}

.refresh-btn {
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 12px;
}

.overview-section,
.analytics-section,
.data-section {
  margin-bottom: 8px;
}

.section-title {
  margin-bottom: 6px;
}

.section-title h2 {
  font-size: 13px;
}

.overview-cards {
  gap: 8px;
}

.card-content {
  padding: 9px 12px;
  gap: 10px;
}

.stat-icon {
  font-size: 22px;
}

.stat-value {
  font-size: 20px;
}

.stat-label,
.stat-trend {
  font-size: 11px;
}

.analytics-grid {
  grid-template-columns: minmax(260px, 300px) 1fr;
  gap: 8px;
}

.chart-card,
.data-panel {
  border-radius: 14px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.07);
}

.card-header {
  padding: 8px 10px;
}

.header-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  font-size: 16px;
}

.card-title {
  font-size: 13px;
}

.card-body,
.progress-card .card-body,
.trend-card .card-body {
  padding: 10px 12px;
}

.progress-display {
  gap: 10px;
}

.trend-chart-wrapper {
  height: 300px;
  padding: 12px;
  border-radius: 14px;
}

.chart-container,
.chart-container > div {
  min-height: 270px !important;
}

.data-panel {
  padding: 10px 12px;
}

.data-panel .panel-header {
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 8px;
}

.detail-filters {
  padding: 8px 10px;
}

.detail-table-wrap {
  border-radius: 12px;
}

.detail-table-wrap :deep(.el-table__header-wrapper) th,
.detail-table-wrap :deep(.el-table__body-wrapper) td {
  padding: 7px 9px;
}

.pagination-wrapper {
  margin-top: 8px;
  padding: 10px;
}

@media (max-width: 1200px) {
  .analytics-grid {
    gap: 8px;
  }

  .progress-card .card-body {
    padding: 10px 12px;
  }
}

@media (max-width: 768px) {
  .picking-progress-container,
  .page-header {
    padding: 8px;
  }

  .page-title {
    font-size: 15px;
  }
}
</style>
