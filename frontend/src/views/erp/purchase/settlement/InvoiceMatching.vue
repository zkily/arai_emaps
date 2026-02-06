<template>
  <div class="invoice-matching">
    <div class="page-header">
      <h2>請求書照合</h2>
      <p class="subtitle">発注・受入・請求書の3点照合・支払依頼データ作成</p>
    </div>

    <!-- サマリーカード -->
    <div class="summary-cards">
      <el-card class="summary-card" shadow="never">
        <div class="summary-value">{{ summary.total }}</div>
        <div class="summary-label">未照合請求書</div>
      </el-card>
      <el-card class="summary-card success" shadow="never">
        <div class="summary-value">{{ summary.matched }}</div>
        <div class="summary-label">照合済（今月）</div>
      </el-card>
      <el-card class="summary-card warning" shadow="never">
        <div class="summary-value">{{ summary.discrepancy }}</div>
        <div class="summary-label">差異あり</div>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <div class="summary-value">¥{{ summary.totalAmount?.toLocaleString() }}</div>
        <div class="summary-label">支払予定額</div>
      </el-card>
    </div>

    <!-- 検索フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="請求書番号">
          <el-input v-model="filters.invoice_no" placeholder="請求書番号" clearable />
        </el-form-item>
        <el-form-item label="仕入先">
          <el-select v-model="filters.supplier_code" placeholder="全て" clearable filterable>
            <el-option v-for="s in suppliers" :key="s.cd" :label="s.name" :value="s.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="未照合" value="pending" />
            <el-option label="照合済" value="matched" />
            <el-option label="差異あり" value="discrepancy" />
            <el-option label="支払済" value="paid" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ツールバー -->
    <div class="toolbar">
      <el-button type="primary" @click="handleAutoMatch" :disabled="!hasPendingSelection">
        <el-icon><Connection /></el-icon> 自動照合
      </el-button>
      <el-button type="success" @click="handleCreatePaymentRequest" :disabled="!hasMatchedSelection">
        <el-icon><Money /></el-icon> 支払依頼作成
      </el-button>
      <el-button @click="handleExport">
        <el-icon><Download /></el-icon> エクスポート
      </el-button>
    </div>

    <!-- 請求書一覧 -->
    <el-card shadow="never">
      <el-table :data="invoiceList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="invoice_no" label="請求書番号" width="140" fixed />
        <el-table-column prop="invoice_date" label="請求日" width="110" />
        <el-table-column prop="supplier_name" label="仕入先" min-width="150" />
        <el-table-column prop="order_no" label="発注番号" width="130" />
        <el-table-column prop="receipt_no" label="受入番号" width="130" />
        <el-table-column prop="invoice_amount" label="請求金額" width="120" align="right">
          <template #default="{ row }">¥{{ row.invoice_amount?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="order_amount" label="発注金額" width="120" align="right">
          <template #default="{ row }">¥{{ row.order_amount?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="difference" label="差異" width="100" align="right">
          <template #default="{ row }">
            <span :class="row.difference !== 0 ? 'text-danger' : ''">
              {{ row.difference !== 0 ? `¥${row.difference?.toLocaleString()}` : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="payment_due" label="支払期限" width="110" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleManualMatch(row)" v-if="row.status === 'pending'">手動照合</el-button>
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
import { Search, Connection, Money, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const invoiceList = ref<any[]>([])
const selectedRows = ref<any[]>([])
const suppliers = ref<{ cd: string; name: string }[]>([])

const summary = reactive({ total: 0, matched: 0, discrepancy: 0, totalAmount: 0 })
const filters = reactive({ invoice_no: '', supplier_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const hasPendingSelection = computed(() => selectedRows.value.some(r => r.status === 'pending'))
const hasMatchedSelection = computed(() => selectedRows.value.some(r => r.status === 'matched'))

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { invoiceList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handleAutoMatch = () => { ElMessage.success('自動照合を実行しました') }
const handleCreatePaymentRequest = () => { ElMessage.success('支払依頼データを作成しました') }
const handleExport = () => { ElMessage.info('エクスポートしました') }
const handleView = (row: any) => { ElMessage.info(`請求書 ${row.invoice_no} の詳細`) }
const handleManualMatch = (row: any) => { ElMessage.info(`請求書 ${row.invoice_no} の手動照合画面を開きます`) }

const getStatusType = (s: string) => ({ pending: 'warning', matched: 'success', discrepancy: 'danger', paid: 'info' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '未照合', matched: '照合済', discrepancy: '差異あり', paid: '支払済' }[s] || s)
</script>

<style scoped>
.invoice-matching { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.summary-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.summary-card { text-align: center; padding: 20px; }
.summary-value { font-size: 28px; font-weight: bold; color: #409eff; }
.summary-card.success .summary-value { color: #67c23a; }
.summary-card.warning .summary-value { color: #e6a23c; }
.summary-label { color: #909399; margin-top: 8px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-danger { color: #f56c6c; font-weight: bold; }
</style>
