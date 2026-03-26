<template>
  <div class="inventory-container">
    <!-- 动态背景 -->
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="32">
              <Box />
            </el-icon>
          </div>
          <div class="header-text">
            <h1 class="main-title">棚卸リスト一覧</h1>
            <p class="subtitle">棚卸リスト(材料、部品、仕掛品の各工程、製品)</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button
            type="primary"
            @click="handleImport"
            :loading="loading"
            :icon="DocumentAdd"
            class="import-button"
          >
            棚卸データ取込
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content-container">
      <!-- 筛选表单 -->
      <el-card class="filter-card" shadow="hover">
        <template #header>
          <div class="filter-header">
            <el-icon class="filter-icon">
              <Search />
            </el-icon>
            <span class="filter-title">検索フィルタ</span>
          </div>
        </template>

        <el-form :inline="true" :model="filters" class="filter-form" @submit.prevent>
          <div class="filter-row">
            <el-form-item label="キーワード" class="filter-item">
              <el-input
                v-model="filters.keyword"
                placeholder="製品名で検索"
                clearable
                class="filter-input"
                :prefix-icon="Search"
              />
            </el-form-item>

            <el-form-item label="日付範囲" class="filter-item">
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

            <div class="filter-actions">
              <el-button type="primary" :icon="Search" @click="handleSearch" class="search-button">
                検索
              </el-button>
              <el-button :icon="RefreshLeft" @click="resetFilters" class="reset-button">
                リセット
              </el-button>
            </div>
          </div>
        </el-form>
      </el-card>

      <!-- Tab切换区域 -->
      <el-card class="tab-card" shadow="hover">
        <el-tabs v-model="activeTab" type="card" @tab-click="handleTabClick" class="custom-tabs">
          <!-- 全て -->
          <el-tab-pane label="全て" name="all">
            <div class="tab-content">
              <div class="tab-header">
                <h3>全ての棚卸データ</h3>
                <div class="tab-stats">
                  <span class="tab-count">総件数: {{ pagination.total }}件</span>
                  <span class="tab-quantity"
                    >数量合計: {{ inventoryTotalQuantity.toLocaleString() }}個</span
                  >
                </div>
              </div>
              <inventory-table
                :data="inventoryList"
                :loading="loading"
                :pagination="pagination"
                :sort-by="sortBy"
                :sort-order="sortOrder"
                :deleting-id="deletingId"
                @page-change="handlePageChange"
                @size-change="handleSizeChange"
                @sort="handleSort"
                @delete="handleDeleteRecord"
              />
            </div>
          </el-tab-pane>

          <!-- 材料 -->
          <el-tab-pane label="材料" name="material">
            <div class="tab-content">
              <div class="tab-header">
                <h3>材料棚卸データ</h3>
                <div class="tab-stats">
                  <span class="tab-count">総件数: {{ materialPagination.total }}件</span>
                  <span class="tab-quantity"
                    >数量合計: {{ materialTotalQuantity.toLocaleString() }}個</span
                  >
                </div>
              </div>
              <inventory-table
                :data="materialList"
                :loading="materialLoading"
                :pagination="materialPagination"
                :sort-by="sortBy"
                :sort-order="sortOrder"
                :deleting-id="deletingId"
                @page-change="handleMaterialPageChange"
                @size-change="handleMaterialSizeChange"
                @sort="handleSort"
                @delete="handleDeleteRecord"
              />
            </div>
          </el-tab-pane>

          <!-- 部品 -->
          <el-tab-pane label="部品" name="component">
            <div class="tab-content">
              <div class="tab-header">
                <h3>部品棚卸データ</h3>
                <div class="tab-stats">
                  <span class="tab-count">総件数: {{ componentPagination.total }}件</span>
                  <span class="tab-quantity"
                    >数量合計: {{ componentTotalQuantity.toLocaleString() }}個</span
                  >
                </div>
              </div>
              <inventory-table
                :data="componentList"
                :loading="componentLoading"
                :pagination="componentPagination"
                :sort-by="sortBy"
                :sort-order="sortOrder"
                :deleting-id="deletingId"
                @page-change="handleComponentPageChange"
                @size-change="handleComponentSizeChange"
                @sort="handleSort"
                @delete="handleDeleteRecord"
              />
            </div>
          </el-tab-pane>

          <!-- ステー -->
          <el-tab-pane label="ステー" name="stage">
            <div class="tab-content">
              <div class="tab-header">
                <div class="tab-header-top">
                  <h3>ステー棚卸データ</h3>
                  <div class="tab-stats">
                    <span class="tab-count">総件数: {{ stagePagination.total }}件</span>
                    <span class="tab-quantity"
                      >数量合計: {{ stageTotalQuantity.toLocaleString() }}個</span
                    >
                  </div>
                </div>
                <div class="stage-subtabs">
                  <el-radio-group
                    v-model="activeStageTab"
                    @change="handleStageTabChange"
                    size="small"
                  >
                    <el-radio-button label="all">全て</el-radio-button>
                    <el-radio-button label="cutting">切断</el-radio-button>
                    <el-radio-button label="surface">面取</el-radio-button>
                    <el-radio-button label="sw">SW</el-radio-button>
                    <el-radio-button label="forming">成型</el-radio-button>
                    <el-radio-button label="plating">メッキ</el-radio-button>
                    <el-radio-button label="welding">溶接</el-radio-button>
                    <el-radio-button label="inspection">検査</el-radio-button>
                    <el-radio-button label="warehouse">倉庫</el-radio-button>
                    <el-radio-button label="outsource_plating">外注メッキ</el-radio-button>
                    <el-radio-button label="outsource_welding">外注溶接</el-radio-button>
                    <el-radio-button label="pre_welding_inspection">溶接前検査</el-radio-button>
                    <el-radio-button label="pre_outsource_inspection">外注検査前</el-radio-button>
                    <el-radio-button label="pre_outsource_delivery">外注支給前</el-radio-button>
                  </el-radio-group>
                </div>
              </div>
              <inventory-table
                :data="stageList"
                :loading="stageLoading"
                :pagination="stagePagination"
                :sort-by="sortBy"
                :sort-order="sortOrder"
                :deleting-id="deletingId"
                @page-change="handleStagePageChange"
                @size-change="handleStageSizeChange"
                @sort="handleSort"
                @delete="handleDeleteRecord"
              />
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  getInventoryLogs,
  importInventoryCSV,
  deleteInventoryLog,
  type InventoryLog,
  type InventoryFilters,
} from '@/api/inventory'

