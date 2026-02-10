<template>
  <transition name="fade-slide" mode="out-in">
    <div class="route-master-container" v-if="true">
      <!-- Compact Header -->
      <div class="page-header">
        <div class="header-content">
          <div class="title-section">
            <div class="title-row">
              <span class="title-icon">🛠️</span>
              <h1 class="main-title">{{ t('master.processRoute.title') }}</h1>
              <div class="stat-badge">
                <span class="stat-number">{{ routeList.length }}</span>
                <span class="stat-label">{{ t('master.common.items') }}</span>
              </div>
            </div>
            <p class="subtitle">{{ t('master.processRoute.subtitle') }}</p>
          </div>
          <el-button type="primary" icon="Plus" @click="openAddDialog" class="add-btn">
            <span class="btn-icon">➕</span> {{ t('master.processRoute.addRoute') }}
          </el-button>
        </div>
      </div>

      <!-- Compact Search Section -->
      <div class="search-section">
        <div class="search-row">
          <div class="search-input-wrapper">
            <el-icon class="search-icon">🔍</el-icon>
            <el-input 
              v-model="filters.keyword" 
              :placeholder="t('master.processRoute.searchPlaceholder')" 
              clearable 
              @keyup.enter="fetchList"
              class="search-input"
            />
          </div>
          <el-button type="primary" @click="fetchList" class="search-btn">{{ t('master.common.search') }}</el-button>
        </div>
      </div>

      <!-- Data Table -->
      <div class="table-section">
        <el-table 
          :data="routeList" 
          border 
          stripe 
          highlight-current-row 
          v-loading="loading" 
          class="modern-table"
          :header-cell-style="{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#fff', fontWeight: '600', fontSize: '13px', padding: '8px 12px' }"
          :cell-style="{ padding: '6px 10px', fontSize: '13px' }"
        >
          <el-table-column :label="t('master.processRoute.routeCD')" prop="route_cd" width="110" align="center">
            <template #default="{ row }">
              <span class="code-cell">{{ row.route_cd }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('master.processRoute.routeName')" prop="route_name" min-width="120">
            <template #default="{ row }">
              <span class="name-cell">{{ row.route_name }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('master.processRoute.description')" prop="description" min-width="180" show-overflow-tooltip />
          <el-table-column :label="t('master.processRoute.inUse')" prop="is_active" width="70" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active !== false ? 'success' : 'info'" size="small" effect="plain" class="status-tag">
                {{ row.is_active !== false ? t('master.common.active') : t('master.common.inactive') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('master.processRoute.default')" prop="is_default" width="85" align="center">
            <template #default="{ row }">
              <el-icon v-if="row.is_default" class="default-icon">✅</el-icon>
              <span v-else class="empty-default">-</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('master.common.actions')" width="240" align="center" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button size="small" type="primary" plain @click="goToSteps(row)" class="action-btn">
                  📋 {{ t('master.processRoute.steps') }}
                </el-button>
                <el-button size="small" type="warning" plain @click="openEditDialog(row)" class="action-btn">
                  ✏️ {{ t('master.common.edit') }}
                </el-button>
                <el-button size="small" type="danger" plain @click="handleDelete(row)" class="action-btn">
                  🗑️
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- Footer Info -->
      <div class="footer-section">
        <div class="result-info">
          <el-icon>📊</el-icon>
          <span>{{ t('master.processRoute.displayCountShort', { n: routeList.length }) }}</span>
        </div>
        <el-pagination 
          v-if="pagination.total > pagination.pageSize"
          v-model:current-page="pagination.currentPage" 
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]" 
          :total="pagination.total" 
          layout="sizes, prev, pager, next"
          @size-change="fetchList" 
          @current-change="fetchList"
          class="compact-pagination"
          size="small"
        />
      </div>

      <RouteEditDialog v-model:visible="showDialog" :mode="dialogMode" :initial-data="editData" @saved="fetchList" />
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessageBox, ElMessage } from 'element-plus'
import { fetchRoutes, deleteRoute } from '@/api/master/processRouterMaster'
import type { RouteItem } from '@/types/master'
import RouteEditDialog from './ProcessRouteEditDialog.vue'

const { t } = useI18n()
const router = useRouter()

/** ステップ編集へ（直接 ProcessRouteStepEditor へ遷移。製品は遷移先で選択） */
const goToSteps = (row: RouteItem) => {
  router.push({
    name: 'RouteStepList',
    params: { route_cd: row.route_cd }
  })
}

const filters = ref({ keyword: '' })
const routeList = ref<RouteItem[]>([])
const loading = ref(false)
const pagination = ref({
  currentPage: 1,
  pageSize: 50,
  total: 0
})

const showDialog = ref(false)
const dialogMode = ref<'add' | 'edit'>('add')
const editData = ref<RouteItem | null>(null)

const fetchList = async () => {
  loading.value = true
  try {
    const result = await fetchRoutes(
      filters.value.keyword,
      pagination.value.currentPage,
      pagination.value.pageSize
    )
    routeList.value = result?.data?.list ?? result?.list ?? []
    pagination.value.total = result?.data?.total ?? result?.total ?? 0
  } catch {
    ElMessage.error(t('master.common.loadError'))
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  dialogMode.value = 'add'
  editData.value = null
  showDialog.value = true
}

const openEditDialog = (row: RouteItem) => {
  dialogMode.value = 'edit'
  editData.value = { ...row }
  showDialog.value = true
}

const handleDelete = async (row: RouteItem) => {
  try {
    await ElMessageBox.confirm(t('master.processRoute.confirmDelete'), t('common.confirm'), { type: 'warning' })
    if (row.id == null) return
    await deleteRoute(row.id)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch {
    // cancelled
  }
}

onMounted(fetchList)
</script>

<style scoped>
.route-master-container {
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
  min-height: 100vh;
}

/* Header */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 14px 20px;
  margin-bottom: 12px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 1.5rem;
}

.main-title {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  color: #fff;
  letter-spacing: 0.5px;
}

.stat-badge {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 4px 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 8px;
}

.stat-number {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.9);
}

.subtitle {
  color: rgba(255, 255, 255, 0.85);
  margin: 4px 0 0;
  font-size: 0.85rem;
}

.add-btn {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  padding: 8px 16px;
  font-weight: 600;
  color: #fff;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.add-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.btn-icon {
  font-size: 0.9rem;
}

/* Search Section */
.search-section {
  background: #fff;
  border-radius: 10px;
  padding: 10px 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.search-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f8fafc;
  border-radius: 8px;
  padding: 0 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s;
}

.search-input-wrapper:focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-icon {
  color: #94a3b8;
}

.search-input :deep(.el-input__wrapper) {
  box-shadow: none !important;
  background: transparent;
}

.search-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  padding: 8px 20px;
  font-weight: 600;
}

/* Table Section */
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
  font-family: 'Consolas', 'Monaco', monospace;
  font-weight: 600;
  color: #667eea;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.name-cell {
  font-weight: 500;
  color: #1e293b;
}

