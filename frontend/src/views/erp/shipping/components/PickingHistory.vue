<template>
  <div class="picking-history-container">
    <!-- Modern Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="title-text">
            <h1 class="page-title">ピッキング履歴分析</h1>
            <p class="page-subtitle">作業履歴の分析と完了率管理</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button
            type="primary"
            @click="refreshData"
            :loading="loading.search"
            class="refresh-btn"
          >
            <el-icon><Refresh /></el-icon>
            データ更新
          </el-button>
        </div>
      </div>
    </div>

    <!-- Modern Filter Card -->
    <el-card class="filter-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Filter /></el-icon>
            <span class="header-title">検索条件</span>
          </div>
          <el-form-item>
            <el-button @click="showDestinationGroupManager" class="reset-btn">
              <el-icon><Setting /></el-icon>
              担当者別納入先グループ管理
            </el-button>
          </el-form-item>
        </div>
      </template>

      <el-form :inline="true" :model="filters" class="filter-form">
        <!-- 期間選択セクション -->
        <div class="date-selection-section">
          <div class="date-selection-row">
            <!-- 快捷日期按钮组 -->
            <div class="quick-date-buttons">
              <el-form-item label="期間" class="date-picker-item">
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  range-separator="〜"
                  start-placeholder="開始日"
                  end-placeholder="終了日"
                  value-format="YYYY-MM-DD"
                  style="width: 280px"
                  @change="handleDateRangeChange"
                  class="modern-date-picker"
                />
              </el-form-item>
              <div class="button-group daily-buttons">
                <span class="group-label">日別:</span>
                <el-button
                  size="small"
                  @click="setQuickDate('yesterday')"
                  class="quick-btn yesterday-btn"
                >
                  <el-icon><ArrowLeft /></el-icon>
                  昨日
                </el-button>
                <el-button
                  size="small"
                  @click="setQuickDate('today')"
                  class="quick-btn today-btn"
                  type="primary"
                >
                  <el-icon><Calendar /></el-icon>
                  今日
                </el-button>
                <el-button
                  size="small"
                  @click="setQuickDate('tomorrow')"
                  class="quick-btn tomorrow-btn"
                >
                  明日
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>

              <div class="button-group monthly-buttons">
                <span class="group-label">月別:</span>
                <el-button
                  size="small"
                  @click="setQuickDate('lastMonth')"
                  class="quick-btn last-month-btn"
                >
                  <el-icon><ArrowLeft /></el-icon>
                  先月
                </el-button>
                <el-button
                  size="small"
                  @click="setQuickDate('thisMonth')"
                  class="quick-btn this-month-btn"
                  type="success"
                >
                  <el-icon><Calendar /></el-icon>
                  今月
                </el-button>
                <el-button
                  size="small"
                  @click="setQuickDate('nextMonth')"
                  class="quick-btn next-month-btn"
                >
                  来月
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
                <el-button
                  type="primary"
                  @click="refreshData"
                  :loading="loading.search"
                  class="search-btn"
                >
                  <el-icon><Search /></el-icon>
                  検索
                </el-button>
                <el-button @click="resetFilters" class="reset-btn">
                  <el-icon><RefreshRight /></el-icon>
                  リセット
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-form>
    </el-card>

    <!-- Modern Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card total-tasks">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><DataBoard /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ historyStats.totalTasks }}</div>
            <div class="stat-label">総ピッキング数</div>
          </div>
        </div>
        <div class="stat-decoration"></div>
      </div>

      <div class="stat-card pending-tasks">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ historyStats.pendingTasks }}</div>
            <div class="stat-label">総未ピッキング数</div>
          </div>
        </div>
        <div class="stat-decoration"></div>
      </div>

      <div class="stat-card completed-tasks">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ historyStats.completedTasks }}</div>
            <div class="stat-label">総ピッキング済数</div>
          </div>
        </div>
        <div class="stat-decoration"></div>
      </div>

      <div class="stat-card completion-rate">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ historyStats.completionRate }}%</div>
            <div class="stat-label">全体完了率</div>
          </div>
        </div>
        <div class="stat-decoration"></div>
      </div>
    </div>

    <!-- Modern Chart Card -->
    <el-card class="chart-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><TrendCharts /></el-icon>
            <span class="header-title">ピッキング進捗推移</span>
          </div>
          <div class="chart-controls">
            <el-button-group class="control-group">
              <el-button
                :type="trendGranularity === 'daily' ? 'primary' : 'default'"
                @click="changeGranularity('daily')"
                size="small"
              >
                日別
              </el-button>
              <el-button
                :type="trendGranularity === 'monthly' ? 'primary' : 'default'"
                @click="changeGranularity('monthly')"
                size="small"
              >
                月別
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>
      <div class="chart-container">
        <ChartWrapper
          v-if="!loading.trend"
          :data="trendChartData"
          :options="trendChartOptions"
          height="400px"
          @error="handleChartError"
          @retry="retryChart"
        />
        <div v-else class="chart-loading-placeholder">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <span>データ読み込み中...</span>
        </div>
      </div>
    </el-card>

    <!-- 担当者別納入先分析カード -->
    <el-card class="performer-analysis-card" shadow="never" v-auto-height>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><User /></el-icon>
            <span class="header-title">担当者別納入先分析</span>
          </div>
          <div class="chart-controls">
            <div class="performer-controls-row">
              <!-- 日付選択を前に配置 -->
              <div class="performer-date-controls">
                <el-form-item label="期間" class="date-picker-item">
                  <el-date-picker
                    v-model="performerDateRange"
                    type="daterange"
                    range-separator="〜"
                    start-placeholder="開始日"
                    end-placeholder="終了日"
                    value-format="YYYY-MM-DD"
                    style="width: 240px; margin-right: 12px"
                    @change="handlePerformerDateChange"
                    class="performer-date-picker"
                    size="small"
                    popper-class="custom-date-picker-popper"
                  />
                </el-form-item>
                <el-form-item label="担当者" class="date-picker-item">
                  <el-select
                    v-model="selectedGroups"
                    multiple
                    placeholder="担当者を選択"
                    style="width: 200px"
                    collapse-tags
                    collapse-tags-tooltip
                    @change="handleGroupChange"
                    class="group-selector"
                    size="small"
                    popper-class="custom-group-selector-popper"
                  >
                    <el-option label="全ての担当者" value="all" />
                    <el-option
                      v-for="user in performerOptionsWithFixed"
                      :key="user.username"
                      :label="user.name"
                      :value="user.name"
                    />
                  </el-select>
                </el-form-item>
              </div>

              <!-- 快捷日期選択ボタン -->
              <div class="performer-quick-date-section">
                <div class="performer-quick-date-buttons">
                  <div class="performer-date-group">
                    <el-button
                      size="small"
                      class="performer-quick-btn yesterday-btn"
                      @click="setPerformerQuickDate('yesterday')"
                    >
                      <el-icon><ArrowLeft /></el-icon>
                      昨日
                    </el-button>
                    <el-button
                      size="small"
                      type="primary"
                      class="performer-quick-btn today-btn"
                      @click="setPerformerQuickDate('today')"
                    >
                      <el-icon><Calendar /></el-icon>
                      今日
                    </el-button>
                    <el-button
                      size="small"
                      class="performer-quick-btn tomorrow-btn"
                      @click="setPerformerQuickDate('tomorrow')"
                    >
                      明日
                      <el-icon><ArrowRight /></el-icon>
                    </el-button>
                  </div>
                  <div class="performer-month-group">
                    <el-button
                      size="small"
                      class="performer-quick-btn last-month-btn"
                      @click="setPerformerQuickDate('lastMonth')"
                    >
                      先月
                    </el-button>
                    <el-button
                      size="small"
                      type="success"
                      class="performer-quick-btn this-month-btn"
                      @click="setPerformerQuickDate('thisMonth')"
                    >
                      今月
                    </el-button>
                    <el-button
                      size="small"
                      class="performer-quick-btn next-month-btn"
                      @click="setPerformerQuickDate('nextMonth')"
                    >
                      来月
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <div class="chart-container" v-loading="loading.performerAnalysis" v-auto-height>
        <div v-if="!loading.performerAnalysis" class="performer-list-view" v-auto-height>
          <div class="performer-list" v-auto-height>
            <div
              v-for="performer in filteredPerformerData"
              :key="performer.performer_id"
              class="performer-list-item"
              v-auto-height
            >
              <div
                class="performer-list-header"
                @click="togglePerformerExpansion(performer.performer_id)"
              >
                <div class="performer-avatar">
                  <el-icon><User /></el-icon>
                </div>
                <div class="performer-summary">
                  <div class="performer-name">{{ performer.performer_name }}</div>
                  <div class="performer-group">担当者: {{ performer.performer_id }}</div>
                </div>
                <div class="performer-stats">
                  <div class="stat-item">
                    <span class="stat-label">納入先</span>
                    <span class="stat-value">{{ performer.destination_count }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">総ピッキング</span>
                    <span class="stat-value">{{ getTotalTasks(performer) }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">完了率</span>
                    <span class="stat-value">{{ getCompletionRate(performer) }}%</span>
                  </div>
                </div>
                <div
                  class="expand-icon"
                  :class="{ expanded: expandedPerformers.includes(performer.performer_id) }"
                >
                  <el-icon><ArrowDown /></el-icon>
                </div>
              </div>

              <div
                v-if="expandedPerformers.includes(performer.performer_id)"
                class="performer-destinations"
                v-auto-height
              >
                <div class="destinations-header">
                  <span class="destinations-title">担当者別納入先一覧</span>
                  <div class="destinations-filter">
                    <!-- <el-select
                      v-model="destinationStatusFilter[performer.performer_id]"
                      placeholder="状態で絞り込み"
                      size="small"
                      style="width: 140px"
                      @change="filterDestinationsByStatus(performer.performer_id)"
                      popper-class="custom-destination-status-popper"
                    >
                      <el-option label="全て" value="" />
                      <el-option label="完了" value="completed" />
                      <el-option label="待機" value="pending" />
                    </el-select> -->
                  </div>
                </div>

                <div class="destinations-list" v-auto-height>
                  <div
                    v-for="destination in getFilteredDestinations(performer)"
                    :key="destination.destination_cd"
                    class="destination-list-item"
                    v-auto-height
                  >
                    <div class="destination-header">
                      <div class="destination-name">{{ destination.destination_name }}</div>
                      <div class="destination-code">{{ destination.destination_cd }}</div>
                    </div>
                    <div class="destination-stats">
                      <div class="stat-row">
                        <span class="label">総タスク数</span>
                        <span class="value">{{ destination.total_tasks }}</span>
                      </div>
                      <div class="stat-row">
                        <span class="label">完了数</span>
                        <span class="value">{{ destination.completed_tasks }}</span>
                      </div>
                      <div class="stat-row">
                        <span class="label">完了率</span>
                        <span class="value">{{ destination.completion_rate }}%</span>
                      </div>
                    </div>
                    <div class="destination-status">
                      <el-tag :type="getDestinationStatusType(destination)" size="small">
                        {{ getDestinationStatusText(destination) }}
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <el-empty
          v-if="!loading.performerAnalysis && filteredPerformerData.length === 0"
          description="担当者データがありません"
        />
      </div>
    </el-card>

    <!-- 担当者每天完成率折线图 -->
    <el-card class="daily-rate-chart-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><TrendCharts /></el-icon>
            <span class="header-title">担当者別日次完了率</span>
          </div>
        </div>
      </template>
      <div class="chart-container">
        <ChartWrapper
          v-if="!loading.trend"
          :data="dailyCompletionRateChartData as any"
          :options="dailyCompletionRateChartOptions as any"
          height="320px"
          @error="handleChartError"
          @retry="retryChart"
        />
        <div v-else class="chart-loading-placeholder">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <span>データ読み込み中...</span>
        </div>
      </div>
    </el-card>

    <!-- Task Detail Dialog -->
    <!-- <el-dialog
      v-model="taskDetailVisible"
      title="タスク詳細"
      width="600px"
      class="task-detail-dialog"
    >
      <el-descriptions v-if="selectedTask" :column="2" border>
        <el-descriptions-item label="ピッキングID">
          <span class="detail-value">{{ selectedTask.picking_id }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="ピッキングNo">
          <span class="detail-value">{{ selectedTask.shipping_no }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="製品CD">
          <span class="detail-value">{{ selectedTask.product_cd }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="製品名">
          <span class="detail-value">{{ selectedTask.product_name }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="確定箱数">
          <span class="detail-value">{{ selectedTask.confirmed_boxes }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="ピッキング数量">
          <span class="detail-value">{{ selectedTask.picked_quantity || 0 }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="保管場所">
          <span class="detail-value">{{ selectedTask.location_cd }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="担当者">
          <span class="detail-value">{{ selectedTask.picker_name || selectedTask.picker_id }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="状態">
          <el-tag :type="getStatusTagType(selectedTask.status)">
            {{ getStatusText(selectedTask.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="作業時間" v-if="selectedTask.work_time">
          <span class="detail-value">{{ selectedTask.work_time }}分</span>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="taskDetailVisible = false" class="close-dialog-btn">
            <el-icon><Close /></el-icon>
            閉じる
          </el-button>
        </div>
      </template>
    </el-dialog> -->

    <!-- 納入先グループ管理ダイアログ -->
    <DestinationGroupManager
      v-model="showGroupManager"
      page-key="picking_history"
      @groups-updated="handleGroupsUpdated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, reactive } from 'vue'
import { safeOnMounted } from '@/utils/lifecycleFix'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis,
  Filter,
  Search,
  Refresh,
  RefreshRight,
  DataBoard,
  Clock,
  CircleCheck,
  TrendCharts,
  User,
  ArrowDown,
  Setting,
  Calendar,
  ArrowLeft,
  ArrowRight,
  Loading,
} from '@element-plus/icons-vue'
import { getPickingHistoryData, getPerformanceByDestination } from '@/api/shipping/picking'
import request from '@/utils/request'
import DestinationGroupManager from './DestinationGroupManager.vue'
import ChartWrapper from '@/components/ChartWrapper.vue'
import { registerChartJS, type ChartData, type ChartOptions } from '@/utils/chartRegistration'

// 确保Chart.js组件在生产环境中正确注册
registerChartJS()

// Interfaces
interface PickingTask {
  shipping_no_p: string
  picking_id: string
  shipping_no: string
  shipping_date?: string
  product_cd: string
  product_name: string
  confirmed_boxes: number
  picked_quantity: number
  location_cd: string
  destination_cd?: string
  destination_name?: string
  status: string
  picker_id: string
  picker_name: string
  start_time?: string
  complete_time?: string
  work_time?: number
  created_at?: string
}

interface TrendDataPoint {
  date: string
  total: number
  completed: number
}

interface HistoryStats {
  totalTasks: number
  completedTasks: number
  pendingTasks: number
  completionRate: number
}

// Reactive data
const loading = ref({
  search: false,
  pendingTasks: false,
  completedTasks: false,
  trend: false,
  performerAnalysis: false,
})

// 图表错误处理
const chartError = ref<string>('')

const filters = ref({})

// Date utilities
const getJapanDate = (date?: Date): Date => {
  const targetDate = date || new Date()
  return new Date(targetDate.toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }))
}

const formatDateString = (date: Date): string => {
  // 转换为日本时区
  const jstDate = new Date(
    date.getTime() + 9 * 60 * 60 * 1000 - date.getTimezoneOffset() * 60 * 1000,
  )
  return (
    jstDate.getFullYear() +
    '-' +
    String(jstDate.getMonth() + 1).padStart(2, '0') +
    '-' +
    String(jstDate.getDate()).padStart(2, '0')
  )
}

const getCurrentMonthRange = (): [string, string] => {
  const japanTime = getJapanDate()
  const year = japanTime.getFullYear()
  const month = japanTime.getMonth()

  const firstDay = new Date(year, month, 1)
  const firstDayStr = formatDateString(firstDay)

  const lastDay = new Date(year, month + 1, 0)
  const lastDayStr = formatDateString(lastDay)

  return [firstDayStr, lastDayStr]
}

const dateRange = ref<[string, string]>(getCurrentMonthRange())

// Data state
const historyStats = reactive<HistoryStats>({
  totalTasks: 0,
  completedTasks: 0,
  pendingTasks: 0,
  completionRate: 0,
})

const pendingTasks = ref<PickingTask[]>([])
const completedTasks = ref<PickingTask[]>([])

// Chart related
const trendGranularity = ref<'daily' | 'monthly'>('daily')
const trendData = ref<TrendDataPoint[]>([])
const rawTrendTasks = ref<PickingTask[]>([])

// 担当者分析関連
interface GroupOption {
  id: string
  group_name: string
  destinations: any[]
}

interface DestinationData {
  destination_cd: string
  destination_name: string
  total_tasks: number
  completed_tasks: number
  completed_from_status?: number
  completion_rate: number
  status?: string
  last_updated?: string
}

interface PerformerAnalysisData {
  performer_id: string
  performer_name: string
  destination_count: number
  completion_rate: number
  total_tasks?: number
  completed_tasks?: number
  last_activity: string
  destinations: DestinationData[]
}

// 担当者＝納入先グループ（destination_groups 的 group_name），每个担当者＝一组納入先，按该组+日期在 picking_tasks 上汇总
const FIXED_GROUP_NAMES = ['福島', '青山', '小森']
const performerOptionsWithFixed = computed(() => {
  const fromGroups = (groupOptions.value || []).map((g) => ({
    username: g.group_name,
    name: g.group_name,
  }))
  const existing = new Set(fromGroups.map((u) => u.username))
  const fixed = FIXED_GROUP_NAMES.filter((n) => !existing.has(n)).map((n) => ({
    username: n,
    name: n,
  }))
  return [...fixed, ...fromGroups]
})

const groupOptions = ref<GroupOption[]>([])
const selectedGroups = ref<string[]>(['all'])
const performerAnalysisData = ref<PerformerAnalysisData[]>([])
const expandedPerformers = ref<string[]>([])
const destinationStatusFilter = ref<Record<string, string>>({})
const performerDateRange = ref<[string, string]>(getCurrentMonthRange())

// 納入先グループ管理関連
const showGroupManager = ref(false)

// 担当者チャート表示関連（将来のテンプレート用に保留）
const _performerViewMode = ref<'chart' | 'list'>('chart')

// 担当者分析関連のcomputed（不显示担当者为空的数据；选具体担当者时按 performer_name 过滤）
const filteredPerformerData = computed(() => {
  const list = performerAnalysisData.value.filter(
    (p) => (p.performer_id || '').trim() !== '' || (p.performer_name || '').trim() !== '',
  )
  if (selectedGroups.value.includes('all') || selectedGroups.value.length === 0) {
    return list
  }
  return list.filter((performer) => selectedGroups.value.includes(performer.performer_name))
})

// 担当者チャート用の計算プロパティ（将来のテンプレート用に保留）
const _performerBarChartData = computed<ChartData<'bar' | 'line'>>(() => {
  const performers = filteredPerformerData.value
  const labels = performers.map((p) => p.performer_name)

  // 納入先件数
  const destinationCounts = performers.map((p) => p.destination_count || 0)

  // 総ピッキング件数：グループ名里含有的納入先在picking_tasks表里shipping_no_p字段的件数
  const _totalTasks = performers.map((p) => p.total_tasks || 0)

  // ピッキング済件数：グループ名里含有的納入先在picking_tasks表里status字段为completed的件数
  const _completedTasks = performers.map((p) => p.completed_tasks || 0)

  // 完了率：ピッキング済件数/総ピッキング件数
  const completionRates = performers.map((p) => p.completion_rate || 0)

  return {
    labels,
    datasets: [
      {
        label: '納入先件数',
        data: destinationCounts,
        backgroundColor: 'rgba(168, 85, 247, 0.8)',
        borderColor: 'rgba(168, 85, 247, 1)',
        borderWidth: 1,
        yAxisID: 'y',
      },
      {
        label: '総ピッキング件数',
        data: _totalTasks,
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
        yAxisID: 'y',
      },
      {
        label: 'ピッキング済件数',
        data: _completedTasks,
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 1,
        yAxisID: 'y',
      },
      {
        label: '完了率 (%)',
        data: completionRates,
        backgroundColor: 'rgba(245, 158, 11, 0.8)',
        borderColor: 'rgba(245, 158, 11, 1)',
        borderWidth: 1,
        yAxisID: 'y1',
        type: 'line',
        tension: 0.3,
        pointRadius: 4,
        pointBackgroundColor: '#ffffff',
        pointBorderColor: '#f59e0b',
        pointBorderWidth: 2,
        fill: false,
      },
    ],
  }
})

const _performerBarChartOptions = computed<ChartOptions<'bar' | 'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  plugins: {
    legend: {
      display: true,
      position: 'top',
    },
    tooltip: {
      callbacks: {
        label: function (context) {
          let label = context.dataset.label || ''
          if (label) {
            label += ': '
          }
          if (context.parsed.y !== null) {
            if (context.dataset.label === '完了率 (%)') {
              label += context.parsed.y + '%'
            } else {
              label += context.parsed.y
            }
          }
          return label
        },
      },
    },
    // 自定义插件：在完了率折线上显示数据标签
    customDatalabels: {
      id: 'customDatalabels',
      afterDraw: function (chart: any) {
        const ctx = chart.ctx
        const meta = chart.getDatasetMeta(2) // 完了率是第3个数据集

        if (meta && meta.data) {
          meta.data.forEach((point: any, index: number) => {
            const performers = filteredPerformerData.value
            const value = performers[index]?.completion_rate
            if (value !== null && value !== undefined) {
              const x = point.x
              const y = point.y - 10 // 向上偏移

              ctx.save()
              ctx.fillStyle = '#f59e0b'
              ctx.font = '10px Arial'
              ctx.textAlign = 'center'
              ctx.textBaseline = 'bottom'
              ctx.fillText(value + '%', x, y)
              ctx.restore()
            }
          })
        }
      },
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
    },
    y: {
      type: 'linear',
      display: true,
      position: 'left',
      title: {
        display: true,
        text: 'タスク数',
      },
      grid: {
        color: '#f1f5f9',
      },
      beginAtZero: true,
    },
    y1: {
      type: 'linear',
      display: true,
      position: 'right',
      title: {
        display: true,
        text: '完了率 (%)',
      },
      grid: {
        drawOnChartArea: false,
      },
      max: 100,
      beginAtZero: true,
    },
  },
}))

const _performerRadarChartData = computed<ChartData<'radar'>>(() => {
  const performers = filteredPerformerData.value.slice(0, 5) // 最大5人まで表示
  const labels = ['完了率', '納入先数', '効率性', '品質', '安定性']

  const datasets = performers.map((performer, index) => {
    const completionRate = performer.completion_rate || 0
    const destinationCount = performer.destination_count || 0

    // 正規化されたスコア（0-100）
    const efficiency = Math.min(100, completionRate) // 完了率をそのまま効率性として使用
    const quality = Math.min(100, completionRate)
    const stability = Math.min(100, destinationCount * 10) // 納入先数に基づく安定性

    const colors = [
      'rgba(59, 130, 246, 0.6)',
      'rgba(34, 197, 94, 0.6)',
      'rgba(245, 158, 11, 0.6)',
      'rgba(239, 68, 68, 0.6)',
      'rgba(139, 92, 246, 0.6)',
    ]

    return {
      label: performer.performer_name,
      data: [completionRate, destinationCount * 5, efficiency, quality, stability],
      backgroundColor: colors[index % colors.length],
      borderColor: colors[index % colors.length].replace('0.6', '1'),
      borderWidth: 2,
      pointBackgroundColor: colors[index % colors.length].replace('0.6', '1'),
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: colors[index % colors.length].replace('0.6', '1'),
    }
  })

  return {
    labels,
    datasets,
  }
})

const _performerRadarChartOptions = computed<ChartOptions<'radar'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top',
    },
    tooltip: {
      callbacks: {
        label: function (context) {
          const label = context.dataset.label || ''
          const value = context.parsed.r
          const dataIndex = context.dataIndex

          let unit = ''
          if (dataIndex === 0)
            unit = '%' // 完了率
          else if (dataIndex === 1)
            unit = '件' // 納入先数（正規化前）
          else unit = 'pt' // その他のスコア

          return `${label}: ${value.toFixed(1)}${unit}`
        },
      },
    },
  },
  scales: {
    r: {
      beginAtZero: true,
      max: 100,
      grid: {
        color: '#f1f5f9',
      },
      pointLabels: {
        font: {
          size: 12,
        },
      },
      ticks: {
        stepSize: 20,
        font: {
          size: 10,
        },
      },
    },
  },
}))

// 統計サマリー用の計算プロパティ（テンプレートで未使用のため _ 接頭辞）
const _totalPickingTasks = computed(() => {
  return filteredPerformerData.value.reduce((sum, performer) => {
    return sum + (performer.total_tasks || 0)
  }, 0)
})

const _averageCompletionRate = computed(() => {
  const performers = filteredPerformerData.value
  if (performers.length === 0) return 0

  const totalRate = performers.reduce((sum, performer) => sum + performer.completion_rate, 0)
  return Math.round(totalRate / performers.length)
})

const trendChartData = computed<ChartData<'bar' | 'line'>>(() => {
  const labels = trendData.value.map((d) => d.date)
  const totalTasks = trendData.value.map((d) => d.total)
  const completedTasks = trendData.value.map((d) => d.completed)
  const completionRates = trendData.value.map(
    (d) => (d.total > 0 ? Number(((d.completed / d.total) * 100).toFixed(1)) : 50), // 默认50%而不是0
  )

  return {
    labels,
    datasets: [
      {
        type: 'bar',
        label: '総ピッキング数',
        data: totalTasks,
        backgroundColor: 'rgba(99, 102, 241, 0.8)',
        borderColor: 'rgba(99, 102, 241, 1)',
        borderWidth: 1,
        yAxisID: 'y',
      },
      {
        type: 'bar',
        label: '総ピッキング済数',
        data: completedTasks,
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 1,
        yAxisID: 'y',
      },
      {
        type: 'line',
        label: '完了率 (%)',
        data: completionRates,
        borderColor: '#f59e0b',
        backgroundColor: '#f59e0b',
        tension: 0.3,
        yAxisID: 'y1',
        pointRadius: 4,
        pointBackgroundColor: '#ffffff',
        pointBorderColor: '#f59e0b',
        pointBorderWidth: 2,
        fill: false,
        spanGaps: true,
        // 添加数据标签
        pointHoverRadius: 6,
        pointHoverBorderWidth: 3,
      },
    ],
  }
}) as any

const trendChartOptions = computed<ChartOptions<'bar' | 'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  scales: {
    x: {
      stacked: false,
      grid: {
        display: false,
      },
    },
    y: {
      type: 'linear',
      display: true,
      position: 'left',
      title: {
        display: true,
        text: 'タスク数',
      },
      grid: {
        color: '#f1f5f9',
      },
      // 动态设置最大值，为当前数据的2倍，确保折线图不被覆盖
      max: computed(() => {
        if (trendData.value.length === 0) return 100
        const maxValue = Math.max(
          ...trendData.value.map((d) => d.total),
          ...trendData.value.map((d) => d.completed),
        )
        return maxValue * 2
      }).value,
    },
    y1: {
      type: 'linear',
      display: true,
      position: 'right',
      title: {
        display: true,
        text: '完了率 (%)',
      },
      grid: {
        drawOnChartArea: false,
      },
      max: 120,
    },
  },
  plugins: {
    tooltip: {
      callbacks: {
        label: function (context) {
          let label = context.dataset.label || ''
          if (label) {
            label += ': '
          }
          if (context.parsed.y !== null) {
            if (context.dataset.label === '完了率 (%)') {
              label += context.parsed.y + '%'
            } else {
              label += context.parsed.y
            }
          }
          return label
        },
      },
    },
    legend: {
      display: true,
      position: 'top',
      labels: {
        usePointStyle: true,
        padding: 20,
        font: {
          size: 12,
        },
      },
    },
    // 完了率折线上的数值由 chartRegistration 的 completionRateDatalabels 插件统一绘制
  },
}))

