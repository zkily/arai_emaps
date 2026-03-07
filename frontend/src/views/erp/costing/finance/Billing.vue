<template>
  <div class="billing">
    <div class="page-header">
      <h2>請求管理（AR）</h2>
      <p class="subtitle">締め請求書発行・入金消込</p>
    </div>

    <!-- サマリー -->
    <div class="summary-cards">
      <el-card class="summary-card" shadow="never">
        <div class="summary-value">¥{{ summary.totalReceivables?.toLocaleString() }}</div>
        <div class="summary-label">売掛金残高</div>
      </el-card>
      <el-card class="summary-card success" shadow="never">
        <div class="summary-value">¥{{ summary.thisMonthBilled?.toLocaleString() }}</div>
        <div class="summary-label">今月請求額</div>
      </el-card>
      <el-card class="summary-card warning" shadow="never">
        <div class="summary-value">¥{{ summary.overdueAmount?.toLocaleString() }}</div>
        <div class="summary-label">延滞金額</div>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <div class="summary-value">{{ summary.overdueCount }}</div>
        <div class="summary-label">延滞件数</div>
      </el-card>
    </div>

    <!-- タブ -->
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 請求書発行 -->
      <el-tab-pane label="請求書発行" name="billing">
        <div class="toolbar">
          <el-button type="primary" @click="handleCreateBilling">
            <el-icon><Document /></el-icon> 締め請求書作成
          </el-button>
          <el-button @click="handlePrintBilling" :disabled="!hasSelection">
            <el-icon><Printer /></el-icon> 請求書印刷
          </el-button>
        </div>

        <el-table :data="billingList" v-loading="loading" stripe border @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="50" fixed />
          <el-table-column prop="invoice_no" label="請求書番号" width="130" fixed />
          <el-table-column prop="billing_date" label="請求日" width="110" />
          <el-table-column prop="customer_name" label="顧客名" min-width="150" />
          <el-table-column prop="billing_amount" label="請求金額" width="130" align="right">
            <template #default="{ row }">¥{{ row.billing_amount?.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column prop="tax_amount" label="消費税" width="100" align="right">
            <template #default="{ row }">¥{{ row.tax_amount?.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column prop="total_amount" label="合計" width="130" align="right">
            <template #default="{ row }">
              <span class="font-bold">¥{{ row.total_amount?.toLocaleString() }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="due_date" label="入金期限" width="110" />
          <el-table-column prop="status" label="ステータス" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getBillingStatusType(row.status)">{{ getBillingStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleViewBilling(row)">詳細</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 入金消込 -->
      <el-tab-pane label="入金消込" name="receipt">
        <div class="toolbar">
          <el-button type="primary" @click="handleAutoReconcile">
            <el-icon><Connection /></el-icon> 自動消込
          </el-button>
          <el-button type="success" @click="handleManualReconcile" :disabled="!hasReceiptSelection">
            <el-icon><Check /></el-icon> 手動消込
          </el-button>
        </div>

        <el-table :data="receiptList" v-loading="loading" stripe border @selection-change="handleReceiptSelectionChange">
          <el-table-column type="selection" width="50" fixed />
          <el-table-column prop="receipt_date" label="入金日" width="110" fixed />
          <el-table-column prop="customer_name" label="顧客名" min-width="150" />
          <el-table-column prop="receipt_amount" label="入金金額" width="130" align="right">
            <template #default="{ row }">¥{{ row.receipt_amount?.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column prop="bank_name" label="振込元銀行" width="150" />
          <el-table-column prop="matched_invoice" label="消込先請求書" width="130" />
          <el-table-column prop="matched_amount" label="消込金額" width="120" align="right">
            <template #default="{ row }">
              <span v-if="row.matched_amount">¥{{ row.matched_amount?.toLocaleString() }}</span>
              <span v-else class="text-warning">未消込</span>
            </template>
          </el-table-column>
          <el-table-column prop="unmatched_amount" label="未消込" width="100" align="right">
            <template #default="{ row }">
              <span v-if="row.unmatched_amount" class="text-danger">¥{{ row.unmatched_amount?.toLocaleString() }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleViewReceipt(row)">詳細</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Printer, Connection, Check } from '@element-plus/icons-vue'

const activeTab = ref('billing')
const loading = ref(false)
const billingList = ref<any[]>([])
const receiptList = ref<any[]>([])
const selectedRows = ref<any[]>([])
const selectedReceipts = ref<any[]>([])

const summary = reactive({ totalReceivables: 0, thisMonthBilled: 0, overdueAmount: 0, overdueCount: 0 })

const hasSelection = computed(() => selectedRows.value.length > 0)
const hasReceiptSelection = computed(() => selectedReceipts.value.length > 0)

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { billingList.value = []; receiptList.value = [] } finally { loading.value = false }
}

const handleSelectionChange = (rows: any[]) => { selectedRows.value = rows }
const handleReceiptSelectionChange = (rows: any[]) => { selectedReceipts.value = rows }
const handleCreateBilling = () => { ElMessage.info('締め請求書作成画面を開きます') }
const handlePrintBilling = () => { ElMessage.info(`${selectedRows.value.length}件の請求書を印刷します`) }
const handleAutoReconcile = () => { ElMessage.success('自動消込を実行しました') }
const handleManualReconcile = () => { ElMessage.info('手動消込画面を開きます') }
const handleViewBilling = (row: any) => { ElMessage.info(`請求書 ${row.invoice_no} の詳細`) }
const handleViewReceipt = (row: any) => { ElMessage.info('入金詳細') }

const getBillingStatusType = (s: string) => ({ draft: 'info', sent: 'primary', partial: 'warning', paid: 'success', overdue: 'danger' }[s] || 'info')
const getBillingStatusLabel = (s: string) => ({ draft: '下書き', sent: '送付済', partial: '一部入金', paid: '入金済', overdue: '延滞' }[s] || s)
</script>

<style scoped>
.billing { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.summary-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.summary-card { text-align: center; padding: 20px; }
.summary-value { font-size: 28px; font-weight: bold; color: #409eff; }
.summary-card.success .summary-value { color: #67c23a; }
.summary-card.warning .summary-value { color: #e6a23c; }
.summary-label { color: #909399; margin-top: 8px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.font-bold { font-weight: bold; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; }
</style>
