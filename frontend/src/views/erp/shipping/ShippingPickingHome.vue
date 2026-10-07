<template>
  <div class="picking-management pb-std">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content pb-hero pb-hero--page">
        <div class="header-fx pb-bubbles" aria-hidden="true" />
        <div class="header-left">
          <div class="title-container">
            <div class="title-icon-wrapper">
              <el-icon class="title-icon">
                <Box />
              </el-icon>
            </div>
            <div class="title-text">
              <h1 class="main-title pb-hero-title">{{ t('shipping.titlePicking') }}</h1>
              <p class="subtitle pb-hero-desc">
                <el-icon class="subtitle-icon">
                  <LocationInformation />
                </el-icon>
                {{ t('shipping.subtitlePicking') }}
              </p>
            </div>
          </div>
        </div>
        <div class="header-right">
          <el-button :icon="Refresh" :loading="syncLoading" @click="handleSyncData" size="default"
            class="header-btn sync-btn">
            <span>{{ t('shipping.syncData') }}</span>
          </el-button>
        </div>
      </div>
    </div>

    <transition name="sync-progress-fade">
      <div v-if="syncProgress > 0" class="sync-progress-banner">
        <p class="sync-progress-hint">{{ t('shipping.syncProgressHint') }}</p>
        <el-progress
          :percentage="Math.min(syncProgress, 100)"
          :stroke-width="10"
          class="sync-progress-el"
        />
      </div>
    </transition>

    <!-- 顶部状态统计 -->
    <div class="status-cards">
      <el-card class="stat-card today-card" shadow="never">
        <div class="stat-item">
          <div class="stat-icon-container">
            <div class="stat-icon today">
              <el-icon>
                <Calendar />
              </el-icon>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-number-container">
              <span class="stat-number">{{ todayOverview.total_today }}</span>
              <div class="stat-trend up">
                <el-icon>
                  <TrendCharts />
                </el-icon>
                <!-- <span>+12%</span> -->
              </div>
            </div>
            <span class="stat-label">{{ t('shipping.todayPallets') }}</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card progress-card" shadow="never">
        <div class="stat-item">
          <div class="stat-icon-container">
            <div class="stat-icon progress">
              <el-icon>
                <Clock />
              </el-icon>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-number-container">
              <span class="stat-number">{{ todayOverview.pending_today }}</span>
              <div class="stat-badge pending">{{ t('shipping.inProgress') }}</div>
            </div>
            <span class="stat-label">{{ t('shipping.todayInProgress') }}</span>
            <div class="stat-progress">
              <div class="progress-bar progress-bar-orange" :style="{ width: pendingProgress }"></div>
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card completed-card" shadow="never">
        <div class="stat-item">
          <div class="stat-icon-container">
            <div class="stat-icon completed">
              <el-icon>
                <Check />
              </el-icon>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-number-container">
              <span class="stat-number">{{ todayOverview.completed_today }}</span>
              <div class="stat-trend up">
                <el-icon>
                  <ArrowUp />
                </el-icon>
                <!-- <span>+8%</span> -->
              </div>
            </div>
            <span class="stat-label">{{ t('shipping.todayCompleted') }}</span>
            <div class="stat-progress">
              <div class="progress-bar progress-bar-green" :style="{ width: completedProgress }"></div>
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card efficiency-card" shadow="never">
        <div class="stat-item">
          <div class="stat-icon-container">
            <div class="stat-icon efficiency">
              <el-icon>
                <TrendCharts />
              </el-icon>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-number-container">
              <span class="stat-number">{{ todayOverview.today_completion_rate }}</span>
              <span class="stat-percent">%</span>
            </div>
            <span class="stat-label">{{ t('shipping.todayCompletionRate') }}</span>
            <div class="circular-progress">
              <svg class="progress-ring" width="60" height="60">
                <circle class="progress-ring-circle" stroke="#d1fae5" stroke-width="4" fill="transparent" r="26" cx="30"
                  cy="30" />
                <circle class="progress-ring-progress" stroke="url(#efficiency-gradient)" stroke-width="4"
                  stroke-linecap="round" fill="transparent" r="26" cx="30" cy="30"
                  :stroke-dasharray="`${todayOverview.today_completion_rate * 1.63} 163`" />
                <defs>
                  <linearGradient id="efficiency-gradient">
                    <stop offset="0%" stop-color="#34d399" />
                    <stop offset="100%" stop-color="#059669" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 主要功能区域 -->
    <el-card class="main-content" shadow="never">
      <div class="content-header">
        <h2 class="content-title">
          <el-icon>
            <Operation />
          </el-icon>
          {{ t('shipping.panelTitle') }}
        </h2>
      </div>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="custom-tabs">
        <el-tab-pane name="generate">
          <template #label>
            <div class="tab-label">
              <el-icon>
                <List />
              </el-icon>
              <span>{{ t('shipping.tabPickingList') }}</span>
            </div>
          </template>
          <PickingListGenerator @refresh="refreshStats" />
        </el-tab-pane>

        <el-tab-pane name="progress">
          <template #label>
            <div class="tab-label">
              <el-icon>
                <Clock />
              </el-icon>
              <span>{{ t('shipping.tabProgress') }}</span>
            </div>
          </template>
          <PickingProgress @refresh="refreshStats" />
        </el-tab-pane>

        <el-tab-pane name="history">
          <template #label>
            <div class="tab-label">
              <el-icon>
                <PieChart />
              </el-icon>
              <span>{{ t('shipping.tabHistory') }}</span>
            </div>
          </template>
          <PickingHistory />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  Box,
  Calendar,
  Clock,
  Check,
  Refresh,
  TrendCharts,
  LocationInformation,
  ArrowUp,
  Operation,
  List,
  PieChart,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import {
  getRefreshPickingLogMatchedTask,
  startRefreshPickingLogMatchedTask,
} from '@/api/shipping/picking'
import {
  normalizePickingProgressResponse,
  filterProductDataForPickingProgress,
} from '@/utils/shippingPickingNewProgressParse'
import PickingListGenerator from './components/PickingListGenerator.vue'
import PickingProgress from './components/PickingProgress.vue'
import PickingHistory from './components/PickingHistory.vue'
import { useSalesOperationPermission } from '@/composables/useSalesOperationPermission'
import { guardSalesOperation } from '@/utils/salesOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = useSalesOperationPermission()