// 担当者別日次完了率（折线图）：按日期 + 各グループ的納入先在 rawTrendTasks 上汇总
function getTaskDateKey(task: PickingTask): string {
  return task.shipping_date
    ? task.shipping_date.split('T')[0]
    : task.created_at
      ? task.created_at.split('T')[0]
      : formatDateString(getJapanDate())
}

function getGroupDestinationCds(group: GroupOption): string[] {
  const dests = group.destinations || []
  return dests
    .map((d: any) => (typeof d === 'object' && d && 'value' in d ? String(d.value) : String(d)))
    .filter(Boolean)
}

const dailyCompletionRateChartData = computed<ChartData<'line'>>(() => {
  const tasks = rawTrendTasks.value
  const groups = groupOptions.value || []
  if (tasks.length === 0 || groups.length === 0) {
    return { labels: [], datasets: [] }
  }
  const dateSet = new Set<string>()
  tasks.forEach((t) => dateSet.add(getTaskDateKey(t)))
  const sortedDates = Array.from(dateSet).sort()
  const rateByDateAndGroup: Record<string, Record<string, number>> = {}
  sortedDates.forEach((d) => {
    rateByDateAndGroup[d] = {}
  })
  groups.forEach((group) => {
    const destCds = new Set(getGroupDestinationCds(group))
    if (destCds.size === 0) return
    sortedDates.forEach((date) => {
      const dayTasks = tasks.filter(
        (t) => getTaskDateKey(t) === date && destCds.has((t.destination_cd || '').trim()),
      )
      const palletMap = new Map<string, string[]>()
      dayTasks.forEach((t) => {
        const key = t.shipping_no_p || t.shipping_no || ''
        if (!key) return
        if (!palletMap.has(key)) palletMap.set(key, [])
        palletMap.get(key)!.push(t.status || 'pending')
      })
      let total = 0
      let completed = 0
      palletMap.forEach((statuses) => {
        total++
        if (statuses.every((s) => s === 'completed' || s === 'picked')) completed++
      })
      const rate = total > 0 ? Number(((completed / total) * 100).toFixed(1)) : 0
      rateByDateAndGroup[date][group.group_name] = rate
    })
  })
  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6']
  const datasets = groups.map((g, i) => ({
    type: 'line' as const,
    label: g.group_name,
    data: sortedDates.map((d) => rateByDateAndGroup[d]?.[g.group_name] ?? null),
    borderColor: colors[i % colors.length],
    backgroundColor: colors[i % colors.length],
    tension: 0.3,
    fill: false,
    pointRadius: 4,
    spanGaps: true,
  }))
  return { labels: sortedDates, datasets }
})

const dailyCompletionRateChartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  scales: {
    x: { grid: { display: false } },
    y: {
      type: 'linear',
      min: 0,
      max: 110,
      title: { display: true, text: '完了率 (%)' },
      grid: { color: '#f1f5f9' },
    },
  },
  plugins: {
    legend: { display: true, position: 'top' },
    tooltip: {
      callbacks: {
        label: (ctx: any) => {
          const v = ctx.parsed?.y
          return v != null ? `${ctx.dataset.label}: ${v}%` : ''
        },
      },
    },
  },
}))

// Methods
async function fetchHistoryStats() {
  loading.value.search = true
  try {
    const params = {
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      page: 1,
      limit: 10000,
    }

    console.log('📊 履歴統計データ取得開始:', params)
    const response = await getPickingHistoryData(params)
    console.log('📊 履歴統計データ取得結果:', response)

    const data = response?.data ?? response

    if (data) {
      // 后端 GET /api/shipping/picking/history 返回 { statistics, items }，任务列表在 items
      const allTasks = Array.isArray(data.items)
        ? data.items
        : Array.isArray(data.tasks)
          ? data.tasks
          : Array.isArray(data)
            ? data
            : []
      if (Array.isArray(allTasks) && allTasks.length > 0) {
        // 过滤掉产品名包含特定关键词的数据（与 PickingListGenerator / 進捗管理 一致）
        const excludeKeywords = ['加工', 'アーチ', '料金']
        const filteredTasks = allTasks.filter((task) => {
          const productName = task.product_name || ''
          return !excludeKeywords.some((keyword) => productName.includes(keyword))
        })

        // 按 shipping_no_p（パレット）分组，托盘状态与 PickingListGenerator 一致：
        // 全部 completed → completed；任一 picking → picking；否则 pending
        const palletGroups = new Map<string, { statuses: string[] }>()
        for (const task of filteredTasks) {
          const key = task.shipping_no_p || task.shipping_no || ''
          if (!key) continue
          if (!palletGroups.has(key)) palletGroups.set(key, { statuses: [] })
          palletGroups.get(key)!.statuses.push(task.status || 'pending')
        }
        let totalTasks = 0
        let pendingTasksCount = 0
        let completedTasksCount = 0
        palletGroups.forEach(({ statuses }) => {
          const allCompleted = statuses.every((s) => s === 'completed' || s === 'picked')
          const anyPicking = statuses.some((s) => s === 'picking')
          totalTasks++
          if (allCompleted) completedTasksCount++
          else if (anyPicking) pendingTasksCount++
          else pendingTasksCount++
        })

        // 更新统计数据（按托盘数）
        historyStats.totalTasks = totalTasks
        historyStats.completedTasks = completedTasksCount
        historyStats.pendingTasks = pendingTasksCount
        historyStats.completionRate =
          totalTasks > 0 ? Number(((completedTasksCount / totalTasks) * 100).toFixed(1)) : 0

        // 任务列表仍按行展示：未ピッキング = pending + picking 行，完了 = completed 行
        pendingTasks.value = filteredTasks.filter(
          (task) =>
            task.status === 'pending' || task.status === 'picking' || task.status === 'assigned',
        )
        completedTasks.value = filteredTasks.filter(
          (task) => task.status === 'completed' || task.status === 'picked',
        )

        console.log('📊 更新後の統計データ:', historyStats)
        console.log('📊 按パレット(shipping_no_p)统计（与ピッキングリスト一致）:', {
          totalTasks,
          completedTasksCount,
          pendingTasksCount,
        })
      } else {
        resetStats()
      }

      await nextTick()
    } else {
      console.warn('📊 履歴統計データが空です:', data)
      resetStats()
      ElMessage.warning('履歴統計データが取得できませんでした')
    }
  } catch (error) {
    console.error('履歴統計取得エラー:', error)
    ElMessage.error('履歴統計の取得に失敗しました')
    resetStats()
  } finally {
    loading.value.search = false
  }
}

