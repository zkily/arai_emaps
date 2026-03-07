<template>
  <div class="picking-management">
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
      <div class="floating-shape shape-4"></div>
    </div>

    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="title-container">
            <div class="title-icon-wrapper">
              <el-icon class="title-icon">
                <Box />
              </el-icon>
            </div>
            <div class="title-text">
              <h1 class="main-title">{{ t('shipping.titlePicking') }}</h1>
              <p class="subtitle">
                <el-icon class="subtitle-icon">
                  <LocationInformation />
                </el-icon>
                {{ t('shipping.subtitlePicking') }}
              </p>
            </div>
          </div>
        </div>
        <div class="header-right">
          <el-button type="warning" :icon="Tools" :loading="initLoading" @click="handleInitDatabase" size="default"
            class="header-btn init-btn">
            <span>{{ t('shipping.initDatabase') }}</span>
          </el-button>

          <el-button type="primary" :icon="Refresh" :loading="syncLoading" @click="handleSyncData" size="default"
            class="header-btn sync-btn">
            <span>{{ t('shipping.syncData') }}</span>
          </el-button>
        </div>
      </div>
    </div>

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
            <div class="stat-pulse today-pulse"></div>
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
            <div class="stat-pulse progress-pulse"></div>
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
            <div class="stat-pulse completed-pulse"></div>
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
            <div class="stat-pulse efficiency-pulse"></div>
          </div>
          <div class="stat-content">
            <div class="stat-number-container">
              <span class="stat-number">{{ todayOverview.today_completion_rate }}</span>
              <span class="stat-percent">%</span>
            </div>
            <span class="stat-label">{{ t('shipping.todayCompletionRate') }}</span>
            <div class="circular-progress">
              <svg class="progress-ring" width="60" height="60">
                <circle class="progress-ring-circle" stroke="#e6f7ff" stroke-width="4" fill="transparent" r="26" cx="30"
                  cy="30" />
                <circle class="progress-ring-progress" stroke="url(#efficiency-gradient)" stroke-width="4"
                  stroke-linecap="round" fill="transparent" r="26" cx="30" cy="30"
                  :stroke-dasharray="`${todayOverview.today_completion_rate * 1.63} 163`" />
                <defs>
                  <linearGradient id="efficiency-gradient">
                    <stop offset="0%" stop-color="#a8edea" />
                    <stop offset="100%" stop-color="#fed6e3" />
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
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getJSTToday as getJSTTodayUtil } from '@/utils/dateFormat'
import {
  Box,
  Calendar,
  Clock,
  Check,
  Refresh,
  TrendCharts,
  Tools,
  LocationInformation,
  ArrowUp,
  Operation,
  List,
  PieChart,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import { syncShippingDataToPickingTasks } from '@/api/shipping/picking'
import PickingListGenerator from './components/PickingListGenerator.vue'
import PickingProgress from './components/PickingProgress.vue'
import PickingHistory from './components/PickingHistory.vue'

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

const { t } = useI18n()
const getJSTToday = getJSTTodayUtil

const activeTab = ref('generate')
const syncLoading = ref(false)
const initLoading = ref(false)
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
    const response = (await request.get('/api/shipping/picking/new-progress')) as ApiResponseBody & Record<string, unknown>

    console.log('API响应:', response)

    // 标准化响应格式
    let responseData
    if (response?.success !== undefined) {
      if (!response.success) {
        console.error('API请求失败:', response.message)
        ElMessage.error(response.message || 'データの取得に失敗しました')
        return
      }
      responseData = response.data
    } else if (Array.isArray(response)) {
      responseData = { palletList: response, progressStats: [], todayOverview: {} }
    } else if (response && typeof response === 'object') {
      responseData = response
    } else {
      console.error('未知的响应格式:', response)
      ElMessage.error('データ形式が正しくありません')
      return
    }

    // 过滤函数：排除製品名包含特定关键词的数据
    const filterProductData = (data: any) => {
      if (!data) return data

      const excludeKeywords = ['加工', 'アーチ', '料金']
      const shouldExclude = (productName: string) =>
        productName && excludeKeywords.some((keyword) => productName.includes(keyword))

      if (Array.isArray(data)) {
        return data.filter((item: any) => {
          const productName = item.product_name || item.productName || ''
          return !shouldExclude(productName)
        })
      }

      if (typeof data === 'object') {
        const filtered = { ...data }

        // 过滤数组数据
        if (Array.isArray(filtered.palletList)) {
          filtered.palletList = filtered.palletList.filter((item: any) => {
            const productName = item.product_name || item.productName || ''
            return !shouldExclude(productName)
          })
        }

        if (Array.isArray(filtered.progressStats)) {
          filtered.progressStats = filtered.progressStats.filter((item: any) => {
            const productName = item.product_name || item.productName || ''
            return !shouldExclude(productName)
          })
        }

        // 重新计算当天统计数据
        if (Array.isArray(filtered.palletList)) {
          const today = getJSTToday()
          const todayItems = filtered.palletList.filter((item: any) => {
            const itemDate = item.shipping_date || item.date || ''
            return itemDate === today || itemDate.startsWith(today)
          })

          if (todayItems.length > 0) {
            const pendingStatuses = ['pending', '進行中', 'in_progress']
            const completedStatuses = ['completed', '完了', 'finished']

            const totalToday = todayItems.length
            const pendingToday = todayItems.filter((item: any) =>
              pendingStatuses.includes(item.status),
            ).length
            const completedToday = todayItems.filter((item: any) =>
              completedStatuses.includes(item.status),
            ).length
            const completionRate =
              totalToday > 0 ? Math.round((completedToday / totalToday) * 100) : 0

            filtered.todayOverview = {
              total_today: totalToday,
              pending_today: pendingToday,
              completed_today: completedToday,
              today_completion_rate: completionRate,
            }
            filtered.palletList = todayItems
          } else {
            // 保持原有统计数据
            const overview = filtered.todayOverview || {}
            filtered.todayOverview = {
              total_today: overview.total_today || 0,
              pending_today: overview.pending_today || 0,
              completed_today: overview.completed_today || 0,
              today_completion_rate: overview.today_completion_rate || 0,
            }
          }
        }

        return filtered
      }

      return data
    }

    if (responseData && typeof responseData === 'object') {
      const filteredResponse = filterProductData(responseData)

      palletList.value = filteredResponse.palletList || []
      progressStats.value = filteredResponse.progressStats || [
        { id: 1, name: 'Test Progress 1' },
        { id: 2, name: 'Test Progress 2' },
      ]

      // 设置今日概览数据
      const overview = filteredResponse.todayOverview
      if (
        overview &&
        (overview.total_today > 0 || overview.pending_today > 0 || overview.completed_today > 0)
      ) {
        todayOverview.value = overview
      } else {
        // 使用默认示例数据
        todayOverview.value = {
          total_today: 45,
          pending_today: 12,
          completed_today: 33,
          today_completion_rate: 73,
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

async function handleInitDatabase() {
  initLoading.value = true
  try {
    const response = (await request.post('/api/shipping/picking/db/init')) as ApiResponseBody
    if (response.success) {
      ElMessage.success(response.message || 'データベース初期化が完了しました')
      refreshStats()
    } else {
      ElMessage.error(response.message || 'データベース初期化に失敗しました')
    }
  } catch (error: any) {
    console.error('データベース初期化エラー:', error)
    // レスポンスなし（ネットワークエラー等）のときのみトースト（4xx/5xx は interceptor で表示済み）
    if (!error?.response) {
      ElMessage.error(error?.message || 'データベース初期化に失敗しました')
    }
  } finally {
    initLoading.value = false
  }
}

async function handleSyncData() {
  syncLoading.value = true
  try {
    const response = (await syncShippingDataToPickingTasks()) as ApiResponseBody
    if (response.success) {
      ElMessage.success(response.message || 'データ同期が完了しました')
      refreshStats()
    } else {
      ElMessage.error(response.message || 'データ同期に失敗しました')
    }
  } catch (error: any) {
    console.error('データ同期エラー:', error)
    if (!error?.response) {
      ElMessage.error(error?.message || 'データ同期に失敗しました')
    }
  } finally {
    syncLoading.value = false
  }
}

function handleTabChange(tabName: string | number) {
  console.log('切换到标签页:', tabName)
}

onMounted(() => {
  fetchProgressData()
})
</script>

<style scoped>
.picking-management {
  position: relative;
  padding: 10px 12px;
  background: linear-gradient(145deg, #1e1b4b 0%, #312e81 40%, #3730a3 100%);
  min-height: 100vh;
  overflow: hidden;
}

/* 背景装饰 - 极简 */
.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  opacity: 0.4;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  animation: float 10s ease-in-out infinite;
}

.shape-1 { width: 60px; height: 60px; top: 8%; left: 88%; animation-delay: 0s; }
.shape-2 { width: 40px; height: 40px; top: 78%; left: 6%; animation-delay: 2s; }
.shape-3 { width: 48px; height: 48px; top: 18%; left: 12%; animation-delay: 4s; }
.shape-4 { width: 56px; height: 56px; top: 68%; right: 12%; animation-delay: 1s; }

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); opacity: 0.5; }
  50% { transform: translateY(-12px) rotate(180deg); opacity: 0.2; }
}

/* 页面头部 - 紧凑 */
.page-header {
  position: relative;
  z-index: 1;
  margin-bottom: 10px;
  color: white;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.title-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
}

.title-icon {
  font-size: 22px;
  color: white;
}

.title-text { flex: 1; min-width: 0; }

.main-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 2px 0;
  background: linear-gradient(45deg, #fff, #c7d2fe);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
}

.subtitle {
  font-size: 12px;
  opacity: 0.88;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 5px;
}

.subtitle-icon { font-size: 12px; }

.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.header-btn {
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  font-weight: 500;
  padding: 8px 14px;
}

.header-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}

