<template>
  <div class="material-issue">
    <div class="page-header">
      <h2>材料出庫指示</h2>
      <p class="subtitle">先入れ先出し(FIFO)・ロット指定出庫・自動引当</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="出庫指示番号">
          <el-input v-model="filters.issue_no" placeholder="出庫指示番号" clearable />
        </el-form-item>
        <el-form-item label="指図番号">
          <el-input v-model="filters.wo_no" placeholder="指図番号" clearable />
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="未出庫" value="pending" />
            <el-option label="一部出庫" value="partial" />
            <el-option label="出庫完了" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleAutoAllocate"><el-icon><Cpu /></el-icon> 自動引当実行</el-button>
      <el-button @click="handleBatchIssue"><el-icon><Box /></el-icon> 一括出庫</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="issueList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="issue_no" label="出庫指示番号" width="140" fixed />
        <el-table-column prop="wo_no" label="指図番号" width="130" />
        <el-table-column prop="material_code" label="材料CD" width="120" />
        <el-table-column prop="material_name" label="材料名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="required_qty" label="所要量" width="80" align="right" />
        <el-table-column prop="allocated_qty" label="引当済" width="80" align="right" />
        <el-table-column prop="issued_qty" label="出庫済" width="80" align="right" />
        <el-table-column prop="lot_no" label="ロット番号" width="130" />
        <el-table-column prop="allocation_rule" label="引当ルール" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.allocation_rule === 'fifo' ? 'FIFO' : 'ロット指定' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleIssue(row)" v-if="row.status !== 'completed'">出庫</el-button>
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
import { Search, Cpu, Box } from '@element-plus/icons-vue'

const loading = ref(false)
const issueList = ref<any[]>([])
const selectedRows = ref<any[]>([])
const filters = reactive({ issue_no: '', wo_no: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { issueList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handleAutoAllocate = () => { ElMessage.info('自動引当処理を実行します') }
const handleBatchIssue = () => { ElMessage.info(`${selectedRows.value.length}件の一括出庫を実行します`) }
const handleView = (row: any) => { ElMessage.info(`出庫指示 ${row.issue_no} の詳細`) }
const handleIssue = (row: any) => { ElMessage.success(`${row.issue_no} の出庫処理を実行しました`) }
const getStatusType = (s: string) => ({ pending: 'info', partial: 'warning', completed: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '未出庫', partial: '一部出庫', completed: '出庫完了' }[s] || s)
</script>

<style scoped>
.material-issue { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
