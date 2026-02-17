<template>
  <div class="shipping-overview">
    <div class="overview-card glass-card">
      <!-- ページタイトル -->
      <div class="card-header glass-header">
        <div class="header-left">
          <div class="header-icon-container">
            <el-icon class="header-icon"><Document /></el-icon>
          </div>
          <h1 class="header-title">{{ t('shipping.overviewTitle') }}</h1>
        </div>
      </div>

      <!-- 出荷予定表カレンダー（オワリ便・吉良・社内便等グループ別印刷） -->
      <ShippingCalendarDialog :model-value="true" inline report-type="schedule" />

      <!-- フィルター条件 -->
      <div class="filter-section glass-filter">
        <div class="filter-row">
          <div class="filter-item">
            <label class="filter-label">{{ t('shipping.dateRange') }}</label>
            <el-date-picker v-model="filters.dateRange" type="daterange" :start-placeholder="t('shipping.startDate')" :end-placeholder="t('shipping.endDate')"
              value-format="YYYY-MM-DD" size="small" @change="handleDateChange" class="date-picker" />
            <div class="date-nav-buttons">
              <el-button size="small" @click="adjustDate(-1)" class="nav-btn nav-prev">←</el-button>
              <el-button size="small" @click="goToToday" class="nav-btn today-btn">{{ t('shipping.today') }}</el-button>
              <el-button size="small" @click="adjustDate(1)" class="nav-btn nav-next">→</el-button>
            </div>
          </div>

          <div class="filter-item">
            <label class="filter-label">{{ t('shipping.destination') }}</label>
            <el-select v-model="filters.destinationCds" multiple :placeholder="t('shipping.selectDestination')" collapse-tags
              collapse-tags-tooltip @change="handleDestinationChange" class="destination-select" size="small">
              <el-option v-for="dest in destinationOptions" :key="dest.value" :label="dest.label" :value="dest.value" />
            </el-select>
            <el-button :icon="Setting" @click="showGroupManager = true" class="action-btn group-btn" :title="t('shipping.groupManage')" size="small">
              {{ t('shipping.group') }}
            </el-button>
          </div>

          <div class="filter-actions">
            <el-button size="small" @click="resetFilters" class="action-btn reset-btn">{{ t('shipping.reset') }}</el-button>
            <el-button type="primary" :icon="Printer" @click="handlePrint"
              :disabled="loading || !overviewData || overviewData.length === 0" class="action-btn print-btn" size="small">
              {{ t('shipping.print') }}
            </el-button>
          </div>
        </div>

        <!-- グループ選択 -->
        <div v-if="hasGroups" class="group-selection">
          <label class="filter-label">{{ t('shipping.group') }}</label>
          <el-radio-group v-model="filters.selectedGroup" @change="handleGroupChange" class="group-radios">
            <el-radio :value="-1" class="group-radio">{{ t('shipping.all') }}</el-radio>
            <el-radio v-for="(group, index) in destinationGroups" :key="group.id || index" :value="index"
              :disabled="!group?.destinations || group.destinations.length === 0" class="group-radio">
              {{ group.groupName }} ({{ group?.destinations?.length || 0 }})
            </el-radio>
          </el-radio-group>
        </div>
      </div>

      <!-- 統計情報 -->
      <div v-if="!loading && overviewData && overviewData.length > 0" class="stats-section glass-stats">
        <div class="stats-grid">
          <div class="stat-card glass-stat destinations">
            <div class="stat-icon">
              <el-icon>
                <Location />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ totalDestinations }}</div>
              <div class="stat-label">{{ t('shipping.statDestinations') }}</div>
            </div>
          </div>

          <div class="stat-card glass-stat dates">
            <div class="stat-icon">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ totalDates }}</div>
              <div class="stat-label">{{ t('shipping.statDates') }}</div>
            </div>
          </div>

          <div class="stat-card glass-stat products">
            <div class="stat-icon">
              <el-icon><Box /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ totalProducts }}</div>
              <div class="stat-label">{{ t('shipping.statProducts') }}</div>
            </div>
          </div>

          <div class="stat-card glass-stat boxes">
            <div class="stat-icon">
              <el-icon><Files /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ totalBoxes }}</div>
              <div class="stat-label">{{ t('shipping.statBoxes') }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- データテーブル -->
      <div class="table-section glass-card" v-loading="loading">
        <el-empty v-if="!loading && (!overviewData || overviewData.length === 0)" :description="t('shipping.noData')"
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
            <el-table-column label="出荷日" prop="shipping_date" width="140" align="center" fixed>
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

            <el-table-column label="納入先" prop="destination_name" width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <template v-if="!(row as TableRow & { _groupHeader?: boolean })._groupHeader">
                  <div class="destination-cell">
                    <el-icon class="destination-icon"><Location /></el-icon>
                    <span class="destination-name">{{ (row as ShippingOverviewData).destination_name }}</span>
                  </div>
                </template>
              </template>
            </el-table-column>

            <el-table-column label="出荷No" prop="shipping_no" width="220">
              <template #default="{ row }">
                <div v-if="!(row as TableRow & { _groupHeader?: boolean })._groupHeader" class="shipping-no-cell">
                  {{ (row as ShippingOverviewData).shipping_no }}
                </div>
              </template>
            </el-table-column>

            <el-table-column label="製品名" prop="product_name" min-width="300" show-overflow-tooltip>
              <template #default="{ row }">
                <template v-if="!(row as TableRow & { _groupHeader?: boolean })._groupHeader">
                  {{ (row as ShippingOverviewData).product_name }}
                </template>
              </template>
            </el-table-column>

            <el-table-column label="箱数" prop="quantity" width="110" align="center">
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

    <!-- 印刷用の隠しコンテナ -->
    <div ref="printContent" class="print-content-hidden">
      <ShippingOverviewPrint :data="overviewData" :filters="filters" />
    </div>

    <!-- グループ管理ダイアログ -->
    <DestinationGroupManager v-model="showGroupManager" page-key="shipping_overview"
      @groups-updated="handleGroupsUpdated" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getJSTToday as getJSTTodayUtil, formatDateJST, localeForIntl } from '@/utils/dateFormat'
