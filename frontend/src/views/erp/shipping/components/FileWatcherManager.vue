<template>
  <div class="file-watcher-manager">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <el-icon class="title-icon" size="28">
            <Monitor />
          </el-icon>
          <div class="title-text">
            <h1>ファイル監視器管理システム</h1>
            <p class="subtitle">自動ファイル処理と監視機能の統合管理</p>
          </div>
        </div>
        <div class="status-badge">
          <el-tag
            :type="watcherStatus.isRunning ? 'success' : 'danger'"
            size="large"
            class="status-tag"
            effect="dark"
          >
            <el-icon class="status-icon">
              <component :is="watcherStatus.isRunning ? 'VideoPlay' : 'VideoPause'" />
            </el-icon>
            {{ watcherStatus.isRunning ? '実行中' : '停止中' }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 状态概览卡片 -->
    <div class="status-overview">
      <el-card class="status-card modern-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <el-icon class="header-icon">
                <Monitor />
              </el-icon>
              <span class="header-title">監視器状態</span>
            </div>
            <div class="header-right">
              <el-button
                type="primary"
                :icon="Refresh"
                @click="refreshStatus"
                :loading="refreshLoading"
                size="small"
                circle
              />
            </div>
          </div>
        </template>

        <div class="status-grid">
          <div class="status-item">
            <div class="status-item-icon">
              <el-icon size="20" color="#409EFF">
                <Folder />
              </el-icon>
            </div>
            <div class="status-item-content">
              <div class="status-item-label">監視パス</div>
              <div class="status-item-value" :title="watcherStatus.watchPath">
                {{ watcherStatus.watchPath || 'N/A' }}
              </div>
            </div>
          </div>

          <div class="status-item">
            <div class="status-item-icon">
              <el-icon size="20" color="#67C23A">
                <Clock />
              </el-icon>
            </div>
            <div class="status-item-content">
              <div class="status-item-label">最終処理時間</div>
              <div class="status-item-value">
                {{ formatDateTime(watcherStatus.lastProcessTime) }}
              </div>
            </div>
          </div>

          <div class="status-item">
            <div class="status-item-icon">
              <el-icon size="20" color="#E6A23C">
                <Document />
              </el-icon>
            </div>
            <div class="status-item-content">
              <div class="status-item-label">処理済みファイル数</div>
              <div class="status-item-value number-value">
                {{ formatNumber(watcherStatus.processedFiles || 0) }}
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 控制按钮 -->
      <el-card class="control-card modern-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <el-icon class="header-icon">
                <Setting />
              </el-icon>
              <span class="header-title">操作コントロール</span>
            </div>
          </div>
        </template>

        <div class="control-buttons">
          <el-button
            type="success"
            :icon="VideoPlay"
            :loading="startLoading"
            :disabled="watcherStatus.isRunning"
            @click="startWatcher"
            size="large"
            class="control-btn start-btn"
          >
            <span>監視開始</span>
          </el-button>

          <el-button
            type="danger"
            :icon="VideoPause"
            :loading="stopLoading"
            :disabled="!watcherStatus.isRunning"
            @click="stopWatcher"
            size="large"
            class="control-btn stop-btn"
          >
            <span>監視停止</span>
          </el-button>

          <el-button
            type="primary"
            :icon="Refresh"
            :loading="refreshLoading"
            @click="refreshStatus"
            size="large"
            class="control-btn refresh-btn"
          >
            <span>状態更新</span>
          </el-button>

          <el-button
            type="warning"
            :icon="Document"
            :loading="processLoading"
            @click="processFile"
            size="large"
            class="control-btn process-btn"
          >
            <span>手動処理</span>
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 统计信息 -->
    <div class="stats-section">
      <el-card class="stats-card modern-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <el-icon class="header-icon">
                <DataAnalysis />
              </el-icon>
              <span class="header-title">処理統計</span>
            </div>
            <div class="header-right">
              <el-button
                type="primary"
                :icon="Refresh"
                @click="loadStats"
                size="small"
                class="refresh-btn"
              >
                統計更新
              </el-button>
            </div>
          </div>
        </template>

        <div class="stats-grid">
          <div class="stat-card total-records">
            <div class="stat-icon">
              <el-icon size="24">
                <Document />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(stats.totalRecords) }}</div>
              <div class="stat-label">総レコード数</div>
            </div>
            <div class="stat-trend">
              <el-icon class="trend-icon">
                <TrendCharts />
              </el-icon>
            </div>
          </div>

          <div class="stat-card today-records">
            <div class="stat-icon">
              <el-icon size="24">
                <Calendar />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(stats.todayRecords) }}</div>
              <div class="stat-label">今日の処理数</div>
            </div>
            <div class="stat-trend">
              <el-icon class="trend-icon">
                <Top />
              </el-icon>
            </div>
          </div>

          <div class="stat-card duplicate-records">
            <div class="stat-icon">
              <el-icon size="24">
                <Warning />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(stats.duplicateRecords) }}</div>
              <div class="stat-label">重複レコード数</div>
            </div>
            <div class="stat-trend">
              <el-icon class="trend-icon">
                <Bottom />
              </el-icon>
            </div>
          </div>

          <div class="stat-card error-records">
            <div class="stat-icon">
              <el-icon size="24">
                <CircleClose />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(stats.errorCount) }}</div>
              <div class="stat-label">エラー数</div>
            </div>
            <div class="stat-trend">
              <el-icon class="trend-icon">
                <Warning />
              </el-icon>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 日志查看 -->
    <div class="logs-section">
      <el-card class="logs-card modern-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <el-icon class="header-icon">
                <List />
              </el-icon>
              <span class="header-title">処理ログ</span>
              <el-badge :value="totalRecords" :max="999" class="logs-badge" type="primary" />
            </div>
            <div class="header-right">
              <div class="logs-controls">
                <el-input
                  v-model="searchQuery"
                  placeholder="ログを検索..."
                  :prefix-icon="Search"
                  @input="handleSearch"
                  clearable
                  class="search-input"
                />
                <el-button
                  type="primary"
                  :icon="Refresh"
                  @click="loadLogs"
                  size="small"
                  class="control-btn-small"
                >
                  更新
                </el-button>
                <el-button
                  type="warning"
                  :icon="Delete"
                  @click="cleanupLogs"
                  size="small"
                  class="control-btn-small"
                >
                  クリア
                </el-button>
              </div>
            </div>
          </div>
        </template>

        <el-table :data="logs" v-loading="logsLoading" height="400" stripe>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="project" label="項目" width="120" />
          <el-table-column prop="picking_no" label="ピッキングNo" width="180" />
          <el-table-column prop="product_name" label="製品名" width="200" show-overflow-tooltip />
          <el-table-column prop="product_code" label="製品CD" width="120" />
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="shipping_quantity" label="出荷数" width="80" />
          <el-table-column prop="date" label="日付" width="120" />
          <el-table-column prop="created_at" label="作成日時" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalRecords"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 数据同步功能 -->
    <div class="sync-section">
      <el-card class="sync-card modern-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <el-icon class="header-icon">
                <Connection />
              </el-icon>
              <span class="header-title">ピッキングタスク同期</span>
            </div>
            <div class="header-right">
              <el-button
                type="primary"
                :icon="Refresh"
                @click="loadSyncStatus"
                size="small"
                class="control-btn-small"
              >
                状態更新
              </el-button>
              <el-button
                type="info"
                :icon="Search"
                @click="showSyncDebugInfo"
                size="small"
                class="control-btn-small"
              >
                デバッグ情報
              </el-button>
            </div>
          </div>
        </template>

        <div class="sync-content">
          <div class="sync-info">
            <el-alert
              title="データ同期機能"
              type="info"
              description="shipping_logテーブルのデータをpicking_tasksテーブルに同期します。picking_no、担当者、日時情報が更新され、ステータスが「済」に変更されます。"
              show-icon
              :closable="false"
              class="sync-alert"
            />
          </div>

          <div class="sync-stats">
            <div class="sync-stat-grid">
              <div class="sync-stat-item available">
                <div class="stat-icon">
                  <el-icon size="20">
                    <Clock />
                  </el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ formatNumber(syncStatus.availableForSync) }}</div>
                  <div class="stat-label">同期可能件数</div>
                </div>
              </div>

              <div class="sync-stat-item synced">
                <div class="stat-icon">
                  <el-icon size="20">
                    <CircleCheck />
                  </el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ formatNumber(syncStatus.alreadySynced) }}</div>
                  <div class="stat-label">同期済み件数</div>
                </div>
              </div>

              <div class="sync-stat-item rate">
                <div class="stat-icon">
                  <el-icon size="20">
                    <TrendCharts />
                  </el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ syncStatus.syncRate }}%</div>
                  <div class="stat-label">同期率</div>
                </div>
              </div>

              <div class="sync-stat-item total">
                <div class="stat-icon">
                  <el-icon size="20">
                    <Document />
                  </el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ formatNumber(syncStatus.totalPickingTasks) }}</div>
                  <div class="stat-label">総タスク数</div>
                </div>
              </div>
            </div>

            <div class="sync-progress">
              <el-progress
                :percentage="syncStatus.syncRate"
                :color="getSyncProgressColor(syncStatus.syncRate)"
                :stroke-width="8"
                class="sync-progress-bar"
              />
            </div>

            <div class="sync-time-info" v-if="syncStatus.lastSyncTime">
              <el-text type="info" size="small">
                <el-icon><Clock /></el-icon>
                最終同期時間: {{ formatDateTime(syncStatus.lastSyncTime) }}
              </el-text>
            </div>
          </div>

          <div class="sync-actions">
            <div v-if="!syncStatus.tableExists" class="table-not-exists">
              <el-alert
                title="picking_tasksテーブルが存在しません"
                type="warning"
                description="データ同期を実行するには、まずpicking_tasksテーブルを作成する必要があります。"
                show-icon
                :closable="false"
                class="table-warning"
              />
              <el-button
                type="warning"
                :icon="Document"
                @click="createPickingTable"
                size="large"
                class="create-table-btn"
              >
                picking_tasksテーブル作成
              </el-button>
            </div>

            <div v-else class="sync-actions">
              <el-button
                type="primary"
                :icon="Connection"
                :loading="syncLoading"
                :disabled="syncStatus.availableForSync === 0"
                @click="syncToPickingTasks"
                size="large"
                class="sync-btn"
              >
                <span>データ同期実行</span>
                <el-badge
                  v-if="syncStatus.availableForSync > 0"
                  :value="syncStatus.availableForSync"
                  :max="999"
                  class="sync-badge"
                />
              </el-button>

              <el-text type="info" size="small" v-if="syncStatus.availableForSync === 0">
                現在同期可能なデータはありません
              </el-text>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 去重功能 -->
    <div class="deduplicate-section">
      <el-card class="deduplicate-card modern-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <el-icon class="header-icon">
                <Filter />
              </el-icon>
              <span class="header-title">重複データ管理</span>
            </div>
          </div>
        </template>

        <div class="deduplicate-content">
          <div class="deduplicate-info">
            <el-alert
              title="注意事項"
              description="重複レコードを検出・削除します。処理前にデータのバックアップを取ることを強くお勧めします。"
              type="warning"
              :closable="false"
              show-icon
            />
          </div>

          <div class="deduplicate-actions">
            <div class="action-buttons">
              <el-button
                type="info"
                :icon="DataAnalysis"
                @click="getDuplicateStats"
                :loading="duplicateStatsLoading"
                size="large"
                class="action-btn stats-btn"
              >
                重複統計取得
              </el-button>
              <el-button
                type="warning"
                :icon="Filter"
                @click="performDeduplicate"
                :loading="deduplicateLoading"
                size="large"
                class="action-btn dedupe-btn"
              >
                重複削除実行
              </el-button>
            </div>
          </div>

          <div v-if="duplicateStats" class="duplicate-stats">
            <el-row :gutter="16" class="stats-overview">
              <el-col :span="6">
                <div class="stats-item">
                  <div class="stats-number">{{ formatNumber(duplicateStats.totalRecords) }}</div>
                  <div class="stats-label">総レコード数</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stats-item duplicate">
                  <div class="stats-number">
                    {{ formatNumber(duplicateStats.totalDuplicateRecords) }}
                  </div>
                  <div class="stats-label">重複レコード数</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stats-item unique">
                  <div class="stats-number">{{ formatNumber(duplicateStats.duplicateGroups) }}</div>
                  <div class="stats-label">重複グループ数</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stats-item rate">
                  <div class="stats-number">{{ calculateDuplicateRate(duplicateStats) }}%</div>
                  <div class="stats-label">重複率</div>
                </div>
              </el-col>
            </el-row>

            <!-- 重复记录详情表格 -->
            <div v-if="duplicateStats.duplicateDetails.length > 0" class="duplicate-details">
              <h4 class="details-title">
                <el-icon><Warning /></el-icon>
                重複レコード詳細 (上位50件)
              </h4>
              <el-table
                :data="duplicateStats.duplicateDetails"
                size="small"
                max-height="300"
                stripe
              >
                <el-table-column prop="picking_no" label="ピッキングNo" width="150" />
                <el-table-column prop="product_code" label="製品CD" width="120" />
                <el-table-column prop="date" label="日付" width="120" />
                <el-table-column prop="count" label="重複数" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag type="warning" size="small">{{ row.count }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="first_created" label="初回作成" width="160">
                  <template #default="{ row }">
                    {{ formatDateTime(row.first_created) }}
                  </template>
                </el-table-column>
                <el-table-column prop="last_created" label="最終作成" width="160">
                  <template #default="{ row }">
                    {{ formatDateTime(row.last_created) }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor,
  VideoPlay,
  VideoPause,
  Refresh,
  Document,
  DataAnalysis,
  List,
  Search,
  Delete,
  Filter,
  Clock,
  TrendCharts,
  Warning,
  Connection,
} from '@element-plus/icons-vue'
import {
  getFileWatcherStatus,
  startFileWatcher,
  stopFileWatcher,
  processFile as processFileAPI,
  getShippingLogs,
  cleanupShippingLogs,
  getDuplicateStats as getDuplicateStatsAPI,
  performDeduplicate as performDeduplicateAPI,
  syncToPickingTasks as syncToPickingTasksAPI,
  getSyncStatus as getSyncStatusAPI,
  createPickingTable as createPickingTableAPI,
  getSyncDebugInfo as getSyncDebugInfoAPI,
  type FileWatcherStatus,
  type ShippingLogRecord,
} from '@/api/shipping/fileWatcher'

// 错误处理接口
interface ApiError {
  response?: {
    data?: {
      message?: string
    }
  }
  message?: string
}

/** API 响应体（request 拦截器已返回 response.data） */
interface ApiResponseBody {
  success?: boolean
  message?: string
  data?: unknown
}

/** shipping-logs API 返回结构 */
interface ShippingLogsResponse {
  items?: ShippingLogRecord[]
  total?: number
  page?: number
  pageSize?: number
}

// 错误消息提取函数
function getErrorMessage(error: unknown, defaultMessage: string): string {
  if (typeof error === 'string') {
    return error
  }

  const apiError = error as ApiError
  return apiError?.response?.data?.message || apiError?.message || defaultMessage
}

// 状态数据
const watcherStatus = ref<FileWatcherStatus>({
  isRunning: false,
  watchPath: '',
  lastProcessTime: null,
  processedFiles: 0,
})

// 统计数据
const stats = ref({
  totalRecords: 0,
  todayRecords: 0,
  duplicateRecords: 0,
  errorCount: 0,
})

// 日志数据
const logs = ref<ShippingLogRecord[]>([])
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalRecords = ref(0)

/** 画面表示用の重複統計（API の DuplicateStats から変換） */
interface DisplayDuplicateStats {
  totalRecords: number
  totalDuplicateRecords: number
  duplicateGroups: number
  duplicateDetails: Array<{ picking_no: string; product_code: string; count: number }>
}

// 重复数据统计
const duplicateStats = ref<DisplayDuplicateStats | null>(null)

// 同步状态数据
const syncStatus = ref({
  availableForSync: 0,
  alreadySynced: 0,
  totalPickingTasks: 0,
  totalShippingLogs: 0,
  lastSyncTime: null as string | null,
  syncRate: 0,
  tableExists: true,
})

// 加载状态
const startLoading = ref(false)
const stopLoading = ref(false)
const refreshLoading = ref(false)
const processLoading = ref(false)
const logsLoading = ref(false)
const duplicateStatsLoading = ref(false)
const deduplicateLoading = ref(false)
const syncLoading = ref(false)

// 获取监视器状态
async function getWatcherStatusData() {
  try {
    const data = await getFileWatcherStatus()
    watcherStatus.value = data
  } catch (error: unknown) {
    const errorMessage = getErrorMessage(error, 'システム状態の取得に失敗しました')
    ElMessage.error(errorMessage)
  }
}

// 启动监视器
async function startWatcher() {
  startLoading.value = true
  try {
    const result = (await startFileWatcher()) as ApiResponseBody
    ElMessage.success(result?.message || 'ファイル監視器を正常に開始しました')
    await getWatcherStatusData()
  } catch (error: unknown) {
    const errorMessage = getErrorMessage(error, 'ファイル監視器の開始に失敗しました')
    ElMessage.error(errorMessage)
  } finally {
    startLoading.value = false
  }
}

// 停止监视器
async function stopWatcher() {
  stopLoading.value = true
  try {
    const result = (await stopFileWatcher()) as ApiResponseBody
    ElMessage.success(result?.message || 'ファイル監視器を正常に停止しました')
    await getWatcherStatusData()
  } catch (error: unknown) {
    const errorMessage = getErrorMessage(error, 'ファイル監視器の停止に失敗しました')
    ElMessage.error(errorMessage)
  } finally {
    stopLoading.value = false
  }
}

// 刷新状态
async function refreshStatus() {
  refreshLoading.value = true
  try {
    await getWatcherStatusData()
    await loadStats()
    ElMessage.success('システム状態を正常に更新しました')
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (error: unknown) {
    ElMessage.error('システム状態の更新に失敗しました')
  } finally {
    refreshLoading.value = false
  }
}

// 手动处理文件
async function processFile() {
  processLoading.value = true
  try {
    const result = (await processFileAPI('')) as ApiResponseBody
    ElMessage.success(result?.message || 'ファイル処理が正常に完了しました')
    await getWatcherStatusData()
    await loadStats()
    await loadLogs()
  } catch (error: unknown) {
    const errorMessage = getErrorMessage(error, 'ファイル処理の実行に失敗しました')
    ElMessage.error(errorMessage)
  } finally {
    processLoading.value = false
  }
}

// 加载统计数据
async function loadStats() {
  try {
    const response = (await getShippingLogs({ page: 1, pageSize: 1 })) as ShippingLogsResponse
    const totalRecords = response.total ?? 0
    try {
      const dupRes = await getDuplicateStatsAPI()
      stats.value = {
        totalRecords,
        todayRecords: 0,
        duplicateRecords: dupRes?.total_duplicates ?? 0,
        errorCount: 0,
      }
    } catch {
      stats.value = {
        totalRecords,
        todayRecords: 0,
        duplicateRecords: 0,
        errorCount: 0,
      }
    }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (error: unknown) {
    // 統計データ取得エラーは静かに処理
  }
}

// 加载日志
async function loadLogs() {
  logsLoading.value = true
  try {
    const params: { page: number; pageSize: number; search?: string } = {
      page: currentPage.value,
      pageSize: pageSize.value,
    }
    if (searchQuery.value) {
      params.search = searchQuery.value
    }

    const response = (await getShippingLogs(params)) as ShippingLogsResponse
    logs.value = response.items || []
    totalRecords.value = response.total ?? 0
  } catch (error: unknown) {
    const errorMessage = getErrorMessage(error, 'ログデータの取得に失敗しました')
    ElMessage.error(errorMessage)
  } finally {
    logsLoading.value = false
  }
}

// 搜索处理
function handleSearch() {
  currentPage.value = 1
  loadLogs()
}

// 分页处理
function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  loadLogs()
}

function handleCurrentChange(page: number) {
  currentPage.value = page
  loadLogs()
}

// 清理日志
async function cleanupLogs() {
  try {
    await ElMessageBox.confirm(
      '古いログデータを削除しますか？この操作は元に戻すことができません。',
      '確認',
      {
        confirmButtonText: '削除実行',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    const result = (await cleanupShippingLogs()) as ApiResponseBody
    ElMessage.success(result.message || 'ログデータを正常にクリアしました')
    await loadLogs()
    await loadStats()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      const errorMessage = getErrorMessage(error, 'ログデータのクリアに失敗しました')
      ElMessage.error(errorMessage)
    }
  }
}

// 获取重复数据统计
async function getDuplicateStats() {
  duplicateStatsLoading.value = true
  try {
    const data = await getDuplicateStatsAPI()
    const totalRecords = data.details?.reduce((s, d) => s + d.count, 0) ?? 0
    duplicateStats.value = {
      totalRecords,
      totalDuplicateRecords: data.total_duplicates ?? 0,
      duplicateGroups: data.unique_picking_nos ?? 0,
      duplicateDetails: data.details ?? [],
    }
    ElMessage.success('重複データ統計を正常に取得しました')
  } catch (error: unknown) {
    const errorMessage = getErrorMessage(error, '重複データ統計の取得に失敗しました')
    ElMessage.error(errorMessage)
  } finally {
    duplicateStatsLoading.value = false
  }
}

// 执行去重
async function performDeduplicate() {
  try {
    await ElMessageBox.confirm(
      '重複レコードを削除しますか？この操作は元に戻すことができません。',
      '確認',
      {
        confirmButtonText: '削除実行',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    deduplicateLoading.value = true
    const result = (await performDeduplicateAPI()) as ApiResponseBody
    ElMessage.success(result?.message || '重複データの削除が正常に完了しました')
    await loadLogs()
    await loadStats()
    await getDuplicateStats()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      const errorMessage = getErrorMessage(error, '重複データの削除に失敗しました')
      ElMessage.error(errorMessage)
    }
  } finally {
    deduplicateLoading.value = false
  }
}

// 格式化日期时间
function formatDateTime(dateTime: string | null) {
  if (!dateTime) return 'N/A'
  return new Date(dateTime).toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })
}

// 格式化数字
function formatNumber(num: number) {
  return num.toLocaleString('ja-JP')
}

// 计算重复率
function calculateDuplicateRate(stats: DisplayDuplicateStats) {
  if (stats.totalRecords === 0) return '0'
  return ((stats.totalDuplicateRecords / stats.totalRecords) * 100).toFixed(1)
}

// 加载同步状态
async function loadSyncStatus() {
  try {
    const response = (await getSyncStatusAPI()) as unknown as Record<string, unknown>
    const data = (response.data ?? response) as Record<string, unknown>
    syncStatus.value = {
      availableForSync: Number(data.availableForSync) ?? 0,
      alreadySynced: Number(data.alreadySynced) ?? 0,
      totalPickingTasks: Number(data.totalPickingTasks) ?? 0,
      totalShippingLogs: Number(data.totalShippingLogs) ?? 0,
      lastSyncTime: (data.lastSyncTime as string) ?? null,
      syncRate: Number(data.syncRate) ?? 0,
      tableExists: (data.tableExists as boolean) ?? true,
    }
  } catch (error: unknown) {
    const errorMessage = getErrorMessage(error, '同期状態の取得に失敗しました')
    ElMessage.error(errorMessage)
  }
}

// 执行数据同步
async function syncToPickingTasks() {
  try {
    await ElMessageBox.confirm(
      'shipping_logのデータをpicking_tasksテーブルに同期しますか？',
      '確認',
      {
        confirmButtonText: '同期実行',
        cancelButtonText: 'キャンセル',
        type: 'info',
      },
    )

    syncLoading.value = true
    const result = (await syncToPickingTasksAPI()) as ApiResponseBody
    ElMessage.success(result?.message || 'データ同期が正常に完了しました')
    await loadSyncStatus()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      const errorMessage = getErrorMessage(error, 'データ同期に失敗しました')
      ElMessage.error(errorMessage)
    }
  } finally {
    syncLoading.value = false
  }
}

// 获取同步进度颜色
function getSyncProgressColor(percentage: number) {
  if (percentage < 30) return '#f56c6c'
  if (percentage < 70) return '#e6a23c'
  return '#67c23a'
}

// 创建picking_tasks表
async function createPickingTable() {
  try {
    await ElMessageBox.confirm('picking_tasksテーブルを作成しますか？', '確認', {
      confirmButtonText: 'テーブル作成',
      cancelButtonText: 'キャンセル',
      type: 'info',
    })

    const result = (await createPickingTableAPI()) as ApiResponseBody
    ElMessage.success(result?.message || 'picking_tasksテーブルが正常に作成されました')
    await loadSyncStatus()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      const errorMessage = getErrorMessage(error, 'テーブル作成に失敗しました')
      ElMessage.error(errorMessage)
    }
  }
}

