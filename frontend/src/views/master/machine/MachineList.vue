<template>
  <div class="machine-master-container">
    <div class="page-header">
      <div class="header-content">
        <div class="title-row">
          <span class="title-icon">🛠️</span>
          <h1 class="main-title">{{ t('master.machine.title') }}</h1>
          <div class="stat-badges">
            <div class="stat-badge"><span class="stat-number">{{ machineList.length }}</span><span class="stat-label">{{ t('master.common.items') }}</span></div>
            <div class="stat-badge stat-active"><span class="stat-number">{{ activeCount }}</span><span class="stat-label">{{ t('master.machine.statusActive') }}</span></div>
          </div>
        </div>
        <el-button type="primary" @click="openForm()" class="add-btn" size="small">➕ {{ t('master.machine.addMachine') }}</el-button>
      </div>
    </div>

    <div class="search-section">
      <div class="search-row">
        <div class="search-group">
          <el-input v-model="filters.keyword" :placeholder="t('master.machine.searchPlaceholder')" clearable @input="handleFilter" class="search-input" size="small">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>
        <div class="filter-group">
          <el-select v-model="filters.machine_type" :placeholder="t('master.machine.machineType')" clearable @change="handleFilter" size="small" class="filter-select">
            <el-option :label="t('master.machine.typeCutting')" value="切断" />
            <el-option :label="t('master.machine.typeChamfering')" value="面取" />
            <el-option :label="t('master.machine.typeSW')" value="SW" />
            <el-option :label="t('master.machine.typeMolding')" value="成型" />
            <el-option :label="t('master.machine.typeWelding')" value="溶接" />
            <el-option :label="t('master.machine.typePlating')" value="メッキ" />
            <el-option :label="t('master.machine.typeInspection')" value="検査" />
          </el-select>
          <el-select v-model="filters.status" :placeholder="t('master.common.status')" clearable @change="handleFilter" size="small" class="filter-select">
            <el-option :label="t('master.machine.statusActive')" value="active" />
            <el-option :label="t('master.machine.statusMaintenance')" value="maintenance" />
            <el-option :label="t('master.machine.statusInactive')" value="inactive" />
          </el-select>
          <el-button text @click="clearFilters" size="small" class="clear-btn">🔄 {{ t('master.common.clear') }}</el-button>
        </div>
      </div>
    </div>

    <div class="table-section">
      <el-table :data="filteredList" stripe highlight-current-row v-loading="loading" class="modern-table"
        :header-cell-style="{ background: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)', color: '#fff', fontWeight: '600', fontSize: '12px', padding: '6px 10px' }"
        :cell-style="{ padding: '5px 8px', fontSize: '12px' }">
        <el-table-column prop="machine_cd" :label="t('master.machine.machineCD')" width="110" align="center">
          <template #default="{ row }"><span class="code-cell">{{ row.machine_cd }}</span></template>
        </el-table-column>
        <el-table-column prop="machine_name" :label="t('master.machine.machineName')" min-width="140" show-overflow-tooltip>
          <template #default="{ row }"><span class="name-cell">{{ row.machine_name }}</span></template>
        </el-table-column>
        <el-table-column prop="machine_type" :label="t('master.machine.machineType')" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.machine_type" size="small" effect="plain">{{ getMachineTypeLabel(row.machine_type) }}</el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="t('master.common.status')" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small" effect="plain">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.machine.availableTime')" width="120" align="center">
          <template #default="{ row }">{{ formatTimeRange(row.available_from, row.available_to) }}</template>
        </el-table-column>
        <el-table-column prop="efficiency" :label="t('master.machine.efficiency')" width="90" align="center">
          <template #default="{ row }">{{ row.efficiency != null ? row.efficiency : '—' }}</template>
        </el-table-column>
        <el-table-column prop="note" :label="t('master.machine.note')" min-width="120" show-overflow-tooltip />
        <el-table-column :label="t('master.common.actions')" fixed="right" width="110" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" type="primary" plain @click="openForm(row)" class="action-btn">✏️</el-button>
              <el-button size="small" type="danger" plain @click="deleteMachine(row.id)" class="action-btn">🗑️</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="footer-section">
      <div class="result-info"><el-icon><DataAnalysis /></el-icon><span>{{ t('master.common.displayCount', { shown: filteredList.length, total: machineList.length }) }}</span></div>
    </div>

    <MachineForm v-model:visible="formVisible" :data="editData" @refresh="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, DataAnalysis } from '@element-plus/icons-vue'
import MachineForm from './MachineForm.vue'
import { getMachineList, deleteMachineById } from '@/api/master/machineMaster'
import type { MachineItem } from '@/types/master'

const { t } = useI18n()

