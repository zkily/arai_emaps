<template>
  <div class="work-order">
    <div class="page-header">
      <h2>製造指図書</h2>
      <p class="subtitle">現品票発行・作業指示書・工程別指示</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="指図番号">
          <el-input v-model="filters.wo_no" placeholder="指図番号" clearable />
        </el-form-item>
        <el-form-item label="品番">
          <el-input v-model="filters.product_code" placeholder="品番" clearable />
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="未発行" value="draft" />
            <el-option label="発行済" value="issued" />
            <el-option label="作業中" value="active" />
            <el-option label="完了" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleCreate"><el-icon><Plus /></el-icon> 新規指図書</el-button>
      <el-button @click="handleBatchPrint"><el-icon><Printer /></el-icon> 一括印刷</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="woList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="wo_no" label="指図番号" width="130" fixed />
        <el-table-column prop="production_order_no" label="生産オーダー" width="140" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="process_name" label="工程" width="100" />
        <el-table-column prop="planned_qty" label="計画数量" width="90" align="right" />
        <el-table-column prop="start_date" label="開始日" width="110" />
        <el-table-column prop="due_date" label="完了予定日" width="110" />
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleIssue(row)" v-if="row.status === 'draft'">発行</el-button>
            <el-button size="small" type="warning" link @click="handlePrintTag(row)">現品票</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
          :total="pagination.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next" background />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus, Printer } from '@element-plus/icons-vue'

const loading = ref(false)
const woList = ref<any[]>([])
const selectedRows = ref<any[]>([])
const filters = reactive({ wo_no: '', product_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { woList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handleCreate = () => { ElMessage.info('新規指図書作成画面を開きます') }
const handleBatchPrint = () => { ElMessage.info(`${selectedRows.value.length}件の指図書を印刷します`) }
const handleView = (row: any) => { ElMessage.info(`指図 ${row.wo_no} の詳細`) }
const handleIssue = (row: any) => { ElMessage.success(`指図 ${row.wo_no} を発行しました`) }
const handlePrintTag = (row: any) => { ElMessage.info(`指図 ${row.wo_no} の現品票を印刷します`) }
const getStatusType = (s: string) => ({ draft: 'info', issued: 'primary', active: 'warning', completed: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ draft: '未発行', issued: '発行済', active: '作業中', completed: '完了' }[s] || s)
</script>

<style scoped>
.work-order { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
