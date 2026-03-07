<template>
  <div class="sales-recording">
    <div class="page-header">
      <h2>売上計上</h2>
      <p class="subtitle">出荷基準/検収基準の売上計上・売上伝票作成・赤黒訂正</p>
    </div>

    <!-- 計上基準切替 -->
    <el-card class="basis-card" shadow="never">
      <div class="basis-toggle">
        <span class="basis-label">計上基準:</span>
        <el-radio-group v-model="recordingBasis">
          <el-radio-button value="shipment">出荷基準</el-radio-button>
          <el-radio-button value="acceptance">検収基準</el-radio-button>
        </el-radio-group>
      </div>
    </el-card>

    <!-- 検索フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="期間">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="〜"
            start-placeholder="開始日" end-placeholder="終了日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="顧客">
          <el-select v-model="filters.customer_code" placeholder="全て" clearable filterable>
            <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="未計上" value="pending" />
            <el-option label="計上済" value="recorded" />
            <el-option label="訂正済" value="corrected" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ツールバー -->
    <div class="toolbar">
      <el-button type="primary" @click="handleBatchRecord" :disabled="!hasSelection">
        <el-icon><Check /></el-icon> 一括売上計上
      </el-button>
      <el-button type="warning" @click="handleCorrection" :disabled="!hasSingleSelection">
        <el-icon><EditPen /></el-icon> 赤黒訂正
      </el-button>
      <el-button @click="handleExportSlip" :disabled="!hasSelection">
        <el-icon><Document /></el-icon> 売上伝票出力
      </el-button>
    </div>

    <!-- 売上一覧 -->
    <el-card shadow="never">
      <el-table :data="salesList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="slip_no" label="伝票番号" width="130" fixed />
        <el-table-column prop="order_no" label="受注番号" width="130" />
        <el-table-column prop="shipment_date" label="出荷日" width="110" />
        <el-table-column prop="acceptance_date" label="検収日" width="110" />
        <el-table-column prop="customer_name" label="顧客名" min-width="150" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="quantity" label="数量" width="80" align="right" />
        <el-table-column prop="unit_price" label="単価" width="100" align="right">
          <template #default="{ row }">¥{{ row.unit_price?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="total_amount" label="売上金額" width="120" align="right">
          <template #default="{ row }">¥{{ row.total_amount?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="correction_type" label="訂正" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.correction_type === 'red'" type="danger" size="small">赤</el-tag>
            <el-tag v-else-if="row.correction_type === 'black'" type="info" size="small">黒</el-tag>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Check, EditPen, Document } from '@element-plus/icons-vue'

const loading = ref(false)
const salesList = ref<any[]>([])
const selectedRows = ref<any[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const recordingBasis = ref('shipment')

const filters = reactive({ dateRange: null as string[] | null, customer_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const hasSelection = computed(() => selectedRows.value.length > 0)
const hasSingleSelection = computed(() => selectedRows.value.length === 1)

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { salesList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }

const handleBatchRecord = async () => {
  await ElMessageBox.confirm(`${selectedRows.value.length}件を売上計上しますか？`, '確認')
  ElMessage.success('売上計上を実行しました')
}

const handleCorrection = async () => {
  await ElMessageBox.confirm('赤黒訂正を実行しますか？', '赤黒訂正')
  ElMessage.success('赤黒訂正を実行しました')
}

const handleExportSlip = () => { ElMessage.info('売上伝票を出力しました') }
const handleView = (row: any) => { ElMessage.info(`伝票 ${row.slip_no} の詳細`) }

const getStatusType = (s: string) => ({ pending: 'warning', recorded: 'success', corrected: 'info' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '未計上', recorded: '計上済', corrected: '訂正済' }[s] || s)
</script>

<style scoped>
.sales-recording { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.basis-card { margin-bottom: 16px; }
.basis-toggle { display: flex; align-items: center; gap: 16px; }
.basis-label { font-weight: 500; color: #606266; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
