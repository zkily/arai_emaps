<template>
  <div class="shipping-list-page">
    <div class="list-card">
      <div class="card-header">
        <div class="header-left">
          <div class="header-icon-container">
            <el-icon class="header-icon"><Document /></el-icon>
          </div>
          <h1 class="header-title">出荷確認リスト</h1>
        </div>
      </div>

      <div class="filter-section">
        <div class="filter-row">
          <div class="filter-item">
            <label class="filter-label">出荷日</label>
            <el-date-picker v-model="filters.dateRange" type="daterange" start-placeholder="開始日" end-placeholder="終了日"
              value-format="YYYY-MM-DD" @change="handleDateChange" class="date-picker" size="small" />
            <div class="date-nav-buttons">
              <el-button size="small" @click="adjustDate(-1)" class="nav-btn">←</el-button>
              <el-button size="small" @click="goToToday" class="nav-btn today-btn">今日</el-button>
              <el-button size="small" @click="adjustDate(1)" class="nav-btn">→</el-button>
            </div>
          </div>

          <div class="filter-item">
            <label class="filter-label">納入先</label>
            <el-select v-model="filters.destinationCds" multiple placeholder="納入先を選択" collapse-tags
              collapse-tags-tooltip @change="handleDestinationChange" class="destination-select" size="small">
              <el-option v-for="dest in destinationOptions" :key="dest.value" :label="dest.label" :value="dest.value" />
            </el-select>
            <el-button :icon="Setting" @click="showGroupManager = true" class="group-btn" title="納入先グループ管理" size="small">
              グループ
            </el-button>
          </div>

          <div class="filter-actions">
            <el-button type="primary" :icon="Printer" @click="handleReport"
              :disabled="loading || !listData || listData.length === 0" class="print-btn" size="small">
              印刷
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

      <div class="table-section" v-loading="loading">
        <el-empty v-if="!loading && (!listData || listData.length === 0)" description="条件に合うデータがありません" :image-size="56" class="empty-state" />
        <div v-else class="table-container">
          <el-table :data="listData" stripe style="width: 100%" show-summary :summary-method="getSummaries" size="small" class="modern-table">
            <el-table-column label="No" prop="no" width="80" align="center" fixed>
              <template #default="{ row }"><div class="no-cell">{{ row.no }}</div></template>
            </el-table-column>
            <el-table-column label="出荷日" prop="shipping_date" width="120" align="center">
              <template #default="{ row }"><div class="date-cell">{{ formatDate(row.shipping_date) }}</div></template>
            </el-table-column>
            <el-table-column label="納入先" prop="destination_name" width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="destination-cell">
                  <el-icon class="destination-icon"><Location /></el-icon>
                  <span class="destination-name">{{ row.destination_name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="出荷No" prop="shipping_no" width="200">
              <template #default="{ row }"><div class="shipping-no-cell">{{ row.shipping_no }}</div></template>
            </el-table-column>
            <el-table-column label="製品名" prop="product_name" min-width="300" show-overflow-tooltip />
            <el-table-column label="箱数" prop="quantity" width="100" align="center">
              <template #default="{ row }"><div class="quantity-cell">{{ row.quantity }}</div></template>
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
import { ElMessage } from 'element-plus'
import { Document, Printer, Location, Setting, Calendar, Box, Files } from '@element-plus/icons-vue'
import request from '@/utils/request'
import ShippingListReport from './components/ShippingListReport.vue'
import DestinationGroupManager from './components/DestinationGroupManager.vue'

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

const loading = ref(false)
const printContent = ref<HTMLElement | null>(null)
const showGroupManager = ref(false)

const getJSTToday = () => {
  const now = new Date()
  const jstDateStr = now.toLocaleString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
  return jstDateStr.replace(/\//g, '-')
}

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
  const date = new Date(dateStr + 'T00:00:00+09:00')
  return date.toLocaleDateString('ja-JP', { timeZone: 'Asia/Tokyo', year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '-')
}

function getSummaries(param: { columns: Array<{ property?: string }>; data: ShippingListItem[] }): string[] {
  const { columns, data } = param
  const sums: string[] = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合計'
      return
    }
    if (column.property === 'quantity') {
      const values = data.map((item) => Number(item.quantity || 0))
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
.shipping-list-page {
  padding: 8px;
  min-height: 100vh;
  background: linear-gradient(145deg, #e8ecf4 0%, #dde2eb 50%, #e2e8f0 100%);
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

.table-section {
  margin: 8px;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.modern-table :deep(.el-table__header th) {
  background: rgba(248, 250, 252, 0.9);
  color: #374151;
  font-weight: 600;
  font-size: 12px;
  padding: 5px 8px;
}

.modern-table :deep(.el-table__body td) {
  padding: 5px 8px;
  font-size: 12px;
}

.no-cell,
.date-cell {
  font-weight: 500;
  color: #374151;
}

.destination-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}

.destination-icon {
  color: #059669;
  font-size: 12px;
}

.destination-name {
  font-weight: 500;
  color: #374151;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shipping-no-cell {
  font-family: ui-monospace, monospace;
  font-weight: 500;
  color: #475569;
  font-size: 11px;
  background: rgba(248, 250, 252, 0.9);
  border-radius: 4px;
  padding: 2px 6px;
  display: inline-block;
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.quantity-cell {
  font-weight: 600;
  color: #dc2626;
  font-size: 12px;
  text-align: right;
}

.print-content-hidden {
  position: absolute;
  left: -9999px;
  top: -9999px;
  visibility: hidden;
}

.empty-state {
  padding: 24px 12px;
  margin: 8px;
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.7);
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