// ✅ Element Plus 图标组件
import { Box, DocumentAdd, Search, RefreshLeft } from '@element-plus/icons-vue'

// 导入表格组件
import InventoryTable from './components/InventoryTable.vue'

// Tab状态
const activeTab = ref('all')
const activeStageTab = ref('all')

// 加载状态
const loading = ref(false)
const materialLoading = ref(false)
const componentLoading = ref(false)
const stageLoading = ref(false)
const deletingId = ref<number | null>(null)

// 数据列表
const inventoryList = ref<any[]>([])
const materialList = ref<any[]>([])
const componentList = ref<any[]>([])
const stageList = ref<any[]>([])

// 数量合计
const inventoryTotalQuantity = ref(0)
const materialTotalQuantity = ref(0)
const componentTotalQuantity = ref(0)
const stageTotalQuantity = ref(0)

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
})

const materialPagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
})

const componentPagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
})

const stagePagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
})

// 筛选条件
const filters = ref({
  keyword: '',
  dateRange: [] as string[],
  monthPicker: '',
})

// 排序条件
const sortBy = ref('log_date')
const sortOrder = ref<'asc' | 'desc'>('desc')

interface ApiError {
  response?: {
    data?: {
      message?: string
    }
  }
  message?: string
}

// 格式化日期
const formatDate = (val: string) => dayjs(val).format('YYYY-MM-DD')

// 格式化时间
const formatTime = (val: string) => dayjs(val, 'HH:mm:ss').format('HH:mm')

// 加载文本
const loadingText = computed(() => {
  const texts = ['データを読み込み中...', 'しばらくお待ちください...', '処理中...']
  return texts[Math.floor(Math.random() * texts.length)]
})

// 获取所有数据
const fetchInventory = async () => {
  loading.value = true
  try {
    const response = await getInventoryLogs({
      ...filters.value,
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value,
    })

    // 由于request拦截器，response直接是data部分
    if (response && response.list) {
      inventoryList.value = response.list || []
      pagination.value.total = response.total || 0
      inventoryTotalQuantity.value = response.totalQuantity || 0
    } else {
      inventoryList.value = []
      pagination.value.total = 0
      inventoryTotalQuantity.value = 0
    }
  } catch (err) {
    console.error('棚卸データ取得に失敗しました', err)
    inventoryList.value = []
    pagination.value.total = 0
  } finally {
    loading.value = false
  }
}

