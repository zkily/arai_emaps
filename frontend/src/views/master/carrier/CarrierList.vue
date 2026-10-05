<template>
  <div class="carrier-master-container car-modern pb-std">
    <div class="page-header pb-hero pb-hero--page">
      <div class="page-header-fx pb-bubbles" aria-hidden="true" />
      <div class="header-content">
        <div class="title-row">
          <span class="title-icon">🚚</span>
          <h1 class="main-title pb-hero-title">{{ t('master.carrier.title') }}</h1>
          <div class="stat-badges" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
            <div class="stat-badge">
              <span class="stat-number">{{ carrierList.length }}</span>
              <span class="stat-label">{{ t('master.common.items') }}</span>
            </div>
            <div class="stat-badge stat-active">
              <span class="stat-number">{{ activeCount }}</span>
              <span class="stat-label">{{ t('master.common.active') }}</span>
            </div>
            <div class="stat-badge stat-inactive">
              <span class="stat-number">{{ carrierList.length - activeCount }}</span>
              <span class="stat-label">{{ t('master.common.inactive') }}</span>
            </div>
          </div>
        </div>
        <el-button v-if="canCreate" type="primary" @click="openForm()" class="add-btn" size="small">
          ➕ {{ t('master.carrier.addCarrier') }}
        </el-button>
      </div>
    </div>

    <div class="search-section">
      <div class="search-row">
        <div class="search-group">
          <el-input
            v-model="filters.keyword"
            :placeholder="t('master.carrier.searchPlaceholder')"
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
          prop="carrier_cd"
          :label="t('master.carrier.carrierCD')"
          width="110"
          align="center"
        >
          <template #default="{ row }">
            <span class="code-cell">{{ row.carrier_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="carrier_name"
          :label="t('master.carrier.carrierName')"
          min-width="140"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <span class="name-cell">{{ row.carrier_name }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="contact_person"
          :label="t('master.carrier.contactPerson')"
          width="100"
          show-overflow-tooltip
        />
        <el-table-column
          prop="phone"
          :label="t('master.customer.phone')"
          width="130"
          show-overflow-tooltip
        />
        <el-table-column
          prop="shipping_time"
          :label="t('master.carrier.shippingTime')"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.shipping_time" class="time-chip">
              {{ formatShippingTime(row.shipping_time) }}
            </span>
            <span v-else class="muted-cell">—</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="report_no"
          :label="t('master.carrier.reportNo')"
          width="90"
          align="center"
          show-overflow-tooltip
        />
        <el-table-column
          prop="note"
          :label="t('master.carrier.note')"
          min-width="140"
          show-overflow-tooltip
        />
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
                @click="deleteCarrier(row.id)"
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
              total: carrierList.length,
            })
          }}
        </span>
      </div>
    </div>

    <CarrierForm v-model:visible="formVisible" :data="editData" @refresh="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, DataAnalysis } from '@element-plus/icons-vue'
import CarrierForm from './CarrierForm.vue'
import { getCarrierList, deleteCarrierById, updateCarrierStatus } from '@/api/master/carrierMaster'
import type { CarrierItem } from '@/types/master'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { t } = useI18n()
const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

type RowEx = CarrierItem & { statusLoading?: boolean }

const loading = ref(false)
const carrierList = ref<RowEx[]>([])
const filters = ref({ keyword: '', status: '' as '' | number })

const handleFilter = () => {}
const clearFilters = () => {
  filters.value = { keyword: '', status: '' }
  fetchList()
}

const activeCount = computed(() => carrierList.value.filter((row) => row.status === 1).length)

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

function formatShippingTime(t: string | undefined): string {
  if (!t) return '—'
  const s = String(t)
  if (s.length >= 5) return s.slice(0, 5)
  return s
}

const filteredList = computed(() => {
  let result = carrierList.value
  if (filters.value.keyword) {
    const k = filters.value.keyword.toLowerCase()
    result = result.filter(
      (row) =>
        row.carrier_cd?.toLowerCase().includes(k) ||
        row.carrier_name?.toLowerCase().includes(k) ||
        row.contact_person?.toLowerCase().includes(k),
    )
  }
  if (filters.value.status !== '')
    result = result.filter((row) => row.status === filters.value.status)
  return result
})

