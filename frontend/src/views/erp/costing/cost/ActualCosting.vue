<template>
  <div class="actual-costing">
    <div class="page-header">
      <h2>実際原価計算</h2>
      <p class="subtitle">実績工数・実績材料費に基づく原価配賦</p>
    </div>

    <!-- フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="対象期間">
          <el-date-picker v-model="filters.period" type="month" placeholder="月選択" value-format="YYYY-MM" />
        </el-form-item>
        <el-form-item label="製造オーダー">
          <el-input v-model="filters.order_no" placeholder="オーダー番号" clearable />
        </el-form-item>
        <el-form-item label="品番">
          <el-select v-model="filters.product_code" placeholder="品番選択" clearable filterable>
            <el-option v-for="p in products" :key="p.cd" :label="`${p.cd} - ${p.name}`" :value="p.cd" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ツールバー -->
    <div class="toolbar">
      <el-button type="primary" @click="handleCalculate">
        <el-icon><DataAnalysis /></el-icon> 原価計算実行
      </el-button>
      <el-button @click="handleExport">
        <el-icon><Download /></el-icon> エクスポート
      </el-button>
    </div>

    <!-- 実際原価一覧 -->
    <el-card shadow="never">
      <el-table :data="costList" v-loading="loading" stripe border>
        <el-table-column prop="order_no" label="製造オーダー" width="140" fixed />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="quantity" label="生産数" width="80" align="right" />
        <el-table-column label="実績材料費" width="120" align="right">
          <template #default="{ row }">¥{{ row.actual_material?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="実績加工費" width="120" align="right">
          <template #default="{ row }">¥{{ row.actual_processing?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="配賦経費" width="100" align="right">
          <template #default="{ row }">¥{{ row.allocated_overhead?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="実際原価" width="130" align="right">
          <template #default="{ row }">
            <span class="total-cost">¥{{ row.total_actual?.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column label="単位原価" width="110" align="right">
          <template #default="{ row }">¥{{ row.unit_cost?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="completion_date" label="完成日" width="110" />
        <el-table-column label="操作" width="100" fixed="right">
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
import { Search, DataAnalysis, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const costList = ref<any[]>([])
const products = ref<{ cd: string; name: string }[]>([])

const filters = reactive({ period: '', order_no: '', product_code: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { costList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleCalculate = () => { ElMessage.success('原価計算を実行しました') }
const handleExport = () => { ElMessage.info('エクスポートしました') }
const handleView = (row: any) => { ElMessage.info(`オーダー ${row.order_no} の詳細`) }
</script>

<style scoped>
.actual-costing { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.total-cost { font-weight: bold; color: #409eff; }
</style>