const machineTypeKeys: Record<string, string> = {
  切断: 'typeCutting',
  面取: 'typeChamfering',
  SW: 'typeSW',
  成型: 'typeMolding',
  溶接: 'typeWelding',
  メッキ: 'typePlating',
  検査: 'typeInspection',
  溶接前検査: 'typePreWeld',
  外注切断: 'typeOutCut',
  外注成型: 'typeOutMold',
  外注メッキ: 'typeOutPlating',
  外注溶接: 'typeOutWeld',
  外注検査: 'typeOutInsp',
}

function getMachineTypeLabel(type: string): string {
  const key = machineTypeKeys[type]
  return key ? t(`master.machine.${key}`) : type
}

const loading = ref(false)
const machineList = ref<MachineItem[]>([])
const filters = ref({ keyword: '', machine_type: '', status: '' })

const handleFilter = () => {}
const clearFilters = () => { filters.value = { keyword: '', machine_type: '', status: '' }; fetchList() }

const activeCount = computed(() => machineList.value.filter((row) => row.status === 'active').length)

function getStatusText(s: string | undefined): string {
  if (!s) return '—'
  if (s === 'active') return t('master.machine.statusActive')
  if (s === 'maintenance') return t('master.machine.statusMaintenance')
  if (s === 'inactive') return t('master.machine.statusInactive')
  return s
}

function getStatusTagType(s: string | undefined): 'success' | 'warning' | 'info' | 'primary' {
  if (s === 'active') return 'success'
  if (s === 'maintenance') return 'warning'
  if (s === 'inactive') return 'info'
  return 'primary'
}

function formatTimeRange(from: string | undefined, to: string | undefined): string {
  const f = from ? String(from).slice(0, 5) : ''
  const t = to ? String(to).slice(0, 5) : ''
  if (!f && !t) return '—'
  return `${f || '—'} 〜 ${t || '—'}`
}

const filteredList = computed(() => {
  let result = machineList.value
  if (filters.value.keyword) {
    const k = filters.value.keyword.toLowerCase()
    result = result.filter((row) =>
      row.machine_cd?.toLowerCase().includes(k) || row.machine_name?.toLowerCase().includes(k)
    )
  }
  if (filters.value.machine_type) result = result.filter((row) => row.machine_type === filters.value.machine_type)
  if (filters.value.status) result = result.filter((row) => row.status === filters.value.status)
  return result
})

const formVisible = ref(false)
const editData = ref<MachineItem | null>(null)
function openForm(row: MachineItem | null = null) { editData.value = row; formVisible.value = true }

async function deleteMachine(id: number | undefined) {
  if (id == null) return
  try {
    await ElMessageBox.confirm(t('master.machine.confirmDelete'), t('common.confirm'), { type: 'warning' })
    await deleteMachineById(id)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch {}
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getMachineList({
      keyword: filters.value.keyword || undefined,
      machine_type: filters.value.machine_type || undefined,
      status: filters.value.status || undefined,
      page: 1,
      pageSize: 5000,
    })
    machineList.value = res.list ?? res.data?.list ?? []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.machine-master-container { padding: 12px 16px; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); min-height: 100vh; }

.page-header { background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%); border-radius: 12px; padding: 12px 18px; margin-bottom: 12px; box-shadow: 0 4px 20px rgba(14, 165, 233, 0.3); }
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
.filter-select { width: 110px; }
.clear-btn { color: #64748b; }

.table-section { background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); overflow: hidden; margin-bottom: 12px; }
.modern-table { width: 100%; }
.code-cell { font-family: 'Consolas', monospace; font-weight: 600; color: #0ea5e9; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 2px 6px; border-radius: 4px; font-size: 11px; }
.name-cell { font-weight: 500; color: #1e293b; }
.action-buttons { display: flex; gap: 4px; justify-content: center; }
.action-btn { padding: 3px 8px; font-size: 11px; border-radius: 6px; min-width: 32px; }

.footer-section { background: #fff; border-radius: 10px; padding: 8px 16px; display: flex; align-items: center; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.result-info { display: flex; align-items: center; gap: 6px; color: #64748b; font-size: 0.85rem; }
.result-info strong { color: #0ea5e9; font-weight: 700; }

@media (max-width: 768px) {
  .machine-master-container { padding: 8px; }
  .page-header { padding: 10px 12px; }
  .header-content { flex-direction: column; align-items: stretch; gap: 10px; }
  .title-row { flex-wrap: wrap; justify-content: center; }
  .add-btn { width: 100%; }
  .search-row { flex-direction: column; }
  .search-group { width: 100%; }
  .filter-group { width: 100%; justify-content: center; }
  .main-title { font-size: 1.1rem; }
}

:deep(.el-table) { --el-table-border-color: #e2e8f0; --el-table-row-hover-bg-color: #f0f9ff; }
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) { background-color: #fafbfc; }
:deep(.el-tag) { border-radius: 10px; font-weight: 500; }
</style>