// 显示同步调试信息
async function showSyncDebugInfo() {
  try {
    const response = (await getSyncDebugInfoAPI()) as unknown as Record<string, unknown>
    const data = (response.data ?? response) as Record<string, { count?: number; latest?: unknown[]; error?: string }>

    const shippingLogCount = data.shipping_log?.count ?? 0
    const pickingTasksCount = data.picking_tasks?.count ?? 0
    const shippingItemsCount = data.shipping_items?.count ?? 0
    const pickingListCount = data.picking_list?.count ?? 0

    await ElMessageBox.alert(
      `
      <div style="text-align: left;">
        <h4>データ同期デバッグ情報</h4>
        <p><strong>shipping_items レコード数:</strong> ${shippingItemsCount}</p>
        <p><strong>shipping_log レコード数:</strong> ${shippingLogCount}</p>
        <p><strong>picking_tasks レコード数:</strong> ${pickingTasksCount}</p>
        <p><strong>picking_list レコード数:</strong> ${pickingListCount}</p>
        <br>
        <p style="font-size: 12px; color: #666;">
          詳細情報はブラウザのコンソールログをご確認ください。
        </p>
      </div>
      `,
      'デバッグ情報',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: 'OK',
      },
    )
  } catch (error: unknown) {
    const errorMessage = getErrorMessage(error, 'デバッグ情報の取得に失敗しました')
    ElMessage.error(errorMessage)
  }
}

