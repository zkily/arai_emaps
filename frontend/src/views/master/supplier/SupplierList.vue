<template>
  <div class="supplier-master-container sup-modern">
    <div class="page-header">
      <div class="page-header-fx" aria-hidden="true">
        <span class="fx-orb orb-a" />
        <span class="fx-orb orb-b" />
        <span class="fx-grid" />
        <span class="fx-sheen" />
      </div>
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon"><OfficeBuilding /></el-icon>
            {{ t('master.supplier.title') }}
          </h1>
          <p class="subtitle">{{ t('master.supplier.subtitle') }}</p>
        </div>
        <div class="header-stats" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
          <div class="stat-card">
            <div class="stat-number">{{ dataList.length }}</div>
            <div class="stat-label">{{ t('master.supplier.totalSuppliers') }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ dataList.filter((s) => s.email).length }}</div>
            <div class="stat-label">{{ t('master.supplier.emailRegistered') }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ emailRate }}<small class="stat-sub">%</small></div>
            <div class="stat-label">メール登録率</div>
          </div>
        </div>
      </div>
    </div>

    <div class="action-section">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon"><Filter /></el-icon>
          <span>{{ t('master.supplier.searchFilter') }}</span>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilter" :icon="Refresh" class="clear-btn">
            {{ t('master.supplier.clear') }}
          </el-button>
          <el-button v-if="canCreate" type="primary" @click="handleAdd" :icon="Plus" class="add-supplier-btn">
            {{ t('master.supplier.addSupplier') }}
          </el-button>
        </div>
      </div>
      <div class="filters-grid">
        <div class="filter-item search-item">
          <label class="filter-label">
            <el-icon><Search /></el-icon>
            {{ t('master.supplier.keywordSearch') }}
          </label>
          <el-input
            v-model="filters.keyword"
            :placeholder="t('master.supplier.placeholder')"
            clearable
            @keyup.enter="fetchList"
            class="filter-input"
          >
            <template #suffix>
              <el-icon v-if="filters.keyword" class="search-active"><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-item">
          <el-button type="primary" @click="fetchList" :icon="Search" class="search-btn">
            {{ t('master.common.search') }}
          </el-button>
        </div>
      </div>
    </div>

    <el-card class="table-card">
      <el-table :data="dataList" stripe highlight-current-row class="modern-table">
        <el-table-column
          :label="t('master.supplier.supplierCD')"
          prop="supplier_cd"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <div class="supplier-code-cell">
              <el-icon class="code-icon"><OfficeBuilding /></el-icon>
              <span>{{ row.supplier_cd }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          :label="t('master.supplier.supplierName')"
          prop="supplier_name"
          min-width="180"
          show-overflow-tooltip
        />
        <el-table-column
          :label="t('master.supplier.contactPerson')"
          prop="contact_person"
          width="120"
          show-overflow-tooltip
        />
        <el-table-column
          :label="t('master.supplier.phone')"
          prop="phone"
          width="150"
          show-overflow-tooltip
        />
        <el-table-column
          :label="t('master.supplier.email')"
          prop="email"
          min-width="200"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <span v-if="row.email" class="mail-chip">{{ row.email }}</span>
            <span v-else class="muted-cell">—</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="canEdit || canDelete"
          :label="t('master.common.actions')"
          width="140"
          fixed="right"
          align="center"
        >
          <template #default="{ row }">
            <div class="action-buttons-table">
              <el-button v-if="canEdit" size="small" type="primary" link @click="handleEdit(row)" :icon="Edit">
                {{ t('master.supplier.edit') }}
              </el-button>
              <el-button v-if="canDelete" size="small" type="danger" link @click="handleDelete(row)" :icon="Delete">
                {{ t('master.supplier.delete') }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="pagination-section">
      <el-pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @update:page-size="handlePageSizeChange"
        @update:current-page="fetchList"
      />
    </div>

    <SupplierEditDialog
      :visible="dialogVisible"
      :editData="editData"
      @update:visible="dialogVisible = $event"
      @saved="fetchList"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  Plus,
  OfficeBuilding,
  Filter,
  Refresh,
  Search,
  Edit,
  Delete,
} from '@element-plus/icons-vue'
import { getSupplierList, deleteSupplier } from '@/api/master/supplierMaster'
import type { Supplier } from '@/types/master'
import SupplierEditDialog from './SupplierEditDialog.vue'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { t } = useI18n()
const { canCreate, canEdit, canDelete } = useMasterOperationPermission()
const filters = reactive({ keyword: '' })
const dataList = ref<Supplier[]>([])
const pagination = reactive({ currentPage: 1, pageSize: 20, total: 0 })

const dialogVisible = ref(false)
const editData = ref<Supplier | null>(null)

// メール登録率（表示中の一覧ベース）
const emailRate = computed(() => {
  const total = dataList.value.length
  return total > 0 ? Math.round((dataList.value.filter((s) => s.email).length / total) * 100) : 0
})

// ヘッダー統計カードの3Dチルト（マウス追従）
function handleStatTilt(e: MouseEvent) {
  const item = (e.target as HTMLElement | null)?.closest<HTMLElement>('.stat-card')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    if (el !== item) {
      el.style.removeProperty('--rx')
      el.style.removeProperty('--ry')
    }
  })
  if (!item) return
  const rect = item.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  item.style.setProperty('--rx', `${((0.5 - py) * 14).toFixed(2)}deg`)
  item.style.setProperty('--ry', `${((px - 0.5) * 14).toFixed(2)}deg`)
  item.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
  item.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
}

