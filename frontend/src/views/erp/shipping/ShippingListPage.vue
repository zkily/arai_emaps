<template>
  <div class="shipping-list-page">
    <div class="list-card">
      <div class="card-header">
        <div class="header-left">
          <div class="header-icon-container">
            <el-icon class="header-icon"><Document /></el-icon>
          </div>
          <h1 class="header-title">{{ t('shipping.listTitle') }}</h1>
        </div>
      </div>

      <!-- 出荷確認リストカレンダー（オワリ便・社内便等グループ別印刷） -->
      <ShippingCalendarDialog :model-value="true" inline report-type="list" />

      <div class="filter-section">
        <div class="filter-row">
          <div class="filter-item">
            <label class="filter-label">{{ t('shipping.dateRange') }}</label>
            <el-date-picker v-model="filters.dateRange" type="daterange" :start-placeholder="t('shipping.startDate')" :end-placeholder="t('shipping.endDate')"
              value-format="YYYY-MM-DD" @change="handleDateChange" class="date-picker" size="small" />
            <div class="date-nav-buttons">
              <el-button size="small" @click="adjustDate(-1)" class="nav-btn">←</el-button>
              <el-button size="small" @click="goToToday" class="nav-btn today-btn">{{ t('shipping.today') }}</el-button>
              <el-button size="small" @click="adjustDate(1)" class="nav-btn">→</el-button>
            </div>
          </div>

          <div class="filter-item">
            <label class="filter-label">{{ t('shipping.destination') }}</label>
            <el-select v-model="filters.destinationCds" multiple :placeholder="t('shipping.selectDestination')" collapse-tags
              collapse-tags-tooltip @change="handleDestinationChange" class="destination-select" size="small">
              <el-option v-for="dest in destinationOptions" :key="dest.value" :label="dest.label" :value="dest.value" />
            </el-select>
            <el-button :icon="Setting" @click="showGroupManager = true" class="group-btn" :title="t('shipping.groupManage')" size="small">
              {{ t('shipping.group') }}
            </el-button>
          </div>

          <div class="filter-actions">
            <el-button type="primary" :icon="Printer" @click="handleReport"
              :disabled="loading || !listData || listData.length === 0" class="print-btn" size="small">
              {{ t('shipping.print') }}
            </el-button>
          </div>
        </div>

        <div v-if="hasGroups" class="group-selection">
          <label class="filter-label">グループ選択</label>
          <el-radio-group v-model="filters.selectedGroup" @change="handleGroupChange" class="group-radios">
            <el-radio :value="-1" class="group-radio">{{ t('shipping.all') }}</el-radio>
            <el-radio v-for="(group, index) in destinationGroups" :key="group.id || index" :value="index"
              :disabled="!group?.destinations || group.destinations.length === 0" class="group-radio">
              {{ group.groupName }} ({{ group?.destinations?.length || 0 }})
            </el-radio>
          </el-radio-group>
        </div>
      </div>

      <div v-if="!loading && listData && listData.length > 0" class="stats-section">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon"><el-icon><Location /></el-icon></div>
            <div class="stat-content">
              <div class="stat-value">{{ totalDestinations }}</div>
              <div class="stat-label">納入先数</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon"><el-icon><Calendar /></el-icon></div>
            <div class="stat-content">
              <div class="stat-value">{{ totalDates }}</div>
              <div class="stat-label">出荷日数</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon"><el-icon><Box /></el-icon></div>
            <div class="stat-content">
              <div class="stat-value">{{ totalProducts }}</div>
              <div class="stat-label">製品種類</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon"><el-icon><Files /></el-icon></div>
            <div class="stat-content">
              <div class="stat-value">{{ totalBoxes }}</div>
              <div class="stat-label">総箱数</div>
            </div>
          </div>
        </div>
      </div>

      <div class="table-section glass-card" v-loading="loading">
        <el-empty v-if="!loading && (!listData || listData.length === 0)" :description="t('shipping.noData')" :image-size="56" class="empty-state" />
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
            <el-table-column label="No" prop="no" width="80" align="center" fixed>
              <template #default="{ row }">
                <template v-if="(row as TableRow & { _groupHeader?: boolean })._groupHeader">
                  <div class="group-header-cell">
                    <el-icon class="group-header-icon"><Location /></el-icon>
                    <span class="group-header-label">{{ (row as { destination_name: string }).destination_name }}</span>
                  </div>
                </template>
                <div v-else class="no-cell">{{ (row as ShippingListItem).no }}</div>
              </template>
            </el-table-column>
            <el-table-column label="出荷日" prop="shipping_date" width="120" align="center">
              <template #default="{ row }">
                <div v-if="!(row as TableRow & { _groupHeader?: boolean })._groupHeader" class="date-cell">
                  {{ formatDate((row as ShippingListItem).shipping_date) }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="納入先" prop="destination_name" width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <div v-if="!(row as TableRow & { _groupHeader?: boolean })._groupHeader" class="destination-cell">
                  <el-icon class="destination-icon"><Location /></el-icon>
                  <span class="destination-name">{{ (row as ShippingListItem).destination_name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="出荷No" prop="shipping_no" width="200">
              <template #default="{ row }">
                <div v-if="!(row as TableRow & { _groupHeader?: boolean })._groupHeader" class="shipping-no-cell">
                  {{ (row as ShippingListItem).shipping_no }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="製品名" prop="product_name" min-width="300" show-overflow-tooltip>
              <template #default="{ row }">
                <template v-if="!(row as TableRow & { _groupHeader?: boolean })._groupHeader">
                  {{ (row as ShippingListItem).product_name }}
                </template>
              </template>
            </el-table-column>
            <el-table-column label="箱数" prop="quantity" width="100" align="center">
              <template #default="{ row }">
                <div v-if="!(row as TableRow & { _groupHeader?: boolean })._groupHeader" class="quantity-cell">
                  {{ (row as ShippingListItem).quantity }}
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <div ref="printContent" class="print-content-hidden">
      <ShippingListReport :data="listData" :filters="filters" />
    </div>

    <DestinationGroupManager v-model="showGroupManager" page-key="shipping_list" @groups-updated="handleGroupsUpdated" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getJSTToday as getJSTTodayUtil, formatDateJST, localeForIntl } from '@/utils/dateFormat'
import { Document, Printer, Location, Setting, Calendar, Box, Files } from '@element-plus/icons-vue'
import request from '@/utils/request'
import ShippingListReport from './components/ShippingListReport.vue'
import DestinationGroupManager from './components/DestinationGroupManager.vue'
import ShippingCalendarDialog from './components/ShippingCalendarDialog.vue'

interface DestinationOption {
  value: string
  label: string
}

interface ShippingListItem {
  no: string
  shipping_date: string
  destination_name: string
  shipping_no: string
  product_name: string
  quantity: number
}

interface DestinationGroup {
  id?: number
  groupName: string
  group_name?: string
  destinations: Array<{ value: string; label?: string }>
}

interface FilterState {
  dateRange: [string, string]
  destinationCds: string[]
  selectedGroup: number
}

/** 表格行：普通数据行 或 納入先分组标题行 */
type TableRow = ShippingListItem | { _groupHeader: true; destination_name: string }

const loading = ref(false)
const printContent = ref<HTMLElement | null>(null)
const showGroupManager = ref(false)

const { t, locale } = useI18n()
const getJSTToday = getJSTTodayUtil

const today = getJSTToday()
const filters = reactive<FilterState>({
  dateRange: [today, today],
  destinationCds: [],
  selectedGroup: -1,
})

const destinationOptions = ref<DestinationOption[]>([])
const listData = ref<ShippingListItem[]>([])
const destinationGroups = ref<DestinationGroup[]>([])

const totalDestinations = computed(() => {
  if (!Array.isArray(listData.value)) return 0
  return new Set(listData.value.map((item) => item?.destination_name).filter(Boolean)).size
})

const totalDates = computed(() => {
  if (!Array.isArray(listData.value)) return 0
  return new Set(listData.value.map((item) => item?.shipping_date).filter(Boolean)).size
})

const totalProducts = computed(() => {
  if (!Array.isArray(listData.value)) return 0
  return new Set(listData.value.map((item) => item?.product_name).filter(Boolean)).size
})

const totalBoxes = computed(() => {
  if (!Array.isArray(listData.value)) return 0
  return listData.value.reduce((sum, item) => sum + (Number(item?.quantity) || 0), 0)
})

const hasGroups = computed(() => {
  if (!Array.isArray(destinationGroups.value)) return false
  return destinationGroups.value.some((group) => group?.destinations?.length > 0)
})

// 按納入先分组后的表格数据（插入分组标题行）
const groupedTableData = computed<TableRow[]>(() => {
  const list = listData.value
  if (!Array.isArray(list) || list.length === 0) return []
  const byDest = new Map<string, ShippingListItem[]>()
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

onMounted(() => {
  fetchDestinationOptions()
  loadDestinationGroups()
  fetchListData()
})

async function fetchDestinationOptions() {
  try {
    const response = await request.get('/api/master/options/destination-options')
    const body = (response as { data?: unknown })?.data ?? response
    let data: unknown = null
    if (body && typeof body === 'object' && 'success' in body && Array.isArray((body as unknown as { data?: unknown }).data)) {
      data = (body as unknown as { data: unknown }).data
    } else if (Array.isArray(body)) {
      data = body
    } else if (body && typeof body === 'object' && Array.isArray((body as unknown as { data?: unknown }).data)) {
      data = (body as unknown as { data: unknown }).data
    }
    if (data && Array.isArray(data)) {
      destinationOptions.value = (data as Array<{ cd: string; name: string }>).map((item) => ({
        value: item.cd,
        label: `${item.cd} - ${item.name}`,
      }))
    } else {
      ElMessage.error('納入先データの取得に失敗しました')
    }
  } catch (error) {
    ElMessage.error('納入先データの取得に失敗しました')
  }
}

async function fetchListData() {
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
    const body = (response as { data?: unknown })?.data ?? response
    let data: unknown[] | null = null
    if (Array.isArray(body)) {
      data = body
    } else if (body && typeof body === 'object' && Array.isArray((body as unknown as { data?: unknown }).data)) {
      data = (body as unknown as { data: unknown[] }).data
    } else if (body && typeof body === 'object' && 'success' in body && Array.isArray((body as unknown as { data?: unknown }).data)) {
      data = (body as unknown as { data: unknown[] }).data
    }
    if (data && Array.isArray(data)) {
      const arr = data as Array<Record<string, unknown>>
      arr.sort((a, b) => (String(a.shipping_no || '')).localeCompare(String(b.shipping_no || '')))
      arr.forEach((item) => {
        const shippingNo = String(item.shipping_no || '')
        item.no = shippingNo.slice(-2) || '00'
      })
      listData.value = arr as unknown as ShippingListItem[]
    } else {
      listData.value = []
    }
  } catch (error) {
    ElMessage.error('データの取得に失敗しました')
    listData.value = []
  } finally {
    loading.value = false
  }
}

function handleDateChange() {
  if (filters.dateRange && filters.dateRange.length === 2) fetchListData()
}

function adjustDate(days: number) {
  if (!filters.dateRange || filters.dateRange.length !== 2) return
  const startDate = new Date(filters.dateRange[0] + 'T00:00:00+09:00')
  const endDate = new Date(filters.dateRange[1] + 'T00:00:00+09:00')
  startDate.setDate(startDate.getDate() + days)
  endDate.setDate(endDate.getDate() + days)
  const formatDateStr = (d: Date) => {
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  }
  filters.dateRange = [formatDateStr(startDate), formatDateStr(endDate)]
  fetchListData()
}

function goToToday() {
  filters.dateRange = [getJSTToday(), getJSTToday()]
  fetchListData()
}

function handleDestinationChange() {
  fetchListData()
}

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  return formatDateJST(dateStr, localeForIntl(locale.value)).replace(/\//g, '-')
}

function tableRowClassName({ row }: { row: TableRow }): string {
  if ('_groupHeader' in row && (row as { _groupHeader?: boolean })._groupHeader) return 'group-header-row'
  return ''
}

function spanMethod({ row, columnIndex }: { row: TableRow; columnIndex: number }): [number, number] {
  const isHeader = '_groupHeader' in row && (row as { _groupHeader?: boolean })._groupHeader
  if (isHeader) {
    if (columnIndex === 0) return [1, 6]
    return [0, 0]
  }
  return [1, 1]
}

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
      const values = dataRows.map((item) => Number((item as ShippingListItem).quantity || 0))
      sums[index] = values.every((v) => isNaN(v)) ? '' : String(values.reduce((p, c) => p + c, 0))
    } else {
      sums[index] = ''
    }
  })
  return sums
}

