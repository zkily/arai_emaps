<template>
  <div class="inspection-master-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <CircleCheck />
            </el-icon>
            材料検品マスタ
          </h1>
          <p class="subtitle">仕入先材料の検品基準を登録・管理します</p>
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

    <!-- 操作栏 -->
    <div class="toolbar-section">
      <div class="toolbar-left">
        <el-icon class="toolbar-icon"><Tickets /></el-icon>
        <span class="toolbar-title">検品基準一覧</span>
        <span class="toolbar-count">全 {{ totalCount }} 件</span>
      </div>
      <div class="toolbar-actions">
        <el-button type="primary" @click="showCreateDialog" :icon="Plus" class="add-btn">
          新規追加
        </el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <el-table
        :data="tableData || []"
        v-loading="loading"
        stripe
        highlight-current-row
        class="modern-table"
        :style="{ width: '100%' }"
        :header-cell-style="{ background: '#f8fafc', fontWeight: '600', color: '#334155' }"
        @row-click="showDetail"
      >
        <el-table-column prop="inspection_cd" label="検品CD" width="140" align="center">
          <template #default="{ row }">
            <div class="code-cell">
              <el-icon class="code-icon"><Tickets /></el-icon>
              <span>{{ row.inspection_cd }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          prop="inspection_standard"
          label="検品規格"
          min-width="280"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <span class="standard-cell">{{ row.inspection_standard }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="作成日時" width="170" align="center">
          <template #default="{ row }">
            <span class="datetime-cell">{{ formatDateTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新日時" width="170" align="center">
          <template #default="{ row }">
            <span class="datetime-cell">{{ formatDateTime(row.updated_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" type="primary" link :icon="Edit" @click.stop="editItem(row)">
                編集
              </el-button>
              <el-button size="small" type="danger" link :icon="Delete" @click.stop="deleteItem(row.id)">
                削除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="pagination-section">
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

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '材料検品マスタ編集' : '材料検品マスタ新規追加'"
      width="560px"
      destroy-on-close
      :close-on-click-modal="false"
      class="form-dialog"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px" class="form-body">
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
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading" class="submit-btn">
          {{ isEdit ? '更新' : '作成' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailVisible"
      title="材料検品マスタ詳細"
      width="560px"
      :close-on-click-modal="false"
      class="detail-dialog"
    >
      <div v-if="selectedItem" class="detail-content">
        <div class="detail-row">
          <label>検品CD</label>
          <span class="detail-code">{{ selectedItem.inspection_cd }}</span>
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
import { CircleCheck, Plus, Delete, Edit, Tickets } from '@element-plus/icons-vue'
import {
  getMaterialInspectionList,
  createMaterialInspection,
  updateMaterialInspection,
  deleteMaterialInspection,
} from '@/api/material'
import type { MaterialInspectionMaster } from '@/types/material'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref<MaterialInspectionMaster[]>([])
const totalCount = ref(0)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const selectedItem = ref<MaterialInspectionMaster | null>(null)

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
    { min: 1, max: 50, message: '検品CDは1〜50文字で入力してください', trigger: 'blur' },
  ],
  inspection_standard: [
    { required: true, message: '検品規格を入力してください', trigger: 'blur' },
    { min: 1, max: 500, message: '検品規格は1〜500文字で入力してください', trigger: 'blur' },
  ],
}

const formRef = ref<FormInstance>()

const filteredCount = computed(() => tableData.value?.length || 0)

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
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
.inspection-master-container {
  padding: 6px;
  background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  border-radius: 14px;
  padding: 12px 18px;
  margin-bottom: 8px;
  box-shadow: 0 6px 24px rgba(71, 85, 105, 0.28);
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
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0 0 3px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: 0.02em;
}

.title-icon {
  font-size: 1.35rem;
  color: rgba(255, 255, 255, 0.92);
}

.subtitle {
  color: rgba(255, 255, 255, 0.78);
  margin: 0;
  font-size: 0.82rem;
}

.header-stats {
  display: flex;
  gap: 8px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(10px);
  color: white;
  padding: 7px 14px;
  border-radius: 12px;
  text-align: center;
  min-width: 76px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  transition: all 0.2s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.24);
  transform: translateY(-1px);
}

.stat-number {
  font-size: 1.45rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.7rem;
  opacity: 0.9;
  margin-top: 3px;
  white-space: nowrap;
}

.toolbar-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border-radius: 12px;
  padding: 10px 16px;
  margin-bottom: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-icon {
  font-size: 1.1rem;
  color: #64748b;
}

.toolbar-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #334155;
}

.toolbar-count {
  font-size: 0.78rem;
  color: #94a3b8;
  padding-left: 8px;
  border-left: 1px solid #e2e8f0;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.add-btn {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%) !important;
  border: none !important;
  border-radius: 10px !important;
  padding: 8px 16px !important;
  font-weight: 600;
  font-size: 13px !important;
  box-shadow: 0 3px 10px rgba(71, 85, 105, 0.3);
  transition: all 0.2s ease;
}

.add-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 5px 14px rgba(71, 85, 105, 0.38);
}

.table-card {
  border-radius: 12px;
  box-shadow: 0 2px 14px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  margin-bottom: 8px;
  overflow: hidden;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.code-cell {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  background: #f1f5f9;
  padding: 3px 8px;
  border-radius: 6px;
}

.code-icon {
  color: #64748b;
  font-size: 13px;
}

.standard-cell {
  color: #334155;
  font-size: 12px;
  line-height: 1.5;
}

.datetime-cell {
  font-size: 11px;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}

.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
}

:deep(.modern-table) {
  font-size: 12px;
}

:deep(.modern-table .el-table__header th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
  font-weight: 600;
  color: #334155;
  font-size: 12px;
  padding: 10px 8px !important;
  border-bottom: 2px solid #e2e8f0 !important;
}

:deep(.modern-table .el-table__row) {
  cursor: pointer;
  transition: background 0.15s ease;
}

:deep(.modern-table .el-table__row:hover > td) {
  background: #f8fafc !important;
}

:deep(.modern-table .el-table__cell) {
  padding: 8px 6px !important;
}

:deep(.modern-table .el-button--small) {
  padding: 4px 8px;
  font-size: 11px;
  border-radius: 6px;
}

.pagination-section {
  background: white;
  border-radius: 12px;
  padding: 10px 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  text-align: center;
}

:deep(.el-pagination) {
  justify-content: center;
}

:deep(.el-pager li) {
  border-radius: 8px;
  font-size: 12px;
  min-width: 30px;
  height: 30px;
  line-height: 30px;
}

:deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  background: #f8fafc;
  border-radius: 10px;
  border-left: 3px solid #64748b;
}

.detail-row--block {
  flex-direction: column;
  gap: 6px;
}

.detail-row label {
  font-weight: 600;
  color: #64748b;
  min-width: 90px;
  font-size: 0.85rem;
}

.detail-row span {
  color: #1e293b;
  flex: 1;
  word-break: break-word;
  font-size: 0.9rem;
  line-height: 1.5;
}

.detail-code {
  font-family: 'Monaco', 'Menlo', monospace;
  font-weight: 600;
  color: #475569 !important;
}

:deep(.form-dialog .el-dialog__header) {
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 14px;
}

:deep(.form-dialog .el-dialog__title) {
  font-weight: 700;
  color: #1e293b;
}

.submit-btn {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%) !important;
  border: none !important;
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
    padding: 10px 14px;
    border-radius: 12px;
  }

  .main-title {
    font-size: 1.2rem;
  }

  .toolbar-section {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
    padding: 10px 12px;
  }

  .toolbar-actions {
    justify-content: flex-end;
  }

  .stat-card {
    min-width: 64px;
    padding: 6px 10px;
  }

  .stat-number {
    font-size: 1.2rem;
  }
}

.page-header,
.toolbar-section,
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
