<template>
  <div class="serial-number-management">
    <div class="page-header">
      <h2>製番管理</h2>
      <p class="subtitle">個別受注生産向け：オーダー別原価管理用の番号発行</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="製番">
          <el-input v-model="filters.serial_no" placeholder="製番" clearable />
        </el-form-item>
        <el-form-item label="受注番号">
          <el-input v-model="filters.order_no" placeholder="受注番号" clearable />
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="発番済" value="issued" />
            <el-option label="製造中" value="in_progress" />
            <el-option label="完了" value="completed" />
            <el-option label="クローズ" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleCreate"><el-icon><Plus /></el-icon> 新規製番発行</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="serialList" v-loading="loading" stripe border>
        <el-table-column prop="serial_no" label="製番" width="130" fixed />
        <el-table-column prop="order_no" label="受注番号" width="130" />
        <el-table-column prop="customer_name" label="顧客名" min-width="130" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="quantity" label="数量" width="80" align="right" />
        <el-table-column prop="material_cost" label="材料費" width="110" align="right">
          <template #default="{ row }">¥{{ row.material_cost?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="labor_cost" label="加工費" width="110" align="right">
          <template #default="{ row }">¥{{ row.labor_cost?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="total_cost" label="合計原価" width="120" align="right">
          <template #default="{ row }"><strong>¥{{ row.total_cost?.toLocaleString() }}</strong></template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
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
import { Search, Plus } from '@element-plus/icons-vue'

const loading = ref(false)
const serialList = ref<any[]>([])
const filters = reactive({ serial_no: '', order_no: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { serialList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleCreate = () => { ElMessage.info('新規製番発行画面を開きます') }
const handleView = (row: any) => { ElMessage.info(`製番 ${row.serial_no} の詳細`) }
const getStatusType = (s: string) => ({ issued: 'primary', in_progress: 'warning', completed: 'success', closed: 'info' }[s] || 'info')
const getStatusLabel = (s: string) => ({ issued: '発番済', in_progress: '製造中', completed: '完了', closed: 'クローズ' }[s] || s)
</script>

<style scoped>
.serial-number-management { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
