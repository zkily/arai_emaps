<template>
  <div class="shipping-report-page">
    <div class="report-card glass-card">
      <!-- 页面标题：玻璃头部 -->
      <div class="card-header glass-header">
        <div class="header-left">
          <div class="header-icon-container">
            <el-icon class="header-icon"><Document /></el-icon>
          </div>
          <h1 class="header-title">出荷報告書</h1>
        </div>
      </div>

      <!-- 営業報告カレンダー（内联，筛选区上方） -->
      <ShippingCalendarDialog :model-value="true" inline />

      <!-- 筛选条件：紧凑 + 玻璃卡片 -->
      <div class="filter-section glass-card">
        <div class="filter-main-row">
          <div class="filter-item">
            <label class="filter-label">出荷日期</label>
            <div class="date-controls">
              <el-date-picker v-model="filters.dateRange" type="daterange" start-placeholder="開始日" end-placeholder="終了日"
                value-format="YYYY-MM-DD" @change="handleDateChange" class="date-picker" size="default" />
              <div class="date-nav-buttons">
                <el-button size="small" @click="adjustDate(-1)" class="nav-btn btn-glass prev-btn" title="前日">←</el-button>
                <el-button size="small" @click="goToToday" class="nav-btn btn-glass today-btn" title="本日">本日</el-button>
                <el-button size="small" @click="adjustDate(1)" class="nav-btn btn-glass next-btn" title="次日">→</el-button>
              </div>
            </div>
          </div>
          <div class="filter-item">
            <label class="filter-label">納入先</label>
            <div class="destination-controls">
              <el-select v-model="filters.destinationCds" multiple placeholder="納入先を選択" collapse-tags
                collapse-tags-tooltip @change="handleDestinationChange" class="destination-select" size="default">
                <el-option v-for="dest in destinationOptions" :key="dest.value" :label="dest.label" :value="dest.value" />
              </el-select>
              <el-button :icon="Setting" @click="showGroupManager = true" class="group-btn btn-glass btn-primary" title="納入先グループ管理">グループ</el-button>
            </div>
          </div>
          <div class="filter-actions">
            <el-button :icon="Clock" @click="showPrintHistory = true" class="action-btn btn-glass btn-info">印刷履歴</el-button>
            <el-button :icon="Document" @click="handleReport"
              :disabled="loading || !overviewData || overviewData.length === 0" class="action-btn btn-glass btn-success">
              報告書印刷
            </el-button>
          </div>
        </div>
        <div v-if="hasGroups" class="group-selection">
          <label class="filter-label">グループ選択</label>
          <el-radio-group v-model="filters.selectedGroup" @change="handleGroupChange" class="group-radios">
            <el-radio :value="-1" class="group-radio">全て</el-radio>
            <el-radio v-for="(group, index) in destinationGroups" :key="group.id || index" :value="index"
              :disabled="!group?.destinations || group.destinations.length === 0" class="group-radio">
              {{ group.groupName }} ({{ group?.destinations?.length || 0 }})
            </el-radio>
          </el-radio-group>
        </div>
      </div>

      <!-- 统计：玻璃卡片 + 颜色区分 -->
      <div v-if="!loading && overviewData && overviewData.length > 0" class="stats-section">
        <div class="stat-card glass-card stat-destinations">
          <div class="stat-icon"><el-icon><Location /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ totalDestinations }}</div>
            <div class="stat-label">納入先数</div>
          </div>
        </div>
        <div class="stat-card glass-card stat-dates">
          <div class="stat-icon"><el-icon><Calendar /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ totalDates }}</div>
            <div class="stat-label">出荷日数</div>
          </div>
        </div>
        <div class="stat-card glass-card stat-products">
          <div class="stat-icon"><el-icon><Box /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ totalProducts }}</div>
            <div class="stat-label">製品種類</div>
          </div>
        </div>
        <div class="stat-card glass-card stat-boxes">
          <div class="stat-icon"><el-icon><Files /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ totalBoxes }}</div>
            <div class="stat-label">総箱数</div>
          </div>
        </div>
      </div>

      <!-- 数据表格：玻璃卡片 -->
      <div class="table-section glass-card" v-loading="loading">
        <el-empty v-if="!loading && (!overviewData || overviewData.length === 0)" description="条件に合うデータがありません"
          :image-size="56" class="empty-state" />

        <div v-else class="table-container">
          <el-table
            :data="groupedTableData"
            stripe
            style="width: 100%"
            show-summary
            :summary-method="getSummaries"
            :span-method="spanMethod"
            :row-class-name="tableRowClassName"
            size="default"
            class="modern-table table-by-destination"
          >
            <el-table-column label="出荷日" prop="shipping_date" width="110" align="center" fixed>
              <template #default="{ row }">
                <template v-if="(row as TableRow & { _groupHeader?: boolean })._groupHeader">
                  <div class="group-header-cell">
                    <el-icon class="group-header-icon"><Location /></el-icon>
                    <span class="group-header-label">{{ (row as { destination_name: string }).destination_name }}</span>
                  </div>
                </template>
                <div v-else class="date-cell">
                  {{ formatDate((row as ShippingOverviewData).shipping_date) }}
                </div>
              </template>
            </el-table-column>

            <el-table-column label="納入先" prop="destination_name" min-width="160" show-overflow-tooltip>
              <template #default="{ row }">
                <template v-if="!(row as TableRow & { _groupHeader?: boolean })._groupHeader">
                  <div class="destination-cell">
                    <el-icon class="destination-icon"><Location /></el-icon>
                    <span class="destination-name">{{ (row as ShippingOverviewData).destination_name }}</span>
                  </div>
                </template>
              </template>
            </el-table-column>

            <el-table-column label="出荷No" prop="shipping_no" min-width="180">
              <template #default="{ row }">
                <div v-if="!(row as TableRow & { _groupHeader?: boolean })._groupHeader" class="shipping-no-cell">
                  {{ (row as ShippingOverviewData).shipping_no }}
                </div>
              </template>
            </el-table-column>

            <el-table-column label="製品名" prop="product_name" min-width="250" show-overflow-tooltip>
              <template #default="{ row }">
                <template v-if="!(row as TableRow & { _groupHeader?: boolean })._groupHeader">
                  {{ (row as ShippingOverviewData).product_name }}
                </template>
              </template>
            </el-table-column>

            <el-table-column label="箱数" prop="quantity" width="100" align="center">
              <template #default="{ row }">
                <div v-if="!(row as TableRow & { _groupHeader?: boolean })._groupHeader" class="quantity-cell">
                  {{ (row as ShippingOverviewData).quantity }}
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <!-- 打印用内容（隐藏渲染，供直接打印） -->
    <div ref="reportContent" class="report-content report-content-for-print">
      <ShippingReport :data="overviewData" :filters="filters" />
    </div>

    <!-- 分组管理弹窗 -->
    <DestinationGroupManager v-model="showGroupManager" page-key="destination_groups_report"
      @groups-updated="handleGroupsUpdated" />

    <!-- 打印履历弹窗 -->
    <PrintHistoryDialog v-model="showPrintHistory" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document,
  Location,
  Setting,
  Clock,
  Calendar,
  Box,
  Files,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import ShippingReport from './components/ShippingReport.vue'
