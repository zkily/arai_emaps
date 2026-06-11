<template>
  <div class="destination-holiday-container">
    <!-- Compact Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-row">
          <span class="title-icon">📅</span>
          <h1 class="main-title">納入先休日設定</h1>
          <div class="stat-badges">
            <div class="stat-badge"><span class="stat-number">{{ holidayList.length }}</span><span class="stat-label">休日</span></div>
            <div class="stat-badge stat-workday"><span class="stat-number">{{ workdayList.length }}</span><span class="stat-label">臨時出勤</span></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Destination Selector -->
    <div class="selector-section">
      <div class="selector-row">
        <div class="selector-group">
          <span class="selector-label">🚚 納入先</span>
          <el-select v-model="filters.destination_cd" filterable placeholder="納入先を選択" class="destination-select" popper-class="destination-select-popper" :loading="optionsLoading" size="small">
            <el-option v-for="item in destinationOptions" :key="item.cd" :label="`${item.cd}｜${item.name}`" :value="item.cd" />
          </el-select>
        </div>
        <el-button type="primary" @click="fetchLists" :disabled="!filters.destination_cd" :loading="loading" class="load-btn" size="small">📥 読み込み</el-button>
      </div>
    </div>

    <!-- Two Column Cards -->
    <div class="cards-grid">
      <!-- Holiday Card -->
      <div class="data-card">
        <div class="card-header holiday-header">
          <div class="card-title">🚫 休日一覧</div>
          <span class="item-count" v-if="holidayList.length">{{ holidayList.length }}件</span>
        </div>
        <div class="card-body">
          <div class="add-row">
            <el-date-picker v-model="newHolidayDates" type="dates" placeholder="休日を選択" value-format="YYYY-MM-DD" :disabled="!filters.destination_cd" class="date-picker" size="small" />
            <el-button v-if="canCreate" type="primary" @click="addHoliday" :disabled="!filters.destination_cd || !newHolidayDates.length" :loading="actionLoading" size="small" class="add-btn">➕ 追加</el-button>
          </div>
          <el-table :data="holidayList" border stripe empty-text="休日なし" class="compact-table" v-loading="loading" :header-cell-style="tableHeaderStyle" :cell-style="tableCellStyle">
            <el-table-column label="日付" align="center" min-width="120">
              <template #default="{ row }"><span class="date-text">{{ formatDate(row.holiday_date) }}</span></template>
            </el-table-column>
            <el-table-column label="曜日" align="center" width="70">
              <template #default="{ row }"><el-tag :type="getWeekdayType(row.holiday_date)" size="small" effect="plain">{{ getWeekday(row.holiday_date) }}</el-tag></template>
            </el-table-column>
            <el-table-column label="" width="60" align="center">
              <template #default="{ row }">
                <el-button v-if="canDelete" type="danger" size="small" link @click="deleteHoliday(row)" :loading="(row as HolidayEx).deleting">🗑️</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- Workday Card -->
      <div class="data-card">
        <div class="card-header workday-header">
          <div class="card-title">☀️ 臨時出勤日一覧</div>
          <span class="item-count" v-if="workdayList.length">{{ workdayList.length }}件</span>
        </div>
        <div class="card-body">
          <div class="add-row">
            <el-date-picker v-model="newWorkdayDate" type="date" placeholder="出勤日" value-format="YYYY-MM-DD" :disabled="!filters.destination_cd" class="date-picker-single" size="small" />
            <el-input v-model="newWorkdayReason" placeholder="理由" :disabled="!filters.destination_cd" class="reason-input" size="small" clearable />
            <el-button v-if="canCreate" type="primary" @click="addWorkday" :disabled="!filters.destination_cd || !newWorkdayDate" :loading="workdayActionLoading" size="small" class="add-btn">➕</el-button>
          </div>
          <el-table :data="workdayList" border stripe empty-text="臨時出勤日なし" class="compact-table" v-loading="workdayLoading" :header-cell-style="tableHeaderStyle" :cell-style="tableCellStyle">
            <el-table-column label="日付" align="center" width="120">
              <template #default="{ row }"><span class="date-text">{{ formatDate(row.work_date) }}</span></template>
            </el-table-column>
            <el-table-column label="曜日" align="center" width="60">
              <template #default="{ row }"><el-tag :type="getWeekdayType(row.work_date)" size="small" effect="plain">{{ getWeekday(row.work_date) }}</el-tag></template>
            </el-table-column>
            <el-table-column label="理由" min-width="100" show-overflow-tooltip>
              <template #default="{ row }"><span>{{ row.reason || '—' }}</span></template>
            </el-table-column>
            <el-table-column label="" width="50" align="center">
              <template #default="{ row }">
                <el-button v-if="canDelete" type="danger" size="small" link @click="deleteWorkday(row)" :loading="(row as WorkdayEx).deleting">🗑️</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getHolidaysByDest, addHolidayDate, deleteHolidayDate, getWorkdaysByDest, addWorkdayDate, deleteWorkdayDate } from '@/api/master/destinationMaster'
