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
              <h1 class="main-title">出荷ピッキング管理システム</h1>
              <p class="subtitle">
                <el-icon class="subtitle-icon">
                  <LocationInformation />
                </el-icon>
                出荷作業のピッキング管理・進捗追跡システム
              </p>
            </div>
          </div>
        </div>
        <div class="header-right">
          <el-button type="warning" :icon="Tools" :loading="initLoading" @click="handleInitDatabase" size="large"
            class="header-btn init-btn">
            <span>データベース初期化</span>
          </el-button>

          <el-button type="primary" :icon="Refresh" :loading="syncLoading" @click="handleSyncData" size="large"
            class="header-btn sync-btn">
            <span>{{ $t('menu.shipping.picking.syncData') }}</span>
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
            <span class="stat-label">今日ピッキング件数</span>
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
              <div class="stat-badge pending">進行中</div>
            </div>
            <span class="stat-label">今日作業中</span>
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
            <span class="stat-label">今日完了</span>
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
            <span class="stat-label">今日完了率</span>
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
          管理パネル
        </h2>
      </div>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="custom-tabs">
        <el-tab-pane name="generate">
          <template #label>
            <div class="tab-label">
              <el-icon>
                <List />
              </el-icon>
              <span>ピッキングリスト</span>
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
              <span>進捗管理</span>
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
              <span>履歴・分析</span>
            </div>
          </template>
          <PickingHistory />
        </el-tab-pane>

        <el-tab-pane name="fileWatcher">
          <template #label>
            <div class="tab-label">
              <el-icon>
                <Monitor />
              </el-icon>
              <span>ファイル監視器</span>
            </div>
          </template>
          <FileWatcherManager />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
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
  Monitor,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import { syncShippingDataToPickingTasks } from '@/api/shipping/picking'
import PickingListGenerator from './components/PickingListGenerator.vue'
import PickingProgress from './components/PickingProgress.vue'
import PickingHistory from './components/PickingHistory.vue'
import FileWatcherManager from './components/FileWatcherManager.vue'

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

// 获取日本标准时间（JST）的今天日期
const getJSTToday = () => {
  const now = new Date()
  const jstOffset = 9 * 60 // JST是UTC+9
  const jstTime = new Date(now.getTime() + jstOffset * 60 * 1000)
  return jstTime.toISOString().slice(0, 10)
}

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
    ElMessage.error(error.message || 'データベース初期化に失敗しました')
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
    ElMessage.error(error.message || 'データ同期に失敗しました')
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
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #6b73ff 100%);
  min-height: 100vh;
  overflow: hidden;
}

/* 背景装饰 - 简化版 */
.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  opacity: 0.6;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  animation: float 8s ease-in-out infinite;
}

.shape-1 {
  width: 80px;
  height: 80px;
  top: 5%;
  left: 85%;
  animation-delay: 0s;
}

.shape-2 {
  width: 50px;
  height: 50px;
  top: 75%;
  left: 5%;
  animation-delay: 2s;
}

.shape-3 {
  width: 60px;
  height: 60px;
  top: 15%;
  left: 15%;
  animation-delay: 4s;
}

.shape-4 {
  width: 90px;
  height: 90px;
  top: 65%;
  right: 15%;
  animation-delay: 1s;
}

@keyframes float {

  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.6;
  }

  50% {
    transform: translateY(-15px) rotate(180deg);
    opacity: 0.3;
  }
}

