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
                      v-for="group in groupOptions"
                      :key="group.id"
                      :label="group.group_name"
                      :value="group.group_name"
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
                <div class="expand-icon">
                  <el-icon
                    :class="{ expanded: expandedPerformers.includes(performer.performer_id) }"
                  >
                    <ArrowDown />
                  </el-icon>
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
                      <el-tag :type="getDestinationStatusType(destination.status)" size="small">
                        {{ getDestinationStatusText(destination.status) }}
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

    <!-- Modern Tables Grid -->
    <div class="tables-grid">
      <!-- Pending Tasks Table -->
      <el-card class="table-card pending-card" shadow="never">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <el-icon class="header-icon pending-icon"><Clock /></el-icon>
              <span class="header-title">未ピッキングリスト</span>
            </div>
            <div class="task-count-badge pending-badge">
              {{ pendingTasks.length }}
            </div>
          </div>
        </template>
        <div class="table-container" v-loading="loading.pendingTasks">
          <el-table
            :data="paginatedPendingTasks"
            @row-click="showTaskDetail"
            :row-class-name="getTaskRowClass"
            height="400"
            size="small"
            class="modern-table"
          >
            <el-table-column prop="shipping_no" label="ピッキングNo" width="120" />
            <el-table-column prop="product_cd" label="製品CD" width="90" />
            <el-table-column
              prop="product_name"
              label="製品名"
              min-width="150"
              show-overflow-tooltip
            />
            <el-table-column label="数量" min-width="100" align="right">
              <template #default="{ row }">
                {{ row.picked_quantity || 0 }}/{{ row.confirmed_boxes || 0 }}
              </template>
            </el-table-column>
            <el-table-column label="状態" min-width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-container" v-if="pendingTasks.length > pendingPageSize">
            <el-pagination
              v-model:current-page="pendingCurrentPage"
              v-model:page-size="pendingPageSize"
              :page-sizes="[10, 20, 50]"
              :total="pendingTasks.length"
              layout="total, sizes, prev, pager, next"
              size="small"
            />
          </div>
        </div>
      </el-card>

      <!-- Completed Tasks Table -->
      <el-card class="table-card completed-card" shadow="never">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <el-icon class="header-icon completed-icon"><CircleCheck /></el-icon>
              <span class="header-title">ピッキング済リスト</span>
            </div>
            <div class="task-count-badge completed-badge">
              {{ completedTasks.length }}
            </div>
          </div>
        </template>
        <div class="table-container" v-loading="loading.completedTasks">
          <el-table
            :data="paginatedCompletedTasks"
            @row-click="showTaskDetail"
            :row-class-name="getTaskRowClass"
            height="400"
            size="small"
            class="modern-table"
          >
            <el-table-column prop="shipping_no" label="ピッキングNo" width="120" />
            <el-table-column prop="product_cd" label="製品CD" width="90" />
            <el-table-column
              prop="product_name"
              label="製品名"
              min-width="150"
              show-overflow-tooltip
            />
            <el-table-column label="数量" min-width="100" align="right">
              <template #default="{ row }">
                {{ row.picked_quantity || 0 }}/{{ row.confirmed_boxes || 0 }}
              </template>
            </el-table-column>
            <el-table-column label="完了時間" min-width="120">
              <template #default="{ row }">
                {{ formatDateTime(row.start_time) }}
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-container" v-if="completedTasks.length > completedPageSize">
            <el-pagination
              v-model:current-page="completedCurrentPage"
              v-model:page-size="completedPageSize"
              :page-sizes="[10, 20, 50]"
              :total="completedTasks.length"
              layout="total, sizes, prev, pager, next"
              size="small"
            />
          </div>
        </div>
      </el-card>
    </div>

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
import DestinationGroupManager from './DestinationGroupManager.vue'
import ChartWrapper from '@/components/ChartWrapper.vue'
import { runChartTests } from '@/utils/chartTest'
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

// Task detail
const taskDetailVisible = ref(false)
const selectedTask = ref<PickingTask | null>(null)

// Pagination
const pendingCurrentPage = ref(1)
const pendingPageSize = ref(10)
const completedCurrentPage = ref(1)
const completedPageSize = ref(10)

// 担当者分析関連
interface PerformerOption {
  username: string
  name: string
}

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
  status: string
  last_updated: string
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

const performerOptions = ref<PerformerOption[]>([])
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

