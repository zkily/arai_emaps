<template>
  <div class="shipping-list">
    <div class="page-header">
      <h2>出荷指示</h2>
      <p class="subtitle">出荷指図書発行・ピッキングリスト・送り状データ出力</p>
    </div>

    <!-- 検索フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="出荷予定日">
          <el-date-picker v-model="filters.shipping_date" type="date" placeholder="日付選択" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="顧客">
          <el-select v-model="filters.customer_code" placeholder="顧客選択" clearable filterable>
            <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="未出荷" value="pending" />
            <el-option label="ピッキング中" value="picking" />
            <el-option label="出荷完了" value="shipped" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
          <el-button @click="handleReset">リセット</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ツールバー -->
    <div class="toolbar">
      <el-button type="primary" @click="handlePrintPickingList" :disabled="!hasSelection">
        <el-icon><Document /></el-icon> ピッキングリスト発行
      </el-button>
      <el-button type="success" @click="handlePrintShippingOrder" :disabled="!hasSelection">
        <el-icon><Tickets /></el-icon> 出荷指図書発行
      </el-button>
      <el-button @click="handleExportInvoiceData" :disabled="!hasSelection">
        <el-icon><Download /></el-icon> 送り状データ出力
      </el-button>
      <el-divider direction="vertical" />
      <el-button type="warning" @click="handleBatchShip" :disabled="!hasSelection">
        <el-icon><Van /></el-icon> 一括出荷処理
      </el-button>
    </div>

    <!-- 出荷一覧テーブル -->
    <el-card shadow="never">
      <el-table :data="shippingList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="order_no" label="受注番号" width="130" fixed />
        <el-table-column prop="shipping_date" label="出荷予定日" width="110" />
        <el-table-column prop="customer_name" label="顧客名" min-width="150" />
        <el-table-column prop="destination_name" label="納入先" min-width="150" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="quantity" label="出荷数" width="90" align="right" />
        <el-table-column prop="location" label="ロケーション" width="120" />
        <el-table-column prop="carrier" label="配送業者" width="100" />
        <el-table-column prop="status" label="ステータス" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleShip(row)" v-if="row.status !== 'shipped'">出荷</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
          :total="pagination.total" :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper" background />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Document, Tickets, Download, Van } from '@element-plus/icons-vue'

const loading = ref(false)
const shippingList = ref<any[]>([])
const selectedRows = ref<any[]>([])
const customers = ref<{ cd: string; name: string }[]>([])

const filters = reactive({
  shipping_date: '',
  customer_code: '',
  status: '',
})

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const hasSelection = computed(() => selectedRows.value.length > 0)

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try {
    // TODO: API呼び出し
    shippingList.value = []
  } finally {
    loading.value = false
  }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleReset = () => { Object.assign(filters, { shipping_date: '', customer_code: '', status: '' }); handleSearch() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }

const handlePrintPickingList = () => { ElMessage.info(`${selectedRows.value.length}件のピッキングリストを発行`) }
const handlePrintShippingOrder = () => { ElMessage.info(`${selectedRows.value.length}件の出荷指図書を発行`) }
const handleExportInvoiceData = () => { ElMessage.info('送り状データを出力しました') }
const handleBatchShip = async () => {
  await ElMessageBox.confirm(`${selectedRows.value.length}件を出荷完了にしますか？`, '確認')
  ElMessage.success('出荷処理を実行しました')
}
const handleView = (row: any) => { ElMessage.info(`受注 ${row.order_no} の詳細`) }
const handleShip = (row: any) => { ElMessage.success(`受注 ${row.order_no} を出荷完了にしました`) }

const getStatusType = (s: string) => ({ pending: 'warning', picking: 'info', shipped: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '未出荷', picking: 'ピッキング中', shipped: '出荷完了' }[s] || s)
</script>

<style scoped>
.shipping-list { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; align-items: center; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