// 更新接口数据结构
interface TodayOverview {
  total_today: number
  pending_today: number
  completed_today: number
  today_completion_rate: number
}

interface PalletInfo {
  [key: string]: any
}

interface ProgressStats {
  [key: string]: any
}

/** API 响应体（request 拦截器已返回 response.data） */
interface ApiResponseBody {
  success?: boolean
  message?: string
  data?: unknown
}

interface PickingSyncTaskStatus {
  task_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress_percent?: number
  message?: string
  updated_rows?: number
  error?: string | null
}

const { t } = useI18n()
const route = useRoute()

const activeTab = ref('generate')
const syncLoading = ref(false)
/** 同期処理の表示用（0 で非表示） */
const syncProgress = ref(0)
let syncProgressTimer: ReturnType<typeof setInterval> | null = null

function clearSyncProgressTimer() {
  if (!guardSalesOperation(canCreate)) return

  if (syncProgressTimer !== null) {
    clearInterval(syncProgressTimer)
    syncProgressTimer = null
  }
}

function tickSyncProgress() {
  if (!guardSalesOperation(canCreate)) return

  const v = syncProgress.value
  if (v >= 90) return
  const step = v < 35 ? 8 : v < 65 ? 5 : 3
  syncProgress.value = Math.min(90, v + step)
}
const loading = ref({
  data: false,
})

const todayOverview = ref<TodayOverview>({
  total_today: 0,
  pending_today: 0,
  completed_today: 0,
  today_completion_rate: 0,
})