// Computed properties
const paginatedPendingTasks = computed(() => {
  const start = (pendingCurrentPage.value - 1) * pendingPageSize.value
  const end = start + pendingPageSize.value
  return pendingTasks.value.slice(start, end)
})

const paginatedCompletedTasks = computed(() => {
  const start = (completedCurrentPage.value - 1) * completedPageSize.value
  const end = start + completedPageSize.value
  return completedTasks.value.slice(start, end)
})

// 担当者分析関連のcomputed
const filteredPerformerData = computed(() => {
  console.log('📊 filteredPerformerData计算:', {
    selectedGroups: selectedGroups.value,
    performerAnalysisData: performerAnalysisData.value,
    includesAll: selectedGroups.value.includes('all'),
    length: selectedGroups.value.length,
  })

  if (selectedGroups.value.includes('all') || selectedGroups.value.length === 0) {
    console.log('📊 返回所有担当者数据:', performerAnalysisData.value)
    return performerAnalysisData.value
  }

  const filtered = performerAnalysisData.value.filter((performer) =>
    selectedGroups.value.includes(performer.performer_id),
  )
  console.log('📊 返回过滤后的担当者数据:', filtered)
  return filtered
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

// 计算完了率数据，供插件使用
const completionRatesData = computed(() => {
  return trendData.value.map((d) =>
    d.total > 0 ? Number(((d.completed / d.total) * 100).toFixed(1)) : 50,
  )
})

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
    // 添加数据标签插件
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
    // 自定义插件：在完了率折线上显示数据标签
    customDatalabels: {
      id: 'customDatalabels',
      afterDraw: function (chart: any) {
        const ctx = chart.ctx
        const meta = chart.getDatasetMeta(2) // 完了率是第3个数据集

        if (meta && meta.data) {
          meta.data.forEach((point: any, index: number) => {
            const value = completionRatesData.value[index]
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

    const data = response?.data || response

    if (data) {
      const allTasks = data.tasks || data || []
      if (Array.isArray(allTasks)) {
        // 过滤掉产品名包含特定关键词的数据
        const excludeKeywords = ['加工', 'アーチ', '料金']
        const filteredTasks = allTasks.filter((task) => {
          const productName = task.product_name || ''
          return !excludeKeywords.some((keyword) => productName.includes(keyword))
        })

        // 総ピッキング数：筛选期间picking_tasks表内shipping_no_p件数统计
        const uniqueShippingNos = new Set(
          filteredTasks.map((task) => task.shipping_no_p || task.shipping_no),
        )
        const totalTasks = uniqueShippingNos.size

        // 総未ピッキング数：status字段为pending的直接件数统计
        const pendingTasksCount = filteredTasks.filter(
          (task) => task.status === 'pending' || task.status === 'assigned',
        ).length

        // 総ピッキング済数：status字段为completed的直接件数统计
        const completedTasksCount = filteredTasks.filter(
          (task) => task.status === 'completed' || task.status === 'picked',
        ).length

        // 更新统计数据
        historyStats.totalTasks = totalTasks
        historyStats.completedTasks = completedTasksCount
        historyStats.pendingTasks = pendingTasksCount
        historyStats.completionRate =
          totalTasks > 0 ? Number(((completedTasksCount / totalTasks) * 100).toFixed(1)) : 0

        // 更新任务列表
        pendingTasks.value = filteredTasks.filter(
          (task) => task.status === 'pending' || task.status === 'assigned',
        )
        completedTasks.value = filteredTasks.filter(
          (task) => task.status === 'completed' || task.status === 'picked',
        )

        console.log('📊 更新後の統計データ:', historyStats)
        console.log('📊 按shipping_no_p件数统计:', {
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

  if (trendGranularity.value === 'daily') {
    // 按日期分组统计
    const dailyStats: Record<string, { total: Set<string>; completed: number }> = {}

    filteredTasks.forEach((task) => {
      // 使用shipping_date字段，如果没有则使用created_at
      const date = task.shipping_date
        ? task.shipping_date.split('T')[0]
        : task.created_at
          ? task.created_at.split('T')[0]
          : formatDateString(getJapanDate())
      if (!dailyStats[date]) {
        dailyStats[date] = { total: new Set(), completed: 0 }
      }

      // 统计shipping_no_p件数（与主统计逻辑一致）
      const shippingNo = task.shipping_no_p || task.shipping_no
      if (shippingNo) {
        dailyStats[date].total.add(shippingNo)
      }

      // 统计completed件数（直接件数统计）
      if (task.status === 'completed' || task.status === 'picked') {
        dailyStats[date].completed++
      }
    })

    // 转换为数组格式
    Object.entries(dailyStats).forEach(([date, stats]) => {
      data.push({
        date,
        total: stats.total.size,
        completed: stats.completed,
      })
    })
  } else {
    // 按月份分组统计
    const monthlyStats: Record<string, { total: Set<string>; completed: number }> = {}

    filteredTasks.forEach((task) => {
      // 使用shipping_date字段，如果没有则使用created_at
      const date = task.shipping_date
        ? task.shipping_date.split('T')[0]
        : task.created_at
          ? task.created_at.split('T')[0]
          : formatDateString(getJapanDate())
      const month = date.substring(0, 7) // YYYY-MM

      if (!monthlyStats[month]) {
        monthlyStats[month] = { total: new Set(), completed: 0 }
      }

      // 统计shipping_no_p件数（与主统计逻辑一致）
      const shippingNo = task.shipping_no_p || task.shipping_no
      if (shippingNo) {
        monthlyStats[month].total.add(shippingNo)
      }

      // 统计completed件数（直接件数统计）
      if (task.status === 'completed' || task.status === 'picked') {
        monthlyStats[month].completed++
      }
    })

    // 转换为数组格式
    Object.entries(monthlyStats).forEach(([month, stats]) => {
      data.push({
        date: month,
        total: stats.total.size,
        completed: stats.completed,
      })
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
    const data = response?.data || response
    const allTasks = data?.tasks || data || []

    if (Array.isArray(allTasks)) {
      trendData.value = generateTrendDataFromTasks(allTasks)
    } else {
      trendData.value = []
    }

    console.log('📈 トレンドデータ更新完了:', trendData.value)
  } catch (error) {
    console.error('❌ トレンドデータ取得エラー:', error)
    ElMessage.error('トレンドデータの取得に失敗しました')
    trendData.value = []
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

function showTaskDetail(task: PickingTask) {
  selectedTask.value = task
  taskDetailVisible.value = true
}

function getTaskRowClass({ row }: { row: PickingTask }) {
  return `task-row-${row.status}`
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

// 担当者分析関連の関数
async function fetchPerformerOptions() {
  try {
    const response = await fetch('/api/master/users')
    const data = await response.json()
    if (data.success && Array.isArray(data.data)) {
      performerOptions.value = data.data.map((user: any) => ({
        username: user.username,
        name: user.name || user.first_name || user.username,
      }))
    }
  } catch (error) {
    console.error('担当者オプション取得エラー:', error)
  }
}

// グループ分析関連の関数
async function fetchGroupOptions() {
  try {
    console.log('📊 グループオプション取得開始')

    const response = await fetch('/api/shipping/destination-groups/picking_history')
    const responseData = await response.json()

    console.log('📊 グループAPI响应:', responseData)

    let data = null

    // 处理不同的响应格式
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
      console.log('📊 グループオプション処理完了:', groupOptions.value)
    } else {
      console.error('グループデータ格式不正确:', responseData)
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
    console.log('📊 担当者分析データ取得開始')
    console.log('📊 選択されたグループ:', selectedGroups.value)

    const groupNames = selectedGroups.value.includes('all') ? [] : selectedGroups.value
    // 使用担当者专用的日期范围
    const dateRange =
      performerDateRange.value && performerDateRange.value.length === 2
        ? performerDateRange.value
        : getCurrentMonthRange()

    console.log('📊 使用日期范围:', dateRange)
    console.log('📊 处理グループ名:', groupNames)

    if (groupNames.length === 0) {
      // 选择"全部"时，获取所有担当者的数据
      console.log('📊 使用"全部"逻辑')
      await fetchAllPerformersData(dateRange)
    } else {
      // 选择特定グループ时，获取该グループ的整体绩效数据
      console.log('📊 使用特定グループ逻辑')
      await fetchSelectedGroupsData(groupNames, dateRange)
    }
  } catch (error) {
    console.error('担当者分析データ取得エラー:', error)
    ElMessage.error('担当者分析データの取得に失敗しました')
    performerAnalysisData.value = []
  } finally {
    loading.value.performerAnalysis = false
  }
}

// 获取所有担当者数据（当选择"全部"时）
async function fetchAllPerformersData(dateRange: [string, string]) {
  try {
    console.log('📊 全グループ分析データ取得開始:', { dateRange })

    // 1. 获取所有グループ管理数据
    const groupResponse = await fetch(`/api/shipping/destination-groups/picking_history`)
    const groupData = await groupResponse.json()

    console.log('📊 グループ管理API响应:', groupData)

    if (!groupData.success || !Array.isArray(groupData.data)) {
      console.warn('📊 グループ管理データが取得できません')
      performerAnalysisData.value = []
      return
    }

    // 获取所有グループ名
    const allGroupNames = groupData.data.map((group: any) => group.group_name).filter(Boolean)
    console.log('📊 全グループ名:', allGroupNames)

    if (allGroupNames.length === 0) {
      console.warn('📊 グループ名が見つかりません')
      performerAnalysisData.value = []
      return
    }

    // 使用现有的fetchSelectedGroupsData函数处理所有グループ
    await fetchSelectedGroupsData(allGroupNames, dateRange)
  } catch (error) {
    console.error('全担当者データ取得エラー:', error)
    performerAnalysisData.value = []
  }
}

// 获取选定担当者的整体绩效数据（新逻辑）（未使用のため _ 接頭辞）
async function _fetchSelectedPerformersData(performerNames: string[], dateRange: [string, string]) {
  try {
    // 使用后端API进行统计计算
    const response = await getPerformanceByDestination({
      start_date: dateRange[0],
      end_date: dateRange[1],
      picker_names: performerNames,
    })

    const data = response?.data || response
    if (data.success && Array.isArray(data.data)) {
      // 直接使用后端返回的数据，因为后端已经按新逻辑处理了
      performerAnalysisData.value = data.data.map((item: any) => ({
        performer_id: item.picker_id,
        performer_name: item.picker_name,
        destination_count: item.destination_count || 0,
        completion_rate: item.completion_rate || 0,
        total_tasks: item.total_tasks || 0,
        completed_tasks: item.completed_tasks || 0,
        last_activity: new Date().toISOString(),
        destinations: item.destinations || [],
      }))
    } else {
      performerAnalysisData.value = []
    }
  } catch (error: any) {
    console.error('選択担当者データ取得エラー:', error)

    // トークンエラーの場合は特別な処理をしない（request.tsで処理済み）
    if (error?.isTokenError) {
      return
    }

    // その他のエラーの場合はメッセージを表示
    ElMessage.error('担当者分析データの取得に失敗しました')
    performerAnalysisData.value = []
  }
}

// 获取选定グループ的整体绩效数据
async function fetchSelectedGroupsData(groupNames: string[], dateRange: [string, string]) {
  try {
    console.log('📊 グループ分析データ取得開始:', { groupNames, dateRange })

    // 使用后端API进行统计计算
    const response = await getPerformanceByDestination({
      start_date: dateRange[0],
      end_date: dateRange[1],
      group_names: groupNames.join(','), // 修正：传递字符串而不是数组
    })

    console.log('📊 API响应:', response)

    const data = response?.data || response
    console.log('📊 处理后的数据:', data)

    // 修正：检查数据格式，支持多种响应格式
    let processedData = []

    if (data && data.success && Array.isArray(data.data)) {
      // 格式1：{success: true, data: [...]}
      processedData = data.data
    } else if (Array.isArray(data)) {
      // 格式2：直接是数组
      processedData = data
    } else if (data && Array.isArray(data.data)) {
      // 格式3：{data: [...]}
      processedData = data.data
    } else {
      console.warn('📊 グループ分析データが取得できません:', data)
      performerAnalysisData.value = []
      return
    }

    // 转换后端数据格式为前端需要的格式
    const groupStats: PerformerAnalysisData[] = processedData.map((item: any) => ({
      performer_id: item.picker_id,
      performer_name: item.picker_name,
      destination_count: item.destination_count || 0,
      completion_rate: item.completion_rate || 0,
      total_tasks: item.total_tasks || 0,
      completed_tasks: item.completed_tasks || 0,
      last_activity: new Date().toISOString(),
      destinations: item.destinations || [],
    }))

    performerAnalysisData.value = groupStats
    console.log('📊 グループ分析データ処理完了:', performerAnalysisData.value)
  } catch (error: any) {
    console.error('📊 グループ分析データが取得できません')
    console.error('選択グループデータ取得エラー:', error)

    // トークンエラーの場合は特別な処理をしない（request.tsで処理済み）
    if (error?.isTokenError) {
      return
    }

    // その他のエラーの場合はメッセージを表示
    ElMessage.error('グループ分析データの取得に失敗しました')
    performerAnalysisData.value = []
  }
}

// 根据担当者获取对应的納入先
async function _getDestinationsByPerformer(performerName: string): Promise<{
  destinations: string[]
  destinationDetails: Array<{ value: string; label: string }>
}> {
  try {
    const response = await fetch(`/api/shipping/destination-groups/picking_history`)
    const data = await response.json()

    if (data.success && Array.isArray(data.data)) {
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
  return performer.destinations.filter((dest) => dest.status === filter)
}

function getDestinationStatusType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  const typeMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    completed: 'success',
    in_progress: 'warning',
    pending: 'info',
  }
  return typeMap[status] || 'info'
}

function getDestinationStatusText(status: string): string {
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

  // 测试Chart.js是否正确加载
  const chartTestResult = runChartTests()
  if (!chartTestResult) {
    console.warn('⚠️ Chart.js测试失败，图表可能无法正常显示')
    ElMessage.warning('チャートライブラリの読み込みに問題があります')
  }

  // 并行加载数据
  await Promise.all([
    fetchPerformerOptions(),
    fetchGroupOptions(),
    refreshData(),
    fetchPerformerAnalysisData(),
  ])

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
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
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

/* Modern Header */
.page-header {
  margin-bottom: 32px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3);
}

.title-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  font-size: 16px;
  color: #fbfbfc;
  margin: 0;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.refresh-btn {
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
}

/* 担当者分析カード */
.performer-analysis-card {
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 1px 0 rgba(255, 255, 255, 0.5) inset;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  overflow: hidden;
  height: auto;
  min-height: 200px;
  transition: all 0.3s ease;
  margin-top: 24px;
  margin-bottom: 24px;
}

.performer-analysis-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.15),
    0 1px 0 rgba(255, 255, 255, 0.6) inset;
}

.performer-analysis-card :deep(.el-card__header) {
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.9) 0%, rgba(226, 232, 240, 0.9) 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  padding: 24px;
  backdrop-filter: blur(10px);
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

/* Modern Filter Card */
.filter-card {
  margin-bottom: 32px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 1px 0 rgba(255, 255, 255, 0.5) inset;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  transition: all 0.3s ease;
}

.filter-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.15),
    0 1px 0 rgba(255, 255, 255, 0.6) inset;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 24px;
  height: 24px;
  color: #6366f1;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.filter-form {
  padding: 8px 0;
}

/* 期間選択セクション样式 */
.date-selection-section {
  margin-bottom: 16px;
}

.date-selection-row {
  display: flex;
  align-items: center;
  gap: 24px;
  width: 100%;
  flex-wrap: wrap;
}

.date-picker-item {
  margin-bottom: 0;
  flex-shrink: 0;
}

/* 快捷日期按钮样式 */
.quick-date-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  align-items: center;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.button-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  margin-right: 8px;
  white-space: nowrap;
}

.quick-btn {
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  padding: 6px 12px;
  transition: all 0.3s ease;
  border: 1px solid #e2e8f0;
  background: white;
  color: #64748b;
}

.quick-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.search-btn {
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
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

/* Modern Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  position: relative;
  padding: 32px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 1px 0 rgba(255, 255, 255, 0.5) inset;
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(20px);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.15),
    0 1px 0 rgba(255, 255, 255, 0.6) inset;
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
  z-index: 2;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 36px;
  font-weight: 800;
  color: #1e293b;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
  font-weight: 600;
  letter-spacing: 0.5px;
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

/* Modern Chart Card */
.chart-card {
  margin-bottom: 32px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 1px 0 rgba(255, 255, 255, 0.5) inset;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  transition: all 0.3s ease;
}

.chart-card:hover {
  transform: translateY(-2px);
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

/* Modern Tables Grid */
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
  border-radius: 16px;
  overflow: hidden;
}

.performer-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: auto; /* 使列表高度自适应 */
}

.performer-list-item {
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  height: auto; /* 使每个列表项高度自适应 */
}

.performer-list-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
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
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 16px;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: auto; /* 使每个目的地项高度自适应 */
}

.destination-list-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
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
</style>
