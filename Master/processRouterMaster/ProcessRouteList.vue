<template>
  <transition name="fade-slide" mode="out-in">
    <div class="route-master-container" v-if="true">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <div class="title-section">
            <h1 class="main-title">
              <el-icon class="title-icon">🛠️</el-icon>
              工程ルート管理
            </h1>
            <p class="subtitle">工程ルートの登録・編集・管理を行います</p>
          </div>
          <div class="header-stats">
            <div class="stat-card">
              <div class="stat-number">{{ routeList.length }}</div>
              <div class="stat-label">総ルート数</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作区/筛选区 -->
      <div class="action-section">
        <div class="filter-header">
          <div class="filter-title">
            <el-icon class="filter-icon">🔍</el-icon>
            <span>検索・絞り込み</span>
          </div>
          <div class="filter-actions">
            <el-button type="primary" @click="openAddDialog" class="add-btn">工程ルート追加</el-button>
          </div>
        </div>
        <div class="filters-grid">
          <div class="filter-item search-item">
            <label class="filter-label">
              <el-icon>🔍</el-icon>
              キーワード検索
            </label>
            <el-input v-model="filters.keyword" placeholder="コード／名称で検索" clearable @keyup.enter="fetchList"
              class="filter-input">
              <template #suffix>
                <el-icon v-if="filters.keyword" class="search-active">🔍</el-icon>
              </template>
            </el-input>
          </div>
        </div>
      </div>

      <!-- 表格卡片 -->
      <el-card class="table-card">
        <el-table :data="routeList" border stripe highlight-current-row v-loading="loading" class="modern-table">
          <el-table-column label="🆔 ルートCD" prop="route_cd" width="110" align="center" />
          <el-table-column label="📛 ルート名称" prop="route_name" min-width="80" />
          <el-table-column label="📝 説明" prop="description" min-width="160" />
          <el-table-column label="✅ デフォルト" prop="is_default" width="120" align="center">
            <template #default="{ row }">
              <el-tag type="success" v-if="row.is_default">✔</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="🛠️ 操作" width="300" align="center">
            <template #default="{ row }">
              <div class="action-buttons-table">
                <el-button size="small" icon="Edit" @click="goToSteps(row)" plain>ステップ編集</el-button>
                <el-button size="small" icon="EditPen" @click="openEditDialog(row)">編集</el-button>
                <el-button size="small" type="danger" icon="Delete" @click="handleDelete(row)">削除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 结果统计 -->
      <div class="result-section">
        <div class="result-info">
          表示件数: {{ routeList.length }}
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="pagination.total > pagination.pageSize">
        <el-pagination v-model:current-page="pagination.currentPage" v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]" :total="pagination.total" layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchList" @current-change="fetchList" />
      </div>

      <!-- 弹窗 -->
      <RouteEditDialog v-model:visible="showDialog" :mode="dialogMode" :initial-data="editData" @saved="fetchList" />
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { fetchRoutes, deleteRoute } from '@/api/master/processRouterMaster'
import type { RouteItem } from '@/types/master'
import RouteEditDialog from './ProcessRouteEditDialog.vue'

const router = useRouter()

const filters = ref({ keyword: '' })
const routeList = ref<RouteItem[]>([])
const loading = ref(false)
const pagination = ref({
  currentPage: 1,
  pageSize: 50, // 每页显示50条
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
    routeList.value = result.list
    pagination.value.total = result.total
  } catch {
    ElMessage.error('工程ルート取得失敗')
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
    await ElMessageBox.confirm('このルートを削除してもよろしいですか？', '確認', { type: 'warning' })
    await deleteRoute(row.id)
    ElMessage.success('削除成功')
    fetchList()
  } catch {
    // cancelled
  }
}

const goToSteps = (row: RouteItem) => {
  router.push({ name: 'RouteStepList', params: { route_cd: row.route_cd } })
}

onMounted(fetchList)
</script>

<style scoped>
.route-master-container {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.page-header {
  background: white;
  border-radius: 20px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.title-section {
  flex: 1;
}

.main-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 8px;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 1.8rem;
  color: #2980b9;
}

.subtitle {
  color: #7f8c8d;
  margin: 0;
  font-size: 1rem;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: linear-gradient(135deg, #2980b9 0%, #27ae60 100%);
  color: white;
  padding: 20px;
  border-radius: 16px;
  text-align: center;
  min-width: 120px;
  box-shadow: 0 4px 15px rgba(41, 128, 185, 0.2);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-top: 4px;
}

.action-section {
  background: white;
  border-radius: 20px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e2e8f0;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #2d3748;
}

.filter-icon {
  font-size: 1.3rem;
  color: #2980b9;
}

.filter-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.add-btn {
  background: linear-gradient(135deg, #27ae60 0%, #2980b9 100%);
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(41, 128, 185, 0.18);
  transition: all 0.3s;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(41, 128, 185, 0.23);
}

.filters-grid {
  display: grid;
  grid-template-columns: 2fr;
  gap: 24px;
  padding: 32px;
  background: white;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-item {
  grid-column: span 1;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  color: #4a5568;
  margin-bottom: 4px;
}

.filter-label .el-icon {
  font-size: 1rem;
  color: #2980b9;
}

.filter-input {
  transition: all 0.3s;
}

.filter-input:hover {
  transform: translateY(-1px);
}

.search-active {
  color: #27ae60;
  animation: pulse 2s infinite;
}

@keyframes pulse {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }
}

.table-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: none;
  margin-bottom: 16px;
}

.modern-table {
  border-radius: 12px;
  overflow: hidden;
}

.action-buttons-table {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.result-section {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.result-info {
  color: #7f8c8d;
  font-size: 0.9rem;
}

@media (max-width:1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }

  .header-stats {
    align-self: stretch;
    justify-content: space-around;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .search-item {
    grid-column: span 1;
  }
}

@media (max-width:768px) {
  .route-master-container {
    padding: 12px;
  }

  .page-header {
    padding: 18px 10px;
  }

  .main-title {
    font-size: 1.5rem;
  }

  .filter-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    padding: 16px 10px;
  }

  .filter-actions>* {
    flex: 1;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 14px;
    padding: 14px 8px;
  }

  .search-item {
    grid-column: span 1;
  }

  .stat-card {
    min-width: auto;
    flex: 1;
  }
}

@media (max-width:480px) {
  .main-title {
    font-size: 1.2rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

@media (prefers-color-scheme: dark) {
  .route-master-container {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  }

  .page-header,
  .action-section,
  .table-card,
  .result-section {
    background: rgba(45, 55, 72, 0.88);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }

  .main-title {
    color: #e2e8f0;
  }

  .subtitle,
  .result-info {
    color: #a0aec0;
  }
}

.table-card,
.page-header,
.action-section,
.result-section {
  animation: fadeInUp 0.6s;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

:deep(.el-table th) {
  background-color: #f8fafc;
  color: #2d3748;
  font-weight: 600;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f7fafc;
}

:deep(.el-tag) {
  border-radius: 12px;
  font-weight: 500;
}
</style>
