<template>
  <div class="credit-management">
    <div class="page-header">
      <h2>与信管理</h2>
      <p class="subtitle">受注時の与信限度額チェック・アラート・与信枠設定</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="顧客">
          <el-select v-model="filters.customer_code" placeholder="顧客選択" clearable filterable>
            <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="正常" value="normal" />
            <el-option label="警告" value="warning" />
            <el-option label="超過" value="exceeded" />
            <el-option label="取引停止" value="suspended" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleSetLimit">
        <el-icon><Setting /></el-icon> 与信限度額設定
      </el-button>
      <el-button type="warning" @click="handleAlertList">
        <el-icon><Warning /></el-icon> アラート一覧
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="creditList" v-loading="loading" stripe border>
        <el-table-column prop="customer_code" label="顧客CD" width="100" fixed />
        <el-table-column prop="customer_name" label="顧客名" min-width="150" />
        <el-table-column prop="credit_limit" label="与信限度額" width="130" align="right">
          <template #default="{ row }">¥{{ row.credit_limit?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="current_balance" label="売掛残高" width="130" align="right">
          <template #default="{ row }">¥{{ row.current_balance?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="pending_orders" label="受注残" width="120" align="right">
          <template #default="{ row }">¥{{ row.pending_orders?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="usage_rate" label="使用率" width="100" align="right">
          <template #default="{ row }">
            <el-progress :percentage="row.usage_rate" :color="getUsageColor(row.usage_rate)" :stroke-width="8" />
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
            <el-button size="small" type="warning" link @click="handleEdit(row)">編集</el-button>
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
import { Search, Setting, Warning } from '@element-plus/icons-vue'

const loading = ref(false)
const creditList = ref<any[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ customer_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { creditList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSetLimit = () => { ElMessage.info('与信限度額設定画面を開きます') }
const handleAlertList = () => { ElMessage.info('アラート一覧を表示します') }
const handleView = (row: any) => { ElMessage.info(`${row.customer_name} の与信詳細`) }
const handleEdit = (row: any) => { ElMessage.info(`${row.customer_name} の与信設定を編集`) }
const getUsageColor = (rate: number) => rate >= 90 ? '#f56c6c' : rate >= 70 ? '#e6a23c' : '#67c23a'
const getStatusType = (s: string) => ({ normal: 'success', warning: 'warning', exceeded: 'danger', suspended: 'info' }[s] || 'info')
const getStatusLabel = (s: string) => ({ normal: '正常', warning: '警告', exceeded: '超過', suspended: '取引停止' }[s] || s)
</script>

<style scoped>
.credit-management { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