import {
  Document,
  Printer,
  Location,
  Box,
  Setting,
  Calendar,
  Files,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import ShippingOverviewPrint from './components/ShippingOverviewPrint.vue'
import ShippingCalendarDialog from './components/ShippingCalendarDialog.vue'
import DestinationGroupManager from './components/DestinationGroupManager.vue'

// 型定義
interface DestinationOption {
  value: string
  label: string
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

interface ShippingOverviewData {
  shipping_date: string
  destination_name: string
  shipping_no: string
  product_name: string
  quantity: number
}

interface FilterData {
  dateRange: string[]
  destinationCds: string[]
  selectedGroup: number
}

/** 表格行：普通数据行 或 納入先分组标题行 */
type TableRow = ShippingOverviewData | { _groupHeader: true; destination_name: string }

// リアクティブデータ
const loading = ref(false)
const printContent = ref<HTMLElement | null>(null)
const showGroupManager = ref(false)

const { t, locale } = useI18n()
const getJSTToday = getJSTTodayUtil

// フィルター条件
const today = getJSTToday()
const filters = reactive<FilterData>({
  dateRange: [today, today],
  destinationCds: [],
  selectedGroup: -1, // -1は全て、0,1,2は対応するグループ
})

// オプションデータ
const destinationOptions = ref<DestinationOption[]>([])
const overviewData = ref<ShippingOverviewData[]>([])
const destinationGroups = ref<DestinationGroup[]>([])

// 計算プロパティ
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

const hasGroups = computed(() => {
  if (!Array.isArray(destinationGroups.value)) return false
  return destinationGroups.value.some((group) => group?.destinations?.length > 0)
})

// メソッド
onMounted(() => {
  fetchDestinationOptions()
  loadDestinationGroups()
  fetchOverviewData()
})

// 納入先オプションを取得（与报告页统一 API）
async function fetchDestinationOptions() {
  try {
    const response = await request.get('/api/master/destinations/options')
    const payload = (response as { data?: unknown }).data !== undefined ? (response as { data: unknown }).data : response
    let data: Array<{ cd: string; name: string }> | null = null
    if (Array.isArray(payload)) {
      data = payload
    } else if (payload && typeof payload === 'object' && Array.isArray((payload as { data?: unknown }).data)) {
      data = (payload as { data: Array<{ cd: string; name: string }> }).data
    }
    if (data && Array.isArray(data)) {
      destinationOptions.value = data.map((item) => ({ value: item.cd, label: `${item.cd} - ${item.name}` }))
    } else {
      ElMessage.error('納入先データの取得に失敗しました')
    }
  } catch (error) {
    ElMessage.error('納入先データの取得に失敗しました')
  }
}

// 一覧データを取得
async function fetchOverviewData() {
  if (!filters.dateRange || filters.dateRange.length !== 2) {
    ElMessage.warning('出荷日範囲を選択してください')
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
    let data: ShippingOverviewData[] | null = null
    if (Array.isArray(payload)) {
      data = payload
    } else if (payload && typeof payload === 'object' && Array.isArray((payload as { data?: unknown }).data)) {
      data = (payload as { data: ShippingOverviewData[] }).data
    }
    overviewData.value = data || []
  } catch (error) {
    ElMessage.error('データの取得に失敗しました')
    overviewData.value = []
  } finally {
    loading.value = false
  }
}

// フィルター条件をリセット
function resetFilters() {
  const today = getJSTToday()
  filters.dateRange = [today, today]
  filters.destinationCds = []
  filters.selectedGroup = -1
  fetchOverviewData()
}

// 日付変更処理
function handleDateChange() {
  if (filters.dateRange && filters.dateRange.length === 2) {
    fetchOverviewData()
  }
}

// 日付を調整
function adjustDate(days: number) {
  if (filters.dateRange && filters.dateRange.length === 2) {
    // JST時区で日付を処理
    const startDate = new Date(filters.dateRange[0] + 'T00:00:00+09:00')
    const endDate = new Date(filters.dateRange[1] + 'T00:00:00+09:00')

    startDate.setDate(startDate.getDate() + days)
    endDate.setDate(endDate.getDate() + days)

    const formatDateStr = (date: Date) => {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }

    filters.dateRange = [formatDateStr(startDate), formatDateStr(endDate)]
    fetchOverviewData()
  }
}

// 今日に戻る
function goToToday() {
  const today = getJSTToday()
  filters.dateRange = [today, today]
  fetchOverviewData()
}

// 納入先変更処理
function handleDestinationChange() {
  fetchOverviewData()
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  return formatDateJST(dateStr, localeForIntl(locale.value)).replace(/\//g, '-')
}

// 分组标题行添加 class 便于样式
function tableRowClassName({ row }: { row: TableRow }): string {
  if ('_groupHeader' in row && (row as { _groupHeader?: boolean })._groupHeader) return 'group-header-row'
  return ''
}

// 按納入先分组时的单元格合并：分组标题行占满整行（5列）
function spanMethod({ row, columnIndex }: { row: TableRow; columnIndex: number }): [number, number] {
  const isHeader = '_groupHeader' in row && (row as { _groupHeader?: boolean })._groupHeader
  if (isHeader) {
    if (columnIndex === 0) return [1, 5]
    return [0, 0]
  }
  return [1, 1]
}

// 合計行（只合计数据行，排除分组标题行）
function getSummaries(param: { columns: Array<{ property?: string }>; data: TableRow[] }): string[] {
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
        sums[index] = String(values.reduce((prev, curr) => prev + curr, 0))
      } else {
        sums[index] = ''
      }
    } else {
      sums[index] = ''
    }
  })
  return sums
}

