<template>
  <div class="supplier-master-container">
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon"><OfficeBuilding /></el-icon>
            {{ t('master.supplier.title') }}
          </h1>
          <p class="subtitle">{{ t('master.supplier.subtitle') }}</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ dataList.length }}</div>
            <div class="stat-label">{{ t('master.supplier.totalSuppliers') }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ dataList.filter((s) => s.email).length }}</div>
            <div class="stat-label">{{ t('master.supplier.emailRegistered') }}</div>
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
          <el-button text @click="clearFilter" :icon="Refresh" class="clear-btn">{{ t('master.supplier.clear') }}</el-button>
          <el-button type="primary" @click="handleAdd" :icon="Plus" class="add-supplier-btn">
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
          <el-button type="primary" @click="fetchList" :icon="Search" class="search-btn">{{ t('master.common.search') }}</el-button>
        </div>
      </div>
    </div>

    <el-card class="table-card">
      <el-table :data="dataList" stripe highlight-current-row class="modern-table">
        <el-table-column :label="t('master.supplier.supplierCD')" prop="supplier_cd" width="120" align="center">
          <template #default="{ row }">
            <div class="supplier-code-cell">
              <el-icon class="code-icon"><OfficeBuilding /></el-icon>
              <span>{{ row.supplier_cd }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.supplier.supplierName')" prop="supplier_name" min-width="180" show-overflow-tooltip />
        <el-table-column :label="t('master.supplier.contactPerson')" prop="contact_person" width="120" show-overflow-tooltip />
        <el-table-column :label="t('master.supplier.phone')" prop="phone" width="150" show-overflow-tooltip />
        <el-table-column :label="t('master.supplier.email')" prop="email" min-width="200" show-overflow-tooltip />
        <el-table-column :label="t('master.common.actions')" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons-table">
              <el-button size="small" type="primary" link @click="handleEdit(row)" :icon="Edit">{{ t('master.supplier.edit') }}</el-button>
              <el-button size="small" type="danger" link @click="handleDelete(row)" :icon="Delete">{{ t('master.supplier.delete') }}</el-button>
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
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, OfficeBuilding, Filter, Refresh, Search, Edit, Delete } from '@element-plus/icons-vue'
import { getSupplierList, deleteSupplier } from '@/api/master/supplierMaster'
import type { Supplier } from '@/types/master'
import SupplierEditDialog from './SupplierEditDialog.vue'

const { t } = useI18n()
const filters = reactive({ keyword: '' })
const dataList = ref<Supplier[]>([])
const pagination = reactive({ currentPage: 1, pageSize: 20, total: 0 })

const dialogVisible = ref(false)
const editData = ref<Supplier | null>(null)

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
  editData.value = null
  dialogVisible.value = true
}

const handleEdit = (row: Supplier) => {
  editData.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: Supplier) => {
  try {
    await ElMessageBox.confirm(t('master.supplier.confirmDelete'), t('common.confirm'), { type: 'warning' })
    await deleteSupplier(row.id!)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch {}
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
</style>