// 获取材料数据
const fetchMaterial = async () => {
  materialLoading.value = true
  try {
    const response = await getInventoryLogs({
      ...filters.value,
      item: '材料棚卸',
      page: materialPagination.value.page,
      pageSize: materialPagination.value.pageSize,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value,
    })

    // 由于request拦截器，response直接是data部分
    if (response && response.list) {
      materialList.value = response.list || []
      materialPagination.value.total = response.total || 0
      materialTotalQuantity.value = response.totalQuantity || 0
    } else {
      materialList.value = []
      materialPagination.value.total = 0
      materialTotalQuantity.value = 0
    }
  } catch (err) {
    console.error('材料データ取得に失敗しました', err)
    materialList.value = []
    materialPagination.value.total = 0
  } finally {
    materialLoading.value = false
  }
}

// 获取部品数据
const fetchComponent = async () => {
  componentLoading.value = true
  try {
    const response = await getInventoryLogs({
      ...filters.value,
      item: '部品棚卸',
      page: componentPagination.value.page,
      pageSize: componentPagination.value.pageSize,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value,
    })

    // 由于request拦截器，response直接是data部分
    if (response && response.list) {
      componentList.value = response.list || []
      componentPagination.value.total = response.total || 0
      componentTotalQuantity.value = response.totalQuantity || 0
    } else {
      componentList.value = []
      componentPagination.value.total = 0
      componentTotalQuantity.value = 0
    }
  } catch (err) {
    console.error('部品データ取得に失敗しました', err)
    componentList.value = []
    componentPagination.value.total = 0
  } finally {
    componentLoading.value = false
  }
}

// 获取ステー数据
const fetchStage = async () => {
  stageLoading.value = true
  try {
    const params: any = {
      ...filters.value,
      page: stagePagination.value.page,
      pageSize: stagePagination.value.pageSize,
    }

    // 如果选择了"全て"，筛选項目字段为'製品棚卸'
    if (activeStageTab.value === 'all') {
      params.item = '製品棚卸'
    } else {
      // 如果选择了具体的ステー类型，筛选对应的工程CD
      params.stageType = activeStageTab.value
    }

    const response = await getInventoryLogs({
      ...params,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value,
    })

    // 由于request拦截器，response直接是data部分
    if (response && response.list) {
      stageList.value = response.list || []
      stagePagination.value.total = response.total || 0
      stageTotalQuantity.value = response.totalQuantity || 0
    } else {
      stageList.value = []
      stagePagination.value.total = 0
      stageTotalQuantity.value = 0
    }
  } catch (err) {
    console.error('ステーデータ取得に失敗しました', err)
    stageList.value = []
    stagePagination.value.total = 0
  } finally {
    stageLoading.value = false
  }
}

const refreshAllTabs = () =>
  Promise.all([fetchInventory(), fetchMaterial(), fetchComponent(), fetchStage()])

// Tab切换处理
const handleTabClick = (tab: any) => {
  switch (tab.name) {
    case 'all':
      fetchInventory()
      break
    case 'material':
      fetchMaterial()
      break
    case 'component':
      fetchComponent()
      break
    case 'stage':
      fetchStage()
      break
  }
}

// ステー子Tab切换处理
const handleStageTabChange = () => {
  stagePagination.value.page = 1
  fetchStage()
}

// 排序处理
const handleSort = (field: string) => {
  if (sortBy.value === field) {
    // 如果点击的是当前排序字段，切换排序方向
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    // 如果是新字段，设置为降序
    sortBy.value = field
    sortOrder.value = 'desc'
  }

  // 重置所有分页到第一页
  pagination.value.page = 1
  materialPagination.value.page = 1
  componentPagination.value.page = 1
  stagePagination.value.page = 1

  // 重新获取数据
  refreshAllTabs()
}

// 月份选择处理
const handleMonthChange = (month: string) => {
  if (month) {
    const year = parseInt(month.split('-')[0])
    const monthNum = parseInt(month.split('-')[1])

    // 设置该月的第一天
    const startDate = dayjs(`${year}-${monthNum.toString().padStart(2, '0')}-01`)

    // 设置该月的最后一天
    const endDate = startDate.endOf('month')

    filters.value.dateRange = [startDate.format('YYYY-MM-DD'), endDate.format('YYYY-MM-DD')]
  } else {
    // 如果清空月份选择，也清空日期范围
    filters.value.dateRange = []
  }
}

// 搜索处理
const handleSearch = async () => {
  pagination.value.page = 1
  materialPagination.value.page = 1
  componentPagination.value.page = 1
  stagePagination.value.page = 1

  await refreshAllTabs()
}

// 重置筛选
const resetFilters = async () => {
  filters.value = {
    keyword: '',
    dateRange: [] as string[],
    monthPicker: '',
  }

  pagination.value.page = 1
  materialPagination.value.page = 1
  componentPagination.value.page = 1
  stagePagination.value.page = 1

  await refreshAllTabs()
}

