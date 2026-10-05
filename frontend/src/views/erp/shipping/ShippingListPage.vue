<template>
  <div class="shipping-list-page sl-modern pb-std">
    <div class="list-card">
      <div class="card-header pb-hero pb-hero--page">
        <div class="header-fx pb-bubbles" aria-hidden="true" />
        <div class="header-left">
          <div class="header-icon-container">
            <el-icon class="header-icon"><Document /></el-icon>
          </div>
          <div class="header-copy">
            <h1 class="header-title pb-hero-title">{{ t('shipping.listTitle') }}</h1>
            <p class="header-desc pb-hero-desc">納入先別に出荷内容を確認し、カレンダーから便グループ別の出荷確認リストを印刷</p>
          </div>
        </div>
        <div class="header-chips">
          <span class="header-chip">
            <el-icon><Calendar /></el-icon>
            {{ headerPeriodText }}
          </span>
          <span class="header-chip">
            <el-icon><Location /></el-icon>
            {{ headerDestinationText }}
          </span>
          <span class="header-chip">
            <el-icon><Files /></el-icon>
            {{ listData?.length || 0 }}件
          </span>
        </div>
      </div>

      <!-- 出荷確認リストカレンダー（オワリ便・鈴鹿便・社内便等グループ別印刷） -->
      <ShippingCalendarDialog :model-value="true" inline report-type="list" />

      <div class="filter-section">
        <div class="filter-row">
          <div class="filter-item">
            <label class="filter-label">{{ t('shipping.dateRange') }}</label>
            <el-date-picker v-model="filters.dateRange" type="daterange" :start-placeholder="t('shipping.startDate')" :end-placeholder="t('shipping.endDate')"
              value-format="YYYY-MM-DD" @change="handleDateChange" class="date-picker" size="small" />
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
            <el-button type="primary" :icon="Printer" @click="handleReport"
              :disabled="loading || !listData || listData.length === 0" class="action-btn print-btn" size="small">
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
          <div class="stat-card destinations">
            <div class="stat-icon"><el-icon><Location /></el-icon></div>
            <div class="stat-content">
              <div class="stat-value">{{ totalDestinations }}</div>
              <div class="stat-label">納入先数</div>
            </div>
          </div>
          <div class="stat-card dates">
            <div class="stat-icon"><el-icon><Calendar /></el-icon></div>
            <div class="stat-content">
              <div class="stat-value">{{ totalDates }}</div>
              <div class="stat-label">出荷日数</div>
            </div>
          </div>
          <div class="stat-card products">
            <div class="stat-icon"><el-icon><Box /></el-icon></div>
            <div class="stat-content">
              <div class="stat-value">{{ totalProducts }}</div>
              <div class="stat-label">製品種類</div>
            </div>
          </div>
          <div class="stat-card boxes">
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
import { useSalesOperationPermission } from '@/composables/useSalesOperationPermission'
import { guardSalesOperation } from '@/utils/salesOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = useSalesOperationPermission()


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

const headerPeriodText = computed(() => {
  const [from, to] = filters.dateRange || []
  if (!from) return '—'
  return !to || from === to ? from : `${from} 〜 ${to}`
})