import { getDestinationMasterOptions } from '@/api/options'
import type { DestinationHolidayItem, DestinationWorkdayItem, OptionItem } from '@/types/master'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { canCreate, canDelete } = useMasterOperationPermission()

type HolidayEx = DestinationHolidayItem & { deleting?: boolean }
type WorkdayEx = DestinationWorkdayItem & { deleting?: boolean }

const filters = reactive({ destination_cd: '' })
const destinationOptions = ref<OptionItem[]>([])
const optionsLoading = ref(false)
const holidayList = ref<HolidayEx[]>([])
const newHolidayDates = ref<string[]>([])
const loading = ref(false)
const actionLoading = ref(false)
const workdayList = ref<WorkdayEx[]>([])
const newWorkdayDate = ref<string>('')
const newWorkdayReason = ref<string>('')
const workdayLoading = ref(false)
const workdayActionLoading = ref(false)

const tableHeaderStyle = { background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#fff', fontWeight: '600', fontSize: '11px', padding: '5px 8px' }
const tableCellStyle = { padding: '4px 6px', fontSize: '12px' }

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
}

function getWeekday(dateStr: string) { if (!dateStr) return ''; return ['日', '月', '火', '水', '木', '金', '土'][new Date(dateStr).getDay()] }
function getWeekdayType(dateStr: string): 'danger' | 'warning' | 'info' { if (!dateStr) return 'info'; const d = new Date(dateStr).getDay(); return d === 0 ? 'danger' : d === 6 ? 'warning' : 'info' }

async function fetchLists() {
  if (!filters.destination_cd) { ElMessage.warning('納入先を選択'); return }
  loading.value = true; workdayLoading.value = true
  try {
    const [h, w] = await Promise.all([getHolidaysByDest(filters.destination_cd), getWorkdaysByDest(filters.destination_cd)])
    holidayList.value = h.map((x) => ({ ...x, deleting: false })); workdayList.value = w.map((x) => ({ ...x, deleting: false }))
    ElMessage.success('読み込み完了')
  } catch { ElMessage.error('読み込み失敗'); holidayList.value = []; workdayList.value = [] }
  finally { loading.value = false; workdayLoading.value = false }
}

async function addHoliday() {
  if (!guardMasterOperation(canCreate)) return
  if (!filters.destination_cd || !newHolidayDates.value.length) return
  actionLoading.value = true
  try { await Promise.all(newHolidayDates.value.map((d) => addHolidayDate(filters.destination_cd, d))); ElMessage.success('休日追加'); newHolidayDates.value = []; fetchLists() }
  catch { ElMessage.error('追加失敗') } finally { actionLoading.value = false }
}

async function deleteHoliday(row: HolidayEx) {
  if (!guardMasterOperation(canDelete)) return
  if (row.id == null) return; row.deleting = true
  try { await deleteHolidayDate(row.id); ElMessage.success('削除'); fetchLists() } catch { ElMessage.error('削除失敗') } finally { row.deleting = false }
}