.status-tag {
  border-radius: 12px;
  font-size: 11px;
  padding: 2px 8px;
}

.default-icon {
  color: #10b981;
  font-size: 1rem;
}

.empty-default {
  color: #cbd5e1;
}

.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
  flex-wrap: nowrap;
}

.action-btn {
  padding: 4px 8px;
  font-size: 11px;
  border-radius: 6px;
}

/* Footer */
.footer-section {
  background: #fff;
  border-radius: 10px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.compact-pagination {
  --el-pagination-button-height: 28px;
}

/* Responsive */
@media (max-width: 1024px) {
  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .add-btn {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .route-master-container {
    padding: 8px;
  }
  .page-header {
    padding: 12px;
  }
  .main-title {
    font-size: 1.2rem;
  }
  .title-row {
    flex-wrap: wrap;
  }
  .search-section {
    padding: 8px 12px;
  }
  .search-row {
    flex-direction: column;
  }
  .search-input-wrapper {
    width: 100%;
  }
  .search-btn {
    width: 100%;
  }
  .footer-section {
    flex-direction: column;
    gap: 8px;
  }
  .action-buttons {
    flex-direction: column;
    gap: 4px;
  }
  .action-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .stat-badge {
    display: none;
  }
  .main-title {
    font-size: 1.1rem;
  }
}

/* Table Styles Override */
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

/* Transition */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