function resetStats() {
  historyStats.totalTasks = 0
  historyStats.completedTasks = 0
  historyStats.pendingTasks = 0
  historyStats.completionRate = 0
  pendingTasks.value = []
  completedTasks.value = []
}

function generateTrendDataFromTasks(tasks: PickingTask[]): TrendDataPoint[] {
  const data: TrendDataPoint[] = []

  // 过滤掉产品名包含特定关键词的数据
  const excludeKeywords = ['加工', 'アーチ', '料金']
  const filteredTasks = tasks.filter((task) => {
    const productName = task.product_name || ''
    return !excludeKeywords.some((keyword) => productName.includes(keyword))
  })

  // 按日期/月分组，再按 shipping_no_p 判定托盘状态（与 PickingListGenerator 一致）
  const getDateKey = (task: PickingTask) =>
    task.shipping_date
      ? task.shipping_date.split('T')[0]
      : task.created_at
        ? task.created_at.split('T')[0]
        : formatDateString(getJapanDate())

  if (trendGranularity.value === 'daily') {
    // 按日期 → shipping_no_p 分组，每个托盘状态：全部 completed → completed，否则任一 picking → picking，否则 pending
    const dailyPallets: Record<string, Map<string, string[]>> = {}
    filteredTasks.forEach((task) => {
      const date = getDateKey(task)
      if (!dailyPallets[date]) dailyPallets[date] = new Map()
      const key = task.shipping_no_p || task.shipping_no || ''
      if (!key) return
      if (!dailyPallets[date].has(key)) dailyPallets[date].set(key, [])
      dailyPallets[date].get(key)!.push(task.status || 'pending')
    })
    Object.entries(dailyPallets).forEach(([date, palletMap]) => {
      let total = 0
      let completed = 0
      palletMap.forEach((statuses) => {
        total++
        if (statuses.every((s) => s === 'completed' || s === 'picked')) completed++
      })
      data.push({ date, total, completed })
    })
  } else {
    const monthlyPallets: Record<string, Map<string, string[]>> = {}
    filteredTasks.forEach((task) => {
      const date = getDateKey(task)
      const month = date.substring(0, 7)
      if (!monthlyPallets[month]) monthlyPallets[month] = new Map()
      const key = task.shipping_no_p || task.shipping_no || ''
      if (!key) return
      if (!monthlyPallets[month].has(key)) monthlyPallets[month].set(key, [])
      monthlyPallets[month].get(key)!.push(task.status || 'pending')
    })
    Object.entries(monthlyPallets).forEach(([month, palletMap]) => {
      let total = 0
      let completed = 0
      palletMap.forEach((statuses) => {
        total++
        if (statuses.every((s) => s === 'completed' || s === 'picked')) completed++
      })
      data.push({ date: month, total, completed })
    })
  }

  // 按日期排序
  return data.sort((a, b) => a.date.localeCompare(b.date))
}