function resetStatTilt(e: MouseEvent) {
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

const fetchList = async () => {
  const res = await getSupplierList({
    keyword: filters.keyword,
    page: pagination.currentPage,
    pageSize: pagination.pageSize,
  })
  dataList.value = res?.data?.list ?? res?.list ?? []
  pagination.total = res?.data?.total ?? res?.total ?? 0
}

const clearFilter = () => {
  filters.keyword = ''
  fetchList()
}

const handlePageSizeChange = () => {
  pagination.currentPage = 1
  fetchList()
}

const handleAdd = () => {
  if (!guardMasterOperation(canCreate)) return
  editData.value = null
  dialogVisible.value = true
}

const handleEdit = (row: Supplier) => {
  if (!guardMasterOperation(canEdit)) return
  editData.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: Supplier) => {
  if (!guardMasterOperation(canDelete)) return
  try {
    await ElMessageBox.confirm(t('master.supplier.confirmDelete'), t('common.confirm'), {
      type: 'warning',
    })
    await deleteSupplier(row.id!)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch {
    void 0
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.supplier-master-container {
  padding: 6px;
  background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 10px 16px;
  margin-bottom: 6px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.25);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.title-section {
  flex: 1;
}

.main-title {
  font-size: 1.35rem;
  font-weight: 700;
  margin: 0 0 2px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 1.3rem;
  color: rgba(255, 255, 255, 0.9);
}

.subtitle {
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  font-size: 0.8rem;
}

.header-stats {
  display: flex;
  gap: 8px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
  color: white;
  padding: 6px 12px;
  border-radius: 10px;
  text-align: center;
  min-width: 70px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.2s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.stat-number {
  font-size: 1.4rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.7rem;
  opacity: 0.9;
  margin-top: 2px;
  white-space: nowrap;
}

.action-section {
  background: white;
  border-radius: 10px;
  margin-bottom: 6px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #334155;
}

.filter-icon {
  font-size: 1rem;
  color: #667eea;
}

.filter-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.clear-btn {
  color: #64748b;
  transition: all 0.2s ease;
  padding: 6px 10px !important;
  font-size: 12px !important;
}

.clear-btn:hover {
  color: #667eea;
}

.add-supplier-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  padding: 7px 12px !important;
  font-weight: 600;
  font-size: 12px !important;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.25);
  transition: all 0.2s;
}

.add-supplier-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
}

.filters-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  padding: 10px 14px;
  align-items: end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
}

.search-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  padding: 7px 14px !important;
  font-weight: 600;
  font-size: 12px !important;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.25);
  transition: all 0.2s;
}

.search-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
}

.table-card {
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  margin-bottom: 6px;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.supplier-code-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 11px;
  color: #667eea;
  font-weight: 600;
}

.code-icon {
  color: #667eea;
  font-size: 14px;
}

