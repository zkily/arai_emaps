<template>
  <div class="inventory-container">
    <div class="page-ambient" aria-hidden="true" />

    <header class="page-toolbar">
      <div class="toolbar-inner">
        <div class="toolbar-brand">
          <div class="brand-icon">
            <el-icon :size="20"><Box /></el-icon>
          </div>
          <div class="brand-text">
            <h1 class="toolbar-title">棚卸リスト一覧</h1>
            <p class="toolbar-sub">材料・部品・ステー（工程別）・製品</p>
          </div>
        </div>
        <el-button
          type="primary"
          size="small"
          @click="handleImport"
          :loading="loading"
          :icon="DocumentAdd"
        >
          棚卸データ取込
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
              <el-button type="primary" size="small" :icon="Search" @click="handleSearch">
                検索
              </el-button>
              <el-button size="small" :icon="RefreshLeft" @click="resetFilters"> リセット </el-button>
            </div>
          </div>
        </el-form>
      </el-card>

      <!-- Tab切换区域 -->
      <el-card class="tab-card" shadow="never">
        <el-tabs v-model="activeTab" type="card" @tab-click="handleTabClick" class="custom-tabs">
          <!-- 全て -->
          <el-tab-pane label="全て" name="all">
            <div class="tab-content">
              <div class="tab-header tab-header--row">
                <h3 class="tab-heading">全て</h3>
                <div class="tab-stats">
                  <span class="stat-pill">{{ pagination.total }} 件</span>
                  <span class="stat-pill stat-pill--qty"
                    >計 {{ inventoryTotalQuantity.toLocaleString() }}</span
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
              <div class="tab-header tab-header--row">
                <h3 class="tab-heading">材料</h3>
                <div class="tab-stats">
                  <span class="stat-pill">{{ materialPagination.total }} 件</span>
                  <span class="stat-pill stat-pill--qty"
                    >計 {{ materialTotalQuantity.toLocaleString() }}</span
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
              <div class="tab-header tab-header--row">
                <h3 class="tab-heading">部品</h3>
                <div class="tab-stats">
                  <span class="stat-pill">{{ componentPagination.total }} 件</span>
                  <span class="stat-pill stat-pill--qty"
                    >計 {{ componentTotalQuantity.toLocaleString() }}</span
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
                <div class="tab-header-top tab-header--row">
                  <h3 class="tab-heading">ステー</h3>
                  <div class="tab-stats">
                    <span class="stat-pill">{{ stagePagination.total }} 件</span>
                    <span class="stat-pill stat-pill--qty"
                      >計 {{ stageTotalQuantity.toLocaleString() }}</span
                    >
                  </div>
                </div>
                <div class="stage-subtabs">
                  <el-radio-group
                    v-model="activeStageTab"
                    @change="handleStageTabChange"
                    size="small"
                  >
                    <el-radio-button value="all">全て</el-radio-button>
                    <el-radio-button value="cutting">切断</el-radio-button>
                    <el-radio-button value="surface">面取</el-radio-button>
                    <el-radio-button value="sw">SW</el-radio-button>
                    <el-radio-button value="forming">成型</el-radio-button>
                    <el-radio-button value="plating">メッキ</el-radio-button>
                    <el-radio-button value="welding">溶接</el-radio-button>
                    <el-radio-button value="inspection">検査</el-radio-button>
                    <el-radio-button value="warehouse">倉庫</el-radio-button>
                    <el-radio-button value="outsource_plating">外注メッキ</el-radio-button>
                    <el-radio-button value="outsource_welding">外注溶接</el-radio-button>
                    <el-radio-button value="pre_welding_inspection">溶接前検査</el-radio-button>
                    <el-radio-button value="pre_outsource_inspection">外注検査前</el-radio-button>
                    <el-radio-button value="pre_outsource_delivery">外注支給前</el-radio-button>
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
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  getInventoryLogs,
  importInventoryCSV,
  deleteInventoryLog,
  type InventoryLog,
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

