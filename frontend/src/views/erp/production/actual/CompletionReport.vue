<template>
  <div class="completion-report">
    <div class="page-header">
      <h2>完成報告</h2>
      <p class="subtitle">製品入庫登録・歩留まり記録・品質データ連携</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="生産オーダー">
          <el-input v-model="filters.order_no" placeholder="オーダー番号" clearable />
        </el-form-item>
        <el-form-item label="品番">
          <el-input v-model="filters.product_code" placeholder="品番" clearable />
        </el-form-item>
        <el-form-item label="期間">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="〜"
            start-placeholder="開始日" end-placeholder="終了日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleCreate"><el-icon><Plus /></el-icon> 完成報告登録</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="reportList" v-loading="loading" stripe border>
        <el-table-column prop="report_no" label="報告番号" width="130" fixed />
        <el-table-column prop="order_no" label="生産オーダー" width="130" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="planned_qty" label="計画数量" width="90" align="right" />
        <el-table-column prop="completed_qty" label="完成数量" width="90" align="right" />
        <el-table-column prop="defect_qty" label="不良数" width="80" align="right">
          <template #default="{ row }">
            <span :class="row.defect_qty > 0 ? 'text-danger' : ''">{{ row.defect_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="yield_rate" label="歩留まり" width="90" align="right">
          <template #default="{ row }">
            <span :class="row.yield_rate < 95 ? 'text-warning' : 'text-success'">{{ row.yield_rate?.toFixed(1) }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="warehouse_name" label="入庫先" width="100" />
        <el-table-column prop="completion_date" label="完成日" width="110" />
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
const reportList = ref<any[]>([])
const filters = reactive({ order_no: '', product_code: '', dateRange: null as string[] | null })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { reportList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleCreate = () => { ElMessage.info('完成報告登録画面を開きます') }
const handleView = (row: any) => { ElMessage.info(`報告 ${row.report_no} の詳細`) }
</script>

<style scoped>
.completion-report { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-danger { color: #f56c6c; font-weight: bold; }
.text-warning { color: #e6a23c; }
.text-success { color: #67c23a; }
</style>