function handleReport() {
  nextTick(() => {
    if (!printContent.value?.innerHTML) {
      ElMessage.error('印刷内容の取得に失敗しました。')
      return
    }
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('ポップアップがブロックされました。ブラウザの設定を確認してください。')
      return
    }
    const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"], style')).map((el) => el.outerHTML).join('')
    printWindow.document.write(`
      <html><head><title>出荷確認リスト印刷</title>${styles}</head>
      <body><div class="print-container">${printContent.value.innerHTML}</div></body></html>
    `)
    printWindow.document.close()
    printWindow.onload = () => {
      printWindow.focus()
      printWindow.print()
      setTimeout(() => printWindow?.close(), 100)
    }
  })
}

async function loadDestinationGroups() {
  try {
    const response = await request.get('/api/shipping/destination-groups/shipping_list')
    const body = (response as { data?: unknown })?.data ?? response
    let rawData: unknown[] = []
    if (Array.isArray(body)) {
      rawData = body
    } else if (body && typeof body === 'object' && 'success' in body && Array.isArray((body as unknown as { data?: unknown }).data)) {
      rawData = ((body as unknown as { data: unknown[] }).data) ?? []
    } else if (body && typeof body === 'object' && Array.isArray((body as unknown as { data?: unknown }).data)) {
      rawData = (body as unknown as { data: unknown[] }).data
    }
    destinationGroups.value = rawData.map((group) => {
      const g = group as Record<string, unknown>
      return { ...g, groupName: g.group_name } as DestinationGroup
    })
  } catch (error) {
    destinationGroups.value = []
  }
}