async function fetchTrendData() {
  loading.value.trend = true
  try {
    const params = {
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      page: 1,
      limit: 10000,
    }

    const response = await getPickingHistoryData(params)
    const data = response?.data ?? response
    const allTasks = Array.isArray(data?.items)
      ? data.items
      : Array.isArray(data?.tasks)
        ? data.tasks
        : Array.isArray(data)
          ? data
          : []

    const excludeKeywords = ['加工', 'アーチ', '料金']
    const filtered = (allTasks as PickingTask[]).filter((task: PickingTask) => {
      const productName = task.product_name || ''
      return !excludeKeywords.some((keyword: string) => productName.includes(keyword))
    })
    trendData.value = generateTrendDataFromTasks(filtered)
    rawTrendTasks.value = filtered
  } catch (error) {
    console.error('❌ トレンドデータ取得エラー:', error)
    ElMessage.error('トレンドデータの取得に失敗しました')
    trendData.value = []
    rawTrendTasks.value = []
  } finally {
    loading.value.trend = false
  }
}

function handleDateRangeChange() {
  if (dateRange.value && dateRange.value.length === 2) {
    refreshData()
  }
}

function resetFilters() {
  dateRange.value = getCurrentMonthRange()
  refreshData()
}

function changeGranularity(granularity: 'daily' | 'monthly') {
  trendGranularity.value = granularity
  fetchTrendData()
}

// 图表错误处理方法
function handleChartError(error: any) {
  console.error('Chart error:', error)
  chartError.value = 'チャートの表示中にエラーが発生しました。再試行してください。'
}

// 重试图表加载
function retryChart() {
  chartError.value = ''
  fetchTrendData()
}

function refreshData() {
  fetchHistoryStats()
  fetchTrendData()
}

// 快捷日期设置函数
function setQuickDate(type: string) {
  const japanTime = getJapanDate()
  let startDate: Date
  let endDate: Date

  switch (type) {
    case 'yesterday': // 昨日
      startDate = new Date(japanTime)
      startDate.setDate(startDate.getDate() - 1)
      endDate = new Date(startDate)
      break

    case 'today': // 今日
      startDate = new Date(japanTime)
      endDate = new Date(startDate)
      break

    case 'tomorrow': // 明日
      startDate = new Date(japanTime)
      startDate.setDate(startDate.getDate() + 1)
      endDate = new Date(startDate)
      break

    case 'lastMonth': // 先月
      startDate = new Date(japanTime.getFullYear(), japanTime.getMonth() - 1, 1)
      endDate = new Date(japanTime.getFullYear(), japanTime.getMonth(), 0)
      break

    case 'thisMonth': // 今月
      startDate = new Date(japanTime.getFullYear(), japanTime.getMonth(), 1)
      endDate = new Date(japanTime.getFullYear(), japanTime.getMonth() + 1, 0)
      break

    case 'nextMonth': // 来月
      startDate = new Date(japanTime.getFullYear(), japanTime.getMonth() + 1, 1)
      endDate = new Date(japanTime.getFullYear(), japanTime.getMonth() + 2, 0)
      break

    default:
      return
  }

  // 设置日期范围
  dateRange.value = [formatDateString(startDate), formatDateString(endDate)]

  // 刷新数据
  refreshData()

  // 显示提示信息
  const dateTypeMap: Record<string, string> = {
    yesterday: '昨日',
    today: '今日',
    tomorrow: '明日',
    lastMonth: '先月',
    thisMonth: '今月',
    nextMonth: '来月',
  }

  ElMessage.success(`${dateTypeMap[type]}の期間に設定しました`)
}

// 担当者分析用の快捷日期設置関数
function setPerformerQuickDate(type: string) {
  const japanTime = getJapanDate()
  let startDate: Date
  let endDate: Date

  switch (type) {
    case 'yesterday': // 昨日
      startDate = new Date(japanTime)
      startDate.setDate(startDate.getDate() - 1)
      endDate = new Date(startDate)
      break

    case 'today': // 今日
      startDate = new Date(japanTime)
      endDate = new Date(startDate)
      break

    case 'tomorrow': // 明日
      startDate = new Date(japanTime)
      startDate.setDate(startDate.getDate() + 1)
      endDate = new Date(startDate)
      break

    case 'lastMonth': // 先月
      startDate = new Date(japanTime.getFullYear(), japanTime.getMonth() - 1, 1)
      endDate = new Date(japanTime.getFullYear(), japanTime.getMonth(), 0)
      break

    case 'thisMonth': // 今月
      startDate = new Date(japanTime.getFullYear(), japanTime.getMonth(), 1)
      endDate = new Date(japanTime.getFullYear(), japanTime.getMonth() + 1, 0)
      break

    case 'nextMonth': // 来月
      startDate = new Date(japanTime.getFullYear(), japanTime.getMonth() + 1, 1)
      endDate = new Date(japanTime.getFullYear(), japanTime.getMonth() + 2, 0)
      break

    default:
      return
  }

  // 担当者分析用の日期範囲を設定
  performerDateRange.value = [formatDateString(startDate), formatDateString(endDate)]

  // 担当者分析データを刷新
  fetchPerformerAnalysisData()

  // 提示信息を表示
  const dateTypeMap: Record<string, string> = {
    yesterday: '昨日',
    today: '今日',
    tomorrow: '明日',
    lastMonth: '先月',
    thisMonth: '今月',
    nextMonth: '来月',
  }

  ElMessage.success(`担当者分析: ${dateTypeMap[type]}の期間に設定しました`)
}

function getStatusTagType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  const typeMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    completed: 'success',
    picked: 'success',
    picking: 'warning',
    pending: 'info',
    assigned: 'info',
    shortage: 'danger',
  }
  return typeMap[status] || 'info'
}

function getStatusText(status: string): string {
  const textMap: Record<string, string> = {
    completed: '完了',
    picked: 'ピッキング済',
    picking: 'ピッキング中',
    pending: '待機中',
    assigned: '割当済',
    shortage: '不足',
  }
  return textMap[status] || status
}

function formatDateTime(dateStr?: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return new Intl.DateTimeFormat('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function _formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return new Intl.DateTimeFormat('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date)
}

// 担当者＝納入先グループ（group_name）。groupOptions 由 fetchGroupOptions 从 destination-groups/picking_history 取得
// グループ分析関連の関数
async function fetchGroupOptions() {
  try {
    const res = await request.get('/api/shipping/destination-groups/picking_history')
    const responseData = (res as any)?.data ?? res

    let data = null
    if (responseData && responseData.success === true && Array.isArray(responseData.data)) {
      data = responseData.data
    } else if (Array.isArray(responseData)) {
      data = responseData
    } else if (responseData && Array.isArray(responseData.data)) {
      data = responseData.data
    }

    if (data && Array.isArray(data)) {
      groupOptions.value = data.map((group: any) => ({
        id: group.id,
        group_name: group.group_name,
        destinations: group.destinations || [],
      }))
    } else {
      groupOptions.value = []
    }
  } catch (error) {
    console.error('グループオプション取得エラー:', error)
    groupOptions.value = []
  }
}

async function fetchPerformerAnalysisData() {
  loading.value.performerAnalysis = true
  try {
    const groupNames = selectedGroups.value.includes('all') ? [] : selectedGroups.value
    const dateRange =
      performerDateRange.value && performerDateRange.value.length === 2
        ? performerDateRange.value
        : getCurrentMonthRange()

    const response = await getPerformanceByDestination({
      start_date: dateRange[0],
      end_date: dateRange[1],
      page_key: 'picking_history',
      ...(groupNames.length > 0 ? { group_names: groupNames.join(',') } : {}),
    })

    const data = response?.data ?? response
    let processedData: any[] = []
    if (data?.success && Array.isArray(data.data)) {
      processedData = data.data
    } else if (Array.isArray(data)) {
      processedData = data
    } else if (data?.data && Array.isArray(data.data)) {
      processedData = data.data
    }

    performerAnalysisData.value = processedData.map((item: any) => ({
      performer_id: item.picker_id,
      performer_name: item.picker_name,
      destination_count: item.destination_count ?? 0,
      completion_rate: item.completion_rate ?? 0,
      total_tasks: item.total_tasks ?? 0,
      completed_tasks: item.completed_tasks ?? 0,
      last_activity: new Date().toISOString(),
      destinations: item.destinations ?? [],
    }))
  } catch (error: any) {
    if (!error?.isTokenError) {
      ElMessage.error('担当者分析データの取得に失敗しました')
    }
    performerAnalysisData.value = []
  } finally {
    loading.value.performerAnalysis = false
  }
}