// 数据导入
const handleImport = async () => {
  loading.value = true
  try {
    const response = await importInventoryCSV()

    if (response.data?.summary) {
      const { summary, fileDetails } = response.data
      let message = `✅ CSV取込が完了しました\n\n【合計】\n処理件数: ${summary.totalProcessed}件\n新規追加: ${summary.newRecords}件\n重複スキップ: ${summary.duplicates}件`

      // 显示各文件的详细信息
      if (fileDetails) {
        message += `\n\n【InventoryLog.csv】\n処理件数: ${fileDetails.inventoryLog.processed}件\n新規追加: ${fileDetails.inventoryLog.newRecords}件\n重複スキップ: ${fileDetails.inventoryLog.duplicates}件`
        if (!fileDetails.inventoryLog.exists) {
          message += '\n⚠️ ファイルが見つかりませんでした'
        }

        message += `\n\n【Partslog.csv】\n処理件数: ${fileDetails.partsLog.processed}件\n新規追加: ${fileDetails.partsLog.newRecords}件\n重複スキップ: ${fileDetails.partsLog.duplicates}件`
        if (!fileDetails.partsLog.exists) {
          message += '\n⚠️ ファイルが見つかりませんでした'
        }

        message += `\n\n【Materiallog.csv】\n処理件数: ${fileDetails.materialLog.processed}件\n新規追加: ${fileDetails.materialLog.newRecords}件\n重複スキップ: ${fileDetails.materialLog.duplicates}件`
        if (!fileDetails.materialLog.exists) {
          message += '\n⚠️ ファイルが見つかりませんでした'
        }
      }

      ElMessage.success(message)
    } else {
      ElMessage.success('✅ ' + (response.message ?? 'CSV取込が完了しました'))
    }

    await refreshAllTabs()
  } catch (err: unknown) {
    const apiError = err as ApiError
    const msg = apiError?.response?.data?.message || apiError?.message || 'CSV取込に失敗しました'
    ElMessage.error('❌ ' + msg)
  } finally {
    loading.value = false
  }
}

// 删除处理
const handleDeleteRecord = async (record: InventoryLog) => {
  try {
    await ElMessageBox.confirm(
      `選択した棚卸データを削除しますか？\n\n製品: ${record.product_name} (${record.product_cd})\n日付: ${formatDate(record.log_date)} ${formatTime(record.log_time)}\n数量: ${record.quantity}`,
      '削除確認',
      {
        confirmButtonText: '削除',
        cancelButtonText: 'キャンセル',
        type: 'warning',
        autofocus: false,
      },
    )
  } catch {
    return
  }

  try {
    deletingId.value = record.id
    await deleteInventoryLog(record.id)
    ElMessage.success('✅ 棚卸データを削除しました')
    await refreshAllTabs()
  } catch (err: unknown) {
    const apiError = err as ApiError
    const msg = apiError?.response?.data?.message || apiError?.message || '削除に失敗しました'
    ElMessage.error('❌ ' + msg)
  } finally {
    deletingId.value = null
  }
}

// 分页处理 - 全て
const handlePageChange = (newPage: number) => {
  pagination.value.page = newPage
  fetchInventory()
}

const handleSizeChange = (newSize: number) => {
  pagination.value.pageSize = newSize
  pagination.value.page = 1
  fetchInventory()
}

// 分页处理 - 材料
const handleMaterialPageChange = (newPage: number) => {
  materialPagination.value.page = newPage
  fetchMaterial()
}

const handleMaterialSizeChange = (newSize: number) => {
  materialPagination.value.pageSize = newSize
  materialPagination.value.page = 1
  fetchMaterial()
}

// 分页处理 - 部品
const handleComponentPageChange = (newPage: number) => {
  componentPagination.value.page = newPage
  fetchComponent()
}

const handleComponentSizeChange = (newSize: number) => {
  componentPagination.value.pageSize = newSize
  componentPagination.value.page = 1
  fetchComponent()
}

// 分页处理 - ステー
const handleStagePageChange = (newPage: number) => {
  stagePagination.value.page = newPage
  fetchStage()
}

const handleStageSizeChange = (newSize: number) => {
  stagePagination.value.pageSize = newSize
  stagePagination.value.page = 1
  fetchStage()
}

// 组件挂载时初始化数据
onMounted(async () => {
  await refreshAllTabs()
})
</script>