async function addWorkday() {
  if (!guardMasterOperation(canCreate)) return
  if (!filters.destination_cd || !newWorkdayDate.value) return
  workdayActionLoading.value = true
  try { await addWorkdayDate(filters.destination_cd, newWorkdayDate.value, newWorkdayReason.value || undefined); ElMessage.success('臨時出勤日追加'); newWorkdayDate.value = ''; newWorkdayReason.value = ''; fetchLists() }
  catch { ElMessage.error('追加失敗') } finally { workdayActionLoading.value = false }
}

async function deleteWorkday(row: WorkdayEx) {
  if (!guardMasterOperation(canDelete)) return
  if (row.id == null) return; row.deleting = true
  try { await deleteWorkdayDate(row.id); ElMessage.success('削除'); fetchLists() } catch { ElMessage.error('削除失敗') } finally { row.deleting = false }
}

onMounted(async () => { optionsLoading.value = true; try { destinationOptions.value = await getDestinationMasterOptions() } catch { destinationOptions.value = [] } finally { optionsLoading.value = false } })
</script>

<style scoped>
.destination-holiday-container { padding: 12px 16px; background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%); min-height: 100vh; }

.page-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 12px 18px; margin-bottom: 12px; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3); }
.header-content { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; }
.title-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.title-icon { font-size: 1.4rem; }
.main-title { font-size: 1.3rem; font-weight: 700; margin: 0; color: #fff; }
.stat-badges { display: flex; gap: 8px; margin-left: 10px; }
.stat-badge { background: rgba(255,255,255,0.2); backdrop-filter: blur(10px); border-radius: 14px; padding: 3px 10px; display: flex; align-items: center; gap: 4px; }
.stat-workday { background: rgba(251, 146, 60, 0.4); }
.stat-number { font-size: 0.95rem; font-weight: 700; color: #fff; }
.stat-label { font-size: 0.7rem; color: rgba(255,255,255,0.9); }

.selector-section { background: #fff; border-radius: 10px; padding: 10px 14px; margin-bottom: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.selector-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.selector-group { display: flex; align-items: center; gap: 8px; flex: 1; }
.selector-label { font-size: 12px; font-weight: 600; color: #374151; white-space: nowrap; }
.destination-select { min-width: 250px; flex: 1; }
.load-btn { border-radius: 8px; font-weight: 600; }

.cards-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.data-card { background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); overflow: hidden; }
.card-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; }
.holiday-header { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
.workday-header { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
.card-title { font-size: 13px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 6px; }
.item-count { font-size: 11px; color: rgba(255,255,255,0.9); background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 10px; }
.card-body { padding: 12px; }

.add-row { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; flex-wrap: wrap; }
.date-picker { min-width: 180px; flex: 1; }
.date-picker-single { width: 130px; }
.reason-input { flex: 1; min-width: 100px; }
.add-btn { border-radius: 6px; font-weight: 600; }

.compact-table { border-radius: 8px; overflow: hidden; }
.date-text { font-weight: 500; font-size: 12px; }

@media (max-width: 900px) {
  .cards-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .destination-holiday-container { padding: 8px; }
  .page-header { padding: 10px 12px; }
  .title-row { justify-content: center; }
  .main-title { font-size: 1.1rem; }
  .selector-row { flex-direction: column; align-items: stretch; }
  .selector-group { width: 100%; }
  .destination-select { width: 100%; min-width: 0; }
  .load-btn { width: 100%; }
  .add-row { flex-direction: column; }
  .date-picker, .date-picker-single, .reason-input { width: 100%; min-width: 0; }
  .add-btn { width: 100%; }
}

:deep(.el-table) { --el-table-border-color: #e2e8f0; }
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) { background-color: #fafbfc; }
:deep(.el-tag) { border-radius: 8px; font-weight: 500; font-size: 10px; }
</style>