const formVisible = ref(false)
const editData = ref<RowEx | null>(null)
function openForm(row: RowEx | null = null) {
  if (row ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  editData.value = row
  formVisible.value = true
}

async function deleteCarrier(id: number | undefined) {
  if (!guardMasterOperation(canDelete)) return
  if (id == null) return
  try {
    await ElMessageBox.confirm(t('master.carrier.confirmDelete'), t('common.confirm'), {
      type: 'warning',
    })
    await deleteCarrierById(id)
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
    await updateCarrierStatus(row.id!, next)
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
    const res = await getCarrierList({
      keyword: filters.value.keyword || undefined,
      status: filters.value.status !== '' ? filters.value.status : undefined,
      page: 1,
      pageSize: 5000,
    })
    carrierList.value = (res.list ?? res.data?.list ?? []).map((row) => ({
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
.carrier-master-container {
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%);
  border-radius: 12px;
  padding: 12px 18px;
  margin-bottom: 12px;
  box-shadow: 0 4px 20px rgba(14, 165, 233, 0.3);
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
  color: #0ea5e9;
  font-weight: 700;
}

@media (max-width: 768px) {
  .carrier-master-container {
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
  .main-title {
    font-size: 1.1rem;
  }
}

:deep(.el-table) {
  --el-table-border-color: #e2e8f0;
  --el-table-row-hover-bg-color: #f0f9ff;
}
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #fafbfc;
}

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（運送便マスタ / indigo→sky）
 * ============================================================ */
.carrier-master-container.car-modern {
  background:
    radial-gradient(1000px 360px at 0% 0%, rgba(67, 56, 202, 0.08), transparent 60%),
    radial-gradient(900px 360px at 100% 0%, rgba(14, 165, 233, 0.08), transparent 60%),
    #f1f5f9;
}

/* ---------- ヒーローヘッダー ---------- */
.car-modern .page-header {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  background: linear-gradient(125deg, #1e1b4b 0%, #312e81 34%, #4338ca 66%, #0ea5e9 100%);
  box-shadow:
    0 18px 36px -18px rgba(49, 46, 129, 0.7),
    0 4px 12px -6px rgba(14, 165, 233, 0.4),
    inset 0 0 0 1px rgba(255, 255, 255, 0.14);
}

.car-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.car-modern .header-content {
  position: relative;
  z-index: 1;
}

.car-modern .title-row {
  gap: 12px;
}

.car-modern .title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  font-size: 20px;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0.08) 100%);
  border: 1px solid rgba(255, 255, 255, 0.34);
  box-shadow:
    0 4px 0 rgba(30, 27, 75, 0.6),
    0 10px 20px -8px rgba(2, 6, 23, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(6px);
  animation: carDrive 3.2s ease-in-out infinite;
}

.car-modern .main-title {
  font-size: 20px;
  font-weight: 800;
  text-shadow: 0 2px 8px rgba(2, 6, 23, 0.4);
}

/* 統計バッジ：3Dチルト＋グレア */
.car-modern .stat-badges {
  perspective: 600px;
}

.car-modern .stat-badge {
  position: relative;
  overflow: hidden;
  padding: 4px 12px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow:
    0 3px 0 rgba(30, 27, 75, 0.5),
    0 10px 18px -10px rgba(2, 6, 23, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.32);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transition:
    transform 0.18s ease-out,
    box-shadow 0.25s ease;
}

.car-modern .stat-badge::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.25s ease;
  background: radial-gradient(
    circle at var(--mx, 50%) var(--my, 50%),
    rgba(255, 255, 255, 0.35) 0%,
    transparent 65%
  );
}

.car-modern .stat-badge:hover::after {
  opacity: 1;
}

.car-modern .stat-number {
  font-size: 1.05rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.car-modern .stat-inactive {
  background: rgba(15, 23, 42, 0.32);
}

/* 追加ボタン：3Dキーキャップ */
.car-modern .add-btn,
.car-modern .add-btn:hover,
.car-modern .add-btn:focus {
  color: #fff;
  font-weight: 700;
  border: 1px solid rgba(255, 255, 255, 0.36);
  background: linear-gradient(135deg, #7dd3fc 0%, #0ea5e9 50%, #0369a1 100%);
}

.car-modern .add-btn {
  box-shadow:
    0 3px 0 #0c4a6e,
    0 10px 18px -8px rgba(14, 165, 233, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    filter 0.18s ease;
}

.car-modern .add-btn:hover {
  filter: brightness(1.06);
  transform: translateY(-2px);
  box-shadow:
    0 5px 0 #0c4a6e,
    0 14px 22px -8px rgba(14, 165, 233, 0.65),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.car-modern .add-btn:active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 #0c4a6e,
    0 4px 8px -4px rgba(14, 165, 233, 0.5);
}

/* ---------- 検索バー ---------- */
.car-modern .search-section,
.car-modern .table-section,
.car-modern .footer-section {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid #c7d2fe;
  box-shadow:
    0 14px 28px -22px rgba(49, 46, 129, 0.5),
    0 1px 3px rgba(15, 23, 42, 0.05);
}

.car-modern .search-section::before,
.car-modern .table-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 5;
  pointer-events: none;
  background: linear-gradient(90deg, #312e81 0%, #4338ca 50%, #0ea5e9 100%);
}

.car-modern .search-section {
  padding-top: 12px;
  background: linear-gradient(110deg, #eef2ff 0%, #ffffff 60%);
}

.car-modern .search-row :deep(.el-input__wrapper.is-focus),
.car-modern .search-row :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px #4f46e5 inset,
    0 0 0 3px rgba(79, 70, 229, 0.15);
}

.car-modern .clear-btn {
  font-weight: 600;
  border-radius: 8px;
  background: #f8fafc;
  box-shadow: inset 0 0 0 1px #e2e8f0;
}

.car-modern .clear-btn:hover {
  color: #4338ca;
  background: #eef2ff;
  box-shadow: inset 0 0 0 1px #c7d2fe;
}

/* ---------- テーブル ---------- */
.car-modern .modern-table :deep(.el-table__header-wrapper th.el-table__cell) {
  color: #312e81 !important;
  font-weight: 700 !important;
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%) !important;
  border-bottom: 2px solid #a5b4fc !important;
}

.car-modern .modern-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child),
.car-modern .modern-table :deep(.el-table__body tr.current-row > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 #4f46e5;
}

.car-modern .code-cell {
  display: inline-block;
  padding: 1px 8px;
  font-size: 11.5px;
  font-weight: 700;
  color: #3730a3;
  border-radius: 6px;
  background: linear-gradient(180deg, #ffffff 0%, #e0e7ff 100%);
  box-shadow:
    inset 0 0 0 1px #c7d2fe,
    0 2px 0 #c7d2fe;
  transition: transform 0.15s ease;
}

.car-modern .modern-table :deep(.el-table__body tr:hover) .code-cell {
  transform: translateY(-1px);
}

.car-modern .time-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 9px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #0369a1;
  border-radius: 999px;
  background: #f0f9ff;
  box-shadow: inset 0 0 0 1px #bae6fd;
}

.car-modern .time-chip::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #0ea5e9;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.18);
}

.car-modern .muted-cell {
  color: #cbd5e1;
}

.car-modern .modern-table :deep(.el-switch.is-checked .el-switch__core) {
  background: #10b981;
  border-color: #10b981;
}

.car-modern .action-btn {
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}

.car-modern .action-btn.el-button--primary {
  box-shadow: 0 2px 0 #bfdbfe;
}

.car-modern .action-btn.el-button--danger {
  box-shadow: 0 2px 0 #fecaca;
}

.car-modern .action-btn:hover {
  transform: translateY(-1px);
}

.car-modern .action-btn.el-button--primary:hover {
  box-shadow:
    0 3px 0 #1e40af,
    0 8px 14px -8px rgba(37, 99, 235, 0.6);
}

.car-modern .action-btn.el-button--danger:hover {
  box-shadow:
    0 3px 0 #991b1b,
    0 8px 14px -8px rgba(220, 38, 38, 0.6);
}

.car-modern .action-btn:active {
  transform: translateY(1px);
  box-shadow: none;
}

/* ---------- フッター ---------- */
.car-modern .footer-section {
  background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%);
}

.car-modern .result-info {
  padding: 2px 10px;
  color: #312e81;
  font-weight: 700;
  border-radius: 999px;
  background: #e0e7ff;
  box-shadow: inset 0 0 0 1px #c7d2fe;
}

/* ---------- キーフレーム ---------- */

@keyframes carDrive {
  0%,
  100% {
    transform: perspective(300px) rotateY(0deg) translateX(0);
  }
  25% {
    transform: perspective(300px) rotateY(-10deg) translateX(-1px) translateY(-1px);
  }
  50% {
    transform: perspective(300px) rotateY(0deg) translateX(1px);
  }
  75% {
    transform: perspective(300px) rotateY(10deg) translateX(0) translateY(-1px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .car-modern .title-icon {
    animation: none;
  }

  .car-modern .stat-badge {
    transform: none;
    transition: none;
  }
}
</style>