import DestinationGroupManager from './components/DestinationGroupManager.vue'
import PrintHistoryDialog from './components/PrintHistoryDialog.vue'
import ShippingCalendarDialog from './components/ShippingCalendarDialog.vue'
import { recordPrintHistory } from '@/api/shipping/printHistory'

// 接口定义
interface DestinationOption {
  value: string
  label: string
}

interface ShippingOverviewData {
  shipping_date: string
  destination_name: string
  shipping_no: string
  product_name: string
  quantity: number
}

interface DestinationGroupDestination {
  value: string
  label?: string
}

interface DestinationGroup {
  id?: string | number
  groupName?: string
  group_name?: string
  destinations: DestinationGroupDestination[]
}

/** 表格行：普通数据行 或 納入先分组标题行 */
type TableRow = ShippingOverviewData | { _groupHeader: true; destination_name: string }

interface SummaryParam {
  columns: Array<{ property: string }>
  data: TableRow[]
}

interface FilterData {
  dateRange: string[]
  destinationCds: string[]
  selectedGroup: number
}

// 响应式数据
const loading = ref(false)
const reportContent = ref<HTMLElement | null>(null)
const showGroupManager = ref(false)
const showPrintHistory = ref(false)

// 筛选条件
// 获取日本标准时间(JST)的今天日期
const getJSTToday = () => {
  const now = new Date()
  const jstOffset = 9 * 60 // JST是UTC+9
  const jstTime = new Date(now.getTime() + (jstOffset * 60 * 1000))
  return jstTime.toISOString().slice(0, 10)
}
const today = getJSTToday()
const filters = reactive<FilterData>({
  dateRange: [today, today],
  destinationCds: [],
  selectedGroup: -1, // -1表示全部，0,1,2表示对应的组
})