function handleGroupsUpdated(groups: DestinationGroup[]) {
  if (Array.isArray(groups)) {
    destinationGroups.value = groups
    if (filters.selectedGroup >= 0 && groups[filters.selectedGroup]?.destinations?.length === 0) {
      filters.selectedGroup = -1
      handleGroupChange()
    }
  }
}

function handleGroupChange() {
  if (filters.selectedGroup === -1) {
    filters.destinationCds = []
  } else {
    const selectedGroup = destinationGroups.value?.[filters.selectedGroup]
    if (selectedGroup?.destinations?.length) {
      filters.destinationCds = selectedGroup.destinations.map((d) => d?.value).filter(Boolean)
    } else {
      filters.destinationCds = []
    }
  }
  fetchListData()
}
</script>

<style scoped>
/* 出荷確認リスト：绿色主题 */
.shipping-list-page {
  padding: 8px;
  min-height: 100vh;
  background: linear-gradient(145deg, #f0fdf4 0%, #dcfce7 50%, #d1fae5 100%);
}

.list-card {
  border-radius: 14px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(14px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.9) 0%, rgba(22, 163, 74, 0.9) 100%);
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
}

.filter-section {
  margin: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(248, 250, 252, 0.7);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-label {
  font-weight: 500;
  color: #475569;
  font-size: 12px;
  white-space: nowrap;
}

.filter-actions {
  margin-left: auto;
  display: flex;
  gap: 6px;
}

.print-btn {
  border-radius: 8px;
  font-weight: 500;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.9) 0%, rgba(22, 163, 74, 0.9) 100%);
  border-color: rgba(255, 255, 255, 0.25);
  color: #fff;
}
.print-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(22, 163, 74, 0.95) 0%, rgba(21, 128, 61, 0.95) 100%);
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.35);
}