// 根据担当者获取对应的納入先
async function _getDestinationsByPerformer(performerName: string): Promise<{
  destinations: string[]
  destinationDetails: Array<{ value: string; label: string }>
}> {
  try {
    const res = await request.get('/api/shipping/destination-groups/picking_history')
    const data = (res as any)?.data ?? res

    if (data?.success && Array.isArray(data.data)) {
      const destinations: string[] = []
      const destinationDetails: Array<{ value: string; label: string }> = []

      data.data.forEach((group: any) => {
        if (group.group_name === performerName && group.destinations) {
          // 解析destinations JSON数组
          const destArray =
            typeof group.destinations === 'string'
              ? JSON.parse(group.destinations)
              : group.destinations

          destArray.forEach((dest: any) => {
            if (typeof dest === 'object' && dest.value) {
              destinations.push(dest.value)
              destinationDetails.push({
                value: dest.value,
                label: dest.label || dest.value,
              })
            } else if (dest) {
              destinations.push(dest)
              destinationDetails.push({
                value: dest,
                label: dest,
              })
            }
          })
        }
      })

      return { destinations, destinationDetails }
    }

    return { destinations: [], destinationDetails: [] }
  } catch (error) {
    console.error('納入先取得エラー:', error)
    return { destinations: [], destinationDetails: [] }
  }
}

// 处理担当者数据（原有逻辑，用于"全部"选项）
function _processPerformerData(data: any[]) {
  const performerMap = new Map<string, PerformerAnalysisData>()

  data.forEach((item: any) => {
    const performerId = item.picker_id
    const performerName = item.picker_name || performerId

    if (!performerMap.has(performerId)) {
      performerMap.set(performerId, {
        performer_id: performerId,
        performer_name: performerName,
        destination_count: 0,
        completion_rate: 0,
        total_tasks: 0,
        completed_tasks: 0,
        last_activity: '',
        destinations: [],
      })
    }

    const performer = performerMap.get(performerId)!

    // 直接使用后端返回的统计数据
    performer.total_tasks = item.total_tasks || 0
    performer.completed_tasks = item.completed_tasks || 0
    performer.completion_rate =
      item.total_tasks > 0 ? Math.round((item.completed_tasks / item.total_tasks) * 100) : 0
    performer.last_activity = new Date().toISOString()
  })

  performerAnalysisData.value = Array.from(performerMap.values())
}

function _handlePerformerChange() {
  fetchPerformerAnalysisData()
}

function handleGroupChange() {
  fetchPerformerAnalysisData()
}

function handlePerformerDateChange() {
  if (performerDateRange.value && performerDateRange.value.length === 2) {
    fetchPerformerAnalysisData()
  }
}

function togglePerformerExpansion(performerId: string) {
  const index = expandedPerformers.value.indexOf(performerId)
  if (index > -1) {
    expandedPerformers.value.splice(index, 1)
  } else {
    expandedPerformers.value.push(performerId)
  }
}

function filterDestinationsByStatus(_performerId: string) {
  // フィルタリングロジックは getFilteredDestinations で処理
}

function getFilteredDestinations(performer: PerformerAnalysisData): DestinationData[] {
  const filter = destinationStatusFilter.value[performer.performer_id]
  if (!filter) {
    return performer.destinations
  }
  return performer.destinations.filter((dest) => getDestinationStatus(dest) === filter)
}

// 納入先状態：后端未返 status 时按 completion_rate 推导
function getDestinationStatus(dest: DestinationData): string {
  if (dest.status) return dest.status
  const rate = dest.completion_rate ?? 0
  if (rate >= 100) return 'completed'
  if (rate > 0) return 'in_progress'
  return 'pending'
}

function getDestinationStatusType(
  dest: DestinationData,
): 'success' | 'warning' | 'danger' | 'info' {
  const status = getDestinationStatus(dest)
  const typeMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    completed: 'success',
    in_progress: 'warning',
    pending: 'info',
  }
  return typeMap[status] || 'info'
}

function getDestinationStatusText(dest: DestinationData): string {
  const status = getDestinationStatus(dest)
  const textMap: Record<string, string> = {
    completed: '完了',
    in_progress: '進行中',
    pending: '待機',
  }
  return textMap[status] || status
}

// 納入先グループ管理関連の関数
function showDestinationGroupManager() {
  showGroupManager.value = true
}

function handleGroupsUpdated() {
  // グループが更新された時の処理
  // 必要に応じてデータを再取得
  refreshData()
  fetchGroupOptions()
  fetchPerformerAnalysisData()
}

// 计算グループ的総ピッキング数
function getTotalTasks(performer: PerformerAnalysisData): number {
  // 直接使用后端返回的total_tasks字段，这是基于グループ所属的所有納入先+日期计算的结果
  return performer.total_tasks || 0
}

// 计算グループ的ピッキング済数（テンプレートで未使用のため _ 接頭辞）
function _getCompletedTasks(performer: PerformerAnalysisData): number {
  // 直接使用后端返回的completed_tasks字段，这是基于グループ所属的所有納入先+日期计算的结果
  return performer.completed_tasks || 0
}

// 计算グループ的完了率
function getCompletionRate(performer: PerformerAnalysisData): number {
  // 直接使用后端返回的completion_rate字段，这是基于グループ所属的所有納入先+日期计算的结果
  return performer.completion_rate || 0
}

// 使用安全的生命周期钩子包装器
safeOnMounted(async () => {
  console.log('🚀 PickingHistory组件初始化开始')

  // 初始化担当者日期范围为当前月份
  performerDateRange.value = getCurrentMonthRange()

  // 并行加载数据（担当者选项来自 納入先グループ group_name）
  await Promise.all([fetchGroupOptions(), refreshData(), fetchPerformerAnalysisData()])

  console.log('🚀 PickingHistory组件初始化完成')
})

// 添加自动高度指令
const vAutoHeight = {
  mounted(el: {
    style: { height: string }
    scrollHeight: any
    querySelectorAll: (arg0: string) => any
    autoHeightCleanup: () => void
  }) {
    const updateHeight = () => {
      el.style.height = 'auto'
      const height = el.scrollHeight
      el.style.height = `${height}px`
    }

    // 初始化和图像加载时更新高度
    updateHeight()
    window.addEventListener('resize', updateHeight)

    // 监听图像加载
    const images = el.querySelectorAll('img')
    images.forEach((img: { addEventListener: (arg0: string, arg1: () => void) => void }) => {
      img.addEventListener('load', updateHeight)
    })

    // 存储清理函数
    el.autoHeightCleanup = () => {
      window.removeEventListener('resize', updateHeight)
      images.forEach((img: { removeEventListener: (arg0: string, arg1: () => void) => void }) => {
        img.removeEventListener('load', updateHeight)
      })
    }
  },
  updated(el: { style: { height: string }; scrollHeight: any }) {
    const updateHeight = () => {
      el.style.height = 'auto'
      const height = el.scrollHeight
      el.style.height = `${height}px`
    }
    updateHeight()
  },
  unmounted(el: { autoHeightCleanup: () => void }) {
    if (el.autoHeightCleanup) {
      el.autoHeightCleanup()
    }
  },
}

// 在 setup 中注册指令
const app = getCurrentInstance()?.appContext.app
if (app) {
  app.directive('auto-height', vAutoHeight)
}
</script>

<style scoped>
.picking-history-container {
  padding: 10px 12px;
  background: linear-gradient(145deg, #1e1b4b 0%, #312e81 45%, #3730a3 100%);
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

.picking-history-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.2) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
  animation: backgroundFloat 20s ease-in-out infinite;
}

@keyframes backgroundFloat {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(1deg);
  }
}

.picking-history-container > * {
  position: relative;
  z-index: 1;
}

/* 紧凑 Header */
.page-header {
  margin-bottom: 12px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
}

.title-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  font-size: 12px;
  color: #e2e8f0;
  margin: 0;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.refresh-btn {
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
  transition: all 0.2s ease;
}

.refresh-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

/* 担当者分析カード - 圆角 20px、白底半透明、阴影、hover 略上浮 */
.performer-analysis-card {
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(16px);
  overflow: hidden;
  height: auto;
  min-height: 160px;
  transition: all 0.25s ease;
  margin-top: 12px;
  margin-bottom: 12px;
}

.performer-analysis-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.performer-analysis-card :deep(.el-card__header) {
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(226, 232, 240, 0.9) 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  padding: 10px 14px;
  backdrop-filter: blur(8px);
}

/* 担当者分析カードのコントロール行 */
.performer-controls-row {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
  width: 100%;
}

.performer-date-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

/* 担当者分析カードの快捷日期選択 */
.performer-quick-date-section {
  padding: 12px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.1);
  flex-shrink: 0;
}

.performer-quick-date-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.performer-date-group,
.performer-month-group {
  display: flex;
  gap: 6px;
  align-items: center;
}