<style scoped>
/* 动画定义 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
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

@keyframes floatOrb {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg) scale(1);
  }
  25% {
    transform: translateY(-25px) rotate(90deg) scale(1.08);
  }
  50% {
    transform: translateY(-8px) rotate(180deg) scale(0.92);
  }
  75% {
    transform: translateY(18px) rotate(270deg) scale(1.04);
  }
}

.inventory-container {
  min-height: 100vh;
  background: linear-gradient(
    135deg,
    rgba(248, 250, 252, 0.95) 0%,
    rgba(241, 245, 249, 0.98) 25%,
    rgba(226, 232, 240, 0.95) 50%,
    rgba(248, 250, 252, 0.98) 75%,
    rgba(241, 245, 249, 0.95) 100%
  );
  position: relative;
  overflow-x: hidden;
  padding: 8px;
  will-change: transform;
  animation: fadeInUp 0.6s ease-out;
}

.inventory-container::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(
    circle,
    rgba(14, 165, 233, 0.08) 0%,
    rgba(6, 182, 212, 0.06) 30%,
    rgba(34, 211, 238, 0.04) 60%,
    transparent 80%
  );
  animation: float 8s ease-in-out infinite;
  pointer-events: none;
  z-index: -1;
}

/* 动态背景 */
.dynamic-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -2;
  overflow: hidden;
  will-change: transform;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(
    45deg,
    rgba(14, 165, 233, 0.06),
    rgba(6, 182, 212, 0.08),
    rgba(34, 211, 238, 0.05)
  );
  animation: floatOrb 35s ease-in-out infinite;
  will-change: transform;
  filter: blur(1px);
}

.orb-1 {
  width: 350px;
  height: 350px;
  top: -175px;
  right: -175px;
  animation-delay: -12s;
  background: linear-gradient(45deg, rgba(14, 165, 233, 0.08), rgba(6, 182, 212, 0.06));
}

.orb-2 {
  width: 280px;
  height: 280px;
  bottom: -140px;
  left: -140px;
  animation-delay: -24s;
  background: linear-gradient(45deg, rgba(14, 165, 233, 0.06), rgba(6, 182, 212, 0.08));
}

.orb-3 {
  width: 320px;
  height: 320px;
  top: 45%;
  left: 75%;
  transform: translate(-50%, -50%);
  animation-delay: -6s;
  background: linear-gradient(45deg, rgba(6, 182, 212, 0.07), rgba(14, 165, 233, 0.05));
}

/* 页面头部 */
.page-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px) saturate(180%);
  border-radius: 12px;
  padding: 12px 20px;
  margin-bottom: 10px;
  border: 1px solid rgba(226, 232, 240, 0.6);
  box-shadow:
    0 2px 12px rgba(0, 0, 0, 0.04),
    0 1px 4px rgba(0, 0, 0, 0.02),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  animation: fadeInUp 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  will-change: transform;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
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
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.6s;
}

.page-header:hover {
  transform: translateY(-1px);
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.06),
    0 2px 8px rgba(0, 0, 0, 0.04),
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
  max-width: 1400px;
  margin: 0 auto;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  animation: slideInLeft 0.5s ease-out 0.1s both;
}

.header-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #0ea5e9, #06b6d4, #22d3ee);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow:
    0 2px 8px rgba(14, 165, 233, 0.25),
    0 1px 4px rgba(6, 182, 212, 0.15);
  animation: iconPulse 4s ease-in-out infinite;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}

.header-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.header-icon:hover {
  transform: translateY(-2px) scale(1.08);
  box-shadow:
    0 6px 20px rgba(14, 165, 233, 0.4),
    0 3px 10px rgba(6, 182, 212, 0.3);
  animation: pulse 2s infinite;
}

.header-icon:hover::before {
  left: 100%;
}

@keyframes iconPulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow:
      0 4px 12px rgba(14, 165, 233, 0.3),
      0 2px 6px rgba(6, 182, 212, 0.2);
  }
  50% {
    transform: scale(1.02);
    box-shadow:
      0 6px 16px rgba(14, 165, 233, 0.4),
      0 3px 8px rgba(6, 182, 212, 0.3);
  }
}

.header-text {
  flex: 1;
}

.main-title {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #0ea5e9, #06b6d4, #0891b2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 2px 0;
  letter-spacing: -0.02em;
  line-height: 1.3;
  animation: fadeInUp 0.5s ease-out 0.2s both;
}

.subtitle {
  font-size: 12px;
  color: #64748b;
  margin: 0;
  font-weight: 500;
  line-height: 1.4;
  animation: fadeInUp 0.5s ease-out 0.25s both;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  flex-shrink: 0;
  animation: slideInRight 0.5s ease-out 0.3s both;
}