// 初始化
onMounted(async () => {
  await getWatcherStatusData()
  await loadStats()
  await loadLogs()
  await loadSyncStatus()
})
</script>

<style scoped>
.file-watcher-manager {
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

/* 页面标题样式 */
.page-header {
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
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
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.title-text h1 {
  margin: 0;
  color: white;
  font-size: 28px;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.subtitle {
  margin: 4px 0 0 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  font-weight: 400;
}

.status-badge {
  display: flex;
  align-items: center;
}

.status-tag {
  padding: 12px 20px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.status-icon {
  margin-right: 8px;
}

/* 现代化卡片样式 */
.modern-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: all 0.3s ease;
}

.modern-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
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
  color: #409eff;
  font-size: 20px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 状态概览样式 */
.status-overview {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
}

.status-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.status-item:hover {
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
  transform: translateX(4px);
}

.status-item-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.status-item-content {
  flex: 1;
  min-width: 0;
}

.status-item-label {
  font-size: 14px;
  color: #6c757d;
  margin-bottom: 4px;
}

.status-item-value {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  word-break: break-all;
}

.number-value {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  font-size: 18px;
  color: #409eff;
}

/* 控制按钮样式 */
.control-buttons {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px;
}

.control-btn {
  width: 100%;
  height: 56px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  border: none;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.control-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.control-btn:hover::before {
  left: 100%;
}

.start-btn {
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
  box-shadow: 0 4px 15px rgba(82, 196, 26, 0.4);
}

.stop-btn {
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%);
  box-shadow: 0 4px 15px rgba(255, 77, 79, 0.4);
}

.refresh-btn {
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
  box-shadow: 0 4px 15px rgba(24, 144, 255, 0.4);
}

.process-btn {
  background: linear-gradient(135deg, #fa8c16 0%, #ffa940 100%);
  box-shadow: 0 4px 15px rgba(250, 140, 22, 0.4);
}

/* 统计信息样式 */
.stats-section {
  margin-bottom: 32px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.stat-card {
  padding: 24px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #409eff, #67c23a);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.total-records::before {
  background: linear-gradient(90deg, #409eff, #40a9ff);
}

.today-records::before {
  background: linear-gradient(90deg, #67c23a, #95de64);
}

.duplicate-records::before {
  background: linear-gradient(90deg, #e6a23c, #ffc53d);
}

.error-records::before {
  background: linear-gradient(90deg, #f56c6c, #ff7875);
}

.stat-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f2f5 0%, #e6f7ff 100%);
  border-radius: 16px;
  color: #409eff;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 4px;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
}

.stat-label {
  font-size: 14px;
  color: #6c757d;
  font-weight: 500;
}

.stat-trend {
  color: #52c41a;
}

.trend-icon {
  font-size: 20px;
}

/* 日志部分样式 */
.logs-section {
  margin-bottom: 32px;
}

.logs-badge {
  margin-left: 8px;
}

.logs-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  width: 280px;
}

.control-btn-small {
  border-radius: 8px;
  font-weight: 500;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

/* 去重功能样式 */
.deduplicate-section {
  margin-bottom: 32px;
}

.deduplicate-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.deduplicate-actions {
  display: flex;
  justify-content: center;
}

.action-buttons {
  display: flex;
  gap: 16px;
}

.action-btn {
  min-width: 160px;
  height: 48px;
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.stats-btn {
  background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(114, 46, 209, 0.4);
}

.dedupe-btn {
  background: linear-gradient(135deg, #fa8c16 0%, #ffa940 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(250, 140, 22, 0.4);
}

.duplicate-stats {
  margin-top: 24px;
}

.stats-overview {
  margin-bottom: 24px;
}

.duplicate-details {
  margin-top: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #fff9e6 0%, #fff2cc 100%);
  border-radius: 12px;
  border: 1px solid #ffd666;
}

.details-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #fa8c16;
}

.stats-item {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.stats-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.stats-number {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
}

.stats-label {
  font-size: 14px;
  color: #6c757d;
  font-weight: 500;
}

.stats-item.duplicate .stats-number {
  color: #fa8c16;
}

.stats-item.unique .stats-number {
  color: #52c41a;
}

.stats-item.rate .stats-number {
  color: #722ed1;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .status-overview {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  }
}

@media (max-width: 768px) {
  .file-watcher-manager {
    padding: 16px;
  }

  .page-header {
    padding: 16px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .title-text h1 {
    font-size: 24px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .logs-controls {
    flex-direction: column;
    gap: 8px;
  }

  .search-input {
    width: 100%;
  }

  .action-buttons {
    flex-direction: column;
    width: 100%;
  }

  .action-btn {
    width: 100%;
  }
}

/* 动画效果 */
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

.modern-card {
  animation: fadeInUp 0.6s ease-out;
}

.stat-card:nth-child(1) {
  animation-delay: 0.1s;
}
.stat-card:nth-child(2) {
  animation-delay: 0.2s;
}
.stat-card:nth-child(3) {
  animation-delay: 0.3s;
}
.stat-card:nth-child(4) {
  animation-delay: 0.4s;
}

/* 同步功能样式 */
.sync-section {
  margin-bottom: 32px;
}

.sync-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sync-alert {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.1);
}

.sync-stats {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sync-stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.sync-stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.sync-stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.sync-stat-item.available {
  border-left: 4px solid #e6a23c;
}

.sync-stat-item.synced {
  border-left: 4px solid #67c23a;
}

.sync-stat-item.rate {
  border-left: 4px solid #409eff;
}

.sync-stat-item.total {
  border-left: 4px solid #909399;
}

.sync-stat-item .stat-icon {
  color: #409eff;
}

.sync-stat-item .stat-content {
  flex: 1;
}

.sync-stat-item .stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #2c3e50;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
}

.sync-stat-item .stat-label {
  font-size: 12px;
  color: #6c757d;
  margin-top: 2px;
}

.sync-progress {
  margin: 16px 0;
}

.sync-progress-bar {
  border-radius: 8px;
}

.sync-time-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 8px;
  border: 1px solid #bae6fd;
}

.sync-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.sync-actions > div {
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
}

.sync-btn {
  position: relative;
  min-width: 200px;
  height: 48px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #409eff 0%, #66b3ff 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.4);
  transition: all 0.3s ease;
  overflow: hidden;
}

.sync-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.5);
}

.sync-btn:active {
  transform: translateY(0);
}

.sync-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.sync-btn:hover::before {
  left: 100%;
}

.sync-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  z-index: 10;
}

.table-not-exists {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  text-align: center;
}

.table-warning {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(250, 173, 20, 0.1);
}

.create-table-btn {
  position: relative;
  min-width: 200px;
  height: 48px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #e6a23c 0%, #f0b90b 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(230, 162, 60, 0.4);
  transition: all 0.3s ease;
  overflow: hidden;
}

.create-table-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(230, 162, 60, 0.5);
}

.create-table-btn:active {
  transform: translateY(0);
}

.create-table-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.create-table-btn:hover::before {
  left: 100%;
}

/* 响应式设计补充 */
@media (max-width: 768px) {
  .sync-stat-grid {
    grid-template-columns: 1fr;
  }

  .sync-btn {
    width: 100%;
    min-width: unset;
  }
}
</style>