.action-buttons-table {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.pagination-section {
  background: white;
  border-radius: 8px;
  padding: 8px 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  text-align: center;
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
  font-size: 12px;
}

:deep(.el-table th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
  color: #334155;
  font-weight: 600;
  font-size: 12px;
  padding: 6px 8px !important;
}

:deep(.el-table td) {
  padding: 4px 6px !important;
}

:deep(.el-table .el-button--small) {
  padding: 4px 8px;
  font-size: 11px;
  border-radius: 5px;
}

:deep(.el-pagination) {
  justify-content: center;
}

:deep(.el-pager li) {
  border-radius: 6px;
  font-size: 12px;
  min-width: 28px;
  height: 28px;
  line-height: 28px;
}

:deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 响应式 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .header-stats {
    align-self: stretch;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .supplier-master-container {
    padding: 4px;
  }
  .page-header {
    padding: 8px 12px;
    border-radius: 10px;
  }
  .main-title {
    font-size: 1.15rem;
  }
  .filter-header {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
    padding: 10px 12px;
  }
  .filter-actions {
    justify-content: flex-start;
  }
  .filters-grid {
    grid-template-columns: 1fr;
    gap: 8px;
    padding: 10px 12px;
  }
  .stat-card {
    min-width: 60px;
    padding: 5px 8px;
  }
  .stat-number {
    font-size: 1.1rem;
  }
}

/* 动画效果 */
.page-header,
.action-section,
.table-card,
.pagination-section {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（仕入先マスタ / rose→red）
 * ============================================================ */
.supplier-master-container.sup-modern {
  --hx-1: #4c0519;
  --hx-2: #881337;
  --hx-3: #e11d48;
  --hx-4: #fb7185;
  --hx-deep: #881337;
  --hx-accent: #e11d48;
  --hx-soft: #fff1f2;
  --hx-soft2: #ffe4e6;
  --hx-line: #fecdd3;
  --hx-orb-a: #fda4af;
  --hx-orb-b: #fbcfe8;
  background:
    radial-gradient(1000px 360px at 0% 0%, rgba(225, 29, 72, 0.07), transparent 60%),
    radial-gradient(900px 360px at 100% 0%, rgba(251, 113, 133, 0.08), transparent 60%),
    #f8fafc;
}

/* ---------- ヒーローヘッダー ---------- */
.sup-modern .page-header {
  position: relative;
  overflow: hidden;
  padding: 12px 18px;
  border-radius: 16px;
  background: linear-gradient(125deg, var(--hx-1) 0%, var(--hx-2) 34%, var(--hx-3) 70%, var(--hx-4) 100%);
  box-shadow:
    0 18px 36px -18px color-mix(in srgb, var(--hx-2) 70%, transparent),
    0 4px 12px -6px color-mix(in srgb, var(--hx-3) 40%, transparent),
    inset 0 0 0 1px rgba(255, 255, 255, 0.16);
}

.sup-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.sup-modern .header-content {
  position: relative;
  z-index: 1;
}

.sup-modern .page-header-fx .fx-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(22px);
  opacity: 0.6;
  animation: supOrbFloat 11s ease-in-out infinite;
}

.sup-modern .page-header-fx .orb-a {
  width: 240px;
  height: 240px;
  top: -140px;
  right: 30%;
  background: radial-gradient(circle, var(--hx-orb-a) 0%, transparent 70%);
}

.sup-modern .page-header-fx .orb-b {
  width: 190px;
  height: 190px;
  bottom: -120px;
  left: 22%;
  background: radial-gradient(circle, var(--hx-orb-b) 0%, transparent 70%);
  animation-delay: -5s;
}

.sup-modern .page-header-fx .fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: radial-gradient(ellipse at 14% 50%, #000 0%, transparent 70%);
}

.sup-modern .page-header-fx .fx-sheen {
  position: absolute;
  top: 0;
  bottom: 0;
  left: -40%;
  width: 35%;
  background: linear-gradient(100deg, transparent 0%, rgba(255, 255, 255, 0.16) 50%, transparent 100%);
  animation: supSheen 7s ease-in-out infinite;
}

.sup-modern .main-title {
  gap: 12px;
  font-size: 20px;
  font-weight: 800;
  text-shadow: 0 2px 8px rgba(2, 6, 23, 0.35);
}

.sup-modern .title-icon {
  width: 40px;
  height: 40px;
  font-size: 20px;
  color: #fff;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.32) 0%, rgba(255, 255, 255, 0.08) 100%);
  border: 1px solid rgba(255, 255, 255, 0.36);
  box-shadow:
    0 4px 0 color-mix(in srgb, var(--hx-1) 70%, transparent),
    0 10px 20px -8px rgba(2, 6, 23, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(6px);
  animation: supIconFloat 5s ease-in-out infinite;
}

.sup-modern .subtitle {
  color: rgba(255, 255, 255, 0.86);
}

/* 統計カード：3Dチルト＋グレア＋上端アクセント */
.sup-modern .header-stats {
  perspective: 700px;
}

.sup-modern .stat-card {
  --sc: rgba(255, 255, 255, 0.9);
  position: relative;
  overflow: hidden;
  min-width: 82px;
  padding: 8px 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow:
    0 10px 22px -12px rgba(2, 6, 23, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transform-style: preserve-3d;
  transition:
    transform 0.18s ease-out,
    box-shadow 0.25s ease,
    background 0.2s ease;
}

.sup-modern .stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--sc);
}

.sup-modern .stat-card::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.25s ease;
  background: radial-gradient(
    circle at var(--mx, 50%) var(--my, 50%),
    rgba(255, 255, 255, 0.32) 0%,
    transparent 60%
  );
}