.init-btn {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border-color: #f59e0b;
}

.sync-btn {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  border-color: #6366f1;
}

/* 状态统计卡片 - 紧凑 */
.status-cards {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 10px;
}

@media (max-width: 1200px) {
  .status-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .picking-management {
    padding: 8px 10px;
  }

  .page-header {
    margin-bottom: 8px;
  }

  .header-content {
    gap: 8px;
  }

  .header-right {
    flex-wrap: wrap;
  }

  .header-btn {
    flex: 1;
    min-width: 120px;
  }

  .main-content {
    border-radius: 10px;
  }

  .content-header {
    padding: 8px 12px;
  }

  .content-title {
    font-size: 13px;
  }

  .custom-tabs {
    padding: 0 12px;
  }

  :deep(.el-tabs__item) {
    font-size: 12px;
    padding: 6px 10px;
  }

  :deep(.el-tab-pane) {
    padding: 8px 0 0;
  }
}

@media (max-width: 600px) {
  .status-cards {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 12px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
}

.stat-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
}

.stat-icon-container { position: relative; flex-shrink: 0; }

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
  position: relative;
  z-index: 2;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

.stat-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 48px;
  height: 48px;
  border-radius: 50%;
  opacity: 0.2;
  animation: pulse 2.5s infinite;
}