/* 页面头部 - 紧凑版 */
.page-header {
  position: relative;
  z-index: 1;
  margin-bottom: 16px;
  color: white;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.title-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 14px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.title-icon {
  font-size: 28px;
  color: white;
}

.title-text {
  flex: 1;
  min-width: 0;
}

.main-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px 0;
  background: linear-gradient(45deg, #fff, #e0e7ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
}

.subtitle {
  font-size: 13px;
  opacity: 0.85;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.subtitle-icon {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.header-btn {
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  font-weight: 500;
}

.header-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.init-btn {
  background: linear-gradient(135deg, #ffeaa7, #fdcb6e);
  border-color: #fdcb6e;
}

.sync-btn {
  background: linear-gradient(135deg, #74b9ff, #0984e3);
  border-color: #74b9ff;
}

/* 状态统计卡片 - 紧凑版 */
.status-cards {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.stat-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px;
}

.stat-icon-container {
  position: relative;
  flex-shrink: 0;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: white;
  position: relative;
  z-index: 2;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.stat-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  border-radius: 50%;
  opacity: 0.25;
  animation: pulse 2.5s infinite;
}

@keyframes pulse {

  0%,
  100% {
    transform: translate(-50%, -50%) scale(0.9);
    opacity: 0.3;
  }

  50% {
    transform: translate(-50%, -50%) scale(1.1);
    opacity: 0.15;
  }
}

.stat-icon.today {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.today-pulse {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.stat-icon.progress {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.progress-pulse {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.stat-icon.completed {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.completed-pulse {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.stat-icon.efficiency {
  background: linear-gradient(135deg, #a8edea, #fed6e3);
}

.efficiency-pulse {
  background: linear-gradient(135deg, #a8edea, #fed6e3);
}

.stat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.stat-number-container {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #1a202c;
  line-height: 1;
}

.stat-percent {
  font-size: 18px;
  font-weight: 600;
  color: #667eea;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 3px 6px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
}

.stat-trend.up {
  background: linear-gradient(135deg, #d4f6cc, #c3f0ca);
  color: #22c55e;
}

.stat-badge {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  color: #d97706;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  line-height: 1.3;
}

.stat-progress {
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
  margin-top: 6px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 2px;
  transition: width 0.8s ease;
}

.progress-bar-orange {
  background: linear-gradient(90deg, #f093fb, #f5576c);
}

.progress-bar-green {
  background: linear-gradient(90deg, #4facfe, #00f2fe);
}

.circular-progress {
  position: absolute;
  top: 16px;
  right: 16px;
}

.progress-ring {
  transform: rotate(-90deg);
}

.progress-ring-circle {
  transition: stroke-dasharray 0.8s ease;
}

.progress-ring-progress {
  transition: stroke-dasharray 0.8s ease;
}

/* 主要功能区域 - 紧凑版 */
.main-content {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.5);
}

.content-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #2d3748;
  margin: 0;
}

.content-title .el-icon {
  font-size: 18px;
  color: #667eea;
}

.content-actions {
  display: flex;
  gap: 6px;
}

.custom-tabs {
  padding: 0 18px;
}

:deep(.el-tabs__header) {
  margin-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

:deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
  transition: all 0.2s ease;
  padding: 12px 16px;
  margin-right: 4px;
  border-radius: 8px 8px 0 0;
}

:deep(.el-tabs__item:hover) {
  color: #667eea;
  background: rgba(102, 126, 234, 0.06);
}

:deep(.el-tabs__item.is-active) {
  color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
  border-bottom: 2px solid #667eea;
  font-weight: 600;
}

:deep(.el-tabs__active-bar) {
  display: none;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-label .el-icon {
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .picking-management {
    padding: 12px;
  }

  .page-header {
    margin-bottom: 12px;
  }

  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .title-container {
    gap: 10px;
  }

  .title-icon-wrapper {
    width: 48px;
    height: 48px;
  }

  .title-icon {
    font-size: 24px;
  }

  .main-title {
    font-size: 20px;
  }

  .subtitle {
    font-size: 12px;
  }

  .header-right {
    width: 100%;
    justify-content: stretch;
  }

  .header-btn {
    flex: 1;
  }

  .status-cards {
    grid-template-columns: 1fr;
    gap: 10px;
    margin-bottom: 12px;
  }

  .stat-item {
    padding: 14px;
  }

  .content-header {
    padding: 12px 16px;
  }

  .custom-tabs {
    padding: 0 16px;
  }

  :deep(.el-tabs__header) {
    margin-bottom: 12px;
  }
}

@media (max-width: 480px) {
  .picking-management {
    padding: 10px;
  }

  .header-right {
    flex-direction: column;
  }

  .stat-number {
    font-size: 24px;
  }

  .stat-icon {
    width: 42px;
    height: 42px;
    font-size: 20px;
  }
}
</style>