const headerDestinationText = computed(() => {
  if (filters.selectedGroup >= 0) {
    const g = destinationGroups.value?.[filters.selectedGroup]
    const name = g?.groupName || g?.group_name
    if (name) return name
  }
  const n = filters.destinationCds.length
  return n > 0 ? `納入先 ${n}件` : '全納入先'
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
  if (!guardSalesOperation(canEdit)) return

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
  if (!guardSalesOperation(canEdit)) return

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
  if (!guardSalesOperation(canEdit)) return

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
  if (!guardSalesOperation(canCreate)) return

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
  if (!guardSalesOperation(canEdit)) return

  if (Array.isArray(groups)) {
    destinationGroups.value = groups
    if (filters.selectedGroup >= 0 && groups[filters.selectedGroup]?.destinations?.length === 0) {
      filters.selectedGroup = -1
      handleGroupChange()
    }
  }
}

function handleGroupChange() {
  if (!guardSalesOperation(canEdit)) return

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

/* 页面美化：現代UI・色分け（出荷確認リスト / 出荷系 green→emerald） */
.shipping-list-page.sl-modern {
  background:
    radial-gradient(1000px 360px at 0% 0%, rgba(34, 197, 94, 0.1), transparent 60%),
    radial-gradient(900px 360px at 100% 0%, rgba(16, 185, 129, 0.09), transparent 60%),
    #f2f8f4;
}

.sl-modern .list-card {
  border-radius: 16px;
  border: 1px solid rgba(187, 247, 208, 0.9);
  background: rgba(255, 255, 255, 0.7);
  box-shadow:
    0 18px 40px -26px rgba(21, 128, 61, 0.55),
    0 2px 6px rgba(15, 23, 42, 0.04);
}

/* ---------- ヘッダー ---------- */
.sl-modern .card-header {
  position: relative;
  overflow: hidden;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px 18px;
  border-bottom: none;
  background: linear-gradient(120deg, #052e16 0%, #166534 34%, #16a34a 70%, #10b981 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

.sl-modern .header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.sl-modern .header-left,
.sl-modern .header-chips {
  position: relative;
  z-index: 1;
}

.sl-modern .header-left {
  gap: 12px;
  min-width: 0;
}

.sl-modern .header-icon-container {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(5, 46, 22, 0.3);
}

.sl-modern .header-icon {
  font-size: 20px;
}

.sl-modern .header-copy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
}

.sl-modern .header-title {
  padding: 0;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.sl-modern .header-desc {
  margin: 0;
  color: rgba(255, 255, 255, 0.86);
  letter-spacing: 0.02em;
}

.sl-modern .header-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.sl-modern .header-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  font-variant-numeric: tabular-nums;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

/* ---------- カレンダーとの間隔をそろえる ---------- */
.sl-modern :deep(.shipping-calendar-inline) {
  margin: 8px 8px 0;
}

/* ---------- 絞り込み ---------- */
.sl-modern .filter-section {
  position: relative;
  overflow: hidden;
  margin: 8px;
  padding: 10px 12px 8px;
  border-radius: 12px;
  border: 1px solid #d1fae5;
  background: linear-gradient(180deg, #ffffff 0%, #f6fcf8 100%);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(21, 128, 61, 0.45);
}

.sl-modern .filter-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #16a34a 0%, #10b981 60%, #34d399 100%);
}

.sl-modern .filter-row {
  gap: 8px 14px;
}

.sl-modern .filter-label {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 700;
  color: #166534;
  border-radius: 999px;
  background: #ecfdf5;
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -1px 0 #a7f3d0;
}

/* 入力枠：枠線は wrapper の内側リングのみ（二重線にしない） */
.sl-modern .date-picker :deep(.el-input__wrapper),
.sl-modern .destination-select :deep(.el-select__wrapper) {
  border: none;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 0 0 1px #cde8d8 inset;
}

.sl-modern .date-picker :deep(.el-input__wrapper:hover),
.sl-modern .destination-select :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #86efac inset;
}

.sl-modern .date-picker :deep(.el-input__wrapper.is-active),
.sl-modern .date-picker :deep(.el-input__wrapper.is-focus),
.sl-modern .destination-select :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px #16a34a inset,
    0 0 0 3px rgba(22, 163, 74, 0.14);
}

/* ---------- ボタン：軽い立体（影・動きは共通ボタン標準、色はグラデーション＋光沢） ---------- */
.sl-modern .nav-btn,
.sl-modern .action-btn {
  --k-from: #4ade80;
  --k-to: #16a34a;
  --k-edge: #15803d;
  --k-rgb: 22 163 74;
  min-width: 0;
  color: #fff;
  font-weight: 700;
  border: 1px solid var(--k-edge);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, var(--k-from) 0%, var(--k-to) 100%);
}

.sl-modern .nav-btn:not(:disabled):hover,
.sl-modern .action-btn:not(:disabled):hover,
.sl-modern .nav-btn:focus-visible,
.sl-modern .action-btn:focus-visible {
  color: #fff;
  border-color: var(--k-edge);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, var(--k-from) 0%, var(--k-to) 100%);
}

.sl-modern .date-nav-buttons {
  gap: 0;
  margin-left: 4px;
}