// 印刷処理
function handlePrint() {
  // 直接印刷を実行
  nextTick(() => {
    executeFrontendPrint(printContent.value)
  })
}

// フロントエンド印刷を実行
function executeFrontendPrint(contentRef: HTMLElement | null) {
  if (!contentRef || !contentRef.innerHTML) {
    ElMessage.error('印刷内容の取得に失敗しました。')
    return
  }

  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('ポップアップがブロックされました。ブラウザの設定を確認してください。')
    return
  }

  const printHtml = contentRef.innerHTML
  const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"], style'))
    .map((el) => el.outerHTML)
    .join('')

  printWindow.document.write(`
    <html>
      <head>
        <title>印刷</title>
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
  }
}

// グループデータを読み込み
async function loadDestinationGroups() {
  try {
    const response = await request.get('/api/shipping/destination-groups/shipping_overview')
    const body = (response as { data?: unknown })?.data ?? response

    let rawData: unknown[] = []
    if (Array.isArray(body)) {
      rawData = body
    } else if (body && typeof body === 'object' && 'success' in body && Array.isArray((body as { data?: unknown }).data)) {
      rawData = ((body as { success?: boolean; data: unknown[] }).data) ?? []
    } else if (body && typeof body === 'object' && Array.isArray((body as { data?: unknown }).data)) {
      rawData = (body as { data: unknown[] }).data
    }

    // group_nameをgroupNameに変換
    destinationGroups.value = rawData.map((group: any) => ({
      ...group,
      groupName: group.group_name,
    }))
  } catch (error) {
    console.error('グループデータの読み込みに失敗しました:', error)
    destinationGroups.value = []
  }
}

// グループ更新処理
function handleGroupsUpdated(groups: DestinationGroup[]) {
  if (Array.isArray(groups)) {
    destinationGroups.value = groups
    // 現在選択されているグループが空になった場合、全てにリセット
    if (filters.selectedGroup >= 0 && groups[filters.selectedGroup]?.destinations?.length === 0) {
      filters.selectedGroup = -1
      handleGroupChange()
    }
  }
}

// グループ選択変更処理
function handleGroupChange() {
  if (filters.selectedGroup === -1) {
    // 全てを選択、フィルター条件をクリア
    filters.destinationCds = []
  } else {
    // 特定のグループを選択、フィルター条件をそのグループの納入先に設定
    const selectedGroup = destinationGroups.value?.[filters.selectedGroup]
    if (
      selectedGroup?.destinations &&
      Array.isArray(selectedGroup.destinations) &&
      selectedGroup.destinations.length > 0
    ) {
      filters.destinationCds = selectedGroup.destinations.map((dest: DestinationGroupDestination) => dest?.value).filter(Boolean)
    } else {
      filters.destinationCds = []
    }
  }
  fetchOverviewData()
}
</script>

<style scoped>
/* ---- 基底・玻璃卡片 ---- */
/* 出荷予定表：紫色主题 */
.shipping-overview {
  padding: 8px;
  min-height: 100vh;
  background: linear-gradient(145deg, #f5f3ff 0%, #ede9fe 50%, #e0e7ff 100%);
}

.glass-card {
  border-radius: 14px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.glass-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.85) 0%, rgba(139, 92, 246, 0.85) 100%);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon-container {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon {
  color: #fff;
  font-size: 18px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin: 0;
  letter-spacing: 0.02em;
}

/* ---- 筛选区・玻璃 ---- */
.glass-filter {
  margin: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(248, 250, 252, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
  justify-content: flex-start;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.filter-label {
  font-weight: 500;
  color: #475569;
  font-size: 12px;
  white-space: nowrap;
}

.filter-actions {
  display: flex;
  gap: 6px;
  margin-left: auto;
}

/* 按钮颜色区分 + 玻璃感 */
.action-btn {
  border-radius: 8px;
  font-weight: 500;
  font-size: 12px;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}
.action-btn.print-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  border-color: rgba(255, 255, 255, 0.25);
  color: #fff;
  box-shadow: 0 1px 4px rgba(99, 102, 241, 0.35);
}
.action-btn.print-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
}
.action-btn.group-btn {
  background: rgba(148, 163, 184, 0.2);
  border: 1px solid rgba(148, 163, 184, 0.4);
  color: #475569;
}
.action-btn.group-btn:hover {
  background: rgba(148, 163, 184, 0.35);
  border-color: rgba(100, 116, 139, 0.5);
}
.action-btn.reset-btn {
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(203, 213, 225, 0.8);
  color: #64748b;
}
.action-btn.reset-btn:hover {
  background: rgba(241, 245, 249, 0.95);
  border-color: #94a3b8;
}

.date-picker {
  width: 188px;
}

.date-picker :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1px solid rgba(203, 213, 225, 0.9);
  background: rgba(255, 255, 255, 0.8);
  transition: all 0.2s ease;
}

.date-picker :deep(.el-input__wrapper:hover),
.date-picker :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.12);
}

.date-nav-buttons {
  display: flex;
  gap: 2px;
  margin-left: 2px;
}

.nav-btn {
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 500;
  min-width: 28px;
  transition: all 0.2s ease;
  border: 1px solid rgba(203, 213, 225, 0.8);
  background: rgba(248, 250, 252, 0.9);
  color: #64748b;
}
.nav-btn.nav-prev:hover,
.nav-btn.nav-next:hover {
  background: rgba(226, 232, 240, 0.95);
  border-color: #94a3b8;
  color: #475569;
}
.nav-btn.today-btn {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.5);
  color: #4f46e5;
}
.nav-btn.today-btn:hover {
  background: rgba(99, 102, 241, 0.35);
  border-color: #6366f1;
}

.destination-select {
  width: 160px;
}

.destination-select :deep(.el-select__wrapper) {
  border-radius: 8px;
  border: 1px solid rgba(203, 213, 225, 0.9);
  background: rgba(255, 255, 255, 0.8);
  transition: all 0.2s ease;
}

.destination-select :deep(.el-select__wrapper:hover),
.destination-select :deep(.el-select__wrapper.is-focused) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.12);
}

.group-selection {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(226, 232, 240, 0.8);
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
}

.group-radios :deep(.el-radio) {
  margin-right: 8px;
  border-radius: 8px;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid rgba(203, 213, 225, 0.8);
  background: rgba(255, 255, 255, 0.7);
  transition: all 0.2s ease;
}

.group-radios :deep(.el-radio:hover) {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.06);
}

.group-radios :deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #6366f1;
}

.group-radios :deep(.el-radio.is-checked) {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.9) 0%, rgba(139, 92, 246, 0.9) 100%);
  border-color: rgba(255, 255, 255, 0.3);
  color: #fff;
}

.group-radios :deep(.el-radio.is-checked .el-radio__label) {
  color: #fff;
}

/* ---- 统计区・玻璃 ---- */
.glass-stats {
  margin: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.75) 0%, rgba(139, 92, 246, 0.75) 100%);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #fff;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 6px;
}

.glass-stat {
  border-radius: 8px;
  padding: 6px 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.28);
  transition: all 0.2s ease;
}

.glass-stat:hover {
  background: rgba(255, 255, 255, 0.26);
  transform: translateY(-0.5px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  font-size: 18px;
  opacity: 0.95;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 10px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.92);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* ---- 表格区・玻璃 ---- */
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
  background: rgba(99, 102, 241, 0.9);
  color: #fff;
  font-weight: 600;
}

.date-cell {
  font-weight: 500;
  color: #374151;
  font-size: 13px;
}

.destination-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.destination-icon {
  color: #6366f1;
  font-size: 14px;
  flex-shrink: 0;
}

.destination-name {
  font-weight: 500;
  color: #374151;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shipping-no-cell {
  font-weight: 500;
  color: #6366f1;
  font-size: 13px;
}

.quantity-cell {
  font-weight: 600;
  font-size: 14px;
  color: #4f46e5;
}

.print-content-hidden {
  position: absolute;
  left: -9999px;
  top: -9999px;
  visibility: hidden;
}

.empty-state {
  padding: 24px 16px;
}

.empty-state :deep(.el-empty__description) {
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
}

.group-header-row :deep(td) {
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.14) 0%, rgba(139, 92, 246, 0.08) 100%) !important;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
}

.group-header-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 13px;
  color: #4f46e5;
  padding: 8px 12px;
}

.group-header-icon {
  color: #6366f1;
  font-size: 16px;
}

.group-header-label {
  letter-spacing: 0.02em;
}

/* ---- 响应式 ---- */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .shipping-overview {
    padding: 6px;
  }

  .glass-header {
    padding: 6px 10px;
  }

  .header-title {
    font-size: 14px;
  }

  .glass-filter {
    margin: 6px;
    padding: 6px 8px;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
  }

  .filter-actions {
    margin-left: 0;
  }

  .date-picker {
    width: 100%;
  }

  .destination-select {
    width: 100%;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .glass-stats {
    margin: 6px;
    padding: 6px 8px;
  }

  .table-section.glass-card {
    margin: 6px;
  }

  .table-container :deep(.el-table__header th),
  .table-container :deep(.el-table__body td) {
    padding: 6px 0;
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .filter-actions {
    flex-wrap: wrap;
  }

  .action-btn {
    flex: 1;
    min-width: 80px;
  }

  .stat-value {
    font-size: 16px;
  }
}

/* 打印样式 */
@media print {
  .shipping-overview {
    background: #fff !important;
    padding: 0 !important;
  }

  .glass-card,
  .glass-header,
  .glass-filter,
  .glass-stats,
  .table-section.glass-card,
  .glass-stat {
    background: #fff !important;
    backdrop-filter: none !important;
    border-color: #e2e8f0 !important;
    box-shadow: none !important;
  }

  .card-header {
    color: #000 !important;
    border-bottom: 2px solid #000 !important;
  }

  .filter-section,
  .stats-section {
    display: none !important;
  }

  .table-container :deep(.el-table__header th) {
    background: #fff !important;
    color: #000 !important;
    border: 1px solid #000 !important;
  }

  .table-container :deep(.el-table__body td) {
    border: 1px solid #000 !important;
    color: #000 !important;
  }

  .table-container :deep(.el-table__body tr:hover) {
    background: #fff !important;
  }
}
</style>
