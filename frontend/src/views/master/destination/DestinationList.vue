<template>
  <div class="destination-master-container dst-modern pb-std">
    <div class="page-header pb-hero pb-hero--page">
      <div class="page-header-fx pb-bubbles" aria-hidden="true" />
      <div class="header-content">
        <div class="title-row">
          <span class="title-icon">🚚</span>
          <h1 class="main-title pb-hero-title">{{ t('master.destination.title') }}</h1>
          <div class="stat-badges" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
            <div class="stat-badge">
              <span class="stat-number">{{ destinationList.length }}</span>
              <span class="stat-label">{{ t('master.common.items') }}</span>
            </div>
            <div class="stat-badge stat-active">
              <span class="stat-number">{{ activeCount }}</span>
              <span class="stat-label">{{ t('master.common.active') }}</span>
            </div>
            <div class="stat-badge stat-inactive">
              <span class="stat-number">{{ destinationList.length - activeCount }}</span>
              <span class="stat-label">{{ t('master.common.inactive') }}</span>
            </div>
            <div class="stat-badge stat-shown">
              <span class="stat-number">{{ filteredList.length }}</span>
              <span class="stat-label">表示中</span>
            </div>
          </div>
        </div>
        <el-button v-if="canCreate" type="primary" @click="openForm()" class="add-btn" size="small">
          ➕ {{ t('master.destination.addDestination') }}
        </el-button>
      </div>
    </div>

    <div class="search-section">
      <div class="search-row">
        <div class="search-group">
          <el-input
            v-model="filters.keyword"
            :placeholder="t('master.destination.searchPlaceholder')"
            clearable
            @input="handleFilter"
            class="search-input"
            size="small"
          >
            <template #prefix><el-icon>🔍</el-icon></template>
          </el-input>
        </div>
        <div class="filter-group">
          <el-select
            v-model="filters.status"
            :placeholder="t('master.common.status')"
            clearable
            @change="handleFilter"
            size="small"
            class="filter-select"
          >
            <el-option :label="t('master.common.active')" :value="1" />
            <el-option :label="t('master.common.inactive')" :value="0" />
          </el-select>
          <el-select
            v-model="filters.issue_type"
            :placeholder="t('master.destination.issueType')"
            clearable
            @change="handleFilter"
            size="small"
            class="filter-select"
          >
            <el-option :label="t('master.destination.issueAuto')" value="自動" />
            <el-option label="1" value="1" />
            <el-option label="2" value="2" />
            <el-option label="3" value="3" />
            <el-option label="4" value="4" />
          </el-select>
          <el-input
            v-model="filters.carrier_cd"
            :placeholder="t('master.destination.carrierCD')"
            clearable
            @input="handleFilter"
            size="small"
            class="filter-input-sm"
          />
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
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: '#fff',
          fontWeight: '600',
          fontSize: '12px',
          padding: '6px 10px',
        }"
        :cell-style="{ padding: '5px 8px', fontSize: '12px' }"
      >
        <el-table-column
          prop="destination_cd"
          :label="t('master.destination.destinationCD')"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span class="code-cell">{{ row.destination_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="destination_name"
          :label="t('master.destination.destinationName')"
          min-width="130"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <span class="name-cell">{{ row.destination_name }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="customer_cd"
          :label="t('master.destination.customerCD')"
          width="90"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.customer_cd" class="ref-chip ref--customer">{{ row.customer_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="carrier_cd"
          :label="t('master.destination.carrierCD')"
          width="90"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.carrier_cd" class="ref-chip ref--carrier">{{ row.carrier_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="delivery_lead_time"
          :label="t('master.destination.deliveryLeadTime')"
          width="65"
          align="center"
        >
          <template #default="{ row }">
            <span class="number-cell">{{ row.delivery_lead_time }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="issue_type"
          :label="t('master.destination.issueType')"
          width="65"
          align="center"
        >
          <template #default="{ row }">
            <el-tag
              :type="row.issue_type === '自動' ? 'info' : 'warning'"
              size="small"
              effect="plain"
              :class="['issue-tag', `issue--${row.issue_type === '自動' ? 'auto' : row.issue_type || 'none'}`]"
            >
              {{ row.issue_type || '—' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="t('master.common.status')" width="80" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.status === 1"
              @update:model-value="(v: string | number | boolean) => toggleStatus(row, v === true)"
              :disabled="!canEdit"
              :loading="row.statusLoading"
              :active-text="t('master.common.active')"
              :inactive-text="t('master.common.inactive')"
              size="small"
            />
          </template>
        </el-table-column>
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
                @click="deleteDestination(row.id)"
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
        <el-icon>📊</el-icon>
        <span>
          {{
            t('master.common.displayCount', {
              shown: filteredList.length,
              total: destinationList.length,
            })
          }}
        </span>
      </div>
    </div>

    <DestinationForm v-model:visible="formVisible" :data="editData" @refresh="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import DestinationForm from './DestinationForm.vue'
import {
  getDestinationList,
  deleteDestinationById,
  updateDestinationStatus,
} from '@/api/master/destinationMaster'
import type { DestinationItem } from '@/types/master'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { t } = useI18n()
const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

type RowEx = DestinationItem & { statusLoading?: boolean }

const loading = ref(false)
const destinationList = ref<RowEx[]>([])
const filters = ref({ keyword: '', status: '' as '' | number, issue_type: '', carrier_cd: '' })

const handleFilter = () => {}
const clearFilters = () => {
  filters.value = { keyword: '', status: '', issue_type: '', carrier_cd: '' }
  fetchList()
}

const activeCount = computed(() => destinationList.value.filter((row) => row.status === 1).length)

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

const filteredList = computed(() => {
  let result = destinationList.value
  if (filters.value.keyword) {
    const k = filters.value.keyword.toLowerCase()
    result = result.filter(
      (row) =>
        row.destination_cd?.toLowerCase().includes(k) ||
        row.destination_name?.toLowerCase().includes(k) ||
        row.customer_cd?.toLowerCase().includes(k),
    )
  }
  if (filters.value.status !== '')
    result = result.filter((row) => row.status === filters.value.status)
  if (filters.value.issue_type)
    result = result.filter((row) => row.issue_type === filters.value.issue_type)
  if (filters.value.carrier_cd)
    result = result.filter((row) =>
      row.carrier_cd?.toLowerCase().includes(filters.value.carrier_cd.toLowerCase()),
    )
  return result
})

const formVisible = ref(false)
const editData = ref<RowEx | null>(null)
function openForm(row: RowEx | null = null) {
  if (row ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  editData.value = row
  formVisible.value = true
}

async function deleteDestination(id: number | undefined) {
  if (!guardMasterOperation(canDelete)) return
  if (id == null) return
  try {
    await ElMessageBox.confirm(t('master.destination.confirmDelete'), t('common.confirm'), {
      type: 'warning',
    })
    await deleteDestinationById(id)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch {
    void 0
  }
}

async function toggleStatus(row: RowEx, on: boolean) {
  if (!guardMasterOperation(canEdit)) return
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
    const res = await getDestinationList({
      keyword: filters.value.keyword || undefined,
      status: filters.value.status !== '' ? filters.value.status : undefined,
      issue_type: filters.value.issue_type || undefined,
      carrier_cd: filters.value.carrier_cd || undefined,
      page: 1,
      pageSize: 5000,
    })
    destinationList.value = (res.list ?? res.data?.list ?? []).map((row) => ({
      ...row,
      statusLoading: false,
    }))
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.destination-master-container {
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 12px 18px;
  margin-bottom: 12px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}
.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
}
.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.title-icon {
  font-size: 1.4rem;
}
.main-title {
  font-size: 1.3rem;
  font-weight: 700;
  margin: 0;
  color: #fff;
}
.stat-badges {
  display: flex;
  gap: 8px;
  margin-left: 10px;
}
.stat-badge {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 14px;
  padding: 3px 10px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.stat-active {
  background: rgba(16, 185, 129, 0.3);
}
.stat-number {
  font-size: 0.95rem;
  font-weight: 700;
  color: #fff;
}
.stat-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.9);
}
.add-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  font-weight: 600;
  color: #fff;
}
.add-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.search-section {
  background: #fff;
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
.search-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.search-group {
  flex: 1;
  min-width: 200px;
}
.search-input {
  width: 100%;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.filter-select {
  width: 100px;
}
.filter-input-sm {
  width: 120px;
}
.clear-btn {
  color: #64748b;
}

.table-section {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  margin-bottom: 12px;
}
.modern-table {
  width: 100%;
}
.code-cell {
  font-family: 'Consolas', monospace;
  font-weight: 600;
  color: #667eea;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}
.name-cell {
  font-weight: 500;
  color: #1e293b;
}
.number-cell {
  font-family: 'Consolas', monospace;
  font-weight: 500;
  color: #374151;
}
.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
}
.action-btn {
  padding: 3px 8px;
  font-size: 11px;
  border-radius: 6px;
  min-width: 32px;
}

.footer-section {
  background: #fff;
  border-radius: 10px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
.result-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #64748b;
  font-size: 0.85rem;
}
.result-info strong {
  color: #667eea;
  font-weight: 700;
}

@media (max-width: 768px) {
  .destination-master-container {
    padding: 8px;
  }
  .page-header {
    padding: 10px 12px;
  }
  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
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
  .filter-select {
    flex: 1;
    min-width: 80px;
  }
  .filter-input-sm {
    flex: 1;
  }
  .main-title {
    font-size: 1.1rem;
  }
}

:deep(.el-table) {
  --el-table-border-color: #e2e8f0;
  --el-table-row-hover-bg-color: #f0f4ff;
}
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #fafbfc;
}
:deep(.el-tag) {
  border-radius: 10px;
  font-weight: 500;
}

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（納入先マスタ / magenta→pink）
 * ============================================================ */
.dst-modern {
  --hx-1: #500724;
  --hx-2: #9d174d;
  --hx-3: #db2777;
  --hx-4: #f472b6;
  --hx-deep: #831843;
  --hx-accent: #db2777;
  --hx-soft: #fdf2f8;
  --hx-line: rgba(219, 39, 119, 0.16);
  background:
    radial-gradient(1100px 360px at 10% -10%, rgba(244, 114, 182, 0.12), transparent 60%),
    radial-gradient(900px 320px at 100% 0%, rgba(168, 85, 247, 0.07), transparent 60%),
    linear-gradient(160deg, #fdf4f9 0%, #fdf2f8 40%, #f8fafc 100%);
}

.dst-modern .page-header {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  padding: 14px 18px;
  background: linear-gradient(125deg, var(--hx-1) 0%, var(--hx-2) 38%, var(--hx-3) 72%, var(--hx-4) 100%);
  box-shadow:
    0 18px 36px -18px rgba(157, 23, 77, 0.6),
    0 6px 14px -6px rgba(244, 114, 182, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.dst-modern .header-content {
  position: relative;
  z-index: 1;
}

.dst-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.dst-modern .title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  font-size: 1.3rem;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow:
    0 4px 0 rgba(80, 7, 36, 0.45),
    0 10px 18px -6px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  animation: dstIconDrive 5s ease-in-out infinite;
}

.dst-modern .main-title {
  text-shadow: 0 2px 10px rgba(80, 7, 36, 0.35);
}

.dst-modern .stat-badges {
  perspective: 600px;
  flex-wrap: wrap;
}

.dst-modern .stat-badge {
  --sc: #fbcfe8;
  position: relative;
  overflow: hidden;
  padding: 5px 12px;
  border-radius: 12px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow:
    0 3px 0 rgba(80, 7, 36, 0.35),
    0 10px 20px -10px rgba(0, 0, 0, 0.45);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transform-style: preserve-3d;
  transition: transform 0.18s ease-out, box-shadow 0.25s ease;
}

.dst-modern .stat-badge::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: var(--sc);
}

.dst-modern .stat-badge::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at var(--mx, 50%) var(--my, 50%), rgba(255, 255, 255, 0.35), transparent 60%);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.dst-modern .stat-badge:hover::after {
  opacity: 1;
}

.dst-modern .stat-badge:hover {
  box-shadow:
    0 5px 0 rgba(80, 7, 36, 0.4),
    0 16px 26px -12px rgba(0, 0, 0, 0.5);
}

.dst-modern .stat-active {
  --sc: #6ee7b7;
  background: linear-gradient(160deg, rgba(16, 185, 129, 0.35), rgba(16, 185, 129, 0.12));
}

.dst-modern .stat-inactive {
  --sc: #cbd5e1;
  background: linear-gradient(160deg, rgba(100, 116, 139, 0.4), rgba(100, 116, 139, 0.14));
}

.dst-modern .stat-shown {
  --sc: #fde68a;
}

.dst-modern .stat-number {
  font-size: 1.05rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  transform: translateZ(14px);
  text-shadow: 0 2px 6px rgba(80, 7, 36, 0.35);
}

.dst-modern .add-btn {
  --k-edge: #047857;
  --k-glow: rgba(16, 185, 129, 0.55);
  height: 32px;
  padding: 0 14px;
  border-radius: 10px;
  border: none;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #34d399, #059669) !important;
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.dst-modern .add-btn:hover {
  transform: translateY(-2px);
  filter: brightness(1.06);
  background: linear-gradient(135deg, #34d399, #059669) !important;
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.dst-modern .add-btn:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 var(--k-edge), inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.dst-modern .search-section,
.dst-modern .table-section,
.dst-modern .footer-section {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid var(--hx-line);
  box-shadow:
    0 10px 24px -16px rgba(157, 23, 77, 0.35),
    0 2px 6px rgba(15, 23, 42, 0.04);
}

.dst-modern .search-section::before,
.dst-modern .table-section::before,
.dst-modern .footer-section::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  z-index: 5;
  background: linear-gradient(90deg, var(--hx-2), var(--hx-3), var(--hx-4), #c084fc);
}

.dst-modern .search-section {
  padding-top: 13px;
}

.dst-modern .search-section :deep(.el-input__wrapper),
.dst-modern .search-section :deep(.el-select__wrapper) {
  border-radius: 10px;
}

.dst-modern .search-section :deep(.el-input__wrapper.is-focus),
.dst-modern .search-section :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px var(--hx-3) inset, 0 0 0 3px rgba(219, 39, 119, 0.12);
}

.dst-modern .clear-btn {
  border-radius: 10px;
  padding: 0 12px;
  color: var(--hx-deep);
  background: var(--hx-soft);
  border: 1px solid rgba(219, 39, 119, 0.2);
  box-shadow: 0 2px 0 rgba(219, 39, 119, 0.18);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.dst-modern .clear-btn:hover {
  transform: translateY(-1px);
  color: var(--hx-deep);
  background: #fce7f3;
  box-shadow: 0 3px 0 rgba(219, 39, 119, 0.24);
}

.dst-modern .table-section {
  padding-top: 3px;
}

.dst-modern .modern-table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: linear-gradient(180deg, #831843, #9d174d) !important;
  color: #fff !important;
  border-bottom: 2px solid var(--hx-4) !important;
  letter-spacing: 0.02em;
}

.dst-modern :deep(.el-table) {
  --el-table-row-hover-bg-color: #fdf2f8;
}

.dst-modern .modern-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 var(--hx-3);
}

.dst-modern .code-cell {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 7px;
  color: var(--hx-deep);
  background: linear-gradient(135deg, #fdf2f8, #fce7f3);
  box-shadow: inset 0 0 0 1px rgba(219, 39, 119, 0.28), 0 2px 0 rgba(219, 39, 119, 0.18);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.dst-modern .modern-table :deep(tr:hover) .code-cell {
  transform: translateY(-1px);
  box-shadow: inset 0 0 0 1px rgba(219, 39, 119, 0.38), 0 3px 0 rgba(219, 39, 119, 0.24);
}

.dst-modern .ref-chip {
  --rc: #64748b;
  display: inline-block;
  padding: 1px 8px;
  border-radius: 999px;
  font-family: 'Consolas', monospace;
  font-size: 11px;
  font-weight: 700;
  color: var(--rc);
  background: color-mix(in srgb, var(--rc) 9%, #fff);
  border: 1px solid color-mix(in srgb, var(--rc) 32%, #fff);
}

.dst-modern .ref--customer { --rc: #0284c7; }
.dst-modern .ref--carrier { --rc: #4f46e5; }

.dst-modern .number-cell {
  display: inline-block;
  min-width: 26px;
  padding: 1px 7px;
  border-radius: 999px;
  font-weight: 800;
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #fde68a;
}

.dst-modern .issue-tag {
  --it: #64748b;
  --el-tag-text-color: var(--it);
  --el-tag-bg-color: color-mix(in srgb, var(--it) 9%, #fff);
  --el-tag-border-color: color-mix(in srgb, var(--it) 35%, #fff);
  font-weight: 700;
  min-width: 30px;
}

.dst-modern .issue--auto { --it: #0891b2; }
.dst-modern .issue--1 { --it: #db2777; }
.dst-modern .issue--2 { --it: #ea580c; }
.dst-modern .issue--3 { --it: #7c3aed; }
.dst-modern .issue--4 { --it: #16a34a; }

.dst-modern .action-btn {
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.dst-modern .action-btn.el-button--primary {
  box-shadow: 0 2px 0 rgba(37, 99, 235, 0.35);
}

.dst-modern .action-btn.el-button--danger {
  box-shadow: 0 2px 0 rgba(220, 38, 38, 0.35);
}

.dst-modern .action-btn:hover {
  transform: translateY(-1px);
}

.dst-modern .action-btn:active {
  transform: translateY(1px);
  box-shadow: none;
}

.dst-modern .footer-section {
  padding-top: 10px;
}

.dst-modern .result-info {
  color: var(--hx-deep);
  font-weight: 600;
}

@keyframes dstIconDrive {
  0%,
  100% {
    transform: perspective(300px) translateX(0) rotateY(0deg);
  }
  30% {
    transform: perspective(300px) translateX(2px) rotateY(-16deg) rotateX(6deg);
  }
  70% {
    transform: perspective(300px) translateX(-2px) rotateY(12deg) rotateX(-4deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .dst-modern .title-icon {
    animation: none;
  }

  .dst-modern .stat-badge {
    transform: none;
  }
}
</style>