.sup-modern .stat-card:hover {
  box-shadow:
    0 16px 28px -12px rgba(2, 6, 23, 0.7),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.sup-modern .stat-card:hover::after {
  opacity: 1;
}

.sup-modern .stat-card:nth-child(2) {
  --sc: #93c5fd;
}

.sup-modern .stat-card:nth-child(3) {
  --sc: #fde68a;
  background: rgba(76, 5, 25, 0.24);
}

.sup-modern .stat-number {
  font-weight: 800;
  text-shadow: 0 1px 6px rgba(2, 6, 23, 0.3);
  transform: translateZ(14px);
}

.sup-modern .stat-sub {
  margin-left: 1px;
  font-size: 0.65em;
  opacity: 0.8;
}

.sup-modern .stat-label {
  font-weight: 600;
}

/* ---------- 検索パネル ---------- */
.sup-modern .action-section,
.sup-modern .table-card,
.sup-modern .pagination-section {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border-color: var(--hx-line);
  box-shadow:
    0 14px 28px -22px color-mix(in srgb, var(--hx-2) 55%, transparent),
    0 1px 3px rgba(15, 23, 42, 0.05);
}

.sup-modern .action-section::before,
.sup-modern .table-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 3;
  pointer-events: none;
  background: linear-gradient(90deg, var(--hx-2) 0%, var(--hx-3) 55%, var(--hx-4) 100%);
}

.sup-modern .filter-header {
  padding-top: 10px;
  background: linear-gradient(110deg, var(--hx-soft) 0%, #ffffff 60%);
  border-bottom: 1px dashed var(--hx-line);
}

.sup-modern .filter-title {
  color: var(--hx-deep);
  font-weight: 700;
}

.sup-modern .filter-icon {
  width: 24px;
  height: 24px;
  font-size: 13px;
  color: #fff;
  border-radius: 7px;
  background: linear-gradient(145deg, var(--hx-4) 0%, var(--hx-2) 100%);
  box-shadow:
    0 2px 0 var(--hx-1),
    0 6px 10px -5px color-mix(in srgb, var(--hx-3) 60%, transparent);
  animation: supIconFloat 6s ease-in-out infinite;
}

.sup-modern .filter-label .el-icon {
  color: var(--hx-accent);
}

.sup-modern .filter-item.search-item {
  padding: 6px 8px;
  border-radius: 10px;
  border-left: 3px solid var(--hx-accent);
  background: linear-gradient(180deg, #ffffff 0%, var(--hx-soft) 100%);
  transition:
    transform 0.15s ease,
    box-shadow 0.2s ease;
}

.sup-modern .filter-item.search-item:focus-within {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px -10px color-mix(in srgb, var(--hx-3) 50%, transparent);
}

.sup-modern .clear-btn {
  font-weight: 600;
  border-radius: 8px;
  background: #f8fafc;
  box-shadow: inset 0 0 0 1px #e2e8f0;
}

.sup-modern .clear-btn:hover {
  color: var(--hx-accent);
  background: var(--hx-soft);
  box-shadow: inset 0 0 0 1px var(--hx-line);
}

/* 3Dキーキャップ */
.sup-modern .add-supplier-btn,
.sup-modern .search-btn {
  --k-edge: var(--hx-1);
  --k-glow: color-mix(in srgb, var(--hx-3) 55%, transparent);
  background: linear-gradient(135deg, var(--hx-4) 0%, var(--hx-3) 45%, var(--hx-2) 100%);
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    filter 0.18s ease;
}

.sup-modern .search-btn {
  --k-edge: #1e3a8a;
  --k-glow: rgba(37, 99, 235, 0.5);
  background: linear-gradient(135deg, #60a5fa 0%, #2563eb 55%, #1d4ed8 100%);
}

.sup-modern .add-supplier-btn:hover,
.sup-modern .search-btn:hover {
  filter: brightness(1.06);
  transform: translateY(-2px);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.36);
}

.sup-modern .add-supplier-btn:active,
.sup-modern .search-btn:active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 var(--k-edge),
    0 4px 8px -4px var(--k-glow);
}

/* ---------- テーブル ---------- */
.sup-modern .modern-table :deep(.el-table__header-wrapper th.el-table__cell) {
  color: var(--hx-deep) !important;
  font-weight: 700;
  background: linear-gradient(180deg, var(--hx-soft) 0%, var(--hx-soft2) 100%) !important;
  border-bottom: 2px solid var(--hx-line) !important;
}

.sup-modern .modern-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child),
.sup-modern .modern-table :deep(.el-table__body tr.current-row > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 var(--hx-accent);
}