// 选项数据
const destinationOptions = ref<DestinationOption[]>([])
const overviewData = ref<ShippingOverviewData[]>([])
const destinationGroups = ref<DestinationGroup[]>([
  { destinations: [] },
  { destinations: [] },
  { destinations: [] },
])

// 计算属性
const totalDestinations = computed(() => {
  if (!Array.isArray(overviewData.value)) return 0
  return new Set(overviewData.value.map((item) => item?.destination_name).filter(Boolean)).size
})

const totalDates = computed(() => {
  if (!Array.isArray(overviewData.value)) return 0
  return new Set(overviewData.value.map((item) => item?.shipping_date).filter(Boolean)).size
})

const totalProducts = computed(() => {
  if (!Array.isArray(overviewData.value)) return 0
  return new Set(overviewData.value.map((item) => item?.product_name).filter(Boolean)).size
})

const totalBoxes = computed(() => {
  if (!Array.isArray(overviewData.value)) return 0
  return overviewData.value.reduce((sum, item) => sum + (Number(item?.quantity) || 0), 0)
})

const hasGroups = computed(() => {
  if (!Array.isArray(destinationGroups.value)) return false
  return destinationGroups.value.some((group) => group?.destinations?.length > 0)
})

// 按納入先分组后的表格数据（插入分组标题行）
const groupedTableData = computed<TableRow[]>(() => {
  const list = overviewData.value
  if (!Array.isArray(list) || list.length === 0) return []
  const byDest = new Map<string, ShippingOverviewData[]>()
  for (const row of list) {
    const key = row.destination_name || ''
    if (!byDest.has(key)) byDest.set(key, [])
    byDest.get(key)!.push(row)
  }
  const sortedKeys = Array.from(byDest.keys()).sort((a, b) => (a || '').localeCompare(b || ''))
  const result: TableRow[] = []
  for (const key of sortedKeys) {
    result.push({ _groupHeader: true, destination_name: key })
    result.push(...(byDest.get(key) || []))
  }
  return result
})

// 方法
onMounted(() => {
  fetchDestinationOptions()
  loadDestinationGroups()
  fetchOverviewData()
})

// 获取納入先选项
async function fetchDestinationOptions() {
  try {
    const response = await request.get('/api/master/destinations/options')
    const payload = (response as { data?: unknown }).data !== undefined ? (response as { data: unknown }).data : response

    // 处理不同的响应格式
    let data: unknown = null
    if (payload && typeof payload === 'object' && (payload as { success?: boolean }).success === true && Array.isArray((payload as { data?: unknown }).data)) {
      data = (payload as { data: unknown[] }).data
    } else if (Array.isArray(payload)) {
      data = payload
    } else if (payload && typeof payload === 'object' && Array.isArray((payload as { data?: unknown }).data)) {
      data = (payload as { data: unknown }).data
    }

    if (data && Array.isArray(data)) {
      destinationOptions.value = data.map((item: { cd: string; name: string }) => ({
        value: item.cd,
        label: `${item.cd} - ${item.name}`,
      }))
    } else {
      console.error('納入先データ格式不正确:', response)
      ElMessage.error('納入先データの取得に失敗しました')
    }
  } catch (error) {
    console.error('获取納入先选项失败:', error)
    ElMessage.error('納入先データの取得に失敗しました')
  }
}