.sl-modern .nav-btn.nav-prev,
.sl-modern .nav-btn.nav-next {
  color: #166534;
  border-color: #bbf7d0;
  background: linear-gradient(180deg, #ffffff 0%, #f3fcf6 100%);
}

.sl-modern .nav-btn.nav-prev:not(:disabled):hover,
.sl-modern .nav-btn.nav-next:not(:disabled):hover,
.sl-modern .nav-btn.nav-prev:focus-visible,
.sl-modern .nav-btn.nav-next:focus-visible {
  color: #14532d;
  border-color: #86efac;
  background: linear-gradient(180deg, #ffffff 0%, #e8f9ee 100%);
}

.sl-modern .nav-btn.today-btn {
  --k-from: #34d399;
  --k-to: #059669;
  --k-edge: #047857;
  --k-rgb: 5 150 105;
}

.sl-modern .action-btn.group-btn {
  --k-from: #94a3b8;
  --k-to: #64748b;
  --k-edge: #475569;
  --k-rgb: 71 85 105;
}

.sl-modern .action-btn.print-btn {
  --k-from: #4ade80;
  --k-to: #15803d;
  --k-edge: #166534;
  --k-rgb: 21 128 61;
}

.sl-modern .action-btn.print-btn:disabled,
.sl-modern .action-btn.print-btn.is-disabled {
  color: #94a3b8;
  border-color: #d1d5db;
  background: #e5e7eb;
}

/* グループ選択：ピルチップ（淡い立体、hover は 1px 浮上のみ） */
.sl-modern .group-selection {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #cde8d8;
}

.sl-modern .group-radios :deep(.el-radio) {
  height: 26px;
  margin-right: 6px;
  padding: 0 12px 0 8px;
  font-size: 12px;
  border-radius: 999px;
  border: 1px solid #d1fae5;
  background: #fff;
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -2px 0 rgba(22, 163, 74, 0.06),
    0 1px 2px rgba(15, 23, 42, 0.05);
  transition:
    transform 0.18s cubic-bezier(0.34, 1.56, 0.64, 1),
    box-shadow 0.18s ease,
    border-color 0.15s ease,
    background 0.15s ease;
}

.sl-modern .group-radios :deep(.el-radio__label) {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
}

.sl-modern .group-radios :deep(.el-radio:not(.is-disabled):not(.is-checked):hover) {
  transform: translateY(-1px);
  border-color: #86efac;
  background: #f6fcf8;
  box-shadow:
    inset 0 1px 0 #ffffff,
    0 6px 12px -6px rgba(22, 163, 74, 0.5);
}

.sl-modern .group-radios :deep(.el-radio.is-checked) {
  border-color: #15803d;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #22c55e 0%, #10b981 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 -2px 0 rgba(20, 83, 45, 0.3),
    0 4px 10px -4px rgba(22, 163, 74, 0.6);
}

.sl-modern .group-radios :deep(.el-radio.is-checked .el-radio__label) {
  color: #fff;
}

.sl-modern .group-radios :deep(.el-radio.is-checked .el-radio__inner) {
  border-color: #fff;
  background: #fff;
}

.sl-modern .group-radios :deep(.el-radio.is-checked .el-radio__inner::after) {
  background: #16a34a;
}

.sl-modern .group-radios :deep(.el-radio.is-disabled) {
  background: #f1f5f9;
  box-shadow: none;
}

.sl-modern .group-radios :deep(.el-radio.is-disabled .el-radio__label) {
  color: #94a3b8;
}

/* ---------- 統計カード（色分け・動きなし） ---------- */
.sl-modern .stats-section {
  margin: 0 8px 8px;
  padding: 0;
  color: inherit;
  border: none;
  background: transparent;
}

.sl-modern .stats-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.sl-modern .stat-card {
  --tc: #16a34a;
  position: relative;
  overflow: hidden;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--tc) 18%, #e2e8f0);
  background: linear-gradient(160deg, color-mix(in srgb, var(--tc) 7%, #fff) 0%, #fff 70%);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 18px -16px color-mix(in srgb, var(--tc) 70%, transparent);
}

.sl-modern .stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--tc) 45%, #fff), var(--tc));
}

.sl-modern .stat-card.destinations {
  --tc: #16a34a;
}

.sl-modern .stat-card.dates {
  --tc: #0891b2;
}

.sl-modern .stat-card.products {
  --tc: #7c3aed;
}

.sl-modern .stat-card.boxes {
  --tc: #d97706;
}

.sl-modern .stat-card .stat-icon {
  width: 32px;
  height: 32px;
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #fff;
  opacity: 1;
  border-radius: 9px;
  background: linear-gradient(145deg, color-mix(in srgb, var(--tc) 60%, #fff) 0%, var(--tc) 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(15, 23, 42, 0.15),
    0 4px 10px -4px color-mix(in srgb, var(--tc) 70%, transparent);
}

.sl-modern .stat-card .stat-value {
  font-size: 19px;
  font-weight: 800;
  line-height: 1.15;
  color: color-mix(in srgb, var(--tc) 40%, #0f172a);
  font-variant-numeric: tabular-nums;
}

.sl-modern .stat-card .stat-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: none;
  color: #64748b;
}

/* ---------- 一覧テーブル ---------- */
.sl-modern .table-section.glass-card {
  position: relative;
  margin: 0 8px 8px;
  border-radius: 12px;
  border: 1px solid #d1fae5;
  background: #fff;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(21, 128, 61, 0.45);
}

.sl-modern .table-section.glass-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 3;
  background: linear-gradient(90deg, #16a34a 0%, #10b981 60%, #34d399 100%);
}

.sl-modern .table-container {
  border-radius: 0;
}

.sl-modern .table-container :deep(.el-table) {
  --el-table-border-color: #eef2f7;
  --el-table-row-hover-bg-color: #f2fbf5;
  border-radius: 0;
  color: #1e293b;
}

.sl-modern .table-container :deep(.el-table__header-wrapper th.el-table__cell) {
  padding: 7px 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #166534;
  background: linear-gradient(180deg, #f6fcf8 0%, #e8f8ee 100%) !important;
  border-bottom: 1px solid #bbf7d0;
}

.sl-modern .table-container :deep(.el-table__body td.el-table__cell) {
  padding: 6px 8px;
  font-size: 13px;
  line-height: 1.45;
}

.sl-modern .table-container :deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: #f8fcf9;
}

.sl-modern .table-container :deep(.el-table__body tr:not(.group-header-row):hover > td.el-table__cell) {
  background: #f2fbf5 !important;
}

.sl-modern .table-container :deep(.el-table__body tr:not(.group-header-row):hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 #16a34a;
}

.sl-modern .group-header-row :deep(td) {
  background: linear-gradient(90deg, #e8f8ee 0%, #f0fdf4 55%, #ffffff 100%) !important;
  border-bottom: 1px solid #d1fae5;
}

.sl-modern .group-header-cell {
  padding: 4px 8px;
  font-size: 13px;
  color: #14532d;
}

.sl-modern .group-header-icon {
  width: 22px;
  height: 22px;
  font-size: 12px;
  color: #fff;
  border-radius: 6px;
  background: linear-gradient(145deg, #4ade80 0%, #16a34a 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(20, 83, 45, 0.3);
}

.sl-modern .no-cell,
.sl-modern .date-cell {
  font-weight: 700;
  color: #334155;
  font-variant-numeric: tabular-nums;
}

.sl-modern .destination-name {
  font-weight: 600;
  color: #1e293b;
}

.sl-modern .shipping-no-cell {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-weight: 600;
  color: #15803d;
}

.sl-modern .quantity-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  padding: 1px 10px;
  font-weight: 800;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  color: #92400e;
  border-radius: 999px;
  background: #fffbeb;
  box-shadow: inset 0 0 0 1px #fde68a;
}

/* 合計行：淡いグリーンで強調（濃い塗りにしない） */
.sl-modern .table-container :deep(.el-table__footer) {
  color: #14532d;
  background: #ecfdf5;
}

.sl-modern .table-container :deep(.el-table__footer-wrapper td.el-table__cell) {
  padding: 7px 8px;
  font-size: 13px;
  font-weight: 800;
  color: #14532d;
  font-variant-numeric: tabular-nums;
  background: #ecfdf5 !important;
  border-top: 2px solid #86efac;
  border-color: #d1fae5;
}

.sl-modern .table-container :deep(.el-table__body-wrapper) {
  scrollbar-width: thin;
  scrollbar-color: #bbf7d0 transparent;
}

.sl-modern .empty-state {
  padding: 20px 16px;
}

@media (max-width: 1200px) {
  .sl-modern .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .sl-modern .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