.sup-modern .supplier-code-cell {
  display: inline-flex;
  padding: 2px 8px;
  font-size: 11.5px;
  font-weight: 700;
  color: var(--hx-deep);
  border-radius: 6px;
  background: linear-gradient(180deg, #ffffff 0%, var(--hx-soft2) 100%);
  box-shadow:
    inset 0 0 0 1px var(--hx-line),
    0 2px 0 var(--hx-line);
  transition: transform 0.15s ease;
}

.sup-modern .code-icon {
  color: var(--hx-accent);
}

.sup-modern .modern-table :deep(.el-table__body tr:hover) .supplier-code-cell {
  transform: translateY(-1px);
}

.sup-modern .mail-chip {
  display: inline-block;
  max-width: 100%;
  padding: 1px 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
  color: #1d4ed8;
  font-size: 11.5px;
  border-radius: 999px;
  background: #eff6ff;
  box-shadow: inset 0 0 0 1px #bfdbfe;
}

.sup-modern .muted-cell {
  color: #cbd5e1;
}

.sup-modern .action-buttons-table :deep(.el-button.is-link) {
  padding: 2px 8px;
  border-radius: 6px;
  transition:
    transform 0.15s ease,
    background 0.15s ease;
}

.sup-modern .action-buttons-table :deep(.el-button--primary.is-link:hover) {
  transform: translateY(-1px);
  background: #eff6ff;
}

.sup-modern .action-buttons-table :deep(.el-button--danger.is-link:hover) {
  transform: translateY(-1px);
  background: #fef2f2;
}

/* ---------- ページネーション ---------- */
.sup-modern .pagination-section {
  background: linear-gradient(180deg, #ffffff 0%, var(--hx-soft) 100%);
}

.sup-modern .pagination-section :deep(.el-pager li.is-active) {
  color: #fff;
  background: linear-gradient(135deg, var(--hx-4) 0%, var(--hx-3) 55%, var(--hx-2) 100%);
  transform: translateY(-1px);
  box-shadow:
    0 2px 0 var(--hx-1),
    0 6px 12px -6px color-mix(in srgb, var(--hx-3) 70%, transparent);
}

.sup-modern .pagination-section :deep(.el-pager li:not(.is-active):hover) {
  color: var(--hx-accent);
}

/* ---------- キーフレーム ---------- */
@keyframes supOrbFloat {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(-18px, 10px, 0) scale(1.08);
  }
}

@keyframes supSheen {
  0%,
  60% {
    left: -40%;
  }
  100% {
    left: 130%;
  }
}

@keyframes supIconFloat {
  0%,
  100% {
    transform: perspective(300px) rotateX(0deg) rotateY(0deg) translateY(0);
  }
  50% {
    transform: perspective(300px) rotateX(10deg) rotateY(-14deg) translateY(-2px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .sup-modern .page-header-fx .fx-orb,
  .sup-modern .page-header-fx .fx-sheen,
  .sup-modern .title-icon,
  .sup-modern .filter-icon {
    animation: none;
  }

  .sup-modern .stat-card {
    transform: none;
    transition: none;
  }
}
</style>
