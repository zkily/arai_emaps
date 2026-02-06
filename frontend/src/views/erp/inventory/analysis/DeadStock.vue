<template>
  <div class="dead-stock">
    <div class="page-header">
      <h2>長期滞留在庫分析</h2>
      <p class="subtitle">死蔵品（Dead Stock）リストアップ・処分提案</p>
    </div>

    <!-- サマリーカード -->
    <div class="summary-cards">
      <el-card class="summary-card" shadow="never">
        <div class="summary-value">{{ summary.totalItems }}</div>
        <div class="summary-label">滞留品目数</div>
      </el-card>
      <el-card class="summary-card warning" shadow="never">
        <div class="summary-value">¥{{ summary.totalValue?.toLocaleString() }}</div>
        <div class="summary-label">滞留在庫金額</div>
      </el-card>
      <el-card class="summary-card danger" shadow="never">
        <div class="summary-value">{{ summary.over365Days }}</div>
        <div class="summary-label">1年以上滞留</div>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <div class="summary-value">{{ summary.over180Days }}</div>
        <div class="summary-label">180日以上滞留</div>
      </el-card>
    </div>

    <!-- フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="滞留期間">
          <el-select v-model="filters.period" placeholder="期間選択">
            <el-option label="90日以上" value="90" />
            <el-option label="180日以上" value="180" />
            <el-option label="365日以上" value="365" />
          </el-select>
        </el-form-item>
        <el-form-item label="倉庫">
          <el-select v-model="filters.warehouse" placeholder="全て" clearable>
            <el-option v-for="w in warehouses" :key="w.cd" :label="w.name" :value="w.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="カテゴリ">
          <el-select v-model="filters.category" placeholder="全て" clearable>
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 分析実行</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ツールバー -->
    <div class="toolbar">
      <el-button @click="handleExport" :disabled="!hasSelection">
        <el-icon><Download /></el-icon> エクスポート
      </el-button>
      <el-button type="warning" @click="handleDisposalProposal" :disabled="!hasSelection">
        <el-icon><Delete /></el-icon> 処分提案作成
      </el-button>
    </div>

    <!-- 滞留在庫一覧 -->
    <el-card shadow="never">
      <el-table :data="deadStockList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="product_code" label="品番" width="120" fixed />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="category" label="カテゴリ" width="100" />
        <el-table-column prop="warehouse_name" label="倉庫" width="120" />
        <el-table-column prop="location" label="ロケーション" width="100" />
        <el-table-column prop="quantity" label="数量" width="80" align="right" />
        <el-table-column prop="unit_cost" label="単価" width="100" align="right">
          <template #default="{ row }">¥{{ row.unit_cost?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="total_value" label="在庫金額" width="120" align="right">
          <template #default="{ row }">¥{{ row.total_value?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="last_movement_date" label="最終出庫日" width="110" />
        <el-table-column prop="stagnant_days" label="滞留日数" width="100" align="right">
          <template #default="{ row }">
            <el-tag :type="getStagnantType(row.stagnant_days)">{{ row.stagnant_days }}日</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="suggestion" label="処分提案" width="120">
          <template #default="{ row }">
            <span v-if="row.suggestion === 'dispose'" class="text-danger">廃棄</span>
            <span v-else-if="row.suggestion === 'discount'" class="text-warning">値下げ</span>
            <span v-else-if="row.suggestion === 'transfer'" class="text-info">移管</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Download, Delete } from '@element-plus/icons-vue'

const loading = ref(false)
const deadStockList = ref<any[]>([])
const selectedRows = ref<any[]>([])
const warehouses = ref<{ cd: string; name: string }[]>([])
const categories = ref<string[]>([])

const summary = reactive({ totalItems: 0, totalValue: 0, over365Days: 0, over180Days: 0 })
const filters = reactive({ period: '90', warehouse: '', category: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const hasSelection = computed(() => selectedRows.value.length > 0)

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { deadStockList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handleExport = () => { ElMessage.info('エクスポートしました') }
const handleDisposalProposal = () => { ElMessage.info('処分提案を作成しました') }
const handleView = (row: any) => { ElMessage.info(`品番 ${row.product_code} の詳細`) }

const getStagnantType = (days: number) => {
  if (days >= 365) return 'danger'
  if (days >= 180) return 'warning'
  return 'info'
}
</script>

<style scoped>
.dead-stock { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.summary-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.summary-card { text-align: center; padding: 20px; }
.summary-value { font-size: 28px; font-weight: bold; color: #409eff; }
.summary-card.warning .summary-value { color: #e6a23c; }
.summary-card.danger .summary-value { color: #f56c6c; }
.summary-label { color: #909399; margin-top: 8px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-danger { color: #f56c6c; font-weight: bold; }
.text-warning { color: #e6a23c; }
.text-info { color: #909399; }
</style>