.import-button {
  background: linear-gradient(135deg, #10b981, #059669, #047857);
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 13px;
  box-shadow:
    0 2px 8px rgba(16, 185, 129, 0.25),
    0 1px 4px rgba(5, 150, 105, 0.15);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(8px);
  position: relative;
  overflow: hidden;
}

.import-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.import-button:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow:
    0 6px 20px rgba(16, 185, 129, 0.4),
    0 3px 10px rgba(5, 150, 105, 0.3);
  background: linear-gradient(135deg, #059669, #047857, #065f46);
}

.import-button:hover::before {
  left: 100%;
}

/* 主要内容区域 */
.content-container {
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 筛选卡片 */
.filter-card {
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(20px) saturate(180%);
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.6);
  box-shadow:
    0 2px 12px rgba(0, 0, 0, 0.04),
    0 1px 4px rgba(0, 0, 0, 0.02),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  animation: slideInLeft 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  will-change: transform;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.filter-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
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
  background: linear-gradient(90deg, transparent, rgba(14, 165, 233, 0.05), transparent);
  transition: left 0.8s;
}

.filter-card:hover {
  transform: translateY(-1px);
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.06),
    0 2px 8px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.filter-card:hover::before {
  left: 100%;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

.filter-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-weight: 700;
  background: linear-gradient(135deg, #0ea5e9, #06b6d4, #0891b2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 15px;
  animation: fadeInUp 0.4s ease-out;
  padding: 0;
}

.filter-icon {
  background: linear-gradient(135deg, #0ea5e9, #06b6d4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 20px;
  animation: pulse 2s infinite;
}

.filter-title {
  font-size: 15px;
  letter-spacing: -0.02em;
  font-weight: 700;
}

.filter-form {
  padding: 0;
}

.filter-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin: 0;
  flex-wrap: nowrap;
}

.filter-item {
  margin-bottom: 0;
  flex-shrink: 0;
}

.filter-item :deep(.el-form-item__label) {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  padding-bottom: 4px;
  white-space: nowrap;
  line-height: 1.2;
}

.filter-item :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-input,
.filter-date-picker,
.filter-month-picker {
  width: 170px;
  border-radius: 6px;
}

.filter-input :deep(.el-input__inner),
.filter-date-picker :deep(.el-input__inner),
.filter-month-picker :deep(.el-input__inner) {
  font-size: 13px;
  height: 32px;
  line-height: 32px;
}

.filter-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(226, 232, 240, 0.8);
  transition: all 0.25s ease;
}

.filter-input :deep(.el-input__wrapper):hover {
  border-color: #0ea5e9;
  background: rgba(255, 255, 255, 0.9);
}

.filter-actions {
  display: flex;
  gap: 6px;
  align-items: flex-end;
  margin-left: auto;
  flex-shrink: 0;
  animation: fadeInUp 0.5s ease-out 0.2s both;
}

.search-button {
  background: linear-gradient(135deg, #0ea5e9, #06b6d4, #22d3ee);
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-weight: 600;
  font-size: 12px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    0 2px 8px rgba(14, 165, 233, 0.25),
    0 1px 4px rgba(6, 182, 212, 0.15);
  position: relative;
  overflow: hidden;
  height: 32px;
}

.search-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.search-button:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow:
    0 6px 24px rgba(14, 165, 233, 0.4),
    0 3px 12px rgba(6, 182, 212, 0.3);
  background: linear-gradient(135deg, #0284c7, #06b6d4, #22d3ee);
}

.search-button:hover::before {
  left: 100%;
}

.reset-button {
  background: rgba(107, 114, 128, 0.08);
  border: 1px solid rgba(107, 114, 128, 0.2);
  border-radius: 6px;
  padding: 6px 12px;
  font-weight: 600;
  font-size: 12px;
  color: #6b7280;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(12px);
  position: relative;
  overflow: hidden;
  height: 32px;
}

.reset-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(107, 114, 128, 0.1), transparent);
  transition: left 0.5s;
}

.reset-button:hover {
  background: rgba(107, 114, 128, 0.15);
  border-color: rgba(107, 114, 128, 0.3);
  transform: translateY(-2px) scale(1.02);
  color: #4b5563;
  box-shadow: 0 4px 12px rgba(107, 114, 128, 0.2);
}

.reset-button:hover::before {
  left: 100%;
}

/* Tab卡片 */
.tab-card {
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(20px) saturate(180%);
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.6);
  box-shadow:
    0 2px 12px rgba(0, 0, 0, 0.04),
    0 1px 4px rgba(0, 0, 0, 0.02),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  animation: slideInRight 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.tab-card :deep(.el-card__body) {
  padding: 12px;
}

.tab-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.05), transparent);
  transition: left 0.8s;
}

