<template>
  <div class="machine-master-container">
    <div class="page-header">
      <div class="header-content">
        <div class="title-row">
          <span class="title-icon">🛠️</span>
          <h1 class="main-title">{{ t('master.machine.title') }}</h1>
          <div class="stat-badges">
            <div class="stat-badge">
              <span class="stat-number">{{ machineList.length }}</span>
              <span class="stat-label">{{ t('master.common.items') }}</span>
            </div>
            <div class="stat-badge stat-active">
              <span class="stat-number">{{ activeCount }}</span>
              <span class="stat-label">{{ t('master.machine.statusActive') }}</span>
            </div>
          </div>
        </div>
        <el-button type="primary" @click="openForm()" class="add-btn" size="small">
          ➕ {{ t('master.machine.addMachine') }}
        </el-button>
      </div>
    </div>

    <div class="search-section">
      <div class="search-row">
        <div class="search-group">
          <el-input
            v-model="filters.keyword"
            :placeholder="t('master.machine.searchPlaceholder')"
            clearable
            @input="handleFilter"
            class="search-input"
            size="small"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-group">
          <el-select
            v-model="filters.machine_type"
            :placeholder="t('master.machine.machineType')"
            clearable
            @change="handleFilter"
            size="small"
            class="filter-select"
          >
            <el-option :label="t('master.machine.typeCutting')" value="切断" />
            <el-option :label="t('master.machine.typeChamfering')" value="面取" />
            <el-option :label="t('master.machine.typeSW')" value="SW" />
            <el-option :label="t('master.machine.typeMolding')" value="成型" />
            <el-option :label="t('master.machine.typeWelding')" value="溶接" />
            <el-option :label="t('master.machine.typePlating')" value="メッキ" />
            <el-option :label="t('master.machine.typeInspection')" value="検査" />
          </el-select>
          <el-select
            v-model="filters.status"
            :placeholder="t('master.common.status')"
            clearable
            @change="handleFilter"
            size="small"
            class="filter-select"
          >
            <el-option :label="t('master.machine.statusActive')" value="active" />
            <el-option :label="t('master.machine.statusMaintenance')" value="maintenance" />
            <el-option :label="t('master.machine.statusInactive')" value="inactive" />
          </el-select>
          <el-button text @click="clearFilters" size="small" class="clear-btn">
            🔄 {{ t('master.common.clear') }}
          </el-button>
        </div>
      </div>
    </div>

    <div class="table-section">
      <el-table
        :data="filteredList"
        stripe
        highlight-current-row
        v-loading="loading"
        class="modern-table"
        :header-cell-style="{
          background: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
          color: '#fff',
          fontWeight: '600',
          fontSize: '12px',
          padding: '6px 10px',
        }"
        :cell-style="{ padding: '5px 8px', fontSize: '12px' }"
      >
        <el-table-column
          prop="machine_cd"
          :label="t('master.machine.machineCD')"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span class="code-cell">{{ row.machine_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="machine_name"
          :label="t('master.machine.machineName')"
          width="140"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <span class="name-cell">{{ row.machine_name }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="machine_type"
          :label="t('master.machine.machineType')"
          width="110"
          align="center"
        >
          <template #default="{ row }">
            <el-tag v-if="row.machine_type" size="small" effect="plain">
              {{ getMachineTypeLabel(row.machine_type) }}
            </el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="t('master.common.status')" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small" effect="plain">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.machine.availableTime')" width="120" align="center">
          <template #default="{ row }">
            {{ formatTimeRange(row.available_from, row.available_to) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="efficiency"
          :label="t('master.machine.efficiency')"
          width="110"
          align="center"
        >
          <template #default="{ row }">
            {{ row.efficiency != null ? row.efficiency : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="available_qty" label="使用可能数" width="110" align="center">
          <template #default="{ row }">
            {{ row.available_qty != null ? row.available_qty : '—' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="note"
          :label="t('master.machine.note')"
          width="140"
          show-overflow-tooltip
        />
        <el-table-column
          :label="t('master.common.actions')"
          fixed="right"
          width="110"
          align="center"
        >
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                size="small"
                type="primary"
                plain
                @click="openForm(row)"
                class="action-btn"
              >
                ✏️
              </el-button>
              <el-button
                size="small"
                type="danger"
                plain
                @click="deleteMachine(row.id)"
                class="action-btn"
              >
                🗑️
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="footer-section">
      <div class="result-info">
        <el-icon><DataAnalysis /></el-icon>
        <span>
          {{
            t('master.common.displayCount', {
              shown: filteredList.length,
              total: machineList.length,
            })
          }}
        </span>
      </div>
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
const clearFilters = () => {
  filters.value = { keyword: '', machine_type: '', status: '' }
  fetchList()
}

const activeCount = computed(
  () => machineList.value.filter((row) => row.status === 'active').length,
)

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
    result = result.filter(
      (row) =>
        row.machine_cd?.toLowerCase().includes(k) || row.machine_name?.toLowerCase().includes(k),
    )
  }
  if (filters.value.machine_type)
    result = result.filter((row) => row.machine_type === filters.value.machine_type)
  if (filters.value.status) result = result.filter((row) => row.status === filters.value.status)
  return result
})

const formVisible = ref(false)
const editData = ref<MachineItem | null>(null)
function openForm(row: MachineItem | null = null) {
  editData.value = row
  formVisible.value = true
}

async function deleteMachine(id: number | undefined) {
  if (id == null) return
  try {
    await ElMessageBox.confirm(t('master.machine.confirmDelete'), t('common.confirm'), {
      type: 'warning',
    })
    await deleteMachineById(id)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch {
    void 0
  }
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
.machine-master-container {
  padding: 10px 12px;
  background: linear-gradient(145deg, #f7fbff 0%, #eef7ff 50%, #f4fbff 100%);
  min-height: calc(100vh - 8px);
}

.page-header {
  background: linear-gradient(135deg, #0284c7 0%, #06b6d4 55%, #22d3ee 100%);
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 10px;
  box-shadow: 0 10px 24px rgba(14, 165, 233, 0.24);
  border: 1px solid rgba(255, 255, 255, 0.36);
}
.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}
.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-icon {
  font-size: 1.2rem;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
}
.main-title {
  font-size: 1.12rem;
  font-weight: 700;
  margin: 0;
  color: #fff;
  letter-spacing: 0.2px;
}
.stat-badges {
  display: flex;
  gap: 6px;
  margin-left: 8px;
}
.stat-badge {
  background: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(10px);
  border-radius: 999px;
  padding: 2px 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  border: 1px solid rgba(255, 255, 255, 0.24);
}
.stat-active {
  background: rgba(16, 185, 129, 0.24);
}
.stat-number {
  font-size: 0.82rem;
  font-weight: 700;
  color: #fff;
}
.stat-label {
  font-size: 0.66rem;
  color: rgba(255, 255, 255, 0.9);
}
.add-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.36);
  border-radius: 8px;
  font-weight: 600;
  color: #fff;
  padding: 6px 10px;
}
.add-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.search-section {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  padding: 8px 10px;
  margin-bottom: 10px;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
  border: 1px solid #dbeafe;
}
.search-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.search-group {
  flex: 1;
  min-width: 180px;
}
.search-input {
  width: 100%;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.filter-select {
  width: 105px;
}
.clear-btn {
  color: #475569;
  padding: 4px 6px;
}

.table-section {
  background: rgba(255, 255, 255, 0.94);
  border-radius: 10px;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.08);
  overflow: hidden;
  margin-bottom: 10px;
  border: 1px solid #dbeafe;
}
.modern-table {
  width: 100%;
}
.code-cell {
  font-family: 'Consolas', monospace;
  font-weight: 600;
  color: #0ea5e9;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}
.name-cell {
  font-weight: 500;
  color: #1e293b;
}
.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
}
.action-btn {
  padding: 2px 7px;
  font-size: 11px;
  border-radius: 6px;
  min-width: 30px;
}

.footer-section {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  padding: 6px 12px;
  display: flex;
  align-items: center;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
  border: 1px solid #dbeafe;
}
.result-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #475569;
  font-size: 0.8rem;
}
.result-info strong {
  color: #0ea5e9;
  font-weight: 700;
}

@media (max-width: 768px) {
  .machine-master-container {
    padding: 6px;
  }
  .page-header {
    padding: 9px 10px;
  }
  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  .title-row {
    flex-wrap: wrap;
    justify-content: center;
  }
  .add-btn {
    width: 100%;
  }
  .search-row {
    flex-direction: column;
  }
  .search-group {
    width: 100%;
  }
  .filter-group {
    width: 100%;
    justify-content: center;
  }
  .main-title {
    font-size: 1rem;
  }
}

:deep(.el-table) {
  --el-table-border-color: #dbeafe;
  --el-table-row-hover-bg-color: #eff6ff;
  --el-table-header-text-color: #ffffff;
  --el-table-text-color: #334155;
}
:deep(.el-table th.el-table__cell) {
  box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.25);
}
:deep(.el-table td.el-table__cell) {
  border-bottom-color: #eaf2ff;
}
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f8fbff;
}
:deep(.el-tag) {
  border-radius: 10px;
  font-weight: 500;
}
:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #dbeafe inset;
}
:deep(.el-button--small) {
  min-height: 26px;
}
</style>