const palletList = ref<PalletInfo[]>([])
const progressStats = ref<ProgressStats[]>([])

// 计算进度百分比
const pendingProgress = computed(() => {
  if (!todayOverview.value.total_today) {
    return '0%'
  }
  const percentage = (todayOverview.value.pending_today / todayOverview.value.total_today) * 100
  return `${percentage.toFixed(0)}%`
})

const completedProgress = computed(() => {
  if (!todayOverview.value.total_today) {
    return '0%'
  }
  const percentage = (todayOverview.value.completed_today / todayOverview.value.total_today) * 100
  return `${percentage.toFixed(0)}%`
})

const fetchProgressData = async () => {
  loading.value.data = true
  try {
    console.log('获取新进度数据...')
    const response = (await request.get('/api/shipping/picking/new-progress')) as ApiResponseBody &
      Record<string, unknown>

    console.log('API响应:', response)

    const normalized = normalizePickingProgressResponse(response)
    if (!normalized.ok) {
      console.error('API请求失败:', normalized.message)
      ElMessage.error(normalized.message || 'データの取得に失敗しました')
      return
    }
    const responseData = normalized.responseData

    if (responseData && typeof responseData === 'object') {
      const filteredResponse = filterProductDataForPickingProgress(responseData) as Record<string, unknown>

      palletList.value = (filteredResponse.palletList as PalletInfo[]) || []
      progressStats.value = (filteredResponse.progressStats as ProgressStats[]) || [
        { id: 1, name: 'Test Progress 1' },
        { id: 2, name: 'Test Progress 2' },
      ]

      // 设置今日概览数据
      const overview = filteredResponse.todayOverview as TodayOverview | undefined
      if (
        overview &&
        (overview.total_today > 0 || overview.pending_today > 0 || overview.completed_today > 0)
      ) {
        todayOverview.value = overview as TodayOverview
      } else {
        todayOverview.value = {
          total_today: 0,
          pending_today: 0,
          completed_today: 0,
          today_completion_rate: 0,
        }
      }

      ElMessage.success(`データを取得しました (${palletList.value.length}件)`)
    } else {
      console.error('API响应格式错误:', responseData)
      ElMessage.error('データの取得に失敗しました')
    }
  } catch (error: any) {
    console.error('数据获取失败:', error)
    ElMessage.error(`データの取得に失敗しました: ${error.message || 'Unknown error'}`)
  } finally {
    loading.value.data = false
  }
}

function refreshStats() {
  fetchProgressData()
}

function syncErrorMessage(error: any): string {
  const isTimeout =
    error?.code === 'ECONNABORTED' ||
    String(error?.message || '').toLowerCase().includes('timeout')
  if (isTimeout) {
    return 'ピッキングログ突合せの処理に時間がかかっています。しばらくしてから進捗を再読込してください。'
  }
  const d = error?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d) && d[0]?.msg) return d.map((x: any) => x.msg).join(' ')
  return error?.message || 'ピッキングログ突合せに失敗しました'
}