.tab-card:hover {
  transform: translateY(-1px);
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.06),
    0 2px 8px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.tab-card:hover::before {
  left: 100%;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

/* 自定义Tab样式 */
.custom-tabs {
  border: none;
  background: transparent;
  border-radius: 14px;
  overflow: hidden;
}

.custom-tabs :deep(.el-tabs__header) {
  background: rgba(248, 250, 252, 0.8);
  backdrop-filter: blur(12px) saturate(180%);
  margin: 0;
  padding: 4px;
  border-radius: 10px;
  box-shadow:
    0 1px 8px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(226, 232, 240, 0.5);
  animation: fadeInUp 0.4s ease-out 0.15s both;
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
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 8px;
  margin: 0 2px;
  font-size: 13px;
  position: relative;
  overflow: hidden;
  line-height: 1.4;
}

.custom-tabs :deep(.el-tabs__item::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(14, 165, 233, 0.1), transparent);
  transition: left 0.5s;
}

.custom-tabs :deep(.el-tabs__item:hover) {
  color: #0ea5e9;
  background: rgba(14, 165, 233, 0.12);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.15);
}

.custom-tabs :deep(.el-tabs__item:hover::before) {
  left: 100%;
}

.custom-tabs :deep(.el-tabs__item.is-active) {
  color: white;
  background: linear-gradient(135deg, #0ea5e9, #06b6d4, #22d3ee);
  backdrop-filter: blur(8px);
  box-shadow:
    0 4px 16px rgba(14, 165, 233, 0.3),
    0 2px 8px rgba(6, 182, 212, 0.2);
  font-weight: 700;
  transform: translateY(-1px);
}

.custom-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.custom-tabs :deep(.el-tabs__content) {
  padding: 0;
  margin-top: 12px;
  animation: fadeInUp 0.4s ease-out 0.3s both;
}

/* Tab内容样式 */
.tab-content {
  min-height: 300px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(12px) saturate(180%);
  border-radius: 10px;
  padding: 16px;
  border: 1px solid rgba(226, 232, 240, 0.5);
  box-shadow:
    0 1px 8px rgba(0, 0, 0, 0.03),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  animation: fadeInUp 0.4s ease-out 0.35s both;
}

.tab-header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(14, 165, 233, 0.12);
  position: relative;
}

.tab-header::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 50px;
  height: 2px;
  background: linear-gradient(135deg, #0ea5e9, #06b6d4);
  border-radius: 1px;
}

.tab-header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tab-header h3 {
  margin: 0;
  color: #1e293b;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.4;
}

.tab-stats {
  display: flex;
  gap: 12px;
  align-items: center;
  animation: slideInRight 0.4s ease-out 0.4s both;
}

.tab-count {
  color: #0ea5e9;
  font-size: 12px;
  font-weight: 600;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.1), rgba(6, 182, 212, 0.08));
  padding: 4px 10px;
  border-radius: 8px;
  border: 1px solid rgba(14, 165, 233, 0.2);
  backdrop-filter: blur(8px);
  box-shadow: 0 1px 4px rgba(14, 165, 233, 0.08);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  line-height: 1.4;
}

.tab-count::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(14, 165, 233, 0.1), transparent);
  transition: left 0.5s;
}

.tab-count:hover {
  transform: translateY(-1px) scale(1.02);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2);
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.15), rgba(6, 182, 212, 0.12));
}

.tab-count:hover::before {
  left: 100%;
}

.tab-quantity {
  color: #10b981;
  font-size: 12px;
  font-weight: 600;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.08));
  padding: 4px 10px;
  border-radius: 8px;
  border: 1px solid rgba(16, 185, 129, 0.2);
  backdrop-filter: blur(8px);
  box-shadow: 0 1px 4px rgba(16, 185, 129, 0.08);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  line-height: 1.4;
}

.tab-quantity::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.1), transparent);
  transition: left 0.5s;
}

.tab-quantity:hover {
  transform: translateY(-1px) scale(1.02);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.12));
}

.tab-quantity:hover::before {
  left: 100%;
}

/* ステー子Tab样式 */
.stage-subtabs {
  display: flex;
  justify-content: center;
  animation: fadeInUp 0.4s ease-out 0.5s both;
  padding: 6px 0;
}

.stage-subtabs :deep(.el-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}

.stage-subtabs :deep(.el-radio-button__inner) {
  border-radius: 6px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  color: #64748b;
  font-size: 11px;
  padding: 4px 10px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 600;
  box-shadow:
    0 1px 4px rgba(0, 0, 0, 0.04),
    0 1px 2px rgba(0, 0, 0, 0.02);
  position: relative;
  overflow: hidden;
  line-height: 1.4;
}