.performer-quick-btn {
  border-radius: 8px;
  font-weight: 500;
  font-size: 12px;
  padding: 6px 12px;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.performer-quick-btn.yesterday-btn {
  border-color: #f59e0b;
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
}

.performer-quick-btn.yesterday-btn:hover {
  background: #f59e0b;
  color: white;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

.performer-quick-btn.today-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-color: #3b82f6;
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.performer-quick-btn.today-btn:hover {
  background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4);
}

.performer-quick-btn.tomorrow-btn {
  border-color: #8b5cf6;
  color: #8b5cf6;
  background: rgba(139, 92, 246, 0.1);
}

.performer-quick-btn.tomorrow-btn:hover {
  background: #8b5cf6;
  color: white;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.performer-quick-btn.last-month-btn {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.performer-quick-btn.last-month-btn:hover {
  background: #ef4444;
  color: white;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.performer-quick-btn.this-month-btn {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border-color: #22c55e;
  color: white;
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
}

.performer-quick-btn.this-month-btn:hover {
  background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
  box-shadow: 0 4px 16px rgba(34, 197, 94, 0.4);
}

.performer-quick-btn.next-month-btn {
  border-color: #06b6d4;
  color: #06b6d4;
  background: rgba(6, 182, 212, 0.1);
}

.performer-quick-btn.next-month-btn:hover {
  background: #06b6d4;
  color: white;
  box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .performer-date-group,
  .performer-month-group {
    flex-direction: column;
    align-items: center;
  }

  .performer-quick-btn {
    width: 100%;
    justify-content: center;
  }
}

.performer-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.performer-selector {
  border-radius: 8px;
  min-width: 200px;
}

.performer-date-picker {
  border-radius: 8px;
  min-width: 250px;
}

.performer-analysis-content {
  padding: 24px;
  min-height: 200px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
}

.performer-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.performer-list-view {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 16px;
  padding: 20px;
  backdrop-filter: blur(15px);
}

.performer-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.performer-list-item {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.9) 100%);
  border: 1px solid rgba(226, 232, 240, 0.6);
  border-radius: 20px;
  overflow: hidden;
  margin-bottom: 20px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 1px 0 rgba(255, 255, 255, 0.5) inset;
  backdrop-filter: blur(15px);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.performer-list-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.performer-list-item:hover {
  transform: translateY(-4px) scale(1.01);
  box-shadow:
    0 16px 48px rgba(0, 0, 0, 0.15),
    0 1px 0 rgba(255, 255, 255, 0.6) inset;
  border-color: rgba(99, 102, 241, 0.4);
}

.performer-list-item:hover::before {
  opacity: 1;
}

.performer-list-header {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%);
  transition: all 0.3s ease;
}

.performer-list-header:hover {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.9) 100%);
}

.performer-summary {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.performer-name {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.performer-group {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.performer-avatar {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
  transition: all 0.3s ease;
}

.performer-list-header:hover .performer-avatar {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}

.performer-stats {
  display: flex;
  gap: 20px;
  align-items: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(99, 102, 241, 0.1);
  transition: all 0.3s ease;
}

.stat-item:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(99, 102, 241, 0.2);
  transform: translateY(-1px);
}

.stat-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.expand-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(99, 102, 241, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  color: #6366f1;
}

.expand-icon:hover {
  background: rgba(99, 102, 241, 0.2);
  transform: scale(1.1);
}

.expand-icon.expanded {
  transform: rotate(180deg);
  background: #6366f1;
  color: white;
}

.expand-icon.expanded:hover {
  transform: rotate(180deg) scale(1.1);
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.performer-destinations {
  border-top: 1px solid rgba(226, 232, 240, 0.5);
  padding: 20px;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.6) 0%, rgba(241, 245, 249, 0.6) 100%);
  backdrop-filter: blur(10px);
}

.destinations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.1);
}

.destinations-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}

.destinations-title::before {
  content: '📍';
  font-size: 16px;
}

.destinations-filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.destinations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.destination-list-item {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  padding: 16px;
  backdrop-filter: blur(15px);
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.06),
    0 1px 0 rgba(255, 255, 255, 0.4) inset;
  transition: all 0.3s ease;
}

.destination-list-item:hover {
  transform: translateY(-1px);
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.1),
    0 1px 0 rgba(255, 255, 255, 0.5) inset;
  border-color: rgba(99, 102, 241, 0.2);
  background: rgba(255, 255, 255, 0.9);
}

.destination-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.3);
}

.destination-name {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.4;
  flex: 1;
}

.destination-code {
  font-size: 11px;
  color: #6366f1;
  background: rgba(99, 102, 241, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 600;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.destination-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(99, 102, 241, 0.1);
  transition: all 0.3s ease;
}

.stat-row:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(99, 102, 241, 0.2);
  transform: translateY(-1px);
}

.stat-row .label {
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-row .value {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.destination-status {
  display: flex;
  justify-content: center;
  padding-top: 8px;
}

/* 紧凑 Filter Card */
.filter-card {
  margin-bottom: 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(16px);
  transition: all 0.25s ease;
}

.filter-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.filter-card :deep(.el-card__header) {
  padding: 10px 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  width: 20px;
  height: 20px;
  color: #6366f1;
}

.header-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.filter-form {
  padding: 6px 0;
}

.date-selection-section {
  margin-bottom: 10px;
}

.date-selection-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  flex-wrap: wrap;
}

.date-picker-item {
  margin-bottom: 0;
  flex-shrink: 0;
}

.quick-date-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.button-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.group-label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  margin-right: 6px;
  white-space: nowrap;
}

.quick-btn {
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  padding: 5px 10px;
  transition: all 0.2s ease;
  border: 1px solid #e2e8f0;
  background: white;
  color: #64748b;
}

.quick-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* 日別按钮样式 */
.yesterday-btn {
  border-color: #f59e0b;
  color: #f59e0b;
}

.yesterday-btn:hover {
  background: #f59e0b;
  color: white;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

.today-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border-color: #3b82f6;
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.today-btn:hover {
  background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4);
}

.tomorrow-btn {
  border-color: #8b5cf6;
  color: #8b5cf6;
}

.tomorrow-btn:hover {
  background: #8b5cf6;
  color: white;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

/* 月別按钮样式 */
.last-month-btn {
  border-color: #ef4444;
  color: #ef4444;
}

.last-month-btn:hover {
  background: #ef4444;
  color: white;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.this-month-btn {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border-color: #22c55e;
  color: white;
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
}

.this-month-btn:hover {
  background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
  box-shadow: 0 4px 16px rgba(34, 197, 94, 0.4);
}

.next-month-btn {
  border-color: #06b6d4;
  color: #06b6d4;
}

.next-month-btn:hover {
  background: #06b6d4;
  color: white;
  box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3);
}

.modern-date-picker {
  border-radius: 12px;
}

.search-btn,
.reset-btn {
  border-radius: 8px;
  padding: 6px 14px;
  font-weight: 600;
  font-size: 12px;
  transition: all 0.2s ease;
}

.search-btn {
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.search-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
}

.reset-btn {
  border: 2px solid #e2e8f0;
  background: white;
  color: #64748b;
}

.reset-btn:hover {
  border-color: #6366f1;
  color: #6366f1;
  transform: translateY(-1px);
}

/* 紧凑 Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.stat-card {
  position: relative;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(16px);
  transition: all 0.25s ease;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
  opacity: 0;
  transition: opacity 0.25s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 2;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 22px;
  font-weight: 800;
  color: #1e293b;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.stat-decoration {
  position: absolute;
  top: -50%;
  right: -20%;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  opacity: 0.1;
  transition: all 0.3s ease;
}

.stat-card:hover .stat-decoration {
  transform: scale(1.2) rotate(45deg);
  opacity: 0.15;
}

.total-tasks .stat-icon {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}

.total-tasks .stat-decoration {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}

.pending-tasks .stat-icon {
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
}

.pending-tasks .stat-decoration {
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
}

.completed-tasks .stat-icon {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
}

.completed-tasks .stat-decoration {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
}

.completion-rate .stat-icon {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
}

.completion-rate .stat-decoration {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
}

/* 紧凑 Chart Card */
.chart-card {
  margin-bottom: 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(16px);
  transition: all 0.25s ease;
}

.chart-card:hover {
  transform: translateY(-1px);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.15),
    0 1px 0 rgba(255, 255, 255, 0.6) inset;
}

.chart-controls {
  display: flex;
  gap: 8px;
}

.control-group {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-container {
  min-height: 400px; /* 确保最小高度 */
  height: auto; /* 使容器高度自适应 */
  position: relative;
}

.chart-wrapper {
  width: 100%;
  height: 400px;
  position: relative;
}

.chart-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.chart-loading-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #909399;
  font-size: 14px;
}

.chart-loading-placeholder .loading-icon {
  font-size: 24px;
  margin-bottom: 8px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Performer Analysis Styles */
.performer-list-view {
  min-height: auto; /* 移除固定高度 */
  height: auto; /* 使列表视图高度自适应 */
}

.performer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.performer-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f1f5f9;
  cursor: pointer;
  transition: all 0.3s ease;
}

.performer-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.performer-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.performer-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.performer-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.performer-details {
  flex: 1;
}