// 获取一览数据
async function fetchOverviewData() {
  if (!filters.dateRange || filters.dateRange.length !== 2) {
    ElMessage.warning('出荷日期範囲を選択してください')
    return
  }

  loading.value = true
  try {
    const params = {
      date_from: filters.dateRange[0],
      date_to: filters.dateRange[1],
      destination_cds: filters.destinationCds.join(','),
    }

    const response = await request.get('/api/shipping/overview', { params })
    const payload = (response as { data?: unknown }).data !== undefined ? (response as { data: unknown }).data : response

    // 处理不同的响应格式
    let data: unknown = null
    if (Array.isArray(payload)) {
      data = payload
    } else if (payload && typeof payload === 'object' && Array.isArray((payload as { data?: unknown }).data)) {
      data = (payload as { data: unknown }).data
    } else if (payload && typeof payload === 'object' && (payload as { success?: boolean }).success === true && Array.isArray((payload as { data?: unknown }).data)) {
      data = (payload as { data: unknown }).data
    }

    overviewData.value = (Array.isArray(data) ? data : []) as ShippingOverviewData[]
  } catch (error) {
    console.error('获取一览数据失败:', error)
    ElMessage.error('データの取得に失敗しました')
    overviewData.value = []
  } finally {
    loading.value = false
  }
}

// 日期变化处理
function handleDateChange() {
  if (filters.dateRange && filters.dateRange.length === 2) {
    fetchOverviewData()
  }
}

// 调整日期
function adjustDate(days: number) {
  if (filters.dateRange && filters.dateRange.length === 2) {
    const startDate = new Date(filters.dateRange[0])
    const endDate = new Date(filters.dateRange[1])

    startDate.setDate(startDate.getDate() + days)
    endDate.setDate(endDate.getDate() + days)

    filters.dateRange = [startDate.toISOString().slice(0, 10), endDate.toISOString().slice(0, 10)]
    fetchOverviewData()
  }
}

// 回到今天
function goToToday() {
  const today = getJSTToday()
  filters.dateRange = [today, today]
  fetchOverviewData()
}

// 納入先变化处理
function handleDestinationChange() {
  fetchOverviewData()
}

// 格式化日期
function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  // 使用日本标准时间格式化日期
  const date = new Date(dateStr + 'T00:00:00+09:00') // 确保使用JST时区
  return date.toLocaleDateString('ja-JP', { timeZone: 'Asia/Tokyo' }).replace(/\//g, '-')
}

// 分组标题行添加 class 便于样式
function tableRowClassName({ row }: { row: TableRow }): string {
  if ('_groupHeader' in row && (row as { _groupHeader?: boolean })._groupHeader) return 'group-header-row'
  return ''
}

// 按納入先分组时的单元格合并：分组标题行占满整行
function spanMethod({
  row,
  columnIndex,
}: {
  row: TableRow
  columnIndex: number
}): [number, number] {
  const isHeader = '_groupHeader' in row && (row as { _groupHeader?: boolean })._groupHeader
  if (isHeader) {
    if (columnIndex === 0) return [1, 5]
    return [0, 0]
  }
  return [1, 1]
}

// 合计行（只合计数据行，排除分组标题行）
function getSummaries(param: SummaryParam): string[] {
  const { columns, data } = param
  const dataRows = data.filter((item) => !('_groupHeader' in item && (item as { _groupHeader?: boolean })._groupHeader))
  const sums: string[] = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合計'
      return
    }
    if (column.property === 'quantity') {
      const values = dataRows.map((item) => Number((item as ShippingOverviewData).quantity || 0))
      if (!values.every((value) => isNaN(value))) {
        sums[index] = values.reduce((prev, curr) => prev + curr, 0).toString()
      } else {
        sums[index] = ''
      }
    } else {
      sums[index] = ''
    }
  })
  return sums
}

// 報告書印刷：直接生成并执行打印（不经过预览弹窗）
async function handleReport() {
  await nextTick()
  await executeFrontendPrint(reportContent.value)
}