async function handleSyncData() {
  if (!guardSalesOperation(canCreate)) return

  syncLoading.value = true
  syncProgress.value = 8
  clearSyncProgressTimer()
  syncProgressTimer = setInterval(tickSyncProgress, 140)

  try {
    const startResponse = (await startRefreshPickingLogMatchedTask()) as ApiResponseBody &
      Record<string, any>
    const startData = (startResponse.data ?? startResponse) as Record<string, any>
    const taskId = String(startData.task_id || '')
    if (!taskId) {
      throw new Error(startResponse.message || 'task_id が取得できませんでした')
    }

    let finalTask: PickingSyncTaskStatus | null = null
    const maxPoll = 600 // 最大 10 分
    for (let i = 0; i < maxPoll; i += 1) {
      await new Promise((r) => setTimeout(r, 1000))
      const statusResponse = (await getRefreshPickingLogMatchedTask(taskId)) as ApiResponseBody &
        Record<string, any>
      const task = (statusResponse.data ?? statusResponse) as PickingSyncTaskStatus
      const p = Number(task.progress_percent ?? 0)
      if (Number.isFinite(p)) {
        syncProgress.value = Math.max(syncProgress.value, Math.min(99, p))
      }
      if (task.status === 'completed' || task.status === 'failed') {
        finalTask = task
        break
      }
    }

    clearSyncProgressTimer()
    syncProgress.value = 100
    await new Promise((r) => setTimeout(r, 380))

    if (!finalTask) {
      ElMessage.warning('処理は継続中です。しばらくしてから再読込してください。')
      return
    }
    if (finalTask.status === 'completed') {
      ElMessage.success(
        finalTask.message || `ピッキングログ突合せが完了しました（更新: ${Number(finalTask.updated_rows || 0)}）`,
      )
      refreshStats()
    } else {
      ElMessage.error(finalTask.error || finalTask.message || 'ピッキングログ突合せに失敗しました')
    }
  } catch (error: any) {
    clearSyncProgressTimer()
    syncProgress.value = 100
    await new Promise((r) => setTimeout(r, 220))
    console.error('ピッキングログ突合せエラー:', error)
    ElMessage.error(syncErrorMessage(error))
  } finally {
    clearSyncProgressTimer()
    syncLoading.value = false
    await new Promise((r) => setTimeout(r, 280))
    syncProgress.value = 0
  }
}

function handleTabChange(tabName: string | number) {
  if (!guardSalesOperation(canEdit)) return

  console.log('切换到标签页:', tabName)
}

onMounted(() => {
  const raw = route.query.tab
  const tab = typeof raw === 'string' ? raw : Array.isArray(raw) ? raw[0] : ''
  if (tab === 'progress' || tab === 'generate' || tab === 'history') {
    activeTab.value = tab
  }
  fetchProgressData()
})

onBeforeUnmount(() => {
  clearSyncProgressTimer()
})
</script>