.performer-name {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.performer-id {
  font-size: 12px;
  color: #64748b;
}

.performer-stats {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.expand-icon {
  transition: transform 0.3s ease;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.performer-destinations {
  border-top: 1px solid #f1f5f9;
  padding-top: 16px;
  margin-top: 16px;
}

.destinations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.destinations-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.destinations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.destination-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.destination-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.destination-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.destination-code {
  font-size: 12px;
  color: #64748b;
  background: white;
  padding: 4px 8px;
  border-radius: 6px;
}

.destination-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.stat-row .label {
  color: #64748b;
}

.stat-row .value {
  font-weight: 600;
  color: #1e293b;
}

.destination-status {
  display: flex;
  justify-content: center;
}

/* Responsive Design for Performer Analysis */
@media (max-width: 1024px) {
  .performer-grid {
    grid-template-columns: 1fr;
  }

  .destinations-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .performer-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .performer-stats {
    justify-content: space-between;
    width: 100%;
  }

  .destination-stats {
    grid-template-columns: 1fr;
  }
}

/* 担当者別日次完了率折线图卡片 */
.daily-rate-chart-card {
  margin-bottom: 24px;
  border-radius: 20px;
  border: none;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
}

.daily-rate-chart-card .chart-container {
  min-height: 320px;
}

/* Modern Tables Grid (保留样式供其他用途) */
.tables-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
}

.table-card {
  border-radius: 20px;
  border: none;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.table-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.pending-card .header-icon {
  color: #f59e0b;
}

.completed-card .header-icon {
  color: #22c55e;
}

.task-count-badge {
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
  color: white;
  min-width: 32px;
  text-align: center;
}

.pending-badge {
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.completed-badge {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
}

.table-container {
  padding: 0;
}

.modern-table {
  border-radius: 12px;
  overflow: hidden;
}

.pagination-container {
  padding: 16px;
  display: flex;
  justify-content: center;
  border-top: 1px solid #f1f5f9;
}

/* Task Detail Dialog */
.task-detail-dialog {
  border-radius: 20px;
}

.detail-value {
  font-weight: 600;
  color: #1e293b;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  padding-top: 16px;
}

.close-dialog-btn {
  border-radius: 12px;
  padding: 10px 24px;
  font-weight: 600;
}

/* Table Row Styles */
:deep(.task-row-pending) {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
}

:deep(.task-row-completed) {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
}

:deep(.task-row-picking) {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
}

/* Responsive Design */
@media (max-width: 1200px) {
  .tables-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .picking-history-container {
    padding: 16px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .page-title {
    font-size: 24px;
  }

  .stat-card {
    padding: 24px;
  }

  .stat-number {
    font-size: 28px;
  }

  /* 快捷按钮响应式样式 */
  .quick-date-buttons {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .button-group {
    justify-content: center;
    flex-wrap: wrap;
  }

  .group-label {
    width: 100%;
    text-align: center;
    margin-bottom: 8px;
    margin-right: 0;
  }

  .quick-btn {
    flex: 1;
    min-width: 80px;
  }
}

/* 下拉菜单样式优化 */
.custom-date-picker-popper,
.custom-group-selector-popper,
.custom-destination-status-popper {
  z-index: 3000 !important;
}

.performer-analysis-card {
  border-radius: 20px;
  overflow: hidden;
}

.performer-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: auto;
}

/* 列表项：白到浅灰渐变、圆角 20px、顶部渐变条 hover 显示 */
.performer-list-item {
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  height: auto;
  position: relative;
  overflow: hidden;
}

.performer-list-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.performer-list-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.performer-list-item:hover::before {
  opacity: 1;
}

.performer-list-header {
  display: flex;
  align-items: center;
  padding: 16px;
  cursor: pointer;
  gap: 16px;
}

.performer-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  transition: transform 0.3s ease;
}

.performer-list-item:hover .performer-avatar {
  transform: scale(1.05);
}

.performer-summary {
  flex-grow: 1;
}

.performer-name {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.performer-group {
  font-size: 12px;
  color: #64748b;
}

.performer-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 12px;
  background: rgba(248, 250, 252, 0.9);
  border-radius: 10px;
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-label {
  font-size: 10px;
  color: #64748b;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.expand-icon {
  transition: transform 0.3s ease;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.performer-destinations {
  border-top: 1px solid #f1f5f9;
  padding: 16px;
}

.destinations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.destinations-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  height: auto; /* 使目的地网格高度自适应 */
}

.destination-list-item {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 16px;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: auto;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.destination-list-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #6366f1;
}

.destination-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.destination-name {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  flex-grow: 1;
  margin-right: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.destination-code {
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 6px;
}

.destination-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.stat-row .label {
  font-size: 10px;
  color: #64748b;
  margin-bottom: 4px;
}

.stat-row .value {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.destination-status {
  display: flex;
  justify-content: center;
}

/* 响应式布局 */
@media (max-width: 1440px) {
  .destinations-list {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }
}

@media (max-width: 1024px) {
  .destinations-list {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }

  .destination-stats {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .date-selection-row {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .quick-date-buttons {
    flex-direction: column;
    gap: 16px;
  }

  .button-group {
    justify-content: center;
  }

  .quick-btn {
    font-size: 11px;
    padding: 4px 8px;
  }

  .performer-controls-row {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .performer-date-controls {
    flex-direction: column;
    gap: 12px;
  }

  .performer-quick-date-buttons {
    flex-direction: column;
    gap: 12px;
  }

  .performer-date-group,
  .performer-month-group {
    justify-content: center;
    flex-wrap: wrap;
  }

  .destinations-list {
    grid-template-columns: repeat(auto-fill, minmax(100%, 1fr));
  }

  .destination-stats {
    grid-template-columns: 1fr 1fr 1fr;
  }

  .destination-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .destination-name {
    width: 100%;
    margin-right: 0;
  }
}

/* ========== Modern compact tab polish ========== */
.picking-history-container {
  min-height: auto;
  padding: 0;
  background: transparent;
}

.picking-history-container::before {
  display: none;
}

.page-header {
  margin-bottom: 8px;
  padding: 9px 12px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(238, 242, 255, 0.9));
  border: 1px solid rgba(203, 213, 225, 0.75);
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.07);
}

.title-icon {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  font-size: 17px;
}

.page-title {
  font-size: 15px;
  color: #172554;
  -webkit-text-fill-color: currentColor;
}

.page-subtitle {
  font-size: 11px;
  color: #64748b;
}

.refresh-btn,
.search-btn,
.reset-btn,
.quick-btn,
.performer-quick-btn {
  height: 30px;
  padding: 0 11px;
  border-radius: 999px;
  font-size: 12px;
}

.filter-card,
.chart-card,
.performer-analysis-card,
.daily-rate-chart-card,
.table-card {
  margin-bottom: 8px;
  border-radius: 14px;
  border: 1px solid rgba(203, 213, 225, 0.72);
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.07);
  background: rgba(255, 255, 255, 0.95);
}

.filter-card :deep(.el-card__header),
.chart-card :deep(.el-card__header),
.performer-analysis-card :deep(.el-card__header),
.daily-rate-chart-card :deep(.el-card__header),
.table-card :deep(.el-card__header) {
  padding: 8px 10px;
  background: linear-gradient(135deg, #f8fafc, #eef2ff);
}

.filter-card :deep(.el-card__body),
.chart-card :deep(.el-card__body),
.performer-analysis-card :deep(.el-card__body),
.daily-rate-chart-card :deep(.el-card__body),
.table-card :deep(.el-card__body) {
  padding: 10px 12px;
}

.date-selection-section,
.performer-quick-date-section {
  padding: 8px 10px;
  border-radius: 12px;
}

.quick-date-buttons,
.performer-quick-date-buttons,
.button-group {
  gap: 6px;
}

.stats-grid {
  gap: 8px;
  margin-bottom: 8px;
}

.stats-grid .stat-card {
  min-height: 58px;
  padding: 10px 12px;
  border-radius: 14px;
}

.stats-grid .stat-icon {
  width: 34px;
  height: 34px;
  border-radius: 11px;
}

.stats-grid .stat-number {
  font-size: 20px;
}

.performer-analysis-content {
  min-height: auto;
  padding: 12px;
}

.performer-list,
.performer-grid {
  gap: 8px;
}

.performer-list-item {
  margin-bottom: 8px;
  border-radius: 14px;
}

.performer-list-header {
  padding: 10px 12px;
  gap: 10px;
}

.performer-avatar {
  width: 38px;
  height: 38px;
}

.performer-stats {
  gap: 8px;
}

.stat-item {
  padding: 6px 9px;
}

.performer-destinations {
  padding: 10px 12px;
}

.destinations-header,
.destination-header,
.destination-stats {
  margin-bottom: 8px;
}

.destinations-list {
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 8px;
}

.destination-list-item {
  padding: 10px;
  border-radius: 12px;
}

.daily-rate-chart-card .chart-container {
  min-height: 260px;
}

.pagination-container {
  padding: 10px;
}

@media (max-width: 768px) {
  .picking-history-container,
  .page-header {
    padding: 8px;
  }

  .page-title {
    font-size: 15px;
  }

  .stats-grid {
    gap: 8px;
  }
}
</style>
