<template>
  <div class="production-order">
    <div class="page-header">
      <h2>生産オーダー</h2>
      <p class="subtitle">生産オーダー生成・進捗管理・優先順位設定</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="オーダー番号">
          <el-input v-model="filters.order_no" placeholder="オーダー番号" clearable />
        </el-form-item>
        <el-form-item label="品番">
          <el-input v-model="filters.product_code" placeholder="品番" clearable />
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="計画中" value="planned" />
            <el-option label="確定" value="confirmed" />
            <el-option label="製造中" value="in_progress" />
            <el-option label="完了" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleCreate"><el-icon><Plus /></el-icon> 新規オーダー</el-button>
      <el-button @click="handleBatchConfirm"><el-icon><Check /></el-icon> 一括確定</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="orderList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="order_no" label="オーダー番号" width="140" fixed />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="planned_qty" label="計画数量" width="100" align="right" />
        <el-table-column prop="completed_qty" label="完了数量" width="100" align="right" />
        <el-table-column prop="progress" label="進捗" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="優先度" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.priority === 'high' ? 'danger' : row.priority === 'medium' ? 'warning' : 'info'" size="small">
              {{ { high: '高', medium: '中', low: '低' }[row.priority] || row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_date" label="開始日" width="110" />
        <el-table-column prop="due_date" label="完了予定日" width="110" />
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleStart(row)" v-if="row.status === 'confirmed'">開始</el-button>
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
import { Search, Plus, Check } from '@element-plus/icons-vue'

const loading = ref(false)
const orderList = ref<any[]>([])
const selectedRows = ref<any[]>([])
const filters = reactive({ order_no: '', product_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { orderList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handleCreate = () => { ElMessage.info('新規生産オーダー作成画面を開きます') }
const handleBatchConfirm = () => { ElMessage.info(`${selectedRows.value.length}件のオーダーを確定します`) }
const handleView = (row: any) => { ElMessage.info(`オーダー ${row.order_no} の詳細`) }
const handleStart = (row: any) => { ElMessage.success(`オーダー ${row.order_no} を開始しました`) }
const getStatusType = (s: string) => ({ planned: 'info', confirmed: 'primary', in_progress: 'warning', completed: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ planned: '計画中', confirmed: '確定', in_progress: '製造中', completed: '完了' }[s] || s)
</script>

<style scoped>
.production-order { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