.group-btn {
  background: rgba(148, 163, 184, 0.2);
  border: 1px solid rgba(148, 163, 184, 0.4);
  color: #475569;
  border-radius: 8px;
}

.group-btn:hover {
  background: rgba(148, 163, 184, 0.35);
}

.date-picker {
  width: 188px;
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
  min-width: 28px;
  border: 1px solid rgba(203, 213, 225, 0.8);
  background: rgba(248, 250, 252, 0.9);
  color: #64748b;
}

.today-btn {
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.35);
  color: #16a34a;
}

.today-btn:hover {
  background: rgba(34, 197, 94, 0.2);
}

.destination-select {
  width: 160px;
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
  font-size: 11px;
}

.stats-section {
  margin: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.75) 0%, rgba(22, 163, 74, 0.75) 100%);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.25);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 6px;
}

.stat-card {
  border-radius: 8px;
  padding: 6px 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.stat-icon {
  font-size: 18px;
  opacity: 0.95;
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
  background: rgba(22, 163, 74, 0.9);
  color: #fff;
  font-weight: 600;
}

.group-header-row :deep(td) {
  background: linear-gradient(90deg, rgba(34, 197, 94, 0.14) 0%, rgba(22, 163, 74, 0.08) 100%) !important;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
}

.group-header-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 13px;
  color: #15803d;
  padding: 8px 12px;
}

.group-header-icon {
  color: #16a34a;
  font-size: 16px;
}

.group-header-label {
  letter-spacing: 0.02em;
}

.empty-state {
  padding: 24px 16px;
}

.no-cell,
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
  color: #16a34a;
  font-size: 14px;
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
  color: #15803d;
  font-size: 13px;
}

.quantity-cell {
  font-weight: 600;
  font-size: 14px;
  color: #16a34a;
}

.print-content-hidden {
  position: absolute;
  left: -9999px;
  top: -9999px;
  visibility: hidden;
}

@media (max-width: 768px) {
  .shipping-list-page {
    padding: 6px;
  }
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-actions {
    margin-left: 0;
  }
  .date-picker,
  .destination-select {
    width: 100%;
  }
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