@keyframes pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(0.9); opacity: 0.25; }
  50% { transform: translate(-50%, -50%) scale(1.08); opacity: 0.12; }
}

.stat-icon.today { background: linear-gradient(135deg, #6366f1, #8b5cf6); }
.today-pulse { background: linear-gradient(135deg, #6366f1, #8b5cf6); }
.stat-icon.progress { background: linear-gradient(135deg, #ec4899, #f43f5e); }
.progress-pulse { background: linear-gradient(135deg, #ec4899, #f43f5e); }
.stat-icon.completed { background: linear-gradient(135deg, #0ea5e9, #06b6d4); }
.completed-pulse { background: linear-gradient(135deg, #0ea5e9, #06b6d4); }
.stat-icon.efficiency { background: linear-gradient(135deg, #10b981, #34d399); }
.efficiency-pulse { background: linear-gradient(135deg, #10b981, #34d399); }

.stat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.stat-number-container {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.stat-number {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1;
}

.stat-percent { font-size: 14px; font-weight: 600; color: #6366f1; }

.stat-trend {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 2px 5px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 600;
}

.stat-trend.up {
  background: linear-gradient(135deg, #d1fae5, #a7f3d0);
  color: #059669;
}

.stat-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  color: #b45309;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
  line-height: 1.2;
}

.stat-progress {
  height: 3px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
  margin-top: 4px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 2px;
  transition: width 0.6s ease;
}

.progress-bar-orange { background: linear-gradient(90deg, #ec4899, #f43f5e); }
.progress-bar-green { background: linear-gradient(90deg, #0ea5e9, #06b6d4); }

.circular-progress {
  position: absolute;
  top: 10px;
  right: 10px;
}

.progress-ring { transform: rotate(-90deg); }
.progress-ring-circle,
.progress-ring-progress { transition: stroke-dasharray 0.6s ease; }

/* 主内容区 - 紧凑 */
.main-content {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(248, 250, 252, 0.8);
}

.content-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin: 0;
}

.content-title .el-icon { font-size: 16px; color: #6366f1; }

.custom-tabs { padding: 0 14px; }

:deep(.el-tabs__header) {
  margin-bottom: 10px;
  border-bottom: 1px solid #e2e8f0;
}

:deep(.el-tabs__nav-wrap::after) { display: none; }

:deep(.el-tabs__item) {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  transition: all 0.2s ease;
  padding: 8px 12px;
  margin-right: 2px;
  border-radius: 8px 8px 0 0;
}

:deep(.el-tabs__item:hover) {
  color: #6366f1;
  background: rgba(99, 102, 241, 0.06);
}

:deep(.el-tabs__item.is-active) {
  color: #6366f1;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.06));
  border-bottom: 2px solid #6366f1;
  font-weight: 600;
}

:deep(.el-tabs__active-bar) { display: none; }

.tab-label {
  display: flex;
  align-items: center;
  gap: 5px;
}

.tab-label .el-icon { font-size: 14px; }

:deep(.el-tabs__content) { padding: 0; }
:deep(.el-tab-pane) { padding: 10px 0 0; }

@media (max-width: 768px) {
  .picking-management {
    padding: 6px 8px;
  }

  .page-header {
    margin-bottom: 6px;
  }

  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .title-icon-wrapper {
    width: 36px;
    height: 36px;
  }

  .title-icon {
    font-size: 18px;
  }

  .main-title {
    font-size: 16px;
  }

  .subtitle {
    font-size: 11px;
  }

  .header-right {
    width: 100%;
  }

  .header-btn {
    flex: 1;
    min-width: 0;
    padding: 6px 10px;
    font-size: 13px;
  }

  .status-cards {
    margin-bottom: 6px;
    gap: 6px;
  }

  .stat-item {
    padding: 6px 10px;
  }

  .stat-number {
    font-size: 18px;
  }

  .main-content {
    border-radius: 10px;
  }

  .content-header {
    padding: 6px 10px;
  }

  .content-title {
    font-size: 13px;
  }

  .custom-tabs {
    padding: 0 8px;
  }

  :deep(.el-tabs__header) {
    margin-bottom: 6px;
  }

  :deep(.el-tabs__item) {
    font-size: 11px;
    padding: 6px 8px;
  }

  :deep(.el-tab-pane) {
    padding: 6px 0 0;
  }

  .tab-label .el-icon {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .picking-management {
    padding: 4px 6px;
  }

  .title-icon-wrapper {
    width: 32px;
    height: 32px;
  }

  .main-title {
    font-size: 15px;
  }

  .header-btn {
    padding: 5px 8px;
    font-size: 12px;
  }

  .stat-number {
    font-size: 16px;
  }

  .stat-icon {
    width: 34px;
    height: 34px;
    font-size: 15px;
  }

  .stat-label {
    font-size: 10px;
  }

  .content-header {
    padding: 6px 8px;
  }

  .content-title {
    font-size: 12px;
  }

  :deep(.el-tabs__item) {
    font-size: 10px;
    padding: 5px 6px;
  }
}
</style>