// 排序处理（服务端全量排序）
const handleSort = (field: string, order: 'asc' | 'desc' | null) => {
  sortBy.value = field
  // Element Plus 第三次点击会回到 null，这里回退为降序，避免状态不明确
  sortOrder.value = order ?? 'desc'

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
.inventory-container {
  --il-surface: rgba(255, 255, 255, 0.92);
  --il-border: rgba(15, 23, 42, 0.08);
  --il-accent: #0ea5e9;
  --il-muted: #64748b;
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
  background: var(--il-surface);
  border: 1px solid var(--il-border);
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
  color: var(--il-muted);
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
  background: var(--il-surface);
  border: 1px solid var(--il-border);
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: box-shadow 0.2s ease;
}

.filter-card:hover,
.tab-card:hover {
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
}

.filter-card :deep(.el-card__header) {
  padding: 9px 12px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.92), rgba(248, 250, 252, 0.62));
}

.filter-card :deep(.el-card__body) {
  padding: 10px 12px 9px;
}

.filter-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  min-height: 18px;
}

.filter-toolbar-icon {
  font-size: 16px;
  color: var(--il-accent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.filter-toolbar-title {
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.filter-form {
  padding: 0;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  flex-wrap: wrap;
}

.filter-item {
  margin-bottom: 0;
  flex-shrink: 0;
}

.filter-item :deep(.el-form-item__label) {
  font-size: 11px;
  color: var(--il-muted);
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

.filter-input,
.filter-date-picker,
.filter-month-picker {
  width: 160px;
}

.filter-input :deep(.el-input__wrapper),
.filter-date-picker :deep(.el-input__wrapper),
.filter-month-picker :deep(.el-input__wrapper) {
  min-height: 30px;
}

.filter-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-left: auto;
  flex-shrink: 0;
  min-height: 30px;
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
  color: var(--il-muted);
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
  min-height: 240px;
  background: rgba(255, 255, 255, 0.75);
  border-radius: 8px;
  padding: 10px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.tab-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(14, 165, 233, 0.15);
}

.tab-header--row {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.tab-header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 8px;
}

.tab-heading {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
  line-height: 1.3;
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

.stage-subtabs {
  padding: 4px 0 0;
  width: 100%;
}

.stage-subtabs :deep(.el-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: flex-start;
}

.stage-subtabs :deep(.el-radio-button__inner) {
  border-radius: 6px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: #fff;
  color: #475569;
  font-size: 11px;
  padding: 3px 8px;
  font-weight: 600;
  line-height: 1.35;
  transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
}

.stage-subtabs :deep(.el-radio-button__inner:hover) {
  color: var(--il-accent);
  border-color: rgba(14, 165, 233, 0.45);
  background: rgba(14, 165, 233, 0.06);
}

.stage-subtabs :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 2px 6px rgba(14, 165, 233, 0.2);
}

@media (max-width: 1200px) {
  .content-container {
    padding: 0 4px;
  }

  .filter-row {
    gap: 6px;
  }

  .filter-input,
  .filter-date-picker,
  .filter-month-picker {
    width: 150px;
  }

  .filter-actions {
    margin-left: 0;
    margin-top: 4px;
  }

  .stage-subtabs :deep(.el-radio-button__inner) {
    font-size: 10px;
    padding: 3px 6px;
  }
}

@media (max-width: 768px) {
  .inventory-container {
    padding: 8px;
  }

  .toolbar-inner {
    align-items: flex-start;
  }

  .toolbar-title {
    font-size: 1rem;
  }

  .custom-tabs :deep(.el-tabs__content) {
    padding: 0;
  }

  .tab-content {
    padding: 8px;
  }

  .tab-header--row {
    align-items: flex-start;
  }

  .stage-subtabs :deep(.el-radio-group) {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: 4px;
    -webkit-overflow-scrolling: touch;
  }

  .stage-subtabs :deep(.el-radio-button__inner) {
    white-space: nowrap;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-input,
  .filter-date-picker,
  .filter-month-picker {
    width: 100%;
  }

  .filter-actions {
    justify-content: flex-start;
    margin-left: 0;
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

  .toolbar-sub {
    font-size: 10px;
  }

  .filter-actions {
    width: 100%;
    gap: 4px;
  }

  .custom-tabs :deep(.el-tabs__item) {
    padding: 5px 8px;
    font-size: 11px;
  }

  .tab-heading {
    font-size: 12px;
  }

  .stat-pill {
    font-size: 10px;
    padding: 2px 6px;
  }
}
</style>