// 执行前端打印
async function executeFrontendPrint(contentRef: HTMLElement | null) {
  if (!contentRef || !contentRef.innerHTML) {
    ElMessage.error('印刷内容の取得に失敗しました。')
    // 记录打印失败
    await recordPrintFailure('印刷内容の取得に失敗しました。')
    return
  }

  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('ポップアップがブロックされました。ブラウザの設定を確認してください。')
    // 记录打印失败
    await recordPrintFailure('ポップアップがブロックされました。')
    return
  }

  const printHtml = contentRef.innerHTML
  const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"], style'))
    .map((el) => el.outerHTML)
    .join('')

  printWindow.document.write(`
    <html>
      <head>
        <title>出荷報告書印刷</title>
        ${styles}
      </head>
      <body>
        <div class="print-container">
          ${printHtml}
        </div>
      </body>
    </html>
  `)

  printWindow.document.close()

  printWindow.onload = () => {
    printWindow.focus()
    printWindow.print()
    printWindow.close()
    // 记录打印成功
    recordPrintSuccess()
  }
}

// 加载保存的分组
async function loadDestinationGroups() {
  try {
    const response = await request.get('/api/shipping/destination-groups/destination_groups_report')
    if (Array.isArray(response)) {
      destinationGroups.value = response.map((group) => ({
        ...group,
        groupName: group.group_name,
      }))
    } else {
      destinationGroups.value = []
    }
  } catch (error) {
    console.error('加载分组失败:', error)
    destinationGroups.value = []
    ElMessage.error('グループデータの取得に失敗しました')
  }
}

// 分组更新处理
function handleGroupsUpdated(groups: DestinationGroup[]) {
  if (Array.isArray(groups)) {
    destinationGroups.value = groups
    // 如果当前选中的分组被清空了，重置为全部
    if (filters.selectedGroup >= 0 && groups[filters.selectedGroup]?.destinations?.length === 0) {
      filters.selectedGroup = -1
      handleGroupChange()
    }
  }
}

// 分组选择变化处理
function handleGroupChange() {
  if (filters.selectedGroup === -1) {
    // 选择全部，清空筛选条件
    filters.destinationCds = []
  } else {
    // 选择特定分组，设置筛选条件为该分组的纳入先
    const selectedGroup = destinationGroups.value?.[filters.selectedGroup]
    if (
      selectedGroup?.destinations &&
      Array.isArray(selectedGroup.destinations) &&
      selectedGroup.destinations.length > 0
    ) {
      filters.destinationCds = selectedGroup.destinations.map((dest) => dest?.value).filter(Boolean)
    } else {
      filters.destinationCds = []
    }
  }
  fetchOverviewData()
}

// 记录打印成功
async function recordPrintSuccess() {
  try {
    await recordPrintHistory({
      report_type: 'shipping_report',
      report_title: '出荷報告書',
      filters: {
        dateRange: filters.dateRange,
        destinationCds: filters.destinationCds,
        selectedGroup: filters.selectedGroup,
      },
      record_count: overviewData.value?.length || 0,
      status: '成功',
    })
    console.log('打印履历记录成功')
  } catch (error) {
    console.error('记录打印履历失败:', error)
  }
}

// 记录打印失败
async function recordPrintFailure(errorMessage: string) {
  try {
    await recordPrintHistory({
      report_type: 'shipping_report',
      report_title: '出荷報告書',
      filters: {
        dateRange: filters.dateRange,
        destinationCds: filters.destinationCds,
        selectedGroup: filters.selectedGroup,
      },
      record_count: overviewData.value?.length || 0,
      status: '失败',
      error_message: errorMessage,
    })
    console.log('打印失败履历记录成功')
  } catch (error) {
    console.error('记录打印失败履历失败:', error)
  }
}
</script>