<style scoped>
/* ============================================================ */
/* 页面美化：出荷ピッキング管理（インディゴ〜スカイ系・淡色ベース） */
/* ============================================================ */
.picking-management {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 100%;
  padding: 10px 12px 14px;
  box-sizing: border-box;
  background: linear-gradient(180deg, #eef0ff 0%, #f8fafc 30%, #f8fafc 100%);
}

/* ---------- ヒーロー ---------- */
.page-header {
  margin: 0;
}

.header-content {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(125deg, #312e81 0%, #4338ca 34%, #6366f1 68%, #0ea5e9 100%);
  box-shadow:
    0 12px 28px -18px rgba(67, 56, 202, 0.7),
    0 1px 2px rgba(15, 23, 42, 0.06);
}

.header-left {
  min-width: 0;
}

.title-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon-wrapper {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(30, 27, 75, 0.3);
}

.title-icon {
  font-size: 20px;
  color: #fff;
}

.title-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.main-title {
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.03em;
  color: #fff;
}

.subtitle {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 5px;
  color: rgba(255, 255, 255, 0.88);
}

.subtitle-icon {
  font-size: 12px;
}

.header-right {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 同期：ヒーロー上の白ピル */
.sync-btn {
  --k-rgb: 79 70 229;
  height: 30px;
  padding: 0 14px;
  border-radius: 999px;
  font-weight: 700;
  color: #4338ca;
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%);
}

.sync-btn:not(.is-disabled):hover,
.sync-btn:focus-visible {
  color: #3730a3;
  border-color: #fff;
  background: #fff;
}

/* ---------- 同期進捗バナー ---------- */
.sync-progress-banner {
  position: relative;
  overflow: hidden;
  padding: 10px 14px 12px 17px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #dfe3fb;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.sync-progress-banner::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: linear-gradient(180deg, #818cf8, #4f46e5);
}

.sync-progress-hint {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  color: #3730a3;
}

.sync-progress-el :deep(.el-progress-bar__outer) {
  border-radius: 999px;
  overflow: hidden;
  background: #eef2ff !important;
  box-shadow: inset 0 0 0 1px #e0e7ff;
}

.sync-progress-el :deep(.el-progress-bar__inner) {
  border-radius: 999px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0) 60%),
    linear-gradient(90deg, #818cf8, #4f46e5);
}

.sync-progress-el :deep(.el-progress__text) {
  font-size: 12px !important;
  font-weight: 800;
  color: #4338ca !important;
  font-variant-numeric: tabular-nums;
}

.sync-progress-fade-enter-active,
.sync-progress-fade-leave-active {
  transition: opacity 0.2s ease;
}

.sync-progress-fade-enter-from,
.sync-progress-fade-leave-to {
  opacity: 0;
}

/* ---------- 本日の統計カード（色分け・左アクセントバー） ---------- */
.status-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.stat-card {
  --accent: #4f46e5;
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--accent) 18%, #e2e8f0);
  background: linear-gradient(160deg, color-mix(in srgb, var(--accent) 6%, #fff) 0%, #fff 70%);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--accent) 45%, #fff), var(--accent));
}

.progress-card {
  --accent: #e11d48;
}

.completed-card {
  --accent: #0284c7;
}

.efficiency-card {
  --accent: #059669;
}

.stat-card :deep(.el-card__body) {
  padding: 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 62px;
  padding: 10px 12px 10px 14px;
  box-sizing: border-box;
}

.stat-icon-container {
  flex-shrink: 0;
}

.stat-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  font-size: 17px;
  color: #fff;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.24) 0%, rgba(255, 255, 255, 0) 55%),
    linear-gradient(135deg, color-mix(in srgb, var(--accent) 60%, #fff), var(--accent));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(15, 23, 42, 0.18);
}

.stat-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.stat-number-container {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.stat-number {
  font-size: 22px;
  font-weight: 800;
  line-height: 1;
  color: color-mix(in srgb, var(--accent) 75%, #0f172a);
  font-variant-numeric: tabular-nums;
}

.stat-percent {
  font-size: 13px;
  font-weight: 700;
  color: var(--accent);
}

.stat-trend {
  display: inline-flex;
  align-items: center;
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  color: #047857;
  background: #d1fae5;
  box-shadow: inset 0 -1px 0 #a7f3d0;
}

.stat-badge {
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  color: #be123c;
  background: #ffe4e6;
  box-shadow: inset 0 -1px 0 #fecdd3;
}

.stat-label {
  font-size: 11px;
  font-weight: 600;
  line-height: 1.2;
  color: #64748b;
}

.stat-progress {
  height: 4px;
  margin-top: 3px;
  border-radius: 999px;
  overflow: hidden;
  background: color-mix(in srgb, var(--accent) 10%, #eef2f7);
}

.progress-bar {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 55%, #fff), var(--accent));
  transition: width 0.6s ease;
}

.circular-progress {
  position: absolute;
  top: 7px;
  right: 8px;
  transform: scale(0.82);
  transform-origin: top right;
}

.progress-ring {
  transform: rotate(-90deg);
}

.progress-ring-circle,
.progress-ring-progress {
  transition: stroke-dasharray 0.6s ease;
}

/* ---------- メインパネル ---------- */
.main-content {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.main-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 1;
  background: linear-gradient(90deg, #4f46e5 0%, #6366f1 55%, #0ea5e9 100%);
}

.main-content > :deep(.el-card__body) {
  padding: 0;
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px 9px;
  background: linear-gradient(180deg, #f5f6ff 0%, #fff 100%);
  border-bottom: 1px solid #e6e8fb;
}

.content-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.03em;
  color: #312e81;
}

.content-title .el-icon {
  width: 22px;
  height: 22px;
  padding: 4px;
  box-sizing: border-box;
  border-radius: 6px;
  font-size: 13px;
  color: #fff;
  background: linear-gradient(135deg, #818cf8, #4f46e5);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(30, 27, 75, 0.3);
}

/* タブ：セグメント（子コンポーネント内のタブには及ばないよう直下のみ） */
.custom-tabs {
  padding: 0 12px 12px;
}

.custom-tabs > :deep(.el-tabs__header) {
  position: sticky;
  top: 0;
  z-index: 5;
  margin: 0 0 10px;
  padding-top: 10px;
  border-bottom: 0;
  background: #fff;
}

.custom-tabs > :deep(.el-tabs__header .el-tabs__nav-wrap::after),
.custom-tabs > :deep(.el-tabs__header .el-tabs__active-bar) {
  display: none;
}

.custom-tabs > :deep(.el-tabs__header .el-tabs__nav) {
  gap: 2px;
  padding: 3px;
  border-radius: 11px;
  background: #eef0fb;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.08);
}

.custom-tabs > :deep(.el-tabs__header .el-tabs__item) {
  height: 32px;
  padding: 0 14px !important;
  border-radius: 9px;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
  transition:
    background-color 0.15s ease,
    color 0.15s ease;
}

.custom-tabs > :deep(.el-tabs__header .el-tabs__item:hover) {
  color: #4338ca;
  background: rgba(255, 255, 255, 0.6);
}

.custom-tabs > :deep(.el-tabs__header .el-tabs__item.is-active) {
  color: #4338ca;
  background: #fff;
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgba(79, 70, 229, 0.18),
    0 1px 3px rgba(15, 23, 42, 0.1);
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 5px;
}

.tab-label .el-icon {
  font-size: 14px;
}

.custom-tabs > :deep(.el-tabs__content) {
  padding: 0;
}

.custom-tabs :deep(.el-tab-pane) {
  padding-top: 0;
}

/* ---------- 子コンポーネントの余白圧縮（従来どおり） ---------- */
:deep(.picking-list-generator),
:deep(.picking-progress-container),
:deep(.picking-history-container) {
  min-height: auto !important;
  padding: 0 !important;
  background: transparent !important;
}

:deep(.picking-progress-container .page-header),
:deep(.picking-history-container .page-header) {
  margin-bottom: 8px !important;
}

:deep(.picking-progress-container .page-title),
:deep(.picking-history-container .page-title) {
  font-size: 15px !important;
}

:deep(.picking-progress-container .page-subtitle),
:deep(.picking-history-container .page-subtitle) {
  font-size: 11px !important;
}

:deep(.picking-progress-container .overview-section),
:deep(.picking-progress-container .analytics-section),
:deep(.picking-progress-container .data-section),
:deep(.picking-history-container .filter-card),
:deep(.picking-history-container .stats-grid),
:deep(.picking-history-container .chart-card),
:deep(.picking-history-container .performer-analysis-card),
:deep(.picking-history-container .daily-rate-chart-card),
:deep(.picking-history-container .table-card) {
  margin-bottom: 8px !important;
}

.custom-tabs :deep(.el-card__header) {
  padding: 8px 12px;
}

.custom-tabs :deep(.el-card__body) {
  padding: 10px 12px;
}

.custom-tabs :deep(.el-table) {
  --el-table-header-bg-color: #f5f6ff;
  font-size: 12px;
}

.custom-tabs :deep(.el-table th),
.custom-tabs :deep(.el-table td) {
  padding: 6px 8px;
}

/* ---------- レスポンシブ ---------- */
@media (max-width: 1200px) {
  .status-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .picking-management {
    padding: 8px;
  }

  .header-right {
    width: 100%;
  }

  .header-btn {
    flex: 1;
    min-width: 0;
  }

  .stat-item {
    min-height: 56px;
  }

  .stat-number {
    font-size: 18px;
  }

  .custom-tabs {
    padding: 0 8px 8px;
  }

  .custom-tabs > :deep(.el-tabs__header .el-tabs__item) {
    padding: 0 10px !important;
    font-size: 11px;
  }
}

@media (max-width: 600px) {
  .status-cards {
    grid-template-columns: 1fr;
  }
}
</style>
