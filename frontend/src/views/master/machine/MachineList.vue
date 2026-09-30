<template>
  <div class="machine-master-container mch-modern">
    <div class="page-header">
      <div class="page-header-fx" aria-hidden="true">
        <span class="fx-orb orb-a" />
        <span class="fx-orb orb-b" />
        <span class="fx-grid" />
        <span class="fx-sheen" />
      </div>
      <div class="header-content">
        <div class="title-row">
          <span class="title-icon">🛠️</span>
          <h1 class="main-title">{{ t('master.machine.title') }}</h1>
          <div class="stat-badges" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
            <div class="stat-badge">
              <span class="stat-number">{{ machineList.length }}</span>
              <span class="stat-label">{{ t('master.common.items') }}</span>
            </div>
            <div class="stat-badge stat-active">
              <span class="stat-number">{{ activeCount }}</span>
              <span class="stat-label">{{ t('master.machine.statusActive') }}</span>
            </div>
            <div class="stat-badge stat-maint">
              <span class="stat-number">{{ maintenanceCount }}</span>
              <span class="stat-label">{{ t('master.machine.statusMaintenance') }}</span>
            </div>
          </div>
        </div>
        <el-button v-if="canCreate" type="primary" @click="openForm()" class="add-btn" size="small">
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
            <el-tag
              v-if="row.machine_type"
              size="small"
              effect="plain"
              :class="['mtype-tag', `mtype--${getMachineTypeTone(row.machine_type)}`]"
            >
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
            <span class="time-range">{{ formatTimeRange(row.available_from, row.available_to) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="efficiency"
          :label="t('master.machine.efficiency')"
          width="110"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.efficiency != null" class="num-pill">{{ row.efficiency }}</span>
            <span v-else class="muted-cell">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="available_qty" label="使用可能数" width="110" align="center">
          <template #default="{ row }">
            {{ row.available_qty != null ? row.available_qty : '—' }}
          </template>
        </el-table-column>
        <el-table-column label="CP-SAT" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.use_in_cpsat === false ? 'info' : 'success'" size="small" effect="plain">
              {{ row.use_in_cpsat === false ? '除外' : '参加' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="note"
          :label="t('master.machine.note')"
          width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="canEdit || canDelete"
          :label="t('master.common.actions')"
          fixed="right"
          width="110"
          align="center"
        >
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                v-if="canEdit"
                size="small"
                type="primary"
                plain
                @click="openForm(row)"
                class="action-btn"
              >
                ✏️
              </el-button>
              <el-button
                v-if="canDelete"
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
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { t } = useI18n()
const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

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

// 設備種類タグの色分けキー（外注系は一括）
function getMachineTypeTone(type: string): string {
  if (type.startsWith('外注')) return 'out'
  const toneMap: Record<string, string> = {
    切断: 'cut',
    面取: 'chamfer',
    SW: 'sw',
    成型: 'mold',
    溶接: 'weld',
    メッキ: 'plating',
    検査: 'insp',
    溶接前検査: 'insp',
  }
  return toneMap[type] ?? 'other'
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
const maintenanceCount = computed(
  () => machineList.value.filter((row) => row.status === 'maintenance').length,
)

// ヘッダー統計バッジの3Dチルト（マウス追従）
function handleStatTilt(e: MouseEvent) {
  const item = (e.target as HTMLElement | null)?.closest<HTMLElement>('.stat-badge')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.stat-badge').forEach((el) => {
    if (el !== item) {
      el.style.removeProperty('--rx')
      el.style.removeProperty('--ry')
    }
  })
  if (!item) return
  const rect = item.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  item.style.setProperty('--rx', `${((0.5 - py) * 18).toFixed(2)}deg`)
  item.style.setProperty('--ry', `${((px - 0.5) * 18).toFixed(2)}deg`)
  item.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
  item.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
}

function resetStatTilt(e: MouseEvent) {
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.stat-badge').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

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
  if (row ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  editData.value = row
  formVisible.value = true
}

async function deleteMachine(id: number | undefined) {
  if (!guardMasterOperation(canDelete)) return
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

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（設備マスタ / graphite×amber）
 * ============================================================ */
.machine-master-container.mch-modern {
  background:
    radial-gradient(1000px 360px at 0% 0%, rgba(63, 63, 70, 0.08), transparent 60%),
    radial-gradient(900px 360px at 100% 0%, rgba(245, 158, 11, 0.08), transparent 60%),
    #f4f4f5;
}

/* ---------- ヒーローヘッダー ---------- */
.mch-modern .page-header {
  position: relative;
  overflow: hidden;
  border: none;
  border-radius: 16px;
  background: linear-gradient(125deg, #18181b 0%, #27272a 34%, #3f3f46 68%, #52525b 100%);
  box-shadow:
    0 18px 36px -18px rgba(24, 24, 27, 0.75),
    0 4px 12px -6px rgba(245, 158, 11, 0.3),
    inset 0 0 0 1px rgba(255, 255, 255, 0.1);
}

.mch-modern .page-header::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 4px;
  z-index: 1;
  background: repeating-linear-gradient(
    -45deg,
    #f59e0b 0 10px,
    #18181b 10px 20px
  );
  opacity: 0.85;
}

.mch-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.mch-modern .header-content {
  position: relative;
  z-index: 2;
}

.mch-modern .page-header-fx .fx-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(24px);
  opacity: 0.45;
  animation: mchOrbFloat 11s ease-in-out infinite;
}

.mch-modern .page-header-fx .orb-a {
  width: 240px;
  height: 240px;
  top: -140px;
  right: 28%;
  background: radial-gradient(circle, #fbbf24 0%, transparent 70%);
}

.mch-modern .page-header-fx .orb-b {
  width: 190px;
  height: 190px;
  bottom: -120px;
  left: 20%;
  background: radial-gradient(circle, #a1a1aa 0%, transparent 70%);
  animation-delay: -5s;
}

.mch-modern .page-header-fx .fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.07) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: radial-gradient(ellipse at 14% 50%, #000 0%, transparent 70%);
}

.mch-modern .page-header-fx .fx-sheen {
  position: absolute;
  top: 0;
  bottom: 0;
  left: -40%;
  width: 35%;
  background: linear-gradient(100deg, transparent 0%, rgba(255, 255, 255, 0.12) 50%, transparent 100%);
  animation: mchSheen 7s ease-in-out infinite;
}

.mch-modern .title-row {
  gap: 12px;
}

.mch-modern .title-icon {
  width: 40px;
  height: 40px;
  font-size: 20px;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(251, 191, 36, 0.4) 0%, rgba(255, 255, 255, 0.06) 100%);
  border: 1px solid rgba(251, 191, 36, 0.45);
  box-shadow:
    0 4px 0 #000,
    0 10px 20px -8px rgba(245, 158, 11, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
  animation: mchIconWork 4s ease-in-out infinite;
}

.mch-modern .main-title {
  font-size: 20px;
  font-weight: 800;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.45);
}

/* 統計バッジ：3Dチルト＋グレア */
.mch-modern .stat-badges {
  perspective: 600px;
}

.mch-modern .stat-badge {
  position: relative;
  overflow: hidden;
  padding: 4px 12px;
  box-shadow:
    0 3px 0 rgba(0, 0, 0, 0.55),
    0 10px 18px -10px rgba(0, 0, 0, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transition:
    transform 0.18s ease-out,
    box-shadow 0.25s ease;
}

.mch-modern .stat-badge::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.25s ease;
  background: radial-gradient(
    circle at var(--mx, 50%) var(--my, 50%),
    rgba(255, 255, 255, 0.32) 0%,
    transparent 65%
  );
}

.mch-modern .stat-badge:hover::after {
  opacity: 1;
}

.mch-modern .stat-number {
  font-size: 1.05rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.mch-modern .stat-active {
  background: rgba(16, 185, 129, 0.3);
  border-color: rgba(52, 211, 153, 0.45);
}

.mch-modern .stat-maint {
  background: rgba(245, 158, 11, 0.3);
  border-color: rgba(251, 191, 36, 0.5);
}

/* 追加ボタン：3Dキーキャップ（アンバー） */
.mch-modern .add-btn,
.mch-modern .add-btn:hover,
.mch-modern .add-btn:focus {
  color: #1c1917;
  font-weight: 800;
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: linear-gradient(135deg, #fde68a 0%, #fbbf24 45%, #d97706 100%);
}

.mch-modern .add-btn {
  box-shadow:
    0 3px 0 #78350f,
    0 10px 18px -8px rgba(245, 158, 11, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    filter 0.18s ease;
}

.mch-modern .add-btn:hover {
  filter: brightness(1.05);
  transform: translateY(-2px);
  box-shadow:
    0 5px 0 #78350f,
    0 14px 22px -8px rgba(245, 158, 11, 0.65),
    inset 0 1px 0 rgba(255, 255, 255, 0.55);
}

.mch-modern .add-btn:active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 #78350f,
    0 4px 8px -4px rgba(245, 158, 11, 0.5);
}

/* ---------- 検索バー ---------- */
.mch-modern .search-section,
.mch-modern .table-section,
.mch-modern .footer-section {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid #d4d4d8;
  box-shadow:
    0 14px 28px -22px rgba(24, 24, 27, 0.5),
    0 1px 3px rgba(15, 23, 42, 0.05);
}

.mch-modern .search-section::before,
.mch-modern .table-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 5;
  pointer-events: none;
  background: linear-gradient(90deg, #3f3f46 0%, #71717a 45%, #f59e0b 100%);
}

.mch-modern .search-section {
  padding-top: 11px;
  background: linear-gradient(110deg, #fafaf9 0%, #ffffff 60%);
}

.mch-modern :deep(.el-input__wrapper),
.mch-modern :deep(.el-select__wrapper) {
  box-shadow: 0 0 0 1px #e4e4e7 inset;
}

.mch-modern .search-row :deep(.el-input__wrapper.is-focus),
.mch-modern .search-row :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px #f59e0b inset,
    0 0 0 3px rgba(245, 158, 11, 0.18);
}

.mch-modern .clear-btn {
  font-weight: 600;
  border-radius: 8px;
  background: #fafafa;
  box-shadow: inset 0 0 0 1px #e4e4e7;
}

.mch-modern .clear-btn:hover {
  color: #b45309;
  background: #fffbeb;
  box-shadow: inset 0 0 0 1px #fde68a;
}

/* ---------- テーブル ---------- */
.mch-modern .modern-table :deep(.el-table__header-wrapper th.el-table__cell) {
  color: #27272a !important;
  font-weight: 700 !important;
  background: linear-gradient(180deg, #fafafa 0%, #e4e4e7 100%) !important;
  border-bottom: 2px solid #f59e0b !important;
  box-shadow: none;
}

.mch-modern .modern-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child),
.mch-modern .modern-table :deep(.el-table__body tr.current-row > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 #f59e0b;
}

.mch-modern .code-cell {
  display: inline-block;
  padding: 1px 8px;
  font-size: 11.5px;
  font-weight: 700;
  color: #27272a;
  border-radius: 6px;
  background: linear-gradient(180deg, #ffffff 0%, #e4e4e7 100%);
  box-shadow:
    inset 0 0 0 1px #d4d4d8,
    0 2px 0 #a1a1aa;
  transition: transform 0.15s ease;
}

.mch-modern .modern-table :deep(.el-table__body tr:hover) .code-cell {
  transform: translateY(-1px);
}

/* 設備種類タグ：工程ごとの色分け */
.mch-modern .mtype-tag {
  --mt: #64748b;
  color: var(--mt);
  font-weight: 700;
  border-color: color-mix(in srgb, var(--mt) 35%, #fff);
  background: color-mix(in srgb, var(--mt) 9%, #fff);
}

.mch-modern .mtype--cut {
  --mt: #2563eb;
}

.mch-modern .mtype--chamfer {
  --mt: #0891b2;
}

.mch-modern .mtype--sw {
  --mt: #7c3aed;
}

.mch-modern .mtype--mold {
  --mt: #0284c7;
}

.mch-modern .mtype--weld {
  --mt: #c026d3;
}

.mch-modern .mtype--plating {
  --mt: #ca8a04;
}

.mch-modern .mtype--insp {
  --mt: #ea580c;
}

.mch-modern .mtype--out {
  --mt: #52525b;
  border-style: dashed;
}

.mch-modern .time-range {
  display: inline-block;
  padding: 1px 8px;
  color: #3f3f46;
  font-size: 11.5px;
  font-variant-numeric: tabular-nums;
  border-radius: 6px;
  background: #f4f4f5;
  box-shadow: inset 0 0 0 1px #e4e4e7;
}

.mch-modern .num-pill {
  display: inline-block;
  min-width: 36px;
  padding: 1px 8px;
  color: #92400e;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  border-radius: 999px;
  background: #fffbeb;
  box-shadow: inset 0 0 0 1px #fde68a;
}

.mch-modern .muted-cell {
  color: #d4d4d8;
}

.mch-modern .action-btn {
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}

.mch-modern .action-btn.el-button--primary {
  box-shadow: 0 2px 0 #bfdbfe;
}

.mch-modern .action-btn.el-button--danger {
  box-shadow: 0 2px 0 #fecaca;
}

.mch-modern .action-btn:hover {
  transform: translateY(-1px);
}

.mch-modern .action-btn.el-button--primary:hover {
  box-shadow:
    0 3px 0 #1e40af,
    0 8px 14px -8px rgba(37, 99, 235, 0.6);
}

.mch-modern .action-btn.el-button--danger:hover {
  box-shadow:
    0 3px 0 #991b1b,
    0 8px 14px -8px rgba(220, 38, 38, 0.6);
}

.mch-modern .action-btn:active {
  transform: translateY(1px);
  box-shadow: none;
}

/* ---------- フッター ---------- */
.mch-modern .footer-section {
  background: linear-gradient(180deg, #ffffff 0%, #fafaf9 100%);
}

.mch-modern .result-info {
  padding: 2px 10px;
  color: #27272a;
  font-weight: 700;
  border-radius: 999px;
  background: #f4f4f5;
  box-shadow: inset 0 0 0 1px #e4e4e7;
}

.mch-modern .result-info .el-icon {
  color: #d97706;
}

/* ---------- キーフレーム ---------- */
@keyframes mchOrbFloat {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(-18px, 10px, 0) scale(1.08);
  }
}

@keyframes mchSheen {
  0%,
  60% {
    left: -40%;
  }
  100% {
    left: 130%;
  }
}

@keyframes mchIconWork {
  0%,
  100% {
    transform: perspective(300px) rotateX(0deg) rotateZ(0deg);
  }
  30% {
    transform: perspective(300px) rotateX(8deg) rotateZ(-12deg);
  }
  60% {
    transform: perspective(300px) rotateX(0deg) rotateZ(8deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .mch-modern .page-header-fx .fx-orb,
  .mch-modern .page-header-fx .fx-sheen,
  .mch-modern .title-icon {
    animation: none;
  }

  .mch-modern .stat-badge {
    transform: none;
    transition: none;
  }
}
</style>