<style scoped>
.shipping-report-page {
  padding: 12px;
  background: linear-gradient(160deg, #f1f5f9 0%, #e2e8f0 100%);
  min-height: 100vh;
}

.report-card.glass-card {
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

.card-header.glass-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 18px;
  background: rgba(30, 58, 138, 0.78);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon-container {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 6px 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.header-icon {
  color: #fff;
  font-size: 18px;
}

.header-title {
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  letter-spacing: 0.02em;
}


.filter-section.glass-card {
  margin: 10px 12px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.filter-main-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin-bottom: 0;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 0 1 auto;
  min-width: 0;
}

.filter-label {
  font-weight: 500;
  color: #475569;
  font-size: 12px;
  margin-bottom: 2px;
  display: block;
}

.date-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.date-picker {
  width: 220px;
  flex-shrink: 0;
}

.date-nav-buttons {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.nav-btn.btn-glass {
  min-width: 32px;
  padding: 6px 8px;
  font-size: 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(6px);
  font-weight: 600;
  transition: all 0.2s ease;
}

.nav-btn.prev-btn,
.nav-btn.next-btn {
  background: rgba(248, 250, 252, 0.9);
  color: #64748b;
  border-color: #e2e8f0;
}

.nav-btn.prev-btn:hover,
.nav-btn.next-btn:hover {
  background: rgba(241, 245, 249, 1);
  color: #334155;
  transform: translateY(-1px);
}

.nav-btn.today-btn {
  background: rgba(37, 99, 235, 0.88);
  color: #fff;
  min-width: 44px;
}

.nav-btn.today-btn:hover {
  background: rgba(29, 78, 216, 0.95);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}

.destination-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.destination-select {
  width: 260px;
  flex-shrink: 0;
}

.destination-select :deep(.el-select__tags .el-tag) {
  border-radius: 6px;
  font-size: 12px;
}

.btn-glass {
  border-radius: 8px;
  font-weight: 600;
  font-size: 12px;
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(8px);
  transition: all 0.2s ease;
}

.btn-glass.btn-primary {
  background: rgba(59, 130, 246, 0.85);
  color: #fff;
}

.btn-glass.btn-primary:hover {
  background: rgba(37, 99, 235, 0.95);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}

.btn-glass.btn-info {
  background: rgba(100, 116, 139, 0.75);
  color: #fff;
}

.btn-glass.btn-info:hover {
  background: rgba(71, 85, 105, 0.9);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(71, 85, 105, 0.3);
}

.btn-glass.btn-success {
  background: rgba(16, 185, 129, 0.82);
  color: #fff;
}

.btn-glass.btn-success:hover {
  background: rgba(5, 150, 105, 0.95);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
}

.btn-glass.btn-success:disabled {
  background: rgba(203, 213, 225, 0.7);
  color: #94a3b8;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.filter-actions {
  display: flex;
  flex-direction: row;
  gap: 6px;
  flex-shrink: 0;
  align-items: flex-end;
  margin-left: auto;
}

.action-btn {
  white-space: nowrap;
  flex-shrink: 0;
}

.group-selection {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e2e8f0;
}

.group-selection .filter-label {
  margin-bottom: 4px;
}

.group-selection .el-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.group-selection .el-radio {
  border-radius: 8px;
  font-weight: 500;
  padding: 5px 10px;
  font-size: 12px;
  border: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.6);
  color: #475569;
}

.group-selection .el-radio:hover {
  background: rgba(248, 250, 252, 0.9);
  border-color: #cbd5e1;
}

.group-selection .el-radio.is-checked {
  background: rgba(37, 99, 235, 0.2);
  color: #1d4ed8;
  border-color: rgba(37, 99, 235, 0.5);
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin: 10px 12px;
}

.stat-card.glass-card {
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.stat-card.glass-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.stat-card.stat-destinations { border-left: 3px solid #3b82f6; }
.stat-card.stat-dates { border-left: 3px solid #8b5cf6; }
.stat-card.stat-products { border-left: 3px solid #10b981; }
.stat-card.stat-boxes { border-left: 3px solid #f59e0b; }

.stat-icon {
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  padding: 6px 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-destinations .stat-icon .el-icon { color: #2563eb; }
.stat-dates .stat-icon .el-icon { color: #7c3aed; }
.stat-products .stat-icon .el-icon { color: #059669; }
.stat-boxes .stat-icon .el-icon { color: #d97706; }

.stat-content { flex: 1; min-width: 0; }

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
  margin-top: 1px;
}

.table-section.glass-card {
  margin: 10px 12px;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.table-container {
  border-radius: 8px;
  overflow: hidden;
  background: transparent;
}

.table-container :deep(.el-table) {
  border-radius: 8px;
  --el-table-border-color: #e2e8f0;
  --el-table-header-bg-color: #f8fafc;
}

.table-container :deep(.el-table__header th) {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  padding: 8px 0;
  border-bottom: 1px solid #e2e8f0;
}

.table-container :deep(.el-table__body td) {
  padding: 8px 0;
  font-size: 12px;
}

.table-container :deep(.el-table__body tr:hover) {
  background-color: #f8fafc !important;
}

.table-container :deep(.el-table__footer) {
  background: rgba(37, 99, 235, 0.9);
  color: #fff;
  font-weight: 600;
}

.empty-state {
  padding: 24px 16px;
}

.date-cell {
  font-weight: 500;
  color: #374151;
  font-size: 13px;
}

.group-header-row :deep(td) {
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.12) 0%, rgba(59, 130, 246, 0.08) 100%) !important;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
}

.group-header-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 13px;
  color: #1e40af;
  padding: 8px 12px;
}

.group-header-icon {
  color: #2563eb;
  font-size: 16px;
}

.group-header-label {
  letter-spacing: 0.02em;
}

.destination-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.destination-icon {
  color: #2563eb;
  font-size: 14px;
}

.destination-name {
  font-weight: 500;
  color: #374151;
  font-size: 13px;
}

.shipping-no-cell {
  font-weight: 500;
  color: #2563eb;
  font-size: 13px;
}

.quantity-cell {
  font-weight: 600;
  font-size: 14px;
  color: #2563eb;
}

/* 对话框样式 */
.report-dialog {
  border-radius: 16px;
  overflow: hidden;
}

.report-dialog :deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.report-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  color: white;
  padding: 16px 20px;
}

/* 打印用内容容器：移出视口外渲染，供直接打印时取 HTML */
.report-content-for-print {
  position: fixed;
  left: -9999px;
  top: 0;
  width: 210mm;
  min-height: 100px;
  overflow: hidden;
  padding: 20px;
  background: #ffffff;
  z-index: -1;
}

.report-content {
  max-height: 70vh;
  overflow-y: auto;
  padding: 20px;
  background: #ffffff;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.dialog-header .dialog-title {
  color: white;
  font-weight: 700;
  font-size: 18px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.dialog-header .dialog-actions {
  display: flex;
  gap: 12px;
}

.dialog-header .dialog-actions .el-button {
  border-radius: 6px;
  font-weight: 500;
  margin-left: 8px;
  transition: all 0.2s ease;
  font-size: 13px;
}

.dialog-header .dialog-actions .el-button:hover {
  transform: translateY(-1px);
}

/* 响应式 */
@media (max-width: 1024px) {
  .shipping-report-page { padding: 10px; }
  .report-card.glass-card { border-radius: 10px; }
  .filter-section.glass-card { margin: 8px 10px; padding: 8px 12px; }
  .stats-section {
    grid-template-columns: repeat(2, 1fr);
    margin: 8px 10px;
  }
  .stat-value { font-size: 16px; }
  .table-section.glass-card { margin: 8px 10px; }
}

@media (max-width: 768px) {
  .shipping-report-page {
    padding: 12px;
  }

  .card-header {
    flex-direction: column;
    gap: 12px;
    text-align: center;
    padding: 12px 16px;
  }

  .header-actions {
    width: 100%;
    justify-content: center;
  }

  .filter-section {
    margin: 12px;
    padding: 12px;
  }

  .filter-main-row {
    flex-direction: column;
    gap: 12px;
  }

  .filter-item {
    width: 100%;
  }

  .date-picker {
    width: 100%;
  }

  .destination-select {
    width: 100%;
  }

  .filter-actions {
    width: 100%;
    margin-left: 0;
    flex-direction: row;
    flex-wrap: wrap;
  }

  .filter-actions .action-btn {
    flex: 1;
    min-width: 100px;
  }

  .filter-label {
    text-align: left;
  }

  .date-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .date-picker {
    width: 100%;
  }

  .date-nav-buttons {
    width: 100%;
    justify-content: space-between;
  }

  .destination-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .destination-controls .group-btn,
  .destination-controls .action-btn {
    width: 100%;
    justify-content: center;
  }

  .destination-select {
    width: 100%;
  }

  .group-selection {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #e5e7eb;
  }

  .group-selection .el-radio-group {
    flex-direction: column;
    gap: 8px;
  }

  .group-selection .el-radio {
    width: 100%;
    text-align: left;
  }

  .stats-section {
    grid-template-columns: 1fr;
    margin: 8px 10px;
    gap: 6px;
  }

  .stat-card.glass-card {
    padding: 8px 12px;
  }

  .stat-value { font-size: 16px; }
  .stat-label { font-size: 11px; }

  .table-section.glass-card {
    margin: 8px 10px;
  }

  .table-container {
    border-radius: 16px;
    overflow: hidden;
    background: white;
  }

  .table-container :deep(.el-table) {
    border-radius: 16px;
  }

  .table-container :deep(.el-table__header) {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  }

  .table-container :deep(.el-table__header th) {
    background: transparent;
    color: #374151;
    font-weight: 700;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 2px solid #e2e8f0;
  }

  .table-container :deep(.el-table__body tr:hover) {
    background-color: #f8fafc;
  }

  .table-container :deep(.el-table__footer) {
    background: #2563eb;
    color: white;
    font-weight: 600;
  }

  .overview-table-container {
    border-radius: 16px;
    overflow: hidden;
    background: white;
  }

  .overview-table-container :deep(.el-table) {
    border-radius: 16px;
  }

  .overview-table-container :deep(.el-table__header) {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  }

  .overview-table-container :deep(.el-table__header th) {
    background: transparent;
    color: #374151;
    font-weight: 700;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 2px solid #e2e8f0;
  }

  .overview-table-container :deep(.el-table__body tr:hover) {
    background-color: #f8fafc;
  }

  .overview-table-container :deep(.el-table__footer) {
    background: #2563eb;
    color: white;
    font-weight: 600;
  }

  .destination-cell {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .destination-icon {
    color: #2563eb;
    font-size: 14px;
  }

  .destination-name {
    font-weight: 500;
    color: #374151;
    font-size: 14px;
  }

  .shipping-no-cell {
    font-weight: 500;
    color: #2563eb;
    font-size: 13px;
  }

  .quantity-cell {
    font-weight: 600;
    font-size: 14px;
    color: #2563eb;
  }
}

@media (max-width: 480px) {
  .shipping-report-page { padding: 6px; }
  .report-card.glass-card { border-radius: 8px; }
  .card-header.glass-header { padding: 8px 12px; }
  .header-title { font-size: 15px; }
  .filter-section.glass-card { margin: 6px 8px; padding: 8px 10px; }
  .filter-actions .action-btn { min-width: 72px; font-size: 11px; }
  .stats-section { margin: 6px 8px; gap: 6px; }
  .stat-card.glass-card { padding: 6px 10px; }
  .stat-value { font-size: 15px; }
  .stat-label { font-size: 10px; }
  .table-section.glass-card { margin: 6px 8px; }
  .table-container :deep(.el-table__header th),
  .table-container :deep(.el-table__body td) { font-size: 11px; padding: 6px 4px; }
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

.report-card.glass-card {
  animation: fadeInUp 0.45s ease-out;
}

.filter-section.glass-card {
  animation: fadeInUp 0.4s ease-out 0.06s both;
}

.stats-section .stat-card {
  animation: fadeInUp 0.35s ease-out both;
}

.stats-section .stat-card:nth-child(1) { animation-delay: 0.1s; }
.stats-section .stat-card:nth-child(2) { animation-delay: 0.14s; }
.stats-section .stat-card:nth-child(3) { animation-delay: 0.18s; }
.stats-section .stat-card:nth-child(4) { animation-delay: 0.22s; }

.table-section.glass-card {
  animation: fadeInUp 0.4s ease-out 0.12s both;
}

/* 滚动条美化 */
.report-content::-webkit-scrollbar {
  width: 8px;
}

.report-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.report-content::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  border-radius: 4px;
}

.report-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
}
</style>