.stage-subtabs :deep(.el-radio-button__inner::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(14, 165, 233, 0.08), transparent);
  transition: left 0.5s;
}

.stage-subtabs :deep(.el-radio-button__inner:hover) {
  color: #0ea5e9;
  border-color: #0ea5e9;
  background: rgba(14, 165, 233, 0.12);
  transform: translateY(-2px) scale(1.02);
  box-shadow:
    0 4px 16px rgba(14, 165, 233, 0.2),
    0 2px 8px rgba(14, 165, 233, 0.1);
}

.stage-subtabs :deep(.el-radio-button__inner:hover::before) {
  left: 100%;
}

.stage-subtabs :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #0ea5e9, #06b6d4, #22d3ee);
  border-color: #0ea5e9;
  color: white;
  font-weight: 700;
  box-shadow:
    0 4px 16px rgba(14, 165, 233, 0.3),
    0 2px 8px rgba(6, 182, 212, 0.2);
  transform: translateY(-2px);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-container {
    padding: 0 12px;
  }

  .filter-row {
    flex-wrap: wrap;
    gap: 10px;
  }

  .filter-input,
  .filter-date-picker,
  .filter-month-picker {
    width: 160px;
  }

  .filter-actions {
    margin-left: 0;
    margin-top: 6px;
  }

  .stage-subtabs {
    margin: 0 8px;
  }

  .stage-subtabs :deep(.el-radio-group) {
    gap: 4px;
  }

  .stage-subtabs :deep(.el-radio-button__inner) {
    font-size: 10px;
    padding: 4px 8px;
  }

  .tab-header {
    gap: 12px;
  }

  .tab-header-top {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }

  .tab-stats {
    gap: 12px;
  }
}

@media (max-width: 768px) {
  .inventory-container {
    padding: 6px;
  }

  .page-header {
    padding: 10px 14px;
    margin-bottom: 8px;
  }

  .header-content {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }

  .header-left {
    justify-content: center;
  }

  .main-title {
    font-size: 18px;
  }

  .subtitle {
    font-size: 12px;
  }

  .header-icon {
    width: 36px;
    height: 36px;
  }

  .custom-tabs :deep(.el-tabs__content) {
    padding: 0;
  }

  .tab-content {
    padding: 12px;
  }

  .tab-header {
    gap: 8px;
    margin-bottom: 10px;
    padding-bottom: 8px;
  }

  .tab-header-top {
    flex-direction: column;
    gap: 6px;
    align-items: flex-start;
  }

  .stage-subtabs {
    margin: 0;
    width: 100%;
  }

  .stage-subtabs :deep(.el-radio-group) {
    justify-content: flex-start;
    overflow-x: auto;
    padding-bottom: 6px;
    gap: 3px;
  }

  .stage-subtabs :deep(.el-radio-button__inner) {
    white-space: nowrap;
    font-size: 10px;
    padding: 3px 6px;
  }

  .filter-row {
    flex-direction: column;
    gap: 6px;
  }

  .filter-input,
  .filter-date-picker,
  .filter-month-picker {
    width: 100%;
  }

  .filter-actions {
    justify-content: center;
    margin-left: 0;
    margin-top: 6px;
  }
}

@media (max-width: 480px) {
  .inventory-container {
    padding: 4px;
  }

  .page-header {
    padding: 10px 12px;
  }

  .header-icon {
    width: 32px;
    height: 32px;
  }

  .main-title {
    font-size: 16px;
  }

  .subtitle {
    font-size: 11px;
  }

  .import-button,
  .refresh-button {
    padding: 6px 12px;
    font-size: 12px;
  }

  .header-actions {
    justify-content: center;
    gap: 6px;
  }

  .filter-row {
    flex-direction: column;
    gap: 4px;
  }

  .filter-input,
  .filter-date-picker,
  .filter-month-picker {
    width: 100%;
  }

  .filter-actions {
    justify-content: center;
    margin-left: 0;
    margin-top: 4px;
    gap: 4px;
  }

  .custom-tabs :deep(.el-tabs__content) {
    padding: 10px;
  }

  .custom-tabs :deep(.el-tabs__item) {
    padding: 8px 12px;
    font-size: 12px;
  }

  .tab-header {
    gap: 6px;
  }

  .tab-header-top {
    flex-direction: column;
    gap: 4px;
    align-items: flex-start;
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
    padding: 3px 8px;
  }

  .stage-subtabs :deep(.el-radio-button__inner) {
    font-size: 9px;
    padding: 2px 4px;
  }
}
</style>
