<template>
  <div class="inspection-master-container">
    <!-- 页面标题 -->
    <el-card class="header-card" shadow="never">
      <div class="header-content">
        <div class="title-section">
          <h1>材料検品マスタ管理</h1>
          <p>仕入先の材料マスタを管理します</p>
        </div>
        <div class="stats-section">
          <div class="stat-item">
            <span class="stat-number">{{ totalCount }}</span>
            <span class="stat-label">総件数</span>
          </div>
          <div class="stat-item">
            <span class="stat-number">{{ filteredCount || 0 }}</span>
            <span class="stat-label">表示件数</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 搜索和操作栏 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-row">
        <div class="filter-item">
          <label>キーワード検索</label>
          <el-input
            v-model="filters.keyword"
            placeholder="検品CD・検品規格"
            clearable
            @input="handleSearch"
          />
        </div>
        <div class="filter-actions">
          <el-button @click="clearFilters">クリア</el-button>
          <el-button type="primary" @click="showCreateDialog">新規追加</el-button>
          <el-button type="danger" :disabled="selectedRows.length === 0" @click="handleBatchDelete">
            一括削除
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <el-table
        :data="tableData || []"
        v-loading="loading"
        stripe
        highlight-current-row
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
            <el-button size="small" type="primary" link @click.stop="editItem(row)">
              編集
            </el-button>
            <el-button size="small" type="danger" link @click.stop="deleteItem(row.id)">
              削除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalCount || 0"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新規追加/編集ダイアログ -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '材料検品マスタ編集' : '材料検品マスタ新規追加'"
      width="600px"
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

    <!-- 詳細ダイアログ -->
    <el-dialog v-model="detailVisible" title="材料検品マスタ詳細" width="600px">
      <div v-if="selectedItem" class="detail-content">
        <div class="detail-row">
          <label>検品CD:</label>
          <span>{{ selectedItem.inspection_cd }}</span>
        </div>
        <div class="detail-row">
          <label>検品規格:</label>
          <span>{{ selectedItem.inspection_standard }}</span>
        </div>
        <div class="detail-row">
          <label>作成日時:</label>
          <span>{{ formatDateTime(selectedItem.created_at) }}</span>
        </div>
        <div class="detail-row">
          <label>更新日時:</label>
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
import {
  getMaterialInspectionList,
  createMaterialInspection,
  updateMaterialInspection,
  deleteMaterialInspection,
  batchDeleteMaterialInspections,
} from '@/api/material'
import type { MaterialInspectionMaster } from '@/types/material'

// 响应式数据
const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref<MaterialInspectionMaster[]>([])
const totalCount = ref(0)
const selectedRows = ref<MaterialInspectionMaster[]>([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const selectedItem = ref<MaterialInspectionMaster | null>(null)

// 筛选器
const filters = ref({
  keyword: '',
  page: 1,
  pageSize: 20,
})

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
})

// 表单数据
const formData = reactive({
  inspection_cd: '',
  inspection_standard: '',
})

// フォームバリデーションルール
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

// 计算属性
const filteredCount = computed(() => tableData.value?.length || 0)

// 方法
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

// 生命周期
onMounted(() => {
  tableData.value = []
  totalCount.value = 0
  fetchData()
})
</script>

<style scoped>
.inspection-master-container {
  padding: 12px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.header-card,
.filter-card,
.table-card {
  margin-bottom: 12px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: none;
}

.header-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h1 {
  margin: 0 0 4px;
  color: white;
  font-size: 1.6rem;
  font-weight: 600;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.title-section p {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.85rem;
}

.stats-section {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  color: white;
  border-radius: 10px;
  min-width: 90px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-number {
  font-size: 1.4rem;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.stat-label {
  font-size: 0.75rem;
  opacity: 0.9;
  margin-top: 2px;
}

.filter-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.filter-row {
  display: flex;
  gap: 12px;
  align-items: end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.filter-item label {
  font-size: 0.85rem;
  font-weight: 500;
  color: #4a5568;
  margin-bottom: 2px;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.table-card :deep(.el-table) {
  border-radius: 0;
}

.table-card :deep(.el-table__header) {
  background: #f8fafc;
}

.table-card :deep(.el-table th) {
  background: #f8fafc !important;
  color: #4a5568;
  font-weight: 600;
  padding: 12px 8px;
  border-bottom: 2px solid #e2e8f0;
}

.table-card :deep(.el-table td) {
  padding: 10px 8px;
  border-bottom: 1px solid #f0f0f0;
}

.table-card :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #fafbfc;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e2e8f0;
  background: #fafbfc;
}

.detail-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
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

/* 优化对话框样式 */
:deep(.el-dialog) {
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}

:deep(.el-dialog__header) {
  padding: 20px 20px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px 12px 0 0;
}

:deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-dialog__footer) {
  padding: 12px 20px 20px;
  background: #fafbfc;
  border-radius: 0 0 12px 12px;
}

/* 优化表单样式 */
:deep(.el-form-item__label) {
  font-weight: 500;
  color: #4a5568;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

:deep(.el-textarea__inner) {
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 优化按钮样式 */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .inspection-master-container {
    padding: 8px;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .stats-section {
    width: 100%;
    justify-content: space-around;
  }

  .filter-row {
    flex-direction: column;
    gap: 10px;
  }

  .filter-actions {
    justify-content: stretch;
  }

  .filter-actions .el-button {
    flex: 1;
  }
}

@media (max-width: 768px) {
  .inspection-master-container {
    padding: 6px;
  }

  .header-card,
  .filter-card,
  .table-card {
    margin-bottom: 8px;
  }

  .header-card :deep(.el-card__body),
  .filter-card :deep(.el-card__body) {
    padding: 12px 16px;
  }

  .title-section h1 {
    font-size: 1.4rem;
  }

  .stats-section {
    flex-direction: column;
    gap: 8px;
    width: 100%;
  }

  .stat-item {
    min-width: auto;
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
    padding: 10px 12px;
  }

  .filter-row {
    flex-direction: column;
  }

  .detail-content {
    grid-template-columns: 1fr;
  }

  .table-card :deep(.el-table th),
  .table-card :deep(.el-table td) {
    padding: 8px 6px;
    font-size: 0.85rem;
  }
}
</style>
