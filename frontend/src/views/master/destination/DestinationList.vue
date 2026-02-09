<template>
  <div class="destination-master-container">
    <div class="page-header">
      <div class="header-content">
        <div class="title-row">
          <span class="title-icon">🚚</span>
          <h1 class="main-title">{{ t('master.destination.title') }}</h1>
          <div class="stat-badges">
            <div class="stat-badge"><span class="stat-number">{{ destinationList.length }}</span><span class="stat-label">{{ t('master.common.items') }}</span></div>
            <div class="stat-badge stat-active"><span class="stat-number">{{ activeCount }}</span><span class="stat-label">{{ t('master.common.active') }}</span></div>
          </div>
        </div>
        <el-button type="primary" @click="openForm()" class="add-btn" size="small">➕ {{ t('master.destination.addDestination') }}</el-button>
      </div>
    </div>

    <div class="search-section">
      <div class="search-row">
        <div class="search-group">
          <el-input v-model="filters.keyword" :placeholder="t('master.destination.searchPlaceholder')" clearable @input="handleFilter" class="search-input" size="small">
            <template #prefix><el-icon>🔍</el-icon></template>
          </el-input>
        </div>
        <div class="filter-group">
          <el-select v-model="filters.status" :placeholder="t('master.common.status')" clearable @change="handleFilter" size="small" class="filter-select">
            <el-option :label="t('master.common.active')" :value="1" /><el-option :label="t('master.common.inactive')" :value="0" />
          </el-select>
          <el-select v-model="filters.issue_type" :placeholder="t('master.destination.issueType')" clearable @change="handleFilter" size="small" class="filter-select">
            <el-option :label="t('master.destination.issueAuto')" value="自動" /><el-option label="1" value="1" /><el-option label="2" value="2" /><el-option label="3" value="3" /><el-option label="4" value="4" />
          </el-select>
          <el-input v-model="filters.carrier_cd" :placeholder="t('master.destination.carrierCD')" clearable @input="handleFilter" size="small" class="filter-input-sm" />
          <el-button text @click="clearFilters" size="small" class="clear-btn">🔄 {{ t('master.common.clear') }}</el-button>
        </div>
      </div>
    </div>

    <div class="table-section">
      <el-table :data="filteredList" stripe highlight-current-row v-loading="loading" class="modern-table"
        :header-cell-style="{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#fff', fontWeight: '600', fontSize: '12px', padding: '6px 10px' }"
        :cell-style="{ padding: '5px 8px', fontSize: '12px' }">
        <el-table-column prop="destination_cd" :label="t('master.destination.destinationCD')" width="100" align="center">
          <template #default="{ row }"><span class="code-cell">{{ row.destination_cd }}</span></template>
        </el-table-column>
        <el-table-column prop="destination_name" :label="t('master.destination.destinationName')" min-width="130" show-overflow-tooltip>
          <template #default="{ row }"><span class="name-cell">{{ row.destination_name }}</span></template>
        </el-table-column>
        <el-table-column prop="customer_cd" :label="t('master.destination.customerCD')" width="90" align="center" />
        <el-table-column prop="carrier_cd" :label="t('master.destination.carrierCD')" width="90" align="center" />
        <el-table-column prop="delivery_lead_time" :label="t('master.destination.deliveryLeadTime')" width="65" align="center">
          <template #default="{ row }"><span class="number-cell">{{ row.delivery_lead_time }}</span></template>
        </el-table-column>
        <el-table-column prop="issue_type" :label="t('master.destination.issueType')" width="65" align="center">
          <template #default="{ row }">
            <el-tag :type="row.issue_type === '自動' ? 'info' : 'warning'" size="small" effect="plain">{{ row.issue_type || '—' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="t('master.common.status')" width="80" align="center">
          <template #default="{ row }">
            <el-switch :model-value="row.status === 1" @update:model-value="(v: string | number | boolean) => toggleStatus(row, v === true)"
              :loading="row.statusLoading" :active-text="t('master.common.active')" :inactive-text="t('master.common.inactive')" size="small" />
          </template>
        </el-table-column>
        <el-table-column :label="t('master.common.actions')" fixed="right" width="110" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" type="primary" plain @click="openForm(row)" class="action-btn">✏️</el-button>
              <el-button size="small" type="danger" plain @click="deleteDestination(row.id)" class="action-btn">🗑️</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="footer-section">
      <div class="result-info"><el-icon>📊</el-icon><span>{{ t('master.common.displayCount', { shown: filteredList.length, total: destinationList.length }) }}</span></div>
    </div>

    <DestinationForm v-model:visible="formVisible" :data="editData" @refresh="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import DestinationForm from './DestinationForm.vue'
import { getDestinationList, deleteDestinationById, updateDestinationStatus } from '@/api/master/destinationMaster'
import type { DestinationItem } from '@/types/master'

const { t } = useI18n()

type RowEx = DestinationItem & { statusLoading?: boolean }

const loading = ref(false)
const destinationList = ref<RowEx[]>([])
const filters = ref({ keyword: '', status: '' as '' | number, issue_type: '', carrier_cd: '' })

const handleFilter = () => {}
const clearFilters = () => { filters.value = { keyword: '', status: '', issue_type: '', carrier_cd: '' }; fetchList() }

const activeCount = computed(() => destinationList.value.filter((row) => row.status === 1).length)

const filteredList = computed(() => {
  let result = destinationList.value
  if (filters.value.keyword) {
    const k = filters.value.keyword.toLowerCase()
    result = result.filter((row) => row.destination_cd?.toLowerCase().includes(k) || row.destination_name?.toLowerCase().includes(k) || row.customer_cd?.toLowerCase().includes(k))
  }
  if (filters.value.status !== '') result = result.filter((row) => row.status === filters.value.status)
  if (filters.value.issue_type) result = result.filter((row) => row.issue_type === filters.value.issue_type)
  if (filters.value.carrier_cd) result = result.filter((row) => row.carrier_cd?.toLowerCase().includes(filters.value.carrier_cd.toLowerCase()))
  return result
})

const formVisible = ref(false)
const editData = ref<RowEx | null>(null)
function openForm(row: RowEx | null = null) { editData.value = row; formVisible.value = true }

async function deleteDestination(id: number | undefined) {
  if (id == null) return
  try {
    await ElMessageBox.confirm(t('master.destination.confirmDelete'), t('common.confirm'), { type: 'warning' })
    await deleteDestinationById(id)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch {}
}

async function toggleStatus(row: RowEx, on: boolean) {
  const next = on ? 1 : 0
  row.statusLoading = true
  try {
    await updateDestinationStatus(row.id!, next)
    row.status = next
    ElMessage.success(t('master.common.updateSuccess'))
  } catch {
    ElMessage.error(t('master.common.saveFailed'))
  } finally {
    row.statusLoading = false
  }
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getDestinationList({ keyword: filters.value.keyword || undefined, status: filters.value.status !== '' ? filters.value.status : undefined, issue_type: filters.value.issue_type || undefined, carrier_cd: filters.value.carrier_cd || undefined, page: 1, pageSize: 5000 })
    destinationList.value = (res.list ?? res.data?.list ?? []).map((row) => ({ ...row, statusLoading: false }))
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(fetchList)
</script>

<style scoped>
.destination-master-container { padding: 12px 16px; background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%); min-height: 100vh; }

.page-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 12px 18px; margin-bottom: 12px; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3); }
.header-content { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
.title-row { display: flex; align-items: center; gap: 10px; }
.title-icon { font-size: 1.4rem; }
.main-title { font-size: 1.3rem; font-weight: 700; margin: 0; color: #fff; }
.stat-badges { display: flex; gap: 8px; margin-left: 10px; }
.stat-badge { background: rgba(255,255,255,0.2); backdrop-filter: blur(10px); border-radius: 14px; padding: 3px 10px; display: flex; align-items: center; gap: 4px; }
.stat-active { background: rgba(16, 185, 129, 0.3); }
.stat-number { font-size: 0.95rem; font-weight: 700; color: #fff; }
.stat-label { font-size: 0.7rem; color: rgba(255,255,255,0.9); }
.add-btn { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; font-weight: 600; color: #fff; }
.add-btn:hover { background: rgba(255,255,255,0.25); }

.search-section { background: #fff; border-radius: 10px; padding: 10px 14px; margin-bottom: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.search-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.search-group { flex: 1; min-width: 200px; }
.search-input { width: 100%; }
.filter-group { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.filter-select { width: 100px; }
.filter-input-sm { width: 120px; }
.clear-btn { color: #64748b; }

.table-section { background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); overflow: hidden; margin-bottom: 12px; }
.modern-table { width: 100%; }
.code-cell { font-family: 'Consolas', monospace; font-weight: 600; color: #667eea; background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%); padding: 2px 6px; border-radius: 4px; font-size: 11px; }
.name-cell { font-weight: 500; color: #1e293b; }
.number-cell { font-family: 'Consolas', monospace; font-weight: 500; color: #374151; }
.action-buttons { display: flex; gap: 4px; justify-content: center; }
.action-btn { padding: 3px 8px; font-size: 11px; border-radius: 6px; min-width: 32px; }

.footer-section { background: #fff; border-radius: 10px; padding: 8px 16px; display: flex; align-items: center; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.result-info { display: flex; align-items: center; gap: 6px; color: #64748b; font-size: 0.85rem; }
.result-info strong { color: #667eea; font-weight: 700; }

@media (max-width: 768px) {
  .destination-master-container { padding: 8px; }
  .page-header { padding: 10px 12px; }
  .header-content { flex-direction: column; align-items: stretch; gap: 10px; }
  .title-row { flex-wrap: wrap; justify-content: center; }
  .add-btn { width: 100%; }
  .search-row { flex-direction: column; }
  .search-group { width: 100%; }
  .filter-group { width: 100%; justify-content: center; }
  .filter-select { flex: 1; min-width: 80px; }
  .filter-input-sm { flex: 1; }
  .main-title { font-size: 1.1rem; }
}

:deep(.el-table) { --el-table-border-color: #e2e8f0; --el-table-row-hover-bg-color: #f0f4ff; }
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) { background-color: #fafbfc; }
:deep(.el-tag) { border-radius: 10px; font-weight: 500; }
</style>
