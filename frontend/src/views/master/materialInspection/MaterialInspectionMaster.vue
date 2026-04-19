<template>
  <div class="inspection-master-container">
    <!-- 页面头部（与 ProductList 同构） -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <CircleCheck />
            </el-icon>
            材料検品マスタ
          </h1>
          <p class="subtitle">仕入先の材料マスタを管理します</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ totalCount }}</div>
            <div class="stat-label">総件数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ filteredCount || 0 }}</div>
            <div class="stat-label">表示件数</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选与操作 -->
    <div class="action-section">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Filter />
          </el-icon>
          <span>検索・フィルター</span>
          <div class="filter-inline-summary" v-if="tableData.length || hasActiveFilters">
            <div class="summary-text">
              <el-icon class="summary-icon">
                <InfoFilled />
              </el-icon>
              <span>表示 {{ filteredCount || 0 }} 件</span>
            </div>
            <div class="active-filters" v-if="hasActiveFilters">
              <el-tag
                v-if="filters.keyword"
                closable
                @close="handleClearFilter('keyword')"
                type="primary"
                size="small"
              >
                キーワード: {{ filters.keyword }}
              </el-tag>
            </div>
          </div>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilters" :icon="Refresh" class="clear-btn">クリア</el-button>
          <el-button type="primary" @click="showCreateDialog" :icon="Plus" class="add-product-btn">
            新規追加
          </el-button>
          <el-button
            type="danger"
            :disabled="selectedRows.length === 0"
            :icon="Delete"
            class="batch-delete-btn"
            @click="handleBatchDelete"
          >
            一括削除
          </el-button>
        </div>
      </div>

      <div class="filters-grid">
        <el-row :gutter="16">
          <el-col :lg="10" :md="14" :sm="24">
            <el-form-item label="🔍 キーワード">
              <el-input
                v-model="filters.keyword"
                placeholder="検品CD・検品規格"
                clearable
                style="width: 100%"
                @input="handleSearch"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-table
      :data="tableData || []"
      v-loading="loading"
      stripe
      border
      highlight-current-row
      :style="{ width: '100%' }"
      height="600"
      :header-cell-style="{ background: '#f5f7fa', fontWeight: 'bold' }"
      :cell-style="{ padding: '4px 8px' }"
      :scrollbar-always-on="true"
      @selection-change="handleSelectionChange"
      @row-click="showDetail"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column prop="inspection_cd" label="検品CD" width="150" align="center" />
      <el-table-column
        prop="inspection_standard"
        label="検品規格"
        min-width="300"
        show-overflow-tooltip
      />
      <el-table-column prop="created_at" label="作成日時" width="180" align="center">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新日時" width="180" align="center">
        <template #default="{ row }">
          {{ formatDateTime(row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" fixed="right" width="150" align="center">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click.stop="editItem(row)">編集</el-button>
          <el-button size="small" type="danger" link @click.stop="deleteItem(row.id)">削除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="totalCount || 0"
      layout="total, sizes, prev, pager, next, jumper"
      class="pagination"
      @size-change="handlePageSizeChange"
      @current-change="handlePageChange"
    />

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '材料検品マスタ編集' : '材料検品マスタ新規追加'"
      width="600px"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
        <el-form-item label="材料検品CD" prop="inspection_cd">
          <el-input
            v-model="formData.inspection_cd"
            placeholder="材料検品CDを入力してください"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="材料検品規格" prop="inspection_standard">
          <el-input
            v-model="formData.inspection_standard"
            type="textarea"
            :rows="4"
            placeholder="材料検品規格を入力してください"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          {{ isEdit ? '更新' : '作成' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailVisible"
      title="材料検品マスタ詳細"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedItem" class="detail-content">
        <div class="detail-row">
          <label>検品CD</label>
          <span>{{ selectedItem.inspection_cd }}</span>
        </div>
        <div class="detail-row detail-row--block">
          <label>検品規格</label>
          <span>{{ selectedItem.inspection_standard }}</span>
        </div>
        <div class="detail-row">
          <label>作成日時</label>
          <span>{{ formatDateTime(selectedItem.created_at) }}</span>
        </div>
        <div class="detail-row">
          <label>更新日時</label>
          <span>{{ formatDateTime(selectedItem.updated_at) }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">閉じる</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { CircleCheck, Filter, Refresh, Plus, Delete, InfoFilled } from '@element-plus/icons-vue'
import {
  getMaterialInspectionList,
  createMaterialInspection,
  updateMaterialInspection,
  deleteMaterialInspection,
  batchDeleteMaterialInspections,
} from '@/api/material'
import type { MaterialInspectionMaster } from '@/types/material'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref<MaterialInspectionMaster[]>([])
const totalCount = ref(0)
const selectedRows = ref<MaterialInspectionMaster[]>([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const selectedItem = ref<MaterialInspectionMaster | null>(null)

const filters = ref({
  keyword: '',
  page: 1,
  pageSize: 20,
})

const pagination = ref({
  page: 1,
  pageSize: 20,
})

const formData = reactive({
  inspection_cd: '',
  inspection_standard: '',
})

const formRules: FormRules = {
  inspection_cd: [
    { required: true, message: '検品CDを入力してください', trigger: 'blur' },
    { min: 1, max: 50, message: '検品CDは1〜3文字で入力してください', trigger: 'blur' },
  ],
  inspection_standard: [
    { required: true, message: '検品規格を入力してください', trigger: 'blur' },
    { min: 1, max: 500, message: '検品規格は1〜50文字で入力してください', trigger: 'blur' },
  ],
}

const formRef = ref<FormInstance>()

const filteredCount = computed(() => tableData.value?.length || 0)

const hasActiveFilters = computed(() => Boolean(filters.value.keyword?.trim()))

const handleClearFilter = (key: 'keyword') => {
  if (key === 'keyword') filters.value.keyword = ''
  pagination.value.page = 1
  fetchData()
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      keyword: filters.value.keyword,
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
    }
    const result = await getMaterialInspectionList(params)
    const data = result?.data
    const list = Array.isArray(data?.list) ? data.list : (result as any)?.list
    const total = data?.total ?? (result as any)?.total ?? 0
    tableData.value = list ?? []
    totalCount.value = total
  } catch (error: any) {
    console.error('データの取得に失敗しました:', error)
    ElMessage.error(`データの取得に失敗しました: ${error?.message ?? error}`)
    tableData.value = []
    totalCount.value = 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.value.page = 1
  fetchData()
}

const clearFilters = () => {
  filters.value = { keyword: '', page: 1, pageSize: 20 }
  pagination.value.page = 1
  fetchData()
}

const handleSelectionChange = (selection: MaterialInspectionMaster[]) => {
  selectedRows.value = selection
}

const showCreateDialog = () => {
  isEdit.value = false
  formData.inspection_cd = ''
  formData.inspection_standard = ''
  dialogVisible.value = true
}

const editItem = (row: MaterialInspectionMaster) => {
  isEdit.value = true
  formData.inspection_cd = row.inspection_cd
  formData.inspection_standard = row.inspection_standard
  selectedItem.value = row
  dialogVisible.value = true
}

const showDetail = (row: MaterialInspectionMaster) => {
  selectedItem.value = row
  detailVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitLoading.value = true

    if (isEdit.value && selectedItem.value) {
      await updateMaterialInspection(selectedItem.value.id, formData)
      ElMessage.success('更新しました')
    } else {
      await createMaterialInspection(formData)
      ElMessage.success('作成しました')
    }

    dialogVisible.value = false
    fetchData()
  } catch (error: any) {
    console.error('送信に失敗しました:', error)
    ElMessage.error(`送信に失敗しました: ${error.message}`)
  } finally {
    submitLoading.value = false
  }
}

const deleteItem = async (id: number) => {
  try {
    await ElMessageBox.confirm('この検品CDを削除しますか？', '削除確認', {
      type: 'warning',
      confirmButtonText: 'はい',
      cancelButtonText: 'キャンセル',
    })

    await deleteMaterialInspection(id)
    ElMessage.success('削除しました')
    fetchData()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('削除に失敗しました:', error)
      ElMessage.error(`削除に失敗しました: ${error.message}`)
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('削除するレコードを選択してください')
    return
  }

  try {
    await ElMessageBox.confirm(
      `選択した ${selectedRows.value.length} 件の検品CDを削除しますか？`,
      '一括削除確認',
      {
        type: 'warning',
        confirmButtonText: 'はい',
        cancelButtonText: 'キャンセル',
      },
    )

    const ids = selectedRows.value.map((row) => row.id)
    await batchDeleteMaterialInspections(ids)
    ElMessage.success(`${ids.length} 件のレコードを削除しました`)
    fetchData()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('一括削除に失敗しました:', error)
      ElMessage.error(`一括削除に失敗しました: ${error.message}`)
    }
  }
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
  fetchData()
}

const handlePageSizeChange = (size: number) => {
  pagination.value.pageSize = size
  pagination.value.page = 1
  fetchData()
}

const formatDateTime = (dateTime: string | undefined) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

onMounted(() => {
  tableData.value = []
  totalCount.value = 0
  fetchData()
})
</script>

<style scoped>
/* 与 ProductList.vue 对齐的页面骨架与配色 */
.inspection-master-container {
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
  padding: 0;
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
  flex-wrap: wrap;
}

.filter-icon {
  font-size: 1rem;
  color: #667eea;
}

.filter-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
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

.add-product-btn {
  border: none;
  border-radius: 8px;
  padding: 7px 12px !important;
  font-weight: 600;
  font-size: 12px !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.25);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    filter 0.2s ease;
}

.add-product-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
}

.batch-delete-btn {
  border: none !important;
  border-radius: 8px;
  padding: 7px 12px !important;
  font-weight: 600;
  font-size: 12px !important;
  background: linear-gradient(135deg, #f87171 0%, #dc2626 100%) !important;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.25);
  color: #fff !important;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.batch-delete-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.35);
  background: linear-gradient(135deg, #fb7185 0%, #ef4444 100%) !important;
}

.batch-delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.filters-grid {
  padding: 10px 14px;
  background: white;
}

.filters-grid :deep(.el-form-item) {
  margin-bottom: 8px;
}

.filters-grid :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  padding-bottom: 2px;
}

.filters-grid :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px #e2e8f0;
}

.filters-grid :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea;
}

.summary-text {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 0;
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 500;
}

.summary-icon {
  color: #667eea;
  font-size: 14px;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.active-filters :deep(.el-tag) {
  border-radius: 4px;
  font-size: 11px;
  padding: 0 6px;
  height: 22px;
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
  font-size: 12px;
}

:deep(.el-table .el-table__header th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
  font-weight: 600;
  color: #334155;
  font-size: 12px;
  padding: 6px 8px !important;
}

:deep(.el-table .el-table__cell) {
  padding: 4px 6px !important;
}

:deep(.el-table .cell) {
  line-height: 1.5;
}

:deep(.el-table .el-button--small) {
  padding: 4px 8px;
  font-size: 11px;
  border-radius: 5px;
}

.filter-inline-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 12px;
  border-left: 1px solid #e2e8f0;
  flex-wrap: wrap;
}

.filter-inline-summary .summary-text {
  margin-bottom: 0;
}

.pagination {
  margin-top: 8px;
  text-align: center;
}

.pagination :deep(.el-pager li) {
  border-radius: 6px;
  font-size: 12px;
  min-width: 28px;
  height: 28px;
  line-height: 28px;
}

.pagination :deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 3px solid #667eea;
}

.detail-row--block {
  flex-direction: column;
  gap: 6px;
}

.detail-row label {
  font-weight: 600;
  color: #4a5568;
  min-width: 90px;
  font-size: 0.9rem;
}

.detail-row span {
  color: #2d3748;
  flex: 1;
  word-break: break-word;
  font-size: 0.9rem;
}

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
  .inspection-master-container {
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

  .stat-card {
    min-width: 60px;
    padding: 5px 8px;
  }

  .stat-number {
    font-size: 1.1rem;
  }
}

.page-header,
.action-section {
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
