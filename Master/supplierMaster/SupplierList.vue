<template>
  <div class="supplier-master-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <OfficeBuilding />
            </el-icon>
            仕入先マスタ管理
          </h1>
          <p class="subtitle">仕入先情報の登録・編集・管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ dataList.length }}</div>
            <div class="stat-label">総仕入先数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{dataList.filter(s => s.email).length}}</div>
            <div class="stat-label">メール登録</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能操作区域 -->
    <div class="action-section">
      <!-- 筛选标题 -->
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Filter />
          </el-icon>
          <span>検索・絞り込み</span>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilter" :icon="Refresh" class="clear-btn">
            クリア
          </el-button>
          <el-button type="primary" @click="handleAdd" :icon="Plus" class="add-supplier-btn">
            仕入先追加
          </el-button>
        </div>
      </div>

      <!-- 筛选内容 -->
      <div class="filters-grid">
        <div class="filter-item search-item">
          <label class="filter-label">
            <el-icon>
              <Search />
            </el-icon>
            キーワード検索
          </label>
          <el-input v-model="filters.keyword" placeholder="仕入先CD・名称で検索" clearable @keyup.enter="fetchList"
            class="filter-input">
            <template #suffix>
              <el-icon v-if="filters.keyword" class="search-active">
                <Search />
              </el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-item">
          <el-button type="primary" @click="fetchList" :icon="Search" class="search-btn">
            検索
          </el-button>
        </div>
      </div>
    </div>

    <!-- 仕入先一覧 -->
    <el-card class="table-card">
      <el-table :data="dataList" stripe highlight-current-row class="modern-table">
        <el-table-column label="仕入先CD" prop="supplier_cd" width="120" align="center">
          <template #default="{ row }">
            <div class="supplier-code-cell">
              <el-icon class="code-icon">
                <OfficeBuilding />
              </el-icon>
              <span>{{ row.supplier_cd }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="仕入先名" prop="supplier_name" min-width="180" show-overflow-tooltip />
        <el-table-column label="担当者" prop="contact_person" width="120" show-overflow-tooltip />
        <el-table-column label="電話番号" prop="phone" width="150" show-overflow-tooltip />
        <el-table-column label="メール" prop="email" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons-table">
              <el-button size="small" type="primary" link @click="handleEdit(row)" :icon="Edit">
                編集
              </el-button>
              <el-button size="small" type="danger" link @click="handleDelete(row)" :icon="Delete">
                削除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ページネーション -->
    <div class="pagination-section">
      <el-pagination v-model:current-page="pagination.currentPage" v-model:page-size="pagination.pageSize"
        :total="pagination.total" :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper"
        @update:page-size="handlePageSizeChange" @update:current-page="fetchList" />
    </div>

    <!-- 編集ダイアログ -->
    <SupplierEditDialog :visible="dialogVisible" :editData="editData" @update:visible="dialogVisible = $event"
      @saved="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, OfficeBuilding, Filter, Refresh, Search, Edit, Delete } from '@element-plus/icons-vue'
import request from '@/utils/request'
import SupplierEditDialog from './SupplierEditDialog.vue'

const filters = reactive({ keyword: '' })
const dataList = ref<any[]>([])
const pagination = reactive({ currentPage: 1, pageSize: 20, total: 0 })

const dialogVisible = ref(false)
const editData = ref<any | null>(null)

const fetchList = async () => {
  const res = await request.get('/api/master/suppliers', {
    params: {
      keyword: filters.keyword,
      page: pagination.currentPage,
      pageSize: pagination.pageSize
    }
  })
  dataList.value = res
  pagination.total = res.total
}

const clearFilter = () => {
  filters.keyword = ''
  fetchList()
}

const handlePageSizeChange = () => {
  pagination.currentPage = 1 // ページサイズ変更時は1ページ目に戻す
  fetchList()
}

const handleAdd = () => {
  editData.value = null
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  editData.value = row
  dialogVisible.value = true
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm('この仕入先を削除しますか？', '確認', { type: 'warning' })
    .then(async () => {
      await request.delete(`/api/master/suppliers/${row.id}`)
      ElMessage.success('削除しました')
      fetchList()
    })
    .catch(() => { })
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.supplier-master-container {
  padding: 20px;
  background: linear-gradient(135deg, #fff3e0 0%, #ffcc80 100%);
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  background: white;
  border-radius: 20px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
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
  color: #f39c12;
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
  background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
  color: white;
  padding: 20px;
  border-radius: 16px;
  text-align: center;
  min-width: 120px;
  box-shadow: 0 4px 15px rgba(243, 156, 18, 0.3);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-top: 4px;
}

/* 操作区域 */
.action-section {
  background: white;
  border-radius: 20px;
  padding: 0;
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
  color: #f39c12;
}

.filter-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.clear-btn {
  color: #718096;
  transition: all 0.3s ease;
}

.clear-btn:hover {
  color: #f39c12;
  transform: scale(1.05);
}

.add-supplier-btn {
  background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(243, 156, 18, 0.3);
  transition: all 0.3s ease;
}

.add-supplier-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(243, 156, 18, 0.4);
}

.filters-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 24px;
  padding: 32px;
  align-items: end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
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
  color: #f39c12;
}

.filter-input {
  transition: all 0.3s ease;
}

.filter-input:hover {
  transform: translateY(-1px);
}

.search-active {
  color: #f39c12;
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

.search-btn {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
  transition: all 0.3s ease;
}

.search-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
}

/* 表格区域 */
.table-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: none;
  margin-bottom: 24px;
}

.modern-table {
  border-radius: 12px;
  overflow: hidden;
}

.supplier-code-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.code-icon {
  color: #f39c12;
  font-size: 1rem;
  flex-shrink: 0;
}

.action-buttons-table {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* 分页区域 */
.pagination-section {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }

  .header-stats {
    align-self: stretch;
    justify-content: space-around;
  }
}

@media (max-width: 768px) {
  .supplier-master-container {
    padding: 16px;
  }

  .page-header {
    padding: 24px 20px;
  }

  .main-title {
    font-size: 1.6rem;
  }

  .filter-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    padding: 20px 24px;
  }

  .filter-actions {
    justify-content: stretch;
  }

  .filter-actions>* {
    flex: 1;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 24px 20px;
  }

  .stat-card {
    min-width: auto;
    flex: 1;
  }
}

/* 动画效果 */
.page-header,
.action-section,
.table-card,
.pagination-section {
  animation: fadeInUp 0.6s ease-out;
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

/* Element Plus 样式覆盖 */
:deep(.el-table th) {
  background-color: #f8fafc;
  color: #2d3748;
  font-weight: 600;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f7fafc;
}

:deep(.el-pagination) {
  justify-content: center;
}
</style>
